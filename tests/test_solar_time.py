"""True Solar Time (真太阳时) — deterministic calculation tests."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from openmetaphysics.core import calendar
from openmetaphysics.core.solar_time import (
    equation_of_time,
    longitude_offset_minutes,
    true_solar_time,
)


def test_equation_of_time_range():
    # Equation of time should be between approx -15 and +15 minutes
    for day in range(0, 365, 30):
        dt = datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=day)
        jd = calendar.julian_day(dt)
        eot = equation_of_time(jd)
        assert -17 < eot < 17


def test_equation_of_time_known_values():
    # Known approximate values (check within 1 minute)
    # Jan 1: ~ -3 minutes
    dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    jd = calendar.julian_day(dt)
    eot = equation_of_time(jd)
    assert abs(eot + 3) < 2.0

    # Feb 1: ~ -13 minutes
    dt = datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc)
    jd = calendar.julian_day(dt)
    eot = equation_of_time(jd)
    assert abs(eot + 13) < 2.0

    # May 1: ~ +3 minutes
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc)
    jd = calendar.julian_day(dt)
    eot = equation_of_time(jd)
    assert abs(eot - 3) < 2.0

    # November 1: ~ +16 minutes
    dt = datetime(2024, 11, 1, 12, 0, tzinfo=timezone.utc)
    jd = calendar.julian_day(dt)
    eot = equation_of_time(jd)
    assert abs(eot - 16) < 2.0


def test_longitude_offset():
    # Beijing is ~116.4°E, offset = (116.4 - 120) * 4 = -14.4 minutes
    offset = longitude_offset_minutes(116.4)
    assert abs(offset + 14.4) < 0.1

    # Urumqi is ~87.6°E → (87.6 - 120)*4 = -129.6 minutes = -2h9m36s
    offset = longitude_offset_minutes(87.6)
    assert abs(offset + 129.6) < 0.1

    # 120°E exactly → 0 offset
    assert longitude_offset_minutes(120.0) == 0.0

    # East of 120° → positive offset
    assert longitude_offset_minutes(135.0) > 0


def test_true_solar_time_structure():
    # Shanghai 121.4°E, 2024-05-01 12:00 CST (UTC+8)
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    result = true_solar_time(dt, 121.4)

    # Check all keys present
    assert "utc_time" in result
    assert "standard_time" in result
    assert "local_mean_time" in result
    assert "equation_of_time_minutes" in result
    assert "true_solar_time" in result
    assert "longitude_offset_minutes" in result
    assert "metadata" in result

    # UTC should be 12:00 CST → 04:00 UTC
    utc_hour = result["utc_time"].hour
    assert utc_hour == 4

    # Longitude offset for 121.4 is (121.4-120)*4 = 5.6 minutes
    assert abs(result["longitude_offset_minutes"] - 5.6) < 0.1


def test_daylight_saving_effect():
    # With DST on, we subtract 1 hour from standard time
    dt = datetime(2024, 6, 1, 13, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    # China doesn't do DST currently, this is just a test
    result_with = true_solar_time(dt, 120.0, daylight_saving=True)
    result_without = true_solar_time(dt, 120.0, daylight_saving=False)

    # Difference should be 1 hour
    delta = result_with["true_solar_time"] - result_without["true_solar_time"]
    assert delta.total_seconds() == -3600.0


def test_determinism():
    # Same input → same output (deterministic guarantee)
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    result1 = true_solar_time(dt, 116.4)
    result2 = true_solar_time(dt, 116.4)
    assert result1["equation_of_time_minutes"] == result2["equation_of_time_minutes"]
    assert result1["true_solar_time"] == result2["true_solar_time"]


def test_all_outputs_timezone_aware():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    result = true_solar_time(dt, 116.4)
    assert result["utc_time"].tzinfo is not None
    assert result["standard_time"].tzinfo is not None
    assert result["local_mean_time"].tzinfo is not None
    assert result["true_solar_time"].tzinfo is not None

