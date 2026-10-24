"""Production Consensus Engine.

Deterministic Evidence[] -> ConsensusReport builder conforming to the frozen
Reference Consensus Layer contract v1.0.0
(``reference/contracts/consensus_contract.json``).

Algorithm (mirrors the Reference ConsensusBuilder semantics):
  1. Deduplicate Evidence by ``evidence_id`` (keep first occurrence)
  2. Group Evidence by ``(domain, conclusion)``
  3. Per group: aggregate confidence = max(evidence) + cross-system bonus,
     clamped to ``[min_confidence, max_confidence]``
  4. Detect conflicts (multiple conclusions in one domain)
  5. Apply the conflict strategy (retain_all / highest_confidence / majority)
  6. Sort conclusions by (domain asc, confidence desc, conclusion asc, id asc)
  7. Build the ConsensusReport

Pure and deterministic: no I/O, no side effects.
"""

from __future__ import annotations

from .models import (
    ConsensusConclusion,
    ConsensusConfig,
    ConsensusInput,
    ConsensusReport,
    ConsensusStrategy,
    Domain,
    Evidence,
    ResultDirection,
    make_conclusion_id,
    make_report_id,
)


class ConsensusEngine:
    """Builds a ConsensusReport from Evidence[]."""

    CONTRACT_VERSION = "1.0.0"

    def build(self, input_data: ConsensusInput) -> ConsensusReport:
        """Build a ConsensusReport from a ConsensusInput."""
        evidence_list = input_data.evidence
        config = input_data.config

        if not evidence_list:
            return self._empty_report(config)

        # 1. Deduplicate by evidence_id (keep first occurrence)
        seen_ids: set[str] = set()
        unique_evidence: list[Evidence] = []
        for ev in evidence_list:
            if ev.evidence_id not in seen_ids:
                seen_ids.add(ev.evidence_id)
                unique_evidence.append(ev)

        # 2. Group by (domain, conclusion)
        groups: dict[tuple[str, str], list[Evidence]] = {}
        for ev in unique_evidence:
            key = (ev.domain.value, ev.conclusion)
            groups.setdefault(key, []).append(ev)

        # 3. Build one conclusion per group
        all_conclusions: list[ConsensusConclusion] = [
            self._build_conclusion(domain_val, conclusion, group_evidence, config)
            for (domain_val, conclusion), group_evidence in groups.items()
        ]

        # 4-5. Detect conflicts and apply the strategy
        conclusions, conflicts = self._apply_strategy(all_conclusions, config)

        # 6. Sort surviving conclusions and dropped conflicts
        conclusions = self._sort_conclusions(conclusions)
        conflicts = self._sort_conclusions(conflicts)

        # 7. Build the report
        domains = sorted({c.domain for c in conclusions}, key=lambda d: d.value)
        all_ev_ids = sorted(seen_ids)

        if conclusions:
            overall = sum(c.confidence for c in conclusions) / len(conclusions)
        else:
            overall = 0.0

        return ConsensusReport(
            report_id=make_report_id([c.conclusion_id for c in conclusions]),
            overall_confidence=round(overall, 6),
            domains=domains,
            conclusions=conclusions,
            conflicts=conflicts,
            evidence_ids=all_ev_ids,
            metadata={
                "strategy": config.strategy.value,
                "total_evidence": len(unique_evidence),
                "total_conclusions": len(conclusions),
                "total_conflicts": len(conflicts),
                "cross_system_bonus_per_system": config.cross_system_bonus_per_system,
                "max_cross_system_bonus": config.max_cross_system_bonus,
            },
            version=self.CONTRACT_VERSION,
        )

    # -- Internal: build a single conclusion --

    @staticmethod
    def _build_conclusion(
        domain_val: str,
        conclusion: str,
        group_evidence: list[Evidence],
        config: ConsensusConfig,
    ) -> ConsensusConclusion:
        """Build one ConsensusConclusion from a group of Evidence."""
        domain = Domain(domain_val)
        evidence_ids = sorted(ev.evidence_id for ev in group_evidence)
        systems = sorted({ev.system for ev in group_evidence})

        base_confidence = max(ev.confidence for ev in group_evidence)

        system_count = len(systems)
        if system_count > 1:
            bonus = min(
                config.cross_system_bonus_per_system * (system_count - 1),
                config.max_cross_system_bonus,
            )
        else:
            bonus = 0.0

        aggregated = min(
            config.max_confidence,
            max(config.min_confidence, base_confidence + bonus),
        )

        # Direction: first non-None item direction, in group order
        direction: ResultDirection | None = None
        for ev in group_evidence:
            for item in ev.items:
                if item.direction is not None:
                    direction = item.direction
                    break
            if direction is not None:
                break

        return ConsensusConclusion(
            conclusion_id=make_conclusion_id(domain_val, conclusion, evidence_ids),
            domain=domain,
            conclusion=conclusion,
            confidence=round(aggregated, 6),
            evidence_ids=evidence_ids,
            evidence_count=len(evidence_ids),
            systems=systems,
            direction=direction,
            is_conflict=False,
            strategy=config.strategy,
            metadata={
                "base_confidence": round(base_confidence, 6),
                "cross_system_bonus": round(bonus, 6),
                "system_count": system_count,
            },
            version=ConsensusEngine.CONTRACT_VERSION,
        )

    # -- Internal: apply the conflict strategy --

    @staticmethod
    def _apply_strategy(
        conclusions: list[ConsensusConclusion],
        config: ConsensusConfig,
    ) -> tuple[list[ConsensusConclusion], list[ConsensusConclusion]]:
        """Return (surviving, dropped) after applying the conflict strategy."""
        by_domain: dict[str, list[ConsensusConclusion]] = {}
        for cc in conclusions:
            by_domain.setdefault(cc.domain.value, []).append(cc)

        surviving: list[ConsensusConclusion] = []
        dropped: list[ConsensusConclusion] = []

        for domain_conclusions in by_domain.values():
            if len(domain_conclusions) <= 1:
                surviving.extend(domain_conclusions)
                continue

            if config.strategy == ConsensusStrategy.RETAIN_ALL:
                for cc in domain_conclusions:
                    cc.is_conflict = True
                surviving.extend(domain_conclusions)

            elif config.strategy == ConsensusStrategy.HIGHEST_CONFIDENCE:
                ranked = sorted(
                    domain_conclusions,
                    key=lambda c: (-c.confidence, c.conclusion, c.conclusion_id),
                )
                ranked[0].is_conflict = True
                surviving.append(ranked[0])
                for cc in ranked[1:]:
                    cc.is_conflict = True
                    dropped.append(cc)

            elif config.strategy == ConsensusStrategy.MAJORITY:
                ranked = sorted(
                    domain_conclusions,
                    key=lambda c: (
                        -c.evidence_count,
                        -c.confidence,
                        c.conclusion,
                        c.conclusion_id,
                    ),
                )
                ranked[0].is_conflict = True
                surviving.append(ranked[0])
                for cc in ranked[1:]:
                    cc.is_conflict = True
                    dropped.append(cc)

        return surviving, dropped

    # -- Internal: sorting --

    @staticmethod
    def _sort_conclusions(
        conclusions: list[ConsensusConclusion],
    ) -> list[ConsensusConclusion]:
        """Sort by domain asc, confidence desc, conclusion asc, id asc."""
        return sorted(
            conclusions,
            key=lambda c: (c.domain.value, -c.confidence, c.conclusion, c.conclusion_id),
        )

    # -- Internal: empty report --

    def _empty_report(self, config: ConsensusConfig) -> ConsensusReport:
        """Build the empty ConsensusReport for empty input."""
        return ConsensusReport(
            report_id=make_report_id([]),
            overall_confidence=0.0,
            domains=[],
            conclusions=[],
            conflicts=[],
            evidence_ids=[],
            metadata={
                "strategy": config.strategy.value,
                "total_evidence": 0,
                "total_conclusions": 0,
                "total_conflicts": 0,
                "cross_system_bonus_per_system": config.cross_system_bonus_per_system,
                "max_cross_system_bonus": config.max_cross_system_bonus,
            },
            version=self.CONTRACT_VERSION,
        )
