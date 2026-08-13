"""Reference Ziwei normative tables.

All Ziwei-specific tables are explicitly defined here, extracted from
docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT_DRAFT.md (BC-009/010/011/012) and the
24 golden vectors (docs/ziwei/golden_vectors.json). No source code from
src/openmetaphysics is imported or consulted.

Shared stem/branch/na-yin infrastructure is reused from
reference/bazi/tables.py (normative, frozen by BAZI_BEHAVIOR_CONTRACT
BC-006/007/008) with explicit citation — see imports below.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Shared infrastructure (explicit reuse, cited):
#   reference/bazi/tables.py — HEAVENLY_STEMS / STEM_YIN_YANG / NAYIN /
#   nayin_for (normative per docs/bazi/BAZI_BEHAVIOR_CONTRACT.md)
# ---------------------------------------------------------------------------
from reference.bazi.tables import HEAVENLY_STEMS, STEM_YIN_YANG, nayin_for  # noqa: F401

# ---------------------------------------------------------------------------
# BC-010: Twelve Palace Layout (ZW-011)
# ---------------------------------------------------------------------------
# 12-palace array starting at 寅 (clockwise branch order, index 0..11).
PALACE_BRANCHES: list[str] = [
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
    "子",
    "丑",
]

# Palace names by offset from the fate palace: 命宫 at index `ming`, then
# 兄弟/夫妻/子女/财帛/疾厄/迁移/奴仆/官禄/田宅/福德/父母 clockwise.
PALACE_NAMES: list[str] = [
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

# ---------------------------------------------------------------------------
# BC-009: WuXing Ju (ZW-010) — element -> ju number
# ---------------------------------------------------------------------------
JU_NUMBER: dict[str, int] = {"水": 2, "木": 3, "金": 4, "土": 5, "火": 6}

# ---------------------------------------------------------------------------
# BC-011: Ziwei Placement (ZW-012, A-1) — unified generative rule
#   idx = (START[ju] + (lunar_day - 1) // STEP[ju]) % 12   (寅=0)
#   START: 水2起丑(11) / 木3起辰(2) / 金4起亥(9) / 土5起午(4) / 火6起酉(7)
#   STEP:  水2步长2日, 其余步长3日
#   Invariants: 木三不落寅卯 / 金四不落酉戌 / 土五不落辰巳 / 火六不落未申
# ---------------------------------------------------------------------------
ZIWEI_JU_START: dict[int, int] = {2: 11, 3: 2, 4: 9, 5: 4, 6: 7}
ZIWEI_JU_STEP: dict[int, int] = {2: 2, 3: 3, 4: 3, 5: 3, 6: 3}


def ziwei_index(ju: int, lunar_day: int) -> int:
    """BC-011: unified generative formula for the Ziwei (紫微) palace index."""
    return (ZIWEI_JU_START[ju] + (lunar_day - 1) // ZIWEI_JU_STEP[ju]) % 12


# ---------------------------------------------------------------------------
# BC-012: Tianfu Mirror & Star Systems (ZW-013/014/015, A-2)
# ---------------------------------------------------------------------------
# 紫微星系 (relative to 紫微, 逆行 = negative offset; 廉贞 = -8 per ACP-ZW-002):
ZIWEI_XINGXI: list[tuple[str, int]] = [
    ("紫微", 0),
    ("天机", -1),
    ("太阳", -3),
    ("武曲", -4),
    ("天同", -5),
    ("廉贞", -8),
]

# 天府星系 (relative to 天府, 顺行 = positive offset):
TIANFU_XINGXI: list[tuple[str, int]] = [
    ("天府", 0),
    ("太阴", 1),
    ("贪狼", 2),
    ("巨门", 3),
    ("天相", 4),
    ("天梁", 5),
    ("七杀", 6),
    ("破军", 10),
]

__all__ = [
    "HEAVENLY_STEMS",
    "STEM_YIN_YANG",
    "nayin_for",
    "PALACE_BRANCHES",
    "PALACE_NAMES",
    "JU_NUMBER",
    "ZIWEI_JU_START",
    "ZIWEI_JU_STEP",
    "ziwei_index",
    "ZIWEI_XINGXI",
    "TIANFU_XINGXI",
]
