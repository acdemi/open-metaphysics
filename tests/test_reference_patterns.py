"""Golden tests for the Reference Pattern Matcher (Phase 6B Sprint 2).

Validates the chain: RuleEvaluation -> PatternMatcher -> PatternMatch -> JSON.

Tests cover: Single Rule, Multi Rule, Cross System, No Match, ANY logic,
determinism, and JSON serialization.

24 tests total.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reference.engine import RuleEngine
from reference.parser import parse_rule_file
from reference.pattern_matcher import PatternMatcher
from reference.patterns import (
    PatternCategory,
    RequirementLogic,
    parse_pattern_file,
)

EXAMPLES = Path(__file__).parent.parent / "reference" / "examples"
PAT_DIR = EXAMPLES / "patterns"

CHART_WITH_SEAL = {
    "ten_gods_map": {"values": ["伤官", "正印", "比肩"]},
    "day_master_strength": 0.35,
    "shen_sha_list": ["羊刃", "天乙贵人"],
}
CHART_NO_SEAL = {
    "ten_gods_map": {"values": ["伤官", "比肩", "正财"]},
    "day_master_strength": 0.5,
    "shen_sha_list": ["羊刃"],
}
CHART_QIMEN = {"dun_type": "yang", "ju": 6}
CHART_EMPTY = {"ten_gods_map": {"values": []}, "day_master_strength": 0.8, "shen_sha_list": []}


def _load_and_eval(yaml_name, chart):
    """Load a rule YAML, evaluate against chart, return list[RuleEvaluation]."""
    rules = parse_rule_file(str(EXAMPLES / yaml_name))
    engine = RuleEngine()
    return engine.evaluate_all(rules, chart)


# ═══════════════════════════════════════════════════════════════════
# Parser tests
# ═══════════════════════════════════════════════════════════════════


class TestPatternParser:
    def test_parse_single_rule_pattern(self):
        p = parse_pattern_file(str(PAT_DIR / "01_single_rule.yaml"))
        assert p.pattern_id == "pattern:bazi:yang_ren_ge:v1"
        assert p.name == "羊刃格"
        assert p.category == PatternCategory.GEJU
        assert len(p.rule_ids) == 1
        assert p.rule_ids[0] == "rule:bazi:yang_ren_ge:v1"
        assert p.knowledge_node_ids == []
        assert p.confidence == pytest.approx(0.85)
        assert len(p.requirements) == 1
        assert p.requirements[0].logic == RequirementLogic.ALL

    def test_parse_multi_rule_pattern(self):
        p = parse_pattern_file(str(PAT_DIR / "02_multi_rule.yaml"))
        assert len(p.rule_ids) == 3
        assert len(p.requirements) == 1
        assert p.requirements[0].logic == RequirementLogic.ALL
        assert len(p.requirements[0].rule_ids) == 3
        assert p.knowledge_node_ids == ["kn:pattern:shang_guan_pei_yin"]

    def test_parse_any_logic_pattern(self):
        p = parse_pattern_file(str(PAT_DIR / "03_any_logic.yaml"))
        assert p.requirements[0].logic == RequirementLogic.ANY
        assert p.requirements[0].min_matches == 1
        assert len(p.requirements[0].rule_ids) == 2

    def test_parse_cross_system_pattern(self):
        p = parse_pattern_file(str(PAT_DIR / "04_cross_system.yaml"))
        assert p.category == PatternCategory.CROSS_SYSTEM
        assert p.systems == ["bazi", "qimen"]
        assert len(p.rule_ids) == 2

    def test_parse_no_match_pattern(self):
        p = parse_pattern_file(str(PAT_DIR / "05_no_match.yaml"))
        assert p.pattern_id == "pattern:bazi:shang_guan_wu_yin_geju:v1"
        assert len(p.rule_ids) == 1
        assert p.confidence == pytest.approx(0.70)


# ═══════════════════════════════════════════════════════════════════
# Single Rule matching
# ═══════════════════════════════════════════════════════════════════


class TestSingleRuleMatch:
    def setup_method(self):
        self.matcher = PatternMatcher()
        self.pattern = parse_pattern_file(str(PAT_DIR / "01_single_rule.yaml"))

    def test_single_rule_match(self):
        evals = _load_and_eval("01_single_condition.yaml", CHART_WITH_SEAL)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert pm is not None
        assert pm.matched is True
        assert pm.pattern_id == "pattern:bazi:yang_ren_ge:v1"
        assert pm.pattern_name == "羊刃格"
        assert pm.matched_by == "bazi"
        assert pm.confidence == pytest.approx(0.85)
        assert len(pm.matched_rule_ids) == 1
        assert "rule:bazi:yang_ren_ge:v1" in pm.matched_rule_ids

    def test_single_rule_no_match(self):
        evals = _load_and_eval("01_single_condition.yaml", CHART_EMPTY)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert pm is not None
        assert pm.matched is False
        assert pm.confidence == 0.0
        assert pm.matched_rule_ids == []

    def test_single_rule_match_fields(self):
        evals = _load_and_eval("01_single_condition.yaml", CHART_WITH_SEAL)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert pm.category == PatternCategory.GEJU
        assert pm.knowledge_node_ids == []
        assert len(pm.evidence) == 1
        assert pm.evidence[0].rule_id == "rule:bazi:yang_ren_ge:v1"
        assert pm.evidence[0].matched is True
        assert pm.evidence[0].system == "bazi"

    def test_single_rule_no_relevant_rules(self):
        """Pattern references rule A, but evaluations only contain rule B."""
        evals = _load_and_eval("07_has_shang_guan.yaml", CHART_WITH_SEAL)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert pm is None


# ═══════════════════════════════════════════════════════════════════
# Multi Rule matching (ALL logic)
# ═══════════════════════════════════════════════════════════════════


class TestMultiRuleMatch:
    def setup_method(self):
        self.matcher = PatternMatcher()
        self.pattern = parse_pattern_file(str(PAT_DIR / "02_multi_rule.yaml"))
        self.engine = RuleEngine()

    def _eval_granular(self, chart):
        evals = []
        for fname in ["07_has_shang_guan.yaml", "08_has_zheng_yin.yaml", "09_weak_day_master.yaml"]:
            rules = parse_rule_file(str(EXAMPLES / fname))
            evals.extend(self.engine.evaluate_all(rules, chart))
        return evals

    def test_multi_rule_all_match(self):
        evals = self._eval_granular(CHART_WITH_SEAL)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert pm is not None
        assert pm.matched is True
        assert len(pm.matched_rule_ids) == 3

    def test_multi_rule_partial_no_match(self):
        """Only 2 of 3 rules match (day_master_strength too high)."""
        chart = {
            "ten_gods_map": {"values": ["伤官", "正印"]},
            "day_master_strength": 0.8,
            "shen_sha_list": [],
        }
        evals = self._eval_granular(chart)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert pm is not None
        assert pm.matched is False

    def test_multi_rule_none_match(self):
        evals = self._eval_granular(CHART_EMPTY)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert pm is not None
        assert pm.matched is False
        assert pm.matched_rule_ids == []

    def test_multi_rule_evidence_count(self):
        evals = self._eval_granular(CHART_WITH_SEAL)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert pm is not None
        assert len(pm.evidence) == 3
        evidence_ids = {e.rule_id for e in pm.evidence}
        assert "rule:bazi:has_shang_guan:v1" in evidence_ids
        assert "rule:bazi:has_zheng_yin:v1" in evidence_ids
        assert "rule:bazi:weak_day_master:v1" in evidence_ids


# ═══════════════════════════════════════════════════════════════════
# ANY logic matching
# ═══════════════════════════════════════════════════════════════════


class TestAnyLogicMatch:
    def setup_method(self):
        self.matcher = PatternMatcher()
        self.pattern = parse_pattern_file(str(PAT_DIR / "03_any_logic.yaml"))

    def test_any_first_branch_match(self):
        """cai_xing_ge#1 (正财) matches in CHART_NO_SEAL."""
        evals = _load_and_eval("03_or.yaml", CHART_NO_SEAL)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert pm is not None
        assert pm.matched is True
        assert "rule:bazi:cai_xing_ge:v1#1" in pm.matched_rule_ids

    def test_any_second_branch_no_match(self):
        """cai_xing_ge#2 (偏财) does not match in CHART_NO_SEAL."""
        evals = _load_and_eval("03_or.yaml", CHART_NO_SEAL)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert "rule:bazi:cai_xing_ge:v1#2" not in pm.matched_rule_ids

    def test_any_neither_matches(self):
        """Neither 正财 nor 偏财 in CHART_WITH_SEAL."""
        evals = _load_and_eval("03_or.yaml", CHART_WITH_SEAL)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert pm is not None
        assert pm.matched is False


