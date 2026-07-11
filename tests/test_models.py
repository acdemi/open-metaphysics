"""Reference-table integrity tests (deterministic ground truth)."""

from openmetaphysics.core import models as m


def test_stems_and_branches_counts():
    assert len(m.HEAVENLY_STEMS) == 10
    assert len(m.EARTHLY_BRANCHES) == 12
    assert len(m.NAYIN) == 60
    assert len(m.HEXAGRAMS) == 64
    assert len(m.SOLAR_TERMS_24) == 24
    assert len(m.BAZI_MONTH_BOUNDARIES) == 12


def test_sexagenary_cycle_roundtrip():
    for i in range(60):
        stem, branch = m.sexagenary_pair(i)
        assert m.sexagenary_index(stem, branch) == i
        assert m.HEAVENLY_STEMS.index(stem) == i % 10
        assert m.EARTHLY_BRANCHES.index(branch) == i % 12


def test_nayin_known_values():
    assert m.nayin_for("甲", "子") == "海中金"
    assert m.nayin_for("壬", "戌") == "大海水"
    assert m.nayin_for("丙", "寅") == "炉中火"
    # every nayin name ends with its element char
    for name in m.NAYIN:
        assert name[-1] in m.WUXING


def test_wuxing_relations():
    assert m.wuxing_relation("金", "金") == "same"
    assert m.wuxing_relation("金", "水") == "sheng"
    assert m.wuxing_relation("水", "金") == "being_sheng"
    assert m.wuxing_relation("金", "木") == "ke"
    assert m.wuxing_relation("木", "金") == "being_ke"


def test_hexagram_lines_canonical():
    assert m.hexagram_lines(1) == [1, 1, 1, 1, 1, 1]  # 乾
    assert m.hexagram_lines(2) == [0, 0, 0, 0, 0, 0]  # 坤
    assert m.hexagram_lines(63) == [1, 0, 1, 0, 1, 0]  # 既济 (alternating)
    assert m.hexagram_lines(64) == [0, 1, 0, 1, 0, 1]  # 未济


def test_hexagram_from_lines_inverse():
    for num in range(1, 65):
        lines = m.hexagram_lines(num)
        assert m.hexagram_from_lines(lines)["num"] == num


def test_trigram_lines_unique():
    seen = set()
    for _name, info in m.TRIGRAMS.items():
        key = tuple(info["lines"])
        assert key not in seen
        seen.add(key)
