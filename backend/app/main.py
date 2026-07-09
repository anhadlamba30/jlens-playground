from __future__ import annotations
import json, logging, platform, sys, time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .schemas import (
    AnalyzeRequest, AnalyzeResponse, ValidateConfigRequest, ValidateConfigResponse,
    ChatGenerateRequest, ChatGenerateResponse, GenerateIntervenedRequest, GenerateIntervenedResponse,
)
from .config import PROJECT_ROOT, EXAMPLE_CONFIG_PATH, LOCAL_CONFIG_PATH, load_model_configs, get_model_config
from .demo import demo_analyze, demo_chat_generate, demo_generate_intervened
from .runner import get_loaded, unload_all
from .interventions.vector_lookup import check_intervention_supported
from .interventions.schemas import InterventionConfig
from .interventions.hooks import InterventionContext

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title='Local JLens Playground v2 API', version='0.4.0')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

logger.info("Server starting — project root: %s", PROJECT_ROOT)

@app.get('/api/health')
def health():
    return {'ok': True, 'version': '0.4.0'}

@app.get('/api/models')
def models():
    return [m.model_dump() for m in load_model_configs()]

@app.get('/api/diagnostics')
def diagnostics():
    lens_files = [str(p.relative_to(PROJECT_ROOT)) for p in (PROJECT_ROOT/'lenses').glob('**/*.pt')]
    try:
        import torch
        torch_info = {'version': torch.__version__, 'cuda': torch.cuda.is_available(), 'mps': bool(getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available())}
    except Exception as e:
        torch_info = {'error': str(e)}
    try:
        import jlens
        jlens_info = {'imported': True, 'file': getattr(jlens, '__file__', None)}
    except Exception as e:
        jlens_info = {'imported': False, 'error': str(e)}
    return {'project_root': str(PROJECT_ROOT), 'config_path': str(EXAMPLE_CONFIG_PATH), 'local_config_path': str(LOCAL_CONFIG_PATH) if LOCAL_CONFIG_PATH.exists() else None, 'python': sys.version, 'platform': platform.platform(), 'torch': torch_info, 'jlens': jlens_info, 'lens_files': lens_files[:100]}

@app.post('/api/analyze')
def analyze(req: AnalyzeRequest):
    t0 = time.time()
    try:
        cfg = get_model_config(req.model_config_id)
        logger.info("Analyze request: config=%s prompt_len=%d top_k=%d max_pos=%d baseline=%s",
                    req.model_config_id, len(req.prompt), req.top_k, req.max_positions,
                    'yes' if req.baseline_prompt else 'no')
        if req.force_demo or cfg.model_id == 'demo' or cfg.lens_path == 'demo':
            result = demo_analyze(req)
        else:
            result = get_loaded(cfg).analyze(req)
        if req.baseline_prompt:
            baseline_req = req.model_copy(update={'prompt': req.baseline_prompt, 'baseline_prompt': None})
            if req.force_demo or cfg.model_id == 'demo' or cfg.lens_path == 'demo':
                baseline_result = demo_analyze(baseline_req)
            else:
                baseline_result = get_loaded(cfg).analyze(baseline_req)
            comparison = compute_comparison(result, baseline_result)
            result_dict = result.model_dump()
            result_dict['comparison'] = comparison
            elapsed = time.time() - t0
            result_dict['meta']['timing'] = {'total_ms': round(elapsed * 1000, 1)}
            return result_dict
        elapsed = time.time() - t0
        result.meta['timing'] = {'total_ms': round(elapsed * 1000, 1)}
        logger.info("Analyze completed in %.2fs", elapsed)
        return result
    except Exception as e:
        logger.exception("Analyze failed")
        raise HTTPException(status_code=500, detail=f'{type(e).__name__}: {e}')

@app.post('/api/chat/generate')
def chat_generate(req: ChatGenerateRequest) -> ChatGenerateResponse:
    t0 = time.time()
    try:
        cfg = get_model_config(req.model_config_id)
        logger.info("Chat generate: config=%s messages=%d max_tokens=%d temp=%.2f",
                    req.model_config_id, len(req.messages), req.max_new_tokens, req.temperature)
        if req.model_config_id == 'demo-synthetic' or cfg.model_id == 'demo' or cfg.lens_path == 'demo':
            result = demo_chat_generate(req)
        else:
            result = get_loaded(cfg).chat_generate(req)
        elapsed = time.time() - t0
        if 'timing' not in result.meta:
            result.meta['timing'] = {}
        result.meta['timing']['total_ms'] = round(elapsed * 1000, 1)
        logger.info("Chat generate completed in %.2fs", elapsed)
        return result
    except Exception as e:
        logger.exception("Chat generate failed")
        raise HTTPException(status_code=500, detail=f'{type(e).__name__}: {e}')

