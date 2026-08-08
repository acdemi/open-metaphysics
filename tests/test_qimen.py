"""奇门遁甲 — 时家奇门排盘 tests.

原有 10 个测试保留; 新增测试覆盖 阳遁/阴遁/节气边界/1~9 局/值符值使/
空亡/九宫完整性/确定性, 以及 Golden Vectors (来自实际确定性计算结果,
经人工按通行转盘法核验, 标记为 implementation assumption)。
"""

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from openmetaphysics.agents.qimen import (
    DOOR_PALACES,
    EIGHT_DOORS,
    EIGHT_GODS,
    NINE_STARS,
    QimenAgent,
    QimenInput,
    branch_to_palace,
    build_palaces,
    dun_type_and_base_ju,
    earth_placement,
    effective_hour,
    hour_branch_index,
    sexagenary_hour_index,
    void_branch_indices,
    xun_shou_liuyi,
)
from openmetaphysics.core.calendar import solar_term_time
from openmetaphysics.core.models import SOLAR_TERMS_24
from openmetaphysics.core.schemas import Gender, GeoPoint

SHANGHAI = ZoneInfo("Asia/Shanghai")
BEIJING = GeoPoint(latitude=39.9, longitude=116.4, timezone="Asia/Shanghai")

_SOLAR_TERM_NAMES = {name for name, _is_jie, _lon in SOLAR_TERMS_24}

_GOLDEN_PATH = Path(__file__).resolve().parent.parent / "docs" / "qimen" / "golden_vectors.json"


def _load_golden_vectors() -> dict:
    """加载规范化 Golden Vector 数据文件 (docs/qimen/golden_vectors.json)."""
    if not _GOLDEN_PATH.exists():
        raise FileNotFoundError(f"golden vectors missing: {_GOLDEN_PATH}")
    with open(_GOLDEN_PATH, encoding="utf-8") as f:
        return json.load(f)


def _vector_input(v: dict) -> QimenInput:
    """由向量 JSON 构造输入 (与记录完全一致)."""
    inp = dict(v["input"])
    inp["born_at"] = datetime.fromisoformat(inp["born_at"])
    inp["born_location"] = GeoPoint(**inp["born_location"])
    return QimenInput(**inp)


def _run(dt):
    inp = QimenInput(
        request_id="q",
        born_at=dt,
        gender=Gender.UNKNOWN,
        born_location=BEIJING,
    )
    return QimenAgent().compute(inp).result


def _run_raw(dt):
    inp = QimenInput(
        request_id="q",
        born_at=dt,
        gender=Gender.UNKNOWN,
        born_location=BEIJING,
    )
    return QimenAgent().compute(inp)


def test_has_all_9_palaces():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=SHANGHAI)
    r = _run(dt)
    assert len(r.cells) == 9
    assert all(p.palace >= 1 and p.palace <= 9 for p in r.cells)


def test_all_cells_have_required_fields():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=SHANGHAI)
    r = _run(dt)
    count_none = 0
    for p in r.cells:
        assert p.name in ["坎", "坤", "震", "巽", "中宫", "乾", "兑", "艮", "离"]
        assert p.nine_stars is not None
        if p.eight_gods is None:
            count_none += 1
    # 八神 has 8 gods for 9 palaces → exactly one palace has no eight god
    assert count_none == 1


def test_dun_type_boundary():
    # 冬至 2023-12-22 UTC → after winter solstice → yang dun
    dt = datetime(2023, 12, 23, 0, 0, tzinfo=timezone.utc)
    r = _run(dt)
    assert r.dun_type == "yang"

    # 夏至 2024-06-21 UTC → after summer solstice → yin dun
    dt = datetime(2024, 6, 22, 0, 0, tzinfo=timezone.utc)
    r = _run(dt)
    assert r.dun_type == "yin"


def test_ju_range():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=SHANGHAI)
    r = _run(dt)
    assert 1 <= r.ju <= 9


def test_triple_offset_correct():
    # day 1-10 → offset 0
    dt = datetime(2024, 5, 5, 12, 0, tzinfo=SHANGHAI)
    r = _run(dt)
    assert r.triple_offset == 0

    # day 11-20 → offset 3
    dt = datetime(2024, 5, 15, 12, 0, tzinfo=SHANGHAI)
    r = _run(dt)
    assert r.triple_offset == 3

    # day 21-30 → offset 6
    dt = datetime(2024, 5, 25, 12, 0, tzinfo=SHANGHAI)
    r = _run(dt)
    assert r.triple_offset == 6


