"""Calendar primitives — solar terms, sexagenary day, 立春 boundary."""

from datetime import datetime, timezone

from openmetaphysics.core import calendar as c


def test_sexagenary_day_anchor_1900():
    # 1900-01-01 is 甲戌 -> index 10
    assert c.sexagenary_day_index(1900, 1, 1) == 10


def test_sexagenary_day_anchor_2000():
    # 2000-01-01 is 戊午 -> index 54
    assert c.sexagenary_day_index(2000, 1, 1) == 54


def test_lichun_within_minutes():
    # 立春 2024 actual ~ 2024-02-04 08:26:53 UTC; allow +-15 min
    lc = c.lichun_time(2024)
    actual = datetime(2024, 2, 4, 8, 26, 53, tzinfo=timezone.utc)
    assert abs((lc - actual).total_seconds()) < 15 * 60


def test_all_24_terms_present():
    terms = c.solar_terms_for_year(2024)
    assert len(terms) == 24
    assert all(t.year == 2024 for t in terms.values())


def test_year_index_lichun_boundary():
    post = datetime(2024, 2, 4, 9, 0, tzinfo=timezone.utc)  # after 立春 -> 甲辰(40)
    pre = datetime(2024, 2, 4, 0, 0, tzinfo=timezone.utc)  # before 立春 -> 癸卯(39)
    assert c.bazi_year_index(post)[0] == 40
    assert c.bazi_year_index(pre)[0] == 39


def test_month_boundary_before():
    # 2024-08-15 is between 立秋 and 白露 -> month branch 申 (index 8)
    born = datetime(2024, 8, 15, 12, 0, tzinfo=timezone.utc)
    branch_idx, term_name, _t = c.month_boundary_before(born)
    assert branch_idx == 8
    assert term_name == "立秋"
