"""Liuyao Reference Runtime — deterministic hexagram divination.

Self-contained reference implementation of the behaviour already present in the
Production agent (``src/openmetaphysics/agents/liuyao.py``). It exists so that
the production output can be compared against an independent implementation
(see ``reference/tests/test_liuyao_equivalence.py``).

Rules expressed here are exactly the rules the production engine already
implements; nothing was added or "corrected":

  LY-01 cast acquisition      explicit casts, else seeded three-coin casting
  LY-02 本卦 line derivation   6/8 -> 阴, 7/9 -> 阳; 6/9 -> changing
  LY-03 变卦 derivation        changing lines flip (9->8, 6->7)
  LY-04 互卦 derivation        lines 2,3,4 / 3,4,5, forced stable
  LY-05 King Wen identification
  LY-06 京房八宫 palace assignment
  LY-07 世应 assignment by palace position
  LY-08 纳甲 stem/branch per line
  LY-09 六亲 by palace-element relation
  LY-10 六神 by day stem (23:00 day rollover)
  LY-11 用神 selection by question keywords

This module MUST NOT import ``openmetaphysics``.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from datetime import timezone as _timezone
from typing import Any

from .astronomy import sexagenary_day_index
from .tables import (
    BA_GONG,
    BRANCH_ELEMENT,
    HEAVENLY_STEMS,
    HEXAGRAMS,
    LIU_QIN_BY_RELATION,
    NAJIA_STEM,
    SHI_BY_POS,
    SIX_SPIRITS,
    SPIRIT_START_BY_STEM,
    YONG_SHEN_RULES,
    hexagram_from_lines,
    najia_branch,
    wuxing_relation,
)

__all__ = ["VERSION", "compute"]

VERSION = "0.1.0"

# 京房八宫 lookup tables (hexagram number -> palace / position within palace)
_PALACE_OF: dict[int, str] = {}
_PALACE_POS: dict[int, int] = {}
for _palace, _nums in BA_GONG:
    for _pos, _num in enumerate(_nums, start=1):
        _PALACE_OF[_num] = _palace
        _PALACE_POS[_num] = _pos


# ---------------------------------------------------------------------------
# LY-01  cast acquisition
# ---------------------------------------------------------------------------
def _three_coin_casts(seed: int) -> list[int]:
    """Six three-coin casts (bottom -> top), 3 coins of 2/3 each.

    Mirrors the production deterministic RNG so seeded inputs replay exactly.
    """
    import random

    rng = random.Random(seed)
    return [sum(rng.choice([2, 3]) for _ in range(3)) for _ in range(6)]


# ---------------------------------------------------------------------------
# LY-02 / LY-03  line derivation
# ---------------------------------------------------------------------------
def _yao(position: int, cast: int, force_stable: bool = False) -> dict[str, Any]:
    is_yin = cast in (6, 8)
    is_changing = (cast in (6, 9)) and not force_stable
    return {
        "position": position,
        "is_yin": is_yin,
        "is_changing": is_changing,
        "cast_value": cast,
    }


def _changed_yao(position: int, cast: int) -> dict[str, Any]:
    if cast in (6, 9):
        flipped = 8 if cast == 9 else 7
        return {
            "position": position,
            "is_yin": flipped in (6, 8),
            "is_changing": False,
            "cast_value": flipped,
        }
    return _yao(position, cast)


# ---------------------------------------------------------------------------
# LY-11  用神
# ---------------------------------------------------------------------------
def select_yong_shen(question: str | None) -> str:
    if not question:
        return "世爻"
    for keys, qin in YONG_SHEN_RULES:
        if any(k in question for k in keys):
            return qin
    return "世爻"


# ---------------------------------------------------------------------------
# The reference computation
# ---------------------------------------------------------------------------
def compute(payload: dict[str, Any]) -> dict[str, Any]:
    """Compute a Liuyao chart.

    ``payload``: ``{"born_at": ISO-8601 str, "casts": [6 ints] | null,
    "question": str | null, "seed": int | null}``
    """
    born_at = payload["born_at"]
    born = datetime.fromisoformat(born_at) if isinstance(born_at, str) else born_at
    if born.tzinfo is None:
        born = born.replace(tzinfo=_timezone.utc)

    casts = payload.get("casts")
    if casts is None:
        seed = payload.get("seed")
        if seed is None:
            raise ValueError("reference requires explicit casts or an explicit seed")
        casts = _three_coin_casts(int(seed))
    casts = [int(c) for c in casts]
    if len(casts) != 6 or any(c not in (6, 7, 8, 9) for c in casts):
        raise ValueError("casts must be 6 values in {6,7,8,9}")

    # LY-02 / LY-03 / LY-04
    original = [_yao(i + 1, c) for i, c in enumerate(casts)]
    changed = [_changed_yao(i + 1, c) for i, c in enumerate(casts)]
    mutual_casts = [casts[1], casts[2], casts[3], casts[2], casts[3], casts[4]]
    mutual = [_yao(i + 1, c, force_stable=True) for i, c in enumerate(mutual_casts)]

    # LY-05
    orig_lines = [0 if y["is_yin"] else 1 for y in original]
    orig_hex = hexagram_from_lines(orig_lines)["num"]

    changed_hex: int | None = None
    if any(y["is_changing"] for y in original):
        changed_lines = [0 if y["is_yin"] else 1 for y in changed]
        changed_hex = hexagram_from_lines(changed_lines)["num"]

    mutual_lines = [0 if y["is_yin"] else 1 for y in mutual]
    mutual_hex = hexagram_from_lines(mutual_lines)["num"]

    # LY-06 / LY-07
    palace = _PALACE_OF[orig_hex]
    palace_pos = _PALACE_POS[orig_hex]
    palace_element = _TRIGRAM_ELEMENT[palace]
    shi = SHI_BY_POS[palace_pos]
    ying = ((shi + 2) % 6) + 1

    # LY-08 / LY-09
    entry = HEXAGRAMS[orig_hex - 1]
    lower, upper = entry["lower"], entry["upper"]
    najia: list[str] = []
    liu_qin: list[str] = []
    for i in range(6):
        tri = lower if i < 3 else upper
        is_outer = i >= 3
        slot = i if i < 3 else i - 3
        stem_idx = NAJIA_STEM[tri][1 if is_outer else 0]
        branch = najia_branch(tri, slot, is_outer)
        najia.append(f"{HEAVENLY_STEMS[stem_idx]}{branch}")
        relation = wuxing_relation(palace_element, BRANCH_ELEMENT[branch])
        liu_qin.append(LIU_QIN_BY_RELATION[relation])

    # LY-10  六神 by day stem (23:00 rollover)
    day_index = sexagenary_day_index(born.year, born.month, born.day)
    if born.hour >= 23:
        nxt = born + timedelta(days=1)
        day_index = sexagenary_day_index(nxt.year, nxt.month, nxt.day)
    day_stem_idx = day_index % 10
    spirit_start = SPIRIT_START_BY_STEM[day_stem_idx]
    liu_shen = [SIX_SPIRITS[(spirit_start + i) % 6] for i in range(6)]

    # LY-11
    yong_shen = select_yong_shen(payload.get("question"))

    return {
        "original": original,
        "changed": changed,
        "mutual": mutual,
        "original_hexagram": orig_hex,
        "changed_hexagram": changed_hex,
        "mutual_hexagram": mutual_hex,
        "najia": najia,
        "liu_qin": liu_qin,
        "liu_shen": liu_shen,
        "shi_position": shi,
        "ying_position": ying,
        "palace": palace,
        "palace_element": palace_element,
        "yong_shen": yong_shen,
    }


# trigram elements (kept separate from the tables module's richer TRIGRAMS dict)
from .tables import TRIGRAMS as _TRIGRAMS  # noqa: E402

_TRIGRAM_ELEMENT: dict[str, str] = {name: info["element"] for name, info in _TRIGRAMS.items()}
