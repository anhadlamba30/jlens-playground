from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "version" in data


def test_models():
    r = client.get("/api/models")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    ids = [m["id"] for m in data]
    assert "demo-synthetic" in ids


def test_diagnostics():
    r = client.get("/api/diagnostics")
    assert r.status_code == 200
    data = r.json()
    assert "project_root" in data
    assert "python" in data
    assert "torch" in data


def test_analyze_demo():
    r = client.post("/api/analyze", json={
        "prompt": "The spider spins a web",
        "top_k": 8,
        "max_positions": 10,
        "force_demo": True
    })
    assert r.status_code == 200
    data = r.json()
    assert "tokens" in data
    assert len(data["tokens"]) > 0
    assert "layers" in data
    assert "cells" in data
    assert "meta" in data
    assert data["meta"]["mode"] == "demo"
