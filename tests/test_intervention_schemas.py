from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.interventions.schemas import InterventionConfig


def test_defaults():
    cfg = InterventionConfig()
    assert cfg.enabled is False
    assert cfg.mode == "none"
    assert cfg.alpha == 1.0
    assert cfg.layer_step == 1
    assert cfg.position_mode == "all"
    assert cfg.normalize_vector is True


def test_valid_add():
    cfg = InterventionConfig(
        enabled=True,
        mode="add",
        token="monkey",
        alpha=1.5,
        layer_start=8,
        layer_end=16,
    )
    assert cfg.enabled is True
    assert cfg.mode == "add"
    assert cfg.token == "monkey"
    assert cfg.alpha == 1.5
    assert cfg.layer_start == 8
    assert cfg.layer_end == 16


def test_valid_ablate():
    cfg = InterventionConfig(
        enabled=True,
        mode="ablate",
        token="negative",
        alpha=0.5,
        layer_start=0,
        layer_end=8,
    )
    assert cfg.mode == "ablate"
    assert cfg.token == "negative"


def test_valid_swap():
    cfg = InterventionConfig(
        enabled=True,
        mode="swap",
        source_token="old",
        target_token="new",
        alpha=1.0,
        layer_start=4,
        layer_end=12,
    )
    assert cfg.mode == "swap"
    assert cfg.source_token == "old"
    assert cfg.target_token == "new"


def test_invalid_swap_missing_source_fails_validation():
    cfg = InterventionConfig(
        enabled=True,
        mode="swap",
        target_token="new",
    )
    assert cfg.source_token is None


def test_position_modes():
    for mode in ["all", "selected", "last_prompt", "generated_only"]:
        cfg = InterventionConfig(position_mode=mode)
        assert cfg.position_mode == mode


def test_serialization():
    cfg = InterventionConfig(
        enabled=True,
        mode="add",
        token="test",
        alpha=2.0,
        layer_start=0,
        layer_end=24,
        layer_step=2,
        position_mode="last_prompt",
    )
    d = cfg.model_dump()
    assert d["enabled"] is True
    assert d["mode"] == "add"
    assert d["token"] == "test"
    assert d["alpha"] == 2.0
    assert d["layer_start"] == 0
    assert d["layer_end"] == 24
    assert d["layer_step"] == 2
    assert d["position_mode"] == "last_prompt"