def test_all_sky_plate_filled():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=SHANGHAI)
    r = _run(dt)
    sky_plates = [p.sky_plate for p in r.cells if p.sky_plate is not None]
    assert len(sky_plates) == 9
    # 乙丙丁戊己庚辛壬癸 → 9 distinct
    assert len(set(sky_plates)) == 9


def test_sanqi_detection():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=SHANGHAI)
    r = _run(dt)
    sanqi = [p.three_qi for p in r.cells if p.three_qi is not None]
    assert len(sanqi) == 3
    assert set(sanqi) == {"乙", "丙", "丁"}


def test_nine_stars_correct():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=SHANGHAI)
    r = _run(dt)
    stars = sorted(p.nine_stars for p in r.cells if p.nine_stars is not None)
    expected = sorted(["天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"])
    assert stars == expected


def test_determinism_replay():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=SHANGHAI)
    inp = QimenInput(
        request_id="q_replay",
        born_at=dt,
        gender=Gender.UNKNOWN,
    )
    from openmetaphysics.agents.qimen import QimenAgent

    def _strip(output):
        d = output.model_dump(mode="json")
        d.pop("computed_at", None)
        return d

    a = _strip(QimenAgent().compute(inp))
    b = _strip(QimenAgent().compute(inp))
    assert a == b


def test_metadata_correct():
    agent = QimenAgent()
    meta = agent._metadata()
    assert meta["deterministic"] is True
    assert meta["has_nine_stars"] is True
    assert meta["has_eight_doors"] is True
    assert meta["has_eight_gods"] is True


# ===========================================================================
# Golden Vectors (时家奇门 转盘法)
# 数据源: docs/qimen/golden_vectors.json (Phase 5.3 规范化, 21 向量,
# 每个向量含 input / expected_board / engine_version / rule_set_version /
# frozen_rules / deferred_rules / assumptions_reference)。
# 状态: candidate normative (非 Behavior Contract); 全部为实际确定性计算
# 产物, 关键向量经人工按通行转盘法核验。
# ===========================================================================

GOLDEN_DATA = _load_golden_vectors()
GOLDEN_VECTORS = GOLDEN_DATA["vectors"]
GOLDEN_CASES = [
    (v["id"], datetime.fromisoformat(v["input"]["born_at"]), v["expected_board"])
    for v in GOLDEN_VECTORS
]


def _board_json(r):
    return r.model_dump(mode="json")


def test_golden_vectors_full_board():
    for name, dt, expected in GOLDEN_CASES:
        r = _run(dt)
        assert _board_json(r) == expected, f"golden vector mismatch: {name}"


def test_golden_vector_yang_semantics():
    # 阳遁 7 局 立春 中元: 值符天柱(旬首甲子戊@兑七) 随时干庚落离九;
    # 值使惊门 随时支午 (步数 6) 落巽四; 甲子旬空亡戌亥 → 乾六宫。
    r = _run(datetime(2024, 2, 15, 12, 0, tzinfo=SHANGHAI))
    c = {p.palace: p for p in r.cells}
    assert r.dun_type == "yang" and r.ju == 7 and r.solar_term == "立春"
    assert c[9].eight_gods == "值符" and c[9].nine_stars == "天柱"
    assert c[4].eight_doors == "惊门"
    assert [p.palace for p in r.cells if p.is_void] == [6]


def test_golden_vector_yin_norotation_semantics():
    # 阴遁 7 局 立秋: 辛亥日午时 → 甲午时, 旬首甲午辛@离九,
    # 时干甲遁于辛 → 值符落离九, 天盘不转 (offset 0);
    # 甲午旬空亡辰巳 → 巽四宫。
    r = _run(datetime(2024, 8, 15, 12, 0, tzinfo=SHANGHAI))
    c = {p.palace: p for p in r.cells}
    assert r.dun_type == "yin" and r.ju == 7 and r.solar_term == "立秋"
    assert c[9].eight_gods == "值符" and c[9].nine_stars == "天英"
    assert c[9].eight_doors == "景门"
    assert all(c[p].sky_plate == c[p].earth_plate for p in range(1, 10))
    assert [p.palace for p in r.cells if p.is_void] == [4]


