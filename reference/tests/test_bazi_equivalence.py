"""BaZi Reference equivalence tests (Phase 6.5 Task D).

Verifies for all 24 golden vectors:
- Production output == Reference output, exact structural equality
  (full chart: pillars all fields, dayun all fields, ten_gods_map,
   boundaries, day_master, gender_assumed). No fuzzy matching,
   no field omission.
- Reference source independence: no openmetaphysics imports.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.core.schemas import Gender, GeoPoint
from reference.bazi import compute as ref_compute

REPO_ROOT = Path(__file__).resolve().parents[2]
VECTOR_FILE = REPO_ROOT / "docs" / "bazi" / "golden_vectors.json"
REFERENCE_DIR = REPO_ROOT / "reference" / "bazi"

GENDER = {"male": Gender.MALE, "female": Gender.FEMALE, "unknown": Gender.UNKNOWN}


def _vectors() -> list[dict]:
    return json.loads(VECTOR_FILE.read_text(encoding="utf-8"))["vectors"]


def _production(v: dict) -> dict:
    inp = v["input"]
    tz = inp["born_location"]["timezone"]
    out = BaziAgent().compute(
        BaziInput(
            request_id="eq",
            born_at=datetime.fromisoformat(inp["born_at"]),
            gender=GENDER[inp["gender"]],
            born_location=GeoPoint(latitude=0.0, longitude=0.0, timezone=tz),
        )
    )
    return out.result.model_dump(mode="json")


def _reference(v: dict) -> dict:
    inp = v["input"]
    return ref_compute(
        {
            "born_at": datetime.fromisoformat(inp["born_at"]),
            "gender": inp["gender"],
            "born_location": {"timezone": inp["born_location"]["timezone"]},
        }
    )


def test_vector_count_24():
    vectors = _vectors()
    assert len(vectors) == 24


def test_equivalence_all_24_vectors():
    """Production == Reference for every vector, full-structure equality."""
    for v in _vectors():
        prod = _production(v)
        ref = _reference(v)
        assert prod == ref, (
            f"divergence at {v['id']}\n"
            f"production: {json.dumps(prod, ensure_ascii=False)}\n"
            f"reference : {json.dumps(ref, ensure_ascii=False)}"
        )


def test_equivalence_field_completeness():
    """No field may be omitted from the comparison surface."""
    prod = _production(_vectors()[0])
    expected_fields = {
        "day_master",
        "day_master_element",
        "pillars",
        "dayun",
        "ten_gods_map",
        "year_boundary",
        "month_boundary",
        "gender_assumed",
    }
    assert expected_fields <= set(prod), "production chart field surface changed"


def test_equivalence_pillar_fields():
    """Pillar sub-fields compared exhaustively (position/stem/branch/idx/hidden/nayin/ten_god)."""
    for v in _vectors():
        prod = _production(v)
        ref = _reference(v)
        for pp, rp in zip(prod["pillars"], ref["pillars"], strict=True):
            assert set(pp) == set(rp) and pp == rp, f"{v['id']} pillar mismatch"


def test_equivalence_dayun_fields():
    """Da Yun sub-fields compared exhaustively (index/ages/stem/branch/idx/start_at)."""
    for v in _vectors():
        prod = _production(v)
        ref = _reference(v)
        assert len(prod["dayun"]) == len(ref["dayun"]), f"{v['id']} dayun length"
        for pd, rd in zip(prod["dayun"], ref["dayun"], strict=True):
            assert set(pd) == set(rd) and pd == rd, f"{v['id']} dayun mismatch"


def test_reference_source_independent_of_src():
    """Reference implementation must not import openmetaphysics (independence)."""
    for py in REFERENCE_DIR.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        assert not re.search(r"^\s*(from|import)\s+openmetaphysics", text, re.MULTILINE), (
            f"production import found in {py}"
        )
