"""H6 regression: measured solar-term precision, honest claims, boundary behaviour.

Review H6: ``core/calendar.py`` claimed "~0.01 deg (well under a minute)", but
0.01 deg of solar longitude is ~14.6 minutes of time and the measured difference
against the high-precision 寿星天文历 reference (``sxtwl``, already a runtime
dependency for ``solar_to_lunar``) is a median ~180 s with a measured worst case
of 780.6 s over 1900-2100. The declaration and the BaZi metadata now state that
measured bound instead of the wrong sub-minute claim.

No library was added: ``sxtwl`` (BSD, ~0.5 MB compiled extension, offline) is
used as the test oracle only.
"""

from __future__ import annotations

import statistics
from datetime import datetime, timedelta, timezone

import sxtwl

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.agents.qimen import QimenAgent, QimenInput
from openmetaphysics.core.calendar import (
    SOLAR_TERM_MAX_ERROR_SECONDS,
    SOLAR_TERM_PRECISION,
    SOLAR_TERM_TYPICAL_ERROR_SECONDS,
    bazi_year_index,
    lichun_time,
    solar_term_time,
)
from openmetaphysics.core.models import SOLAR_TERMS_24
from openmetaphysics.core.schemas import Gender

# sxtwl's 24 jieqi indices, starting at 冬至 (index 0) like its C++ backend.
SXTWL_ORDER = [
    "冬至",
    "小寒",
    "大寒",
    "立春",
    "雨水",
    "惊蛰",
    "春分",
    "清明",
    "谷雨",
    "立夏",
    "小满",
    "芒种",
    "夏至",
    "小暑",
    "大暑",
    "立秋",
    "处暑",
    "白露",
    "秋分",
    "寒露",
    "霜降",
    "立冬",
    "小雪",
    "大雪",
]
TARGET_LON = {name: lon for name, _is_jie, lon in SOLAR_TERMS_24}
BEIJING = timezone(timedelta(hours=8))


def _sxtwl_terms(year: int) -> dict[str, datetime]:
    """High-precision solar-term times for ``year`` (converted to UTC)."""
    out: dict[str, datetime] = {}
    first = datetime(year, 1, 1)
    for offset in range(367):
        day = first + timedelta(days=offset)
        if day.year != year:
            break
        obj = sxtwl.fromSolar(day.year, day.month, day.day)
        if not obj.hasJieQi():
            continue
        detail = sxtwl.JD2DD(obj.getJieQiJD())
        local = datetime(int(detail.Y), int(detail.M), int(detail.D), tzinfo=BEIJING) + timedelta(
            hours=float(detail.h), minutes=float(detail.m), seconds=float(detail.s)
        )
        out[SXTWL_ORDER[obj.getJieQi()]] = local.astimezone(timezone.utc)
    return out


def _bazi(born_at: datetime):
    return (
        BaziAgent().compute(BaziInput(request_id="h6", born_at=born_at, gender=Gender.MALE)).result
    )


def _qimen(born_at: datetime):
    return (
        QimenAgent()
        .compute(QimenInput(request_id="h6", born_at=born_at, gender=Gender.UNKNOWN))
        .result
    )


# -- measured error vs the high-precision reference -------------------------


def test_truncated_series_stays_within_declared_error_bound():
    """Full 1900-2100 x 24 terms sweep: measured error <= declared bound."""
    errors: list[float] = []
    for year in range(1900, 2101):
        reference = _sxtwl_terms(year)
        for name, longitude in TARGET_LON.items():
            ours = solar_term_time(year, longitude)
            errors.append(abs((ours - reference[name]).total_seconds()))

    worst = max(errors)
    assert len(errors) == 201 * 24 == 4824
    assert worst <= SOLAR_TERM_MAX_ERROR_SECONDS, (
        f"measured worst {worst:.1f}s exceeds declared bound {SOLAR_TERM_MAX_ERROR_SECONDS}s"
    )
    median = statistics.median(errors)
    assert median <= SOLAR_TERM_TYPICAL_ERROR_SECONDS * 1.5, f"median drifted: {median:.1f}s"
    # The old "well under a minute" claim was wrong: the measured worst case is
    # itself larger than the +/-10 min boundary window the tests below probe.
    assert worst > 600, f"precision unexpectedly improved ({worst:.1f}s); update the claim"


def test_bazi_metadata_declares_the_measured_precision():
    output = BaziAgent().compute(
        BaziInput(
            request_id="h6-meta",
            born_at=datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc),
            gender=Gender.MALE,
        )
    )
    precision = output.metadata["solar_term_precision"]
    assert precision == SOLAR_TERM_PRECISION
    assert str(SOLAR_TERM_MAX_ERROR_SECONDS) in precision
    assert "approx_1min" not in precision
    assert "well under a minute" not in precision


# -- +/-10 minute boundaries ------------------------------------------------


def test_lichun_boundary_plus_minus_ten_minutes():
    boundary = lichun_time(2024)

    before = _bazi(boundary - timedelta(minutes=10))
    after = _bazi(boundary + timedelta(minutes=10))

    assert (before.pillars[0].stem, before.pillars[0].branch) != (
        after.pillars[0].stem,
        after.pillars[0].branch,
    )
    assert before.pillars[1].branch == "丑"  # 节 boundary: 丑月 before 立春
    assert after.pillars[1].branch == "寅"  # 寅月 from 立春 (inclusive)

    assert bazi_year_index(boundary - timedelta(minutes=10))[0] == (2023 - 4) % 60
    assert bazi_year_index(boundary + timedelta(minutes=10))[0] == (2024 - 4) % 60


def test_winter_solstice_boundary_plus_minus_ten_minutes():
    boundary = solar_term_time(2024, 270)  # 冬至

    assert _qimen(boundary - timedelta(minutes=10)).dun_type == "yin"
    assert _qimen(boundary).dun_type == "yang"  # 冬至(含) -> 阳遁
    assert _qimen(boundary + timedelta(minutes=10)).dun_type == "yang"


def test_spring_equinox_boundary_plus_minus_ten_minutes():
    boundary = solar_term_time(2024, 0)  # 春分

    before = _qimen(boundary - timedelta(minutes=10))
    after = _qimen(boundary + timedelta(minutes=10))

    assert before.solar_term == "惊蛰"
    assert after.solar_term == "春分"
    assert before.ju != after.ju  # 三元 base ju changes with the governing term
