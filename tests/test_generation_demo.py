from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_generate_demo():
    r = client.post("/api/chat/generate", json={
        "model_config_id": "demo-synthetic",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_new_tokens": 16,
        "temperature": 0.0,
        "top_p": 1.0,
        "seed": 0,
        "analyze_response": True,
        "trace_generation": False,
    })
    assert r.status_code == 200
    data = r.json()
    assert "messages" in data
    assert data["messages"][-1]["role"] == "assistant"
    assert len(data["messages"][-1]["content"]) > 0
    assert "generated_text" in data
    assert "generated_tokens" in data
    assert "meta" in data
    assert "timing" in data["meta"]


def test_chat_generate_no_analysis():
    r = client.post("/api/chat/generate", json={
        "model_config_id": "demo-synthetic",
        "messages": [{"role": "user", "content": "Hello"}],
        "analyze_response": False,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["analysis"] is None


def test_chat_generate_with_trace():
    r = client.post("/api/chat/generate", json={
        "model_config_id": "demo-synthetic",
        "messages": [{"role": "user", "content": "Hello"}],
        "analyze_response": True,
        "trace_generation": True,
        "trace_layers": [0, 8, 16],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["trace"] is not None
    assert data["trace"]["mode"] == "post_hoc"
    assert len(data["trace"]["tokens"]) > 0
    for tok in data["trace"]["tokens"]:
        assert "generated_index" in tok
        assert "full_position" in tok
        assert "text" in tok


def test_chat_generate_timing():
    r = client.post("/api/chat/generate", json={
        "model_config_id": "demo-synthetic",
        "messages": [{"role": "user", "content": "Hi"}],
    })
    data = r.json()
    assert "timing" in data["meta"]
    assert data["meta"]["timing"]["total_ms"] > 0