def test_golden_vector_yin_zhonggong_jigong_semantics():
    # 庚戌日丙子时 (甲戌旬): 时干丙所在地盘为中五宫, 值符落中宫 →
    # 八神值符寄坤二宫; 值使死门 (甲戌己@坤二) 逆行 2 步
    # (子时相对戌时) 落离九; 甲戌旬空亡申酉 → 坤二 + 兑七。
    r = _run(datetime(2024, 8, 14, 0, 30, tzinfo=SHANGHAI))
    c = {p.palace: p for p in r.cells}
    assert r.dun_type == "yin" and r.ju == 7
    assert c[2].eight_gods == "值符"  # 中宫寄坤二
    assert c[5].sky_plate == "己"  # 旬首己 天盘干落中宫 (值符宫)
    assert c[5].nine_stars == "天芮"  # 值符星落中宫 (天盘)
    assert c[9].eight_doors == "死门"
    assert sorted(p.palace for p in r.cells if p.is_void) == [2, 7]


# ---------------------------------------------------------------------------
# 节气边界: 阴阳遁切换 + 局数重算
# ---------------------------------------------------------------------------
def test_winter_solstice_boundary_switch():
    t = solar_term_time(2023, 270)  # 冬至 2023 (calendar, 独立于排盘实现)
    before = _run(t - timedelta(hours=1))
    after = _run(t + timedelta(hours=1))
    assert before.dun_type == "yin" and before.ju == 9  # 大雪 阴遁十二局 + 下元
    assert after.dun_type == "yang" and after.ju == 7  # 冬至 阳遁一局 + 下元


def test_summer_solstice_boundary_switch():
    t = solar_term_time(2024, 90)  # 夏至 2024
    before = _run(t - timedelta(hours=1))
    after = _run(t + timedelta(hours=1))
    assert before.dun_type == "yang" and before.ju == 6  # 芒种 阳遁十二局 + 中元
    assert after.dun_type == "yin" and after.ju == 4  # 夏至 阴遁一局 + 中元


# ---------------------------------------------------------------------------
# 1~9 局覆盖 (阳遁; 每局验证 局数/地盘/九宫完整性)
# ---------------------------------------------------------------------------
# (date, 期望局数): 局数 = ((节气基本局 - 1) + 三元偏移) % 9 + 1,
# 每个日期均先按该独立公式人工核算后再冻结。
JU_COVERAGE = [
    (datetime(2024, 5, 6, 12, 0, tzinfo=SHANGHAI), 1),  # 立夏 上元
    (datetime(2024, 1, 7, 12, 0, tzinfo=SHANGHAI), 2),  # 小寒 上元
    (datetime(2024, 6, 6, 12, 0, tzinfo=SHANGHAI), 3),  # 芒种 上元
    (datetime(2024, 2, 5, 12, 0, tzinfo=SHANGHAI), 4),  # 立春 上元
    (datetime(2024, 3, 1, 12, 0, tzinfo=SHANGHAI), 5),  # 雨水 上元
    (datetime(2024, 3, 6, 12, 0, tzinfo=SHANGHAI), 6),  # 惊蛰 上元
    (datetime(2024, 2, 11, 12, 0, tzinfo=SHANGHAI), 7),  # 立春 中元
    (datetime(2024, 4, 5, 12, 0, tzinfo=SHANGHAI), 8),  # 清明 上元
    (datetime(2024, 1, 21, 12, 0, tzinfo=SHANGHAI), 9),  # 大寒 下元
]


def test_ju_1_to_9_coverage():
    seen = set()
    for dt, expected_ju in JU_COVERAGE:
        r = _run(dt)
        assert r.dun_type == "yang"
        assert r.ju == expected_ju, f"ju mismatch for {dt}"
        seen.add(r.ju)
        # 地盘与独立纯函数一致
        earth = earth_placement("yang", r.ju)
        for cell in r.cells:
            assert cell.earth_plate == earth[cell.palace]
        assert len(r.cells) == 9
    assert seen == set(range(1, 10))


# ---------------------------------------------------------------------------
# 纯函数不变量 (独立于引擎)
# ---------------------------------------------------------------------------
def test_earth_placement_invariants():
    order = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
    for ju in range(1, 10):
        yang = earth_placement("yang", ju)
        assert set(yang.values()) == set(order)  # 六仪三奇集合完整
        for i, stem in enumerate(order):
            assert yang[(ju - 1 + i) % 9 + 1] == stem  # 阳遁: 戊在 ju 宫顺布
        yin = earth_placement("yin", ju)
        assert set(yin.values()) == set(order)
        for i, stem in enumerate(order):
            assert yin[((9 - ju) - i) % 9 + 1] == stem  # 阴遁: 戊在 (10-ju) 宫逆布


