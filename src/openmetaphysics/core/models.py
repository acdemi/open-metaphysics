"""Static metaphysics reference tables (pure data, no I/O, no LLM).

These are the deterministic ground-truth tables every engine consults:
Heavenly Stems / Earthly Branches, Wuxing relations, the 60 Nayin,
the 24 solar terms, the 8 trigrams and the 64 King-Wen hexagrams.
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

BRANCH_ELEMENT: dict[str, str] = {
    "寅": "木",
    "卯": "木",
    "巳": "火",
    "午": "火",
    "申": "金",
    "酉": "金",
    "亥": "水",
    "子": "水",
    "丑": "土",
    "辰": "土",
    "未": "土",
    "戌": "土",
}

BRANCH_ZODIAC: dict[str, str] = {
    "子": "鼠",
    "丑": "牛",
    "寅": "虎",
    "卯": "兔",
    "辰": "龙",
    "巳": "蛇",
    "午": "马",
    "未": "羊",
    "申": "猴",
    "酉": "鸡",
    "戌": "狗",
    "亥": "猪",
}

# Hidden stems (藏干) per branch, main qi first.
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
# Wuxing (五行) interactions
# ---------------------------------------------------------------------------
WUXING: list[str] = ["金", "木", "水", "火", "土"]

WUXING_SHENG: dict[str, str] = {  # 生: A generates B
    "金": "水",
    "水": "木",
    "木": "火",
    "火": "土",
    "土": "金",
}

WUXING_KE: dict[str, str] = {  # 克: A overcomes B
    "金": "木",
    "木": "土",
    "土": "水",
    "水": "火",
    "火": "金",
}


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
# Sexagenary cycle (六十甲子) + Nayin (纳音)
# ---------------------------------------------------------------------------
def sexagenary_pair(index: int) -> tuple[str, str]:
    """Index 0..59 -> (stem, branch). 甲子 = 0."""
    i = index % 60
    return HEAVENLY_STEMS[i % 10], EARTHLY_BRANCHES[i % 12]


def sexagenary_index(stem: str, branch: str) -> int:
    """Inverse of sexagenary_pair. Requires matching stem/branch parity."""
    si = HEAVENLY_STEMS.index(stem)
    bi = EARTHLY_BRANCHES.index(branch)
    # solve k: k % 10 == si and k % 12 == bi, 0 <= k < 60
    for k in range(60):
        if k % 10 == si and k % 12 == bi:
            return k
    raise ValueError(f"invalid stem-branch pair: {stem}{branch}")


# 60 甲子纳音, indexed by sexagenary index (0..59). Each name ends with its element.
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
# 24 Solar Terms (二十四节气)
# ---------------------------------------------------------------------------
# In ecliptic-longitude order. 立春 = 315° is the Bazi year boundary.
# is_jie True => 节 (month boundary for Bazi); False => 气 (中气).
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

# The 12 节 that bound Bazi months, in calendar order starting at 立春.
BAZI_MONTH_BOUNDARIES: list[tuple[str, int, int]] = [
    # (term, longitude, branch_index of the month it starts)
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

# ---------------------------------------------------------------------------
# Trigrams (八卦)
# ---------------------------------------------------------------------------
# lines: bottom->top, 1=yang, 0=yin.
TRIGRAMS: dict[str, dict] = {
    "乾": {"lines": [1, 1, 1], "element": "金", "nature": "天", "direction": "西北"},
    "兑": {"lines": [1, 1, 0], "element": "金", "nature": "泽", "direction": "西"},
    "离": {"lines": [1, 0, 1], "element": "火", "nature": "火", "direction": "南"},
    "震": {"lines": [1, 0, 0], "element": "木", "nature": "雷", "direction": "东"},
    "巽": {"lines": [0, 1, 1], "element": "木", "nature": "风", "direction": "东南"},
    "坎": {"lines": [0, 1, 0], "element": "水", "nature": "水", "direction": "北"},
    "艮": {"lines": [0, 0, 1], "element": "土", "nature": "山", "direction": "东北"},
    "坤": {"lines": [0, 0, 0], "element": "土", "nature": "地", "direction": "西南"},
}

TRIGRAM_NAMES: list[str] = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]


def trigram_from_lines(lines: list[int]) -> str:
    for name, info in TRIGRAMS.items():
        if info["lines"] == list(lines):
            return name
    raise ValueError(f"no trigram for lines {lines}")


# ---------------------------------------------------------------------------
# 64 Hexagrams (六十四卦) — King Wen order
# ---------------------------------------------------------------------------
HEXAGRAMS: list[dict] = [
    {"num": 1, "name": "乾", "upper": "乾", "lower": "乾"},
    {"num": 2, "name": "坤", "upper": "坤", "lower": "坤"},
    {"num": 3, "name": "屯", "upper": "坎", "lower": "震"},
    {"num": 4, "name": "蒙", "upper": "艮", "lower": "坎"},
    {"num": 5, "name": "需", "upper": "坎", "lower": "乾"},
    {"num": 6, "name": "讼", "upper": "乾", "lower": "坎"},
    {"num": 7, "name": "师", "upper": "坤", "lower": "坎"},
    {"num": 8, "name": "比", "upper": "坎", "lower": "坤"},
    {"num": 9, "name": "小畜", "upper": "巽", "lower": "乾"},
    {"num": 10, "name": "履", "upper": "乾", "lower": "兑"},
    {"num": 11, "name": "泰", "upper": "坤", "lower": "乾"},
    {"num": 12, "name": "否", "upper": "乾", "lower": "坤"},
    {"num": 13, "name": "同人", "upper": "乾", "lower": "离"},
    {"num": 14, "name": "大有", "upper": "离", "lower": "乾"},
    {"num": 15, "name": "谦", "upper": "坤", "lower": "艮"},
    {"num": 16, "name": "豫", "upper": "震", "lower": "坤"},
    {"num": 17, "name": "随", "upper": "兑", "lower": "震"},
    {"num": 18, "name": "蛊", "upper": "艮", "lower": "巽"},
    {"num": 19, "name": "临", "upper": "坤", "lower": "兑"},
    {"num": 20, "name": "观", "upper": "巽", "lower": "坤"},
    {"num": 21, "name": "噬嗑", "upper": "离", "lower": "震"},
    {"num": 22, "name": "贲", "upper": "艮", "lower": "离"},
    {"num": 23, "name": "剥", "upper": "艮", "lower": "坤"},
    {"num": 24, "name": "复", "upper": "坤", "lower": "震"},
    {"num": 25, "name": "无妄", "upper": "乾", "lower": "震"},
    {"num": 26, "name": "大畜", "upper": "艮", "lower": "乾"},
    {"num": 27, "name": "颐", "upper": "艮", "lower": "震"},
    {"num": 28, "name": "大过", "upper": "兑", "lower": "巽"},
    {"num": 29, "name": "坎", "upper": "坎", "lower": "坎"},
    {"num": 30, "name": "离", "upper": "离", "lower": "离"},
    {"num": 31, "name": "咸", "upper": "兑", "lower": "艮"},
    {"num": 32, "name": "恒", "upper": "震", "lower": "巽"},
    {"num": 33, "name": "遯", "upper": "乾", "lower": "艮"},
    {"num": 34, "name": "大壮", "upper": "震", "lower": "乾"},
    {"num": 35, "name": "晋", "upper": "离", "lower": "坤"},
    {"num": 36, "name": "明夷", "upper": "坤", "lower": "离"},
    {"num": 37, "name": "家人", "upper": "巽", "lower": "离"},
    {"num": 38, "name": "睽", "upper": "离", "lower": "兑"},
    {"num": 39, "name": "蹇", "upper": "坎", "lower": "艮"},
    {"num": 40, "name": "解", "upper": "震", "lower": "坎"},
    {"num": 41, "name": "损", "upper": "艮", "lower": "兑"},
    {"num": 42, "name": "益", "upper": "巽", "lower": "震"},
    {"num": 43, "name": "夬", "upper": "兑", "lower": "乾"},
    {"num": 44, "name": "姤", "upper": "乾", "lower": "巽"},
    {"num": 45, "name": "萃", "upper": "兑", "lower": "坤"},
    {"num": 46, "name": "升", "upper": "坤", "lower": "巽"},
    {"num": 47, "name": "困", "upper": "兑", "lower": "坎"},
    {"num": 48, "name": "井", "upper": "坎", "lower": "巽"},
    {"num": 49, "name": "革", "upper": "兑", "lower": "离"},
    {"num": 50, "name": "鼎", "upper": "离", "lower": "巽"},
    {"num": 51, "name": "震", "upper": "震", "lower": "震"},
    {"num": 52, "name": "艮", "upper": "艮", "lower": "艮"},
    {"num": 53, "name": "渐", "upper": "巽", "lower": "艮"},
    {"num": 54, "name": "归妹", "upper": "震", "lower": "兑"},
    {"num": 55, "name": "丰", "upper": "震", "lower": "离"},
    {"num": 56, "name": "旅", "upper": "离", "lower": "艮"},
    {"num": 57, "name": "巽", "upper": "巽", "lower": "巽"},
    {"num": 58, "name": "兑", "upper": "兑", "lower": "兑"},
    {"num": 59, "name": "涣", "upper": "巽", "lower": "坎"},
    {"num": 60, "name": "节", "upper": "坎", "lower": "兑"},
    {"num": 61, "name": "中孚", "upper": "巽", "lower": "兑"},
    {"num": 62, "name": "小过", "upper": "震", "lower": "艮"},
    {"num": 63, "name": "既济", "upper": "坎", "lower": "离"},
    {"num": 64, "name": "未济", "upper": "离", "lower": "坎"},
]


def hexagram_lines(num: int) -> list[int]:
    """6 lines bottom->top (1=yang, 0=yin) for King Wen hexagram `num` (1..64)."""
    h = HEXAGRAMS[num - 1]
    return TRIGRAMS[h["lower"]]["lines"] + TRIGRAMS[h["upper"]]["lines"]


def hexagram_from_lines(lines: list[int]) -> dict:
    """Find King Wen hexagram from 6 lines bottom->top."""
    lower = trigram_from_lines(lines[:3])
    upper = trigram_from_lines(lines[3:])
    for h in HEXAGRAMS:
        if h["upper"] == upper and h["lower"] == lower:
            return h
    raise ValueError(f"no hexagram for lines {lines}")
