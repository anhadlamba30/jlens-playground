from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

FALLBACK_SYSTEM = "You are a helpful assistant."


def format_chat_prompt(
    tokenizer,
    messages: list[dict],
    add_generation_prompt: bool = True,
) -> str:
    if hasattr(tokenizer, "apply_chat_template") and getattr(tokenizer, "chat_template", None) is not None:
        try:
            result = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=add_generation_prompt,
            )
            logger.info("Using native chat template")
            return result
        except Exception as e:
            logger.warning("Native chat template failed, falling back: %s", e)

    logger.info("Using fallback chat format")
    lines: list[str] = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            lines.append(f"System: {content}")
        elif role == "user":
            lines.append(f"User: {content}")
        elif role == "assistant":
            lines.append(f"Assistant: {content}")
        else:
            lines.append(f"{role.capitalize()}: {content}")
    if add_generation_prompt:
        lines.append("Assistant:")
    return "\n".join(lines)