def test_hour_pillar_invariants():
    # 五鼠遁: 日干 → 子时天干
    for day_stem, _sub_gan in enumerate(["甲", "丙", "戊", "庚", "壬"]):
        start = (day_stem % 5) * 2
        for hb in range(12):
            idx = sexagenary_hour_index(day_stem, hb)
            assert idx % 12 == hb
            assert idx % 10 == (start + hb) % 10
    # 经典锚点: 甲日子时甲子(0), 己日午时庚午(6), 庚日子时丙子(12)
    assert sexagenary_hour_index(0, 0) == 0
    assert sexagenary_hour_index(5, 6) == 6
    assert sexagenary_hour_index(6, 0) == 12
    # 时支划分: 23/0 子, 12 午, 22 亥
    assert hour_branch_index(0) == 0 and hour_branch_index(23) == 0
    assert hour_branch_index(12) == 6
    assert hour_branch_index(22) == 11


def test_void_branch_invariants():
    # 六甲旬空亡 (独立干支规则)
    expected = {0: (10, 11), 10: (8, 9), 20: (6, 7), 30: (4, 5), 40: (2, 3), 50: (0, 1)}
    for shou, void in expected.items():
        for idx in range(shou, shou + 10):
            assert void_branch_indices(idx) == void, f"void mismatch for {idx}"
    # 支 → 宫: 子坎1, 丑艮8, 寅艮8, 辰巽4, 巳巽4, 午离9, 未坤2, 申坤2, 酉兑7, 戌乾6, 亥乾6
    for branch, palace in [
        (0, 1),
        (1, 8),
        (2, 8),
        (3, 3),
        (4, 4),
        (5, 4),
        (6, 9),
        (7, 2),
        (8, 2),
        (9, 7),
        (10, 6),
        (11, 6),
    ]:
        assert branch_to_palace(branch) == palace


def test_zhifu_zhishi_on_boards():
    # 值符 = 八神之首的落宫; 值使 = 值使门 (旬首宫地盘门) 落宫
    dt = datetime(2024, 2, 15, 12, 0, tzinfo=SHANGHAI)
    r = _run(dt)
    c = {p.palace: p for p in r.cells}
    zhi_fu_cell = next(p for p in r.cells if p.eight_gods == "值符")
    assert zhi_fu_cell.palace == 9  # 时干庚 地盘离九
    assert zhi_fu_cell.nine_stars == "天柱"  # 值符星 (旬首甲子戊@兑七 → 天柱)
    assert c[9].sky_plate == "戊"  # 值符宫天盘干 = 旬首仪戊
    zhishi_cell = next(p for p in r.cells if p.eight_doors == "惊门")
    assert zhishi_cell.palace == 4  # 值使随时支午 (6 步) 落巽四


# ---------------------------------------------------------------------------
# 空亡落宫
# ---------------------------------------------------------------------------
def test_void_palace_rule():
    # 甲子旬 → 戌亥 → 乾六宫
    r = _run(datetime(2024, 2, 15, 12, 0, tzinfo=SHANGHAI))
    assert [p.palace for p in r.cells if p.is_void] == [6]
    # 甲午旬 → 辰巳 → 巽四宫
    r = _run(datetime(2024, 8, 15, 12, 0, tzinfo=SHANGHAI))
    assert [p.palace for p in r.cells if p.is_void] == [4]
    # 甲戌旬 → 申酉 → 坤二 + 兑七
    r = _run(datetime(2024, 8, 14, 0, 30, tzinfo=SHANGHAI))
    assert sorted(p.palace for p in r.cells if p.is_void) == [2, 7]


# ---------------------------------------------------------------------------
# 九宫完整性
# ---------------------------------------------------------------------------
def test_nine_palace_completeness():
    for _name, dt, _expected in GOLDEN_CASES:
        r = _run(dt)
        assert len(r.cells) == 9
        palaces = [p.palace for p in r.cells]
        assert palaces == list(range(1, 10))  # 无遗漏、无重复
        assert {p.name for p in r.cells} == {"坎", "坤", "震", "巽", "中宫", "乾", "兑", "艮", "离"}
        # 中宫: 无八门八神, is_central
        central = next(p for p in r.cells if p.is_central)
        assert central.palace == 5 and central.eight_doors is None
        # 八门 8 个、八神 8 个、九星 9 个、天盘干 9 个、地盘干 9 个
        assert {p.eight_doors for p in r.cells if p.eight_doors} == set(EIGHT_DOORS.values()) - {
            None
        }
        assert {p.eight_gods for p in r.cells if p.eight_gods} == set(EIGHT_GODS)
        assert {p.nine_stars for p in r.cells} == set(NINE_STARS.values())
        assert {p.sky_plate for p in r.cells} == {
            "戊",
            "己",
            "庚",
            "辛",
            "壬",
            "癸",
            "丁",
            "丙",
            "乙",
        }
        assert {p.earth_plate for p in r.cells} == {
            "戊",
            "己",
            "庚",
            "辛",
            "壬",
            "癸",
            "丁",
            "丙",
            "乙",
        }


