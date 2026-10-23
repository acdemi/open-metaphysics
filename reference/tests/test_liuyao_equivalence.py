"""Production ↔ Reference Liuyao equivalence proof (Phase B contractization).

Runs the same inputs through:

1. Production Runtime  (src/openmetaphysics/agents/liuyao.py)
2. Reference Runtime   (reference/liuyao/domain.py, self-contained)

and compares the full chart JSON byte-for-byte. Also guards the reference
tables against drift from the shared metaphysics tables.

This file is an equivalence harness, so (like reference/tests/test_equivalence.py
for Qimen) it is allowed to import both sides. The Reference source independence
is asserted from within it.
"""

from __future__ import annotations

import json
import random
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput
from reference.liuyao import compute as reference_compute

ROOT = Path(__file__).resolve().parents[2]
VECTOR_FILE = ROOT / "docs" / "liuyao" / "golden_vectors.json"
REFERENCE_SOURCES = [
    ROOT / "reference" / "liuyao" / "domain.py",
    ROOT / "reference" / "liuyao" / "tables.py",
    ROOT / "reference" / "liuyao" / "astronomy.py",
]

_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+openmetaphysics", re.MULTILINE)

SEED = 20260916
GENERATED = 40


def _canonical(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def _production(vector_input: dict) -> dict:
    payload = LiuyaoInput(
        request_id="eq",
        born_at=datetime.fromisoformat(vector_input["born_at"]),
        casts=vector_input["casts"],
        question=vector_input.get("question"),
        seed=vector_input.get("seed"),
    )
    return LiuyaoAgent().compute(payload).result.model_dump()


def _both(vector_input: dict) -> tuple[str, str]:
    return _canonical(_production(vector_input)), _canonical(reference_compute(vector_input))


def _vectors() -> list[dict]:
    return json.loads(VECTOR_FILE.read_text(encoding="utf-8"))["vectors"]


# == Independence ==


def test_reference_source_is_independent_of_src():
    for path in REFERENCE_SOURCES:
        text = path.read_text(encoding="utf-8")
        assert not _IMPORT_RE.search(text), f"{path.name} imports openmetaphysics"


def test_reference_tables_match_production_tables():
    """The reference tables are a frozen copy; drift must be caught here."""
    from openmetaphysics.core import calendar as production_calendar
    from openmetaphysics.core import models as production_models
    from reference.liuyao import astronomy, tables

    assert tables.HEXAGRAMS == production_models.HEXAGRAMS
    assert tables.TRIGRAMS == production_models.TRIGRAMS
    assert tables.HEAVENLY_STEMS == production_models.HEAVENLY_STEMS
    assert tables.EARTHLY_BRANCHES == production_models.EARTHLY_BRANCHES
    assert tables.BRANCH_ELEMENT == production_models.BRANCH_ELEMENT
    assert tables.WUXING_SHENG == production_models.WUXING_SHENG
    assert tables.WUXING_KE == production_models.WUXING_KE

    assert astronomy.sexagenary_day_index(2024, 5, 1) == production_calendar.sexagenary_day_index(
        2024, 5, 1
    )
    assert astronomy.julian_day_number(1985, 8, 15) == production_calendar.julian_day_number(
        1985, 8, 15
    )


def test_reference_rejects_inputs_the_production_rejects():
    for casts in ([7] * 5, [5, 7, 7, 7, 7, 7], [7, 7, 7, 7, 7, 10]):
        with pytest.raises(ValueError):
            LiuyaoInput(request_id="x", born_at=datetime(2024, 5, 1), casts=casts)
        with pytest.raises(ValueError):
            reference_compute(
                {"born_at": "2024-05-01T12:00:00+00:00", "casts": casts, "question": None}
            )

    with pytest.raises(ValueError, match="timezone-aware"):
        LiuyaoInput(
            request_id="x",
            born_at=datetime(2024, 5, 1, 12),
            casts=[7] * 6,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        reference_compute(
            {"born_at": "2024-05-01T12:00:00", "casts": [7] * 6, "question": None}
        )


def test_auto_seed_path_is_outside_the_frozen_contract():
    """LC-D04: no casts/seed is intentionally outside the contract.

    Production may auto-seed for API convenience, but the Reference rejects it
    because the result is not guaranteed across processes (PYTHONHASHSEED).
    """
    payload = LiuyaoInput(
        request_id="auto",
        born_at=datetime(2024, 5, 1, 12, tzinfo=ZoneInfo("UTC")),
    )
    assert LiuyaoAgent().compute(payload).result.original_hexagram in range(1, 65)
    with pytest.raises(ValueError, match="explicit casts or an explicit seed"):
        reference_compute(
            {
                "born_at": "2024-05-01T12:00:00+00:00",
                "casts": None,
                "question": None,
                "seed": None,
            }
        )


# == Equivalence ==


def test_all_golden_vectors_are_equivalent():
    mismatched: list[str] = []
    checked = 0
    for vector in _vectors():
        if vector["input"].get("casts") is None and vector["input"].get("seed") is None:
            continue
        if vector.get("expected_error"):
            continue
        production, reference = _both(vector["input"])
        checked += 1
        if production != reference:
            mismatched.append(vector["id"])
    assert checked >= 21, f"only {checked} vectors exercised"
    assert not mismatched, f"equivalence failure: {mismatched}"


def test_generated_inputs_are_equivalent():
    rng = random.Random(SEED)
    mismatched: list[str] = []
    for i in range(GENERATED):
        casts = [rng.choice([6, 7, 8, 9]) for _ in range(6)]
        year = rng.choice([2023, 2024, 2025])
        hour = rng.randrange(0, 24)
        minute = rng.choice([0, 15, 30, 45])
        tz = ZoneInfo(rng.choice(["UTC", "Asia/Shanghai"]))
        vector_input = {
            "born_at": datetime(year, 5, 1, hour, minute, tzinfo=tz).isoformat(),
            "casts": casts,
            "question": rng.choice([None, "财运", "事业升迁", "考试结果", "出行平安", "婚姻"]),
        }
        production, reference = _both(vector_input)
        if production != reference:
            mismatched.append(f"case#{i}")
    print(f"[Liuyao Equivalence] {GENERATED - len(mismatched)}/{GENERATED} inputs byte-identical")
    assert not mismatched, f"equivalence failure: {mismatched}"


def test_seeded_casting_path_is_equivalent():
    for seed in (0, 1, 12345, 2**31 - 1):
        vector_input = {
            "born_at": "2024-05-01T12:00:00+00:00",
            "casts": None,
            "question": None,
            "seed": seed,
        }
        production, reference = _both(vector_input)
        assert production == reference, f"seeded casting differs for seed={seed}"


def test_day_rollover_boundary_is_equivalent():
    for iso in (
        "2024-05-01T22:59:00+00:00",
        "2024-05-01T23:00:00+00:00",
        "2024-05-01T23:30:00+00:00",
        "2024-05-02T00:00:00+00:00",
        "2023-12-31T23:30:00+00:00",
    ):
        vector_input = {"born_at": iso, "casts": [6, 7, 8, 9, 6, 7], "question": None}
        production, reference = _both(vector_input)
        assert production == reference, iso
