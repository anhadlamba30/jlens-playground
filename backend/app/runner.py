from __future__ import annotations
import logging, time
from pathlib import Path
from typing import Any
import gc
import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from .config import PROJECT_ROOT
from .schemas import (
    ModelConfig, AnalyzeRequest, AnalyzeResponse, TokenInfo, TopToken, CellReadout,
    ChatGenerateRequest, ChatGenerateResponse, ChatMessage, GeneratedToken,
)
from .chat_templates import format_chat_prompt
from .generation import generate_text

logger = logging.getLogger(__name__)

def choose_device(device: str) -> str:
    if device and device != "auto":
        return device
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"

def choose_dtype(dtype: str, device: str):
    if dtype == "float32":
        return torch.float32
    if dtype == "float16":
        return torch.float16
    if dtype == "bfloat16":
        return torch.bfloat16
    if dtype == "auto":
        return torch.float32 if device == "cpu" else torch.float16
    return None

def resolve_path(p: str) -> Path:
    path = Path(p).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path

class Loaded:
    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg
        self.device = choose_device(cfg.device)
        dtype = choose_dtype(cfg.dtype, self.device)
        logger.info("Loading model %s on %s", cfg.model_id, self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(cfg.model_id)
        kwargs: dict[str, Any] = {}
        if dtype is not None:
            kwargs["torch_dtype"] = dtype
        self.hf = AutoModelForCausalLM.from_pretrained(cfg.model_id, **kwargs)
        self.hf.eval()
        if self.device != "cpu":
            self.hf.to(self.device)
        import jlens
        self.jlens = jlens
        logger.info("Building JLens model wrapper")
        self.model = jlens.from_hf(self.hf, self.tokenizer)
        lens_path = resolve_path(cfg.lens_path)
        if not lens_path.exists():
            found = list((PROJECT_ROOT / 'lenses').glob('**/*.pt'))
            raise FileNotFoundError(f"Lens file not found: {lens_path}. Found .pt files: {[str(x) for x in found[:20]]}")
        self.lens_path = lens_path
        self.lens = self._load_lens(lens_path)
        logger.info("Model loaded: %s", cfg.model_id)

    def _load_lens(self, lens_path: Path):
        jlens = self.jlens
        errors = []
        if hasattr(jlens, 'JacobianLens'):
            JL = jlens.JacobianLens
            if hasattr(JL, 'from_pretrained'):
                try:
                    return JL.from_pretrained(str(lens_path.parent), filename=lens_path.name)
                except Exception as e:
                    errors.append(f"JacobianLens.from_pretrained failed: {type(e).__name__}: {e}")
            if hasattr(JL, 'load'):
                try:
                    return JL.load(str(lens_path))
                except Exception as e:
                    errors.append(f"JacobianLens.load failed: {type(e).__name__}: {e}")
        try:
            obj = torch.load(str(lens_path), map_location='cpu')
            if hasattr(obj, 'apply'):
                return obj
            errors.append(f"torch.load returned {type(obj)} without .apply")
        except Exception as e:
            errors.append(f"torch.load failed: {type(e).__name__}: {e}")
        raise RuntimeError("Could not load lens. " + " | ".join(errors))

    def tokenize(self, prompt: str):
        ids = self.tokenizer(prompt, return_tensors='pt', add_special_tokens=False)['input_ids'][0].tolist()
        return [TokenInfo(index=i, token_id=int(t), text=self.tokenizer.convert_ids_to_tokens(int(t)).replace('Ġ', '·')) for i, t in enumerate(ids)]

    def analyze(self, req: AnalyzeRequest) -> AnalyzeResponse:
        t0 = time.time()
        token_infos = self.tokenize(req.prompt)
        t1 = time.time()
        n = len(token_infos)
        positions = req.positions or list(range(min(n, req.max_positions)))
        positions = [p if p >= 0 else n + p for p in positions]
        positions = [p for p in positions if 0 <= p < n] or [n - 1]
        with torch.no_grad():
            lens_logits, model_logits, extra = self.lens.apply(self.model, req.prompt, positions=positions)
        t2 = time.time()
        layers = sorted([int(k) for k in lens_logits.keys()])
        cells = []
        for layer in layers:
            logits = lens_logits[layer]
            arr = logits.detach().float().cpu() if isinstance(logits, torch.Tensor) else torch.tensor(np.asarray(logits), dtype=torch.float32)
            if arr.ndim == 1:
                arr = arr.unsqueeze(0)
            for i, pos in enumerate(positions[:arr.shape[0]]):
                vals, inds = arr[i].topk(req.top_k)
                top = []
                for rank, (v, idx) in enumerate(zip(vals.tolist(), inds.tolist()), start=1):
                    top.append(TopToken(token=self.tokenizer.decode([int(idx)]), token_id=int(idx), score=float(v), rank=rank))
                cells.append(CellReadout(layer=layer, position=pos, top=top))
        t3 = time.time()
        return AnalyzeResponse(
            model_config_id=req.model_config_id, prompt=req.prompt, tokens=token_infos,
            layers=layers, positions=positions, cells=cells,
            meta={
                "mode": "real", "device": self.device, "model_id": self.cfg.model_id,
                "lens_path": str(self.lens_path),
                "timing": {
                    "tokenize_ms": round((t1 - t0) * 1000, 1),
                    "lens_apply_ms": round((t2 - t1) * 1000, 1),
                    "postprocess_ms": round((t3 - t2) * 1000, 1),
                    "total_ms": round((t3 - t0) * 1000, 1),
                }
            }
        )

    def chat_generate(self, req: ChatGenerateRequest) -> ChatGenerateResponse:
        t0 = time.time()
        msgs_dict = [{"role": m.role, "content": m.content} for m in req.messages]
        prompt_text = format_chat_prompt(
            self.tokenizer,
            msgs_dict,
            add_generation_prompt=True,
        )
        t1 = time.time()

        gen_text, gen_tokens_raw = generate_text(
            model=self.hf,
            tokenizer=self.tokenizer,
            prompt_text=prompt_text,
            max_new_tokens=req.max_new_tokens,
            temperature=req.temperature,
            top_p=req.top_p,
            seed=req.seed,
            device=self.device,
        )
        gen_tokens = [GeneratedToken(index=i, token_id=t["token_id"], text=t["text"]) for i, t in enumerate(gen_tokens_raw)]
        t2 = time.time()

        analysis = None
        if req.analyze_response:
            full_text = prompt_text + gen_text
            analyze_req = AnalyzeRequest(
                model_config_id=req.model_config_id,
                prompt=full_text,
                top_k=8,
                max_positions=256,
            )
            analysis = self.analyze(analyze_req)
        t3 = time.time()

        trace = None
        if req.trace_generation and analysis:
            trace = self._build_trace(gen_tokens, analysis, req.trace_layers)

        elapsed = time.time() - t0
        return ChatGenerateResponse(
            model_config_id=req.model_config_id,
            messages=list(req.messages) + [ChatMessage(role="assistant", content=gen_text)],
            generated_text=gen_text,
            generated_tokens=gen_tokens,
            analysis=analysis,
            trace=trace,
            meta={
                "mode": "chat",
                "device": self.device,
                "model_id": self.cfg.model_id,
                "timing": {
                    "format_ms": round((t1 - t0) * 1000, 1),
                    "generate_ms": round((t2 - t1) * 1000, 1),
                    "analyze_ms": round((t3 - t2) * 1000, 1),
                    "total_ms": round(elapsed * 1000, 1),
                },
            },
        )

    def _build_trace(self, gen_tokens, analysis, trace_layers):
        tokens = []
        for gt in gen_tokens:
            full_pos = gt.index
            if analysis:
                matches = [t for t in analysis.tokens if t.text.strip() == gt.text.strip() and t.index >= 0]
                if matches:
                    full_pos = matches[0].index
            trace_entry = {
                "generated_index": gt.index,
                "full_position": full_pos,
                "text": gt.text,
                "model_top_logits": None,
                "jlens_by_layer": {},
            }
            if trace_layers and analysis:
                jlens_map = {}
                for layer in trace_layers:
                    cells_at = [c for c in analysis.cells if c.layer == layer and c.position == full_pos]
                    if cells_at:
                        jlens_map[str(layer)] = [t.model_dump() for t in cells_at[0].top[:5]]
                trace_entry["jlens_by_layer"] = jlens_map
            tokens.append(trace_entry)
        return {"mode": "post_hoc", "tokens": tokens}


_LOADED: dict[str, Loaded] = {}


def get_loaded(cfg: ModelConfig) -> Loaded:
    if cfg.id not in _LOADED:
        _LOADED[cfg.id] = Loaded(cfg)
    return _LOADED[cfg.id]


def unload_all():
    _LOADED.clear()
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
