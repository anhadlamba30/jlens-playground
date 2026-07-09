from __future__ import annotations
import logging
import time
import torch

logger = logging.getLogger(__name__)


def generate_text(
    model,
    tokenizer,
    prompt_text: str,
    max_new_tokens: int = 64,
    temperature: float = 0.0,
    top_p: float = 1.0,
    seed: int = 0,
    device: str = "cpu",
) -> tuple[str, list[dict]]:
    torch.manual_seed(seed)

    inputs = tokenizer(prompt_text, return_tensors="pt", add_special_tokens=False)
    input_ids = inputs["input_ids"].to(device)
    attention_mask = inputs.get("attention_mask", None)
    if attention_mask is not None:
        attention_mask = attention_mask.to(device)

    gen_kwargs = {
        "max_new_tokens": max_new_tokens,
        "do_sample": temperature > 0,
        "top_p": top_p if temperature > 0 else 1.0,
        "temperature": temperature if temperature > 0 else 1.0,
        "pad_token_id": tokenizer.eos_token_id or 0,
        "eos_token_id": tokenizer.eos_token_id or 0,
    }

    with torch.no_grad():
        output_ids = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            **gen_kwargs,
        )

    prompt_len = input_ids.shape[1]
    new_ids = output_ids[0][prompt_len:].tolist()
    generated_text = tokenizer.decode(new_ids, skip_special_tokens=True)

    generated_tokens = []
    for i, tid in enumerate(new_ids):
        generated_tokens.append({
            "index": i,
            "token_id": tid,
            "text": tokenizer.decode([tid]),
        })

    return generated_text, generated_tokens
