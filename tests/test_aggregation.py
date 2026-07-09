from __future__ import annotations

def compute_aggregation(cells):
    token_map = {}
    for cell in cells:
        if not cell.get("top"):
            continue
        for t in cell["top"]:
            token = t["token"]
            if token not in token_map:
                token_map[token] = {"cellCount": 0, "scores": [], "ranks": [], "positions": set(), "layers": set()}
            entry = token_map[token]
            entry["cellCount"] += 1
            entry["scores"].append(t["score"])
            entry["ranks"].append(t["rank"])
            entry["positions"].add(cell["position"])
            entry["layers"].add(cell["layer"])
    return [
        {"token": k, "cellCount": v["cellCount"],
         "avgScore": sum(v["scores"]) / len(v["scores"]) if v["scores"] else 0,
         "bestRank": min(v["ranks"]) if v["ranks"] else 0,
         "positions": len(v["positions"]),
         "layers": len(v["layers"])}
        for k, v in token_map.items()
    ]


def make_cell(layer, pos, tops):
    return {
        "layer": layer,
        "position": pos,
        "top": [{"token": t, "score": 1.0, "rank": i + 1} for i, t in enumerate(tops)]
    }


def test_aggregation_counts_tokens():
    cells = [
        make_cell(0, 0, ["cat", "dog", "bird"]),
        make_cell(0, 1, ["cat", "fish", "dog"]),
    ]
    agg = compute_aggregation(cells)
    cat = [a for a in agg if a["token"] == "cat"][0]
    assert cat["cellCount"] == 2
    dog = [a for a in agg if a["token"] == "dog"][0]
    assert dog["cellCount"] == 2
    bird = [a for a in agg if a["token"] == "bird"][0]
    assert bird["cellCount"] == 1


def test_aggregation_respects_layer_filter():
    cells = [
        make_cell(0, 0, ["cat"]),
        make_cell(1, 0, ["dog"]),
        make_cell(2, 0, ["cat"]),
    ]
    filtered = [c for c in cells if c["layer"] in [0, 1]]
    agg = compute_aggregation(filtered)
    cat = [a for a in agg if a["token"] == "cat"][0]
    assert cat["cellCount"] == 1
    assert cat["layers"] == 1


def test_aggregation_respects_position_filter():
    cells = [
        make_cell(0, 0, ["cat"]),
        make_cell(0, 1, ["cat"]),
        make_cell(0, 2, ["dog"]),
    ]
    filtered = [c for c in cells if c["position"] in [0, 1]]
    agg = compute_aggregation(filtered)
    cat = [a for a in agg if a["token"] == "cat"][0]
    assert cat["cellCount"] == 2
    dog_tokens = [a for a in agg if a["token"] == "dog"]
    assert len(dog_tokens) == 0


def test_aggregation_sorts_by_cell_count():
    cells = [
        make_cell(0, 0, ["cat", "dog"]),
        make_cell(1, 0, ["cat", "bird"]),
        make_cell(2, 0, ["dog"]),
    ]
    agg = compute_aggregation(cells)
    counts = [a["cellCount"] for a in sorted(agg, key=lambda x: -x["cellCount"])]
    assert counts == sorted(counts, reverse=True)
