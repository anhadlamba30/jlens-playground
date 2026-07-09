from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.schemas import AnalyzeRequest
from app.demo import demo_analyze


def test_demo_returns_tokens():
    req = AnalyzeRequest(prompt="Hello world")
    res = demo_analyze(req)
    assert len(res.tokens) > 0
    assert all(t.text for t in res.tokens)
    assert all(t.token_id > 0 for t in res.tokens)


def test_demo_returns_layers():
    req = AnalyzeRequest(prompt="test")
    res = demo_analyze(req)
    assert len(res.layers) == 25
    assert res.layers == list(range(25))


def test_demo_returns_cells():
    req = AnalyzeRequest(prompt="test")
    res = demo_analyze(req)
    assert len(res.cells) > 0
    for cell in res.cells:
        assert cell.layer in res.layers
        assert cell.position in res.positions
        assert len(cell.top) > 0


def test_demo_cells_have_top_tokens():
    req = AnalyzeRequest(prompt="spider web", top_k=5)
    res = demo_analyze(req)
    for cell in res.cells:
        assert len(cell.top) <= 5
        for t in cell.top:
            assert t.rank >= 1
            assert t.score > 0
            assert isinstance(t.token, str)


def test_demo_respects_max_positions():
    req = AnalyzeRequest(prompt="a b c d e f g h", max_positions=3)
    res = demo_analyze(req)
    assert len(res.positions) <= 3
    assert len(res.tokens) == 3


def test_demo_respects_top_k():
    req = AnalyzeRequest(prompt="test", top_k=3)
    res = demo_analyze(req)
    for cell in res.cells:
        assert len(cell.top) == 3
