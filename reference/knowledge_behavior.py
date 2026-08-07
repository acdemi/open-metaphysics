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

    # == Full Behavior Audit ==

    @staticmethod
    def audit(store: KnowledgeStore) -> dict:
        """Run a full behavior audit on a KnowledgeStore.

        Returns a dict of contract_id -> bool for all verifiable contracts.
        """
        results = {}

        # KB-012: null handling
        results["KB-012"] = KnowledgeBehavior.verify_null_handling(
            store,
            "kn:nonexistent:node",
        )

        # KB-013~017: sorting
        results["KB-013_015"] = KnowledgeBehavior.verify_node_sorting(
            store.all_nodes(),
        )
        results["KB-016"] = KnowledgeBehavior.verify_relation_sorting(
            store.all_relations(),
        )
        results["KB-017"] = KnowledgeBehavior.verify_reference_sorting(
            store.all_references(),
        )

        # KB-019: determinism
        if store.node_count > 0:
            first_node = store.all_nodes()[0]
            query = KnowledgeQuery(
                query_type=KnowledgeQueryType.FIND_BY_ID,
                node_id=first_node.id,
            )
            results["KB-019"] = KnowledgeBehavior.verify_determinism(store, query)
        else:
            results["KB-019"] = True

        # Architecture boundary
        results["ARCH-no-reasoning"] = KnowledgeBehavior.verify_no_reasoning_methods()
        results["ARCH-no-conclusion"] = KnowledgeBehavior.verify_node_no_conclusion_field()

        return results