# ---------------------------------------------------------------------------
# 确定性 (字节级 JSON)
# ---------------------------------------------------------------------------
def test_determinism_json_bytes():
    dt = datetime(2024, 2, 15, 12, 0, tzinfo=SHANGHAI)
    a = _run_raw(dt)
    b = _run_raw(dt)

    def _stable(output):
        d = output.model_dump(mode="json")
        d.pop("computed_at", None)  # 信封时间戳非计算内容
        return json.dumps(d, ensure_ascii=False, sort_keys=True)

    assert _stable(a) == _stable(b)


# ===========================================================================
# 状态不变量 (Phase 5.1 Algorithm Stabilization Review)
# ===========================================================================
def _assert_board_state_valid(r, when):
    """九宫盘状态不变量: 完整性/唯一性/无非法宫状态。"""
    cells = r.cells
    assert len(cells) == 9, when
    assert [c.palace for c in cells] == list(range(1, 10)), when
    assert 1 <= r.ju <= 9, when
    assert r.triple_offset in (0, 3, 6), when
    assert r.dun_type in ("yang", "yin"), when
    assert r.solar_term in _SOLAR_TERM_NAMES, when  # 24 节气之一

    central = [c for c in cells if c.is_central]
    assert len(central) == 1 and central[0].palace == 5, when
    central_cell = central[0]
    # 仅中宫: 无八门/八神; 非中宫必须满布
    assert central_cell.eight_doors is None and central_cell.eight_gods is None, when
    for c in cells:
        if c.palace != 5:
            assert c.eight_doors is not None and c.eight_gods is not None, when
            assert c.name in ("坎", "坤", "震", "巽", "乾", "兑", "艮", "离"), when
        assert c.sky_plate is not None and c.earth_plate is not None, when
        assert c.nine_stars is not None, when

    # 符号唯一性 (互异且齐全)
    assert len({c.sky_plate for c in cells}) == 9, when
    assert len({c.earth_plate for c in cells}) == 9, when
    assert len({c.nine_stars for c in cells}) == 9, when
    assert len({c.eight_doors for c in cells if c.eight_doors}) == 8, when
    assert len({c.eight_gods for c in cells if c.eight_gods}) == 8, when

    # 空亡: 1~2 个宫, 且与旬空支映射一致
    void_palaces = [c.palace for c in cells if c.is_void]
    assert 1 <= len(void_palaces) <= 2, when
    assert all(p in DOOR_PALACES for p in void_palaces), when

    # 三奇: 恰为 乙丙丁 各一次
    sanqi = [c.three_qi for c in cells if c.three_qi is not None]
    assert set(sanqi) == {"乙", "丙", "丁"}, when


def test_invariant_sweep_full_year():
    """跨全年各月/各时辰的批量不变量扫描。"""
    hours = [0, 6, 12, 23]
    dates = [
        datetime(2023, 12, 23, 12, 0, tzinfo=SHANGHAI),
        datetime(2024, 1, 15, 12, 0, tzinfo=SHANGHAI),
        datetime(2024, 2, 15, 12, 0, tzinfo=SHANGHAI),
        datetime(2024, 3, 15, 12, 0, tzinfo=SHANGHAI),
        datetime(2024, 4, 15, 12, 0, tzinfo=SHANGHAI),
        datetime(2024, 5, 15, 12, 0, tzinfo=SHANGHAI),
        datetime(2024, 6, 15, 12, 0, tzinfo=SHANGHAI),
        datetime(2024, 7, 15, 12, 0, tzinfo=SHANGHAI),
        datetime(2024, 8, 15, 12, 0, tzinfo=SHANGHAI),
        datetime(2024, 9, 15, 12, 0, tzinfo=SHANGHAI),
        datetime(2024, 10, 15, 12, 0, tzinfo=SHANGHAI),
        datetime(2024, 11, 15, 12, 0, tzinfo=SHANGHAI),
        datetime(2024, 12, 15, 12, 0, tzinfo=SHANGHAI),
        datetime(2024, 12, 31, 23, 0, tzinfo=SHANGHAI),
    ]
    n = 0
    for base in dates:
        for h in hours:
            dt = base.replace(hour=h)
            r = _run(dt)
            _assert_board_state_valid(r, f"{dt.isoformat()}")
            n += 1
    assert n >= 50


