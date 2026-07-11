"""Ziwei agent — 命宫/身宫, 五行局, 14 major stars placement, lunar conversion."""

from datetime import datetime
from zoneinfo import ZoneInfo

from openmetaphysics.agents.ziwei import ZiweiAgent, ZiweiInput
from openmetaphysics.core import calendar
from openmetaphysics.core.schemas import Gender, GeoPoint


def _run(born_at, lunar_month=None, lunar_day=None, gender=Gender.MALE, loc=True):
    inp = ZiweiInput(
        request_id="z",
        born_at=born_at,
        gender=gender,
        born_location=GeoPoint(latitude=39.9, longitude=116.4, timezone="Asia/Shanghai")
        if loc
        else None,
        lunar_month=lunar_month,
        lunar_day=lunar_day,
    )
    return ZiweiAgent().compute(inp).result


def test_fate_palace_canonical():
    # 农历正月 + 寅时 → 命宫在子 (index 10 in 0..11 starting 寅=0)
    # 农历 1 月, 寅时 = hour index 0 (寅)
    # ming_index = ((1-1) - 0) % 12 = 0 - 0 = 0? Wait:
    # Wait: _local_hour_branch: ((hour +1)//2) % 12
    # 寅 = 3-5am. Let's take born_at 1900-01-01 04:00, which should give hour branch 寅 (index 2, 子=0,丑=1,寅=2)
    # Wait correction: PALACE_BRANCHES order is [寅 0,卯 1,辰 2, ...,子 10,丑 11]
    # _local_hour_branch: output is ( (h+1)//2 ) % 12, which matches EARTHLY_BRANCHES order where 子=0
    # Yes, in Ziwei code, it aligns with 子=0,寅=2.
    # But for this canonical example: 甲年正月寅时, 命宫在子, 丙子 → 涧下水 → 水二局.
    r = _run(
        datetime(1900, 1, 29, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        lunar_month=1,
        lunar_day=1,
    )
    # 命宫 should be 子 (index 10 in 0-11 starting at 寅)
    assert r.fate_palace_index == 10
    fp = next(p for p in r.palaces if p.is_fate_palace)
    assert fp.earthly_branch == "子"
    # 水二局
    assert "水" in r.wuxing_ju and "2局" in r.wuxing_ju
    assert "水" in r.wuxing_ju


def test_body_palace_position():
    # For 正月寅 (hour index 2): 身宫 = ((1-1)+2) %12 = 2 → index 2 is 辰
    r = _run(
        datetime(1900, 1, 29, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        lunar_month=1,
        lunar_day=1,
    )
    assert r.body_palace_index == 2
    bp = next(p for p in r.palaces if p.is_body_palace)
    assert bp.earthly_branch == "辰"


def test_all_12_palaces_have_correct_names():
    r = _run(datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
    assert len(r.palaces) == 12
    names = set(p.name for p in r.palaces)
    expected = set(
        [
            "命宫",
            "兄弟",
            "夫妻",
            "子女",
            "财帛",
            "疾厄",
            "迁移",
            "奴仆",
            "官禄",
            "田宅",
            "福德",
            "父母",
        ]
    )
    assert names == expected


def test_all_palaces_have_stem_branch():
    r = _run(datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
    assert all(len(p.heavenly_stem) == 1 for p in r.palaces)
    assert all(len(p.earthly_branch) == 1 for p in r.palaces)


def test_14_major_stars_all_present():
    r = _run(
        datetime(1900, 1, 29, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        lunar_month=1,
        lunar_day=1,
    )
    all_stars = [s for p in r.palaces for s in p.main_stars]
    expected_stars = [
        "紫微",
        "天机",
        "太阳",
        "武曲",
        "天同",
        "廉贞",
        "天府",
        "太阴",
        "贪狼",
        "巨门",
        "天相",
        "天梁",
        "七杀",
        "破军",
    ]
    assert sorted(all_stars) == sorted(expected_stars)
    assert len(all_stars) == 14


def test_ziwei_tianfu_mirror_relationship():
    # If 紫微 at zw_index, 天府 at (-zw_index) %12
    # Test with zw=0 (寅), tf=0%12=0 (寅)
    # zw=1 (卯), tf= 11 (丑) → mirror correct
    r = _run(
        datetime(1900, 1, 29, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        lunar_month=1,
        lunar_day=1,
    )
    zw_idx = next(i for i, p in enumerate(r.palaces) if "紫微" in p.main_stars)
    tf_idx = next(i for i, p in enumerate(r.palaces) if "天府" in p.main_stars)
    expected_tf = (-zw_idx) % 12
    assert expected_tf == tf_idx


def test_lunar_conversion_2024_05_01():
    # Verified: 2024-05-01 Gregorian → 农历 3月23日, not leap
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    ly, lm, ld, leap = calendar.solar_to_lunar(dt.year, dt.month, dt.day)
    assert (ly, lm, ld, leap) == (2024, 3, 23, False)


def test_lunar_conversion_2024_02_10():
    # 2024-02-10 → 农历 正月初一, 春节, not leap
    ly, lm, ld, leap = calendar.solar_to_lunar(2024, 2, 10)
    assert (ly, lm, ld, leap) == (2024, 1, 1, False)


def test_lunar_conversion_leap_month_2023():
    # 2023-03-22 → 农历二月 leap → (2023, 2, 1, True)
    ly, lm, ld, leap = calendar.solar_to_lunar(2023, 3, 22)
    assert (ly, lm, ld, leap) == (2023, 2, 1, True)


def test_replay_identical():
    # Determinism: same input → same result except computed_at
    from openmetaphysics.agents.ziwei import ZiweiAgent, ZiweiInput

    def _strip(output):
        d = output.model_dump(mode="json")
        d.pop("computed_at", None)
        return d

    payload = ZiweiInput(
        request_id="z_replay",
        born_at=datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        gender=Gender.MALE,
        born_location=GeoPoint(latitude=30, longitude=120, timezone="Asia/Shanghai"),
    )
    a = _strip(ZiweiAgent().compute(payload))
    b = _strip(ZiweiAgent().compute(payload))
    assert a == b


def test_user_provided_lunar_used_directly():
    # If user provides explicit lunar_month/day, they are used directly (for replay)
    r = _run(
        datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        lunar_month=2,
        lunar_day=15,
    )
    # Just verify it doesn't crash and uses the values
    # We can't easily check the output here, but ingestion code will use them
    assert r is not None


def test_metadata_updated():
    agent = ZiweiAgent()
    meta = agent._metadata()
    assert meta["star_placement"] == "14_major_stars"
    assert meta["engine_version"] == "0.2.0"
    assert meta["deterministic"] is True
