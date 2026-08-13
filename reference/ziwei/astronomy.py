"""Reference Ziwei astronomy primitives.

Independent implementation of the calendar contracts, no src/ imports.

- BC-005 (ZW-004): Gregorian -> lunar conversion via sxtwl==2.0.7
  (exact pin per ACP-ZW-004). Lunar date is taken from the LOCAL civil
  date; late Zi hour (23:00+) does NOT roll the lunar day.
"""

from __future__ import annotations


def solar_to_lunar(year: int, month: int, day: int) -> tuple[int, int, int, bool]:
    """BC-005: convert Gregorian (solar) date to lunar date.

    Returns: (lunar_year, lunar_month, lunar_day, is_leap_month)
    - lunar_month is 1..12; a leap month keeps the same month number
    - is_leap_month is True for the leap (闰) month
    The underlying sxtwl library is pinned to ==2.0.7 (ACP-ZW-004).
    """
    import sxtwl

    d = sxtwl.fromSolar(year, month, day)
    return (
        d.getLunarYear(),
        d.getLunarMonth(),
        d.getLunarDay(),
        d.isLunarLeap(),
    )


__all__ = ["solar_to_lunar"]
