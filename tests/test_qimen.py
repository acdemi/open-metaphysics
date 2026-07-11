"""奇门遁甲 — 时家奇门排盘 tests."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from openmetaphysics.agents.qimen import QimenAgent, QimenInput
from openmetaphysics.core.schemas import Gender, GeoPoint


def _run(dt):
    inp = QimenInput(
        request_id="q",
        born_at=dt,
        gender=Gender.UNKNOWN,
        born_location=GeoPoint(latitude=39.9, longitude=116.4, timezone="Asia/Shanghai"),
    )
    return QimenAgent().compute(inp).result


def test_has_all_9_palaces():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    r = _run(dt)
    assert len(r.cells) == 9
    assert all(p.palace >= 1 and p.palace <= 9 for p in r.cells)


def test_all_cells_have_required_fields():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    r = _run(dt)
    count_none = 0
    for p in r.cells:
        assert p.name in ["坎", "坤", "震", "巽", "中宫", "乾", "兑", "艮", "离"]
        assert p.nine_stars is not None
        if p.eight_gods is None:
            count_none += 1
    # 八神 has 8 gods for 9 palaces → exactly one palace has no eight god
    assert count_none == 1


def test_dun_type_boundary():
    # 冬至 2023-12-22 UTC → after winter solstice → yang dun
    dt = datetime(2023, 12, 23, 0, 0, tzinfo=timezone.utc)
    r = _run(dt)
    assert r.dun_type == "yang"

    # 夏至 2024-06-21 UTC → after summer solstice → yin dun
    dt = datetime(2024, 6, 22, 0, 0, tzinfo=timezone.utc)
    r = _run(dt)
    assert r.dun_type == "yin"


def test_ju_range():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    r = _run(dt)
    assert 1 <= r.ju <= 9


def test_triple_offset_correct():
    # day 1-10 → offset 0
    dt = datetime(2024, 5, 5, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    r = _run(dt)
    assert r.triple_offset == 0

    # day 11-20 → offset 3
    dt = datetime(2024, 5, 15, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    r = _run(dt)
    assert r.triple_offset == 3

    # day 21-30 → offset 6
    dt = datetime(2024, 5, 25, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    r = _run(dt)
    assert r.triple_offset == 6


def test_all_sky_plate_filled():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    r = _run(dt)
    sky_plates = [p.sky_plate for p in r.cells if p.sky_plate is not None]
    assert len(sky_plates) == 9
    # 乙丙丁戊己庚辛壬癸 → 9 distinct
    assert len(set(sky_plates)) == 9


def test_sanqi_detection():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    r = _run(dt)
    sanqi = [p.three_qi for p in r.cells if p.three_qi is not None]
    assert len(sanqi) == 3
    assert set(sanqi) == {"乙", "丙", "丁"}


def test_nine_stars_correct():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    r = _run(dt)
    stars = sorted(p.nine_stars for p in r.cells if p.nine_stars is not None)
    expected = sorted(["天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"])
    assert stars == expected


def test_determinism_replay():
    dt = datetime(2024, 5, 1, 12, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    inp = QimenInput(
        request_id="q_replay",
        born_at=dt,
        gender=Gender.UNKNOWN,
    )
    from openmetaphysics.agents.qimen import QimenAgent

    def _strip(output):
        d = output.model_dump(mode="json")
        d.pop("computed_at", None)
        return d

    a = _strip(QimenAgent().compute(inp))
    b = _strip(QimenAgent().compute(inp))
    assert a == b


def test_metadata_correct():
    agent = QimenAgent()
    meta = agent._metadata()
    assert meta["deterministic"] is True
    assert meta["has_nine_stars"] is True
    assert meta["has_eight_doors"] is True
    assert meta["has_eight_gods"] is True
