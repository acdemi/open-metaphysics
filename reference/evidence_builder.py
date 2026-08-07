"""Reference Evidence Builder -- Phase 6B Sprint 3.

Converts RuleEvaluation and PatternMatch into EvidenceItem / Evidence.

This is the integration point where the Rule layer and Pattern layer
meet the Evidence layer. After conversion, downstream consumers
(Consensus Engine) only see Evidence -- never RuleEvaluation or
PatternMatch.

    RuleEvaluation[]  -->  EvidenceItem[]  -->  Evidence[]
    PatternMatch[]    -->  EvidenceItem[]  -->  Evidence[]

Knowledge conversion is NOT implemented. The ``KnowledgeEvidenceProvider``
protocol in ``evidence.py`` defines the future interface.

Contract export:
    ``export_evidence_contract()`` runs the Reference Runtime on golden
    examples and produces ``reference/contracts/evidence_contract.json``.
    This file is an Architecture Contract, not test data. All future
    implementations (Rust, Go, Python AI Layer) must conform to it.

See: docs/design/phase6/06_flow_diagram.md
     docs/design/phase6/09_test_plan.md (Evidence builder tests)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .evidence import (
    Evidence,
    EvidenceItem,
    EvidenceSource,
    EvidenceType,
    make_evidence_group_id,
    make_evidence_item_id,
)
from .models import Domain, Rule, RuleEvaluation
from .patterns import PatternCategory, PatternMatch

# == Category -> Domain mapping ==

_CATEGORY_DOMAIN_MAP: dict[PatternCategory, Domain] = {
    PatternCategory.PERSONALITY: Domain.PERSONALITY,
    PatternCategory.CAREER: Domain.CAREER,
    PatternCategory.GEJU: Domain.OVERALL,
    PatternCategory.SHENSHA: Domain.OVERALL,
    PatternCategory.RELATION: Domain.OVERALL,
    PatternCategory.WUXING: Domain.OVERALL,
    PatternCategory.CROSS_SYSTEM: Domain.OVERALL,
}


def category_to_domain(category: PatternCategory | None) -> Domain:
    """Map a PatternCategory to a Domain. Defaults to OVERALL."""
    if category is None:
        return Domain.OVERALL
    return _CATEGORY_DOMAIN_MAP.get(category, Domain.OVERALL)


# == EvidenceBuilder ==


class EvidenceBuilder:
    """Builds Evidence from RuleEvaluation and PatternMatch.

    Deterministic: same inputs always produce identical Evidence.
    Pure: no I/O (except contract export), no side effects, no LLM.
    """

    CONTRACT_VERSION = "1.0.0"

    # -- RuleEvaluation -> EvidenceItem --

    def from_rule_evaluation(
        self,
        evaluation: RuleEvaluation,
        system: str,
        rule: Rule | None = None,
    ) -> list[EvidenceItem]:
        """Convert a single RuleEvaluation to EvidenceItems.

        A matched rule with N results produces N EvidenceItems
        (one per conclusion). Non-matched rules produce nothing.

        Args:
            evaluation: The RuleEvaluation to convert.
            system: The metaphysics system (e.g. "bazi").
            rule: Optional Rule for source enrichment (name, citation).
                  If None, source_name falls back to the rule_id.
        """
        if not evaluation.matched:
            return []

        items: list[EvidenceItem] = []
        for index, result in enumerate(evaluation.results):
            source_name = rule.name if rule is not None else evaluation.rule_id
            source_ref = rule.source.text if rule is not None else ""
            credibility = rule.source.credibility if rule is not None else 0.8

            trace: list[str] = [evaluation.rule_id]
            if result.conclusion_node_id:
                trace.append(result.conclusion_node_id)

            item = EvidenceItem(
                evidence_id=make_evidence_item_id(
                    EvidenceType.RULE.value,
                    evaluation.rule_id,
                    system,
                    result.conclusion,
                    index,
                ),
                source_type=EvidenceType.RULE,
                source_id=evaluation.rule_id,
                system=system,
                domain=result.domain,
                confidence=evaluation.confidence,
                conclusion=result.conclusion,
                direction=result.direction,
                weight=result.weight,
                trace=trace,
                metadata={
                    "source_name": source_name,
                    "source_ref": source_ref,
                    "credibility": credibility,
                    "priority": evaluation.priority,
                    "conclusion_node_id": result.conclusion_node_id,
                    "result_index": index,
                },
                version=self.CONTRACT_VERSION,
            )
            items.append(item)

        return items

    def from_rule_evaluations(
        self,
        evaluations: list[RuleEvaluation],
        system: str,
        rules: dict[str, Rule] | None = None,
    ) -> list[EvidenceItem]:
        """Convert multiple RuleEvaluations to EvidenceItems."""
        items: list[EvidenceItem] = []
        for ev in evaluations:
            rule = rules.get(ev.rule_id) if rules else None
            items.extend(self.from_rule_evaluation(ev, system, rule))
        return items

    # -- PatternMatch -> EvidenceItem --

    def from_pattern_match(
        self,
        match: PatternMatch,
    ) -> EvidenceItem | None:
        """Convert a PatternMatch to an EvidenceItem.

        Returns None if the pattern did not match.
        Only matched patterns produce evidence.
        """
        if not match.matched:
            return None

        domain = category_to_domain(match.category)
        trace: list[str] = [match.pattern_id]
        trace.extend(sorted(match.matched_rule_ids))
        trace.extend(sorted(match.knowledge_node_ids))

        return EvidenceItem(
            evidence_id=make_evidence_item_id(
                EvidenceType.PATTERN.value,
                match.pattern_id,
                match.matched_by,
                match.pattern_name,
            ),
            source_type=EvidenceType.PATTERN,
            source_id=match.pattern_id,
            system=match.matched_by,
            domain=domain,
            confidence=match.confidence,
            conclusion=match.pattern_name,
            direction=None,
            weight=match.confidence,
            trace=trace,
            metadata={
                "source_name": match.pattern_name,
                "category": match.category.value if match.category else None,
                "matched_rule_count": len(match.matched_rule_ids),
                "evidence_count": len(match.evidence),
                "knowledge_node_ids": list(match.knowledge_node_ids),
            },
            version=self.CONTRACT_VERSION,
        )

    def from_pattern_matches(
        self,
        matches: list[PatternMatch],
    ) -> list[EvidenceItem]:
        """Convert multiple PatternMatches to EvidenceItems."""
        items: list[EvidenceItem] = []
        for match in matches:
            item = self.from_pattern_match(match)
            if item is not None:
                items.append(item)
        return items

    # -- Grouping into Evidence --

    def build_from_evaluations(
        self,
        evaluations: list[RuleEvaluation],
        system: str,
        rules: dict[str, Rule] | None = None,
    ) -> list[Evidence]:
        """Convert RuleEvaluations to grouped Evidence list."""
        items = self.from_rule_evaluations(evaluations, system, rules)
        return self._group_into_evidence(items)

    def build_from_pattern_matches(
        self,
        matches: list[PatternMatch],
    ) -> list[Evidence]:
        """Convert PatternMatches to grouped Evidence list."""
        items = self.from_pattern_matches(matches)
        return self._group_into_evidence(items)

    def build_all(
        self,
        evaluations: list[RuleEvaluation],
        matches: list[PatternMatch],
        system: str,
        rules: dict[str, Rule] | None = None,
    ) -> list[Evidence]:
        """Convert both RuleEvaluations and PatternMatches to Evidence."""
        items = self.from_rule_evaluations(evaluations, system, rules)
        items.extend(self.from_pattern_matches(matches))
        return self._group_into_evidence(items)

    # -- Internal: grouping --

    @staticmethod
    def _group_into_evidence(
        items: list[EvidenceItem],
    ) -> list[Evidence]:
        """Group EvidenceItems by (domain, conclusion) into Evidence.

        Items sharing the same domain and conclusion are bundled into
        one Evidence. The group confidence is the max of item
        confidences (final aggregation is the Consensus Engine's job).
        """
        if not items:
            return []

        groups: dict[tuple[str, str], list[EvidenceItem]] = {}
        for item in items:
            key = (item.domain.value, item.conclusion)
            groups.setdefault(key, []).append(item)

        result: list[Evidence] = []
        for (domain_val, conclusion), group_items in sorted(
            groups.items(), key=lambda kv: (kv[0][0], kv[0][1])
        ):
            item_ids = sorted(i.evidence_id for i in group_items)
            group_id = make_evidence_group_id(domain_val, conclusion, item_ids)
            max_confidence = max(i.confidence for i in group_items)
            systems = sorted({i.system for i in group_items})
            primary_system = systems[0] if len(systems) == 1 else "multi"

            result.append(
                Evidence(
                    evidence_id=group_id,
                    domain=Domain(domain_val),
                    conclusion=conclusion,
                    confidence=max_confidence,
                    system=primary_system,
                    items=group_items,
                    version=EvidenceBuilder.CONTRACT_VERSION,
                )
            )

        return result

    # -- Source enrichment helpers --

    @staticmethod
    def source_from_rule(rule: Rule) -> EvidenceSource:
        """Build an EvidenceSource from a Rule's SourceRef."""
        return EvidenceSource(
            source_type=EvidenceType.RULE,
            source_id=rule.id,
            source_name=rule.name,
            source_ref=rule.source.text,
            credibility=rule.source.credibility,
        )

    @staticmethod
    def source_from_pattern(match: PatternMatch) -> EvidenceSource:
        """Build an EvidenceSource from a PatternMatch."""
        return EvidenceSource(
            source_type=EvidenceType.PATTERN,
            source_id=match.pattern_id,
            source_name=match.pattern_name,
            source_ref="",
            credibility=match.confidence,
        )


# == Contract Export ==

CONTRACT_PATH = Path(__file__).parent / "contracts" / "evidence_contract.json"


def _build_golden_examples(builder: EvidenceBuilder) -> list[dict[str, Any]]:
    """Build golden examples by running the Reference Runtime.

    These are real runtime outputs, not hand-written fixtures.
    """
    from .engine import RuleEngine
    from .parser import parse_rule_file
    from .pattern_matcher import PatternMatcher
    from .patterns import parse_pattern_file

    examples_dir = Path(__file__).parent / "examples"
    pat_dir = examples_dir / "patterns"
    engine = RuleEngine()
    matcher = PatternMatcher()

    chart_with_seal = {
        "ten_gods_map": {"values": ["伤官", "正印", "比肩"]},
        "day_master_strength": 0.35,
        "shen_sha_list": ["羊刃", "天乙贵人"],
    }
    chart_no_yang_ren = {
        "ten_gods_map": {"values": ["正官"]},
        "day_master_strength": 0.7,
        "shen_sha_list": ["天乙贵人"],
    }
    chart_qimen = {"dun_type": "yang", "ju": 6}

    golden: list[dict[str, Any]] = []

    # Example 1: Single rule -> Evidence
    rules = parse_rule_file(str(examples_dir / "01_single_condition.yaml"))
    evals = engine.evaluate_all(rules, chart_with_seal)
    evidence = builder.build_from_evaluations(evals, "bazi")
    golden.append(
        {
            "name": "single_rule_to_evidence",
            "description": "A single matched rule produces Evidence with one item.",
            "input_type": "rule_evaluation",
            "evidence": [e.model_dump(mode="json") for e in evidence],
        }
    )

    # Example 2: Multi-rule pattern -> Evidence
    multi_rules: list[Rule] = []
    for fname in [
        "07_has_shang_guan.yaml",
        "08_has_zheng_yin.yaml",
        "09_weak_day_master.yaml",
    ]:
        multi_rules.extend(parse_rule_file(str(examples_dir / fname)))
    multi_evals = engine.evaluate_all(multi_rules, chart_with_seal)
    pattern = parse_pattern_file(str(pat_dir / "02_multi_rule.yaml"))
    pm = matcher.match(pattern, multi_evals, "bazi")
    pattern_evidence = builder.build_from_pattern_matches([pm])
    golden.append(
        {
            "name": "multi_rule_pattern_to_evidence",
            "description": "Three matched rules trigger a pattern, producing pattern Evidence.",
            "input_type": "pattern_match",
            "evidence": [e.model_dump(mode="json") for e in pattern_evidence],
        }
    )

    # Example 3: Combined rule + pattern -> Evidence
    combined_evals = (
        engine.evaluate_all(
            parse_rule_file(str(examples_dir / "01_single_condition.yaml")),
            chart_with_seal,
        )
        + multi_evals
    )
    pattern1 = parse_pattern_file(str(pat_dir / "01_single_rule.yaml"))
    pm1 = matcher.match(pattern1, combined_evals, "bazi")
    combined_evidence = builder.build_all(combined_evals, [pm1, pm], "bazi")
    golden.append(
        {
            "name": "combined_rule_pattern_evidence",
            "description": "Rules and patterns combined produce grouped Evidence.",
            "input_type": "combined",
            "evidence": [e.model_dump(mode="json") for e in combined_evidence],
        }
    )

    # Example 4: Cross-system -> Evidence
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
    cross_evidence = builder.build_from_pattern_matches([cross_pm])
    golden.append(
        {
            "name": "cross_system_evidence",
            "description": "A cross-system pattern produces Evidence spanning bazi + qimen.",
            "input_type": "pattern_match",
            "evidence": [e.model_dump(mode="json") for e in cross_evidence],
        }
    )

    # Example 5: Non-matched rule -> no evidence
    no_match_evals = engine.evaluate_all(
        parse_rule_file(str(examples_dir / "01_single_condition.yaml")),
        chart_no_yang_ren,
    )
    no_match_evidence = builder.build_from_evaluations(no_match_evals, "bazi")
    golden.append(
        {
            "name": "no_match_no_evidence",
            "description": "A non-matched rule produces no Evidence (empty list).",
            "input_type": "rule_evaluation",
            "evidence": [e.model_dump(mode="json") for e in no_match_evidence],
        }
    )

    return golden


def export_evidence_contract(
    builder: EvidenceBuilder | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Export the Evidence Layer contract from golden examples.

    The contract is generated by running the Reference Runtime on
    golden examples. It is NOT hand-written. It serves as the
    Architecture Contract for all future implementations (Rust, Go,
    Python AI Layer). Any implementation whose output violates this
    contract is considered a bug.

    Args:
        builder: EvidenceBuilder instance (default: new instance).
        output_path: Path to write the contract JSON. If provided,
                     writes the file; always returns the dict.
    """
    if builder is None:
        builder = EvidenceBuilder()

    golden = _build_golden_examples(builder)

    contract: dict[str, Any] = {
        "contract_name": "evidence",
        "contract_version": EvidenceBuilder.CONTRACT_VERSION,
        "description": (
            "Reference Runtime Evidence Layer Contract. "
            "Generated from golden examples. "
            "All future implementations must conform to this contract."
        ),
        "generated_by": "reference.evidence_builder.export_evidence_contract",
        "evidence_types": [e.value for e in EvidenceType],
        "domains": [d.value for d in Domain],
        "models": {
            "EvidenceItem": {
                "type": "object",
                "required": [
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
                ],
                "optional": ["direction", "weight", "timestamp"],
                "field_types": {
                    "evidence_id": "string",
                    "source_type": "enum",
                    "source_id": "string",
                    "system": "string",
                    "domain": "enum",
                    "confidence": "number [0,1]",
                    "conclusion": "string",
                    "direction": "enum | null",
                    "weight": "number [0,1]",
                    "trace": "array<string>",
                    "metadata": "object",
                    "timestamp": "string | null",
                    "version": "string",
                },
            },
            "Evidence": {
                "type": "object",
                "required": [
                    "evidence_id",
                    "domain",
                    "conclusion",
                    "confidence",
                    "system",
                    "items",
                    "version",
                ],
                "field_types": {
                    "evidence_id": "string",
                    "domain": "enum",
                    "conclusion": "string",
                    "confidence": "number [0,1]",
                    "system": "string",
                    "items": "array<EvidenceItem>",
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