def test_hour_plan_consistency():
    """build_palaces 的 HourPlan 与盘面自洽。"""
    for _name, dt, _expected in GOLDEN_CASES:
        utc = dt.astimezone(timezone.utc)
        dun_type, base_ju, _term = dun_type_and_base_ju(utc)
        cells, ju, triple_offset, plan = build_palaces(dun_type, base_ju, dt.date(), dt.hour)
        assert ju == _expected["ju"] and triple_offset == _expected["triple_offset"]
        earth = {c.palace: c.earth_plate for c in cells}
        # 旬首宫 = 旬首六仪在地盘之宫
        assert earth[plan.xun_palace] == xun_shou_liuyi(plan.hour_index)
        # 值符宫 (寄宫后) 不可能是中宫
        assert plan.zhi_fu_palace in DOOR_PALACES
        assert plan.zhi_shi_palace in DOOR_PALACES
        # 时干为甲 (旬首时辰) 时, 时干宫 = 旬首宫
        if plan.hour_stem == "甲":
            assert plan.hour_stem_palace == plan.xun_palace
        # 天盘: 值符宫天盘干 = 旬首仪
        sky = {c.palace: c.sky_plate for c in cells}
        assert sky[plan.hour_stem_palace] == xun_shou_liuyi(plan.hour_index)


def test_symbol_uniqueness():
    """符号唯一性: 每类符号在盘面中恰好出现一次。"""
    for _name, dt, _expected in GOLDEN_CASES:
        r = _run(dt)
        sky = [c.sky_plate for c in r.cells]
        earth = [c.earth_plate for c in r.cells]
        stars = [c.nine_stars for c in r.cells]
        doors = [c.eight_doors for c in r.cells if c.eight_doors]
        gods = [c.eight_gods for c in r.cells if c.eight_gods]
        assert len(set(sky)) == len(sky) == 9
        assert len(set(earth)) == len(earth) == 9
        assert len(set(stars)) == len(stars) == 9
        assert len(set(doors)) == len(doors) == 8
        assert len(set(gods)) == len(gods) == 8
        # 三奇落宫互异
        sanqi_cells = [c.palace for c in r.cells if c.three_qi is not None]
        assert len(sanqi_cells) == len(set(sanqi_cells)) == 3


# ===========================================================================
# 规则裁定回归 (Phase 5.2 — docs/qimen/QIMEN_RULE_DECISION.md)
# 冻结规则 (F1-F12) 的可观察行为; 修改冻结规则必须同步更新本测试与 Golden
# Vectors, 并递增 QimenEngine.version。
# ===========================================================================
def test_frozen_rule_regression():
    """逐条验证 12 项冻结规则的盘面表现。"""
    # F1 (D1) 阴阳遁: 冬至时刻(含)切换为阳遁, 夏至时刻(含)切换为阴遁 (UTC)
    t_ws = solar_term_time(2023, 270)
    assert _run(t_ws).dun_type == "yang"
    assert _run(t_ws - timedelta(minutes=1)).dun_type == "yin"

    # F2 (D3) 局数公式: 阳遁一局 = 冬至上元 (2024-01-01 甲子日, 日号 1 → 偏移 0)
    r = _run(datetime(2024, 1, 1, 8, 0, tzinfo=SHANGHAI))
    assert r.ju == 1 and r.triple_offset == 0 and r.dun_type == "yang"

    # F3 (D4) 地盘: 阳遁 n 局甲子戊在 n 宫; 阴遁 n 局甲子戊在 (10-n) 宫
    for ju in range(1, 10):
        assert earth_placement("yang", ju)[ju] == "戊"
        assert earth_placement("yin", ju)[((10 - ju) - 1) % 9 + 1] == "戊"

    # F4 (D5) 值符随时干: 戊辰时 (时干戊@坎一) → 值符落坎一, 天盘干=旬首仪戊
    c = {p.palace: p for p in r.cells}
    assert c[1].eight_gods == "值符" and c[1].sky_plate == "戊"
    assert c[1].nine_stars == "天蓬"  # 值符星 (甲子戊@坎一 → 天蓬)

    # F5 (D6) 天盘顺转: 时干宫=旬首宫 (甲子旬戊辰时) → offset 0, 天盘=地盘
    assert all(p.sky_plate == p.earth_plate for p in r.cells)

    # F6 (D7) 值使随时支 mod12 + 落中宫寄坤二: 甲子旬辰时 步数 4 →
    # 休门 坎一→…→中五 → 寄坤二宫
    assert c[2].eight_doors == "休门"

    # F7 (D8) 天禽参与转盘: G1 (阳遁7局, offset 2) 天禽@兑七
    g1 = _run(datetime(2024, 2, 15, 12, 0, tzinfo=SHANGHAI))
    assert {p.palace: p for p in g1.cells}[7].nine_stars == "天禽"

    # F8 (D9) 八门洛书序顺布 (跳过中宫): 中宫无门, 非中宫全有门
    assert c[5].eight_doors is None
    assert all(p.eight_doors is not None for p in r.cells if p.palace != 5)

    # F9 (D10) 八神顺布 (阴阳遁同向): G3 值符@坤二 → 螣蛇@震三 → 太阴@巽四 …
    g3 = _run(datetime(2024, 8, 14, 0, 30, tzinfo=SHANGHAI))
    gods = {p.palace: p.eight_gods for p in g3.cells}
    god_start = DOOR_PALACES.index(2)  # 坤二在八宫环中的位置
    expect_gods = {DOOR_PALACES[(god_start + i) % 8]: god for i, god in enumerate(EIGHT_GODS)}
    assert all(gods[p] == god for p, god in expect_gods.items())

    # F10 (D11) 空亡: 甲子旬 → 戌亥 → 乾六宫
    assert [p.palace for p in r.cells if p.is_void] == [6]

    # F11 (D12) 中宫寄坤二: 值使落中宫寄坤二 (F6 同用例); 值符落中宫寄坤二 (G3)
    assert gods[2] == "值符"

    # F12 (D13) 真太阳时定时辰: 北京 2024-02-15 11:20 → 真太阳时 巳时;
    # 无坐标时回退钟表时 午时
    dt2 = datetime(2024, 2, 15, 11, 20, tzinfo=SHANGHAI)
    with_loc = QimenInput(
        request_id="f12a", born_at=dt2, gender=Gender.UNKNOWN, born_location=BEIJING
    )
    no_loc = QimenInput(request_id="f12b", born_at=dt2, gender=Gender.UNKNOWN)
    assert effective_hour(with_loc) == 10  # 巳时
    assert effective_hour(no_loc) == 11  # 午时


