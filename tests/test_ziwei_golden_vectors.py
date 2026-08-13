"""Ziwei Golden Vector regression tests (Phase 6.7.2).

Verifies:
- 24 vectors present with complete metadata (engine v0.3.0)
- Determinism: same input -> byte-identical output on repeated runs
- Every vector's expected chart matches live engine replay
- Rule coverage: all 17 ZW rules (ZW-001..ZW-017) covered by >=1 vector
- Serialization stability (json.dumps sort_keys consistency)

Golden vectors are normative evidence generated from ZiweiEngine v0.3.0
output; expected values are never hand-edited.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from openmetaphysics.agents.ziwei import ZiweiEngine, ZiweiInput
from openmetaphysics.core.schemas import Gender, GeoPoint

VECTOR_FILE = Path(__file__).resolve().parents[1] / "docs" / "ziwei" / "golden_vectors.json"

GENDER = {"male": Gender.MALE, "female": Gender.FEMALE, "unknown": Gender.UNKNOWN}

ALL_RULES = [f"ZW-{i:03d}" for i in range(1, 18)]


def _load() -> dict:
    return json.loads(VECTOR_FILE.read_text(encoding="utf-8"))


def _vectors() -> list[dict]:
    return _load()["vectors"]


def _make_input(v: dict) -> ZiweiInput:
    inp = v["input"]
    loc = inp["born_location"]
    return ZiweiInput(
        request_id=inp["request_id"],
        born_at=datetime.fromisoformat(inp["born_at"]),
        born_location=GeoPoint(**loc) if loc else None,
        gender=GENDER[inp["gender"]],
        question=inp["question"],
        locale=inp["locale"],
        seed=inp["seed"],
        client_nonce=inp["client_nonce"],
        lunar_month=inp["lunar_month"],
        lunar_day=inp["lunar_day"],
    )


def _chart_for(v: dict) -> dict:
    return ZiweiEngine().calculate(_make_input(v))


def test_vector_count() -> None:
    data = _load()
    assert data["metadata"]["total_vectors"] == 24
    assert len(_vectors()) == 24


def test_vector_ids_unique() -> None:
    ids = [v["id"] for v in _vectors()]
    assert len(ids) == len(set(ids)), "duplicate vector ids"
    for v in _vectors():
        assert v["id"].startswith("ZV-")


def test_engine_version() -> None:
    data = _load()
    assert data["metadata"]["domain"] == "ziwei"
    assert data["metadata"]["status"] == "candidate"
    assert data["metadata"]["engine_version"] == ZiweiEngine.version
    for v in _vectors():
        assert v["expected"]["metadata"]["engine_version"] == ZiweiEngine.version
    assert ZiweiEngine.version == "0.3.0"


def test_determinism() -> None:
    for v in _vectors():
        first = _chart_for(v)
        second = _chart_for(v)
        assert first == second, f"{v['id']} not deterministic"
        assert first == v["expected"]["chart"], f"{v['id']} expected mismatch"


def test_all_vectors_replay() -> None:
    for v in _vectors():
        assert _chart_for(v) == v["expected"]["chart"], f"{v['id']} replay failed"


def test_rule_coverage_complete() -> None:
    covered = {rule for v in _vectors() for rule in v["rule_coverage"]}
    missing = [r for r in ALL_RULES if r not in covered]
    assert not missing, f"rules not covered: {missing}"
    for v in _vectors():
        assert v["rule_coverage"], f"{v['id']} has empty rule_coverage"


def test_serialization_stable() -> None:
    data = _load()
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    assert canonical == VECTOR_FILE.read_text(encoding="utf-8"), (
        "golden_vectors.json is not in canonical sorted-key form"
    )
    # double-dump stability
    again = json.dumps(json.loads(canonical), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    assert again == canonical
