from __future__ import annotations
import hashlib, math, re, time
from .schemas import (
    AnalyzeRequest, AnalyzeResponse, TokenInfo, TopToken, CellReadout,
    ChatMessage, ChatGenerateRequest, ChatGenerateResponse, GeneratedToken,
    TraceToken, GenerateIntervenedRequest, GenerateIntervenedResponse,
    SideBySideOutput, DiffInfo, InterventionConfigRequest,
)

BASE = ["thought","working","answer","reason","plan","memory","hidden","concept","workspace","token","layer"]

def toks(prompt: str) -> list[str]:
    return re.findall(r"\s+|\w+|[^\w\s]", prompt) or [""]

def words(prompt: str) -> list[str]:
    p = prompt.lower()
    out = []
    def add(xs):
        for x in xs:
            if x not in out: out.append(x)
    if "web" in p or "spider" in p: add(["spider","eight","legs","animal","web","arachnid"])
    if "france" in p: add(["France","Paris","capital","Euro","Europe","French"])
    if "china" in p: add(["China","Beijing","capital","Yuan","Asia","Chinese"])
    if "bug" in p or "code" in p or "error" in p: add(["error","bug","exception","fix","issue"])
    if "calc" in p or "math" in p or "3" in p: add(["arithmetic","nine","seven","equals","answer"])
    add(BASE)
    return out

def score(seed, layer, pos, word):
    h = hashlib.sha256(f"{seed}|{layer}|{pos}|{word}".encode()).hexdigest()
    a = int(h[:10], 16) / float(0xffffffffff)
    b = 0.5 + 0.5 * math.sin(layer * .29 + pos * .41 + len(word))
    return .7*a + .3*b

def demo_analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    t0 = time.time()
    raw = toks(req.prompt)[:req.max_positions]
    token_infos = [TokenInfo(index=i, token_id=1000+i, text=t) for i,t in enumerate(raw)]
    positions = req.positions or list(range(len(raw)))
    positions = [p if p >= 0 else len(raw)+p for p in positions]
    positions = [p for p in positions if 0 <= p < len(raw)] or [len(raw)-1]
    layers = list(range(25))
    vocab = words(req.prompt)
    cells = []
    for layer in layers:
        for pos in positions:
            ranked = sorted(vocab, key=lambda w: score(req.prompt, layer, pos, w), reverse=True)
            top = [TopToken(token=w, token_id=abs(hash(w))%50000, score=float(score(req.prompt, layer, pos, w)), rank=i+1) for i,w in enumerate(ranked[:req.top_k])]
            cells.append(CellReadout(layer=layer, position=pos, top=top))
    elapsed = time.time() - t0
    return AnalyzeResponse(
        model_config_id=req.model_config_id, prompt=req.prompt, tokens=token_infos,
        layers=layers, positions=positions, cells=cells,
        meta={"mode":"demo", "warning":"Synthetic demo data; not a real J-lens readout.",
              "timing": {"total_ms": round(elapsed * 1000, 1)}}
    )


DEMO_NEXT_TOKENS = [
    " The", " spider", " has", " eight", " legs", " and", " spins", " webs", ".\n",
    "It", " is", " an", " arachnid", ",", " not", " an", " insect", ".",
]


def demo_chat_generate(req: ChatGenerateRequest) -> ChatGenerateResponse:
    t0 = time.time()
    t1 = t0 + 0.01

    user_text = " ".join(m.content for m in req.messages if m.role == "user")
    gen_text = "The spider has eight legs and spins webs. It is an arachnid, not an insect."
    gen_tokens = []
    for i, tok_text in enumerate(DEMO_NEXT_TOKENS):
        gen_tokens.append(GeneratedToken(index=i, token_id=2000+i, text=tok_text))
    t2 = time.time() + 0.02

    analysis = None
    if req.analyze_response:
        full_prompt_text = user_text + " " + gen_text
        analyze_req = AnalyzeRequest(
            model_config_id=req.model_config_id,
            prompt=full_prompt_text,
            top_k=8,
            max_positions=48,
            force_demo=True,
        )
        analysis = demo_analyze(analyze_req)
    t3 = time.time() + 0.03

    trace = None
    if req.trace_generation:
        trace = _demo_build_trace(gen_tokens, analysis, req.trace_layers)

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
            "device": "cpu",
            "model_id": "demo",
            "timing": {
                "format_ms": round((t1 - t0) * 1000, 1),
                "generate_ms": round((t2 - t1) * 1000, 1),
                "analyze_ms": round((t3 - t2) * 1000, 1),
                "total_ms": round(elapsed * 1000, 1),
            },
        },
    )


