"""Reference BaZi domain — deterministic four-pillar computation.

Independent implementation of docs/bazi/BAZI_BEHAVIOR_CONTRACT.md v1.0.0
(BC-001~BC-014). Self-contained: no imports from openmetaphysics.

Normative sources (in order):
1. BAZI_BEHAVIOR_CONTRACT.md v1.0.0 (frozen clauses BC-001~014)
2. docs/bazi/golden_vectors.json (24 normative fixtures)
3. docs/bazi/BAZI_ALGORITHM_ASSUMPTIONS.md (B1~B6)

Input format (mirrors golden vector input):
    {"born_at": ISO8601 (tz-aware), "gender": "male"|"female"|"unknown",
     "born_location": {"timezone": IANA name} | None,
     "dayun_count": int = 8}

Output: JSON-serializable dict structurally identical to production
BaziChart.model_dump(mode="json") for exact equivalence testing.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .astronomy import (
    UTC,
    bazi_year_index,
    month_boundaries,
    month_boundary_before,
    sexagenary_day_index,
)
from .tables import (
    BRANCH_HIDDEN_STEMS,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    NAYIN,
    STEM_ELEMENT,
    STEM_YIN_YANG,
    sexagenary_index,
    sexagenary_pair,
    wuxing_relation,
)


def _local_tz(payload: dict) -> ZoneInfo | None:
    """BC-012 timezone resolution: born_location.timezone -> born_at.tzinfo -> UTC."""
    if payload.get("born_location") and payload["born_location"].get("timezone"):
        try:
            return ZoneInfo(payload["born_location"]["timezone"])
        except Exception:
            pass
    return payload["born_at"].tzinfo or UTC


def _add_years(dt: datetime, n: int) -> datetime:
    y = dt.year + n
    try:
        return dt.replace(year=y)
    except ValueError:
        return dt.replace(year=y, day=28)


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


def _boundaries_around(born_at: datetime) -> tuple[tuple, tuple]:
    y = born_at.astimezone(UTC).year
    cands = sorted(
        month_boundaries(y - 1) + month_boundaries(y) + month_boundaries(y + 1),
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


def _fmt_dt(dt: datetime) -> str:
    """Pydantic-v2-compatible datetime JSON serialization.

    Matches production BaziChart.model_dump(mode="json"): microseconds
    omitted when zero; UTC offsets rendered as 'Z'; others as +HH:MM.
    """
    base = dt.strftime("%Y-%m-%dT%H:%M:%S")
    if dt.microsecond:
        base += f".{dt.microsecond:06d}"
    off = dt.utcoffset()
    if off is None:
        return base
    if off == timedelta(0):
        return base + "Z"
    sign = "+" if off.total_seconds() >= 0 else "-"
    off = abs(off)
    return f"{base}{sign}{off.seconds // 3600:02d}:{(off.seconds % 3600) // 60:02d}"


def compute(payload: dict) -> dict:
    """Compute the full BaZi chart per BC-001~014."""
    born = payload["born_at"]
    dayun_count = int(payload.get("dayun_count", 8))

    # --- BC-002 year pillar (B1: Lichun boundary, UTC compare) ---
    year_idx, year_boundary = bazi_year_index(born)
    year_stem, year_branch = sexagenary_pair(year_idx)

    # --- BC-003 month pillar (B2: 12 节 + 五虎遁, UTC compare) ---
    m_branch_idx, m_term, _m_time = month_boundary_before(born)
    year_stem_idx = year_idx % 10
    yin_month_stem = (year_stem_idx * 2 + 2) % 10  # 五虎遁
    month_stem_idx = (yin_month_stem + (m_branch_idx - 2)) % 10
    month_stem = HEAVENLY_STEMS[month_stem_idx]
    month_branch = EARTHLY_BRANCHES[m_branch_idx]

    # --- BC-004 day pillar (B3: JDN+49, 23:00 local rollover) ---
    tz = _local_tz(payload)
    local = born.astimezone(tz)
    eff = local + timedelta(days=1) if local.hour >= 23 else local
    day_idx = sexagenary_day_index(eff.year, eff.month, eff.day)
    day_stem, day_branch = sexagenary_pair(day_idx)

    # --- BC-005 hour pillar (B4: 五鼠遁, clock time) ---
    hour_branch_idx = ((local.hour + 1) // 2) % 12
    hour_stem_idx = ((day_idx % 10) * 2 + hour_branch_idx) % 10
    hour_stem = HEAVENLY_STEMS[hour_stem_idx]
    hour_branch = EARTHLY_BRANCHES[hour_branch_idx]

    day_master = day_stem
    day_master_element = STEM_ELEMENT[day_master]

    def pillar(pos, stem, branch, sidx, bidx) -> dict:
        return {
            "position": pos,
            "stem": stem,
            "branch": branch,
            "stem_index": sidx,
            "branch_index": bidx,
            "hidden_stems": BRANCH_HIDDEN_STEMS[branch],
            "nayin": NAYIN[sexagenary_index(stem, branch)],
            "ten_god": _ten_god(day_master, stem),
        }

    pillars = [
        pillar("year", year_stem, year_branch, year_idx % 10, year_idx % 12),
        pillar("month", month_stem, month_branch, month_stem_idx, m_branch_idx),
        pillar("day", day_stem, day_branch, day_idx % 10, day_idx % 12),
        pillar("hour", hour_stem, hour_branch, hour_stem_idx, hour_branch_idx),
    ]

    # --- BC-006 ten gods map (BC-007 hidden stems feed the map) ---
    ten_gods_map: dict[str, str] = {}
    for p in pillars:
        ten_gods_map[p["stem"]] = _ten_god(day_master, p["stem"])
    for p in pillars:
        for hs in p["hidden_stems"]:
            if hs not in ten_gods_map:
                ten_gods_map[hs] = _ten_god(day_master, hs)

    # --- BC-009/010/011 Da Yun ---
    prev, nxt = _boundaries_around(born)
    yang_year = STEM_YIN_YANG[year_stem] == "阳"
    female = payload["gender"] == "female"
    forward = (yang_year and not female) or ((not yang_year) and female)
    if forward:
        days = (nxt[2] - born).total_seconds() / 86400.0
    else:
        days = (born - prev[2]).total_seconds() / 86400.0
    start_age = max(0, round(days / 3.0))
    month_idx = sexagenary_index(month_stem, month_branch)
    dir_step = 1 if forward else -1
    dayun: list[dict] = []
    for k in range(dayun_count):
        idx = (month_idx + (k + 1) * dir_step) % 60
        stem, branch = sexagenary_pair(idx)
        sa = start_age + 10 * k
        dayun.append(
            {
                "index": k + 1,
                "start_age": sa,
                "end_age": sa + 10,
                "stem": stem,
                "branch": branch,
                "stem_index": idx % 10,
                "branch_index": idx % 12,
                "start_at": _fmt_dt(_add_years(local, sa)),
            }
        )

    gender_assumed = payload["gender"] not in ("male", "female")

    return {
        "day_master": day_master,
        "day_master_element": day_master_element,
        "pillars": pillars,
        "dayun": dayun,
        "ten_gods_map": ten_gods_map,
        "year_boundary": _fmt_dt(year_boundary),
        "month_boundary": m_term,
        "gender_assumed": gender_assumed,
    }
