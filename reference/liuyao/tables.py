"""Liuyao reference tables — self-contained (no src imports).

Generated once from the production metaphysics tables; the Reference Runtime
must not import ``openmetaphysics``. See reference/liuyao/README.md.
"""

from __future__ import annotations

# == 五行 ==
WUXING_SHENG: dict[str, str] = {"金": "水", "水": "木", "木": "火", "火": "土", "土": "金"}
WUXING_KE: dict[str, str] = {"金": "木", "木": "土", "土": "水", "水": "火", "火": "金"}

# == 八卦 ==
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

# == 六十四卦 (King Wen) ==
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

# == 天干地支 ==
HEAVENLY_STEMS: list[str] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
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


# == Lookup helpers ==


def trigram_from_lines(lines: list[int]) -> str:
    """Trigram name for three lines bottom->top."""
    for name, info in TRIGRAMS.items():
        if info["lines"] == list(lines):
            return name
    raise ValueError(f"no trigram for lines {lines}")


def hexagram_from_lines(lines: list[int]) -> dict:
    """Find the King Wen hexagram for 6 lines bottom->top."""
    lower = trigram_from_lines(lines[:3])
    upper = trigram_from_lines(lines[3:])
    for h in HEXAGRAMS:
        if h["upper"] == upper and h["lower"] == lower:
            return h
    raise ValueError(f"no hexagram for lines {lines}")


def wuxing_relation(a: str, b: str) -> str:
    """Return 'sheng', 'ke', 'being_sheng', 'being_ke', 'same' or 'unrelated'."""
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


# == 京房八宫 ==
BA_GONG: list[tuple[str, list[int]]] = [
    ("乾", [1, 44, 33, 12, 20, 23, 35, 14]),
    ("坎", [29, 60, 3, 63, 49, 55, 36, 7]),
    ("艮", [52, 22, 26, 41, 38, 10, 61, 53]),
    ("震", [51, 16, 40, 32, 46, 48, 28, 17]),
    ("巽", [57, 9, 37, 42, 25, 21, 27, 18]),
    ("离", [30, 56, 50, 64, 4, 59, 6, 13]),
    ("坤", [2, 24, 19, 11, 34, 43, 5, 8]),
    ("兑", [58, 47, 45, 31, 39, 15, 62, 54]),
]
SHI_BY_POS: dict[int, int] = {1: 6, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 4, 8: 3}

# == 纳甲 ==
NAJIA_STEM: dict[str, tuple[int, int]] = {
    "乾": (0, 8),
    "坤": (1, 9),
    "艮": (2, 2),
    "兑": (3, 3),
    "坎": (4, 4),
    "离": (5, 5),
    "震": (6, 6),
    "巽": (7, 7),
}
YANG_TRIGRAMS: set[str] = {"震", "坎", "艮", "乾"}
YANG_BRANCHES: list[str] = ["子", "寅", "辰", "午", "申", "戌"]
YIN_BRANCHES: list[str] = ["丑", "卯", "巳", "未", "酉", "亥"]
_YANG_START: dict[str, int] = {"乾": 0, "震": 0, "坎": 1, "艮": 2}
_YIN_START: dict[str, int] = {"坤": 3, "巽": 0, "离": 1, "兑": 2}

# == 六神 / 六亲 / 用神 ==
SIX_SPIRITS: list[str] = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
SPIRIT_START_BY_STEM: dict[int, int] = {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5}
LIU_QIN_BY_RELATION: dict[str, str] = {
    "same": "兄弟",
    "sheng": "子孙",
    "being_sheng": "父母",
    "ke": "妻财",
    "being_ke": "官鬼",
}
YONG_SHEN_RULES: list[tuple[tuple[str, ...], str]] = [
    (("财", "钱", "利", "薪", "买卖", "交易", "投资"), "妻财"),
    (("官", "功名", "事业", "升迁", "官司", "丈夫", "工作", "考试升"), "官鬼"),
    (("父", "母", "长辈", "文书", "房", "屋", "学", "考"), "父母"),
    (("兄", "弟", "朋友", "同事", "合伙"), "兄弟"),
    (("子", "女", "晚辈", "下属", "平安", "出行", "药", "医", "求谋"), "子孙"),
]


def najia_branch(trigram: str, slot: int, is_outer: bool) -> str:
    """Earthly branch for a trigram line slot (0,1,2) in the inner/outer trigram."""
    if trigram in YANG_TRIGRAMS:
        start = _YANG_START[trigram]
        idx = (start + (3 if is_outer else 0) + slot) % 6
        return YANG_BRANCHES[idx]
    start = _YIN_START[trigram]
    idx = (start - (3 if is_outer else 0) - slot) % 6
    return YIN_BRANCHES[idx]
