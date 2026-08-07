"""Golden tests for the Reference Evidence Layer (Phase 6B Sprint 3).

Validates the chain:
    RuleEvaluation --> EvidenceItem --> Evidence --> JSON
    PatternMatch   --> EvidenceItem --> Evidence --> JSON

Tests cover:
  - Model creation and validation (EvidenceItem, Evidence, EvidenceSource)
  - All 4 EvidenceType source types
  - Rule -> Evidence conversion
  - Pattern -> Evidence conversion
  - Combined rule + pattern Evidence
  - JSON serialization and roundtrip
  - Deterministic output (repeated input -> identical JSON)
  - Evidence traceability (every item traces to its source)
  - Contract export, determinism, and file validation
  - KnowledgeEvidenceProvider protocol (interface only)
  - Full-chain golden examples
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from reference.engine import RuleEngine
from reference.evidence import (
    Evidence,
    EvidenceItem,
    EvidenceSource,
    EvidenceType,
    KnowledgeEvidenceProvider,
    make_evidence_group_id,
    make_evidence_item_id,
)
from reference.evidence_builder import (
    CONTRACT_PATH,
    EvidenceBuilder,
    category_to_domain,
    export_evidence_contract,
)
from reference.models import (
    Domain,
    ResultDirection,
    RuleEvaluation,
    RuleResult,
)
from reference.parser import parse_rule_file
from reference.pattern_matcher import PatternMatcher
from reference.patterns import (
    PatternCategory,
    PatternMatch,
    parse_pattern_file,
)

EXAMPLES = Path(__file__).parent.parent / "reference" / "examples"
PAT_DIR = EXAMPLES / "patterns"

CHART_WITH_SEAL = {
    "ten_gods_map": {"values": ["伤官", "正印", "比肩"]},
    "day_master_strength": 0.35,
    "shen_sha_list": ["羊刃", "天乙贵人"],
}
CHART_NO_YANG_REN = {
    "ten_gods_map": {"values": ["正官"]},
    "day_master_strength": 0.7,
    "shen_sha_list": ["天乙贵人"],
}
CHART_QIMEN = {"dun_type": "yang", "ju": 6}


# == Helpers ==


def _make_result(
    conclusion="测试结论",
    domain=Domain.PERSONALITY,
    weight=0.8,
    direction=ResultDirection.POSITIVE,
    conclusion_node_id=None,
):
    return RuleResult(
        domain=domain,
        conclusion=conclusion,
        conclusion_node_id=conclusion_node_id,
        weight=weight,
        direction=direction,
    )


def _make_rule_eval(
    rule_id="rule:bazi:test_rule:v1",
    matched=True,
    results=None,
    priority=50,
    confidence=0.9,
):
    return RuleEvaluation(
        rule_id=rule_id,
        matched=matched,
        results=results or [],
        priority=priority,
        confidence=confidence,
    )


def _make_pattern_match(
    pattern_id="pattern:bazi:test_pat:v1",
    pattern_name="测试格局",
    matched=True,
    matched_by="bazi",
    confidence=0.85,
    matched_rule_ids=None,
    evidence=None,
    knowledge_node_ids=None,
    category=PatternCategory.GEJU,
):
    return PatternMatch(
        pattern_id=pattern_id,
        pattern_name=pattern_name,
        matched=matched,
        matched_by=matched_by,
        confidence=confidence,
        matched_rule_ids=matched_rule_ids or [],
        evidence=evidence or [],
        knowledge_node_ids=knowledge_node_ids or [],
        category=category,
    )


def _make_evidence_item(
    evidence_id=None,
    source_type=EvidenceType.RULE,
    source_id="rule:bazi:test_rule:v1",
    system="bazi",
    domain=Domain.PERSONALITY,
    confidence=0.9,
    conclusion="测试结论",
    trace=None,
    metadata=None,
    version="1.0.0",
):
    return EvidenceItem(
        evidence_id=evidence_id
        or make_evidence_item_id(
            source_type.value,
            source_id,
            system,
            conclusion,
        ),
        source_type=source_type,
        source_id=source_id,
        system=system,
        domain=domain,
        confidence=confidence,
        conclusion=conclusion,
        trace=trace or [source_id],
        metadata=metadata or {},
        version=version,
    )


# ==================================================================
# Model tests
# ==================================================================


class TestEvidenceModels:
    def test_evidence_item_creation(self):
        item = _make_evidence_item()
        assert item.source_type == EvidenceType.RULE
        assert item.source_id == "rule:bazi:test_rule:v1"
        assert item.system == "bazi"
        assert item.domain == Domain.PERSONALITY
        assert item.confidence == pytest.approx(0.9)
        assert item.conclusion == "测试结论"
        assert item.trace == ["rule:bazi:test_rule:v1"]
        assert item.version == "1.0.0"

    def test_evidence_item_required_fields_in_json(self):
        item = _make_evidence_item()
        j = json.loads(item.model_dump_json())
        required = [
            "evidence_id",
            "source_type",
            "source_id",
            "system",
            "domain",
            "confidence",
            "conclusion",
            "trace",
            "metadata",
            "version",
        ]
        for field in required:
            assert field in j, f"Missing required field: {field}"

    def test_evidence_item_deterministic_id(self):
        id1 = make_evidence_item_id("rule", "rule:bazi:x:v1", "bazi", "结论A")
        id2 = make_evidence_item_id("rule", "rule:bazi:x:v1", "bazi", "结论A")
        assert id1 == id2
        id3 = make_evidence_item_id("rule", "rule:bazi:x:v1", "bazi", "结论B")
        assert id1 != id3

    def test_evidence_type_enum_values(self):
        assert EvidenceType.RULE.value == "rule"
        assert EvidenceType.PATTERN.value == "pattern"
        assert EvidenceType.KNOWLEDGE_NODE.value == "knowledge_node"
        assert EvidenceType.RELATION.value == "relation"
        assert len(EvidenceType) == 4

    def test_evidence_source_creation(self):
        src = EvidenceSource(
            source_type=EvidenceType.RULE,
            source_id="rule:bazi:x:v1",
            source_name="羊刃格",
            source_ref="三命通会",
            credibility=0.85,
        )
        assert src.source_type == EvidenceType.RULE
        assert src.source_name == "羊刃格"
        assert src.credibility == pytest.approx(0.85)

    def test_evidence_creation(self):
        item = _make_evidence_item()
        ev = Evidence(
            evidence_id="ev:personality:test123",
            domain=Domain.PERSONALITY,
            conclusion="测试结论",
            confidence=0.9,
            system="bazi",
            items=[item],
        )
        assert ev.domain == Domain.PERSONALITY
        assert len(ev.items) == 1
        assert ev.confidence == pytest.approx(0.9)

    def test_evidence_empty_items_rejected(self):
        """Evidence with empty items list must be rejected."""
        with pytest.raises(ValidationError):
            Evidence(
                evidence_id="ev:test:xxx",
                domain=Domain.PERSONALITY,
                conclusion="test",
                confidence=0.5,
                system="bazi",
                items=[],
            )

    def test_evidence_serialization_roundtrip(self):
        item = _make_evidence_item()
        ev = Evidence(
            evidence_id="ev:personality:test123",
            domain=Domain.PERSONALITY,
            conclusion="测试结论",
            confidence=0.9,
            system="bazi",
            items=[item],
        )
        j = ev.model_dump_json()
        ev2 = Evidence.model_validate_json(j)
        assert ev2.evidence_id == ev.evidence_id
        assert ev2.items[0].evidence_id == item.evidence_id


class TestEvidenceItemSourceTypes:
    """Phase 6 test_plan: test_evidence_item_source_types -- all 4 types."""

    def test_all_four_source_types(self):
        for st in EvidenceType:
            item = _make_evidence_item(source_type=st, source_id=f"id:{st.value}")
            assert item.source_type == st
            j = json.loads(item.model_dump_json())
            assert j["source_type"] == st.value


# ==================================================================
# Rule -> Evidence
# ==================================================================


class TestRuleToEvidence:
    def test_from_rule_evaluation_matched(self):
        ev = _make_rule_eval(
            results=[_make_result(conclusion="性格刚毅", conclusion_node_id="kn:p:resolute")],
        )
        builder = EvidenceBuilder()
        items = builder.from_rule_evaluation(ev, "bazi")
        assert len(items) == 1
        assert items[0].source_type == EvidenceType.RULE
        assert items[0].source_id == "rule:bazi:test_rule:v1"
        assert items[0].conclusion == "性格刚毅"
        assert items[0].confidence == pytest.approx(0.9)

    def test_from_rule_evaluation_not_matched(self):
        ev = _make_rule_eval(matched=False, results=[])
        builder = EvidenceBuilder()
        items = builder.from_rule_evaluation(ev, "bazi")
        assert items == []

    def test_from_rule_evaluation_multiple_results(self):
        ev = _make_rule_eval(
            rule_id="rule:bazi:multi:v1",
            results=[
                _make_result(conclusion="结论A", domain=Domain.PERSONALITY),
                _make_result(conclusion="结论B", domain=Domain.CAREER),
            ],
        )
        builder = EvidenceBuilder()
        items = builder.from_rule_evaluation(ev, "bazi")
        assert len(items) == 2
        assert items[0].conclusion == "结论A"
        assert items[1].conclusion == "结论B"
        assert items[0].evidence_id != items[1].evidence_id

    def test_from_rule_evaluation_with_rule_enrichment(self):
        rules = parse_rule_file(str(EXAMPLES / "01_single_condition.yaml"))
        rule = rules[0]
        engine = RuleEngine()
        evals = engine.evaluate_all(rules, CHART_WITH_SEAL)
        builder = EvidenceBuilder()
        items = builder.from_rule_evaluation(evals[0], "bazi", rule=rule)
        assert len(items) == 1
        assert items[0].metadata["source_name"] == rule.name
        assert items[0].metadata["source_ref"] == rule.source.text
        assert items[0].metadata["credibility"] == rule.source.credibility

    def test_build_from_evaluations(self):
        eval1 = _make_rule_eval(
            rule_id="rule:bazi:rule_a:v1",
            results=[_make_result(conclusion="结论A", domain=Domain.PERSONALITY)],
        )
        eval2 = _make_rule_eval(
            rule_id="rule:bazi:rule_b:v1",
            results=[_make_result(conclusion="结论B", domain=Domain.CAREER)],
        )
        builder = EvidenceBuilder()
        evidence = builder.build_from_evaluations([eval1, eval2], "bazi")
        assert len(evidence) == 2

    def test_build_from_evaluations_same_conclusion_grouped(self):
        eval1 = _make_rule_eval(
            rule_id="rule:bazi:rule_a:v1",
            results=[_make_result(conclusion="性格刚毅", domain=Domain.PERSONALITY, weight=0.7)],
            confidence=0.8,
        )
        eval2 = _make_rule_eval(
            rule_id="rule:bazi:rule_b:v1",
            results=[_make_result(conclusion="性格刚毅", domain=Domain.PERSONALITY, weight=0.9)],
            confidence=0.85,
        )
        builder = EvidenceBuilder()
        evidence = builder.build_from_evaluations([eval1, eval2], "bazi")
        assert len(evidence) == 1
        assert evidence[0].conclusion == "性格刚毅"
        assert len(evidence[0].items) == 2
        assert evidence[0].confidence == pytest.approx(0.85)

    def test_build_from_evaluations_no_match_empty(self):
        ev = _make_rule_eval(matched=False, results=[])
        builder = EvidenceBuilder()
        evidence = builder.build_from_evaluations([ev], "bazi")
        assert evidence == []


# ==================================================================
# Pattern -> Evidence
# ==================================================================


class TestPatternToEvidence:
    def test_from_pattern_match_matched(self):
        pm = _make_pattern_match(
            pattern_id="pattern:bazi:test_geju:v1",
            pattern_name="测试格局",
            matched_rule_ids=["rule:bazi:rule_a:v1"],
            knowledge_node_ids=["kn:pattern:test"],
            category=PatternCategory.GEJU,
        )
        builder = EvidenceBuilder()
        item = builder.from_pattern_match(pm)
        assert item is not None
        assert item.source_type == EvidenceType.PATTERN
        assert item.source_id == "pattern:bazi:test_geju:v1"
        assert item.conclusion == "测试格局"
        assert item.confidence == pytest.approx(0.85)
        assert item.domain == Domain.OVERALL

    def test_from_pattern_match_not_matched(self):
        pm = _make_pattern_match(matched=False, confidence=0.0)
        builder = EvidenceBuilder()
        item = builder.from_pattern_match(pm)
        assert item is None

    def test_from_pattern_matches(self):
        pm1 = _make_pattern_match(pattern_id="pattern:bazi:p1:v1", pattern_name="格局一")
        pm2 = _make_pattern_match(pattern_id="pattern:bazi:p2:v1", pattern_name="格局二")
        pm3 = _make_pattern_match(matched=False, confidence=0.0)
        builder = EvidenceBuilder()
        items = builder.from_pattern_matches([pm1, pm2, pm3])
        assert len(items) == 2

    def test_build_from_pattern_matches(self):
        pm = _make_pattern_match(
            pattern_id="pattern:bazi:test_geju:v1",
            pattern_name="测试格局",
            matched_rule_ids=["rule:bazi:rule_a:v1"],
        )
        builder = EvidenceBuilder()
        evidence = builder.build_from_pattern_matches([pm])
        assert len(evidence) == 1
        assert evidence[0].conclusion == "测试格局"
        assert evidence[0].items[0].source_type == EvidenceType.PATTERN

    def test_category_to_domain_mapping(self):
        assert category_to_domain(PatternCategory.PERSONALITY) == Domain.PERSONALITY
        assert category_to_domain(PatternCategory.CAREER) == Domain.CAREER
        assert category_to_domain(PatternCategory.GEJU) == Domain.OVERALL
        assert category_to_domain(PatternCategory.CROSS_SYSTEM) == Domain.OVERALL
        assert category_to_domain(None) == Domain.OVERALL


# ==================================================================
# Combined Evidence
# ==================================================================


class TestCombinedEvidence:
    def test_build_all_combined(self):
        evals = [
            _make_rule_eval(
                rule_id="rule:bazi:rule_a:v1",
                results=[_make_result(conclusion="性格刚毅", domain=Domain.PERSONALITY)],
            )
        ]
        pm = _make_pattern_match(
            pattern_id="pattern:bazi:test_geju:v1",
            pattern_name="测试格局",
            matched_rule_ids=["rule:bazi:rule_a:v1"],
        )
        builder = EvidenceBuilder()
        evidence = builder.build_all(evals, [pm], "bazi")
        assert len(evidence) == 2
        types = {e.items[0].source_type for e in evidence}
        assert EvidenceType.RULE in types
        assert EvidenceType.PATTERN in types

    def test_build_all_cross_system_pattern(self):
        pm = _make_pattern_match(
            pattern_id="pattern:cross:test:v1",
            pattern_name="跨体系格局",
            matched_by="cross_system",
            matched_rule_ids=["rule:bazi:x:v1", "rule:qimen:y:v1"],
            knowledge_node_ids=["kn:cross:test"],
            category=PatternCategory.CROSS_SYSTEM,
        )
        builder = EvidenceBuilder()
        evidence = builder.build_from_pattern_matches([pm])
        assert len(evidence) == 1
        assert evidence[0].system == "cross_system"


# ==================================================================
# Traceability
# ==================================================================


class TestTraceability:
    def test_rule_evidence_trace(self):
        ev = _make_rule_eval(
            rule_id="rule:bazi:trace_test:v1",
            results=[
                _make_result(
                    conclusion="可追溯结论",
                    conclusion_node_id="kn:personality:trace",
                )
            ],
        )
        builder = EvidenceBuilder()
        items = builder.from_rule_evaluation(ev, "bazi")
        assert len(items) == 1
        assert items[0].trace[0] == "rule:bazi:trace_test:v1"
        assert items[0].trace[1] == "kn:personality:trace"
        assert len(items[0].trace) == 2

    def test_pattern_evidence_trace(self):
        pm = _make_pattern_match(
            pattern_id="pattern:bazi:trace_pat:v1",
            pattern_name="追溯格局",
            matched_rule_ids=["rule:bazi:r2:v1", "rule:bazi:r1:v1"],
            knowledge_node_ids=["kn:p:z", "kn:p:a"],
        )
        builder = EvidenceBuilder()
        item = builder.from_pattern_match(pm)
        assert item is not None
        assert item.trace[0] == "pattern:bazi:trace_pat:v1"
        assert "rule:bazi:r1:v1" in item.trace
        assert "rule:bazi:r2:v1" in item.trace
        assert "kn:p:a" in item.trace
        assert "kn:p:z" in item.trace

    def test_trace_starts_with_source_id(self):
        ev = _make_rule_eval(
            rule_id="rule:bazi:source_check:v1",
            results=[_make_result(conclusion="检查")],
        )
        builder = EvidenceBuilder()
        items = builder.from_rule_evaluation(ev, "bazi")
        assert items[0].trace[0] == items[0].source_id


# ==================================================================
# Determinism
# ==================================================================


class TestDeterminism:
    def test_deterministic_item_id_repeated(self):
        builder = EvidenceBuilder()
        ev = _make_rule_eval(
            results=[_make_result(conclusion="确定性测试")],
        )
        items1 = builder.from_rule_evaluation(ev, "bazi")
        items2 = builder.from_rule_evaluation(ev, "bazi")
        assert items1[0].evidence_id == items2[0].evidence_id

    def test_deterministic_output_repeated(self):
        builder = EvidenceBuilder()
        ev1 = _make_rule_eval(
            rule_id="rule:bazi:det_a:v1",
            results=[_make_result(conclusion="结论X", domain=Domain.PERSONALITY)],
        )
        ev2 = _make_rule_eval(
            rule_id="rule:bazi:det_b:v1",
            results=[_make_result(conclusion="结论Y", domain=Domain.CAREER)],
        )
        ev_list = [ev1, ev2]
        e1 = builder.build_from_evaluations(ev_list, "bazi")
        e2 = builder.build_from_evaluations(ev_list, "bazi")
        assert e1[0].model_dump_json() == e2[0].model_dump_json()
        assert e1[1].model_dump_json() == e2[1].model_dump_json()

    def test_deterministic_group_id(self):
        id1 = make_evidence_group_id("personality", "结论Z", ["ev:bazi:aaa", "ev:bazi:bbb"])
        id2 = make_evidence_group_id("personality", "结论Z", ["ev:bazi:bbb", "ev:bazi:aaa"])
        assert id1 == id2


# ==================================================================
# JSON Serialization
# ==================================================================


class TestJSONSerialization:
    def test_json_roundtrip_evidence_item(self):
        item = _make_evidence_item(
            trace=["rule:bazi:x:v1", "kn:test"],
            metadata={"source_name": "测试规则"},
        )
        j = item.model_dump_json()
        item2 = EvidenceItem.model_validate_json(j)
        assert item2.evidence_id == item.evidence_id
        assert item2.trace == item.trace
        assert item2.metadata["source_name"] == "测试规则"

    def test_json_serialization_all_fields_present(self):
        ev = _make_rule_eval(
            results=[_make_result(conclusion="JSON测试", conclusion_node_id="kn:j:test")],
        )
        builder = EvidenceBuilder()
        evidence = builder.build_from_evaluations([ev], "bazi")
        j = json.loads(evidence[0].model_dump_json())
        assert "evidence_id" in j
        assert "domain" in j
        assert "conclusion" in j
        assert "confidence" in j
        assert "system" in j
        assert "items" in j
        assert "version" in j
        item_j = j["items"][0]
        assert "evidence_id" in item_j
        assert "source_type" in item_j
        assert "trace" in item_j
        assert "metadata" in item_j


# ==================================================================
# Contract
# ==================================================================


class TestContract:
    def test_contract_export_structure(self):
        contract = export_evidence_contract()
        assert contract["contract_name"] == "evidence"
        assert contract["contract_version"] == "1.0.0"
        assert "description" in contract
        assert "models" in contract
        assert "EvidenceItem" in contract["models"]
        assert "Evidence" in contract["models"]
        assert "golden_examples" in contract

    def test_contract_evidence_types(self):
        contract = export_evidence_contract()
        assert set(contract["evidence_types"]) == {
            "rule",
            "pattern",
            "knowledge_node",
            "relation",
        }

    def test_contract_golden_examples_valid(self):
        contract = export_evidence_contract()
        examples = contract["golden_examples"]
        assert len(examples) >= 5
        for ex in examples:
            assert "name" in ex
            assert "description" in ex
            assert "input_type" in ex
            assert "evidence" in ex

    def test_contract_golden_example_has_items(self):
        contract = export_evidence_contract()
        single = [e for e in contract["golden_examples"] if e["name"] == "single_rule_to_evidence"][
            0
        ]
        assert len(single["evidence"]) == 1
        ev = single["evidence"][0]
        assert len(ev["items"]) >= 1
        assert ev["items"][0]["source_type"] == "rule"

    def test_contract_determinism(self):
        c1 = export_evidence_contract()
        c2 = export_evidence_contract()
        assert c1 == c2
        assert json.dumps(c1, sort_keys=True) == json.dumps(c2, sort_keys=True)

    def test_contract_file_matches_runtime(self):
        with open(CONTRACT_PATH, encoding="utf-8") as f:
            file_contract = json.load(f)
        runtime_contract = export_evidence_contract()
        assert file_contract == runtime_contract

    def test_contract_validation_evidence_items(self):
        """Every evidence item in the contract conforms to the model spec."""
        contract = export_evidence_contract()
        required = set(contract["models"]["EvidenceItem"]["required"])
        for ex in contract["golden_examples"]:
            for ev in ex["evidence"]:
                for item in ev["items"]:
                    assert required.issubset(set(item.keys())), (
                        f"Item missing required fields in {ex['name']}"
                    )


# ==================================================================
# Knowledge Protocol (interface only, no implementation)
# ==================================================================


class TestKnowledgeProtocol:
    def test_knowledge_protocol_has_methods(self):
        assert hasattr(KnowledgeEvidenceProvider, "from_knowledge_node")
        assert hasattr(KnowledgeEvidenceProvider, "from_knowledge_nodes")

    def test_knowledge_protocol_runtime_checkable(self):
        class _Stub:
            def from_knowledge_node(self, node_id, system):
                return None

            def from_knowledge_nodes(self, node_ids, system):
                return []

        assert isinstance(_Stub(), KnowledgeEvidenceProvider)

    def test_knowledge_protocol_rejects_non_implementor(self):
        class _NotAProvider:
            pass

        assert not isinstance(_NotAProvider(), KnowledgeEvidenceProvider)


# ==================================================================
# Golden full-chain tests
# ==================================================================


class TestGoldenFullChain:
    def test_golden_full_chain_rule_to_evidence(self):
        rules = parse_rule_file(str(EXAMPLES / "01_single_condition.yaml"))
        engine = RuleEngine()
        evals = engine.evaluate_all(rules, CHART_WITH_SEAL)
        builder = EvidenceBuilder()
        evidence = builder.build_from_evaluations(evals, "bazi")
        assert len(evidence) >= 1
        j = json.loads(evidence[0].model_dump_json())
        assert j["items"][0]["source_type"] == "rule"
        assert j["items"][0]["source_id"] == "rule:bazi:yang_ren_ge:v1"
        assert j["items"][0]["trace"][0] == "rule:bazi:yang_ren_ge:v1"

    def test_golden_full_chain_pattern_to_evidence(self):
        multi_rules = []
        for fname in ["07_has_shang_guan.yaml", "08_has_zheng_yin.yaml", "09_weak_day_master.yaml"]:
            multi_rules.extend(parse_rule_file(str(EXAMPLES / fname)))
        engine = RuleEngine()
        evals = engine.evaluate_all(multi_rules, CHART_WITH_SEAL)
        pattern = parse_pattern_file(str(PAT_DIR / "02_multi_rule.yaml"))
        matcher = PatternMatcher()
        pm = matcher.match(pattern, evals, "bazi")
        assert pm is not None and pm.matched
        builder = EvidenceBuilder()
        evidence = builder.build_from_pattern_matches([pm])
        assert len(evidence) == 1
        j = json.loads(evidence[0].model_dump_json())
        assert j["items"][0]["source_type"] == "pattern"
        assert j["items"][0]["conclusion"] == "伤官佩印格局"
        assert "kn:pattern:shang_guan_pei_yin" in j["items"][0]["trace"]

    def test_golden_full_chain_no_match_produces_no_evidence(self):
        rules = parse_rule_file(str(EXAMPLES / "01_single_condition.yaml"))
        engine = RuleEngine()
        evals = engine.evaluate_all(rules, CHART_NO_YANG_REN)
        assert all(not ev.matched for ev in evals)
        builder = EvidenceBuilder()
        evidence = builder.build_from_evaluations(evals, "bazi")
        assert evidence == []

    def test_golden_full_chain_cross_system(self):
        bazi_evals = engine_eval("01_single_condition.yaml", CHART_WITH_SEAL)
        qimen_evals = engine_eval("05_scope.yaml", CHART_QIMEN)
        pattern = parse_pattern_file(str(PAT_DIR / "04_cross_system.yaml"))
        matcher = PatternMatcher()
        pm = matcher.match_cross_system(
            pattern,
            {"bazi": bazi_evals, "qimen": qimen_evals},
        )
        assert pm is not None and pm.matched
        builder = EvidenceBuilder()
        evidence = builder.build_from_pattern_matches([pm])
        assert len(evidence) == 1
        assert evidence[0].system == "cross_system"

    def test_golden_full_chain_combined_json_deterministic(self):
        rules = parse_rule_file(str(EXAMPLES / "01_single_condition.yaml"))
        engine = RuleEngine()
        evals = engine.evaluate_all(rules, CHART_WITH_SEAL)
        pattern = parse_pattern_file(str(PAT_DIR / "01_single_rule.yaml"))
        matcher = PatternMatcher()
        pm = matcher.match(pattern, evals, "bazi")
        builder = EvidenceBuilder()
        e1 = builder.build_all(evals, [pm], "bazi")
        e2 = builder.build_all(evals, [pm], "bazi")
        j1 = json.dumps([e.model_dump(mode="json") for e in e1], sort_keys=True)
        j2 = json.dumps([e.model_dump(mode="json") for e in e2], sort_keys=True)
        assert j1 == j2


def engine_eval(yaml_name, chart):
    rules = parse_rule_file(str(EXAMPLES / yaml_name))
    engine = RuleEngine()
    return engine.evaluate_all(rules, chart)
