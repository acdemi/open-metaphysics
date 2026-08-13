"""BaZi white-box unit tests (Phase 6.4 Task A).

Closes the +14 gap from docs/bazi/BAZI_TEST_COVERAGE_REVIEW.md §4:
- 五虎遁 month stem (3)          G1
- 五鼠遁 hour stem (3)            G2
- Da Yun direction & rounding (4) G3/G4
- Timezone fallback (2)           G5/G6
- UNKNOWN gender (2)              G12/B6
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.core.models import sexagenary_index
from openmetaphysics.core.schemas import Gender, GeoPoint

CN8 = timezone(timedelta(hours=8))
SH = GeoPoint(latitude=39.9, longitude=116.4, timezone="Asia/Shanghai")


def _chart(dt: datetime, gender: Gender = Gender.MALE, loc: GeoPoint | None = SH):
    inp = BaziInput(request_id="wu", born_at=dt, gender=gender, born_location=loc)
    return BaziAgent().compute(inp).result


def _pillar(chart, pos):
    for p in chart.pillars:
        if p.position == pos:
            return p
    raise AssertionError(pos)


def _month_index(chart) -> int:
    m = _pillar(chart, "month")
    return sexagenary_index(m.stem, m.branch)


# ---------------------------------------------------------------------------
# 五虎遁 month stem (G1)
# ---------------------------------------------------------------------------


def test_wuhu_dun_jia_ji_year_bing_yin_month():
    """甲年(2024) 立春后 -> 丙寅月. 五虎遁: (甲0*2+2+0)%10 = 丙."""
    chart = _chart(datetime(2024, 2, 5, 10, 0, tzinfo=CN8))
    m = _pillar(chart, "month")
    assert m.stem == "丙" and m.branch == "寅"
    assert _pillar(chart, "year").stem == "甲"


def test_wuhu_dun_yi_geng_year_wu_yin_month():
    """乙年(2025) 立春后 -> 戊寅月. 五虎遁: (乙1*2+2)%10 = 戊."""
    chart = _chart(datetime(2025, 2, 5, 10, 0, tzinfo=CN8))
    m = _pillar(chart, "month")
    assert m.stem == "戊" and m.branch == "寅"
    assert _pillar(chart, "year").stem == "乙"


def test_wuhu_dun_bing_xin_year_geng_yin_month():
    """丙年(2026) 立春后 -> 庚寅月; 立春前(2025-02-01) 仍用上年甲干 -> 乙丑月."""
    after = _chart(datetime(2026, 2, 5, 10, 0, tzinfo=CN8))
    m = _pillar(after, "month")
    assert m.stem == "庚" and m.branch == "寅"
    assert _pillar(after, "year").stem == "丙"

    before = _chart(datetime(2025, 2, 1, 10, 0, tzinfo=CN8))
    mb = _pillar(before, "month")
    assert _pillar(before, "year").stem == "甲", "pre-Lichun year = previous year"
    assert mb.branch == "丑"
    assert mb.stem == "乙", "五虎遁 uses previous-year stem for 丑月"


# ---------------------------------------------------------------------------
# 五鼠遁 hour stem (G2)
# ---------------------------------------------------------------------------


def test_wushu_dun_jia_ji_day_jia_zi_hour():
    """己日(2024-03-16) 子时 -> 甲子. 五鼠遁: (己5*2+子0)%10 = 甲."""
    chart = _chart(datetime(2024, 3, 16, 0, 30, tzinfo=CN8))
    h = _pillar(chart, "hour")
    assert _pillar(chart, "day").stem == "己"
    assert h.stem == "甲" and h.branch == "子"


def test_wushu_dun_yi_geng_day_bing_zi_hour():
    """庚日(2024-03-17) 子时 -> 丙子. 五鼠遁: (庚6*2)%10 = 丙."""
    chart = _chart(datetime(2024, 3, 17, 0, 30, tzinfo=CN8))
    h = _pillar(chart, "hour")
    assert _pillar(chart, "day").stem == "庚"
    assert h.stem == "丙" and h.branch == "子"


def test_wushu_dun_bing_xin_day_wu_zi_hour():
    """辛日(2024-03-18) 子时 -> 戊子. 五鼠遁: (辛7*2)%10 = 戊."""
    chart = _chart(datetime(2024, 3, 18, 0, 30, tzinfo=CN8))
    h = _pillar(chart, "hour")
    assert _pillar(chart, "day").stem == "辛"
    assert h.stem == "戊" and h.branch == "子"


# ---------------------------------------------------------------------------
# Da Yun direction & rounding (G3/G4)
# ---------------------------------------------------------------------------


def _dayun_first(chart):
    d = chart.dayun[0]
    return d, sexagenary_index(d.stem, d.branch)


def test_dayun_forward_yang_male_yin_female():
    """阳年男(2024 甲辰) 与 阴年女(2025 乙巳) -> 顺排: dayun[0] = 月柱 +1 步."""
    yang_male = _chart(datetime(2024, 3, 15, 10, 0, tzinfo=CN8))
    d0, idx = _dayun_first(yang_male)
    assert idx == (_month_index(yang_male) + 1) % 60, "forward step"
    assert yang_male.dayun[1].start_age - d0.start_age == 10
    assert len(yang_male.dayun) == 8

    yin_female = _chart(datetime(2025, 2, 5, 10, 0, tzinfo=CN8), gender=Gender.FEMALE)
    d0, idx = _dayun_first(yin_female)
    assert idx == (_month_index(yin_female) + 1) % 60


def test_dayun_reverse_yin_male_yang_female():
    """阴年男(2025 乙巳) 与 阳年女(2024 甲辰) -> 逆排: dayun[0] = 月柱 -1 步."""
    yin_male = _chart(datetime(2025, 2, 5, 10, 0, tzinfo=CN8), gender=Gender.MALE)
    d0, idx = _dayun_first(yin_male)
    assert idx == (_month_index(yin_male) - 1) % 60

    yang_female = _chart(datetime(2024, 3, 15, 10, 0, tzinfo=CN8), gender=Gender.FEMALE)
    d0, idx = _dayun_first(yang_female)
    assert idx == (_month_index(yang_female) - 1) % 60


def test_dayun_bankers_rounding_x5():
    """距节 4.5 天 -> days/3 = 1.5 -> round(1.5) = 2 (banker's, 取偶)."""
    chart = _chart(datetime(2024, 3, 31, 2, 55, tzinfo=CN8))
    assert chart.dayun[0].start_age == 2
    assert round(1.5) == 2, "python banker's rounding semantics"


def test_dayun_fractional_floor():
    """距节 4 天 -> days/3 = 1.333 -> round = 1."""
    chart = _chart(datetime(2024, 3, 31, 14, 55, tzinfo=CN8))
    assert chart.dayun[0].start_age == 1
    assert round(1.333) == 1


# ---------------------------------------------------------------------------
# Timezone fallback (G5/G6)
# ---------------------------------------------------------------------------


def test_timezone_valid_offset():
    """born_at UTC + born_location Asia/Shanghai -> 本地 10:00 -> 巳时."""
    chart = _chart(
        datetime(2024, 3, 15, 2, 0, tzinfo=timezone.utc),
        loc=GeoPoint(latitude=39.9, longitude=116.4, timezone="Asia/Shanghai"),
    )
    h = _pillar(chart, "hour")
    assert h.branch == "巳"
    d = _pillar(chart, "day")
    assert d.stem + d.branch == "戊寅"


def test_timezone_invalid_fallback(caplog):
    """无效时区 -> 静默回退 born_at.tzinfo (UTC) -> 本地 02:00 -> 丑时."""
    chart = _chart(
        datetime(2024, 3, 15, 2, 0, tzinfo=timezone.utc),
        loc=GeoPoint(latitude=0.0, longitude=0.0, timezone="Bad/Zone"),
    )
    h = _pillar(chart, "hour")
    assert h.branch == "丑", "fallback to born_at.tzinfo (UTC)"
    assert not caplog.records, "fallback is silent (no warning emitted)"


# ---------------------------------------------------------------------------
# UNKNOWN gender (G12 / B6)
# ---------------------------------------------------------------------------


def test_unknown_gender_default_fallback_male():
    """gender 缺省(=UNKNOWN) -> 按男处理 + gender_assumed=True."""
    inp = BaziInput(
        request_id="wu",
        born_at=datetime(2024, 3, 15, 10, 0, tzinfo=CN8),
        born_location=SH,
    )
    assert inp.gender == Gender.UNKNOWN, "schema default is UNKNOWN"
    out = BaziAgent().compute(inp).result
    assert out.gender_assumed is True
    male = _chart(datetime(2024, 3, 15, 10, 0, tzinfo=CN8), gender=Gender.MALE)
    assert [d.start_age for d in out.dayun] == [d.start_age for d in male.dayun]


def test_unknown_gender_explicit_flag():
    """显式 Gender.UNKNOWN -> 大运与 male 一致 + gender_assumed 标记."""
    chart = _chart(datetime(2024, 3, 15, 10, 0, tzinfo=CN8), gender=Gender.UNKNOWN)
    male = _chart(datetime(2024, 3, 15, 10, 0, tzinfo=CN8), gender=Gender.MALE)
    assert chart.gender_assumed is True
    assert [d.start_age for d in chart.dayun] == [d.start_age for d in male.dayun]
    assert [d.stem for d in chart.dayun] == [d.stem for d in male.dayun]
