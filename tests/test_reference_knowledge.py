"""Golden tests for the Reference Knowledge Layer (Phase 6B Sprint 4).

Validates the chain: KnowledgeNode / KnowledgeRelation / KnowledgeReference
-> KnowledgeStore -> KnowledgeQuery -> KnowledgeResult -> JSON.

Tests cover:
  - Node / Relation / Reference validation
  - In-memory query behavior (find_by_id/type/system/tag/relation/reference)
  - Stable sorting (deterministic output)
  - Null handling (unknown node -> None)
  - Duplicate node / relation rejection
  - Deterministic output and JSON stability
  - Auto-generated Knowledge Contract
  - Behavior Contract verification (KB-001 ~ KB-020)
  - Architecture boundary (no reasoning, no conclusions)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from reference.knowledge import (
    KnowledgeNode,
    KnowledgeReference,
    KnowledgeRelation,
    NodeType,
    ReferenceTarget,
    ReferenceType,
    RelationDirection,
    RelationEvidence,
    RelationType,
    SchoolView,
    parse_nodes_file,
    parse_references_file,
    parse_relations_file,
)
from reference.knowledge_behavior import KnowledgeBehavior
from reference.knowledge_query import (
    KNOWLEDGE_CONTRACT_PATH,
    KnowledgeQuery,
    KnowledgeQueryType,
    KnowledgeStore,
    export_knowledge_contract,
    load_knowledge_store,
)
from reference.models import MetaphysicsSystem, SourceRef

EXAMPLES = Path(__file__).parent.parent / "reference" / "examples" / "knowledge"


# == Helpers ==


def _src(text="测试典籍", credibility=0.85):
    return SourceRef(text=text, credibility=credibility)


def _make_node(
    node_id="kn:test:node",
    node_type=NodeType.WUXING,
    name_cn="测试",
    name_en="test",
    systems=None,
    source=None,
    interpretation="测试解释",
    tags=None,
    confidence=0.9,
    schools=None,
    attributes=None,
):
    return KnowledgeNode(
        id=node_id,
        node_type=node_type,
        name_cn=name_cn,
        name_en=name_en,
        systems=systems or [MetaphysicsSystem.BAZI],
        source=source or _src(),
        interpretation=interpretation,
        tags=tags or [],
        confidence=confidence,
        schools=schools or [],
        attributes=attributes or {},
    )


def _make_relation(
    rel_id="rel:test:a:b:v1",
    source_node_id="kn:test:a",
    target_node_id="kn:test:b",
    relation_type=RelationType.SHENG,
    direction=RelationDirection.DIRECTED,
    weight=1.0,
    source=None,
    evidence=None,
):
    return KnowledgeRelation(
        id=rel_id,
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        relation_type=relation_type,
        direction=direction,
        weight=weight,
        source=source or _src(),
        evidence=evidence or [],
    )


def _make_reference(
    ref_id="ref:test:ref1",
    target_type=ReferenceTarget.NODE,
    target_id="kn:test:node",
    ref_type=ReferenceType.CLASSIC_TEXT,
    source=None,
    passage="测试引用",
    school=None,
    credibility=0.9,
):
    return KnowledgeReference(
        reference_id=ref_id,
        target_type=target_type,
        target_id=target_id,
        ref_type=ref_type,
        source=source or _src(),
        passage=passage,
        school=school,
        credibility=credibility,
    )


def _load_store():
    return load_knowledge_store(
        nodes_path=EXAMPLES / "nodes.yaml",
        relations_path=EXAMPLES / "relations.yaml",
        references_path=EXAMPLES / "references.yaml",
    )


# ==================================================================
# Node Validation
# ==================================================================


class TestKnowledgeNodeValidation:
    def test_node_valid_full(self):
        node = _make_node(
            node_id="kn:wuxing:mu",
            node_type=NodeType.WUXING,
            name_cn="木",
            name_en="wood",
            systems=[MetaphysicsSystem.BAZI, MetaphysicsSystem.ZIWEI],
            tags=["阳", "东方"],
            confidence=1.0,
        )
        assert node.id == "kn:wuxing:mu"
        assert node.node_type == NodeType.WUXING
        assert len(node.systems) == 2
        assert node.confidence == 1.0

    def test_node_invalid_id_format(self):
        with pytest.raises(ValidationError):
            _make_node(node_id="invalid_id")

    def test_node_empty_systems_rejected(self):
        with pytest.raises(ValidationError):
            KnowledgeNode(
                id="kn:test:empty",
                node_type=NodeType.WUXING,
                name_cn="测试",
                name_en="test",
                systems=[],
                source=_src(),
                interpretation="测试",
                confidence=0.9,
            )

    def test_node_confidence_out_of_range(self):
        with pytest.raises(ValidationError):
            _make_node(confidence=1.5)
        with pytest.raises(ValidationError):
            _make_node(confidence=-0.1)

    def test_node_extra_fields_rejected(self):
        with pytest.raises(ValidationError):
            KnowledgeNode(
                id="kn:test:x",
                node_type=NodeType.WUXING,
                name_cn="测试",
                name_en="test",
                systems=[MetaphysicsSystem.BAZI],
                source=_src(),
                interpretation="测试",
                confidence=0.9,
                extra_field="forbidden",
            )

    def test_node_all_node_types_valid(self):
        for nt in NodeType:
            node = _make_node(
                node_id=f"kn:{nt.value}:test",
                node_type=nt,
            )
            assert node.node_type == nt

    def test_node_schools_multiple(self):
        schools = [
            SchoolView(school="子平", interpretation="解释A", source=_src("书A"), weight=1.0),
            SchoolView(school="盲派", interpretation="解释B", source=_src("书B"), weight=0.8),
        ]
        node = _make_node(schools=schools)
        assert len(node.schools) == 2
        assert node.schools[0].school == "子平"
        assert node.schools[1].weight == 0.8

    def test_node_yaml_parsing(self):
        nodes = parse_nodes_file(str(EXAMPLES / "nodes.yaml"))
        assert len(nodes) == 10
        assert nodes[0].id == "kn:wuxing:mu"
        mu = [n for n in nodes if n.id == "kn:wuxing:mu"][0]
        assert mu.name_cn == "木"
        assert mu.node_type == NodeType.WUXING
        assert len(mu.schools) == 1


# ==================================================================
# Relation Validation
# ==================================================================


class TestKnowledgeRelationValidation:
    def test_relation_valid(self):
        rel = _make_relation()
        assert rel.id == "rel:test:a:b:v1"
        assert rel.relation_type == RelationType.SHENG
        assert rel.direction == RelationDirection.DIRECTED

    def test_relation_invalid_id_format(self):
        with pytest.raises(ValidationError):
            _make_relation(rel_id="invalid_rel_id")

    def test_relation_all_relation_types(self):
        for rt in RelationType:
            rel = _make_relation(relation_type=rt)
            assert rel.relation_type == rt

    def test_relation_direction_values(self):
        for d in RelationDirection:
            rel = _make_relation(direction=d)
            assert rel.direction == d

    def test_relation_weight_bounds(self):
        with pytest.raises(ValidationError):
            _make_relation(weight=1.5)
        with pytest.raises(ValidationError):
            _make_relation(weight=-0.1)

    def test_relation_yaml_parsing(self):
        rels = parse_relations_file(str(EXAMPLES / "relations.yaml"))
        assert len(rels) == 7
        sheng_rels = [r for r in rels if r.relation_type == RelationType.SHENG]
        assert len(sheng_rels) == 5
        assert rels[0].source_node_id == "kn:wuxing:mu"

    def test_relation_with_evidence(self):
        ev = RelationEvidence(
            description="测试证据",
            source=_src("测试书"),
            weight=0.9,
        )
        rel = _make_relation(evidence=[ev])
        assert len(rel.evidence) == 1
        assert rel.evidence[0].description == "测试证据"


# ==================================================================
# Reference Validation
# ==================================================================


class TestKnowledgeReferenceValidation:
    def test_reference_valid(self):
        ref = _make_reference()
        assert ref.reference_id == "ref:test:ref1"
        assert ref.ref_type == ReferenceType.CLASSIC_TEXT
        assert ref.target_type == ReferenceTarget.NODE

    def test_reference_invalid_id_format(self):
        with pytest.raises(ValidationError):
            _make_reference(ref_id="invalid_ref_id")

    def test_reference_all_ref_types(self):
        for rt in ReferenceType:
            ref = _make_reference(ref_type=rt)
            assert ref.ref_type == rt

    def test_reference_target_types(self):
        ref_node = _make_reference(target_type=ReferenceTarget.NODE)
        ref_rel = _make_reference(target_type=ReferenceTarget.RELATION)
        assert ref_node.target_type == ReferenceTarget.NODE
        assert ref_rel.target_type == ReferenceTarget.RELATION

    def test_reference_yaml_parsing(self):
        refs = parse_references_file(str(EXAMPLES / "references.yaml"))
        assert len(refs) == 6
        classic = [r for r in refs if r.ref_type == ReferenceType.CLASSIC_TEXT]
        assert len(classic) == 4
        school = [r for r in refs if r.ref_type == ReferenceType.SCHOOL_COMMENTARY]
        assert len(school) == 2

    def test_reference_with_school(self):
        ref = _make_reference(
            ref_type=ReferenceType.SCHOOL_COMMENTARY,
            school="子平",
        )
        assert ref.school == "子平"


# ==================================================================
# Memory Query
# ==================================================================


class TestMemoryQuery:
    def setup_method(self):
        self.store = _load_store()

    def test_find_by_id_found(self):
        node = self.store.find_by_id("kn:wuxing:mu")
        assert node is not None
        assert node.name_cn == "木"
        assert node.node_type == NodeType.WUXING

    def test_find_by_id_not_found(self):
        """KB-012: Unknown node returns None, not exception."""
        node = self.store.find_by_id("kn:unknown:nonexistent")
        assert node is None

    def test_find_by_type(self):
        wuxing = self.store.find_by_type(NodeType.WUXING)
        assert len(wuxing) == 5
        for n in wuxing:
            assert n.node_type == NodeType.WUXING

    def test_find_by_system(self):
        bazi = self.store.find_by_system("bazi")
        assert len(bazi) == 10
        ziwei = self.store.find_by_system("ziwei")
        assert len(ziwei) == 7
        meihua = self.store.find_by_system("meihua")
        assert len(meihua) == 0

    def test_find_by_tag(self):
        yang = self.store.find_by_tag("阳")
        assert len(yang) == 2
        nonexistent = self.store.find_by_tag("nonexistent_tag")
        assert len(nonexistent) == 0

    def test_find_relation_all(self):
        mu_rels = self.store.find_relation("kn:wuxing:mu")
        assert len(mu_rels) == 3

    def test_find_relation_by_type(self):
        sheng = self.store.find_relation("kn:wuxing:mu", relation_type=RelationType.SHENG)
        assert len(sheng) == 2
        ke = self.store.find_relation("kn:wuxing:mu", relation_type=RelationType.KE)
        assert len(ke) == 1

    def test_find_reference(self):
        mu_refs = self.store.find_reference("kn:wuxing:mu")
        assert len(mu_refs) == 1
        assert mu_refs[0].ref_type == ReferenceType.CLASSIC_TEXT

    def test_find_reference_relation_target(self):
        rel_refs = self.store.find_reference("rel:wuxing:mu:sheng:huo:v1")
        assert len(rel_refs) == 1
        assert rel_refs[0].target_type == ReferenceTarget.RELATION

    def test_find_reference_not_found(self):
        refs = self.store.find_reference("kn:nonexistent:node")
        assert refs == []


# ==================================================================
# Sorting (deterministic output)
# ==================================================================


class TestSorting:
    def setup_method(self):
        self.store = _load_store()

    def test_find_by_type_sorted(self):
        """KB-013: find_by_type returns sorted list."""
        wuxing = self.store.find_by_type(NodeType.WUXING)
        ids = [n.id for n in wuxing]
        assert ids == sorted(ids)

    def test_find_by_system_sorted(self):
        """KB-014: find_by_system returns sorted list."""
        bazi = self.store.find_by_system("bazi")
        ids = [n.id for n in bazi]
        assert ids == sorted(ids)

    def test_find_by_tag_sorted(self):
        """KB-015: find_by_tag returns sorted list."""
        yang = self.store.find_by_tag("阳")
        ids = [n.id for n in yang]
        assert ids == sorted(ids)

    def test_find_relation_sorted(self):
        """KB-016: find_relation returns sorted list."""
        mu_rels = self.store.find_relation("kn:wuxing:mu")
        ids = [r.id for r in mu_rels]
        assert ids == sorted(ids)

    def test_find_reference_sorted(self):
        """KB-017: find_reference returns sorted list."""
        all_refs = self.store.all_references()
        ids = [r.reference_id for r in all_refs]
        assert ids == sorted(ids)

    def test_all_nodes_sorted(self):
        nodes = self.store.all_nodes()
        ids = [n.id for n in nodes]
        assert ids == sorted(ids)


# ==================================================================
# Deterministic Output
# ==================================================================


class TestDeterminism:
    def setup_method(self):
        self.store = _load_store()

    def test_deterministic_find_by_id(self):
        """KB-019: Same query produces identical output."""
        n1 = self.store.find_by_id("kn:wuxing:mu")
        n2 = self.store.find_by_id("kn:wuxing:mu")
        assert n1.model_dump_json() == n2.model_dump_json()

    def test_deterministic_find_by_type(self):
        l1 = self.store.find_by_type(NodeType.WUXING)
        l2 = self.store.find_by_type(NodeType.WUXING)
        assert [n.model_dump_json() for n in l1] == [n.model_dump_json() for n in l2]

    def test_deterministic_execute(self):
        q = KnowledgeQuery(
            query_type=KnowledgeQueryType.FIND_BY_SYSTEM,
            system="bazi",
        )
        r1 = self.store.execute(q)
        r2 = self.store.execute(q)
        assert r1.model_dump_json() == r2.model_dump_json()

    def test_deterministic_json_stability(self):
        """KB-020: JSON serialization is stable."""
        q = KnowledgeQuery(
            query_type=KnowledgeQueryType.FIND_BY_TYPE,
            node_type=NodeType.WUXING,
        )
        result = self.store.execute(q)
        j1 = result.model_dump_json()
        j2 = result.model_dump_json()
        assert j1 == j2

    def test_behavior_verify_determinism(self):
        q = KnowledgeQuery(
            query_type=KnowledgeQueryType.FIND_BY_ID,
            node_id="kn:wuxing:mu",
        )
        assert KnowledgeBehavior.verify_determinism(self.store, q)


# ==================================================================
# Duplicate Handling
# ==================================================================


class TestDuplicateHandling:
    def test_duplicate_node_rejected(self):
        """KB-018: Duplicate node ID is rejected."""
        store = KnowledgeStore()
        node = _make_node(node_id="kn:test:dup")
        store.add_node(node)
        dup = _make_node(node_id="kn:test:dup")
        with pytest.raises(ValueError, match="Duplicate node ID"):
            store.add_node(dup)

    def test_duplicate_relation_rejected(self):
        store = KnowledgeStore()
        rel = _make_relation(rel_id="rel:test:dup:v1")
        store.add_relation(rel)
        dup = _make_relation(rel_id="rel:test:dup:v1")
        with pytest.raises(ValueError, match="Duplicate relation ID"):
            store.add_relation(dup)

    def test_duplicate_reference_rejected(self):
        store = KnowledgeStore()
        ref = _make_reference(ref_id="ref:test:dup")
        store.add_reference(ref)
        dup = _make_reference(ref_id="ref:test:dup")
        with pytest.raises(ValueError, match="Duplicate reference ID"):
            store.add_reference(dup)

    def test_behavior_verify_duplicate_rejected(self):
        store = KnowledgeStore()
        node = _make_node(node_id="kn:test:bdup")
        store.add_node(node)
        dup = _make_node(node_id="kn:test:bdup")
        assert KnowledgeBehavior.verify_duplicate_node_rejected(store, dup)


# ==================================================================
# KnowledgeResult
# ==================================================================


class TestKnowledgeResult:
    def setup_method(self):
        self.store = _load_store()

    def test_result_contains_all_fields(self):
        q = KnowledgeQuery(query_type=KnowledgeQueryType.FIND_BY_TYPE, node_type=NodeType.WUXING)
        result = self.store.execute(q)
        j = json.loads(result.model_dump_json())
        assert "query_type" in j
        assert "found" in j
        assert "nodes" in j
        assert "relations" in j
        assert "references" in j
        assert "metadata" in j
        assert "version" in j

    def test_result_metadata(self):
        q = KnowledgeQuery(query_type=KnowledgeQueryType.FIND_BY_TYPE, node_type=NodeType.WUXING)
        result = self.store.execute(q)
        assert result.metadata["total"] == 5
        assert result.metadata["query_type"] == "find_by_type"
        assert result.metadata["node_type"] == "wuxing"

    def test_result_empty_lists_for_no_match(self):
        q = KnowledgeQuery(query_type=KnowledgeQueryType.FIND_BY_TAG, tag="nonexistent")
        result = self.store.execute(q)
        assert result.nodes == []
        assert result.relations == []
        assert result.references == []
        assert result.found is False

    def test_result_found_true_when_match(self):
        q = KnowledgeQuery(query_type=KnowledgeQueryType.FIND_BY_ID, node_id="kn:wuxing:mu")
        result = self.store.execute(q)
        assert result.found is True
        assert len(result.nodes) == 1


# ==================================================================
# KnowledgeQuery Execute
# ==================================================================


class TestKnowledgeQueryExecute:
    def setup_method(self):
        self.store = _load_store()

    def test_execute_find_by_id(self):
        q = KnowledgeQuery(query_type=KnowledgeQueryType.FIND_BY_ID, node_id="kn:wuxing:huo")
        result = self.store.execute(q)
        assert result.found is True
        assert result.nodes[0].name_cn == "火"

    def test_execute_find_by_system(self):
        q = KnowledgeQuery(query_type=KnowledgeQueryType.FIND_BY_SYSTEM, system="ziwei")
        result = self.store.execute(q)
        assert result.metadata["total"] == 7

    def test_execute_find_relation(self):
        q = KnowledgeQuery(
            query_type=KnowledgeQueryType.FIND_RELATION,
            node_id="kn:wuxing:mu",
            relation_type=RelationType.KE,
        )
        result = self.store.execute(q)
        assert result.found is True
        assert len(result.relations) == 1
        assert result.relations[0].relation_type == RelationType.KE

    def test_execute_find_reference(self):
        q = KnowledgeQuery(
            query_type=KnowledgeQueryType.FIND_REFERENCE,
            target_id="kn:ten_god:shang_guan",
        )
        result = self.store.execute(q)
        assert result.found is True
        assert len(result.references) == 1
        assert result.references[0].ref_type == ReferenceType.SCHOOL_COMMENTARY


# ==================================================================
# Contract
# ==================================================================


class TestContract:
    def test_contract_structure(self):
        contract = export_knowledge_contract()
        assert contract["contract_name"] == "knowledge"
        assert contract["contract_version"] == "1.0.0"
        assert "models" in contract
        assert "KnowledgeNode" in contract["models"]
        assert "KnowledgeRelation" in contract["models"]
        assert "KnowledgeReference" in contract["models"]
        assert "KnowledgeResult" in contract["models"]
        assert "golden_examples" in contract

    def test_contract_golden_examples(self):
        contract = export_knowledge_contract()
        examples = contract["golden_examples"]
        assert len(examples) >= 7
        for ex in examples:
            assert "name" in ex
            assert "query" in ex
            assert "result" in ex

    def test_contract_determinism(self):
        c1 = export_knowledge_contract()
        c2 = export_knowledge_contract()
        assert c1 == c2
        assert json.dumps(c1, sort_keys=True) == json.dumps(c2, sort_keys=True)

    def test_contract_file_matches_runtime(self):
        with open(KNOWLEDGE_CONTRACT_PATH, encoding="utf-8") as f:
            file_contract = json.load(f)
        runtime_contract = export_knowledge_contract()
        assert file_contract == runtime_contract

    def test_contract_node_types_complete(self):
        contract = export_knowledge_contract()
        assert len(contract["node_types"]) == 20
        assert len(contract["relation_types"]) == 15
        assert len(contract["reference_types"]) == 4
        assert len(contract["query_types"]) == 6


# ==================================================================
# Behavior Verification
# ==================================================================


class TestBehaviorVerification:
    def setup_method(self):
        self.store = _load_store()

    def test_verify_sorting(self):
        result = self.store.execute(
            KnowledgeQuery(
                query_type=KnowledgeQueryType.FIND_BY_TYPE,
                node_type=NodeType.WUXING,
            )
        )
        assert KnowledgeBehavior.verify_result_sorting(result)

    def test_verify_null_handling(self):
        assert KnowledgeBehavior.verify_null_handling(self.store, "kn:nonexistent:x")

    def test_verify_no_reasoning_methods(self):
        assert KnowledgeBehavior.verify_no_reasoning_methods()

    def test_verify_node_no_conclusion_field(self):
        assert KnowledgeBehavior.verify_node_no_conclusion_field()

    def test_verify_confidence_unchanged(self):
        assert KnowledgeBehavior.verify_knowledge_does_not_increase_confidence(
            self.store,
            "kn:wuxing:mu",
        )

    def test_full_audit(self):
        audit = KnowledgeBehavior.audit(self.store)
        for key, value in audit.items():
            assert value is True, f"Audit failed for {key}"


# ==================================================================
# Architecture Boundary
# ==================================================================


class TestArchitectureBoundary:
    def test_store_has_no_reasoning_methods(self):
        forbidden = [
            "reason",
            "conclude",
            "evaluate",
            "infer",
            "generate_conclusion",
            "modify_evidence",
            "increase_confidence",
            "call_rule",
        ]
        for name in forbidden:
            assert not hasattr(KnowledgeStore, name), f"KnowledgeStore has forbidden method: {name}"

    def test_node_has_no_conclusion_field(self):
        assert not hasattr(KnowledgeNode, "conclusion")
        assert not hasattr(KnowledgeNode, "direction")
        assert not hasattr(KnowledgeNode, "weight")

    def test_store_is_read_only_after_build(self):
        """Queries do not modify store state."""
        store = _load_store()
        count_before = store.node_count
        store.find_by_id("kn:wuxing:mu")
        store.find_by_type(NodeType.WUXING)
        store.find_by_system("bazi")
        store.find_by_tag("阳")
        store.find_relation("kn:wuxing:mu")
        store.find_reference("kn:wuxing:mu")
        assert store.node_count == count_before


# ==================================================================
# JSON Serialization
# ==================================================================


class TestJSONSerialization:
    def setup_method(self):
        self.store = _load_store()

    def test_node_json_roundtrip(self):
        node = self.store.find_by_id("kn:wuxing:mu")
        j = node.model_dump_json()
        node2 = KnowledgeNode.model_validate_json(j)
        assert node2.id == node.id
        assert node2.name_cn == node.name_cn

    def test_result_json_roundtrip(self):
        q = KnowledgeQuery(query_type=KnowledgeQueryType.FIND_BY_TYPE, node_type=NodeType.WUXING)
        result = self.store.execute(q)
        j = result.model_dump_json()
        assert '"nodes"' in j
        assert '"metadata"' in j
        assert '"version"' in j

    def test_null_fields_serialized(self):
        """Null fields are serialized as JSON null, not omitted."""
        ref = _make_reference(school=None)
        j = json.loads(ref.model_dump_json())
        assert j["school"] is None
