"""Reference Rule Engine -- evaluates Rules against chart data.

Pure deterministic: same input always produces same output.
No I/O, no LLM, no side effects.

See: docs/design/phase6/02_rule_layer_architecture.md
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .models import (
    ConditionOperator,
    ConflictStrategy,
    Rule,
    RuleEvaluation,
    RuleType,
)
from .parser import parse_rule_file

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

    CONTRACT_VERSION = "1.0.0"

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


# ── Rule Layer Contract ────────────────────────────────────────────

CONTRACT_PATH = Path(__file__).parent / "contracts" / "rule_contract.json"


def _build_golden_examples() -> list[dict[str, Any]]:
    """Run the Rule layer on the golden example rules and charts."""
    engine = RuleEngine()
    examples_dir = Path(__file__).parent / "examples"

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
    chart_no_yin = {
        "ten_gods_map": {"values": ["伤官"]},
        "day_master_strength": 0.35,
        "shen_sha_list": ["羊刃"],
    }
    chart_complex = {
        "ten_gods_map": {"values": ["正官"]},
        "day_master_strength": 0.35,
        "shen_sha_list": [],
    }
    chart_qimen = {"dun_type": "yang", "ju": 6}
    chart_no_match = {
        "ten_gods_map": {"values": ["正印"]},
        "day_master_strength": 0.8,
        "shen_sha_list": [],
    }

    def run(rule_file: str, chart: dict) -> list[dict[str, Any]]:
        rules = parse_rule_file(str(examples_dir / rule_file))
        return [ev.model_dump(mode="json") for ev in engine.evaluate_all(rules, chart)]

    return [
        {
            "name": "single_condition_matched",
            "description": "A single condition matches and emits its declared results.",
            "input": {"rule_file": "01_single_condition.yaml", "chart": chart_full},
            "evaluations": run("01_single_condition.yaml", chart_full),
        },
        {
            "name": "all_conditions_matched",
            "description": "All conditions of an 'all' rule match.",
            "input": {"rule_file": "02_and.yaml", "chart": chart_full},
            "evaluations": run("02_and.yaml", chart_full),
        },
        {
            "name": "any_dnf_expansion",
            "description": "An 'any' rule expands to two DNF rules; one matches.",
            "input": {"rule_file": "03_or.yaml", "chart": chart_cai},
            "evaluations": run("03_or.yaml", chart_cai),
        },
        {
            "name": "not_negation",
            "description": "A negated leaf condition matches when the field is absent.",
            "input": {"rule_file": "04_not.yaml", "chart": chart_no_yin},
            "evaluations": run("04_not.yaml", chart_no_yin),
        },
        {
            "name": "scope_qimen",
            "description": "A scoped rule evaluates against Qimen chart data.",
            "input": {"rule_file": "05_scope.yaml", "chart": chart_qimen},
            "evaluations": run("05_scope.yaml", chart_qimen),
        },
        {
            "name": "complex_nested_dnf",
            "description": "Nested any/not expands to DNF and evaluates deterministically.",
            "input": {"rule_file": "06_complex.yaml", "chart": chart_complex},
            "evaluations": run("06_complex.yaml", chart_complex),
        },
        {
            "name": "no_match",
            "description": "A non-matching rule reports matched=false and empty results.",
            "input": {"rule_file": "01_single_condition.yaml", "chart": chart_no_match},
            "evaluations": run("01_single_condition.yaml", chart_no_match),
        },
    ]


def export_rule_contract(output_path: str | Path | None = None) -> dict[str, Any]:
    """Export the Rule Layer contract from golden examples.

    Auto-generated by running the Reference Runtime. NOT hand-written.
    """
    contract: dict[str, Any] = {
        "contract_name": "rule",
        "contract_version": RuleEngine.CONTRACT_VERSION,
        "description": (
            "Reference Runtime Rule Layer Contract. "
            "Generated from golden examples. "
            "All future implementations must conform to this contract."
        ),
        "generated_by": "reference.engine.export_rule_contract",
        "operators": [op.value for op in ConditionOperator],
        "rule_types": [rt.value for rt in RuleType],
        "conflict_strategies": [cs.value for cs in ConflictStrategy],
        "models": {
            "RuleCondition": {
                "type": "object",
                "required": ["field", "operator"],
                "optional": ["value", "negate", "description"],
                "field_types": {
                    "field": "string (dotted path)",
                    "operator": "enum",
                    "value": "any | null",
                    "negate": "boolean",
                    "description": "string",
                },
            },
            "RuleResult": {
                "type": "object",
                "required": ["domain", "conclusion", "weight", "direction"],
                "optional": ["conclusion_node_id"],
                "field_types": {
                    "domain": "enum",
                    "conclusion": "string",
                    "conclusion_node_id": "string | null",
                    "weight": "number [0,1]",
                    "direction": "enum",
                },
            },
            "RuleEvaluation": {
                "type": "object",
                "required": ["rule_id", "matched", "results", "priority", "confidence"],
                "field_types": {
                    "rule_id": "string",
                    "matched": "boolean",
                    "results": "array<RuleResult>",
                    "priority": "integer [0,100]",
                    "confidence": "number [0,1]",
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
