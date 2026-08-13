"""Ziwei agent — 命宫/身宫, 五行局, 14 major stars placement, lunar conversion."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from openmetaphysics.agents.ziwei import (
    JU_NUMBER,
    PALACE_BRANCHES,
    PALACE_NAMES,
    TIANFU_XINGXI,
    ZIWEI_POS,
    ZIWEI_XINGXI,
    ZiweiAgent,
    ZiweiChart,
    ZiweiInput,
)
from openmetaphysics.core import calendar
from openmetaphysics.core.models import HEAVENLY_STEMS, nayin_for
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
    assert meta["engine_version"] == "0.3.0"
    assert meta["deterministic"] is True


# ---------------------------------------------------------------------------
# Phase 6.7.1 — 算法稳定化补测（全部确定性, 锁定当前行为; 不修改 src）
# ---------------------------------------------------------------------------


def test_ziwei_pos_table_structure():
    assert set(ZIWEI_POS) == {2, 3, 4, 5, 6}
    for _ju, days in ZIWEI_POS.items():
        assert set(days) == set(range(1, 31))
        for _day, idx in days.items():
            assert 0 <= idx <= 11


def test_ziwei_pos_values_snapshot():
    digest = hashlib.sha256(
        json.dumps(ZIWEI_POS, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()
    assert digest == "1cc796400c628e419e9942a2ddba236c77a95e4285fc1f94fcc9b4d057c44909"


def test_ziwei_tianfu_mirror_multiple_ju():
    anchors = [
        datetime(2024, 1, 1, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        datetime(2024, 6, 6, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        datetime(2024, 10, 3, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        datetime(2024, 8, 4, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        datetime(2024, 2, 5, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
    ]
    for dt in anchors:
        r = _run(dt)
        zw = next(p.index for p in r.palaces if "紫微" in p.main_stars)
        tf = next(p.index for p in r.palaces if "天府" in p.main_stars)
        assert tf == (-zw) % 12


def test_ziwei_xingxi_offsets():
    r = _run(
        datetime(1900, 1, 29, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        lunar_month=1,
        lunar_day=1,
    )
    zw = next(p.index for p in r.palaces if "紫微" in p.main_stars)
    for name, offset in ZIWEI_XINGXI:
        star_idx = next(p.index for p in r.palaces if name in p.main_stars)
        assert star_idx == (zw + offset) % 12


def test_tianfu_xingxi_offsets():
    r = _run(
        datetime(1900, 1, 29, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        lunar_month=1,
        lunar_day=1,
    )
    tf = next(p.index for p in r.palaces if "天府" in p.main_stars)
    for name, offset in TIANFU_XINGXI:
        star_idx = next(p.index for p in r.palaces if name in p.main_stars)
        assert star_idx == (tf + offset) % 12


def test_palace_stems_follow_wuhu_dun():
    dt = datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    r = _run(dt)
    year_idx, _ = calendar.bazi_year_index(dt)
    yin_month_stem = (year_idx % 10 * 2 + 2) % 10
    for p in r.palaces:
        assert p.heavenly_stem == HEAVENLY_STEMS[(yin_month_stem + p.index) % 10]


def test_palace_names_positions_mapping():
    r = _run(datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
    for p in r.palaces:
        assert p.earthly_branch == PALACE_BRANCHES[p.index]
        assert p.name == PALACE_NAMES[(r.fate_palace_index - p.index) % 12]


def test_ming_shen_formula_sweep():
    for month in range(1, 13):
        for hour_idx in range(12):
            hour = 22 if hour_idx == 11 else 2 * hour_idx
            r = _run(
                datetime(2024, 5, 1, hour, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
                lunar_month=month,
                lunar_day=15,
            )
            assert r.fate_palace_index == ((month - 1) - hour_idx) % 12
            assert r.body_palace_index == ((month - 1) + hour_idx) % 12


def test_wuxing_ju_all_five_elements():
    anchors = {
        "水2局": datetime(2024, 1, 1, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        "火6局": datetime(2024, 2, 5, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        "木3局": datetime(2024, 6, 6, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        "土5局": datetime(2024, 8, 4, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        "金4局": datetime(2024, 10, 3, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
    }
    for expected_ju, dt in anchors.items():
        assert _run(dt).wuxing_ju == expected_ju


def test_wuxing_ju_nayin_invariant():
    for dt in [
        datetime(2024, 1, 1, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        datetime(2024, 6, 6, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
    ]:
        r = _run(dt)
        fp = next(p for p in r.palaces if p.is_fate_palace)
        nayin = nayin_for(fp.heavenly_stem, fp.earthly_branch)
        assert r.wuxing_ju == f"{nayin[-1]}{JU_NUMBER[nayin[-1]]}局"


def test_yin_yang_year_stem():
    assert _run(datetime(1984, 6, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))).yin_yang == "yang"
    assert _run(datetime(1985, 6, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))).yin_yang == "yin"


def test_yin_yang_lichun_boundary():
    lc = calendar.lichun_time(2024)
    before = _run(lc - timedelta(hours=1))
    after = _run(lc + timedelta(hours=1))
    assert before.yin_yang == "yin"
    assert after.yin_yang == "yang"


def test_hour_window_boundary_2259_vs_2300():
    before = _run(datetime(1985, 8, 15, 22, 59, tzinfo=ZoneInfo("Asia/Shanghai")))
    after = _run(datetime(1985, 8, 15, 23, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
    assert before.fate_palace_index == 6 and before.wuxing_ju == "水2局"
    assert after.fate_palace_index == 5 and after.wuxing_ju == "木3局"


def test_timezone_changes_fate_palace():
    instant = datetime(1985, 8, 15, 2, 0, tzinfo=timezone.utc)
    sh = ZiweiInput(
        request_id="z",
        born_at=instant,
        gender=Gender.MALE,
        born_location=GeoPoint(latitude=39.9, longitude=116.4, timezone="Asia/Shanghai"),
    )
    utc = ZiweiInput(
        request_id="z",
        born_at=instant,
        gender=Gender.MALE,
        born_location=GeoPoint(latitude=51.5, longitude=0.0, timezone="UTC"),
    )
    r_sh = ZiweiAgent().compute(sh).result
    r_utc = ZiweiAgent().compute(utc).result
    assert r_sh.fate_palace_index != r_utc.fate_palace_index


def test_no_location_uses_born_tzinfo():
    born = datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    with_loc = ZiweiInput(
        request_id="z",
        born_at=born,
        gender=Gender.MALE,
        born_location=GeoPoint(latitude=39.9, longitude=116.4, timezone="Asia/Shanghai"),
    )
    without_loc = ZiweiInput(request_id="z", born_at=born, gender=Gender.MALE)
    a = ZiweiAgent().compute(with_loc).result.model_dump(mode="json")
    b = ZiweiAgent().compute(without_loc).result.model_dump(mode="json")
    assert a == b


def test_timezone_invalid_fallback():
    born = datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    bad = ZiweiInput(
        request_id="z",
        born_at=born,
        gender=Gender.MALE,
        born_location=GeoPoint(latitude=1.0, longitude=2.0, timezone="Not/AZone"),
    )
    plain = ZiweiInput(request_id="z", born_at=born, gender=Gender.MALE)
    a = ZiweiAgent().compute(bad).result.model_dump(mode="json")
    b = ZiweiAgent().compute(plain).result.model_dump(mode="json")
    assert a == b


def test_leap_month_placement_uses_month_number():
    r = _run(datetime(2023, 3, 22, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
    assert r.calendar_note is not None and "leap month 2" in r.calendar_note
    assert r.fate_palace_index == ((2 - 1) - 6) % 12


def test_user_lunar_override_flows_into_placement():
    r = _run(
        datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        lunar_month=2,
        lunar_day=15,
    )
    ju = JU_NUMBER[r.wuxing_ju[0]]
    zw = next(p.index for p in r.palaces if "紫微" in p.main_stars)
    assert zw == ZIWEI_POS[ju][15]


def test_lunar_input_out_of_range_rejected():
    # ACP-ZW-003: explicit validation — invalid lunar inputs raise ValueError
    # (pydantic ValidationError is a ValueError subclass), not KeyError.
    base = dict(
        request_id="z",
        born_at=datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        gender=Gender.MALE,
    )
    with pytest.raises(ValueError):
        ZiweiInput(**base, lunar_month=2, lunar_day=31)
    with pytest.raises(ValueError):
        ZiweiInput(**base, lunar_month=2, lunar_day=0)
    with pytest.raises(ValueError):
        ZiweiInput(**base, lunar_month=13, lunar_day=15)
    with pytest.raises(ValueError):
        ZiweiInput(**base, lunar_month=0, lunar_day=15)
    with pytest.raises(ValueError):
        ZiweiInput(**base, lunar_month=2)
    with pytest.raises(ValueError):
        ZiweiInput(**base, lunar_day=15)
    ZiweiInput(**base, lunar_month=2, lunar_day=15)  # valid combination accepted


def test_aux_stars_always_empty():
    for dt in [
        datetime(2024, 1, 1, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        datetime(2024, 6, 6, 4, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
    ]:
        assert all(p.auxiliary_stars == [] for p in _run(dt).palaces)


def test_output_serialization_roundtrip():
    out = ZiweiAgent().compute(
        ZiweiInput(
            request_id="z",
            born_at=datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
            gender=Gender.MALE,
        )
    )
    dumped = out.model_dump(mode="json")
    json.loads(json.dumps(dumped, ensure_ascii=False))
    assert ZiweiChart(**dumped["result"]).model_dump(mode="json") == dumped["result"]