# ===========================================================================
# Golden 元数据校验 (Phase 5.3)
# 每个向量的 input / engine_version / rule_set_version / frozen_rules /
# deferred_rules / assumptions_reference 一致性。
# ===========================================================================


def test_golden_metadata_validation():
    """每个 Golden Vector 的输入/版本/规则集/假设出处一致性。"""
    assert GOLDEN_DATA["engine_version"] == GOLDEN_DATA["rule_set_version"]
    for v in GOLDEN_VECTORS:
        vid = v["id"]
        # 向量内元数据与数据文件头一致
        assert v["engine_version"] == GOLDEN_DATA["engine_version"], vid
        assert v["rule_set_version"] == GOLDEN_DATA["rule_set_version"], vid
        assert v["frozen_rules"] == GOLDEN_DATA["frozen_rules"], vid
        assert v["deferred_rules"] == GOLDEN_DATA["deferred_rules"], vid
        assert v["assumptions_reference"].startswith("docs/qimen/"), vid
        assert v["decision_reference"].startswith("docs/qimen/"), vid
        assert v["classification"] in ("regression", "candidate_normative", "normative_fixture"), (
            vid
        )
        # 输入必须可复现: 相同输入 → 相同 output 与 input_hash
        out1 = QimenAgent().compute(_vector_input(v))
        out2 = QimenAgent().compute(_vector_input(v))
        assert out1.input_hash == out2.input_hash, vid
        assert out1.engine_version == v["engine_version"], vid
        assert out1.metadata["method"] == "zhuanpan", vid
        assert out1.metadata["placement"] == "full_shibapan", vid
        # 盘面头部与 expected_board 一致
        r1 = out1.result
        assert r1.ju == v["expected_board"]["ju"], vid
        assert r1.dun_type == v["expected_board"]["dun_type"], vid
        assert r1.solar_term == v["expected_board"]["solar_term"], vid
        assert r1.day_of_month == v["expected_board"]["day_of_month"], vid
        assert r1.triple_offset == v["expected_board"]["triple_offset"], vid


