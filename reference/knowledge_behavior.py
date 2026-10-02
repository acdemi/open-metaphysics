"""Reference Knowledge Behavior -- Phase 6B Sprint 4.

Provides behavior verification utilities for the Knowledge Layer.
Used by Golden Tests and CI to verify that the KnowledgeStore
satisfies all 20 Behavior Contracts (KB-001 through KB-020).

Architecture Boundary:
  KnowledgeBehavior verifies that Knowledge remains a READ-ONLY
  citation/reference provider. It does NOT add reasoning, conclusion
  generation, Evidence modification, or Confidence manipulation.

See: docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md
"""

from __future__ import annotations

from pydantic import ValidationError

from .knowledge import KnowledgeNode, KnowledgeReference, KnowledgeRelation
from .knowledge_query import (
    KnowledgeQuery,
    KnowledgeQueryType,
    KnowledgeResult,
    KnowledgeStore,
)


class KnowledgeBehavior:
    """Verifies Knowledge Layer behavior contracts (KB-001 ~ KB-020).

    All methods are static and return bool or raise on violation.
    Used by tests and CI to enforce behavior contracts.
    """

    CONTRACT_VERSION = "1.0.0"

    # == Determinism Verification ==

    @staticmethod
    def verify_determinism(
        store: KnowledgeStore,
        query: KnowledgeQuery,
    ) -> bool:
        """KB-019: Same query produces identical output.

        Runs the query twice and compares JSON output byte-for-byte.
        """
        r1 = store.execute(query)
        r2 = store.execute(query)
        return r1.model_dump_json() == r2.model_dump_json()

    @staticmethod
    def verify_json_stability(result: KnowledgeResult) -> bool:
        """KB-020: JSON serialization is stable across repeated calls.

        Serializes the same result twice and compares.
        """
        j1 = result.model_dump_json()
        j2 = result.model_dump_json()
        return j1 == j2

    # == Sorting Verification ==

    @staticmethod
    def verify_node_sorting(nodes: list[KnowledgeNode]) -> bool:
        """KB-013~015: Node list is sorted by ID."""
        ids = [n.id for n in nodes]
        return ids == sorted(ids)

    @staticmethod
    def verify_relation_sorting(relations: list[KnowledgeRelation]) -> bool:
        """KB-016: Relation list is sorted by ID."""
        ids = [r.id for r in relations]
        return ids == sorted(ids)

    @staticmethod
    def verify_reference_sorting(references: list[KnowledgeReference]) -> bool:
        """KB-017: Reference list is sorted by reference_id."""
        ids = [r.reference_id for r in references]
        return ids == sorted(ids)

    @staticmethod
    def verify_result_sorting(result: KnowledgeResult) -> bool:
        """Verify all lists in a KnowledgeResult are sorted."""
        return (
            KnowledgeBehavior.verify_node_sorting(result.nodes)
            and KnowledgeBehavior.verify_relation_sorting(result.relations)
            and KnowledgeBehavior.verify_reference_sorting(result.references)
        )

    # == Null Handling Verification ==

    @staticmethod
    def verify_null_handling(store: KnowledgeStore, unknown_id: str) -> bool:
        """KB-012: Unknown node returns None, not an exception."""
        try:
            result = store.find_by_id(unknown_id)
        except Exception:
            return False
        return result is None

    # == Duplicate Handling Verification ==

    @staticmethod
    def verify_duplicate_node_rejected(
        store: KnowledgeStore,
        duplicate_node: KnowledgeNode,
    ) -> bool:
        """KB-018: Duplicate node ID is rejected with ValueError."""
        try:
            store.add_node(duplicate_node)
        except ValueError:
            return True
        return False

    @staticmethod
    def verify_duplicate_relation_rejected(
        store: KnowledgeStore,
        duplicate_relation: KnowledgeRelation,
    ) -> bool:
        """KB-019-relation: Duplicate relation ID is rejected with ValueError."""
        try:
            store.add_relation(duplicate_relation)
        except ValueError:
            return True
        return False

    @staticmethod
    def verify_duplicate_reference_rejected(
        store: KnowledgeStore,
        duplicate_reference: KnowledgeReference,
    ) -> bool:
        """Duplicate reference ID is rejected with ValueError."""
        try:
            store.add_reference(duplicate_reference)
        except ValueError:
            return True
        return False

    # == Architecture Boundary Verification ==

    @staticmethod
    def verify_no_reasoning_methods() -> bool:
        """Architecture Boundary: KnowledgeStore has no reasoning methods.

        Verifies that KnowledgeStore does not expose methods that would
        allow it to participate in reasoning, generate conclusions,
        modify Evidence, increase Confidence, or call Rule.
        """
        forbidden = [
            "reason",
            "conclude",
            "evaluate",
            "infer",
            "generate_conclusion",
            "modify_evidence",
            "increase_confidence",
            "call_rule",
            "run_rule",
            "evaluate_rule",
            "match_pattern",
        ]
        for method_name in forbidden:
            if hasattr(KnowledgeStore, method_name):
                return False
        return True

    @staticmethod
    def verify_node_no_conclusion_field() -> bool:
        """Architecture Boundary: KnowledgeNode has no 'conclusion' field.

        Knowledge nodes provide interpretations, not conclusions.
        """
        return not hasattr(KnowledgeNode, "conclusion")

    @staticmethod
    def verify_knowledge_does_not_increase_confidence(
        store: KnowledgeStore,
        node_id: str,
    ) -> bool:
        """Architecture Boundary: Querying a node does not change its confidence.

        The node's confidence before and after a query must be identical.
        """
        node = store.find_by_id(node_id)
        if node is None:
            return True
        confidence_before = node.confidence
        store.find_by_id(node_id)
        store.find_by_type(node.node_type)
        node_after = store.find_by_id(node_id)
        if node_after is None:
            return False
        return confidence_before == node_after.confidence

    # == Schema / Validation Verification (KB-001 ~ KB-011) ==
    #
    # Phase 7.4 (ACP-REF-001 Option A): these contracts previously had NO
    # verifier at all, yet CF-015 lists them as required coverage. Each
    # verifier below asserts BOTH that a valid payload is accepted (positive
    # control, so the check cannot pass vacuously) AND that the specific
    # violation is rejected.

    @staticmethod
    def _valid_node_payload() -> dict:
        return {
            "id": "kn:wuxing:mu",
            "node_type": "wuxing",
            "name_cn": "木",
            "name_en": "wood",
            "systems": ["ziwei"],
            "source": {"text": "probe"},
            "interpretation": "probe",
            "confidence": 0.5,
        }

    @staticmethod
    def _valid_relation_payload() -> dict:
        return {
            "id": "rel:sheng:probe",
            "source_node_id": "kn:wuxing:mu",
            "target_node_id": "kn:wuxing:huo",
            "relation_type": "sheng",
            "source": {"text": "probe"},
        }

    @staticmethod
    def _valid_reference_payload() -> dict:
        return {
            "reference_id": "ref:classic:probe",
            "target_type": "node",
            "target_id": "kn:wuxing:mu",
            "ref_type": "classic_text",
            "source": {"text": "probe"},
        }

    @staticmethod
    def _is_rejected(model: type, payload: dict) -> bool:
        """True iff constructing ``model`` from ``payload`` raises ValidationError."""
        try:
            model(**payload)
        except ValidationError:
            return True
        except Exception:
            return False
        return False

    @staticmethod
    def verify_kb_001_node_id_format() -> bool:
        """KB-001: node id MUST match ^kn:[a-z_]+:[a-z_0-9]+$."""
        from .knowledge import KnowledgeNode

        base = KnowledgeBehavior._valid_node_payload()
        valid = not KnowledgeBehavior._is_rejected(KnowledgeNode, base)
        return valid and KnowledgeBehavior._is_rejected(KnowledgeNode, {**base, "id": "wuxing:mu"})

    @staticmethod
    def verify_kb_002_node_type() -> bool:
        """KB-002: node_type MUST be one of the 20 NodeType values."""
        from .knowledge import KnowledgeNode

        base = KnowledgeBehavior._valid_node_payload()
        valid = not KnowledgeBehavior._is_rejected(KnowledgeNode, base)
        return valid and KnowledgeBehavior._is_rejected(
            KnowledgeNode, {**base, "node_type": "not_a_node_type"}
        )

    @staticmethod
    def verify_kb_003_systems_non_empty() -> bool:
        """KB-003: systems MUST have at least one element."""
        from .knowledge import KnowledgeNode

        base = KnowledgeBehavior._valid_node_payload()
        valid = not KnowledgeBehavior._is_rejected(KnowledgeNode, base)
        return valid and KnowledgeBehavior._is_rejected(KnowledgeNode, {**base, "systems": []})

    @staticmethod
    def verify_kb_004_confidence_bounds() -> bool:
        """KB-004: confidence MUST be within [0.0, 1.0]."""
        from .knowledge import KnowledgeNode

        base = KnowledgeBehavior._valid_node_payload()
        valid = not KnowledgeBehavior._is_rejected(KnowledgeNode, base)
        return (
            valid
            and KnowledgeBehavior._is_rejected(KnowledgeNode, {**base, "confidence": 1.5})
            and KnowledgeBehavior._is_rejected(KnowledgeNode, {**base, "confidence": -0.1})
            and not KnowledgeBehavior._is_rejected(KnowledgeNode, {**base, "confidence": 0.0})
            and not KnowledgeBehavior._is_rejected(KnowledgeNode, {**base, "confidence": 1.0})
        )

    @staticmethod
    def verify_kb_005_extra_fields_rejected() -> bool:
        """KB-005: KnowledgeNode MUST reject unknown fields (extra='forbid')."""
        from .knowledge import KnowledgeNode

        base = KnowledgeBehavior._valid_node_payload()
        valid = not KnowledgeBehavior._is_rejected(KnowledgeNode, base)
        return valid and KnowledgeBehavior._is_rejected(
            KnowledgeNode, {**base, "unexpected_field": 1}
        )

    @staticmethod
    def verify_kb_006_relation_id_format() -> bool:
        """KB-006: relation id MUST match ^rel:.+$."""
        from .knowledge import KnowledgeRelation

        base = KnowledgeBehavior._valid_relation_payload()
        valid = not KnowledgeBehavior._is_rejected(KnowledgeRelation, base)
        return valid and KnowledgeBehavior._is_rejected(
            KnowledgeRelation, {**base, "id": "sheng:probe"}
        )

    @staticmethod
    def verify_kb_007_relation_type() -> bool:
        """KB-007: relation_type MUST be one of the 15 RelationType values."""
        from .knowledge import KnowledgeRelation

        base = KnowledgeBehavior._valid_relation_payload()
        valid = not KnowledgeBehavior._is_rejected(KnowledgeRelation, base)
        return valid and KnowledgeBehavior._is_rejected(
            KnowledgeRelation, {**base, "relation_type": "not_a_relation_type"}
        )

    @staticmethod
    def verify_kb_008_relation_direction() -> bool:
        """KB-008: direction MUST be 'directed' or 'undirected'."""
        from .knowledge import KnowledgeRelation

        base = KnowledgeBehavior._valid_relation_payload()
        valid = not KnowledgeBehavior._is_rejected(KnowledgeRelation, base)
        return (
            valid
            and KnowledgeBehavior._is_rejected(KnowledgeRelation, {**base, "direction": "sideways"})
            and not KnowledgeBehavior._is_rejected(
                KnowledgeRelation, {**base, "direction": "undirected"}
            )
        )

    @staticmethod
    def verify_kb_009_relation_weight_bounds() -> bool:
        """KB-009: weight MUST be within [0.0, 1.0]."""
        from .knowledge import KnowledgeRelation

        base = KnowledgeBehavior._valid_relation_payload()
        valid = not KnowledgeBehavior._is_rejected(KnowledgeRelation, base)
        return (
            valid
            and KnowledgeBehavior._is_rejected(KnowledgeRelation, {**base, "weight": 2.0})
            and KnowledgeBehavior._is_rejected(KnowledgeRelation, {**base, "weight": -1.0})
        )

    @staticmethod
    def verify_kb_010_reference_id_format() -> bool:
        """KB-010: reference id MUST match ^ref:[a-z_]+:[a-z_0-9]+$."""
        from .knowledge import KnowledgeReference

        base = KnowledgeBehavior._valid_reference_payload()
        valid = not KnowledgeBehavior._is_rejected(KnowledgeReference, base)
        return valid and KnowledgeBehavior._is_rejected(
            KnowledgeReference, {**base, "reference_id": "classic:probe"}
        )

    @staticmethod
    def verify_kb_011_reference_type() -> bool:
        """KB-011: ref_type MUST be one of the 4 ReferenceType values."""
        from .knowledge import KnowledgeReference

        base = KnowledgeBehavior._valid_reference_payload()
        valid = not KnowledgeBehavior._is_rejected(KnowledgeReference, base)
        return valid and KnowledgeBehavior._is_rejected(
            KnowledgeReference, {**base, "ref_type": "not_a_ref_type"}
        )

    # == Full Behavior Audit ==

    @staticmethod
    def audit(store: KnowledgeStore) -> dict:
        """Run a full behavior audit on a KnowledgeStore.

        Returns a dict of contract_id -> bool for **all 20** Knowledge
        Behavior Contracts (KB-001 ~ KB-020), plus architecture-boundary
        entries. Phase 7.4 (ACP-REF-001 Option A) extended this from the
        previous partial set (5 contract keys) to the full coverage that
        CF-015 requires.
        """
        results = {}

        # KB-001 ~ KB-011: schema / validation contracts (store-independent)
        results["KB-001"] = KnowledgeBehavior.verify_kb_001_node_id_format()
        results["KB-002"] = KnowledgeBehavior.verify_kb_002_node_type()
        results["KB-003"] = KnowledgeBehavior.verify_kb_003_systems_non_empty()
        results["KB-004"] = KnowledgeBehavior.verify_kb_004_confidence_bounds()
        results["KB-005"] = KnowledgeBehavior.verify_kb_005_extra_fields_rejected()
        results["KB-006"] = KnowledgeBehavior.verify_kb_006_relation_id_format()
        results["KB-007"] = KnowledgeBehavior.verify_kb_007_relation_type()
        results["KB-008"] = KnowledgeBehavior.verify_kb_008_relation_direction()
        results["KB-009"] = KnowledgeBehavior.verify_kb_009_relation_weight_bounds()
        results["KB-010"] = KnowledgeBehavior.verify_kb_010_reference_id_format()
        results["KB-011"] = KnowledgeBehavior.verify_kb_011_reference_type()

        # KB-012: unknown node returns None
        results["KB-012"] = KnowledgeBehavior.verify_null_handling(
            store,
            "kn:nonexistent:node",
        )

        nodes = store.all_nodes()
        if nodes:
            probe = nodes[0]

            # KB-013: find_by_type sorted by node id
            r13 = store.execute(
                KnowledgeQuery(
                    query_type=KnowledgeQueryType.FIND_BY_TYPE,
                    node_type=probe.node_type,
                )
            )
            results["KB-013"] = KnowledgeBehavior.verify_node_sorting(r13.nodes)

            # KB-014: find_by_system sorted by node id
            r14 = store.execute(
                KnowledgeQuery(
                    query_type=KnowledgeQueryType.FIND_BY_SYSTEM,
                    system=probe.systems[0],
                )
            )
            results["KB-014"] = KnowledgeBehavior.verify_node_sorting(r14.nodes)

            # KB-015: find_by_tag sorted by node id
            tag = probe.tags[0] if probe.tags else "probe"
            r15 = store.execute(KnowledgeQuery(query_type=KnowledgeQueryType.FIND_BY_TAG, tag=tag))
            results["KB-015"] = KnowledgeBehavior.verify_node_sorting(r15.nodes)

            # KB-016: find_relation sorted by relation id
            r16 = store.execute(
                KnowledgeQuery(
                    query_type=KnowledgeQueryType.FIND_RELATION,
                    node_id=probe.id,
                )
            )
            results["KB-016"] = KnowledgeBehavior.verify_relation_sorting(r16.relations)

            # KB-017: find_reference sorted by reference_id
            r17 = store.execute(
                KnowledgeQuery(
                    query_type=KnowledgeQueryType.FIND_REFERENCE,
                    target_id=probe.id,
                )
            )
            results["KB-017"] = KnowledgeBehavior.verify_reference_sorting(r17.references)
        else:
            # No data to exercise the query contracts -> NOT a pass.
            for cid in ("KB-013", "KB-014", "KB-015", "KB-016", "KB-017"):
                results[cid] = False

        # KB-018: duplicate node id rejected
        results["KB-018"] = bool(nodes) and (
            KnowledgeBehavior.verify_duplicate_node_rejected(store, nodes[0])
        )

        # KB-019: duplicate relation id rejected
        relations = store.all_relations()
        results["KB-019"] = bool(relations) and (
            KnowledgeBehavior.verify_duplicate_relation_rejected(store, relations[0])
        )

        # KB-020: deterministic output + stable JSON
        if nodes:
            query = KnowledgeQuery(
                query_type=KnowledgeQueryType.FIND_BY_ID,
                node_id=nodes[0].id,
            )
            results["KB-020"] = KnowledgeBehavior.verify_determinism(
                store, query
            ) and KnowledgeBehavior.verify_json_stability(store.execute(query))
        else:
            results["KB-020"] = False

        # Architecture boundary
        results["ARCH-no-reasoning"] = KnowledgeBehavior.verify_no_reasoning_methods()
        results["ARCH-no-conclusion"] = KnowledgeBehavior.verify_node_no_conclusion_field()

        return results
