"""One-off generator: emit reference/liuyao/tables.py + astronomy.py.

The Reference Runtime must be self-contained (no src imports at runtime), so the
shared metaphysics tables it needs are emitted once as static Python literals
here. Regenerate only when the underlying tables change.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")

from openmetaphysics.agents import liuyao as L  # noqa: E402
from openmetaphysics.core import models as M  # noqa: E402

OUT = Path("reference/liuyao")
OUT.mkdir(parents=True, exist_ok=True)


def blk(name: str, value: object, annotation: str = "") -> str:
    ann = f": {annotation}" if annotation else ""
    return f"{name}{ann} = {value!r}\n"


header = '''"""Liuyao reference tables — self-contained (no src imports).

Generated once from the production metaphysics tables; the Reference Runtime
must not import ``openmetaphysics``. See reference/liuyao/README.md.
"""

from __future__ import annotations

'''

parts = [header]

# -- shared metaphysics tables --
parts.append("# == 五行 ==\n")
parts.append(blk("WUXING_SHENG", M.WUXING_SHENG, "dict[str, str]"))
parts.append(blk("WUXING_KE", M.WUXING_KE, "dict[str, str]"))
parts.append("\n# == 八卦 ==\n")
parts.append(blk("TRIGRAMS", M.TRIGRAMS, "dict[str, dict]"))
parts.append("\n# == 六十四卦 (King Wen) ==\n")
parts.append(blk("HEXAGRAMS", M.HEXAGRAMS, "list[dict]"))
parts.append("\n# == 天干地支 ==\n")
parts.append(blk("HEAVENLY_STEMS", M.HEAVENLY_STEMS, "list[str]"))
parts.append(blk("EARTHLY_BRANCHES", M.EARTHLY_BRANCHES, "list[str]"))
parts.append(blk("BRANCH_ELEMENT", M.BRANCH_ELEMENT, "dict[str, str]"))
parts.append("")

parts.append('''

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
''')

# -- liuyao-specific tables --
parts.append("\n\n# == 京房八宫 ==\n")
parts.append(blk("BA_GONG", L.BA_GONG, "list[tuple[str, list[int]]]"))
parts.append(blk("SHI_BY_POS", L.SHI_BY_POS, "dict[int, int]"))
parts.append("\n# == 纳甲 ==\n")
parts.append(blk("NAJIA_STEM", L.NAJIA_STEM, "dict[str, tuple[int, int]]"))
parts.append(blk("YANG_TRIGRAMS", L.YANG_TRIGRAMS, "set[str]"))
parts.append(blk("YANG_BRANCHES", L.YANG_BRANCHES, "list[str]"))
parts.append(blk("YIN_BRANCHES", L.YIN_BRANCHES, "list[str]"))
parts.append(blk("_YANG_START", L._YANG_START, "dict[str, int]"))
parts.append(blk("_YIN_START", L._YIN_START, "dict[str, int]"))
parts.append("\n# == 六神 / 六亲 / 用神 ==\n")
parts.append(blk("SIX_SPIRITS", L.SIX_SPIRITS, "list[str]"))
parts.append(blk("SPIRIT_START_BY_STEM", L.SPIRIT_START_BY_STEM, "dict[int, int]"))
parts.append(blk("LIU_QIN_BY_RELATION", L.LIU_QIN_BY_RELATION, "dict[str, str]"))
parts.append(blk("YONG_SHEN_RULES", L.YONG_SHEN_RULES, "list[tuple[tuple[str, ...], str]]"))
parts.append("")
parts.append('''

def najia_branch(trigram: str, slot: int, is_outer: bool) -> str:
    """Earthly branch for a trigram line slot (0,1,2) in the inner/outer trigram."""
    if trigram in YANG_TRIGRAMS:
        start = _YANG_START[trigram]
        idx = (start + (3 if is_outer else 0) + slot) % 6
        return YANG_BRANCHES[idx]
    start = _YIN_START[trigram]
    idx = (start - (3 if is_outer else 0) - slot) % 6
    return YIN_BRANCHES[idx]
''')

(OUT / "tables.py").write_text("".join(parts), encoding="utf-8", newline="\n")

astronomy = '''"""Liuyao reference astronomy — Julian Day Number / 干支纪日.

Self-contained: the Reference Runtime must not import ``openmetaphysics``.
"""

from __future__ import annotations


def julian_day_number(year: int, month: int, day: int) -> int:
    """Julian Day Number for a Gregorian date (integer, noon-based)."""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def sexagenary_day_index(year: int, month: int, day: int) -> int:
    """Sexagenary index 0..59 (甲子 = 0) for a Gregorian date."""
    return (julian_day_number(year, month, day) + 49) % 60
'''
(OUT / "astronomy.py").write_text(astronomy, encoding="utf-8", newline="\n")

print("wrote tables.py + astronomy.py")
