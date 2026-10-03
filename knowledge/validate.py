"""Knowledge corpus schema validation -- Phase 7.0 (multi-domain, P2.1/P2.2).

Validates nodes/relations/references against the frozen KB contracts
(KB-001~020) using the normative reference models (reference/knowledge.py),
plus cross-referential integrity checks (relation endpoints exist,
reference targets exist, ids unique).

P2.1 BaZi Knowledge Integration: the checks now run per corpus domain
(``corpus/<domain>/``) and additionally assert that ids stay globally unique
across domains, because every domain's nodes are loaded into the same
retriever. The checks themselves are unchanged.

P2.2 Qimen Knowledge Integration: ``qimen`` joins the domain tuple. The checks
are still unchanged -- adding a domain requires no new validation rule.

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
DOMAINS = ("ziwei", "bazi", "qimen")

MIN_NODES = 10
MIN_RELATIONS = 10
MIN_REFERENCES = 2


def _corpus_dir(domain: str) -> Path:
    return ROOT / "corpus" / domain


def _load_domain(
    domain: str,
) -> tuple[list[KnowledgeNode], list[KnowledgeRelation], list[KnowledgeReference]]:
    base = _corpus_dir(domain)
    nodes: list[KnowledgeNode] = []
    relations: list[KnowledgeRelation] = []
    references: list[KnowledgeReference] = []

    for path in sorted((base / "nodes").glob("*.yaml")):
        nodes.extend(parse_nodes_file(str(path)))
    for path in sorted((base / "relations").glob("*.yaml")):
        relations.extend(parse_relations_file(str(path)))
    for path in sorted((base / "references").glob("*.yaml")):
        references.extend(parse_references_file(str(path)))
    return nodes, relations, references


def _validate_domain(domain: str, failures: list[str]) -> None:
    """Per-domain schema + cross-referential integrity checks."""
    base = _corpus_dir(domain)
    if not base.is_dir():
        failures.append(f"{domain}: corpus directory missing ({base})")
        return

    nodes, relations, references = _load_domain(domain)

    # KB-001~003: model-level schema (id pattern, enums, ranges) enforced by pydantic
    # during parse; nothing extra needed here beyond the required minimum counts.
    if len(nodes) < MIN_NODES:
        failures.append(f"{domain}: nodes < {MIN_NODES} ({len(nodes)})")
    if len(relations) < MIN_RELATIONS:
        failures.append(f"{domain}: relations < {MIN_RELATIONS} ({len(relations)})")
    if len(references) < MIN_REFERENCES:
        failures.append(f"{domain}: references < {MIN_REFERENCES} ({len(references)})")

    # KREF-003: provenance non-empty on every node/relation/reference
    for n in nodes:
        if not n.source.text:
            failures.append(f"{domain}: {n.id}: empty source.text")
    for r in relations:
        if not r.source.text:
            failures.append(f"{domain}: {r.id}: empty source.text")
    for r in references:
        if not r.source.text:
            failures.append(f"{domain}: {r.reference_id}: empty source.text")

    # Cross-referential integrity
    node_ids = {n.id for n in nodes}
    rel_ids = {r.id for r in relations}
    for r in relations:
        if r.source_node_id not in node_ids:
            failures.append(f"{domain}: {r.id}: source_node {r.source_node_id} missing")
        if r.target_node_id not in node_ids:
            failures.append(f"{domain}: {r.id}: target_node {r.target_node_id} missing")
    for r in references:
        if r.target_type.value == "node" and r.target_id not in node_ids:
            failures.append(f"{domain}: {r.reference_id}: target node {r.target_id} missing")
        if r.target_type.value == "relation" and r.target_id not in rel_ids:
            failures.append(f"{domain}: {r.reference_id}: target relation {r.target_id} missing")

    # Duplicate ids (list length vs set length)
    for label, ids in (
        ("node", [n.id for n in nodes]),
        ("relation", [r.id for r in relations]),
        ("reference", [r.reference_id for r in references]),
    ):
        if len(ids) != len(set(ids)):
            failures.append(f"{domain}: duplicate {label} ids detected")


def _validate_cross_domain(failures: list[str]) -> None:
    """Every domain's nodes share one retriever, so ids must stay unique."""
    seen: dict[str, str] = {}
    for domain in DOMAINS:
        base = _corpus_dir(domain)
        if not base.is_dir():
            continue
        nodes, _, _ = _load_domain(domain)
        for n in nodes:
            owner = seen.get(n.id)
            if owner is not None and owner != domain:
                failures.append(f"cross-domain duplicate node id {n.id} ({owner}, {domain})")
            seen[n.id] = domain


def validate() -> list[str]:
    """Run all validations; returns a list of failure messages (empty = PASS)."""
    failures: list[str] = []
    for domain in DOMAINS:
        _validate_domain(domain, failures)
    _validate_cross_domain(failures)
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
