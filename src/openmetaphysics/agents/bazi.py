"""Bazi (八字) agent — deterministic four-pillar calculation.

Year/month pillars are anchored on solar-term boundaries (立春 year start,
节 month start). Day pillar uses the sexagenary day cycle with a 23:00 rollover.
Hour pillar uses 五鼠遁. Includes 藏干, 纳音, 十神, and 大运 (decade luck).
No LLM anywhere in compute().
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from ..core.calendar import (
    UTC,
    _month_boundaries,
    bazi_year_index,
    month_boundary_before,
    sexagenary_day_index,
)
from ..core.engines import BaseAgent, DeterministicEngine
from ..core.models import (
    BRANCH_HIDDEN_STEMS,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    STEM_ELEMENT,
    STEM_YIN_YANG,
    nayin_for,
    sexagenary_index,
    sexagenary_pair,
    wuxing_relation,
)
from ..core.schemas import AgentInput, AgentOutput, Gender


class BaziInput(AgentInput):
    dayun_count: int = 8  # number of 大运 decades to compute


class Pillar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    position: Literal["year", "month", "day", "hour"]
    stem: str
    branch: str
    stem_index: int
    branch_index: int
    hidden_stems: list[str]
    nayin: str
    ten_god: str  # 十神 of this pillar's stem relative to day master


class DaYun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    index: int
    start_age: int
    end_age: int
    stem: str
    branch: str
    stem_index: int
    branch_index: int
    start_at: datetime


class BaziChart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    day_master: str
    day_master_element: str
    pillars: list[Pillar]
    dayun: list[DaYun]
    ten_gods_map: dict[str, str]
    year_boundary: datetime
    month_boundary: str  # 节 term name governing the month pillar
    gender_assumed: bool


class BaziOutput(AgentOutput):
    agent: str = "bazi"
    result: BaziChart


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ten_god(day_stem: str, other_stem: str) -> str:
    de, oe = STEM_ELEMENT[day_stem], STEM_ELEMENT[other_stem]
    rel = wuxing_relation(de, oe)
    same = STEM_YIN_YANG[day_stem] == STEM_YIN_YANG[other_stem]
    return {
        "same": "比肩" if same else "劫财",
        "being_sheng": "偏印" if same else "正印",
        "sheng": "食神" if same else "伤官",
        "being_ke": "七杀" if same else "正官",
        "ke": "偏财" if same else "正财",
    }[rel]


def _boundaries_around(born_at) -> tuple[tuple[int, str, Any], tuple[int, str, Any]]:
    y = born_at.astimezone(UTC).year
    cands = sorted(
        _month_boundaries(y - 1) + _month_boundaries(y) + _month_boundaries(y + 1),
        key=lambda x: x[0],
    )
    prev = cands[0]
    nxt = cands[-1]
    for t, b, tn in cands:
        if t <= born_at:
            prev = (b, tn, t)
        else:
            nxt = (b, tn, t)
            break
    return prev, nxt


def _add_years(dt, n: int):
    y = dt.year + n
    try:
        return dt.replace(year=y)
    except ValueError:
        return dt.replace(year=y, day=28)


def _local_tz(payload: BaziInput):
    if payload.born_location and payload.born_location.timezone:
        from zoneinfo import ZoneInfo

        try:
            return ZoneInfo(payload.born_location.timezone)
        except Exception:
            return payload.born_at.tzinfo or UTC
    return payload.born_at.tzinfo or UTC


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
class BaziEngine(DeterministicEngine):
    version = "0.1.0"

    def calculate(self, payload: BaziInput) -> dict[str, Any]:
        born = payload.born_at

        # --- year pillar (立春 boundary) ---
        year_idx, year_boundary = bazi_year_index(born)
        year_stem, year_branch = sexagenary_pair(year_idx)
        self.trace.record(
            "bazi.year_pillar",
            "sexagenary year on 立春 boundary",
            inputs={"lichun_year": (year_idx + 4) % 60 + 4},
            outputs={"stem": year_stem, "branch": year_branch, "idx": year_idx},
        )

        # --- month pillar (节 boundary) ---
        m_branch_idx, m_term, _m_time = month_boundary_before(born)
        year_stem_idx = year_idx % 10
        yin_month_stem = (year_stem_idx * 2 + 2) % 10  # 五虎遁
        month_stem_idx = (yin_month_stem + (m_branch_idx - 2)) % 10
        month_stem = HEAVENLY_STEMS[month_stem_idx]
        month_branch = EARTHLY_BRANCHES[m_branch_idx]
        self.trace.record(
            "bazi.month_pillar",
            "month stem/branch on 节 boundary (五虎遁)",
            inputs={"boundary_term": m_term},
            outputs={"stem": month_stem, "branch": month_branch},
        )

        # --- day pillar (sexagenary day, 23:00 rollover) ---
        tz = _local_tz(payload)
        local = born.astimezone(tz)
        eff = local + timedelta(days=1) if local.hour >= 23 else local
        day_idx = sexagenary_day_index(eff.year, eff.month, eff.day)
        day_stem, day_branch = sexagenary_pair(day_idx)
        self.trace.record(
            "bazi.day_pillar",
            "sexagenary day cycle (JDN+49), 23:00 rollover",
            inputs={"local_date": str(eff.date())},
            outputs={"stem": day_stem, "branch": day_branch, "idx": day_idx},
        )

        # --- hour pillar (五鼠遁) ---
        hour_branch_idx = ((local.hour + 1) // 2) % 12
        hour_stem_idx = ((day_idx % 10) * 2 + hour_branch_idx) % 10
        hour_stem = HEAVENLY_STEMS[hour_stem_idx]
        hour_branch = EARTHLY_BRANCHES[hour_branch_idx]
        self.trace.record(
            "bazi.hour_pillar",
            "hour stem/branch (五鼠遁)",
            inputs={"local_hour": local.hour},
            outputs={"stem": hour_stem, "branch": hour_branch},
        )

        day_master = day_stem
        day_master_element = STEM_ELEMENT[day_master]

        def pillar(pos, stem, branch, sidx, bidx) -> Pillar:
            return Pillar(
                position=pos,
                stem=stem,
                branch=branch,
                stem_index=sidx,
                branch_index=bidx,
                hidden_stems=BRANCH_HIDDEN_STEMS[branch],
                nayin=nayin_for(stem, branch),
                ten_god=_ten_god(day_master, stem),
            )

        pillars = [
            pillar("year", year_stem, year_branch, year_idx % 10, year_idx % 12),
            pillar("month", month_stem, month_branch, month_stem_idx, m_branch_idx),
            pillar("day", day_stem, day_branch, day_idx % 10, day_idx % 12),
            pillar("hour", hour_stem, hour_branch, hour_stem_idx, hour_branch_idx),
        ]

        # 十神 map: every appearing stem (incl. hidden) -> 十神 vs day master
        ten_gods_map: dict[str, str] = {}
        for p in pillars:
            ten_gods_map[p.stem] = _ten_god(day_master, p.stem)
        for p in pillars:
            for hs in p.hidden_stems:
                if hs not in ten_gods_map:
                    ten_gods_map[hs] = _ten_god(day_master, hs)
        self.trace.record(
            "bazi.ten_gods", "derive 十神 vs day master", outputs={"count": len(ten_gods_map)}
        )

        # --- 大运 ---
        dayun = self._dayun(payload, local, month_stem, month_branch, year_stem)

        chart = BaziChart(
            day_master=day_master,
            day_master_element=day_master_element,
            pillars=pillars,
            dayun=dayun,
            ten_gods_map=ten_gods_map,
            year_boundary=year_boundary,
            month_boundary=m_term,
            gender_assumed=(payload.gender == Gender.UNKNOWN),
        )
        return chart.model_dump(mode="json")

    def _dayun(self, payload: BaziInput, local, month_stem, month_branch, year_stem) -> list[DaYun]:
        prev, nxt = _boundaries_around(payload.born_at)
        yang_year = STEM_YIN_YANG[year_stem] == "阳"
        female = payload.gender == Gender.FEMALE
        forward = (yang_year and not female) or ((not yang_year) and female)
        if forward:
            days = (nxt[2] - payload.born_at).total_seconds() / 86400.0
        else:
            days = (payload.born_at - prev[2]).total_seconds() / 86400.0
        start_age = max(0, round(days / 3.0))
        self.trace.record(
            "bazi.dayun.direction",
            "大运 direction by gender+year polarity",
            inputs={"forward": forward, "days_to_boundary": round(days, 3)},
            outputs={"start_age": start_age},
        )
        month_idx = sexagenary_index(month_stem, month_branch)
        dir_step = 1 if forward else -1
        out: list[DaYun] = []
        for k in range(payload.dayun_count):
            idx = (month_idx + (k + 1) * dir_step) % 60
            stem, branch = sexagenary_pair(idx)
            sa = start_age + 10 * k
            out.append(
                DaYun(
                    index=k + 1,
                    start_age=sa,
                    end_age=sa + 10,
                    stem=stem,
                    branch=branch,
                    stem_index=idx % 10,
                    branch_index=idx % 12,
                    start_at=_add_years(local, sa),
                )
            )
        return out


class BaziAgent(BaseAgent):
    name = "bazi"
    engine_version = BaziEngine.version
    input_schema = BaziInput
    output_schema = BaziOutput
    engine = BaziEngine()

    def _compute_result(self, payload: BaziInput) -> dict[str, Any]:
        return self.engine.calculate(payload)

    def _metadata(self) -> dict[str, str | int | float | bool]:
        return {
            "engine_version": self.engine_version,
            "deterministic": True,
            "solar_term_precision": "approx_1min",
        }

    def _explain_fallback(self, output: BaziOutput, *, style: str = "concise") -> str:
        r = output.result
        p = {x.position: x for x in r.pillars}
        return (
            f"日主: {r.day_master}({r.day_master_element}) | "
            f"年: {p['year'].stem}{p['year'].branch} 月: {p['month'].stem}{p['month'].branch} "
            f"日: {p['day'].stem}{p['day'].branch} 时: {p['hour'].stem}{p['hour'].branch} | "
            f"起运: {r.dayun[0].start_age}岁 ({len(r.dayun)}步大运)"
        )
