#!/usr/bin/env python
"""Reference Demo -- DSL -> Rule -> Evaluate -> JSON.

Usage:
    python -m reference.demo                          # Run all examples
    python -m reference.demo reference/examples/01_single_condition.yaml

This demo validates the full reference chain end-to-end.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .engine import RuleEngine
from .parser import parse_rule_file

# ── Sample chart data for demonstration ────────────────────────────

CHART_BAZI_WITH_SEAL = {
    "ten_gods_map": {"values": ["伤官", "正印", "比肩"]},
    "day_master_strength": 0.35,
    "shen_sha_list": ["羊刃", "天乙贵人"],
}

CHART_BAZI_NO_SEAL = {
    "ten_gods_map": {"values": ["伤官", "比肩", "正财"]},
    "day_master_strength": 0.5,
    "shen_sha_list": ["羊刃"],
}

CHART_BAZI_GUAN_SHA = {
    "ten_gods_map": {"values": ["正官", "七杀", "比肩"]},
    "day_master_strength": 0.4,
    "shen_sha_list": ["羊刃"],
}

CHART_QIMEN = {
    "dun_type": "yang",
    "ju": 6,
}


def run_example(yaml_path: str, chart_data: dict) -> None:
    """Parse a YAML rule file, evaluate against chart data, print JSON."""
    print(f"\n{'=' * 60}")
    print(f"File:    {yaml_path}")
    print(f"Chart:   {json.dumps(chart_data, ensure_ascii=False)}")
    print(f"{'=' * 60}")

    rules = parse_rule_file(yaml_path)
    print(f"Parsed:  {len(rules)} rule(s)")
    for r in rules:
        print(f"  - {r.id} ({r.name}) conditions={len(r.conditions)}")

    engine = RuleEngine()
    evaluations = engine.evaluate_all(rules, chart_data)

    print("\nEvaluations:")
    for ev in evaluations:
        print(json.dumps(ev.model_dump(mode="json"), ensure_ascii=False, indent=2))


def main():
    examples_dir = Path(__file__).parent / "examples"

    if len(sys.argv) > 1:
        yaml_path = sys.argv[1]
        chart = CHART_BAZI_WITH_SEAL
        run_example(yaml_path, chart)
        return

    # Run all examples with appropriate chart data
    run_example(str(examples_dir / "01_single_condition.yaml"), CHART_BAZI_WITH_SEAL)
    run_example(str(examples_dir / "02_and.yaml"), CHART_BAZI_WITH_SEAL)
    run_example(str(examples_dir / "03_or.yaml"), CHART_BAZI_WITH_SEAL)
    run_example(str(examples_dir / "04_not.yaml"), CHART_BAZI_NO_SEAL)
    run_example(str(examples_dir / "05_scope.yaml"), CHART_QIMEN)
    run_example(str(examples_dir / "06_complex.yaml"), CHART_BAZI_GUAN_SHA)

    print(f"\n{'=' * 60}")
    print("Demo complete. Full chain validated: YAML -> Rule -> Evaluate -> JSON")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
