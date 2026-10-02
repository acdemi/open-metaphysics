"""Liuyao golden vector regression tests (Phase B contractization).

Verifies that the 24 candidate vectors still match the live deterministic
engine, that rejected inputs stay rejected, and that the engine is
reproducible. Mirrors tests/test_bazi_golden_vectors.py.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput

VECTOR_FILE = Path(__file__).resolve().parents[1] / "docs" / "liuyao" / "golden_vectors.json"


def _load() -> dict:
    return json.loads(VECTOR_FILE.read_text(encoding="utf-8"))


def _vectors() -> list[dict]:
    return _load()["vectors"]


def _payload(vector: dict) -> LiuyaoInput:
    v = vector["input"]
    return LiuyaoInput(
        request_id="gv-test",
        born_at=datetime.fromisoformat(v["born_at"]),
        casts=v["casts"],
        question=v.get("question"),
        seed=v.get("seed"),
    )


def test_vector_file_shape():
    doc = _load()
    meta = doc["metadata"]
    assert meta["domain"] == "liuyao"
    assert meta["status"] == "candidate"
    assert meta["reference"] == "reference/liuyao/domain.py"
    vectors = doc["vectors"]
    assert len(vectors) == meta["total_vectors"] == 24
    assert len({v["id"] for v in vectors}) == 24
    assert set(meta["categories"]) == {"normal", "edge", "boundary", "invalid"}


def test_every_vector_matches_live_engine():
    mismatched: list[str] = []
    for vector in _vectors():
        if vector.get("expected") is None:
            continue
        actual = LiuyaoAgent().compute(_payload(vector)).result.model_dump()
        if actual != vector["expected"]:
            mismatched.append(vector["id"])
    assert not mismatched, f"golden vector drift: {mismatched}"


def test_invalid_vectors_are_rejected():
    invalid = [v for v in _vectors() if v.get("expected_error")]
    assert len(invalid) == 3
    for vector in invalid:
        with pytest.raises(ValueError) as excinfo:
            _payload(vector)
        assert vector["expected_error"] in str(excinfo.value), vector["id"]


def test_engine_is_reproducible():
    for vector in _vectors():
        if vector.get("expected") is None:
            continue
        payload = _payload(vector)
        first = LiuyaoAgent().compute(payload).result.model_dump()
        second = LiuyaoAgent().compute(payload).result.model_dump()
        assert first == second, vector["id"]


def test_coverage_ids_are_known_rules():
    known = {f"LY-{i:02d}" for i in range(1, 12)}
    for vector in _vectors():
        for rule in vector.get("coverage", []):
            assert rule in known, f"{vector['id']} references unknown rule {rule}"


def test_categories_cover_the_required_matrix():
    categories = {v["category"] for v in _vectors()}
    assert {"normal", "edge", "boundary", "invalid"} <= categories
    counts = {c: sum(1 for v in _vectors() if v["category"] == c) for c in categories}
    assert counts["normal"] >= 5
    assert counts["boundary"] >= 3
