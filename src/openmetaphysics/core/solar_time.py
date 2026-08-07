from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict

from . import calendar as c

"""Deterministic True Solar Time (真太阳时) calculation.

Implements:
- Longitude correction for local mean solar time
- Equation of Time (均时差) via astronomical formula
- True Solar Time calculation
- UTC / standard time / local mean / true solar conversions
- Daylight saving time support (configurable)

All calculations are deterministic, no LLM involved.
Formula based on standard astronomical algorithms (Meeus).
"""


def equation_of_time(jd: float) -> float:
    """Calculate Equation of Time in minutes.

    The equation of time is the difference between apparent solar time
    and mean solar time. Result is in minutes (can be negative).

    Formula from: Astronomical Algorithms by Jean Meeus, 1998.
    """
    t = (jd - 2451545.0) / 36525.0
    # mean anomaly of the Sun
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    m_rad = math.radians(m)
    # mean longitude of the Sun
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    # Sun's true longitude
    alpha = (
        l0
        + (1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m_rad)
        + (0.019993 - 0.000101 * t) * math.sin(2 * m_rad)
        + 0.000289 * math.sin(3 * m_rad)
    )
    # reduce alpha to 0-360
    alpha = alpha % 360
    alpha_rad = math.radians(alpha)
    # obliquity of the ecliptic
    eps = 23 + (26 + (21.448 - 46.8150 * t - 0.00059 * t * t) / 60) / 60
    eps_rad = math.radians(eps)
    # right ascension of the Sun
    ra = math.degrees(math.atan(math.cos(eps_rad) * math.tan(alpha_rad)))
    # correction to RA: align quadrant with alpha
    alpha_quad = int(math.floor(alpha / 90)) * 90
    ra_quad = int(math.floor(ra / 90)) * 90
    ra += alpha_quad - ra_quad
    # equation of time in degrees
    l0_mod = l0 % 360
    eot = l0_mod - ra
    # wrap to [-180, 180]
    eot = eot % 360
    if eot > 180:
        eot -= 360
    elif eot < -180:
        eot += 360
    # convert to minutes (1 degree = 4 minutes)
    return eot * 4


def longitude_offset_minutes(longitude: float) -> float:
    """Calculate longitude offset in minutes from standard meridian (120°E for China).

    China standard time is UTC+8 based on 120°E longitude.
    Each degree east of 120 adds 4 minutes, each degree west subtracts 4 minutes.
    """
    standard_meridian = 120.0  # for China Standard Time (UTC+8)
    return (longitude - standard_meridian) * 4.0


def standard_to_local_mean(
    standard_dt: datetime,
    longitude: float,
) -> datetime:
    """Convert standard clock time to local mean solar time."""
    offset_min = longitude_offset_minutes(longitude)
    return standard_dt + timedelta(minutes=offset_min)


def add_equation_of_time(local_mean_dt: datetime, jd: float) -> datetime:
    """Add equation of time to local mean time to get true solar time."""
    eot_min = equation_of_time(jd)
    return local_mean_dt + timedelta(minutes=eot_min)


def true_solar_time(
    born_at: datetime,
    longitude: float,
    daylight_saving: bool = False,
) -> dict[str, float | datetime | dict]:
    """Calculate true solar time from input datetime.

    Args:
        born_at: Timezone-aware input datetime (usually from birth record).
        longitude: Longitude of the location in degrees (east positive).
        daylight_saving: Whether daylight saving was in effect.

    Returns:
        Dict with all intermediate results:
        - utc_time: UTC datetime
        - standard_time: Original standard time
        - local_mean_time: Local mean solar time after longitude correction
        - equation_of_time_minutes: Equation of Time in minutes
        - true_solar_time: Final true solar time
        - longitude_offset_minutes: Longitude correction in minutes
        - metadata: calculation metadata
    """
    # Convert to UTC
    utc_dt = born_at.astimezone(timezone.utc)
    jd = c.julian_day(utc_dt)

    # Handle DST: if DST is on, clock is +1hr, subtract it
    if daylight_saving:
        standard_dt = born_at - timedelta(hours=1)
    else:
        standard_dt = born_at

    # Longitude correction → local mean time
    lon_offset_min = longitude_offset_minutes(longitude)
    local_mean_dt = standard_to_local_mean(standard_dt, longitude)

    # Add equation of time → true solar time
    eot_min = equation_of_time(jd)
    true_solar_dt = add_equation_of_time(local_mean_dt, jd)

    return {
        "utc_time": utc_dt,
        "standard_time": standard_dt,
        "local_mean_time": local_mean_dt,
        "equation_of_time_minutes": eot_min,
        "true_solar_time": true_solar_dt,
        "longitude_offset_minutes": lon_offset_min,
        "metadata": {
            "daylight_saving": daylight_saving,
            "input_longitude": longitude,
            "standard_meridian": 120.0,
        },
    }


class TrueSolarTimeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    utc_time: datetime
    standard_time: datetime
    local_mean_time: datetime
    equation_of_time_minutes: float
    true_solar_time: datetime
    longitude_offset_minutes: float
    metadata: dict[str, bool | float]


__all__ = [
    "equation_of_time",
    "longitude_offset_minutes",
    "standard_to_local_mean",
    "add_equation_of_time",
    "true_solar_time",
    "TrueSolarTimeResult",
]
