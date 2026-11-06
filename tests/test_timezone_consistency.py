"""H5 regression: one timezone policy for every domain + a real true-solar meridian.

Review H5: Liuyao read ``born_at`` with whatever UTC offset the caller
serialized, and Qimen's true-solar time was hard-coded to the 120°E meridian
(and used the input offset's date), so a non-+08:00 input produced a wrong
chart -- London 12:00 came out as "true solar 04:00".

After the fix every domain first converts the instant to the birth location's
timezone (``core.solar_time.local_datetime``) and only then decides date/hour/
pillar; Qimen derives the standard meridian from that local clock's UTC offset
(UTC+8 -> 120°E, UTC+1 -> 15°E, UTC -> 0°). D14 (late 子时 does not roll the day
pillar) and the lunar/solar-term algorithms are untouched.
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.agents.liuyao import (
    SIX_SPIRITS,
    SPIRIT_START_BY_STEM,
    LiuyaoAgent,
    LiuyaoInput,
)
from openmetaphysics.agents.qimen import QimenAgent, QimenInput, effective_hour
from openmetaphysics.agents.ziwei import ZiweiAgent, ZiweiInput
from openmetaphysics.api.app import create_app
from openmetaphysics.core.models import HEAVENLY_STEMS
from openmetaphysics.core.schemas import Gender, GeoPoint
from openmetaphysics.core.solar_time import (
    local_datetime,
    standard_meridian_for,
    true_solar_time,
)

BEIJING = GeoPoint(latitude=39.9, longitude=116.4, timezone="Asia/Shanghai")
LONDON = GeoPoint(latitude=51.5, longitude=-0.1278, timezone="Europe/London")

# The H5 example: one instant, two legal representations.
INSTANT_BJ = datetime(2024, 5, 1, 0, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
INSTANT_UTC = INSTANT_BJ.astimezone(timezone.utc)  # 2024-04-30T16:30Z

CASTS = [7, 7, 8, 8, 7, 8]


def _qimen(born_at: datetime, location: GeoPoint = BEIJING):
    payload = QimenInput(
        request_id="h5", born_at=born_at, gender=Gender.UNKNOWN, born_location=location
    )
    return QimenAgent().compute(payload).result


def _liuyao(born_at: datetime, location: GeoPoint = BEIJING):
    payload = LiuyaoInput(
        request_id="h5",
        born_at=born_at,
        gender=Gender.MALE,
        born_location=location,
        casts=CASTS,
    )
    return LiuyaoAgent().compute(payload).result


def _bazi(born_at: datetime, location: GeoPoint = BEIJING):
    payload = BaziInput(
        request_id="h5", born_at=born_at, gender=Gender.MALE, born_location=location
    )
    return BaziAgent().compute(payload).result


def _ziwei(born_at: datetime, location: GeoPoint = BEIJING):
    payload = ZiweiInput(
        request_id="h5", born_at=born_at, gender=Gender.MALE, born_location=location
    )
    return ZiweiAgent().compute(payload).result


# -- local clock policy -----------------------------------------------------


def test_local_datetime_reads_location_timezone_not_input_offset():
    assert local_datetime(INSTANT_BJ, BEIJING) == local_datetime(INSTANT_UTC, BEIJING)
    local = local_datetime(INSTANT_UTC, BEIJING)
    assert local.hour == 0 and local.minute == 30
    assert local.utcoffset() is not None and local.utcoffset().total_seconds() == 8 * 3600


def test_standard_meridian_follows_local_clock_offset():
    assert standard_meridian_for(datetime(2024, 5, 1, 12, tzinfo=ZoneInfo("Asia/Shanghai"))) == (
        pytest.approx(120.0)
    )
    assert standard_meridian_for(datetime(2024, 5, 1, 12, tzinfo=ZoneInfo("Europe/London"))) == (
        pytest.approx(15.0)  # BST = UTC+1 -> 15°E
    )
    assert standard_meridian_for(datetime(2024, 12, 1, 12, tzinfo=ZoneInfo("Europe/London"))) == (
        pytest.approx(0.0)  # GMT
    )
    assert standard_meridian_for(datetime(2024, 5, 1, 12, tzinfo=ZoneInfo("Asia/Kolkata"))) == (
        pytest.approx(82.5)  # UTC+5:30
    )


def test_london_noon_is_not_4am_true_solar():
    noon = datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Europe/London"))
    result = true_solar_time(noon, LONDON.longitude)

    assert result["metadata"]["standard_meridian"] == pytest.approx(15.0)
    true_solar = result["true_solar_time"]
    assert true_solar.hour == 11, true_solar  # ~11:02 BST, not 04:00
    assert true_solar.hour != 4

    payload = QimenInput(
        request_id="h5-london", born_at=noon, gender=Gender.UNKNOWN, born_location=LONDON
    )
    assert effective_hour(payload) == 11


# -- same instant, different representation -> identical charts -------------


def test_same_instant_different_timezone_representation_same_charts():
    assert _qimen(INSTANT_BJ) == _qimen(INSTANT_UTC)
    assert _liuyao(INSTANT_BJ) == _liuyao(INSTANT_UTC)
    assert _bazi(INSTANT_BJ) == _bazi(INSTANT_UTC)
    assert _ziwei(INSTANT_BJ) == _ziwei(INSTANT_UTC)

    # the Qimen day number follows the local clock day (05-01), not the UTC day
    assert _qimen(INSTANT_UTC).day_of_month == 1


# -- cross-domain consistency: Liuyao 六神 vs Bazi 日柱 ---------------------


def test_liuyao_liu_shen_matches_bazi_day_pillar():
    # 2024-04-30 15:30Z -> Beijing 23:30 (late 子时; D14: hour = 子, day rolls to 05-01)
    instant = datetime(2024, 4, 30, 15, 30, tzinfo=timezone.utc)
    bazi = _bazi(instant)
    liuyao = _liuyao(instant)

    day_stem = bazi.pillars[2].stem
    stem_index = HEAVENLY_STEMS.index(day_stem)
    expected_liu_shen = [SIX_SPIRITS[(SPIRIT_START_BY_STEM[stem_index] + i) % 6] for i in range(6)]
    assert liuyao.liu_shen == expected_liu_shen

    # both domains agree across timezone representations
    assert _bazi(instant) == _bazi(instant.astimezone(ZoneInfo("Asia/Shanghai")))
    assert _liuyao(instant) == _liuyao(instant.astimezone(ZoneInfo("Asia/Shanghai")))

    # the 23:00 rollover policy is unchanged: the day pillar matches 05-01
    assert (
        bazi.pillars[2]
        == _bazi(datetime(2024, 5, 1, 0, 30, tzinfo=ZoneInfo("Asia/Shanghai"))).pillars[2]
    )


# -- explicit policy for unsupported/unknown zones -------------------------


def test_unknown_timezone_is_an_explicit_error():
    bad = GeoPoint(latitude=1.0, longitude=2.0, timezone="Not/AZone")
    with pytest.raises(ValidationError, match="timezone"):
        QimenInput(request_id="h5", born_at=INSTANT_BJ, born_location=bad)
    with pytest.raises(ValidationError, match="timezone"):
        LiuyaoInput(request_id="h5", born_at=INSTANT_BJ, born_location=bad)


def test_api_rejects_unknown_timezone_with_422():
    client = TestClient(create_app())
    response = client.post(
        "/agents/qimen/compute",
        json={
            "request_id": "h5-api",
            "born_at": "2024-05-01T00:30:00+08:00",
            "born_location": {"latitude": 1.0, "longitude": 2.0, "timezone": "Not/AZone"},
        },
    )
    assert response.status_code == 422, response.text
    assert "timezone" in response.text.lower()


def test_no_location_keeps_clock_time_fallback():
    """Documented fallback: no location -> the input clock is used as-is (no TST)."""
    payload = QimenInput(request_id="h5", born_at=INSTANT_BJ, gender=Gender.UNKNOWN)
    assert effective_hour(payload) == INSTANT_BJ.hour == 0
