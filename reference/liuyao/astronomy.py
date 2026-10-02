"""Liuyao reference astronomy — Julian Day Number / 干支纪日.

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
