"""Bazi (八字) agent — deterministic four-pillar calculation.

Year/month pillars are anchored on solar-term boundaries (立春 year start,
节 month start). Day pillar uses the sexagenary day cycle with a 23:00 rollover.
Hour pillar uses 五鼠遁. Includes 藏干, 纳音, 十神, and 大运 (decade luck).
No LLM anywhere in compute().
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.core.schemas import Gender, GeoPoint


def _run(born_at, gender=Gender.MALE, loc=True):
    inp = BaziInput(
        request_id="b",
        born_at=born_at,
        gender=gender,
        born_location=GeoPoint(latitude=39.9, longitude=116.4, timezone="Asia/Shanghai")
        if loc
        else None,
    )
    return BaziAgent().compute(inp).result


def test_year_pillar_1985():
    r = _run(datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
    y = r.pillars[0]
    assert y.stem == "乙" and y.branch == "丑"
    assert y.stem_index == 1 and y.branch_index == 1


def test_month_and_hour_branches():
    r = _run(datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
    assert r.pillars[1].branch_index == 8  # 申月
    assert r.pillars[3].branch_index == 5  # 巳时 (09-10:59)


def test_day_pillar_sexagenary_parity():
    r = _run(datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
    d = r.pillars[2]
    assert d.stem_index % 2 == d.branch_index % 2  # valid 干支 pair


def test_lichun_boundary_switches_year():
    pre = _run(datetime(2024, 2, 4, 0, 0, tzinfo=timezone.utc))
    post = _run(datetime(2024, 2, 4, 9, 0, tzinfo=timezone.utc))
    assert (pre.pillars[0].stem_index, pre.pillars[0].branch_index) == (9, 3)  # 癸卯
    assert (post.pillars[0].stem_index, post.pillars[0].branch_index) == (0, 4)  # 甲辰


def test_2300_day_rollover():
    a = _run(datetime(2024, 5, 1, 22, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
    b = _run(datetime(2024, 5, 1, 23, 30, tzinfo=ZoneInfo("Asia/Shanghai")))
    assert a.pillars[2].stem_index != b.pillars[2].stem_index  # day rolled
    assert a.pillars[3].branch_index == 11  # 亥时
    assert b.pillars[3].branch_index == 0  # 子时


def test_hidden_stems_and_nayin_present():
    r = _run(datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
    for p in r.pillars:
        assert len(p.hidden_stems) >= 1
        assert p.nayin and p.nayin[-1] in "金木水火土"


def test_ten_gods_against_day_master():
    r = _run(datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
    # day pillar's stem ten-god vs itself is 比肩
    assert r.pillars[2].ten_god == "比肩"
    assert r.day_master in r.ten_gods_map


def test_dayun_count_and_progression():
    r = _run(datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")))
    assert len(r.dayun) == 8
    ages = [d.start_age for d in r.dayun]
    assert ages == sorted(ages) and ages[1] - ages[0] == 10


def test_gender_assumed_flag():
    from openmetaphysics.core.schemas import Gender as G

    r = _run(datetime(2024, 3, 1, 6, 0, tzinfo=timezone.utc), gender=G.UNKNOWN)
    assert r.gender_assumed is True


def test_bazi_explainer_fallback():
    from openmetaphysics.agents import BaziExplainer
    from openmetaphysics.core.schemas import AgentOutput, ConfidenceScore, Gender, GeoPoint
    from openmetaphysics.agents.bazi import BaziAgent, BaziInput
    from datetime import datetime
    from zoneinfo import ZoneInfo

    agent = BaziAgent()
    inp = BaziInput(
        request_id="test-explainer",
        born_at=datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        gender=Gender.MALE,
        born_location=GeoPoint(latitude=39.9, longitude=116.4, timezone="Asia/Shanghai"),
    )
    output = agent.compute(inp)

    explainer = BaziExplainer(provider=None)
    text = explainer.render(output)

    # Check that fallback output contains key terms
    assert "日主" in text
    assert "月令" in text
    assert "格局" in text
    assert output.result.day_master in text
    print(f"✓ Bazi explainer fallback output: {text}")


def test_bazi_explainer_pattern_extraction():
    from openmetaphysics.agents import BaziExplainer
    from openmetaphysics.agents.bazi import BaziAgent, BaziInput
    from openmetaphysics.core.schemas import Gender, GeoPoint
    from datetime import datetime
    from zoneinfo import ZoneInfo

    agent = BaziAgent()
    inp = BaziInput(
        request_id="test-pattern",
        born_at=datetime(1985, 8, 15, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        gender=Gender.MALE,
        born_location=GeoPoint(latitude=39.9, longitude=116.4, timezone="Asia/Shanghai"),
    )
    output = agent.compute(inp)
    chart = output.result

    explainer = BaziExplainer()
    pattern_info = explainer._get_pattern_info(chart)

    assert pattern_info["month_earthly_branch"] == "申"
    assert "庚" in pattern_info["month_hidden_stems"]
    assert pattern_info["dominant_hidden"] == "庚"
    # 乙日主，庚是正官
    assert pattern_info["pattern_ten_god"] == "正官"