# ===========================================================================
# Golden Vector 数量与覆盖 (Phase 5.3)
# ===========================================================================
def test_golden_vector_count():
    """向量数量: 至少 3 (既有) + 8 (新增) = 11; 覆盖 阳遁 1-9 局与阴遁 ≥3 局。"""
    assert len(GOLDEN_VECTORS) >= 11
    yang_ju = {
        v["expected_board"]["ju"]
        for v in GOLDEN_VECTORS
        if v["expected_board"]["dun_type"] == "yang"
    }
    yin_ju = {
        v["expected_board"]["ju"]
        for v in GOLDEN_VECTORS
        if v["expected_board"]["dun_type"] == "yin"
    }
    assert yang_ju == set(range(1, 10)), f"yang ju coverage: {sorted(yang_ju)}"
    assert len(yin_ju) >= 3, f"yin ju coverage: {sorted(yin_ju)}"
    # 关键覆盖标签齐备
    tags = {t for v in GOLDEN_VECTORS for t in v["coverage"]}
    for required in (
        "winter_solstice",
        "summer_solstice_before",
        "summer_solstice_after",
        "zishi",
        "true_solar_cross",
        "zhifu_zhonggong",
        "zhishi_zhonggong",
        "chunfen",
        "qiufen",
        "late_zishi",
    ):
        assert required in tags, f"missing coverage: {required}"
    # 春分/秋分/晚子时 向量存在 (Phase 5.5 freeze-gap 关闭)
    terms = {v["expected_board"]["solar_term"] for v in GOLDEN_VECTORS}
    assert "春分" in terms and "秋分" in terms
    late_zi = [v for v in GOLDEN_VECTORS if "late_zishi" in v["coverage"]]
    assert late_zi and late_zi[0]["expected_board"]["day_of_month"] == 15


# ===========================================================================
# Golden Vector 确定性 (Phase 5.3)
# ===========================================================================
def test_golden_vector_determinism():
    """每个向量同输入两次计算 → 盘面 JSON 完全一致 (去掉信封时间戳)。"""
    for v in GOLDEN_VECTORS:
        out1 = QimenAgent().compute(_vector_input(v))
        out2 = QimenAgent().compute(_vector_input(v))
        d1 = out1.result.model_dump(mode="json")
        d2 = out2.result.model_dump(mode="json")
        assert json.dumps(d1, ensure_ascii=False, sort_keys=True) == json.dumps(
            d2, ensure_ascii=False, sort_keys=True
        ), v["id"]


# ===========================================================================
# 盘面序列化稳定性 (Phase 5.3)
# ===========================================================================
_BOARD_KEY_ORDER = ["solar_term", "ju", "dun_type", "day_of_month", "triple_offset", "cells"]
_CELL_KEY_ORDER = [
    "palace",
    "name",
    "sky_plate",
    "earth_plate",
    "eight_gods",
    "nine_stars",
    "eight_doors",
    "three_qi",
    "is_void",
    "is_central",
]


def test_board_serialization_stability():
    """JSON 序列化稳定: 键顺序固定 + 字节级一致 + 数据文件键结构一致。"""
    for _name, dt, _expected in GOLDEN_CASES:
        d = _run(dt).model_dump(mode="json")
        assert list(d.keys()) == _BOARD_KEY_ORDER, _name
        assert all(list(c.keys()) == _CELL_KEY_ORDER for c in d["cells"]), _name
        s1 = json.dumps(d, ensure_ascii=False, sort_keys=True)
        s2 = json.dumps(_run(dt).model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
        assert s1 == s2, _name
    # 数据文件中的 expected_board 键结构必须与 Schema 一致
    for v in GOLDEN_VECTORS:
        b = v["expected_board"]
        assert list(b.keys()) == _BOARD_KEY_ORDER, v["id"]
        assert all(list(c.keys()) == _CELL_KEY_ORDER for c in b["cells"]), v["id"]


# ===========================================================================
# 全年随机抽样 (Phase 5.3 额外验证: 不少于 100 盘无异常)
# ===========================================================================
def test_random_year_sample_100_boards():
    """固定种子随机抽样全年 100 个时刻, 全部满足盘面状态不变量。"""
    rng = random.Random(2024)
    n = 0
    for _ in range(100):
        year = rng.choice([2023, 2024, 2025])
        dt = datetime(year, 1, 1, 0, 0, tzinfo=SHANGHAI) + timedelta(days=rng.randrange(0, 365))
        dt = dt.replace(hour=rng.randrange(0, 24), minute=rng.randrange(0, 60))
        if rng.random() < 0.1:  # 少量无坐标输入 (钟表时路径)
            inp = QimenInput(request_id=f"rs{n}", born_at=dt, gender=Gender.UNKNOWN)
        else:
            inp = QimenInput(
                request_id=f"rs{n}", born_at=dt, gender=Gender.UNKNOWN, born_location=BEIJING
            )
        r = QimenAgent().compute(inp).result
        _assert_board_state_valid(r, f"random #{n} {dt.isoformat()}")
        n += 1
    assert n == 100
