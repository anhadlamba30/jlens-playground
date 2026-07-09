from __future__ import annotations
import json
import logging
from pathlib import Path
from .schemas import ModelConfig

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_CONFIG_PATH = PROJECT_ROOT / "configs" / "models.example.json"
LOCAL_CONFIG_PATH = PROJECT_ROOT / "configs" / "models.local.json"

def load_model_configs() -> list[ModelConfig]:
    configs = []
    if EXAMPLE_CONFIG_PATH.exists():
        data = json.loads(EXAMPLE_CONFIG_PATH.read_text())
        configs.extend(ModelConfig(**x) for x in data)
    if LOCAL_CONFIG_PATH.exists():
        local_data = json.loads(LOCAL_CONFIG_PATH.read_text())
        local_ids = {x["id"] for x in local_data}
        configs = [c for c in configs if c.id not in local_ids]
        configs.extend(ModelConfig(**x) for x in local_data)
    return configs

def get_model_config(config_id: str) -> ModelConfig:
    for cfg in load_model_configs():
        if cfg.id == config_id:
            return cfg
    raise KeyError(f"Unknown model_config_id={config_id}")

def write_local_config(configs: list[ModelConfig]) -> None:
    data = [c.model_dump() for c in configs]
    LOCAL_CONFIG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    logger.info("Wrote %d config(s) to %s", len(configs), LOCAL_CONFIG_PATH)