# ═══════════════════════════════════════════════════════════════════
# Cross System matching
# ═══════════════════════════════════════════════════════════════════


class TestCrossSystemMatch:
    def setup_method(self):
        self.matcher = PatternMatcher()
        self.pattern = parse_pattern_file(str(PAT_DIR / "04_cross_system.yaml"))

    def test_cross_system_both_match(self):
        bazi_evals = _load_and_eval("01_single_condition.yaml", CHART_WITH_SEAL)
        qimen_evals = _load_and_eval("05_scope.yaml", CHART_QIMEN)
        pm = self.matcher.match_cross_system(
            self.pattern, {"bazi": bazi_evals, "qimen": qimen_evals}
        )
        assert pm is not None
        assert pm.matched is True
        assert pm.matched_by == "cross_system"
        assert len(pm.matched_rule_ids) == 2

    def test_cross_system_one_missing(self):
        """Only bazi matches, qimen does not."""
        bazi_evals = _load_and_eval("01_single_condition.yaml", CHART_WITH_SEAL)
        qimen_evals = _load_and_eval("05_scope.yaml", {"dun_type": "yin", "ju": 3})
        pm = self.matcher.match_cross_system(
            self.pattern, {"bazi": bazi_evals, "qimen": qimen_evals}
        )
        assert pm is not None
        assert pm.matched is False

    def test_cross_system_evidence_systems(self):
        bazi_evals = _load_and_eval("01_single_condition.yaml", CHART_WITH_SEAL)
        qimen_evals = _load_and_eval("05_scope.yaml", CHART_QIMEN)
        pm = self.matcher.match_cross_system(
            self.pattern, {"bazi": bazi_evals, "qimen": qimen_evals}
        )
        assert pm is not None
        systems_in_evidence = {e.system for e in pm.evidence}
        assert "bazi" in systems_in_evidence
        assert "qimen" in systems_in_evidence


