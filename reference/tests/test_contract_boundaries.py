"""Reference Qimen — 契约边界/异常场景测试 (Phase 5.7 对齐 Sprint).

独立性: 本文件只依赖 reference.qimen (domain + astronomy), 不导入 src。

覆盖:
- 节气边界: 冬至/夏至时刻切换 (QC-003), 立春节气切换局数重算 (QC-004)
- 晚子时: 不换日柱 (D14)
- 时辰越界/非法日期: compute 输入防御
- 盘面不变量抽查 (QC-002/005~014 代表性断言)
"""

from datetime import datetime, timedelta, timezone

import pytest

from reference.qimen.astronomy import solar_term_time
from reference.qimen.domain import compute, dun_type_and_base_ju

UTC = timezone.utc


def _payload(iso: str) -> dict:
    return {
        "request_id": "ref-boundary",
        "born_at": iso,
        "gender": "unknown",
        "born_location": {"latitude": 39.9, "longitude": 116.4, "timezone": "Asia/Shanghai"},
    }


def test_winter_solstice_boundary_switch():
    """冬至时刻(含)切阳遁, 前一刻为阴遁 (QC-003)。"""
    t = solar_term_time(2023, 270)
    before = compute(_payload((t - timedelta(minutes=1)).isoformat()))
    at = compute(_payload(t.isoformat()))
    after = compute(_payload((t + timedelta(minutes=1)).isoformat()))
    assert before["dun_type"] == "yin"
    assert at["dun_type"] == "yang"
    assert after["dun_type"] == "yang"


def test_summer_solstice_boundary_switch():
    """夏至时刻(含)切阴遁, 前一刻为阳遁 (QC-003)。"""
    t = solar_term_time(2024, 90)
    before = compute(_payload((t - timedelta(minutes=1)).isoformat()))
    at = compute(_payload(t.isoformat()))
    assert before["dun_type"] == "yang"
    assert at["dun_type"] == "yin"


def test_lichun_term_switch_ju_recompute():
    """立春前后: 管辖节气/基本局切换, 局数重算 (QC-004)。"""
    t = solar_term_time(2024, 315)
    before = compute(_payload((t - timedelta(hours=4)).isoformat()))
    after = compute(_payload((t + timedelta(hours=4)).isoformat()))
    assert before["solar_term"] == "大寒"
    assert after["solar_term"] == "立春"
    assert 1 <= before["ju"] <= 9 and 1 <= after["ju"] <= 9


def test_late_zi_hour_no_day_rollover():
    """晚子时 23:00-24:00 不换日柱 (D14)。"""
    board = compute(_payload("2024-05-15T23:30:00+08:00"))
    assert board["day_of_month"] == 15
    assert 1 <= board["ju"] <= 9


def test_invalid_datetime_rejected():
    """非法输入 (无效日期/非法时间) 必须报错, 不产生盘面。"""
    for bad in (
        "2024-02-30T12:00:00+08:00",
        "2024-13-01T12:00:00+08:00",
        "2024-05-15T24:00:00+08:00",
    ):
        with pytest.raises((ValueError, TypeError)):
            compute(_payload(bad))


def test_no_location_wall_clock_fallback():
    """无坐标: 回退钟表时 (D13)。"""
    payload = {"request_id": "r", "born_at": "2024-02-15T12:00:00+08:00", "gender": "unknown"}
    board = compute(payload)
    assert len(board["cells"]) == 9


def test_nine_palace_invariants_sample():
    """盘面结构不变量抽查 (QC-002/009~014)。"""
    board = compute(_payload("2024-02-15T12:00:00+08:00"))
    cells = board["cells"]
    assert len(cells) == 9
    assert [c["palace"] for c in cells] == list(range(1, 10))
    central = [c for c in cells if c["is_central"]]
    assert len(central) == 1 and central[0]["palace"] == 5
    stars = {c["nine_stars"] for c in cells}
    assert len(stars) == 9
    doors = [c["eight_doors"] for c in cells if c["eight_doors"]]
    assert len(set(doors)) == 8
    gods = [c["eight_gods"] for c in cells if c["eight_gods"]]
    assert len(set(gods)) == 8
    sanqi = [c["three_qi"] for c in cells if c["three_qi"]]
    assert set(sanqi) == {"乙", "丙", "丁"} and len(sanqi) == 3
    void = [c for c in cells if c["is_void"]]
    assert 1 <= len(void) <= 2


def test_dun_type_base_ju_known_dates():
    """经典锚点: 冬至后阳遁/基本局 1, 夏至后阴遁/基本局 1 (QC-003/004)。"""
    dongzhi_after = datetime(2023, 12, 23, 0, 0, tzinfo=UTC)
    dun, base, term = dun_type_and_base_ju(dongzhi_after)
    assert (dun, base, term) == ("yang", 1, "冬至")
    xiazhi_after = datetime(2024, 6, 22, 0, 0, tzinfo=UTC)
    dun, base, term = dun_type_and_base_ju(xiazhi_after)
    assert (dun, base, term) == ("yin", 1, "夏至")
