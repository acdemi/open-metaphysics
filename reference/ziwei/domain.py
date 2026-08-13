"""Reference Ziwei domain logic (independent implementation).

Implements docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT_DRAFT.md clauses BC-001~014.
Every computation step cites its contract clause. No src/ imports;
shared normative primitives are reused from reference/bazi/* with
explicit citations (BC-006: year stem Lichun boundary).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel, model_validator

from reference.bazi.astronomy import bazi_year_index  # BC-006: shared Lichun primitive
from reference.bazi.tables import HEAVENLY_STEMS, STEM_YIN_YANG, nayin_for  # shared tables

from .astronomy import solar_to_lunar  # BC-005: sxtwl==2.0.7
from .tables import (
    JU_NUMBER,
    PALACE_BRANCHES,
    PALACE_NAMES,
    TIANFU_XINGXI,
    ZIWEI_XINGXI,
    ziwei_index,
)


class ZiweiReferenceInput(BaseModel):
    """BC-002 (ZW-001): input schema mirroring the contract field set."""

    model_config = {"extra": "forbid"}

    request_id: str
    born_at: datetime  # must be tz-aware (BC-002 precondition)
    born_location: dict[str, Any] | None = None
    gender: str = "unknown"  # never read by the engine (BC-013 boundary)
    question: str | None = None
    locale: str = "zh-CN"
    seed: int | None = None
    client_nonce: str | None = None
    lunar_month: int | None = None  # 1..12; None -> compute from solar date
    lunar_day: int | None = None  # 1..30; None -> compute from solar date

    @model_validator(mode="after")
    def _validate_lunar_fields(self) -> ZiweiReferenceInput:
        # BC-002 (ZW-001, ACP-ZW-003): explicit validation --
        # both-or-neither provision, month in [1,12], day in [1,30].
        if (self.lunar_month is None) != (self.lunar_day is None):
            raise ValueError("lunar_month and lunar_day must be provided together")
        if self.lunar_month is not None and not 1 <= self.lunar_month <= 12:
            raise ValueError("lunar_month must be in 1..12")
        if self.lunar_day is not None and not 1 <= self.lunar_day <= 30:
            raise ValueError("lunar_day must be in 1..30")
        return self


def _local_tz(payload: ZiweiReferenceInput):
    """BC-003 (ZW-002): two-level timezone chain, silent fallback.

    born_location.timezone (ZoneInfo) -> born_at.tzinfo. No UTC fallback;
    an invalid timezone string silently falls back to born_at.tzinfo
    (D-ZW-2 / A-4 policy).
    """
    loc = payload.born_location
    if loc and loc.get("timezone"):
        try:
            return ZoneInfo(loc["timezone"])
        except Exception:
            return payload.born_at.tzinfo
    return payload.born_at.tzinfo


def _hour_branch(local_dt: datetime) -> int:
    """BC-004 (ZW-003): clock-time hour branch, 子时 = 23:00~00:59.

    No true solar time (difference vs Qimen D13 declared in contract).
    """
    return ((local_dt.hour + 1) // 2) % 12


def compute(payload: dict[str, Any] | ZiweiReferenceInput) -> dict[str, Any]:
    """Run the reference engine, returning the chart dict.

    Structurally identical to the contract ZiweiChart JSON; the 24 golden
    vectors must match byte-for-byte (test_ziwei_equivalence.py).
    """
    inp = payload if isinstance(payload, ZiweiReferenceInput) else ZiweiReferenceInput(**payload)
    # BC-002 precondition: born_at must be tz-aware.
    if inp.born_at.tzinfo is None:
        raise ValueError("born_at must be tz-aware")

    born = inp.born_at
    local_tz = _local_tz(inp)  # BC-003
    local = born.astimezone(local_tz)
    hour_idx = _hour_branch(local)  # BC-004
    calendar_note = None

    # BC-005 (ZW-004): lunar date - user override (BC-002) or sxtwl conversion.
    if inp.lunar_month is not None and inp.lunar_day is not None:
        month = inp.lunar_month
        day = inp.lunar_day
    else:
        _ly, lm, ld, leap = solar_to_lunar(local.year, local.month, local.day)
        month = lm
        day = ld
        if leap:
            # BC-005 (A-6): leap month keeps month number for placement,
            # recorded in calendar_note (byte-exact contract string).
            calendar_note = f"leap month {lm} (闰月) using month number {lm} for placement"

    # BC-008 (ZW-007/008): fate/body palaces from lunar month + hour branch.
    ming_index = ((month - 1) - hour_idx) % 12
    shen_index = ((month - 1) + hour_idx) % 12

    # BC-006 (ZW-005): year stem via shared Bazi Lichun primitive.
    year_idx, _ = bazi_year_index(born)
    year_stem_idx = year_idx % 10

    # BC-007 (ZW-006): WuHu Dun - 甲己起丙寅.
    yin_month_stem = (year_stem_idx * 2 + 2) % 10

    # BC-013 (ZW-016): yin/yang mark from year stem.
    yin_yang = "yang" if STEM_YIN_YANG[HEAVENLY_STEMS[year_stem_idx]] == "阳" else "yin"

    # BC-009 (ZW-009/010): fate palace stem + WuXing Ju via na-yin last char.
    ming_stem_idx = (yin_month_stem + ming_index) % 10
    ming_stem = HEAVENLY_STEMS[ming_stem_idx]
    ming_branch = PALACE_BRANCHES[ming_index]
    nayin = nayin_for(ming_stem, ming_branch)
    ju_elem = nayin[-1]
    ju = JU_NUMBER[ju_elem]
    wuxing_ju = f"{ju_elem}{ju}局"  # contract format "{元素}{数}局"

    # BC-010 (ZW-011): twelve palace layout.
    palaces: list[dict[str, Any]] = []
    for i in range(12):
        stem_idx = (yin_month_stem + i) % 10
        name = PALACE_NAMES[(ming_index - i) % 12]
        palaces.append(
            {
                "index": i,
                "name": name,
                "earthly_branch": PALACE_BRANCHES[i],
                "heavenly_stem": HEAVENLY_STEMS[stem_idx],
                "main_stars": [],
                "auxiliary_stars": [],  # BC-013 (ZW-017): always empty
                "is_fate_palace": (i == ming_index),
                "is_body_palace": (i == shen_index),
            }
        )

    # BC-011 (ZW-012, A-1): Ziwei placement via unified generative rule.
    zw_index = ziwei_index(ju, day)

    # BC-012 (ZW-013): Tianfu mirror across the 寅-申 axis.
    tf_index = (-zw_index) % 12

    # BC-012 (ZW-014): 紫微星系 first (fixed offset order).
    for name, offset in ZIWEI_XINGXI:
        palaces[(zw_index + offset) % 12]["main_stars"].append(name)

    # BC-012 (ZW-015): 天府星系 second (fixed offset order).
    for name, offset in TIANFU_XINGXI:
        palaces[(tf_index + offset) % 12]["main_stars"].append(name)

    return {
        "fate_palace_index": ming_index,
        "body_palace_index": shen_index,
        "yin_yang": yin_yang,
        "wuxing_ju": wuxing_ju,
        "palaces": palaces,
        "calendar_note": calendar_note,
    }


__all__ = ["ZiweiReferenceInput", "compute"]
