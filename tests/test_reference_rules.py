"""Golden tests for the Reference Rule implementation (Phase 6B Sprint 1).

Validates the full chain: DSL (YAML) -> Pydantic Rule -> RuleEngine.evaluate() -> JSON.

Each test corresponds to an example in reference/examples/.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from reference.engine import RuleEngine, resolve_field
from reference.models import Rule
from reference.parser import parse_rule_file

EXAMPLES = Path(__file__).parent.parent / "reference" / "examples"

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

CHART_GUAN_SHA = {
    "ten_gods_map": {"values": ["正官", "七杀", "比肩"]},
    "day_master_strength": 0.4,
    "shen_sha_list": ["羊刃"],
}

CHART_QIMEN = {
    "dun_type": "yang",
    "ju": 6,
}


# ═══════════════════════════════════════════════════════════════════
# Parser tests
# ═══════════════════════════════════════════════════════════════════


class TestParser:
    def test_single_condition(self):
        rules = parse_rule_file(str(EXAMPLES / "01_single_condition.yaml"))
        assert len(rules) == 1
        r = rules[0]
        assert r.id == "rule:bazi:yang_ren_ge:v1"
        assert r.name == "羊刃格"
        assert len(r.conditions) == 1
        assert r.conditions[0].field == "shen_sha_list"
        assert r.conditions[0].operator.value == "contains"
        assert r.conditions[0].value == "羊刃"
        assert r.conditions[0].negate is False
        assert len(r.results) == 1
        assert r.results[0].domain.value == "personality"
        assert r.results[0].conclusion == "性格刚毅果敢"
        assert r.priority == 60
        assert r.source.text == "三命通会"

    def test_and_conditions(self):
        rules = parse_rule_file(str(EXAMPLES / "02_and.yaml"))
        assert len(rules) == 1
        r = rules[0]
        assert r.id == "rule:bazi:shang_guan_pei_yin:v1"
        assert len(r.conditions) == 3
        assert all(not c.negate for c in r.conditions)
        assert len(r.results) == 2
        assert r.scope is not None
        assert r.scope.systems == ["bazi"]
        assert r.conflicts == ["rule:bazi:shang_guan_jian_sha:v1"]

    def test_or_dnf_expansion(self):
        rules = parse_rule_file(str(EXAMPLES / "03_or.yaml"))
        assert len(rules) == 2
        assert rules[0].id == "rule:bazi:cai_xing_ge:v1#1"
        assert rules[1].id == "rule:bazi:cai_xing_ge:v1#2"
        assert len(rules[0].conditions) == 1
        assert rules[0].conditions[0].value == "正财"
        assert rules[1].conditions[0].value == "偏财"
        # Both rules share the same results, priority, source
        assert rules[0].results == rules[1].results
        assert rules[0].priority == rules[1].priority
        assert rules[0].source.text == rules[1].source.text

    def test_not_negate(self):
        rules = parse_rule_file(str(EXAMPLES / "04_not.yaml"))
        assert len(rules) == 1
        r = rules[0]
        assert len(r.conditions) == 2
        assert r.conditions[0].negate is False
        assert r.conditions[1].negate is True
        assert r.conditions[1].value == "正印"

    def test_scope(self):
        rules = parse_rule_file(str(EXAMPLES / "05_scope.yaml"))
        assert len(rules) == 1
        r = rules[0]
        assert r.scope is not None
        assert r.scope.systems == ["qimen"]
        assert r.scope.gender == ["male"]
        assert r.scope.age_range == (25, 60)
        assert r.scope.lunar_month_range == (1, 6)

    def test_complex_dnf(self):
        """any inside all -> DNF produces 2 rules, each with 2 conditions."""
        rules = parse_rule_file(str(EXAMPLES / "06_complex.yaml"))
        assert len(rules) == 2
        assert rules[0].id == "rule:bazi:guan_sha_hun:v1#1"
        assert rules[1].id == "rule:bazi:guan_sha_hun:v1#2"
        # Each rule has 2 conditions: one from any branch + one from not
        assert len(rules[0].conditions) == 2
        assert len(rules[1].conditions) == 2
        # First condition differs (正官 vs 七杀)
        assert rules[0].conditions[0].value == "正官"
        assert rules[1].conditions[0].value == "七杀"
        # Second condition is the not (negate=True)
        assert rules[0].conditions[1].negate is True
        assert rules[1].conditions[1].negate is True
        assert rules[0].conditions[1].value == "天乙贵人"


# ═══════════════════════════════════════════════════════════════════
# Engine tests
# ═══════════════════════════════════════════════════════════════════


class TestEngine:
    def setup_method(self):
        self.engine = RuleEngine()

    def test_single_match(self):
        rules = parse_rule_file(str(EXAMPLES / "01_single_condition.yaml"))
        ev = self.engine.evaluate(rules[0], CHART_WITH_SEAL)
        assert ev.matched is True
        assert ev.rule_id == "rule:bazi:yang_ren_ge:v1"
        assert len(ev.results) == 1
        assert ev.results[0].conclusion == "性格刚毅果敢"
        assert ev.priority == 60
        assert ev.confidence == pytest.approx(0.9)

    def test_single_no_match(self):
        rules = parse_rule_file(str(EXAMPLES / "01_single_condition.yaml"))
        ev = self.engine.evaluate(rules[0], {"shen_sha_list": ["天乙贵人"]})
        assert ev.matched is False
        assert ev.results == []

    def test_and_all_match(self):
        rules = parse_rule_file(str(EXAMPLES / "02_and.yaml"))
        ev = self.engine.evaluate(rules[0], CHART_WITH_SEAL)
        assert ev.matched is True
        assert len(ev.results) == 2

    def test_and_partial_no_match(self):
        rules = parse_rule_file(str(EXAMPLES / "02_and.yaml"))
        chart = {
            "ten_gods_map": {"values": ["伤官", "正印"]},
            "day_master_strength": 0.8,
            "shen_sha_list": [],
        }
        ev = self.engine.evaluate(rules[0], chart)
        assert ev.matched is False

    def test_or_first_branch_match(self):
        rules = parse_rule_file(str(EXAMPLES / "03_or.yaml"))
        ev0 = self.engine.evaluate(rules[0], CHART_NO_SEAL)
        assert ev0.matched is True  # 正财 in values
        ev1 = self.engine.evaluate(rules[1], CHART_NO_SEAL)
        assert ev1.matched is False  # 偏财 not in values

    def test_not_condition(self):
        rules = parse_rule_file(str(EXAMPLES / "04_not.yaml"))
        ev = self.engine.evaluate(rules[0], CHART_NO_SEAL)
        assert ev.matched is True  # 伤官 present, 正印 absent (negate=True passes)

    def test_not_condition_fails_when_present(self):
        rules = parse_rule_file(str(EXAMPLES / "04_not.yaml"))
        ev = self.engine.evaluate(rules[0], CHART_WITH_SEAL)
        assert ev.matched is False  # 正印 present -> negate=True fails

    def test_complex_match(self):
        rules = parse_rule_file(str(EXAMPLES / "06_complex.yaml"))
        ev0 = self.engine.evaluate(rules[0], CHART_GUAN_SHA)
        assert ev0.matched is True  # 正官 + no 天乙贵人
        ev1 = self.engine.evaluate(rules[1], CHART_GUAN_SHA)
        assert ev1.matched is True  # 七杀 + no 天乙贵人

    def test_complex_no_match_with_tianyi(self):
        rules = parse_rule_file(str(EXAMPLES / "06_complex.yaml"))
        chart = {
            "ten_gods_map": {"values": ["正官", "七杀"]},
            "shen_sha_list": ["天乙贵人"],
        }
        ev0 = self.engine.evaluate(rules[0], chart)
        assert ev0.matched is False  # 天乙贵人 present -> not fails

    def test_qimen_scope(self):
        rules = parse_rule_file(str(EXAMPLES / "05_scope.yaml"))
        ev = self.engine.evaluate(rules[0], CHART_QIMEN)
        assert ev.matched is True
        assert ev.results[0].conclusion == "阳遁金局，主肃杀果断"

    def test_evaluate_all(self):
        rules = parse_rule_file(str(EXAMPLES / "03_or.yaml"))
        evals = self.engine.evaluate_all(rules, CHART_NO_SEAL)
        assert len(evals) == 2
        assert evals[0].matched is True
        assert evals[1].matched is False

    def test_evaluate_matched_only(self):
        rules = parse_rule_file(str(EXAMPLES / "03_or.yaml"))
        evals = self.engine.evaluate_matched(rules, CHART_NO_SEAL)
        assert len(evals) == 1
        assert evals[0].matched is True


# ═══════════════════════════════════════════════════════════════════
# Field path resolution tests
# ═══════════════════════════════════════════════════════════════════


class TestFieldPath:
    def test_simple_path(self):
        data = {"day_master_strength": 0.35}
        assert resolve_field(data, "day_master_strength") == 0.35

    def test_dotted_path(self):
        data = {"ten_gods_map": {"values": ["伤官", "正印"]}}
        assert resolve_field(data, "ten_gods_map.values") == ["伤官", "正印"]

    def test_indexed_path(self):
        data = {"pillars": [{"ten_gods_stem": "比肩"}, {"ten_gods_stem": "伤官"}]}
        assert resolve_field(data, "pillars[0].ten_gods_stem") == "比肩"
        assert resolve_field(data, "pillars[1].ten_gods_stem") == "伤官"

    def test_key_error(self):
        with pytest.raises(KeyError):
            resolve_field({"a": 1}, "b")


# ═══════════════════════════════════════════════════════════════════
# Golden end-to-end tests
# ═══════════════════════════════════════════════════════════════════


class TestGoldenChain:
    """Golden tests: verify the full DSL -> Rule -> Evaluate -> JSON chain."""

    def test_golden_single_condition(self):
        """01_single_condition: matched=True, 1 result, correct JSON fields."""
        rules = parse_rule_file(str(EXAMPLES / "01_single_condition.yaml"))
        engine = RuleEngine()
        ev = engine.evaluate(rules[0], CHART_WITH_SEAL)
        j = ev.model_dump(mode="json")

        assert j["rule_id"] == "rule:bazi:yang_ren_ge:v1"
        assert j["matched"] is True
        assert len(j["results"]) == 1
        assert j["results"][0]["domain"] == "personality"
        assert j["results"][0]["conclusion"] == "性格刚毅果敢"
        assert j["results"][0]["weight"] == 0.75
        assert j["results"][0]["direction"] == "positive"
        assert j["priority"] == 60
        assert j["confidence"] == 0.9

    def test_golden_and(self):
        """02_and: 3 conditions all match, 2 results."""
        rules = parse_rule_file(str(EXAMPLES / "02_and.yaml"))
        engine = RuleEngine()
        ev = engine.evaluate(rules[0], CHART_WITH_SEAL)
        j = ev.model_dump(mode="json")

        assert j["matched"] is True
        assert len(j["results"]) == 2
        assert j["results"][0]["domain"] == "career"
        assert j["results"][1]["domain"] == "personality"

    def test_golden_or_dnf(self):
        """03_or: DNF expansion to 2 rules, first matches, second doesn't."""
        rules = parse_rule_file(str(EXAMPLES / "03_or.yaml"))
        engine = RuleEngine()
        evals = engine.evaluate_all(rules, CHART_NO_SEAL)

        assert len(evals) == 2
        assert evals[0].rule_id == "rule:bazi:cai_xing_ge:v1#1"
        assert evals[0].matched is True
        assert evals[1].rule_id == "rule:bazi:cai_xing_ge:v1#2"
        assert evals[1].matched is False

    def test_golden_not(self):
        """04_not: negate=True condition, matches when value absent."""
        rules = parse_rule_file(str(EXAMPLES / "04_not.yaml"))
        engine = RuleEngine()
        ev = engine.evaluate(rules[0], CHART_NO_SEAL)
        j = ev.model_dump(mode="json")

        assert j["matched"] is True
        assert j["results"][0]["direction"] == "negative"

    def test_golden_json_serialization(self):
        """Verify RuleEvaluation JSON serialization is valid JSON."""
        rules = parse_rule_file(str(EXAMPLES / "01_single_condition.yaml"))
        engine = RuleEngine()
        ev = engine.evaluate(rules[0], CHART_WITH_SEAL)
        json_str = ev.model_dump_json()

        parsed = json.loads(json_str)
        assert parsed["rule_id"] == "rule:bazi:yang_ren_ge:v1"
        assert parsed["matched"] is True

    def test_golden_rule_model_json_schema(self):
        """Verify Rule can export JSON Schema (Phase 6 compatibility)."""
        schema = Rule.model_json_schema()
        assert "properties" in schema
        assert "id" in schema["properties"]
        assert "conditions" in schema["properties"]
        assert "results" in schema["properties"]

    def test_golden_determinism(self):
        """Same input always produces same output (byte-identical JSON)."""
        rules = parse_rule_file(str(EXAMPLES / "02_and.yaml"))
        engine = RuleEngine()

        ev1 = engine.evaluate(rules[0], CHART_WITH_SEAL)
        ev2 = engine.evaluate(rules[0], CHART_WITH_SEAL)

        assert ev1.model_dump_json() == ev2.model_dump_json()
