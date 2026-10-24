"""Reference Pattern Matcher -- Phase 6B Sprint 2.

Evaluates whether Patterns are satisfied by RuleEvaluations.

Supports four matching modes:
  1. Single Rule: one RuleEvaluation triggers a Pattern
  2. Multi Rule:  multiple RuleEvaluations must all match
  3. Cross System: evaluations from multiple Systems combine
  4. No Match:    pattern requirements not satisfied

See: docs/design/phase6/07_adr.md (ADR-004)
     docs/design/phase6/06_flow_diagram.md (Pattern matching flow)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .engine import RuleEngine
from .models import RuleEvaluation
from .parser import parse_rule_file
from .patterns import (
    Pattern,
    PatternCategory,
    PatternEvidence,
    PatternMatch,
    PatternRequirement,
    RequirementLogic,
    parse_pattern_file,
)


class PatternMatcher:
    """Matches Pattern definitions against RuleEvaluation results.

    Deterministic: same Pattern + same evaluations always produce
    the same PatternMatch (or None).
    """

    CONTRACT_VERSION = "1.0.0"

    def match(
        self,
        pattern: Pattern,
        evaluations: list[RuleEvaluation],
        system: str = "reference",
    ) -> PatternMatch | None:
        """Try to match a single pattern against evaluations from one system.

        Returns PatternMatch(matched=True) if requirements are satisfied,
        PatternMatch(matched=False) if the pattern is referenced but not
        fully satisfied, or None if no related rules are in evaluations.
        """
        matched_rule_ids = {ev.rule_id for ev in evaluations if ev.matched}
        all_evaluated_ids = {ev.rule_id for ev in evaluations}

        # Check if any pattern rules are present in evaluations at all
        pattern_rule_set = set(pattern.rule_ids)
        for req in pattern.requirements:
            pattern_rule_set.update(req.rule_ids)
        relevant_ids = pattern_rule_set & all_evaluated_ids
        if not relevant_ids:
            return None

        # Check requirements
        requirements_met = self._check_requirements(pattern, matched_rule_ids)

        # Build evidence from all relevant evaluations
        evidence = self._build_evidence(pattern, evaluations, system)

        actual_matched = sorted(rid for rid in matched_rule_ids if rid in pattern_rule_set)

        return PatternMatch(
            pattern_id=pattern.pattern_id,
            pattern_name=pattern.name,
            matched=requirements_met,
            matched_by=system,
            confidence=pattern.confidence if requirements_met else 0.0,
            matched_rule_ids=actual_matched,
            evidence=evidence,
            knowledge_node_ids=list(pattern.knowledge_node_ids),
            category=pattern.category,
        )

    def match_all(
        self,
        patterns: list[Pattern],
        evaluations: list[RuleEvaluation],
        system: str = "reference",
    ) -> list[PatternMatch]:
        """Match multiple patterns against evaluations from one system.

        Returns only PatternMatches where matched=True.
        """
        results: list[PatternMatch] = []
        for pattern in patterns:
            pm = self.match(pattern, evaluations, system)
            if pm is not None and pm.matched:
                results.append(pm)
        return results

    def match_all_with_misses(
        self,
        patterns: list[Pattern],
        evaluations: list[RuleEvaluation],
        system: str = "reference",
    ) -> list[PatternMatch]:
        """Like match_all but also includes non-matched patterns.

        Useful for debugging: shows which patterns were considered
        but did not fully match.
        """
        results: list[PatternMatch] = []
        for pattern in patterns:
            pm = self.match(pattern, evaluations, system)
            if pm is not None:
                results.append(pm)
        return results

    def match_cross_system(
        self,
        pattern: Pattern,
        evaluations_by_system: dict[str, list[RuleEvaluation]],
    ) -> PatternMatch | None:
        """Match a cross-system pattern against evaluations from multiple systems.

        Args:
            pattern: Pattern with category=cross_system or systems spanning
                     multiple values.
            evaluations_by_system: dict mapping system name to its evaluations.

        Returns:
            PatternMatch if matched, None if no relevant rules found.
        """
        combined: list[RuleEvaluation] = []
        evidence: list[PatternEvidence] = []

        for sys_name, evals in evaluations_by_system.items():
            combined.extend(evals)
            for ev in evals:
                if ev.rule_id in set(pattern.rule_ids):
                    evidence.append(
                        PatternEvidence(
                            rule_id=ev.rule_id,
                            system=sys_name,
                            matched=ev.matched,
                            conclusions=[r.conclusion for r in ev.results],
                        )
                    )

        matched_rule_ids = {ev.rule_id for ev in combined if ev.matched}
        all_evaluated_ids = {ev.rule_id for ev in combined}

        pattern_rule_set = set(pattern.rule_ids)
        for req in pattern.requirements:
            pattern_rule_set.update(req.rule_ids)
        if not (pattern_rule_set & all_evaluated_ids):
            return None

        requirements_met = self._check_requirements(pattern, matched_rule_ids)

        actual_matched = sorted(rid for rid in matched_rule_ids if rid in pattern_rule_set)

        return PatternMatch(
            pattern_id=pattern.pattern_id,
            pattern_name=pattern.name,
            matched=requirements_met,
            matched_by="cross_system",
            confidence=pattern.confidence if requirements_met else 0.0,
            matched_rule_ids=actual_matched,
            evidence=evidence,
            knowledge_node_ids=list(pattern.knowledge_node_ids),
            category=pattern.category,
        )

    # ── Internal helpers ───────────────────────────────────────────

    def _check_requirements(
        self,
        pattern: Pattern,
        matched_rule_ids: set[str],
    ) -> bool:
        """Check if all pattern requirements are satisfied."""
        if not pattern.requirements:
            # No explicit requirements: at least one rule must match
            return bool(matched_rule_ids & set(pattern.rule_ids))

        for req in pattern.requirements:
            if not self._check_requirement(req, matched_rule_ids):
                return False
        return True

    def _check_requirement(
        self,
        req: PatternRequirement,
        matched_rule_ids: set[str],
    ) -> bool:
        """Check a single requirement."""
        req_matched = matched_rule_ids & set(req.rule_ids)

        if req.logic == RequirementLogic.ALL:
            return len(req_matched) == len(req.rule_ids)
        if req.logic == RequirementLogic.ANY:
            return len(req_matched) >= req.min_matches
        return False

    def _build_evidence(
        self,
        pattern: Pattern,
        evaluations: list[RuleEvaluation],
        system: str,
    ) -> list[PatternEvidence]:
        """Build evidence list from evaluations referencing pattern rules."""
        pattern_rules = set(pattern.rule_ids)
        evidence: list[PatternEvidence] = []

        for ev in evaluations:
            if ev.rule_id in pattern_rules:
                evidence.append(
                    PatternEvidence(
                        rule_id=ev.rule_id,
                        system=system,
                        matched=ev.matched,
                        conclusions=[r.conclusion for r in ev.results],
                    )
                )

        return evidence


# ── Pattern Layer Contract ─────────────────────────────────────────

CONTRACT_PATH = Path(__file__).parent / "contracts" / "pattern_contract.json"


def _dump_match(match: PatternMatch | None) -> dict[str, Any] | None:
    return match.model_dump(mode="json") if match is not None else None


def _build_golden_examples() -> list[dict[str, Any]]:
    """Run the Pattern layer on the golden example patterns and charts."""
    matcher = PatternMatcher()
    engine = RuleEngine()
    examples_dir = Path(__file__).parent / "examples"
    patterns_dir = examples_dir / "patterns"

    chart_full = {
        "ten_gods_map": {"values": ["伤官", "正印"]},
        "day_master_strength": 0.35,
        "shen_sha_list": ["羊刃", "天乙贵人"],
    }
    chart_cai = {
        "ten_gods_map": {"values": ["正财", "伤官", "正印"]},
        "day_master_strength": 0.35,
        "shen_sha_list": ["羊刃", "天乙贵人"],
    }
    chart_qimen = {"dun_type": "yang", "ju": 6}

    def rule_evals(rule_files: list[str], chart: dict) -> list[RuleEvaluation]:
        out: list[RuleEvaluation] = []
        for name in rule_files:
            out.extend(engine.evaluate_all(parse_rule_file(str(examples_dir / name)), chart))
        return out

    def example(
        name: str,
        description: str,
        pattern_file: str,
        evaluations: list[RuleEvaluation],
        *,
        cross_system: dict[str, list[RuleEvaluation]] | None = None,
    ) -> dict[str, Any]:
        pattern = parse_pattern_file(str(patterns_dir / pattern_file))
        if cross_system is not None:
            match = matcher.match_cross_system(pattern, cross_system)
            mode = "cross_system"
            dumped = {
                system: [ev.model_dump(mode="json") for ev in evals]
                for system, evals in cross_system.items()
            }
        else:
            match = matcher.match(pattern, evaluations, "bazi")
            mode = "single_system"
            dumped = [ev.model_dump(mode="json") for ev in evaluations]
        return {
            "name": name,
            "description": description,
            "input": {
                "pattern_file": pattern_file,
                "mode": mode,
                "evaluations": dumped,
            },
            "match": _dump_match(match),
        }

    return [
        example(
            "single_rule_match",
            "One matched rule satisfies the pattern requirement.",
            "01_single_rule.yaml",
            rule_evals(["01_single_condition.yaml"], chart_full),
        ),
        example(
            "multi_rule_match",
            "Three matched rules satisfy an ALL requirement.",
            "02_multi_rule.yaml",
            rule_evals(
                [
                    "07_has_shang_guan.yaml",
                    "08_has_zheng_yin.yaml",
                    "09_weak_day_master.yaml",
                ],
                chart_full,
            ),
        ),
        example(
            "any_logic_match",
            "An ANY requirement with min_matches=1 matches via DNF expansion.",
            "03_any_logic.yaml",
            rule_evals(["03_or.yaml"], chart_cai),
        ),
        example(
            "cross_system_match",
            "A cross-system pattern matches bazi + qimen evaluations.",
            "04_cross_system.yaml",
            [],
            cross_system={
                "bazi": rule_evals(["01_single_condition.yaml"], chart_full),
                "qimen": rule_evals(["05_scope.yaml"], chart_qimen),
            },
        ),
        example(
            "pattern_not_triggered",
            "A referenced pattern whose requirement is not satisfied returns matched=false.",
            "05_no_match.yaml",
            rule_evals(["04_not.yaml"], chart_full),
        ),
        example(
            "unrelated_evaluations_none",
            "Evaluations without any pattern rule yield no PatternMatch (null).",
            "01_single_rule.yaml",
            rule_evals(["03_or.yaml"], chart_cai),
        ),
    ]


def export_pattern_contract(output_path: str | Path | None = None) -> dict[str, Any]:
    """Export the Pattern Layer contract from golden examples.

    Auto-generated by running the Reference Runtime. NOT hand-written.
    """
    contract: dict[str, Any] = {
        "contract_name": "pattern",
        "contract_version": PatternMatcher.CONTRACT_VERSION,
        "description": (
            "Reference Runtime Pattern Layer Contract. "
            "Generated from golden examples. "
            "All future implementations must conform to this contract."
        ),
        "generated_by": "reference.pattern_matcher.export_pattern_contract",
        "categories": [c.value for c in PatternCategory],
        "requirement_logic": [logic.value for logic in RequirementLogic],
        "models": {
            "PatternRequirement": {
                "type": "object",
                "required": ["rule_ids"],
                "optional": ["logic", "min_matches"],
                "field_types": {
                    "rule_ids": "array<string> (min_length=1)",
                    "logic": "enum",
                    "min_matches": "integer >= 1",
                },
            },
            "PatternEvidence": {
                "type": "object",
                "required": ["rule_id", "system", "matched", "conclusions"],
                "field_types": {
                    "rule_id": "string",
                    "system": "string",
                    "matched": "boolean",
                    "conclusions": "array<string>",
                },
            },
            "PatternMatch": {
                "type": "object",
                "required": [
                    "pattern_id",
                    "pattern_name",
                    "matched",
                    "matched_by",
                    "confidence",
                    "matched_rule_ids",
                    "evidence",
                    "knowledge_node_ids",
                ],
                "optional": ["category"],
                "field_types": {
                    "pattern_id": "string",
                    "pattern_name": "string",
                    "matched": "boolean",
                    "matched_by": "string",
                    "confidence": "number [0,1]",
                    "matched_rule_ids": "array<string>",
                    "evidence": "array<PatternEvidence>",
                    "knowledge_node_ids": "array<string>",
                    "category": "enum | null",
                },
            },
        },
        "golden_examples": _build_golden_examples(),
    }

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        out.write_text(text, encoding="utf-8", newline="\n")

    return contract
