"""Reference DSL Parser -- YAML -> Pydantic Rule.

Implements the Phase 6.5 Rule DSL grammar:
  - Single condition (inline)
  - all: (AND)
  - any: (OR) -- DNF expansion to multiple Rules
  - not: -- maps to negate=True

See: docs/engineering/01_rule_dsl.md
"""

from __future__ import annotations

import yaml

from .models import Rule, RuleCondition


def _is_leaf(node):
    return isinstance(node, dict) and "field" in node and "operator" in node


def _flip_negate(leaf):
    result = dict(leaf)
    result["negate"] = not result.get("negate", False)
    return result


def _to_dnf(node):
    """Convert condition tree to DNF (list of conjunctions)."""
    if _is_leaf(node):
        return [[node]]

    if not isinstance(node, dict):
        raise ValueError("Invalid condition node: " + repr(node))

    if "all" in node:
        children = node["all"]
        if not children:
            raise ValueError("all must contain at least one condition")
        result = [[]]
        for child in children:
            child_dnf = _to_dnf(child)
            new_result = []
            for conj in result:
                for child_conj in child_dnf:
                    new_result.append(conj + child_conj)
            result = new_result
        return result

    if "any" in node:
        children = node["any"]
        if not children:
            raise ValueError("any must contain at least one condition")
        result = []
        for child in children:
            result.extend(_to_dnf(child))
        return result

    if "not" in node:
        child = node["not"]
        if _is_leaf(child):
            return [[_flip_negate(child)]]
        if isinstance(child, dict) and "all" in child:
            return _to_dnf({"any": [{"not": c} for c in child["all"]]})
        if isinstance(child, dict) and "any" in child:
            return _to_dnf({"all": [{"not": c} for c in child["any"]]})
        if isinstance(child, dict) and "not" in child:
            return _to_dnf(child["not"])
        raise ValueError("Cannot apply not to node: " + repr(child))

    raise ValueError("Unrecognized condition node: " + repr(node))


def parse_rule_document(yaml_text):
    """Parse a YAML rule document into a list of Rule objects."""
    doc = yaml.safe_load(yaml_text)
    if not isinstance(doc, dict) or "rule" not in doc:
        raise ValueError("YAML must contain a top-level rule mapping")

    rule_data = dict(doc["rule"])

    if "if" not in rule_data:
        raise ValueError("Rule must contain an if section")
    if_section = rule_data.pop("if")
    dnf = _to_dnf(if_section)

    if "then" in rule_data:
        rule_data["results"] = rule_data.pop("then")

    rules = []
    base_id = rule_data["id"]

    for i, conjunction in enumerate(dnf):
        rule_dict = dict(rule_data)
        if len(dnf) > 1:
            rule_dict["id"] = base_id + "#" + str(i + 1)
        rule_dict["conditions"] = [RuleCondition(**cd) for cd in conjunction]
        rules.append(Rule(**rule_dict))

    return rules


def parse_rule_file(path):
    """Parse a YAML rule file into a list of Rule objects."""
    with open(path, encoding="utf-8") as f:
        return parse_rule_document(f.read())
