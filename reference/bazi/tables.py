"""Reference BaZi tables (self-contained, no openmetaphysics imports).

Frozen normative data per docs/bazi/BAZI_BEHAVIOR_CONTRACT.md v1.0.0
(BC-006/007/008: ten gods, hidden stems, na yin; BC-002/003: solar terms).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Heavenly Stems (天干)
# ---------------------------------------------------------------------------
HEAVENLY_STEMS: list[str] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

STEM_ELEMENT: dict[str, str] = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

STEM_YIN_YANG: dict[str, str] = {
    "甲": "阳",
    "丙": "阳",
    "戊": "阳",
    "庚": "阳",
    "壬": "阳",
    "乙": "阴",
    "丁": "阴",
    "己": "阴",
    "辛": "阴",
    "癸": "阴",
}

# ---------------------------------------------------------------------------
# Earthly Branches (地支)
# ---------------------------------------------------------------------------
EARTHLY_BRANCHES: list[str] = [
    "子",
    "丑",
    "寅",
    "卯",
    "辰",
    "巳",
    "午",
    "未",
    "申",
    "酉",
    "戌",
    "亥",
]

# Hidden stems (藏干) per branch, main qi first (BC-007).
BRANCH_HIDDEN_STEMS: dict[str, list[str]] = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

# ---------------------------------------------------------------------------
# Wuxing interactions (BC-006)
# ---------------------------------------------------------------------------
WUXING_SHENG: dict[str, str] = {"金": "水", "水": "木", "木": "火", "火": "土", "土": "金"}
WUXING_KE: dict[str, str] = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}


def wuxing_relation(a: str, b: str) -> str:
    """Return 'sheng', 'ke', 'being_sheng', 'being_ke', or 'same'."""
    if a == b:
        return "same"
    if WUXING_SHENG.get(a) == b:
        return "sheng"
    if WUXING_SHENG.get(b) == a:
        return "being_sheng"
    if WUXING_KE.get(a) == b:
        return "ke"
    if WUXING_KE.get(b) == a:
        return "being_ke"
    return "unrelated"


# ---------------------------------------------------------------------------
# Sexagenary cycle (六十甲子) + Nayin (纳音, BC-008)
# ---------------------------------------------------------------------------
def sexagenary_pair(index: int) -> tuple[str, str]:
    """Index 0..59 -> (stem, branch). 甲子 = 0."""
    i = index % 60
    return HEAVENLY_STEMS[i % 10], EARTHLY_BRANCHES[i % 12]


def sexagenary_index(stem: str, branch: str) -> int:
    """Inverse of sexagenary_pair."""
    si = HEAVENLY_STEMS.index(stem)
    bi = EARTHLY_BRANCHES.index(branch)
    for k in range(60):
        if k % 10 == si and k % 12 == bi:
            return k
    raise ValueError(f"invalid stem-branch pair: {stem}{branch}")


NAYIN: list[str] = [
    "海中金",
    "海中金",
    "炉中火",
    "炉中火",
    "大林木",
    "大林木",
    "路旁土",
    "路旁土",
    "剑锋金",
    "剑锋金",
    "山头火",
    "山头火",
    "涧下水",
    "涧下水",
    "城头土",
    "城头土",
    "白蜡金",
    "白蜡金",
    "杨柳木",
    "杨柳木",
    "泉中水",
    "泉中水",
    "屋上土",
    "屋上土",
    "霹雳火",
    "霹雳火",
    "松柏木",
    "松柏木",
    "长流水",
    "长流水",
    "砂中金",
    "砂中金",
    "山下火",
    "山下火",
    "平地木",
    "平地木",
    "壁上土",
    "壁上土",
    "金箔金",
    "金箔金",
    "覆灯火",
    "覆灯火",
    "天河水",
    "天河水",
    "大驿土",
    "大驿土",
    "钗钏金",
    "钗钏金",
    "桑柘木",
    "桑柘木",
    "大溪水",
    "大溪水",
    "沙中土",
    "沙中土",
    "天上火",
    "天上火",
    "石榴木",
    "石榴木",
    "大海水",
    "大海水",
]


def nayin_for(stem: str, branch: str) -> str:
    return NAYIN[sexagenary_index(stem, branch)]


# ---------------------------------------------------------------------------
# Solar terms (节气, BC-002/003): name, is_jie, ecliptic longitude.
# 立春 = 315° is the Bazi year boundary.
# ---------------------------------------------------------------------------
SOLAR_TERMS_24: list[tuple[str, bool, int]] = [
    ("春分", False, 0),
    ("清明", True, 15),
    ("谷雨", False, 30),
    ("立夏", True, 45),
    ("小满", False, 60),
    ("芒种", True, 75),
    ("夏至", False, 90),
    ("小暑", True, 105),
    ("大暑", False, 120),
    ("立秋", True, 135),
    ("处暑", False, 150),
    ("白露", True, 165),
    ("秋分", False, 180),
    ("寒露", True, 195),
    ("霜降", False, 210),
    ("立冬", True, 225),
    ("小雪", False, 240),
    ("大雪", True, 255),
    ("冬至", False, 270),
    ("小寒", True, 285),
    ("大寒", False, 300),
    ("立春", True, 315),
    ("雨水", False, 330),
    ("惊蛰", True, 345),
]

# The 12 节 that start Bazi months: (term, longitude, month branch index).
BAZI_MONTH_BOUNDARIES: list[tuple[str, int, int]] = [
    ("立春", 315, 2),
    ("惊蛰", 345, 3),
    ("清明", 15, 4),
    ("立夏", 45, 5),
    ("芒种", 75, 6),
    ("小暑", 105, 7),
    ("立秋", 135, 8),
    ("白露", 165, 9),
    ("寒露", 195, 10),
    ("立冬", 225, 11),
    ("大雪", 255, 0),
    ("小寒", 285, 1),
]
