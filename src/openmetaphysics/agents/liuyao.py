"""Liuyao (六爻) agent — deterministic hexagram divination.

Full reference implementation: seeded coin casting, 本/变/互 hexagrams, 纳甲,
六亲, 六神, 世应, and rule-based 用神 selection. No LLM anywhere in compute().
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..core.engines import BaseAgent, DeterministicEngine, derive_seed, deterministic_rng
from ..core.models import (
    BRANCH_ELEMENT,
    HEAVENLY_STEMS,
    HEXAGRAMS,
    TRIGRAMS,
    hexagram_from_lines,
    wuxing_relation,
)
from ..core.schemas import AgentInput, AgentOutput


# ---------------------------------------------------------------------------
# Input / output schemas
# ---------------------------------------------------------------------------
class LiuyaoInput(AgentInput):
    casts: list[int] | None = None  # optional 6 cast values (6/7/8/9), bottom->top

    @field_validator("casts")
    @classmethod
    def _check_casts(cls, v: list[int] | None) -> list[int] | None:
        if v is None:
            return v
        if len(v) != 6:
            raise ValueError("casts must have exactly 6 values (bottom->top)")
        if any(c not in (6, 7, 8, 9) for c in v):
            raise ValueError("each cast value must be 6,7,8 or 9")
        return v


class YaoLine(BaseModel):
    model_config = ConfigDict(extra="forbid")
    position: int = Field(ge=1, le=6)  # 初爻..上爻
    is_yin: bool
    is_changing: bool
    cast_value: int  # 6(老阴) 7(少阳) 8(少阴) 9(老阳)


class LiuyaoChart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    original: list[YaoLine]
    changed: list[YaoLine]
    mutual: list[YaoLine]
    original_hexagram: int  # King Wen number 1..64
    changed_hexagram: int | None
    mutual_hexagram: int | None
    najia: list[str]  # 干支 per line, bottom->top
    liu_qin: list[str]  # 六亲 per line
    liu_shen: list[str]  # 六神 per line
    shi_position: int  # 1..6
    ying_position: int  # 1..6
    palace: str
    palace_element: str
    yong_shen: str | None = None


class LiuyaoOutput(AgentOutput):
    agent: str = "liuyao"
    result: LiuyaoChart


# ---------------------------------------------------------------------------
# Reference tables (Liuyao-specific)
# ---------------------------------------------------------------------------
# 京房八宫: palace -> [8 hexagram numbers in palace order (本宫,一世..归魂)]
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

_PALACE_OF: dict[int, str] = {}
_PALACE_POS: dict[int, int] = {}
for _palace, _nums in BA_GONG:
    for _pos, _num in enumerate(_nums, start=1):
        _PALACE_OF[_num] = _palace
        _PALACE_POS[_num] = _pos

# 世 position (1-indexed) by palace position 1..8
SHI_BY_POS: dict[int, int] = {1: 6, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 4, 8: 3}

# 纳甲 stems (inner, outer) per trigram, by stem index
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
YANG_TRIGRAMS = {"乾", "震", "坎", "艮"}
YANG_BRANCHES = ["子", "寅", "辰", "午", "申", "戌"]  # ascending
YIN_BRANCHES = ["丑", "卯", "巳", "未", "酉", "亥"]  # ascending; assigned descending
_YANG_START = {"乾": 0, "震": 0, "坎": 1, "艮": 2}
_YIN_START = {"坤": 3, "巽": 0, "离": 1, "兑": 2}

SIX_SPIRITS = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]
SPIRIT_START_BY_STEM = {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5}

LIU_QIN_BY_RELATION = {
    "same": "兄弟",
    "sheng": "子孙",
    "being_sheng": "父母",
    "ke": "妻财",
    "being_ke": "官鬼",
}

# Rule-based 用神 keywords -> 六亲
YONG_SHEN_RULES: list[tuple[tuple[str, ...], str]] = [
    (("财", "钱", "利", "薪", "买卖", "交易", "投资"), "妻财"),
    (("官", "功名", "事业", "升迁", "官司", "丈夫", "工作", "考试升"), "官鬼"),
    (("父", "母", "长辈", "文书", "房", "屋", "学", "考"), "父母"),
    (("兄", "弟", "朋友", "同事", "合伙"), "兄弟"),
    (("子", "女", "晚辈", "下属", "平安", "出行", "药", "医", "求谋"), "子孙"),
]


def _najia_branch(trigram: str, slot: int, is_outer: bool) -> str:
    """Branch for trigram line slot (0,1,2) in inner/outer trigram."""
    if trigram in YANG_TRIGRAMS:
        start = _YANG_START[trigram]
        idx = (start + (3 if is_outer else 0) + slot) % 6
        return YANG_BRANCHES[idx]
    start = _YIN_START[trigram]
    idx = (start - (3 if is_outer else 0) - slot) % 6
    return YIN_BRANCHES[idx]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
class LiuyaoEngine(DeterministicEngine):
    version = "0.1.0"

    def calculate(self, payload: LiuyaoInput) -> dict[str, Any]:
        casts = self._casts(payload)
        self.trace.record(
            "liuyao.cast",
            "determine 6 cast values (bottom->top)",
            inputs={"seed": payload.seed},
            outputs={"casts": casts},
        )

        original = [self._yao(i, c) for i, c in enumerate(casts)]
        changed = [self._changed_yao(i, c) for i, c in enumerate(casts)]
        # 互卦: lines 2,3,4 (idx1,2,3) -> lower; 3,4,5 (idx2,3,4) -> upper
        mutual_vals = [casts[1], casts[2], casts[3], casts[2], casts[3], casts[4]]
        mutual = [self._yao(i, c, force_stable=True) for i, c in enumerate(mutual_vals)]

        orig_lines = [0 if y.is_yin else 1 for y in original]
        orig_hex = hexagram_from_lines(orig_lines)["num"]
        self.trace.record(
            "liuyao.original_hexagram", "identify original hexagram", outputs={"king_wen": orig_hex}
        )

        changed_hex: int | None = None
        if any(y.is_changing for y in original):
            ch_lines = [0 if y.is_yin else 1 for y in changed]
            changed_hex = hexagram_from_lines(ch_lines)["num"]
            self.trace.record(
                "liuyao.changed_hexagram",
                "identify changed hexagram",
                outputs={"king_wen": changed_hex},
            )

        mutual_lines = [0 if y.is_yin else 1 for y in mutual]
        mutual_hex = hexagram_from_lines(mutual_lines)["num"]

        # palace / 世应
        palace = _PALACE_OF[orig_hex]
        palace_pos = _PALACE_POS[orig_hex]
        palace_element = TRIGRAMS[palace]["element"]
        shi = SHI_BY_POS[palace_pos]
        ying = ((shi + 2) % 6) + 1
        self.trace.record(
            "liuyao.shi_ying",
            "assign 世/应 by palace position",
            inputs={"palace": palace, "pos": palace_pos},
            outputs={"shi": shi, "ying": ying},
        )

        # 纳甲 / 六亲 per line
        lower = HEXAGRAMS[orig_hex - 1]["lower"]
        upper = HEXAGRAMS[orig_hex - 1]["upper"]
        najia: list[str] = []
        liu_qin: list[str] = []
        for i in range(6):
            tri = lower if i < 3 else upper
            is_outer = i >= 3
            slot = i if i < 3 else i - 3
            stem_idx = NAJIA_STEM[tri][1 if is_outer else 0]
            branch = _najia_branch(tri, slot, is_outer)
            najia.append(f"{HEAVENLY_STEMS[stem_idx]}{branch}")
            rel = wuxing_relation(palace_element, BRANCH_ELEMENT[branch])
            liu_qin.append(LIU_QIN_BY_RELATION[rel])
        self.trace.record(
            "liuyao.najia_liuqin",
            "assign 纳甲干支 and 六亲 per line",
            outputs={"najia": najia, "liu_qin": liu_qin},
        )

        # 六神 by day stem
        return self._assemble(
            payload,
            original,
            changed,
            mutual,
            orig_hex,
            changed_hex,
            mutual_hex,
            najia,
            liu_qin,
            palace,
            palace_element,
            shi,
            ying,
        )

    # -- helpers ----------------------------------------------------------
    def _casts(self, payload: LiuyaoInput) -> list[int]:
        if payload.casts is not None:
            return list(payload.casts)
        rng = deterministic_rng(derive_seed(payload))
        out = []
        for _ in range(6):
            out.append(sum(rng.choice([2, 3]) for _ in range(3)))
        return out

    @staticmethod
    def _yao(i: int, cast: int, force_stable: bool = False) -> YaoLine:
        is_yin = cast in (6, 8)
        is_changing = (cast in (6, 9)) and not force_stable
        return YaoLine(position=i + 1, is_yin=is_yin, is_changing=is_changing, cast_value=cast)

    @staticmethod
    def _changed_yao(i: int, cast: int) -> YaoLine:
        # changing lines flip yin<->yang and become stable in the changed hexagram
        if cast in (6, 9):
            flipped = 7 if cast == 9 else 8  # old yang->young yang? flip to opposite stable
            # 9(老阳)->变阴? In changed hexagram the line becomes its opposite: 9->8(阴), 6->7(阳)
            flipped = 8 if cast == 9 else 7
            is_yin = flipped in (6, 8)
            return YaoLine(position=i + 1, is_yin=is_yin, is_changing=False, cast_value=flipped)
        return LiuyaoEngine._yao(i, cast)

    def _assemble(
        self,
        payload,
        original,
        changed,
        mutual,
        orig_hex,
        changed_hex,
        mutual_hex,
        najia,
        liu_qin,
        palace,
        palace_element,
        shi,
        ying,
    ) -> dict[str, Any]:
        # 六神 needs the day stem -> compute from born_at's sexagenary day index
        from ..core.calendar import sexagenary_day_index

        b = payload.born_at
        day_idx = sexagenary_day_index(b.year, b.month, b.day)
        # apply 23:00 day rollover for 六神 day stem consistency
        if b.hour >= 23:
            from datetime import timedelta

            nb = b + timedelta(days=1)
            day_idx = sexagenary_day_index(nb.year, nb.month, nb.day)
        day_stem_idx = day_idx % 10
        spirit_start = SPIRIT_START_BY_STEM[day_stem_idx]
        liu_shen = [SIX_SPIRITS[(spirit_start + i) % 6] for i in range(6)]
        self.trace.record(
            "liuyao.liu_shen",
            "assign 六神 by day stem",
            inputs={"day_stem": HEAVENLY_STEMS[day_stem_idx]},
            outputs={"liu_shen": liu_shen},
        )

        yong_shen = self._yong_shen(payload.question, liu_qin)
        self.trace.record(
            "liuyao.yong_shen", "select 用神 by question keywords", outputs={"yong_shen": yong_shen}
        )

        chart = LiuyaoChart(
            original=original,
            changed=changed,
            mutual=mutual,
            original_hexagram=orig_hex,
            changed_hexagram=changed_hex,
            mutual_hexagram=mutual_hex,
            najia=najia,
            liu_qin=liu_qin,
            liu_shen=liu_shen,
            shi_position=shi,
            ying_position=ying,
            palace=palace,
            palace_element=palace_element,
            yong_shen=yong_shen,
        )
        return chart.model_dump()


def _select_yong_shen(question: str | None, liu_qin: list[str]) -> str | None:
    if not question:
        return "世爻"
    for keys, qin in YONG_SHEN_RULES:
        if any(k in question for k in keys):
            return qin
    return "世爻"


# attach as method to keep engine self-contained
LiuyaoEngine._yong_shen = staticmethod(_select_yong_shen)  # type: ignore[assignment]


class LiuyaoAgent(BaseAgent):
    name = "liuyao"
    engine_version = LiuyaoEngine.version
    input_schema = LiuyaoInput
    output_schema = LiuyaoOutput
    engine = LiuyaoEngine()

    def _compute_result(self, payload: LiuyaoInput) -> dict[str, Any]:
        return self.engine.calculate(payload)

    def _explain_fallback(self, output: LiuyaoOutput, *, style: str = "concise") -> str:
        r = output.result
        parts = [
            f"本卦: 第{r.original_hexagram}卦 ({HEXAGRAMS[r.original_hexagram - 1]['name']})",
            f"宫位: {r.palace}宫({r.palace_element})",
            f"世爻: 第{r.shi_position}爻, 应爻: 第{r.ying_position}爻",
            f"用神: {r.yong_shen}",
        ]
        if r.changed_hexagram:
            parts.append(
                f"变卦: 第{r.changed_hexagram}卦 ({HEXAGRAMS[r.changed_hexagram - 1]['name']})"
            )
        return " | ".join(parts)