@app.post('/api/chat/generate-intervened')
def generate_intervened(req: GenerateIntervenedRequest) -> GenerateIntervenedResponse:
    t0 = time.time()
    try:
        cfg = get_model_config(req.model_config_id)
        logger.info("Generate intervened: config=%s intervention_mode=%s",
                    req.model_config_id, req.intervention.mode)
        if req.model_config_id == 'demo-synthetic' or cfg.model_id == 'demo' or cfg.lens_path == 'demo':
            result = demo_generate_intervened(req)
        else:
            result = _real_generate_intervened(cfg, req)
        elapsed = time.time() - t0
        if 'timing' not in result.meta:
            result.meta['timing'] = {}
        result.meta['timing']['total_ms'] = round(elapsed * 1000, 1)
        logger.info("Generate intervened completed in %.2fs", elapsed)
        return result
    except Exception as e:
        logger.exception("Generate intervened failed")
        raise HTTPException(status_code=500, detail=f'{type(e).__name__}: {e}')

@app.post('/api/chat/check-intervention')
def check_intervention():
    try:
        cfg = get_model_config("demo-synthetic")
        loaded = get_loaded(cfg)
        result = check_intervention_supported(loaded.lens)
        return result
    except Exception as e:
        return {"supported": False, "reason": str(e), "methods_tried": []}

def _real_generate_intervened(cfg, req: GenerateIntervenedRequest) -> GenerateIntervenedResponse:
    from .chat_templates import format_chat_prompt
    from .generation import generate_text
    loaded = get_loaded(cfg)
    msgs_dict = [{"role": m.role, "content": m.content} for m in req.messages]
    prompt_text = format_chat_prompt(loaded.tokenizer, msgs_dict, add_generation_prompt=True)
    gen = req.generation

    clean_text, clean_tokens_raw = generate_text(
        model=loaded.hf, tokenizer=loaded.tokenizer, prompt_text=prompt_text,
        max_new_tokens=gen.max_new_tokens, temperature=gen.temperature,
        top_p=gen.top_p, seed=gen.seed, device=loaded.device,
    )
    clean_toks = [{"index": i, "token_id": t["token_id"], "text": t["text"]} for i, t in enumerate(clean_tokens_raw)]

    int_cfg = InterventionConfig(
        enabled=req.intervention.enabled,
        mode=req.intervention.mode,
        token=req.intervention.token,
        source_token=req.intervention.source_token,
        target_token=req.intervention.target_token,
        alpha=req.intervention.alpha,
        layer_start=req.intervention.layer_start,
        layer_end=req.intervention.layer_end,
        layer_step=req.intervention.layer_step,
        position_mode=req.intervention.position_mode,
        selected_positions=req.intervention.selected_positions,
        normalize_vector=req.intervention.normalize_vector,
    )
    if int_cfg.enabled and int_cfg.mode != "none":
        with InterventionContext(loaded.model, loaded.lens, loaded.tokenizer, int_cfg):
            intervened_text, intervened_tokens_raw = generate_text(
                model=loaded.hf, tokenizer=loaded.tokenizer, prompt_text=prompt_text,
                max_new_tokens=gen.max_new_tokens, temperature=gen.temperature,
                top_p=gen.top_p, seed=gen.seed, device=loaded.device,
            )
        intervened_toks = [{"index": i, "token_id": t["token_id"], "text": t["text"]} for i, t in enumerate(intervened_tokens_raw)]
    else:
        intervened_text = clean_text
        intervened_toks = list(clean_toks)

    clean_analysis = None
    intervened_analysis = None
    if req.analyze_outputs:
        from .schemas import AnalyzeRequest
        clean_analysis = loaded.analyze(AnalyzeRequest(
            model_config_id=req.model_config_id,
            prompt=prompt_text + clean_text,
            top_k=8, max_positions=256,
        ))
        intervened_analysis = loaded.analyze(AnalyzeRequest(
            model_config_id=req.model_config_id,
            prompt=prompt_text + intervened_text,
            top_k=8, max_positions=256,
        ))

    clean_len = len(clean_toks)
    intervened_len = len(intervened_toks)

    return GenerateIntervenedResponse(
        clean={
            "generated_text": clean_text,
            "generated_tokens": clean_toks,
            "analysis": clean_analysis.model_dump() if clean_analysis else None,
        },
        intervened={
            "generated_text": intervened_text,
            "generated_tokens": intervened_toks,
            "analysis": intervened_analysis.model_dump() if intervened_analysis else None,
        },
        diff={
            "same_output": clean_text == intervened_text,
            "clean_length": clean_len,
            "intervened_length": intervened_len,
        },
        intervention=int_cfg.model_dump() if int_cfg else {},
        meta={
            "warning": "Experimental intervention. Effects may be model/lens dependent.",
            "timing": {},
        },
    )

