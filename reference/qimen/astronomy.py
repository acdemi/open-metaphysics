"""Reference Qimen 天文/干支基础 (自包含, Phase 5.7 对齐 Sprint).

规范移植声明: 本模块为 core 共享基础层 (src/openmetaphysics/core/calendar.py
与 core/solar_time.py) 的独立规范移植 —— 算法同源 (Meeus 截断), 无导入依赖,
保证 Reference 实现完全独立于 Product 侧。行为一致性由 24 规范向量验收 +
等价性抽样 (reference/tests/test_equivalence.py) 强制。

精度: 黄经 ~0.01°, 节气时刻误差 < 1 分钟, 满足日级/时辰级排盘需求。
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

UTC = timezone.utc

# ---------------------------------------------------------------------------
# 天干 / 地支 / 24 节气 (规范性数据, 与契约 QC 一致)
# ---------------------------------------------------------------------------
HEAVENLY_STEMS: list[str] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES: list[str] = [
    "子",
    "丑",
    "寅",
    "卯",
    "辰",
    "巳",
    "午",
    "未",
    "申",
    "酉",
    "戌",
    "亥",
]

SOLAR_TERMS_24: list[tuple[str, bool, int]] = [
    ("春分", False, 0),
    ("清明", True, 15),
    ("谷雨", False, 30),
    ("立夏", True, 45),
    ("小满", False, 60),
    ("芒种", True, 75),
    ("夏至", False, 90),
    ("小暑", True, 105),
    ("大暑", False, 120),
    ("立秋", True, 135),
    ("处暑", False, 150),
    ("白露", True, 165),
    ("秋分", False, 180),
    ("寒露", True, 195),
    ("霜降", False, 210),
    ("立冬", True, 225),
    ("小雪", False, 240),
    ("大雪", True, 255),
    ("冬至", False, 270),
    ("小寒", True, 285),
    ("大寒", False, 300),
    ("立春", True, 315),
    ("雨水", False, 330),
    ("惊蛰", True, 345),
]


# ---------------------------------------------------------------------------
# 儒略日
# ---------------------------------------------------------------------------
def julian_day_number(year: int, month: int, day: int) -> int:
    """格里高利日期 → 儒略日数 (整数, 午正基准)."""
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def julian_day(dt: datetime) -> float:
    """datetime (视为 UTC) → 儒略日 (浮点)."""
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


# ---------------------------------------------------------------------------
# 太阳黄经 (Meeus, 截断)
# ---------------------------------------------------------------------------
def solar_longitude(jd: float) -> float:
    """太阳视黄经 (度, [0, 360))."""
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
    """`year` 年内太阳到达 `target_lon` 度的 UTC 时刻 (二分搜索)."""
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


def sexagenary_day_index(year: int, month: int, day: int) -> int:
    """日干支序 (0..59, 甲子=0)."""
    return (julian_day_number(year, month, day) + 49) % 60


# ---------------------------------------------------------------------------
# 真太阳时 (均时差 + 经度校正; 标准子午线 120°E)
# ---------------------------------------------------------------------------
def equation_of_time(jd: float) -> float:
    """均时差 (分钟)."""
    t = (jd - 2451545.0) / 36525.0
    m = 357.52911 + 35999.05029 * t - 0.0001537 * t * t
    m_rad = math.radians(m)
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    alpha = (
        l0
        + (1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m_rad)
        + (0.019993 - 0.000101 * t) * math.sin(2 * m_rad)
        + 0.000289 * math.sin(3 * m_rad)
    )
    alpha = alpha % 360
    alpha_rad = math.radians(alpha)
    eps = 23 + (26 + (21.448 - 46.8150 * t - 0.00059 * t * t) / 60) / 60
    eps_rad = math.radians(eps)
    ra = math.degrees(math.atan(math.cos(eps_rad) * math.tan(alpha_rad)))
    ra += (int(math.floor(alpha / 90)) * 90) - (int(math.floor(ra / 90)) * 90)
    eot = (l0 % 360) - ra
    eot = eot % 360
    if eot > 180:
        eot -= 360
    elif eot < -180:
        eot += 360
    return eot * 4


def longitude_offset_minutes(longitude: float) -> float:
    """经度校正 (分钟); 标准子午线 120°E (中国标准时 UTC+8)."""
    return (longitude - 120.0) * 4.0


def true_solar_hour(born_at: datetime, longitude: float, daylight_saving: bool = False) -> int:
    """真太阳时小时 (D13: 有坐标定时辰)."""
    utc_dt = born_at.astimezone(UTC)
    jd = julian_day(utc_dt)
    standard_dt = born_at - timedelta(hours=1) if daylight_saving else born_at
    local_mean = standard_dt + timedelta(minutes=longitude_offset_minutes(longitude))
    true_solar = local_mean + timedelta(minutes=equation_of_time(jd))
    return true_solar.hour


__all__ = [
    "HEAVENLY_STEMS",
    "EARTHLY_BRANCHES",
    "SOLAR_TERMS_24",
    "julian_day_number",
    "julian_day",
    "solar_longitude",
    "solar_term_time",
    "sexagenary_day_index",
    "equation_of_time",
    "longitude_offset_minutes",
    "true_solar_hour",
]
