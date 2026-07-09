from __future__ import annotations
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.schemas import ModelConfig
from app.config import load_model_configs


def test_example_config_parses():
    configs = load_model_configs()
    assert len(configs) > 0
    for cfg in configs:
        assert isinstance(cfg, ModelConfig)
        assert cfg.id
        assert cfg.label
        assert cfg.model_id


def test_example_config_has_demo():
    configs = load_model_configs()
    ids = [c.id for c in configs]
    assert "demo-synthetic" in ids


def test_local_config_override(monkeypatch, tmp_path):
    from app import config as cfg_mod

    example = tmp_path / "models.example.json"
    example.write_text(json.dumps([
        {"id": "shared", "label": "Example", "model_id": "org/example", "lens_path": "example.pt"},
        {"id": "only-example", "label": "Only Example", "model_id": "org/example", "lens_path": "ex.pt"},
    ]))

    local = tmp_path / "models.local.json"
    local.write_text(json.dumps([
        {"id": "shared", "label": "Local Override", "model_id": "org/local", "lens_path": "local.pt"},
        {"id": "only-local", "label": "Only Local", "model_id": "org/local", "lens_path": "loc.pt"},
    ]))

    monkeypatch.setattr(cfg_mod, "EXAMPLE_CONFIG_PATH", example)
    monkeypatch.setattr(cfg_mod, "LOCAL_CONFIG_PATH", local)

    configs = cfg_mod.load_model_configs()
    ids = [c.id for c in configs]
    assert "shared" in ids
    assert "only-example" in ids
    assert "only-local" in ids

    shared = [c for c in configs if c.id == "shared"][0]
    assert shared.label == "Local Override"
    assert shared.model_id == "org/local"
