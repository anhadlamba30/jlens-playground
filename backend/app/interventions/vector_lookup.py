from __future__ import annotations
import logging
import torch

logger = logging.getLogger(__name__)

SUPPORTED = False


def get_lens_vector(
    jlens_model,
    lens,
    tokenizer,
    token_text: str,
    layer: int,
) -> torch.Tensor:
    tokenizer_output = tokenizer(token_text, add_special_tokens=False)
    ids = tokenizer_output["input_ids"]
    if len(ids) != 1:
        raise ValueError(
            f"Token text {token_text!r} maps to {len(ids)} token IDs ({ids}), expected exactly 1. "
            f"Use a single-token word."
        )
    token_id = ids[0]

    vector = _extract_lens_vector(lens, layer, token_id)
    if vector is None:
        raise RuntimeError(
            f"Could not extract lens vector for layer {layer}, token_id {token_id}. "
            f"Lens object type: {type(lens).__name__}. "
            f"Intervention mode not supported for this lens structure."
        )
    return vector


def _extract_lens_vector(lens, layer: int, token_id: int) -> torch.Tensor | None:
    if hasattr(lens, "vectors") and isinstance(lens.vectors, dict):
        key = (int(layer), int(token_id))
        if key in lens.vectors:
            return lens.vectors[key].detach().clone()
        key = f"{layer}:{token_id}"
        if key in lens.vectors:
            return lens.vectors[key].detach().clone()

    if hasattr(lens, "get_vector"):
        try:
            return lens.get_vector(layer=layer, token_id=token_id).detach().clone()
        except Exception:
            pass

    if hasattr(lens, "W_U") and hasattr(lens, "W_U") and hasattr(lens, "b_U"):
        W_U = lens.W_U.detach()
        b_U = lens.b_U.detach()
        if isinstance(layer, int) and 0 <= layer < W_U.shape[0]:
            vec = W_U[token_id] - W_U[layer]
            return vec

    if hasattr(lens, "W_U") and isinstance(lens.W_U, torch.Tensor):
        W_U = lens.W_U.detach()
        if token_id < W_U.shape[0]:
            vec = W_U[token_id]
            return vec

    return None


def check_intervention_supported(lens) -> dict:
    result = {
        "supported": False,
        "reason": "unknown",
        "methods_tried": [],
    }
    if hasattr(lens, "vectors") and isinstance(lens.vectors, dict):
        result["supported"] = True
        result["methods_tried"].append("lens.vectors dict")
        result["reason"] = "ok"
        return result
    if hasattr(lens, "get_vector"):
        result["methods_tried"].append("lens.get_vector")
        try:
            _ = lens.get_vector(layer=0, token_id=0)
            result["supported"] = True
            result["reason"] = "ok"
            return result
        except Exception as e:
            result["methods_tried"].append(f"get_vector failed: {e}")
    if hasattr(lens, "W_U"):
        result["methods_tried"].append("lens.W_U")
        result["supported"] = True
        result["reason"] = "ok (using W_U embedding)"
        return result
    result["reason"] = "No compatible vector field found on lens object"
    return result
