"""Ziwei pattern matcher — deterministic rule-based pattern recognition.
All patterns are matched via canonical rules, no LLM involved.
"""
from __future__ import annotations

from typing import List, Set, Tuple

from ..ziwei import Palace


def _palace_has_stars(palace: Palace, stars: Set[str]) -> bool:
    """Check if palace has all specified stars."""
    return all(s in palace.main_stars for s in stars)


def _sanfang_sizheng(palaces: list[Palace], center_idx: int) -> Tuple[Palace, Palace, Palace, Palace]:
    """Get 三方四正 palaces relative to center index: [命宫，三方1，三方2，对宫]"""
    # 三方：+4, +8 modulo 12; 对宫：+6 modulo 12
    return (
        palaces[center_idx],
        palaces[(center_idx + 4) % 12],
        palaces[(center_idx + 8) % 12],
        palaces[(center_idx + 6) % 12],
    )


def match_patterns(palaces: List[Palace]) -> List[str]:
    """Match all deterministic patterns from the given 12 palaces.
    Returns list of pattern names in Chinese.
    """
    patterns = []
    fate_palace = next(p for p in palaces if p.is_fate_palace)
    fate_idx = fate_palace.index
    ming, sf1, sf2, dui = _sanfang_sizheng(palaces, fate_idx)
    all_sanfang = [ming, sf1, sf2, dui]
    all_sanfang_stars = {s for p in all_sanfang for s in p.main_stars}

    # -----------------------------------------------------------------------
    # 格局 1: 杀破狼 (七杀、破军、贪狼在三方四正)
    # -----------------------------------------------------------------------
    if {"七杀", "破军", "贪狼"}.issubset(all_sanfang_stars):
        patterns.append("杀破狼")

    # -----------------------------------------------------------------------
    # 格局 2: 府相朝垣 (天府在命宫，天相在对宫；或天相在命宫，天府在对宫)
    # -----------------------------------------------------------------------
    if ({"天府"}.issubset(ming.main_stars) and {"天相"}.issubset(dui.main_stars)) or \
       ({"天相"}.issubset(ming.main_stars) and {"天府"}.issubset(dui.main_stars)):
        patterns.append("府相朝垣")

    # -----------------------------------------------------------------------
    # 格局 3: 紫府同宫 (紫微和天府同宫)
    # -----------------------------------------------------------------------
    for p in palaces:
        if {"紫微", "天府"}.issubset(p.main_stars):
            patterns.append("紫府同宫")
            break

    # -----------------------------------------------------------------------
    # 格局 4: 日月同明 / 日月并明 (太阳和太阴都在庙旺位置，三方四正有吉星)
    # 规则简化：太阳在卯/辰/巳/午，太阴在酉/戌/亥/子，且同时出现在三方四正
    # -----------------------------------------------------------------------
    taiyang = next((p for p in all_sanfang if "太阳" in p.main_stars), None)
    taiyin = next((p for p in all_sanfang if "太阴" in p.main_stars), None)
    if taiyang and taiyin:
        taiyang_miao = taiyang.earthly_branch in ["卯", "辰", "巳", "午"]
        taiyin_miao = taiyin.earthly_branch in ["酉", "戌", "亥", "子"]
        if taiyang_miao and taiyin_miao:
            patterns.append("日月同明")

    # -----------------------------------------------------------------------
    # 格局 5: 机月同梁 (天机、太阴、天同、天梁在三方四正)
    # -----------------------------------------------------------------------
    if {"天机", "太阴", "天同", "天梁"}.issubset(all_sanfang_stars):
        patterns.append("机月同梁")

    # -----------------------------------------------------------------------
    # 格局 6: 贪武同行 (贪狼和武曲同宫)
    # -----------------------------------------------------------------------
    for p in palaces:
        if {"贪狼", "武曲"}.issubset(p.main_stars):
            patterns.append("贪武同行")
            break

    # -----------------------------------------------------------------------
    # 格局 7: 紫府朝垣 (紫微、天府在三方朝拱命宫)
    # -----------------------------------------------------------------------
    if {"紫微", "天府"}.issubset(all_sanfang_stars) and not any({"紫微", "天府"}.issubset(p.main_stars) for p in [ming]):
        patterns.append("紫府朝垣")

    # -----------------------------------------------------------------------
    # 格局 8: 科权禄夹格 (化科、化权、化禄夹命宫) —— 需四化支持，暂时预留
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # 格局 9: 左右昌曲夹格 (左辅、右弼/文昌、文曲夹命宫) —— 需辅星支持，暂时预留
    # -----------------------------------------------------------------------

    # -----------------------------------------------------------------------
    # 格局 10: 空劫夹命格 (地空、地劫夹命宫) —— 需辅星支持，暂时预留
    # -----------------------------------------------------------------------

    # 去重返回
    return list(set(patterns))

