"""Reference BaZi astronomy — deterministic solar terms (self-contained).

Port of the frozen calendar primitives (Meeus, truncated, ~0.01 deg / <1 min)
governing BC-002/003 (year/month boundaries at UTC instants) and BC-010
(Da Yun boundary distances). No imports from openmetaphysics.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from .tables import BAZI_MONTH_BOUNDARIES

UTC = timezone.utc


def julian_day_number(year: int, month: int, day: int) -> int:
    """Julian Day Number for a Gregorian date (integer, noon-based)."""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def julian_day(dt: datetime) -> float:
    """Julian Day (float) for a datetime, interpreted as UTC."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    jdn = julian_day_number(dt.year, dt.month, dt.day)
    return (
        jdn
        + (dt.hour - 12) / 24.0
        + dt.minute / 1440.0
        + dt.second / 86400.0
        + dt.microsecond / 86400e6
    )


def solar_longitude(jd: float) -> float:
    """Apparent geocentric ecliptic longitude of the Sun, degrees [0, 360)."""
    t = (jd - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    mr = math.radians(m)
    c = (
        (1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(mr)
        + (0.019993 - 0.000101 * t) * math.sin(2 * mr)
        + 0.000289 * math.sin(3 * mr)
    )
    theta = l0 + c
    omega = 125.04 - 1934.136 * t
    theta_app = theta - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    return theta_app % 360.0


def _wrapped_diff(jd: float, target_lon: float) -> float:
    return (solar_longitude(jd) - target_lon) % 360.0


def solar_term_time(year: int, target_lon: int) -> datetime:
    """UTC datetime in `year` when the Sun reaches `target_lon` degrees."""
    start = datetime(year, 1, 1, tzinfo=UTC)
    for day in range(0, 367):
        t0 = start + timedelta(days=day)
        t1 = t0 + timedelta(days=1)
        w0 = _wrapped_diff(julian_day(t0), target_lon)
        w1 = _wrapped_diff(julian_day(t1), target_lon)
        if w0 > w1 and (w0 - w1) > 180.0:
            lo, hi = t0, t1
            for _ in range(60):
                mid = lo + (hi - lo) / 2
                wl = _wrapped_diff(julian_day(lo), target_lon)
                wm = _wrapped_diff(julian_day(mid), target_lon)
                if wl > wm and (wl - wm) > 180.0:
                    hi = mid
                else:
                    lo = mid
            return lo
    raise ValueError(f"solar term {target_lon} not found in {year}")


def lichun_time(year: int) -> datetime:
    """The 立春 boundary (Bazi year start) for a Gregorian year, UTC."""
    return solar_term_time(year, 315)


def sexagenary_day_index(year: int, month: int, day: int) -> int:
    """Sexagenary index 0..59 (甲子=0) for a Gregorian date (BC-004)."""
    return (julian_day_number(year, month, day) + 49) % 60


def month_boundaries(year: int) -> list[tuple[datetime, int, str]]:
    """All 12 节 boundaries spanning `year`, sorted ascending by time."""
    out: list[tuple[datetime, int, str]] = []
    for term_name, lon, branch_idx in BAZI_MONTH_BOUNDARIES:
        out.append((solar_term_time(year, lon), branch_idx, term_name))
    out.sort(key=lambda x: x[0])
    return out


def month_boundary_before(born_at: datetime) -> tuple[int, str, datetime]:
    """The 节 boundary governing `born_at`: (branch_index, term_name, time)."""
    y = born_at.astimezone(UTC).year
    candidates = month_boundaries(y - 1) + month_boundaries(y) + month_boundaries(y + 1)
    cur = (2, "立春", lichun_time(y))
    for t, branch_idx, term_name in candidates:
        if t <= born_at:
            cur = (branch_idx, term_name, t)
    return cur


def bazi_year_index(born_at: datetime) -> tuple[int, datetime]:
    """Sexagenary year index and the Lichun boundary that governs `born_at`."""
    y = born_at.astimezone(UTC).year
    lc = lichun_time(y)
    if born_at >= lc:
        lichun_year = y
        boundary = lc
    else:
        lichun_year = y - 1
        boundary = lichun_time(y - 1)
    return (lichun_year - 4) % 60, boundary
