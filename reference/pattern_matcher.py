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

from .models import RuleEvaluation
from .patterns import (
    Pattern,
    PatternEvidence,
    PatternMatch,
    PatternRequirement,
    RequirementLogic,
)


class PatternMatcher:
    """Matches Pattern definitions against RuleEvaluation results.

    Deterministic: same Pattern + same evaluations always produce
    the same PatternMatch (or None).
    """

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
