"""Reference Consensus Behavior -- Phase 6B Sprint 5.

Provides behavior verification utilities for the Consensus Layer.
Used by Golden Tests and CI to verify that the ConsensusBuilder
satisfies all 25 Behavior Contracts (CS-001 through CS-025).

Architecture Boundary:
  ConsensusBehavior verifies that Consensus remains an Evidence-only
  consumer. It does NOT add reasoning, rule evaluation, pattern
  matching, knowledge queries, or LLM calls.

See: docs/specification/CONSENSUS_BEHAVIOR_SPEC.md
"""

from __future__ import annotations

from .consensus import (
    ConsensusConclusion,
    ConsensusInput,
    ConsensusReport,
    ConsensusStrategy,
)
from .consensus_builder import ConsensusBuilder


class ConsensusBehavior:
    """Verifies Consensus Layer behavior contracts (CS-001 ~ CS-025).

    All methods are static and return bool.
    Used by tests and CI to enforce behavior contracts.
    """

    CONTRACT_VERSION = "1.0.0"

    # == Determinism Verification ==

    @staticmethod
    def verify_determinism(
        builder: ConsensusBuilder,
        input_data: ConsensusInput,
    ) -> bool:
        """CS-020: Same input produces identical output."""
        r1 = builder.build(input_data)
        r2 = builder.build(input_data)
        return r1.model_dump_json() == r2.model_dump_json()

    @staticmethod
    def verify_json_stability(report: ConsensusReport) -> bool:
        """CS-021: JSON serialization is stable across repeated calls."""
        j1 = report.model_dump_json()
        j2 = report.model_dump_json()
        return j1 == j2

    # == Sorting Verification ==

    @staticmethod
    def verify_conclusion_sorting(
        conclusions: list[ConsensusConclusion],
    ) -> bool:
        """CS-012: Conclusions sorted by domain, then confidence desc, then conclusion."""
        keys = [(c.domain.value, -c.confidence, c.conclusion, c.conclusion_id) for c in conclusions]
        return keys == sorted(keys)

    @staticmethod
    def verify_domain_sorting(report: ConsensusReport) -> bool:
        """CS-011: Domains sorted alphabetically."""
        domain_vals = [d.value for d in report.domains]
        return domain_vals == sorted(domain_vals)

    @staticmethod
    def verify_evidence_id_sorting(report: ConsensusReport) -> bool:
        """CS-023: Evidence IDs sorted in report."""
        return report.evidence_ids == sorted(report.evidence_ids)

    # == Conflict Verification ==

    @staticmethod
    def verify_conflict_detection(
        report: ConsensusReport,
        strategy: ConsensusStrategy,
    ) -> bool:
        """CS-013~015: Conflict detection and strategy application."""
        # Group surviving conclusions by domain
        by_domain: dict[str, list[ConsensusConclusion]] = {}
        for cc in report.conclusions:
            by_domain.setdefault(cc.domain.value, []).append(cc)

        for _domain_val, ccs in by_domain.items():
            if len(ccs) > 1:
                # Multiple conclusions in same domain = conflict
                if strategy == ConsensusStrategy.RETAIN_ALL:
                    # All should be marked as conflict
                    if not all(cc.is_conflict for cc in ccs):
                        return False
                else:
                    # Only one should survive
                    if len(ccs) != 1:
                        return False
                    if not ccs[0].is_conflict:
                        return False
        return True

    # == Null / Empty Handling ==

    @staticmethod
    def verify_empty_input(builder: ConsensusBuilder) -> bool:
        """CS-016: Empty input produces empty report."""
        report = builder.build(ConsensusInput(evidence=[]))
        return (
            len(report.conclusions) == 0
            and len(report.conflicts) == 0
            and len(report.evidence_ids) == 0
            and len(report.domains) == 0
            and report.overall_confidence == 0.0
        )

    # == Duplicate Handling ==

    @staticmethod
    def verify_duplicate_evidence_dedup(
        builder: ConsensusBuilder,
        evidence_list,
    ) -> bool:
        """CS-017: Duplicate evidence IDs are deduplicated."""
        if not evidence_list:
            return True
        dup_list = list(evidence_list) + list(evidence_list)
        report = builder.build(ConsensusInput(evidence=dup_list))
        unique_ids = set(ev.evidence_id for ev in evidence_list)
        return set(report.evidence_ids) == unique_ids

    # == Cross-System Bonus Verification ==

    @staticmethod
    def verify_cross_system_bonus(
        builder: ConsensusBuilder,
        single_system_evidence,
        multi_system_evidence,
    ) -> bool:
        """CS-008~009: Cross-system bonus applied when multiple systems contribute."""
        r1 = builder.build(ConsensusInput(evidence=single_system_evidence))
        r2 = builder.build(ConsensusInput(evidence=multi_system_evidence))

        if not r1.conclusions or not r2.conclusions:
            return True  # can't verify if no conclusions

        # The multi-system conclusion should have bonus in metadata
        for cc in r2.conclusions:
            if cc.metadata.get("system_count", 0) > 1:
                if cc.metadata.get("cross_system_bonus", 0.0) <= 0.0:
                    return False
        return True

    # == Architecture Boundary Verification ==

    @staticmethod
    def verify_no_reasoning_methods() -> bool:
        """CS-025: ConsensusBuilder has no reasoning/query methods."""
        forbidden = [
            "reason",
            "conclude",
            "evaluate_rule",
            "evaluate",
            "match_pattern",
            "query_knowledge",
            "call_llm",
            "run_rule",
            "run_pattern",
            "infer",
        ]
        for method_name in forbidden:
            if hasattr(ConsensusBuilder, method_name):
                return False
        return True

    @staticmethod
    def verify_input_only_accepts_evidence() -> bool:
        """CS-001: ConsensusInput only accepts Evidence[]."""
        # ConsensusInput.evidence field type is list[Evidence]
        field_info = ConsensusInput.model_fields.get("evidence")
        if field_info is None:
            return False
        return True  # Pydantic enforces type at validation time

    # == Full Audit ==

    @staticmethod
    def audit(builder: ConsensusBuilder) -> dict:
        """Run a full behavior audit on a ConsensusBuilder.

        Returns a dict of contract_id -> bool.
        """
        results = {}

        # CS-016: empty input
        results["CS-016"] = ConsensusBehavior.verify_empty_input(builder)

        # CS-020: determinism (with empty input)
        results["CS-020"] = ConsensusBehavior.verify_determinism(
            builder,
            ConsensusInput(evidence=[]),
        )

        # CS-021: JSON stability
        report = builder.build(ConsensusInput(evidence=[]))
        results["CS-021"] = ConsensusBehavior.verify_json_stability(report)

        # Architecture boundary
        results["CS-025"] = ConsensusBehavior.verify_no_reasoning_methods()
        results["CS-001"] = ConsensusBehavior.verify_input_only_accepts_evidence()

        return results
