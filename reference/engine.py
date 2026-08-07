"""Reference Rule Engine -- evaluates Rules against chart data.

Pure deterministic: same input always produces same output.
No I/O, no LLM, no side effects.

See: docs/design/phase6/02_rule_layer_architecture.md
"""

from __future__ import annotations

import re
from typing import Any

from .models import Rule, RuleEvaluation

# ── Field path resolution ──────────────────────────────────────────


def resolve_field(data: dict, path: str) -> Any:
    """Resolve a dotted path with index support against chart data.

    Examples:
      "day_master_strength"           -> data["day_master_strength"]
      "ten_gods_map.values"           -> data["ten_gods_map"]["values"]
      "pillars[0].ten_gods_stem"      -> data["pillars"][0]["ten_gods_stem"]
    """
    current: Any = data
    # Split on dots, but handle [N] index syntax within segments
    for segment in path.split("."):
        # Extract index if present, e.g. "pillars[0]" -> "pillars", 0
        match = re.match(r"^(\w+)(\[\d+\])*$", segment)
        if match:
            key = match.group(1)
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                raise KeyError(f"Field not found: {key} in path {path}")
            # Apply indices
            for idx_match in re.finditer(r"\[(\d+)\]", segment):
                idx = int(idx_match.group(1))
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    raise IndexError(f"Index {idx} out of range in path {path}")
        else:
            raise ValueError(f"Invalid path segment: {segment}")
    return current


def field_exists(data: dict, path: str) -> bool:
    """Check if a field path exists in the data."""
    try:
        resolve_field(data, path)
        return True
    except (KeyError, IndexError):
        return False


# ── Operator evaluation ────────────────────────────────────────────


def _apply_operator(operator: str, actual: Any, expected: Any) -> bool:
    """Apply a single operator comparison."""
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    if operator == "contains":
        if actual is None:
            return False
        return expected in actual
    if operator == "not_contains":
        if actual is None:
            return True
        return expected not in actual
    if operator == "in":
        return actual in expected
    if operator == "not_in":
        return actual not in expected
    if operator == "greater_than":
        return actual > expected
    if operator == "less_than":
        return actual < expected
    if operator == "matches":
        return re.search(expected, str(actual)) is not None
    raise ValueError(f"Unknown operator: {operator}")


def _eval_condition(condition, data: dict) -> bool:
    """Evaluate a single RuleCondition against chart data."""
    op = condition.operator.value
    negate = condition.negate

    if op == "exists":
        result = field_exists(data, condition.field)
    elif op == "not_exists":
        result = not field_exists(data, condition.field)
    else:
        actual = resolve_field(data, condition.field)
        result = _apply_operator(op, actual, condition.value)

    return (not result) if negate else result


# ── RuleEngine ─────────────────────────────────────────────────────


class RuleEngine:
    """Evaluates Rules against chart data.

    All conditions in a Rule are ANDed (they must all match).
    This is by design: 'any:' (OR) is expanded to multiple Rules
    by the DSL parser, so each Rule has only AND conditions.
    """

    def evaluate(self, rule: Rule, data: dict) -> RuleEvaluation:
        """Evaluate a single rule against chart data.

        Args:
            rule: The Rule to evaluate.
            data: Chart data dict (e.g. BaziChart fields).

        Returns:
            RuleEvaluation with matched=True if all conditions pass.
        """
        all_match = all(_eval_condition(cond, data) for cond in rule.conditions)

        if all_match:
            return RuleEvaluation(
                rule_id=rule.id,
                matched=True,
                results=list(rule.results),
                priority=rule.priority,
                confidence=rule.confidence,
            )

        return RuleEvaluation(
            rule_id=rule.id,
            matched=False,
            results=[],
            priority=rule.priority,
            confidence=rule.confidence,
        )

    def evaluate_all(self, rules: list[Rule], data: dict) -> list[RuleEvaluation]:
        """Evaluate multiple rules against the same chart data."""
        return [self.evaluate(rule, data) for rule in rules]

    def evaluate_matched(self, rules: list[Rule], data: dict) -> list[RuleEvaluation]:
        """Evaluate rules and return only matched evaluations."""
        return [ev for ev in self.evaluate_all(rules, data) if ev.matched]
