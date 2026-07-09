from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class InterventionConfig(BaseModel):
    enabled: bool = False
    mode: Literal["none", "add", "ablate", "swap"] = "none"
    token: str | None = None
    source_token: str | None = None
    target_token: str | None = None
    alpha: float = 1.0
    layer_start: int | None = None
    layer_end: int | None = None
    layer_step: int = 1
    position_mode: Literal["all", "selected", "last_prompt", "generated_only"] = "all"
    selected_positions: list[int] | None = None
    normalize_vector: bool = True
