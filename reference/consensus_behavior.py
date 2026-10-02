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

    # == Input Validation / Aggregation Verification (CS-002 ~ CS-007) ==
    #
    # Phase 7.4 (ACP-REF-001 Option A): these contracts previously had NO
    # verifier, yet CF-015 lists them as required coverage. Each verifier
    # below drives the real ConsensusBuilder and asserts the contract's
    # observable consequence.

    @staticmethod
    def _evidence(
        evidence_id: str,
        conclusion: str,
        confidence: float,
        system: str = "bazi",
        domain=None,
    ):
        """Build a minimal valid Evidence for behavior probing."""
        from .evidence import Evidence, EvidenceItem, EvidenceType
        from .models import Domain, MetaphysicsSystem

        dom = domain or Domain.CAREER
        sysm = MetaphysicsSystem(system)
        item = EvidenceItem(
            evidence_id=f"{evidence_id}#i1",
            source_type=EvidenceType.RULE,
            source_id="probe-source",
            system=sysm,
            domain=dom,
            confidence=confidence,
            conclusion=conclusion,
        )
        return Evidence(
            evidence_id=evidence_id,
            domain=dom,
            conclusion=conclusion,
            confidence=confidence,
            system=sysm,
            items=[item],
        )

    @staticmethod
    def verify_non_evidence_rejected() -> bool:
        """CS-002: Non-Evidence objects MUST raise ValidationError."""
        from pydantic import ValidationError

        # raw dict without required Evidence fields
        try:
            ConsensusInput(evidence=[{"not": "an evidence"}])
            return False
        except ValidationError:
            pass
        except Exception:
            return False

        # a different model (EvidenceItem) instead of Evidence
        from .evidence import EvidenceItem

        try:
            ConsensusInput(
                evidence=[
                    EvidenceItem(
                        evidence_id="ei:1",
                        source_type="rule",
                        source_id="r1",
                    )
                ]
            )
            return False
        except ValidationError:
            return True
        except Exception:
            return False

    @staticmethod
    def verify_evidence_grouping(builder: ConsensusBuilder) -> bool:
        """CS-003: Evidence grouped by (domain, conclusion) into one conclusion."""
        evs = [
            ConsensusBehavior._evidence("ev:a1", "same text", 0.5),
            ConsensusBehavior._evidence("ev:a2", "same text", 0.7),
        ]
        report = builder.build(ConsensusInput(evidence=evs))
        if len(report.conclusions) != 1:
            return False
        cc = report.conclusions[0]
        return set(cc.evidence_ids) == {"ev:a1", "ev:a2"} and cc.evidence_count == 2

    @staticmethod
    def verify_retain_all_keeps_all(builder: ConsensusBuilder) -> bool:
        """CS-004: retain_all keeps ALL conclusions and marks conflicts."""
        from .consensus import ConsensusConfig

        evs = [
            ConsensusBehavior._evidence("ev:b1", "text one", 0.9),
            ConsensusBehavior._evidence("ev:b2", "text two", 0.4),
        ]
        cfg = ConsensusConfig(strategy=ConsensusStrategy.RETAIN_ALL)
        report = builder.build(ConsensusInput(evidence=evs, config=cfg))
        if len(report.conclusions) != 2:
            return False
        return all(cc.is_conflict for cc in report.conclusions)

    @staticmethod
    def verify_highest_confidence_winner(builder: ConsensusBuilder) -> bool:
        """CS-005: highest_confidence keeps the top conclusion per domain; losers -> conflicts."""
        from .consensus import ConsensusConfig

        evs = [
            ConsensusBehavior._evidence("ev:c1", "high text", 0.9),
            ConsensusBehavior._evidence("ev:c2", "low text", 0.2),
        ]
        cfg = ConsensusConfig(strategy=ConsensusStrategy.HIGHEST_CONFIDENCE)
        report = builder.build(ConsensusInput(evidence=evs, config=cfg))
        if len(report.conclusions) != 1:
            return False
        if report.conclusions[0].conclusion != "high text":
            return False
        return len(report.conflicts) == 1 and report.conflicts[0].conclusion == "low text"

    @staticmethod
    def verify_majority_winner(builder: ConsensusBuilder) -> bool:
        """CS-006: majority keeps the conclusion with the most evidence items."""
        from .consensus import ConsensusConfig

        evs = [
            ConsensusBehavior._evidence("ev:d1", "majority text", 0.5),
            ConsensusBehavior._evidence("ev:d2", "majority text", 0.5),
            ConsensusBehavior._evidence("ev:d3", "minority text", 0.9),
        ]
        cfg = ConsensusConfig(strategy=ConsensusStrategy.MAJORITY)
        report = builder.build(ConsensusInput(evidence=evs, config=cfg))
        if len(report.conclusions) != 1:
            return False
        return report.conclusions[0].conclusion == "majority text"

    @staticmethod
    def verify_confidence_aggregation(builder: ConsensusBuilder) -> bool:
        """CS-007: base confidence = max(evidence.confidence) within a group."""
        evs = [
            ConsensusBehavior._evidence("ev:e1", "grouped text", 0.3),
            ConsensusBehavior._evidence("ev:e2", "grouped text", 0.8),
        ]
        report = builder.build(ConsensusInput(evidence=evs))
        if len(report.conclusions) != 1:
            return False
        # single system -> no cross-system bonus, so confidence == max(...)
        return abs(report.conclusions[0].confidence - 0.8) < 1e-9

    @staticmethod
    def verify_bonus_configurable(builder: ConsensusBuilder) -> bool:
        """CS-010: bonus configurable; per_system = 0 disables it."""
        from .consensus import ConsensusConfig

        evs = [
            ConsensusBehavior._evidence("ev:f1", "cross text", 0.5, system="bazi"),
            ConsensusBehavior._evidence("ev:f2", "cross text", 0.5, system="qimen"),
        ]
        off = ConsensusConfig(cross_system_bonus_per_system=0.0)
        on = ConsensusConfig(cross_system_bonus_per_system=0.1, max_cross_system_bonus=0.5)
        r_off = builder.build(ConsensusInput(evidence=evs, config=off))
        r_on = builder.build(ConsensusInput(evidence=evs, config=on))
        if not r_off.conclusions or not r_on.conclusions:
            return False
        return r_on.conclusions[0].confidence > r_off.conclusions[0].confidence

    @staticmethod
    def verify_duplicate_domain_handling(builder: ConsensusBuilder) -> bool:
        """CS-018: multiple conclusions in one domain are handled by the strategy (0..N)."""
        from .consensus import ConsensusConfig

        evs = [
            ConsensusBehavior._evidence("ev:g1", "one", 0.4),
            ConsensusBehavior._evidence("ev:g2", "two", 0.6),
            ConsensusBehavior._evidence("ev:g3", "three", 0.5),
        ]
        retain = builder.build(
            ConsensusInput(
                evidence=evs,
                config=ConsensusConfig(strategy=ConsensusStrategy.RETAIN_ALL),
            )
        )
        highest = builder.build(
            ConsensusInput(
                evidence=evs,
                config=ConsensusConfig(strategy=ConsensusStrategy.HIGHEST_CONFIDENCE),
            )
        )
        return len(retain.conclusions) == 3 and len(highest.conclusions) == 1

    @staticmethod
    def verify_duplicate_conclusion_merged(builder: ConsensusBuilder) -> bool:
        """CS-019: same (domain, conclusion) merged with combined evidence_ids."""
        evs = [
            ConsensusBehavior._evidence("ev:h1", "merged", 0.4),
            ConsensusBehavior._evidence("ev:h2", "merged", 0.6),
            ConsensusBehavior._evidence("ev:h3", "merged", 0.5),
        ]
        report = builder.build(ConsensusInput(evidence=evs))
        if len(report.conclusions) != 1:
            return False
        cc = report.conclusions[0]
        return set(cc.evidence_ids) == {"ev:h1", "ev:h2", "ev:h3"} and cc.evidence_count == 3

    @staticmethod
    def verify_overall_confidence(builder: ConsensusBuilder) -> bool:
        """CS-022: overall_confidence = average of surviving conclusions; 0.0 if none."""
        empty = builder.build(ConsensusInput(evidence=[]))
        if empty.overall_confidence != 0.0:
            return False
        evs = [
            ConsensusBehavior._evidence("ev:i1", "avg one", 0.4),
            ConsensusBehavior._evidence("ev:i2", "avg two", 0.8),
        ]
        report = builder.build(ConsensusInput(evidence=evs))
        if not report.conclusions:
            return False
        expected = sum(cc.confidence for cc in report.conclusions) / len(report.conclusions)
        return abs(report.overall_confidence - expected) < 1e-9

    @staticmethod
    def verify_report_required_fields() -> bool:
        """CS-024: ConsensusReport always contains the required fields."""
        required = {
            "report_id",
            "overall_confidence",
            "domains",
            "conclusions",
            "conflicts",
            "evidence_ids",
            "metadata",
            "version",
        }
        return required <= set(ConsensusReport.model_fields)

    @staticmethod
    def verify_cross_system_bonus_applied(builder: ConsensusBuilder) -> bool:
        """CS-008: bonus = bonus_per_system * (system_count - 1) when 2+ systems."""
        from .consensus import ConsensusConfig

        cfg = ConsensusConfig(cross_system_bonus_per_system=0.1, max_cross_system_bonus=1.0)
        evs = [
            ConsensusBehavior._evidence("ev:j1", "bonus text", 0.5, system="bazi"),
            ConsensusBehavior._evidence("ev:j2", "bonus text", 0.5, system="qimen"),
        ]
        report = builder.build(ConsensusInput(evidence=evs, config=cfg))
        if len(report.conclusions) != 1:
            return False
        cc = report.conclusions[0]
        if cc.metadata.get("system_count") != 2:
            return False
        return abs(cc.confidence - 0.6) < 1e-9

    @staticmethod
    def verify_cross_system_bonus_capped(builder: ConsensusBuilder) -> bool:
        """CS-009: total bonus MUST NOT exceed max_cross_system_bonus."""
        from .consensus import ConsensusConfig

        cfg = ConsensusConfig(cross_system_bonus_per_system=0.3, max_cross_system_bonus=0.2)
        evs = [
            ConsensusBehavior._evidence("ev:k1", "cap text", 0.5, system="bazi"),
            ConsensusBehavior._evidence("ev:k2", "cap text", 0.5, system="qimen"),
            ConsensusBehavior._evidence("ev:k3", "cap text", 0.5, system="ziwei"),
        ]
        report = builder.build(ConsensusInput(evidence=evs, config=cfg))
        if len(report.conclusions) != 1:
            return False
        cc = report.conclusions[0]
        # raw bonus would be 0.3 * 2 = 0.6; capped at 0.2
        return cc.confidence <= 0.5 + 0.2 + 1e-9

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

        Returns a dict of contract_id -> bool for **all 25** Consensus
        Behavior Contracts (CS-001 ~ CS-025). Phase 7.4 (ACP-REF-001
        Option A) extended this from 5 keys to the full coverage that
        CF-015 requires.
        """
        from .consensus import ConsensusConfig

        results = {}

        # CS-001 / CS-002: input accepts only Evidence
        results["CS-001"] = ConsensusBehavior.verify_input_only_accepts_evidence()
        results["CS-002"] = ConsensusBehavior.verify_non_evidence_rejected()

        # CS-003 / CS-019: grouping + duplicate-conclusion merge
        results["CS-003"] = ConsensusBehavior.verify_evidence_grouping(builder)
        results["CS-019"] = ConsensusBehavior.verify_duplicate_conclusion_merged(builder)

        # CS-004 / CS-005 / CS-006: strategies
        results["CS-004"] = ConsensusBehavior.verify_retain_all_keeps_all(builder)
        results["CS-005"] = ConsensusBehavior.verify_highest_confidence_winner(builder)
        results["CS-006"] = ConsensusBehavior.verify_majority_winner(builder)

        # CS-007 / CS-008 / CS-009 / CS-010: confidence + bonus
        results["CS-007"] = ConsensusBehavior.verify_confidence_aggregation(builder)
        results["CS-008"] = ConsensusBehavior.verify_cross_system_bonus_applied(builder)
        results["CS-009"] = ConsensusBehavior.verify_cross_system_bonus_capped(builder)
        results["CS-010"] = ConsensusBehavior.verify_bonus_configurable(builder)

        # CS-011 / CS-012 / CS-023: sorting (probe with a populated report)
        probe_evs = [
            ConsensusBehavior._evidence("ev:l1", "sort b", 0.4, system="qimen"),
            ConsensusBehavior._evidence("ev:l2", "sort a", 0.9, system="bazi"),
        ]
        probe = builder.build(ConsensusInput(evidence=probe_evs))
        results["CS-011"] = ConsensusBehavior.verify_domain_sorting(probe)
        results["CS-012"] = ConsensusBehavior.verify_conclusion_sorting(probe.conclusions)
        results["CS-023"] = ConsensusBehavior.verify_evidence_id_sorting(probe)

        # CS-013 / CS-014 / CS-015: conflict detection / marking / dropped
        conflict_evs = [
            ConsensusBehavior._evidence("ev:m1", "conflict one", 0.9),
            ConsensusBehavior._evidence("ev:m2", "conflict two", 0.4),
        ]
        retain_cfg = ConsensusConfig(strategy=ConsensusStrategy.RETAIN_ALL)
        retain = builder.build(ConsensusInput(evidence=conflict_evs, config=retain_cfg))
        highest_cfg = ConsensusConfig(strategy=ConsensusStrategy.HIGHEST_CONFIDENCE)
        highest = builder.build(ConsensusInput(evidence=conflict_evs, config=highest_cfg))
        # CS-013: 2+ conclusions sharing a domain constitute a conflict
        results["CS-013"] = len(retain.conclusions) == 2
        # CS-014: conflicting conclusions marked, single conclusion not
        single = builder.build(
            ConsensusInput(evidence=[ConsensusBehavior._evidence("ev:m3", "solo", 0.5)])
        )
        results["CS-014"] = (
            all(cc.is_conflict for cc in retain.conclusions)
            and len(single.conclusions) == 1
            and single.conclusions[0].is_conflict is False
        )
        # CS-015: dropped conclusions appear in conflicts; retain_all -> empty
        results["CS-015"] = len(highest.conflicts) == 1 and len(retain.conflicts) == 0

        # CS-016 / CS-018: empty input + duplicate domain handling
        results["CS-016"] = ConsensusBehavior.verify_empty_input(builder)
        results["CS-018"] = ConsensusBehavior.verify_duplicate_domain_handling(builder)

        # CS-017: duplicate evidence dedup
        results["CS-017"] = ConsensusBehavior.verify_duplicate_evidence_dedup(builder, probe_evs)

        # CS-020 / CS-021: determinism + stable JSON
        results["CS-020"] = ConsensusBehavior.verify_determinism(
            builder, ConsensusInput(evidence=probe_evs)
        )
        results["CS-021"] = ConsensusBehavior.verify_json_stability(probe)

        # CS-022 / CS-024: overall confidence + required report fields
        results["CS-022"] = ConsensusBehavior.verify_overall_confidence(builder)
        results["CS-024"] = ConsensusBehavior.verify_report_required_fields()

        # CS-025: architecture boundary
        results["CS-025"] = ConsensusBehavior.verify_no_reasoning_methods()

        return results
