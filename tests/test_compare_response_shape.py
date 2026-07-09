from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_generate_intervened_shape():
    r = client.post("/api/chat/generate-intervened", json={
        "model_config_id": "demo-synthetic",
        "messages": [{"role": "user", "content": "Tell me about spiders"}],
        "generation": {
            "max_new_tokens": 16,
            "temperature": 0.0,
            "top_p": 1.0,
            "seed": 0,
        },
        "intervention": {
            "enabled": True,
            "mode": "add",
            "token": "monkey",
            "alpha": 1.0,
            "layer_start": 8,
            "layer_end": 16,
            "position_mode": "all",
        },
        "analyze_outputs": True,
    })
    assert r.status_code == 200
    data = r.json()

    assert "clean" in data
    assert "intervened" in data
    assert "diff" in data
    assert "intervention" in data
    assert "meta" in data

    clean = data["clean"]
    assert "generated_text" in clean
    assert "generated_tokens" in clean
    assert "analysis" in clean

    intervened = data["intervened"]
    assert "generated_text" in intervened
    assert "generated_tokens" in intervened
    assert "analysis" in intervened

    diff = data["diff"]
    assert "same_output" in diff
    assert "clean_length" in diff
    assert "intervened_length" in diff

    assert "mode" in data["intervention"]
    assert "warning" in data["meta"]


def test_generate_intervened_no_intervention():
    r = client.post("/api/chat/generate-intervened", json={
        "model_config_id": "demo-synthetic",
        "messages": [{"role": "user", "content": "Hello"}],
        "intervention": {"enabled": False},
        "analyze_outputs": False,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["clean"]["generated_text"] == data["intervened"]["generated_text"]
    assert data["diff"]["same_output"] is True


def test_generate_intervened_metadata():
    r = client.post("/api/chat/generate-intervened", json={
        "model_config_id": "demo-synthetic",
        "messages": [{"role": "user", "content": "Hi"}],
        "intervention": {
            "enabled": True,
            "mode": "add",
            "token": "test",
            "alpha": 0.5,
            "layer_start": 0,
            "layer_end": 12,
        },
    })
    data = r.json()
    iv = data["intervention"]
    assert iv["mode"] == "add"
    assert iv["enabled"] is True
    assert iv["alpha"] == 0.5
