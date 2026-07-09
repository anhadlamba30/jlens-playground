from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    id: str
    label: str
    model_id: str
    lens_path: str
    device: str = "auto"
    dtype: str = "auto"
    enabled: bool = True
    notes: str | None = None


class AnalyzeRequest(BaseModel):
    model_config_id: str = "demo-synthetic"
    prompt: str
    baseline_prompt: str | None = None
    positions: list[int] | None = None
    top_k: int = Field(default=8, ge=1, le=50)
    max_positions: int = Field(default=48, ge=1, le=256)
    force_demo: bool = False


class TokenInfo(BaseModel):
    index: int
    token_id: int
    text: str


class TopToken(BaseModel):
    token: str
    token_id: int
    score: float
    rank: int


class CellReadout(BaseModel):
    layer: int
    position: int
    top: list[TopToken]


class AnalyzeResponse(BaseModel):
    model_config_id: str
    prompt: str
    tokens: list[TokenInfo]
    layers: list[int]
    positions: list[int]
    cells: list[CellReadout]
    meta: dict[str, Any]


class ValidateConfigRequest(BaseModel):
    model_config_id: str
    deep: bool = False


class ValidateConfigResponse(BaseModel):
    ok: bool
    checks: list[dict[str, Any]]


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatGenerateRequest(BaseModel):
    model_config_id: str = "demo-synthetic"
    messages: list[ChatMessage]
    max_new_tokens: int = 64
    temperature: float = 0.0
    top_p: float = 1.0
    seed: int = 0
    analyze_response: bool = True
    trace_generation: bool = False
    trace_layers: list[int] | None = None


class GeneratedToken(BaseModel):
    index: int
    token_id: int
    text: str


class TraceToken(BaseModel):
    generated_index: int
    full_position: int
    text: str
    model_top_logits: list[dict[str, Any]] | None = None
    jlens_by_layer: dict[str, list[TopToken]] | None = None


class ChatTiming(BaseModel):
    format_ms: float = 0
    generate_ms: float = 0
    analyze_ms: float = 0
    total_ms: float = 0


class ChatGenerateResponse(BaseModel):
    model_config_id: str
    messages: list[ChatMessage]
    generated_text: str
    generated_tokens: list[GeneratedToken] | None = None
    analysis: AnalyzeResponse | None = None
    trace: dict[str, Any] | None = None
    meta: dict[str, Any]


class GenerationSettings(BaseModel):
    max_new_tokens: int = 64
    temperature: float = 0.0
    top_p: float = 1.0
    seed: int = 0


class InterventionConfigRequest(BaseModel):
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


class GenerateIntervenedRequest(BaseModel):
    model_config_id: str = "demo-synthetic"
    messages: list[ChatMessage]
    generation: GenerationSettings = Field(default_factory=GenerationSettings)
    intervention: InterventionConfigRequest = Field(default_factory=InterventionConfigRequest)
    analyze_outputs: bool = True


class SideBySideOutput(BaseModel):
    generated_text: str
    generated_tokens: list[GeneratedToken]
    analysis: AnalyzeResponse | None = None


class DiffInfo(BaseModel):
    same_output: bool = False
    clean_length: int = 0
    intervened_length: int = 0


class GenerateIntervenedResponse(BaseModel):
    clean: SideBySideOutput
    intervened: SideBySideOutput
    diff: DiffInfo
    intervention: dict[str, Any]
    meta: dict[str, Any]
