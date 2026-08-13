"""Ziwei (紫微斗数) agent — deterministic rule-based placement engine.

Core placement is canonical and deterministic: 命宫/身宫 (from lunar month +
birth hour), 阴阳 (year stem polarity), 五行局 (via 命宫干支 纳音), full
14 major stars placement via canonical 紫微定局. Auxiliary stars, flowing
year, and 四化 are Phase 5/6. No LLM in compute().
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..core.calendar import (
    bazi_year_index,
    solar_to_lunar,
)
from ..core.engines import BaseAgent, DeterministicEngine
from ..core.models import (
    HEAVENLY_STEMS,
    STEM_YIN_YANG,
    nayin_for,
)
from ..core.schemas import AgentInput, AgentOutput

# 12-palace array starting at 寅 (clockwise branch order, index 0..11)
PALACE_BRANCHES = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
PALACE_NAMES = [
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
JU_NUMBER = {"水": 2, "木": 3, "金": 4, "土": 5, "火": 6}

# ---------------------------------------------------------------------------
# 紫微定局: 紫微 palace index from (ju: 2-6, lunar_day: 1-30)
# Canonical rule (ACP-ZW-001, 2026-08-13):
#   idx = (START[ju] + (day - 1) // STEP[ju]) % 12
#   START 起宫: 水二丑 / 木三辰 / 金四亥 / 土五午 / 火六酉
#   STEP 步长: 水二 2 日, 木三/金四/土五/火六 3 日
#   Invariants: 木三局不落寅卯 / 金四局不落酉戌 / 土五局不落辰巳 / 火六局不落未申
# ---------------------------------------------------------------------------
ZIWEI_JU_START: dict[int, int] = {2: 11, 3: 2, 4: 9, 5: 4, 6: 7}
ZIWEI_JU_STEP: dict[int, int] = {2: 2, 3: 3, 4: 3, 5: 3, 6: 3}


def _ziwei_pos_table() -> dict[int, dict[int, int]]:
    return {
        ju: {
            day: (ZIWEI_JU_START[ju] + (day - 1) // ZIWEI_JU_STEP[ju]) % 12 for day in range(1, 31)
        }
        for ju in sorted(ZIWEI_JU_START)
    }


ZIWEI_POS: dict[int, dict[int, int]] = _ziwei_pos_table()

# 14 major stars: 紫微星系 (relative to Ziwei position,逆行) + 天府星系 (relative to Tianfu position,顺行)
# 紫微星系: [name: offset from 紫微 (逆行 = negative)]
# 廉贞 -8 (ACP-ZW-002, 2026-08-13): "隔一阳武天同居, 又隔二位廉贞地"
ZIWEI_XINGXI: list[tuple[str, int]] = [
    ("紫微", 0),
    ("天机", -1),
    ("太阳", -3),
    ("武曲", -4),
    ("天同", -5),
    ("廉贞", -8),
]

# 天府星系: [name: offset from 天府 (顺行 = positive)]
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


class ZiweiInput(AgentInput):
    lunar_month: int | None = None  # 1..12; None -> compute from solar date
    lunar_day: int | None = None  # 1..30; None -> compute from solar date

    @model_validator(mode="after")
    def _validate_lunar_fields(self) -> ZiweiInput:
        # ACP-ZW-003 (2026-08-13): explicit validation per contract —
        # both-or-neither provision, month in [1,12], day in [1,30].
        if (self.lunar_month is None) != (self.lunar_day is None):
            raise ValueError("lunar_month and lunar_day must be provided together")
        if self.lunar_month is not None and not 1 <= self.lunar_month <= 12:
            raise ValueError("lunar_month must be in 1..12")
        if self.lunar_day is not None and not 1 <= self.lunar_day <= 30:
            raise ValueError("lunar_day must be in 1..30")
        return self


class Palace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    index: int = Field(ge=0, le=11)  # position in PALACE_BRANCHES (0..11)
    name: str
    earthly_branch: str
    heavenly_stem: str
    main_stars: list[str] = Field(default_factory=list)
    auxiliary_stars: list[str] = Field(default_factory=list)
    is_fate_palace: bool = False
    is_body_palace: bool = False


class ZiweiChart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fate_palace_index: int
    body_palace_index: int
    yin_yang: Literal["yin", "yang"]
    wuxing_ju: str  # e.g. "水二局"
    palaces: list[Palace]  # 12 palaces
    calendar_note: str | None = None


class ZiweiOutput(AgentOutput):
    agent: str = "ziwei"
    result: ZiweiChart


def _local_tz(payload: ZiweiInput):
    if payload.born_location and payload.born_location.timezone:
        from zoneinfo import ZoneInfo

        try:
            return ZoneInfo(payload.born_location.timezone)
        except Exception:
            return payload.born_at.tzinfo
    return payload.born_at.tzinfo


def _local_hour_branch(local_dt) -> int:
    # hour branch index 0..11 (子=0..亥=11) from local civil hour
    return ((local_dt.hour + 1) // 2) % 12


class ZiweiEngine(DeterministicEngine):
    version = "0.3.0"  # ACP-ZW-001/002/003 (2026-08-13): canonical 定局表 + 廉贞 -8 + 输入校验

    def calculate(self, payload: ZiweiInput) -> dict[str, Any]:
        born = payload.born_at
        local_tz = _local_tz(payload)
        local = born.astimezone(local_tz)
        hour_idx = _local_hour_branch(local)
        calendar_note = None

        # Get lunar date: use user-provided if available, else compute via sxtwl
        if payload.lunar_month is not None and payload.lunar_day is not None:
            month = payload.lunar_month
            day = payload.lunar_day
        else:
            ly, lm, ld, leap = solar_to_lunar(local.year, local.month, local.day)
            month = lm
            day = ld
            if leap:
                calendar_note = f"leap month {lm} (闰月) using month number {lm} for placement"

        # 命宫 / 身宫 calculation: 命宫 = ((month-1) - hour_idx) % 12; 身宫 = ((month-1) + hour_idx) % 12
        ming_index = ((month - 1) - hour_idx) % 12
        shen_index = ((month - 1) + hour_idx) % 12
        self.trace.record(
            "ziwei.fate_body_palace",
            "命宫/身宫 from lunar month + hour",
            inputs={"lunar_month": month, "lunar_day": day, "hour_branch_idx": hour_idx},
            outputs={"fate_index": ming_index, "body_index": shen_index},
        )

        # Year stem uses Lichun boundary consistent with Bazi
        year_idx, _ = bazi_year_index(born)
        year_stem_idx = year_idx % 10
        yin_month_stem = (year_stem_idx * 2 + 2) % 10  # 五虎遁: 甲己起丙寅
        yin_yang = "yang" if STEM_YIN_YANG[HEAVENLY_STEMS[year_stem_idx]] == "阳" else "yin"

        # 五行局 via 纳音 of 命宫干支
        ming_stem_idx = (yin_month_stem + ming_index) % 10
        ming_stem = HEAVENLY_STEMS[ming_stem_idx]
        ming_branch = PALACE_BRANCHES[ming_index]
        nayin = nayin_for(ming_stem, ming_branch)
        ju_elem = nayin[-1]
        ju = JU_NUMBER[ju_elem]
        wuxing_ju = f"{ju_elem}{ju}局"
        self.trace.record(
            "ziwei.wuxing_ju",
            "五行局 via 命宫干支 纳音",
            outputs={"ming_ganzhi": ming_stem + ming_branch, "nayin": nayin, "ju": wuxing_ju},
        )

        # Generate 12 palaces with stem/branch, name, fate/body flags
        palaces: list[Palace] = []
        for i in range(12):
            stem_idx = (yin_month_stem + i) % 10
            name = PALACE_NAMES[(ming_index - i) % 12]
            p = Palace(
                index=i,
                name=name,
                earthly_branch=PALACE_BRANCHES[i],
                heavenly_stem=HEAVENLY_STEMS[stem_idx],
                is_fate_palace=(i == ming_index),
                is_body_palace=(i == shen_index),
            )
            palaces.append(p)

        # Place 14 major stars
        zw_index = ZIWEI_POS[ju][day]
        tf_index = (-zw_index) % 12  # 天府 is mirror across 寅-申 axis
        self.trace.record(
            "ziwei.ziwei_position",
            "紫微 position from 定局: 五行局数 + lunar birth day",
            outputs={"ju": ju, "lunar_day": day, "ziwei_index": zw_index, "tianfu_index": tf_index},
        )

        # Place 紫微星系 (relative to 紫微,逆行 = subtract offset)
        for name, offset in ZIWEI_XINGXI:
            idx = (zw_index + offset) % 12
            palaces[idx].main_stars.append(name)

        # Place 天府星系 (relative to 天府,顺行 = add offset)
        for name, offset in TIANFU_XINGXI:
            idx = (tf_index + offset) % 12
            palaces[idx].main_stars.append(name)

        self.trace.record(
            "ziwei.main_stars",
            "14 major stars placement complete",
            outputs={"total_stars": len(ZIWEI_XINGXI) + len(TIANFU_XINGXI)},
        )

        chart = ZiweiChart(
            fate_palace_index=ming_index,
            body_palace_index=shen_index,
            yin_yang=yin_yang,
            wuxing_ju=wuxing_ju,
            palaces=palaces,
            calendar_note=calendar_note,
        )
        return chart.model_dump(mode="json")


class ZiweiAgent(BaseAgent):
    name = "ziwei"
    engine_version = ZiweiEngine.version
    input_schema = ZiweiInput
    output_schema = ZiweiOutput
    engine = ZiweiEngine()

    def _compute_result(self, payload: ZiweiInput) -> dict[str, Any]:
        return self.engine.calculate(payload)

    def _metadata(self) -> dict[str, str | int | float | bool]:
        return {
            "engine_version": self.engine_version,
            "deterministic": True,
            "star_placement": "14_major_stars",
            "calendar_conversion": "sxtwl",
        }

    def _explain_fallback(self, output: ZiweiOutput, *, style: str = "concise") -> str:
        r = output.result
        fp = next(p for p in r.palaces if p.is_fate_palace)
        stars = [s for p in r.palaces for s in p.main_stars if s]
        return (
            f"[{self.name}] {r.wuxing_ju} | 命宫 {fp.heavenly_stem}{fp.earthly_branch} "
            f"| 14主星: {', '.join(stars)}"
        )