@app.post('/api/unload')
def unload():
    unload_all()
    logger.info("All models unloaded")
    return {'ok': True}

@app.post('/api/save-run')
def save_run(payload: dict):
    runs = PROJECT_ROOT/'runs'
    runs.mkdir(exist_ok=True)
    name = payload.get('name') or 'jlens-run'
    safe = ''.join(c if c.isalnum() or c in '-_' else '-' for c in name)[:80]
    path = runs/f'{safe}.json'
    path.write_text(json.dumps(payload.get('data', payload), indent=2, ensure_ascii=False))
    logger.info("Saved run to %s", path)
    return {'ok': True, 'path': str(path)}

@app.post('/api/validate-config', response_model=ValidateConfigResponse)
def validate_config(req: ValidateConfigRequest):
    checks = []
    try:
        cfg = get_model_config(req.model_config_id)
        checks.append({'name': 'config_exists', 'ok': True})
    except KeyError as e:
        matches = [c.id for c in load_model_configs()]
        return ValidateConfigResponse(ok=False, checks=[{'name': 'config_exists', 'ok': False, 'detail': str(e)}, {'name': 'valid_ids', 'ok': True, 'detail': f'Known IDs: {matches}'}])

    lens_path = Path(cfg.lens_path)
    if not lens_path.is_absolute():
        lens_path = PROJECT_ROOT / cfg.lens_path
    checks.append({'name': 'lens_path_exists', 'ok': lens_path.exists(), 'detail': str(lens_path.relative_to(PROJECT_ROOT)) if lens_path.exists() else f'Not found at {lens_path.relative_to(PROJECT_ROOT)}'})

    if not req.deep:
        return ValidateConfigResponse(ok=all(c['ok'] for c in checks), checks=checks)

    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(cfg.model_id)
        checks.append({'name': 'tokenizer_loads', 'ok': True, 'detail': f'Loaded {type(tokenizer).__name__}'})
    except Exception as e:
        checks.append({'name': 'tokenizer_loads', 'ok': False, 'detail': str(e)})

    try:
        import jlens
        checks.append({'name': 'jlens_imports', 'ok': True, 'detail': getattr(jlens, '__file__', None)})
    except Exception as e:
        checks.append({'name': 'jlens_imports', 'ok': False, 'detail': str(e)})

    return ValidateConfigResponse(ok=all(c['ok'] for c in checks), checks=checks)

frontend_dist = PROJECT_ROOT / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
    logger.info("Serving frontend static files from %s", frontend_dist)
else:
    logger.info("No frontend dist at %s — API only. Run 'npm run build' in frontend/ to enable.", frontend_dist)

def compute_comparison(primary: AnalyzeResponse, baseline: AnalyzeResponse) -> dict:
    cell_map_p = {(c.layer, c.position): c.top for c in primary.cells}
    cell_map_b = {(c.layer, c.position): c.top for c in baseline.cells}
    shared_positions = set(primary.positions) & set(baseline.positions)
    shared_layers = set(primary.layers) & set(baseline.layers)
    token_scores_p = {}
    token_scores_b = {}
    for layer in shared_layers:
        for pos in shared_positions:
            for t in cell_map_p.get((layer, pos), []):
                token_scores_p[t.token] = token_scores_p.get(t.token, 0) + 1
            for t in cell_map_b.get((layer, pos), []):
                token_scores_b[t.token] = token_scores_b.get(t.token, 0) + 1
    all_tokens = set(token_scores_p.keys()) | set(token_scores_b.keys())
    deltas = []
    for token in all_tokens:
        pc = token_scores_p.get(token, 0)
        bc = token_scores_b.get(token, 0)
        delta = pc - bc
        if delta > 0 or (delta == 0 and pc > 0):
            deltas.append({'token': token, 'primary_cells': pc, 'baseline_cells': bc, 'delta': delta})
    deltas.sort(key=lambda x: -x['delta'])
    note = (f"Comparing {len(shared_positions)} shared positions across {len(shared_layers)} shared layers. "
            f"Primary and baseline had {len(primary.tokens)} and {len(baseline.tokens)} tokens respectively.")
    return {'notes': [note], 'region_token_delta': deltas[:30]}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='127.0.0.1', port=8787, reload=False)
