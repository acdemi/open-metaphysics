"""Reference Qimen Domain — 依契约 v1.0.0 的实现 (Phase 5.9B 实现, 5.7 对齐).

对齐:
- 行为权威: docs/specification/QIMEN_BEHAVIOR_CONTRACT.md (Frozen v1.0.0)
- 规范装置: docs/qimen/golden_vectors.json (24, normative fixtures)
- 验收标准: 输出与 24 规范向量 expected_board 逐字节一致
  (reference/tests/test_golden_vectors.py 强制; E015/E016 Evidence 记录)

独立性声明 (Phase 5.7 对齐 Sprint):
- 本模块 + astronomy.py 完全自包含, **不导入 src/openmetaphysics 任何模块**
  (含 Product Runtime 与 core 共享基础层)
- 天文/干支基础为 core 的规范移植 (astronomy.py, Meeus 同源算法)

奇门规范性内容 (宫名/九星/八门/八神/六仪三奇/六甲/宫支映射/遁序节气表/
地盘/天盘/值符/值使/空亡/中宫) 在本模块内自包含。

流派裁定 (契约 v1.0.0): 三元 = 日号近似 (D2 Option A); 晚子时不换日 (D14);
转盘法; 中宫寄坤二; 天禽参与转盘; 八神顺布。流派差异记录见
reference/qimen/concepts/schools.md。
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from .astronomy import (
    HEAVENLY_STEMS,
    SOLAR_TERMS_24,
    sexagenary_day_index,
    solar_term_time,
    true_solar_hour,
)

# ---------------------------------------------------------------------------
# 规范性表格 (自包含)
# ---------------------------------------------------------------------------
PALACE_NAMES_9 = {
    1: "坎",
    2: "坤",
    3: "震",
    4: "巽",
    5: "中宫",
    6: "乾",
    7: "兑",
    8: "艮",
    9: "离",
}
EIGHT_GODS = ["值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
NINE_STARS = {
    1: "天蓬",
    2: "天芮",
    3: "天冲",
    4: "天辅",
    5: "天禽",
    6: "天心",
    7: "天柱",
    8: "天任",
    9: "天英",
}
EIGHT_DOORS = {
    1: "休门",
    2: "死门",
    3: "伤门",
    4: "杜门",
    5: None,
    6: "开门",
    7: "惊门",
    8: "生门",
    9: "景门",
}
LIUYI = ["戊", "己", "庚", "辛", "壬", "癸"]
SANQI = ["乙", "丙", "丁"]
LIUJIA = [
    ("甲子", "戊"),
    ("甲戌", "己"),
    ("甲申", "庚"),
    ("甲午", "辛"),
    ("甲辰", "壬"),
    ("甲寅", "癸"),
]
DOOR_PALACES = [1, 2, 3, 4, 6, 7, 8, 9]
PALACE_BRANCHES = {
    1: [0],
    2: [7, 8],
    3: [3],
    4: [4, 5],
    6: [10, 11],
    7: [9],
    8: [1, 2],
    9: [6],
}
SOLAR_TERMS_YANGDUN = [
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
]
SOLAR_TERMS_YINDUN = [
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
JU_PER_TERM_YANG = {term: i + 1 for i, term in enumerate(SOLAR_TERMS_YANGDUN)}
JU_PER_TERM_YIN = {term: i + 1 for i, term in enumerate(SOLAR_TERMS_YINDUN)}

_ORDER = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]


# ---------------------------------------------------------------------------
# 干支基础 (QC-006/007/008/013 前置)
# ---------------------------------------------------------------------------
def hour_branch_index(hour: int) -> int:
    return ((hour + 1) // 2) % 12


def sexagenary_hour_index(day_stem_index: int, hour_branch_index: int) -> int:
    """五鼠遁: 时干支序 0..59."""
    start = (day_stem_index % 5) * 2
    stem = (start + hour_branch_index) % 10
    for k in range(stem, 60, 10):
        if k % 12 == hour_branch_index:
            return k
    raise ValueError("no sexagenary hour")


def xun_shou_liuyi(sexagenary_index: int) -> str:
    return LIUYI[sexagenary_index // 10]


def xun_shou_branch(sexagenary_index: int) -> int:
    return ((sexagenary_index // 10) * 10) % 12


def void_branch_indices(sexagenary_index: int) -> tuple[int, int]:
    shou = (sexagenary_index // 10) * 10
    return (shou - 2) % 12, (shou - 1) % 12


def branch_to_palace(branch_index: int) -> int:
    for palace, branches in PALACE_BRANCHES.items():
        if branch_index in branches:
            return palace
    raise ValueError(f"no palace for branch {branch_index}")


# ---------------------------------------------------------------------------
# 遁与局 (QC-003/004)
# ---------------------------------------------------------------------------
def dun_type_and_base_ju(utc_dt: datetime) -> tuple[str, int, str]:
    """阴阳遁/基本局/管辖节气 (D1; 扫描前一年+当年)."""
    y = utc_dt.astimezone(timezone.utc).year
    terms: list[tuple[str, datetime]] = []
    for yy in (y - 1, y):
        for name, _is_jie, lon in SOLAR_TERMS_24:
            terms.append((name, solar_term_time(yy, lon)))
    terms.sort(key=lambda x: x[1])
    current = terms[0][0]
    for name, t in terms:
        if t <= utc_dt:
            current = name
    if current in JU_PER_TERM_YANG:
        return "yang", JU_PER_TERM_YANG[current], current
    return "yin", JU_PER_TERM_YIN[current], current


def ju_from_day_of_month(day: int) -> int:
    """三元偏移 (D2 Option A: 日号近似)."""
    if 1 <= day <= 10:
        return 0
    if 11 <= day <= 20:
        return 3
    return 6


def earth_placement(dun_type: str, ju: int) -> dict[int, str]:
    """地盘六仪三奇 (QC-005, D4)."""
    if dun_type == "yang":
        start, step = ju - 1, 1
    else:
        start, step = (9 - ju) % 9, -1
    out: dict[int, str] = {}
    for i, stem in enumerate(_ORDER):
        out[(start + step * i) % 9 + 1] = stem
    return out


# ---------------------------------------------------------------------------
# 盘面构建 (QC-006 ~ QC-014)
# ---------------------------------------------------------------------------
def build_board(dun_type: str, base_ju: int, local_date: date, hour: int, solar_term: str) -> dict:
    """按契约构建完整九宫盘 (JSON 形态, 与规范向量 expected_board 同构)."""
    triple_offset = ju_from_day_of_month(local_date.day)
    ju = ((base_ju - 1) + triple_offset) % 9 + 1
    earth = earth_placement(dun_type, ju)

    day_stem = sexagenary_day_index(local_date.year, local_date.month, local_date.day) % 10
    hb = hour_branch_index(hour)
    hour_index = sexagenary_hour_index(day_stem, hb)

    xun_liuyi = xun_shou_liuyi(hour_index)
    xun_name, _ = LIUJIA[hour_index // 10]
    xun_palace = next(p for p, s in earth.items() if s == xun_liuyi)
    xun_branch = xun_shou_branch(hour_index)

    hour_stem = HEAVENLY_STEMS[hour_index % 10]
    hour_stem_palace = next((p for p, s in earth.items() if s == hour_stem), xun_palace)
    zhi_fu_palace = hour_stem_palace if hour_stem_palace != 5 else 2

    offset = (hour_stem_palace - xun_palace) % 9
    sky_gan = {p: earth[((p - 1) - offset) % 9 + 1] for p in range(1, 10)}
    sky_star = {p: NINE_STARS[((p - 1) - offset) % 9 + 1] for p in range(1, 10)}

    home = xun_palace if xun_palace != 5 else 2
    steps = (hb - xun_branch) % 12
    if dun_type == "yang":
        zhi_shi_palace = ((home - 1) + steps) % 9 + 1
    else:
        zhi_shi_palace = ((home - 1) - steps) % 9 + 1
    if zhi_shi_palace == 5:
        zhi_shi_palace = 2

    door_offset = (DOOR_PALACES.index(zhi_shi_palace) - DOOR_PALACES.index(home)) % 8
    doors: dict[int, str | None] = {5: None}
    for p in DOOR_PALACES:
        doors[p] = EIGHT_DOORS[DOOR_PALACES[(DOOR_PALACES.index(p) - door_offset) % 8]]

    gods: dict[int, str] = {}
    god_start = DOOR_PALACES.index(zhi_fu_palace)
    for i, god in enumerate(EIGHT_GODS):
        gods[DOOR_PALACES[(god_start + i) % 8]] = god

    void_palaces = sorted({branch_to_palace(b) for b in void_branch_indices(hour_index)})

    cells: list[dict] = []
    for p in range(1, 10):
        gan = sky_gan[p]
        cells.append(
            {
                "palace": p,
                "name": PALACE_NAMES_9[p],
                "sky_plate": gan,
                "earth_plate": earth[p],
                "eight_gods": gods.get(p),
                "nine_stars": sky_star[p],
                "eight_doors": doors[p],
                "three_qi": gan if gan in SANQI else None,
                "is_void": p in void_palaces,
                "is_central": p == 5,
            }
        )

    return {
        "solar_term": solar_term,
        "ju": ju,
        "dun_type": dun_type,
        "day_of_month": local_date.day,
        "triple_offset": triple_offset,
        "cells": cells,
    }


def effective_hour(born_at: datetime, longitude: float | None) -> int:
    """真太阳时定时辰 (D13); 无坐标回退钟表时。"""
    if longitude is None:
        return born_at.hour
    return true_solar_hour(born_at, longitude)


def compute(payload: dict) -> dict:
    """入口: 输入信封 (JSON 形态) → 完整九宫盘 (JSON 形态)。

    输入字段: born_at (ISO 8601, tz-aware), born_location (可选, 含 longitude)。
    行为与契约 QC-001~014 一致; 晚子时不换日柱 (D14)。
    """
    born_at = datetime.fromisoformat(payload["born_at"])
    loc = payload.get("born_location")
    longitude = loc.get("longitude") if loc else None
    dun_type, base_ju, term = dun_type_and_base_ju(born_at.astimezone(timezone.utc))
    hour = effective_hour(born_at, longitude)
    return build_board(dun_type, base_ju, born_at.date(), hour, term)


__all__ = [
    "PALACE_NAMES_9",
    "EIGHT_GODS",
    "NINE_STARS",
    "EIGHT_DOORS",
    "LIUYI",
    "SANQI",
    "LIUJIA",
    "DOOR_PALACES",
    "PALACE_BRANCHES",
    "SOLAR_TERMS_YANGDUN",
    "SOLAR_TERMS_YINDUN",
    "JU_PER_TERM_YANG",
    "JU_PER_TERM_YIN",
    "hour_branch_index",
    "sexagenary_hour_index",
    "xun_shou_liuyi",
    "xun_shou_branch",
    "void_branch_indices",
    "branch_to_palace",
    "dun_type_and_base_ju",
    "ju_from_day_of_month",
    "earth_placement",
    "build_board",
    "effective_hour",
    "compute",
]