# ═══════════════════════════════════════════════════════════════════
# No Match
# ═══════════════════════════════════════════════════════════════════


class TestNoMatch:
    def setup_method(self):
        self.matcher = PatternMatcher()
        self.pattern = parse_pattern_file(str(PAT_DIR / "05_no_match.yaml"))

    def test_no_match_when_seal_present(self):
        """shang_guan_wu_yin rule requires NO 正印, but CHART_WITH_SEAL has it."""
        evals = _load_and_eval("04_not.yaml", CHART_WITH_SEAL)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert pm is not None
        assert pm.matched is False

    def test_no_match_returns_zero_confidence(self):
        evals = _load_and_eval("04_not.yaml", CHART_WITH_SEAL)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert pm is not None
        assert pm.confidence == 0.0

    def test_no_match_when_seal_absent(self):
        """shang_guan_wu_yin rule SHOULD match when 正印 is absent."""
        evals = _load_and_eval("04_not.yaml", CHART_NO_SEAL)
        pm = self.matcher.match(self.pattern, evals, "bazi")
        assert pm is not None
        assert pm.matched is True


# ═══════════════════════════════════════════════════════════════════
# Golden / Determinism / JSON
# ═══════════════════════════════════════════════════════════════════


class TestGolden:
    def test_determinism_same_input(self):
        """Same Pattern + same evaluations -> byte-identical JSON."""
        matcher = PatternMatcher()
        pattern = parse_pattern_file(str(PAT_DIR / "01_single_rule.yaml"))
        evals = _load_and_eval("01_single_condition.yaml", CHART_WITH_SEAL)

        pm1 = matcher.match(pattern, evals, "bazi")
        pm2 = matcher.match(pattern, evals, "bazi")
        assert pm1.model_dump_json() == pm2.model_dump_json()

    def test_determinism_cross_system(self):
        """Cross-system matching is also deterministic."""
        matcher = PatternMatcher()
        pattern = parse_pattern_file(str(PAT_DIR / "04_cross_system.yaml"))
        bazi_evals = _load_and_eval("01_single_condition.yaml", CHART_WITH_SEAL)
        qimen_evals = _load_and_eval("05_scope.yaml", CHART_QIMEN)

        pm1 = matcher.match_cross_system(pattern, {"bazi": bazi_evals, "qimen": qimen_evals})
        pm2 = matcher.match_cross_system(pattern, {"bazi": bazi_evals, "qimen": qimen_evals})
        assert pm1.model_dump_json() == pm2.model_dump_json()

    def test_json_serialization_valid(self):
        """PatternMatch JSON is valid JSON with expected fields."""
        matcher = PatternMatcher()
        pattern = parse_pattern_file(str(PAT_DIR / "01_single_rule.yaml"))
        evals = _load_and_eval("01_single_condition.yaml", CHART_WITH_SEAL)
        pm = matcher.match(pattern, evals, "bazi")

        j = json.loads(pm.model_dump_json())
        assert j["pattern_id"] == "pattern:bazi:yang_ren_ge:v1"
        assert j["matched"] is True
        assert "evidence" in j
        assert "matched_rule_ids" in j
        assert "confidence" in j

    def test_json_serialization_no_match(self):
        """Non-matched PatternMatch also serializes correctly."""
        matcher = PatternMatcher()
        pattern = parse_pattern_file(str(PAT_DIR / "05_no_match.yaml"))
        evals = _load_and_eval("04_not.yaml", CHART_WITH_SEAL)
        pm = matcher.match(pattern, evals, "bazi")

        j = json.loads(pm.model_dump_json())
        assert j["matched"] is False
        assert j["confidence"] == 0.0

    def test_match_all_multiple_patterns(self):
        """match_all returns only matched patterns."""
        matcher = PatternMatcher()
        patterns = [
            parse_pattern_file(str(PAT_DIR / "01_single_rule.yaml")),
            parse_pattern_file(str(PAT_DIR / "05_no_match.yaml")),
        ]
        evals = _load_and_eval("01_single_condition.yaml", CHART_WITH_SEAL)
        evals += _load_and_eval("04_not.yaml", CHART_WITH_SEAL)

        matches = matcher.match_all(patterns, evals, "bazi")
        assert len(matches) == 1
        assert matches[0].pattern_id == "pattern:bazi:yang_ren_ge:v1"

    def test_match_all_with_misses(self):
        """match_all_with_misses includes non-matched patterns."""
        matcher = PatternMatcher()
        patterns = [
            parse_pattern_file(str(PAT_DIR / "01_single_rule.yaml")),
            parse_pattern_file(str(PAT_DIR / "05_no_match.yaml")),
        ]
        evals = _load_and_eval("01_single_condition.yaml", CHART_WITH_SEAL)
        evals += _load_and_eval("04_not.yaml", CHART_WITH_SEAL)

        results = matcher.match_all_with_misses(patterns, evals, "bazi")
        assert len(results) == 2
        matched = [r for r in results if r.matched]
        not_matched = [r for r in results if not r.matched]
        assert len(matched) == 1
        assert len(not_matched) == 1

    def test_golden_full_chain_single(self):
        """Full chain: rule.yaml -> evaluate -> pattern -> match -> JSON."""
        evals = _load_and_eval("01_single_condition.yaml", CHART_WITH_SEAL)
        pattern = parse_pattern_file(str(PAT_DIR / "01_single_rule.yaml"))
        matcher = PatternMatcher()
        pm = matcher.match(pattern, evals, "bazi")
        j = pm.model_dump(mode="json")

        assert j["pattern_id"] == "pattern:bazi:yang_ren_ge:v1"
        assert j["pattern_name"] == "羊刃格"
        assert j["matched"] is True
        assert j["matched_by"] == "bazi"
        assert j["confidence"] == 0.85
        assert j["category"] == "geju"
        assert len(j["evidence"]) == 1
        assert j["evidence"][0]["rule_id"] == "rule:bazi:yang_ren_ge:v1"
        assert j["evidence"][0]["matched"] is True
        assert j["evidence"][0]["system"] == "bazi"

    def test_golden_full_chain_multi(self):
        """Full chain with multi-rule pattern: 3 rules -> 1 pattern."""
        engine = RuleEngine()
        evals = []
        for fname in ["07_has_shang_guan.yaml", "08_has_zheng_yin.yaml", "09_weak_day_master.yaml"]:
            rules = parse_rule_file(str(EXAMPLES / fname))
            evals.extend(engine.evaluate_all(rules, CHART_WITH_SEAL))

        pattern = parse_pattern_file(str(PAT_DIR / "02_multi_rule.yaml"))
        matcher = PatternMatcher()
        pm = matcher.match(pattern, evals, "bazi")
        j = pm.model_dump(mode="json")

        assert j["matched"] is True
        assert len(j["matched_rule_ids"]) == 3
        assert len(j["evidence"]) == 3
        assert "kn:pattern:shang_guan_pei_yin" in j["knowledge_node_ids"]

    def test_golden_full_chain_cross_system(self):
        """Full chain cross-system: bazi + qimen -> 1 cross-system pattern."""
        bazi_evals = _load_and_eval("01_single_condition.yaml", CHART_WITH_SEAL)
        qimen_evals = _load_and_eval("05_scope.yaml", CHART_QIMEN)
        pattern = parse_pattern_file(str(PAT_DIR / "04_cross_system.yaml"))
        matcher = PatternMatcher()
        pm = matcher.match_cross_system(pattern, {"bazi": bazi_evals, "qimen": qimen_evals})
        j = pm.model_dump(mode="json")

        assert j["matched"] is True
        assert j["matched_by"] == "cross_system"
        assert j["category"] == "cross_system"
        assert len(j["matched_rule_ids"]) == 2
        assert len(j["evidence"]) == 2
        systems = {e["system"] for e in j["evidence"]}
        assert systems == {"bazi", "qimen"}
