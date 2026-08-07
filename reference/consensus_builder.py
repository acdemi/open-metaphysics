"""Reference Consensus Builder -- Phase 6B Sprint 5.

The ConsensusBuilder consumes Evidence[] and produces a
ConsensusReport containing ConsensusConclusion[].

Algorithm:
  1. Deduplicate Evidence by evidence_id
  2. Group Evidence by (domain, conclusion)
  3. For each group: aggregate confidence + cross-system bonus
  4. Detect conflicts (multiple conclusions in same domain)
  5. Apply conflict strategy (retain_all / highest_confidence / majority)
  6. Sort conclusions (by domain, then confidence desc, then conclusion)
  7. Build ConsensusReport

Architecture Boundary:
  ConsensusBuilder does NOT import or call RuleEngine, PatternMatcher,
  KnowledgeStore, or any LLM. It only consumes Evidence.

See: docs/design/phase6/06_flow_diagram.md
     docs/specification/CONSENSUS_BEHAVIOR_SPEC.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .consensus import (
    ConsensusConclusion,
    ConsensusConfig,
    ConsensusInput,
    ConsensusReport,
    ConsensusStrategy,
    make_conclusion_id,
    make_report_id,
)
from .evidence import Evidence
from .models import Domain, ResultDirection

# == ConsensusBuilder ==


class ConsensusBuilder:
    """Builds a ConsensusReport from Evidence[].

    Deterministic: same input always produces identical output.
    Pure: no I/O (except contract export), no side effects.
    """

    CONTRACT_VERSION = "1.0.0"

    def build(self, input_data: ConsensusInput) -> ConsensusReport:
        """Build a ConsensusReport from a ConsensusInput.

        Args:
            input_data: ConsensusInput containing Evidence[] and config.

        Returns:
            ConsensusReport with sorted conclusions and conflicts.
        """
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

        # 3. Build conclusions for each group
        all_conclusions: list[ConsensusConclusion] = []
        for (domain_val, conclusion), group_evidence in groups.items():
            cc = self._build_conclusion(
                domain_val,
                conclusion,
                group_evidence,
                config,
            )
            all_conclusions.append(cc)

        # 4-5. Detect conflicts and apply strategy
        conclusions, conflicts = self._apply_strategy(all_conclusions, config)

        # 6. Sort
        conclusions = self._sort_conclusions(conclusions)
        conflicts = self._sort_conclusions(conflicts)

        # 7. Build report
        domains = sorted(
            set(c.domain for c in conclusions),
            key=lambda d: d.value,
        )
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
        """Build a ConsensusConclusion from a group of Evidence."""
        domain = Domain(domain_val)
        evidence_ids = sorted(ev.evidence_id for ev in group_evidence)

        # Collect distinct systems
        systems = sorted(set(ev.system for ev in group_evidence))

        # Base confidence: max of evidence confidences
        base_confidence = max(ev.confidence for ev in group_evidence)

        # Cross-system bonus
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

        # Direction: first non-None from evidence items
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
            version=ConsensusBuilder.CONTRACT_VERSION,
        )

    # -- Internal: apply conflict strategy --

    @staticmethod
    def _apply_strategy(
        conclusions: list[ConsensusConclusion],
        config: ConsensusConfig,
    ) -> tuple[list[ConsensusConclusion], list[ConsensusConclusion]]:
        """Apply conflict strategy and return (surviving, dropped).

        A conflict exists when multiple conclusions share the same domain.
        """
        # Group by domain
        by_domain: dict[str, list[ConsensusConclusion]] = {}
        for cc in conclusions:
            by_domain.setdefault(cc.domain.value, []).append(cc)

        surviving: list[ConsensusConclusion] = []
        dropped: list[ConsensusConclusion] = []

        for _domain_val, domain_conclusions in by_domain.items():
            if len(domain_conclusions) <= 1:
                # No conflict
                surviving.extend(domain_conclusions)
                continue

            # Conflict detected: multiple conclusions in same domain
            if config.strategy == ConsensusStrategy.RETAIN_ALL:
                for cc in domain_conclusions:
                    cc.is_conflict = True
                surviving.extend(domain_conclusions)

            elif config.strategy == ConsensusStrategy.HIGHEST_CONFIDENCE:
                sorted_ccs = sorted(
                    domain_conclusions,
                    key=lambda c: (-c.confidence, c.conclusion, c.conclusion_id),
                )
                winner = sorted_ccs[0]
                winner.is_conflict = True
                surviving.append(winner)
                for cc in sorted_ccs[1:]:
                    cc.is_conflict = True
                    dropped.append(cc)

            elif config.strategy == ConsensusStrategy.MAJORITY:
                sorted_ccs = sorted(
                    domain_conclusions,
                    key=lambda c: (
                        -c.evidence_count,
                        -c.confidence,
                        c.conclusion,
                        c.conclusion_id,
                    ),
                )
                winner = sorted_ccs[0]
                winner.is_conflict = True
                surviving.append(winner)
                for cc in sorted_ccs[1:]:
                    cc.is_conflict = True
                    dropped.append(cc)

        return surviving, dropped

    # -- Internal: sorting --

    @staticmethod
    def _sort_conclusions(
        conclusions: list[ConsensusConclusion],
    ) -> list[ConsensusConclusion]:
        """Sort by domain (asc), then confidence (desc), then conclusion (asc)."""
        return sorted(
            conclusions,
            key=lambda c: (c.domain.value, -c.confidence, c.conclusion, c.conclusion_id),
        )

    # -- Internal: empty report --

    @staticmethod
    def _empty_report(config: ConsensusConfig) -> ConsensusReport:
        """Build an empty ConsensusReport for empty input."""
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
            version=ConsensusBuilder.CONTRACT_VERSION,
        )


# == Contract Export ==

CONSENSUS_CONTRACT_PATH = Path(__file__).parent / "contracts" / "consensus_contract.json"


def _build_golden_examples() -> list[dict[str, Any]]:
    """Build golden examples by running the Reference Runtime."""
    from .engine import RuleEngine
    from .evidence_builder import EvidenceBuilder
    from .parser import parse_rule_file
    from .pattern_matcher import PatternMatcher
    from .patterns import parse_pattern_file

    examples_dir = Path(__file__).parent / "examples"
    pat_dir = examples_dir / "patterns"
    engine = RuleEngine()
    matcher = PatternMatcher()
    ev_builder = EvidenceBuilder()
    builder = ConsensusBuilder()

    chart_with_seal = {
        "ten_gods_map": {"values": ["伤官", "正印", "比肩"]},
        "day_master_strength": 0.35,
        "shen_sha_list": ["羊刃", "天乙贵人"],
    }
    chart_qimen = {"dun_type": "yang", "ju": 6}

    golden: list[dict[str, Any]] = []

    # Example 1: Single evidence -> consensus
    rules = parse_rule_file(str(examples_dir / "01_single_condition.yaml"))
    evals = engine.evaluate_all(rules, chart_with_seal)
    evidence = ev_builder.build_from_evaluations(evals, "bazi")
    report = builder.build(ConsensusInput(evidence=evidence))
    golden.append(
        {
            "name": "single_evidence_consensus",
            "description": "A single Evidence produces one conclusion.",
            "input_type": "single_evidence",
            "report": report.model_dump(mode="json"),
        }
    )

    # Example 2: Multiple evidence (rule + pattern) -> consensus
    multi_rules = []
    for fname in ["07_has_shang_guan.yaml", "08_has_zheng_yin.yaml", "09_weak_day_master.yaml"]:
        multi_rules.extend(parse_rule_file(str(examples_dir / fname)))
    multi_evals = engine.evaluate_all(multi_rules, chart_with_seal)
    pattern = parse_pattern_file(str(pat_dir / "02_multi_rule.yaml"))
    pm = matcher.match(pattern, multi_evals, "bazi")
    combined_evals = evals + multi_evals
    pattern1 = parse_pattern_file(str(pat_dir / "01_single_rule.yaml"))
    pm1 = matcher.match(pattern1, combined_evals, "bazi")
    all_evidence = ev_builder.build_all(combined_evals, [pm1, pm], "bazi")
    report2 = builder.build(ConsensusInput(evidence=all_evidence))
    golden.append(
        {
            "name": "multiple_evidence_consensus",
            "description": "Multiple Evidence (rules + patterns) produce multiple conclusions.",
            "input_type": "multiple_evidence",
            "report": report2.model_dump(mode="json"),
        }
    )

    # Example 3: Cross-system evidence -> consensus with bonus
    bazi_evals = engine.evaluate_all(
        parse_rule_file(str(examples_dir / "01_single_condition.yaml")),
        chart_with_seal,
    )
    qimen_evals = engine.evaluate_all(
        parse_rule_file(str(examples_dir / "05_scope.yaml")),
        chart_qimen,
    )
    cross_pattern = parse_pattern_file(str(pat_dir / "04_cross_system.yaml"))
    cross_pm = matcher.match_cross_system(
        cross_pattern,
        {"bazi": bazi_evals, "qimen": qimen_evals},
    )
    bazi_ev = ev_builder.build_from_evaluations(bazi_evals, "bazi")
    cross_ev = ev_builder.build_from_pattern_matches([cross_pm])
    all_cross_ev = bazi_ev + cross_ev
    report3 = builder.build(ConsensusInput(evidence=all_cross_ev))
    golden.append(
        {
            "name": "cross_system_consensus",
            "description": "Evidence from bazi and cross_system produces conclusions with cross-system bonus.",
            "input_type": "cross_system",
            "report": report3.model_dump(mode="json"),
        }
    )

    # Example 4: Conflict with retain_all
    conflict_evidence = [
        Evidence(
            evidence_id="ev:personality:conflict_a",
            domain=Domain.PERSONALITY,
            conclusion="性格刚毅",
            confidence=0.9,
            system="bazi",
            items=all_evidence[0].items if all_evidence else [],
        ),
        Evidence(
            evidence_id="ev:personality:conflict_b",
            domain=Domain.PERSONALITY,
            conclusion="性格柔顺",
            confidence=0.8,
            system="ziwei",
            items=all_evidence[0].items if all_evidence else [],
        ),
    ]
    report4 = builder.build(
        ConsensusInput(
            evidence=conflict_evidence,
            config=ConsensusConfig(strategy=ConsensusStrategy.RETAIN_ALL),
        )
    )
    golden.append(
        {
            "name": "conflict_retain_all",
            "description": "Two conflicting conclusions in personality domain, retain_all keeps both.",
            "input_type": "conflict",
            "report": report4.model_dump(mode="json"),
        }
    )

    # Example 5: Conflict with highest_confidence
    report5 = builder.build(
        ConsensusInput(
            evidence=conflict_evidence,
            config=ConsensusConfig(strategy=ConsensusStrategy.HIGHEST_CONFIDENCE),
        )
    )
    golden.append(
        {
            "name": "conflict_highest_confidence",
            "description": "Same conflict, highest_confidence keeps only the stronger conclusion.",
            "input_type": "conflict",
            "report": report5.model_dump(mode="json"),
        }
    )

    # Example 6: Empty input
    report6 = builder.build(ConsensusInput(evidence=[]))
    golden.append(
        {
            "name": "empty_input",
            "description": "Empty Evidence list produces an empty report.",
            "input_type": "empty",
            "report": report6.model_dump(mode="json"),
        }
    )

    return golden


def export_consensus_contract(
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Export the Consensus Layer contract from golden examples.

    Auto-generated by running the Reference Runtime. NOT hand-written.
    """
    golden = _build_golden_examples()

    contract: dict[str, Any] = {
        "contract_name": "consensus",
        "contract_version": "1.0.0",
        "description": (
            "Reference Runtime Consensus Layer Contract. "
            "Generated from golden examples. "
            "All future implementations must conform to this contract."
        ),
        "generated_by": "reference.consensus_builder.export_consensus_contract",
        "strategies": [s.value for s in ConsensusStrategy],
        "models": {
            "ConsensusInput": {
                "type": "object",
                "required": ["evidence", "config"],
                "field_types": {
                    "evidence": "array<Evidence>",
                    "config": "ConsensusConfig",
                },
            },
            "ConsensusConfig": {
                "type": "object",
                "required": ["strategy"],
                "field_types": {
                    "strategy": "enum (retain_all|highest_confidence|majority)",
                    "cross_system_bonus_per_system": "number [0,1]",
                    "max_cross_system_bonus": "number [0,1]",
                    "min_confidence": "number [0,1]",
                    "max_confidence": "number [0,1]",
                },
            },
            "ConsensusConclusion": {
                "type": "object",
                "required": [
                    "conclusion_id",
                    "domain",
                    "conclusion",
                    "confidence",
                    "evidence_ids",
                    "evidence_count",
                    "systems",
                    "is_conflict",
                    "strategy",
                    "metadata",
                    "version",
                ],
                "optional": ["direction"],
                "field_types": {
                    "conclusion_id": "string (pattern: cc:<domain>:<hash>)",
                    "domain": "enum (10 values)",
                    "conclusion": "string",
                    "confidence": "number [0,1]",
                    "evidence_ids": "array<string>",
                    "evidence_count": "integer",
                    "systems": "array<string>",
                    "direction": "enum | null",
                    "is_conflict": "boolean",
                    "strategy": "enum",
                    "metadata": "object",
                    "version": "string",
                },
            },
            "ConsensusReport": {
                "type": "object",
                "required": [
                    "report_id",
                    "overall_confidence",
                    "domains",
                    "conclusions",
                    "conflicts",
                    "evidence_ids",
                    "metadata",
                    "version",
                ],
                "field_types": {
                    "report_id": "string (pattern: cr:<hash>)",
                    "overall_confidence": "number [0,1]",
                    "domains": "array<enum>",
                    "conclusions": "array<ConsensusConclusion>",
                    "conflicts": "array<ConsensusConclusion>",
                    "evidence_ids": "array<string>",
                    "metadata": "object",
                    "version": "string",
                },
            },
        },
        "golden_examples": golden,
    }

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(contract, f, ensure_ascii=False, indent=2, sort_keys=True)

    return contract