def _demo_build_trace(
    gen_tokens: list[GeneratedToken],
    analysis: AnalyzeResponse | None,
    trace_layers: list[int] | None,
) -> dict:
    tokens = []
    for gt in gen_tokens:
        full_pos = gt.index
        if analysis:
            found_tok = [t for t in analysis.tokens if t.text.strip() == gt.text.strip()]
            if found_tok:
                full_pos = found_tok[0].index
        trace_tok: dict = {
            "generated_index": gt.index,
            "full_position": full_pos,
            "text": gt.text,
            "model_top_logits": None,
            "jlens_by_layer": {},
        }
        if analysis and trace_layers:
            jlens_map = {}
            for layer in trace_layers:
                cells_at = [c for c in analysis.cells if c.layer == layer and c.position == full_pos]
                if cells_at:
                    jlens_map[str(layer)] = [t.model_dump() for t in cells_at[0].top[:5]]
            trace_tok["jlens_by_layer"] = jlens_map
        tokens.append(trace_tok)
    return {
        "mode": "post_hoc",
        "tokens": tokens,
    }


def _demo_generate_text(seed_text: str) -> str:
    return "The spider has eight legs and spins webs. It is an arachnid, not an insect."


def _demo_generate_tokens(seed_text: str) -> list[GeneratedToken]:
    return [GeneratedToken(index=i, token_id=2000+i, text=t) for i, t in enumerate(DEMO_NEXT_TOKENS)]


def demo_generate_intervened(req: GenerateIntervenedRequest) -> GenerateIntervenedResponse:
    user_text = " ".join(m.content for m in req.messages if m.role == "user")

    clean_text = _demo_generate_text(user_text)
    clean_tokens = _demo_generate_tokens(user_text)

    if req.intervention.enabled and req.intervention.mode != "none":
        intervened_text = clean_text.replace("spider", "butterfly").replace("eight", "four") + " [intervened]"
        intervened_tokens = _demo_generate_tokens(user_text + " intervened")
    else:
        intervened_text = clean_text
        intervened_tokens = clean_tokens

    clean_analysis = None
    intervened_analysis = None
    if req.analyze_outputs:
        analyze_req = AnalyzeRequest(
            model_config_id=req.model_config_id,
            prompt=user_text + " " + clean_text,
            top_k=8,
            max_positions=48,
            force_demo=True,
        )
        clean_analysis = demo_analyze(analyze_req)
        analyze_req2 = AnalyzeRequest(
            model_config_id=req.model_config_id,
            prompt=user_text + " " + intervened_text,
            top_k=8,
            max_positions=48,
            force_demo=True,
        )
        intervened_analysis = demo_analyze(analyze_req2)

    clean_len = len(clean_tokens)
    intervened_len = len(intervened_tokens)

    return GenerateIntervenedResponse(
        clean=SideBySideOutput(
            generated_text=clean_text,
            generated_tokens=clean_tokens,
            analysis=clean_analysis,
        ),
        intervened=SideBySideOutput(
            generated_text=intervened_text,
            generated_tokens=intervened_tokens,
            analysis=intervened_analysis,
        ),
        diff=DiffInfo(
            same_output=clean_text == intervened_text,
            clean_length=clean_len,
            intervened_length=intervened_len,
        ),
        intervention=req.intervention.model_dump(),
        meta={
            "warning": "Experimental intervention. Effects may be model/lens dependent.",
            "timing": {"total_ms": 50},
        },
    )
