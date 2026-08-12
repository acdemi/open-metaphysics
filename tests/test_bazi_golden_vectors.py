"""BaZi Golden Vector regression tests (Phase 6.3A).

Verifies:
- 24 vectors present with unique ids and complete metadata
- Engine output byte-identical on repeated runs (determinism, QC-001 style)
- Serialization stability (json.dumps sort_keys consistency)
- Boundary regressions: Li Chun before/after, 23:00 day rollover,
  Da Yun banker's rounding (X.5 cases)
- Coverage completeness: B1..B6 all covered
- Every vector's expected payload matches live engine output
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.core.schemas import Gender, GeoPoint

VECTOR_FILE = Path(__file__).resolve().parents[1] / "docs" / "bazi" / "golden_vectors.json"

GENDER = {"male": Gender.MALE, "female": Gender.FEMALE, "unknown": Gender.UNKNOWN}


def _load() -> dict:
    return json.loads(VECTOR_FILE.read_text(encoding="utf-8"))


def _vectors() -> list[dict]:
    return _load()["vectors"]


def _input_for(v: dict) -> BaziInput:
    tz = v["input"]["born_location"]["timezone"]
    return BaziInput(
        request_id="gv-test",
        born_at=datetime.fromisoformat(v["input"]["born_at"]),
        gender=GENDER[v["input"]["gender"]],
        born_location=GeoPoint(latitude=0.0, longitude=0.0, timezone=tz),
    )


def _chart_for(v: dict):
    return BaziAgent().compute(_input_for(v)).result


def _pillars_of(chart) -> dict:
    return {x.position: x for x in chart.pillars}


def _assert_matches(v: dict, chart) -> None:
    e = v["expected"]
    p = _pillars_of(chart)
    for pos in ("year", "month", "day", "hour"):
        exp = e[f"{pos}_pillar"]
        assert p[pos].stem == exp["stem"], f"{v['id']} {pos} stem"
        assert p[pos].branch == exp["branch"], f"{v['id']} {pos} branch"
        assert p[pos].hidden_stems == e["hidden_stems"][pos], f"{v['id']} {pos} hidden"
        assert p[pos].nayin == e["nayin"][pos], f"{v['id']} {pos} nayin"

    exp_gods = {g["stem"]: g["ten_god"] for g in e["ten_gods"]}
    assert chart.ten_gods_map == exp_gods, f"{v['id']} ten_gods"

    exp_dayun = [
        (d["index"], d["start_age"], d["end_age"], d["stem"], d["branch"]) for d in e["dayun"]
    ]
    got_dayun = [(d.index, d.start_age, d.end_age, d.stem, d.branch) for d in chart.dayun]
    assert got_dayun == exp_dayun, f"{v['id']} dayun"

    assert chart.gender_assumed is e["gender_assumed"], f"{v['id']} gender_assumed"


def _by_id(vectors: list[dict], vid: str) -> dict:
    for v in vectors:
        if v["id"] == vid:
            return v
    raise AssertionError(f"vector {vid} missing")


def test_vector_count():
    data = _load()
    vectors = data["vectors"]
    assert len(vectors) == 24
    assert data["metadata"]["total_vectors"] == 24
    assert data["metadata"]["domain"] == "bazi"
    assert data["metadata"]["engine_version"] == "0.1.0"
    assert data["metadata"]["status"] == "candidate"
    ids = [v["id"] for v in vectors]
    assert len(set(ids)) == 24, "duplicate vector ids"


def test_determinism():
    for v in _vectors():
        a = BaziAgent().compute(_input_for(v)).result.model_dump(mode="json")
        b = BaziAgent().compute(_input_for(v)).result.model_dump(mode="json")
        assert a == b, f"{v['id']} not deterministic"


def test_serialization_stable():
    data = _load()
    s1 = json.dumps(data, ensure_ascii=False, sort_keys=True)
    s2 = json.dumps(data, ensure_ascii=False, sort_keys=True)
    assert s1 == s2
    assert json.loads(s1) == data


def test_vectors_match_engine():
    for v in _vectors():
        _assert_matches(v, _chart_for(v))


def test_boundary_regression():
    vectors = _vectors()

    lc_before = _by_id(vectors, "B_term_001")
    lc_after = _by_id(vectors, "B_term_002")
    assert lc_before["expected"]["year_pillar"] == {"stem": "癸", "branch": "卯"}
    assert lc_after["expected"]["year_pillar"] == {"stem": "甲", "branch": "辰"}

    late1 = _by_id(vectors, "B_late_001")
    late2 = _by_id(vectors, "B_late_002")
    late3 = _by_id(vectors, "B_late_003")
    assert late1["expected"]["hour_pillar"]["branch"] == "亥"
    assert late2["expected"]["hour_pillar"]["branch"] == "子"
    assert late1["expected"]["day_pillar"] != late2["expected"]["day_pillar"]
    assert late2["expected"]["day_pillar"] == late3["expected"]["day_pillar"]
    assert late1["input"]["born_at"].endswith("22:59:00+08:00")
    assert late2["input"]["born_at"].endswith("23:00:00+08:00")

    x5 = _by_id(vectors, "B_dayun_004")
    frac = _by_id(vectors, "B_dayun_005")
    assert x5["expected"]["dayun"][0]["start_age"] == 2, "round(1.5)=2 banker's"
    assert frac["expected"]["dayun"][0]["start_age"] == 1, "round(1.333)=1"

    # live engine agreement on the boundary cases
    _assert_matches(lc_before, _chart_for(lc_before))
    _assert_matches(x5, _chart_for(x5))


def test_coverage_completeness():
    covered: set[str] = set()
    for v in _vectors():
        covered.update(v["coverage"])
    assert {"B1", "B2", "B3", "B4", "B5", "B6"} <= covered


def test_gender_unknown_locked():
    unk = _by_id(_vectors(), "B_dayun_003")
    male = _by_id(_vectors(), "B_dayun_001")
    assert unk["input"]["gender"] == "unknown"
    assert unk["expected"]["gender_assumed"] is True
    assert unk["expected"]["dayun"] == male["expected"]["dayun"], "UNKNOWN must follow male path"
