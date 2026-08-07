"""Golden tests for the Reference Conformance Framework (Phase 6B Sprint 5.5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from reference.conformance import (
    ConformanceCategory,
    ConformanceCheckResult,
    ConformanceLayer,
    ConformanceManifest,
    ConformanceResult,
    GoldenVector,
)
from reference.conformance_runner import (
    CONTRACTS_DIR,
    GOLDEN_DIR,
    ConformanceRunner,
    ReferenceAdapter,
    _canonical_json,
    certify,
    generate_golden_vectors,
    load_golden_vectors,
)


@pytest.fixture(scope="module")
def golden_vectors():
    return load_golden_vectors()


@pytest.fixture(scope="module")
def adapter():
    return ReferenceAdapter()


@pytest.fixture(scope="module")
def result(adapter):
    return ConformanceRunner().run(adapter, "reference", "1.0.0")


class TestGoldenVectorModel:
    def test_valid_vector(self):
        gv = GoldenVector(vector_id="v1", layer=ConformanceLayer.RULE, name="test")
        assert gv.vector_id == "v1"
        assert gv.layer == ConformanceLayer.RULE

    def test_default_expected_output_is_none(self):
        gv = GoldenVector(vector_id="v1", layer=ConformanceLayer.RULE, name="t")
        assert gv.expected_output is None

    def test_expected_output_accepts_list(self):
        gv = GoldenVector(
            vector_id="v1", layer=ConformanceLayer.RULE, name="t", expected_output=[1, 2, 3]
        )
        assert gv.expected_output == [1, 2, 3]

    def test_expected_output_accepts_dict(self):
        gv = GoldenVector(
            vector_id="v1", layer=ConformanceLayer.RULE, name="t", expected_output={"a": 1}
        )
        assert gv.expected_output == {"a": 1}

    def test_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            GoldenVector(vector_id="v1", layer=ConformanceLayer.RULE, name="t", extra="bad")


class TestConformanceResultModel:
    def test_defaults(self):
        r = ConformanceResult(runtime_name="x", runtime_version="1.0")
        assert r.passed == 0
        assert r.failed == 0
        assert r.total == 0
        assert r.certified is False
        assert r.coverage == 0.0

    def test_add_check_pass(self):
        r = ConformanceResult(runtime_name="x", runtime_version="1.0")
        r.add_check(
            ConformanceCheckResult(
                check_id="c1", category=ConformanceCategory.GOLDEN_JSON, name="n", passed=True
            )
        )
        assert r.passed == 1
        assert r.failed == 0
        assert r.total == 1
        assert r.certified is True
        assert r.coverage == 1.0

    def test_add_check_fail(self):
        r = ConformanceResult(runtime_name="x", runtime_version="1.0")
        r.add_check(
            ConformanceCheckResult(
                check_id="c1", category=ConformanceCategory.GOLDEN_JSON, name="n", passed=False
            )
        )
        assert r.passed == 0
        assert r.failed == 1
        assert r.certified is False
        assert r.coverage == 0.0

    def test_mixed_checks(self):
        r = ConformanceResult(runtime_name="x", runtime_version="1.0")
        r.add_check(
            ConformanceCheckResult(
                check_id="c1", category=ConformanceCategory.GOLDEN_JSON, name="n", passed=True
            )
        )
        r.add_check(
            ConformanceCheckResult(
                check_id="c2", category=ConformanceCategory.GOLDEN_JSON, name="n2", passed=False
            )
        )
        assert r.passed == 1
        assert r.failed == 1
        assert r.total == 2
        assert r.certified is False
        assert r.coverage == 0.5

    def test_version_defaults(self):
        r = ConformanceResult(runtime_name="x", runtime_version="1.0")
        assert r.contract_version == "1.0.0"
        assert r.behavior_version == "1.0.0"


class TestConformanceManifestModel:
    def test_defaults(self):
        m = ConformanceManifest(runtime_name="x", runtime_version="1.0")
        assert m.supported_layers == []
        assert m.supported_contracts == {}
        assert m.supported_behaviors == []
        assert m.certified is False

    def test_extra_rejected(self):
        with pytest.raises(ValidationError):
            ConformanceManifest(runtime_name="x", runtime_version="1.0", extra=1)


class TestReferenceAdapterRule:
    def test_evaluate_returns_canonical_json(self, adapter):
        rule_yaml = Path("reference/examples/01_single_condition.yaml").read_text(encoding="utf-8")
        chart = {
            "ten_gods_map": {"values": ["伤官", "正印", "比肩"]},
            "day_master_strength": 0.35,
            "shen_sha_list": ["羊刃", "天乙贵人"],
        }
        out = adapter.evaluate_rule(rule_yaml, chart)
        parsed = json.loads(out)
        assert isinstance(parsed, list)
        assert len(parsed) > 0

    def test_evaluate_deterministic(self, adapter):
        rule_yaml = Path("reference/examples/01_single_condition.yaml").read_text(encoding="utf-8")
        chart = {
            "ten_gods_map": {"values": ["伤官"]},
            "day_master_strength": 0.3,
            "shen_sha_list": [],
        }
        a1 = adapter.evaluate_rule(rule_yaml, chart)
        a2 = adapter.evaluate_rule(rule_yaml, chart)
        assert a1 == a2

    def test_evaluate_sorted_keys(self, adapter):
        rule_yaml = Path("reference/examples/01_single_condition.yaml").read_text(encoding="utf-8")
        chart = {
            "ten_gods_map": {"values": ["伤官"]},
            "day_master_strength": 0.3,
            "shen_sha_list": [],
        }
        out = adapter.evaluate_rule(rule_yaml, chart)
        reparsed = json.loads(out)
        assert _canonical_json(reparsed) == out


class TestReferenceAdapterPattern:
    def test_single_system_match(self, adapter):
        gv = next(
            v
            for v in load_golden_vectors()
            if v.layer == ConformanceLayer.PATTERN
            and "cross" not in v.name
            and "no_match" not in v.name
        )
        runner = ConformanceRunner()
        actual = runner._run_adapter(adapter, gv)
        expected = _canonical_json(gv.expected_output)
        assert actual == expected

    def test_cross_system_match(self, adapter):
        gv = next(
            v
            for v in load_golden_vectors()
            if v.layer == ConformanceLayer.PATTERN and "cross" in v.name
        )
        runner = ConformanceRunner()
        actual = runner._run_adapter(adapter, gv)
        expected = _canonical_json(gv.expected_output)
        assert actual == expected

    def test_no_match_returns_null(self, adapter):
        gv = next(
            v
            for v in load_golden_vectors()
            if v.layer == ConformanceLayer.PATTERN and "no_match" in v.name
        )
        runner = ConformanceRunner()
        actual = runner._run_adapter(adapter, gv)
        assert actual == "null"

    def test_pattern_deterministic(self, adapter):
        gv = next(
            v
            for v in load_golden_vectors()
            if v.layer == ConformanceLayer.PATTERN and "cross" not in v.name
        )
        runner = ConformanceRunner()
        a1 = runner._run_adapter(adapter, gv)
        a2 = runner._run_adapter(adapter, gv)
        assert a1 == a2


class TestReferenceAdapterEvidence:
    def test_build_evidence(self, adapter):
        gv = next(v for v in load_golden_vectors() if v.layer == ConformanceLayer.EVIDENCE)
        runner = ConformanceRunner()
        actual = runner._run_adapter(adapter, gv)
        parsed = json.loads(actual)
        assert isinstance(parsed, list)
        assert len(parsed) > 0

    def test_evidence_deterministic(self, adapter):
        gv = next(v for v in load_golden_vectors() if v.layer == ConformanceLayer.EVIDENCE)
        runner = ConformanceRunner()
        a1 = runner._run_adapter(adapter, gv)
        a2 = runner._run_adapter(adapter, gv)
        assert a1 == a2


class TestReferenceAdapterKnowledge:
    def test_query_knowledge(self, adapter):
        gv = next(v for v in load_golden_vectors() if v.layer == ConformanceLayer.KNOWLEDGE)
        runner = ConformanceRunner()
        actual = runner._run_adapter(adapter, gv)
        parsed = json.loads(actual)
        assert isinstance(parsed, dict)

    def test_knowledge_deterministic(self, adapter):
        gv = next(v for v in load_golden_vectors() if v.layer == ConformanceLayer.KNOWLEDGE)
        runner = ConformanceRunner()
        a1 = runner._run_adapter(adapter, gv)
        a2 = runner._run_adapter(adapter, gv)
        assert a1 == a2


class TestReferenceAdapterConsensus:
    @pytest.mark.parametrize("strategy", ["retain_all", "highest_confidence", "majority"])
    def test_build_consensus(self, adapter, strategy):
        gv = next(
            v
            for v in load_golden_vectors()
            if v.layer == ConformanceLayer.CONSENSUS and strategy in v.name
        )
        runner = ConformanceRunner()
        actual = runner._run_adapter(adapter, gv)
        parsed = json.loads(actual)
        assert "overall_confidence" in parsed
        assert "conclusions" in parsed

    def test_consensus_deterministic(self, adapter):
        gv = next(v for v in load_golden_vectors() if v.layer == ConformanceLayer.CONSENSUS)
        runner = ConformanceRunner()
        a1 = runner._run_adapter(adapter, gv)
        a2 = runner._run_adapter(adapter, gv)
        assert a1 == a2


class TestGoldenVectorGeneration:
    def test_vector_count(self, golden_vectors):
        assert len(golden_vectors) >= 19

    def test_all_layers_covered(self, golden_vectors):
        layers = {v.layer for v in golden_vectors}
        assert ConformanceLayer.RULE in layers
        assert ConformanceLayer.PATTERN in layers
        assert ConformanceLayer.EVIDENCE in layers
        assert ConformanceLayer.KNOWLEDGE in layers
        assert ConformanceLayer.CONSENSUS in layers

    def test_unique_vector_ids(self, golden_vectors):
        ids = [v.vector_id for v in golden_vectors]
        assert len(ids) == len(set(ids))

    def test_auto_discovered_from_disk(self):
        files = list(GOLDEN_DIR.glob("*_vectors.json"))
        assert len(files) == 5

    def test_regenerate_matches_loaded(self):
        fresh = generate_golden_vectors()
        loaded = load_golden_vectors()
        assert len(fresh) == len(loaded)
        fresh_map = {v.vector_id: v for v in fresh}
        loaded_map = {v.vector_id: v for v in loaded}
        assert set(fresh_map) == set(loaded_map)
        for vid in fresh_map:
            assert fresh_map[vid].expected_output == loaded_map[vid].expected_output


class TestConformanceRunner:
    def test_all_pass(self, result):
        assert result.failed == 0

    def test_total_checks_positive(self, result):
        assert result.total > 0

    def test_certified(self, result):
        assert result.certified is True

    def test_full_coverage(self, result):
        assert result.coverage == 1.0

    def test_contract_version(self, result):
        assert result.contract_version == "1.0.0"

    def test_runtime_name(self, result):
        assert result.runtime_name == "reference"
        assert result.runtime_version == "1.0.0"


class TestDeterminism:
    def test_same_input_same_output(self, adapter, golden_vectors):
        runner = ConformanceRunner()
        gv = golden_vectors[0]
        a1 = runner._run_adapter(adapter, gv)
        a2 = runner._run_adapter(adapter, gv)
        assert a1 == a2

    def test_all_golden_match(self, adapter, golden_vectors):
        runner = ConformanceRunner()
        for gv in golden_vectors:
            actual = runner._run_adapter(adapter, gv)
            expected = _canonical_json(gv.expected_output)
            assert actual == expected, f"Mismatch: {gv.vector_id}"


class TestContractDiff:
    def test_contracts_exist(self):
        files = sorted(CONTRACTS_DIR.glob("*.json"))
        assert len(files) >= 3

    def test_contracts_valid_structure(self):
        for cf in CONTRACTS_DIR.glob("*.json"):
            data = json.loads(cf.read_text(encoding="utf-8"))
            assert "contract_version" in data
            assert "golden_examples" in data


class TestArchitectureBoundary:
    def test_no_forbidden_methods(self, adapter):
        forbidden = [
            "call_llm",
            "query_database",
            "call_graph_db",
            "embed",
            "rag_search",
            "call_ollama",
        ]
        for m in forbidden:
            assert not hasattr(adapter, m)

    def test_boundary_check_passes(self, result):
        arch_checks = [
            c for c in result.checks if c.category == ConformanceCategory.ARCHITECTURE_BOUNDARY
        ]
        assert len(arch_checks) > 0
        assert all(c.passed for c in arch_checks)


class TestCertification:
    def test_certify_returns_manifest(self, result):
        m = certify(result)
        assert isinstance(m, ConformanceManifest)

    def test_certified_manifest(self, result):
        m = certify(result)
        assert m.certified is True

    def test_supported_layers_populated(self, result):
        m = certify(result)
        assert len(m.supported_layers) == 5


class TestConformanceRules:
    def test_golden_json_checks_present(self, result):
        cats = {c.category for c in result.checks}
        assert ConformanceCategory.GOLDEN_JSON in cats

    def test_deterministic_checks_present(self, result):
        cats = {c.category for c in result.checks}
        assert ConformanceCategory.DETERMINISTIC_OUTPUT in cats

    def test_stable_ordering_checks_present(self, result):
        cats = {c.category for c in result.checks}
        assert ConformanceCategory.STABLE_ORDERING in cats

    def test_contract_diff_checks_present(self, result):
        cats = {c.category for c in result.checks}
        assert ConformanceCategory.CONTRACT_DIFF in cats

    def test_behavior_coverage_checks_present(self, result):
        cats = {c.category for c in result.checks}
        assert ConformanceCategory.BEHAVIOR_COVERAGE in cats

    def test_architecture_boundary_present(self, result):
        cats = {c.category for c in result.checks}
        assert ConformanceCategory.ARCHITECTURE_BOUNDARY in cats

    def test_null_handling_checks_present(self, result):
        cats = {c.category for c in result.checks}
        assert ConformanceCategory.NULL_HANDLING in cats

    def test_result_json_serializable(self, result):
        data = result.model_dump(mode="json")
        assert "checks" in data
        assert "certified" in data
        json.dumps(data, ensure_ascii=False, sort_keys=True)

    def test_manifest_json_serializable(self, result):
        m = certify(result)
        data = m.model_dump(mode="json")
        json.dumps(data, ensure_ascii=False, sort_keys=True)

    def test_all_checks_pass(self, result):
        for c in result.checks:
            assert c.passed, f"Failed: {c.check_id} - {c.message}"
