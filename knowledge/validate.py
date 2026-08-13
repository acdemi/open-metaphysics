"""Knowledge corpus schema validation -- Phase 7.0.

Validates nodes/relations/references against the frozen KB contracts
(KB-001~020) using the normative reference models (reference/knowledge.py),
plus cross-referential integrity checks (relation endpoints exist,
reference targets exist, ids unique).

Run:  python knowledge/validate.py   (prints PASS/FAIL report)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from reference.knowledge import (  # noqa: E402  (sys.path bootstrap above)
    KnowledgeNode,
    KnowledgeReference,
    KnowledgeRelation,
    parse_nodes_file,
    parse_references_file,
    parse_relations_file,
)

ROOT = Path(__file__).resolve().parent
CORPUS_DIR = ROOT / "corpus" / "ziwei"


def validate() -> list[str]:
    """Run all validations; returns a list of failure messages (empty = PASS)."""
    failures: list[str] = []

    nodes: list[KnowledgeNode] = []
    relations: list[KnowledgeRelation] = []
    references: list[KnowledgeReference] = []

    for path in sorted((CORPUS_DIR / "nodes").glob("*.yaml")):
        nodes.extend(parse_nodes_file(str(path)))
    for path in sorted((CORPUS_DIR / "relations").glob("*.yaml")):
        relations.extend(parse_relations_file(str(path)))
    for path in sorted((CORPUS_DIR / "references").glob("*.yaml")):
        references.extend(parse_references_file(str(path)))

    # KB-001~003: model-level schema (id pattern, enums, ranges) enforced by pydantic
    # during parse; nothing extra needed here beyond counts.
    if len(nodes) < 10:
        failures.append(f"nodes < 10 ({len(nodes)})")
    if len(relations) < 10:
        failures.append(f"relations < 10 ({len(relations)})")
    if len(references) < 2:
        failures.append(f"references < 2 ({len(references)})")

    # KREF-003: provenance non-empty on every node/relation/reference
    for n in nodes:
        if not n.source.text:
            failures.append(f"{n.id}: empty source.text")
    for r in relations:
        if not r.source.text:
            failures.append(f"{r.id}: empty source.text")
    for r in references:
        if not r.source.text:
            failures.append(f"{r.reference_id}: empty source.text")

    # Cross-referential integrity
    node_ids = {n.id for n in nodes}
    rel_ids = {r.id for r in relations}
    for r in relations:
        if r.source_node_id not in node_ids:
            failures.append(f"{r.id}: source_node {r.source_node_id} missing")
        if r.target_node_id not in node_ids:
            failures.append(f"{r.id}: target_node {r.target_node_id} missing")
    for r in references:
        if r.target_type.value == "node" and r.target_id not in node_ids:
            failures.append(f"{r.reference_id}: target node {r.target_id} missing")
        if r.target_type.value == "relation" and r.target_id not in rel_ids:
            failures.append(f"{r.reference_id}: target relation {r.target_id} missing")

    # Duplicate ids (list length vs set length)
    for label, ids in (
        ("node", [n.id for n in nodes]),
        ("relation", [r.id for r in relations]),
        ("reference", [r.reference_id for r in references]),
    ):
        if len(ids) != len(set(ids)):
            failures.append(f"duplicate {label} ids detected")

    return failures


def main() -> None:
    failures = validate()
    if failures:
        print(f"VALIDATION FAILED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        raise SystemExit(1)
    print("VALIDATION PASSED: all corpus entries conform to KB-001~020")


if __name__ == "__main__":
    main()
