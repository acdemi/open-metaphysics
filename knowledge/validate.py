"""Knowledge corpus validation + *honest* evidence coverage report (H10).

The old validator printed ``VALIDATION PASSED`` after checking only minimum
counts and non-empty provenance, while most nodes had no entry-level
``KnowledgeReference`` at all. It also never parsed the source files, so eight
``sources/*.yaml`` files that were actually Markdown tables (invalid YAML) went
unnoticed.

This validator now:

1. runs the original structural checks (KB-001~020, cross-references, ids);
2. parses the machine-readable source registry
   (``knowledge/sources/registry.yaml``) and checks every citation label used by
   nodes/relations/references is registered, with a declared classification;
3. checks references: non-empty passage, registered source, entry-level anchor
   (chapter/page) for ``classic_text``, and whether the cited source actually
   declares a verbatim verification (offline text re-verification is impossible,
   so this is a declaration check, not a text check);
4. checks the frozen corpus register (``knowledge/coverage_baseline.json``):
   corpus sha256, counts and ``source_digests`` must match the registered
   artifact; a drifted corpus is a failure;
5. prints a real coverage report (per-domain nodes/relations without entry-level
   references, verbatim vs attributed evidence) and compares the known gaps with
   the registered baseline: a *new* gap is a failure, a *stale* baseline entry is
   a failure. ``--strict`` additionally fails every known gap.

Default mode therefore means: structural + registry + no-drift + no-new-gap.
It is NOT a claim that every node has evidence. Use ``--strict`` for that gate.

Run: python knowledge/validate.py [--strict] [--json]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml

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

DOMAINS = ("ziwei", "bazi", "qimen", "liuyao")
MIN_NODES = 10
MIN_RELATIONS = 10
MIN_REFERENCES = 2

REGISTRY_RELPATH = Path("sources") / "registry.yaml"
BASELINE_RELPATH = Path("coverage_baseline.json")
REQUIRED_SOURCE_KEYS = ("source_id", "title", "classification", "evidence_status")
SOURCE_CLASSIFICATIONS = (
    "classic_text",
    "school_commentary",
    "modern_interpretation",
    "internal_contract",
)
# A declared verbatim verification marker; declaration only (offline text
# re-fetch is impossible, so the validator never claims to have re-read it).
VERBATIM_MARKER = "verbatim_verified"


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


# -- source registry --------------------------------------------------------


def load_source_registry() -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Load and check ``knowledge/sources/registry.yaml``.

    Returns ``(entries_by_title, failures)``. Missing/unreadable registry yields
    an empty mapping and a failure (callers may downgrade to a warning when the
    validator runs on a synthetic ROOT, as the negative-control tests do).
    """
    path = ROOT / REGISTRY_RELPATH
    failures: list[str] = []
    if not path.is_file():
        return {}, [f"source registry missing: {path}"]
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return {}, [f"source registry is not valid YAML: {exc}"]
    if not isinstance(doc, dict) or not isinstance(doc.get("sources"), list):
        return {}, ["source registry must have a top-level 'sources' list"]

    entries: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()
    for raw in doc["sources"]:
        if not isinstance(raw, dict):
            failures.append("source registry entry is not a mapping")
            continue
        missing = [key for key in REQUIRED_SOURCE_KEYS if not raw.get(key)]
        if missing:
            failures.append(f"source registry entry missing {missing}: {raw.get('title')!r}")
            continue
        title = str(raw["title"])
        if title in entries:
            failures.append(f"duplicate source title in registry: {title}")
        source_id = str(raw["source_id"])
        if source_id in seen_ids:
            failures.append(f"duplicate source_id in registry: {source_id}")
        seen_ids.add(source_id)
        if raw["classification"] not in SOURCE_CLASSIFICATIONS:
            failures.append(
                f"source {title}: unknown classification {raw['classification']!r} "
                f"(allowed: {', '.join(SOURCE_CLASSIFICATIONS)})"
            )
        for rel in raw.get("files") or []:
            if not (ROOT / "sources" / rel).is_file():
                failures.append(f"source {title}: registered dossier missing: sources/{rel}")
        entries[title] = raw
    return entries, failures


def _source_evidence_status(entry: dict[str, Any] | None, domain: str) -> str:
    """Declared evidence level for one citation, domain-specific when registered."""
    if not entry:
        return ""
    per_domain = entry.get("evidence_status_by_domain")
    if isinstance(per_domain, dict) and per_domain.get(domain):
        return str(per_domain[domain])
    return str(entry.get("evidence_status", ""))


def _source_is_verbatim(entry: dict[str, Any] | None, domain: str) -> bool:
    return VERBATIM_MARKER in _source_evidence_status(entry, domain).lower()


def _source_classification(entry: dict[str, Any] | None) -> str:
    return str(entry.get("classification", "unregistered")) if entry else "unregistered"


# -- per-domain structural checks (unchanged contract checks) ---------------


def _validate_domain(
    domain: str,
    failures: list[str],
    strict_failures: list[str],
    registry: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Per-domain schema + integrity + evidence checks; returns coverage data."""
    base = _corpus_dir(domain)
    if not base.is_dir():
        failures.append(f"{domain}: corpus directory missing ({base})")
        return {}

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

    # -- evidence coverage (H10) ------------------------------------------
    if registry is None:
        registry, registry_failures = load_source_registry()
        failures.extend(registry_failures)
    else:
        registry_failures = []

    referenced_nodes = {r.target_id for r in references if r.target_type.value == "node"}
    referenced_relations = {r.target_id for r in references if r.target_type.value == "relation"}
    uncovered_nodes = sorted(node_ids - referenced_nodes)
    uncovered_relations = sorted(rel_ids - referenced_relations)

    missing_anchor: list[str] = []
    missing_verbatim: list[str] = []
    attributed_only = 0
    verbatim_count = 0
    non_classic_citations: list[str] = []
    for ref in references:
        entry = registry.get(ref.source.text)
        if entry is None:
            failures.append(
                f"{domain}: {ref.reference_id}: source {ref.source.text!r} is not "
                f"registered in {REGISTRY_RELPATH.as_posix()}"
            )
            continue
        classification = _source_classification(entry)
        if classification != "classic_text":
            non_classic_citations.append(f"{ref.reference_id} -> {ref.source.text}")
        if not ref.passage.strip():
            failures.append(f"{domain}: {ref.reference_id}: empty passage")
        if _source_is_verbatim(entry, domain):
            verbatim_count += 1
        else:
            attributed_only += 1
            missing_verbatim.append(ref.reference_id)
        if ref.ref_type.value == "classic_text" and not (ref.source.chapter or ref.source.page):
            missing_anchor.append(ref.reference_id)

    # Node/relation provenance labels must also be registered (they are
    # provenance, not necessarily verbatim evidence).
    unregistered_provenance: list[str] = []
    for item_id, text in [(n.id, n.source.text) for n in nodes] + [
        (r.id, r.source.text) for r in relations
    ]:
        if text not in registry:
            unregistered_provenance.append(f"{item_id} -> {text}")
            failures.append(f"{domain}: {item_id}: provenance source {text!r} not registered")

    # Strict evidence gate: every node/relation needs an entry-level reference;
    # every classic_text reference needs a chapter/page anchor and a cited source
    # whose registered evidence_status declares verbatim verification.
    for node_id in uncovered_nodes:
        strict_failures.append(f"{domain}: {node_id}: no entry-level KnowledgeReference")
    for rel_id in uncovered_relations:
        strict_failures.append(f"{domain}: {rel_id}: no entry-level KnowledgeReference")
    for ref_id in missing_anchor:
        strict_failures.append(
            f"{domain}: {ref_id}: classic_text reference has no chapter/page anchor"
        )
    for ref_id in missing_verbatim:
        strict_failures.append(
            f"{domain}: {ref_id}: cited source has no registered verbatim verification claim"
        )

    return {
        "nodes": len(nodes),
        "relations": len(relations),
        "references": len(references),
        "referenced_nodes": len(node_ids & referenced_nodes),
        "uncovered_nodes": uncovered_nodes,
        "referenced_relations": len(rel_ids & referenced_relations),
        "uncovered_relations": uncovered_relations,
        "references_verbatim_source": verbatim_count,
        "references_attributed_source": attributed_only,
        "references_missing_anchor": missing_anchor,
        "references_missing_verbatim": missing_verbatim,
        "non_classic_citations": non_classic_citations,
        "unregistered_provenance": unregistered_provenance,
    }


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


# -- frozen corpus register + coverage baseline -----------------------------


def _corpus_file(domain: str) -> Path:
    return ROOT / f"{domain}_corpus.json"


def _corpus_digest(domain: str) -> str | None:
    path = _corpus_file(domain)
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_digests(domain: str) -> dict[str, str]:
    directory = ROOT / "sources" / domain
    if not directory.is_dir():
        return {}
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.glob("*.yaml"))
    }


def load_baseline() -> tuple[dict[str, Any] | None, list[str]]:
    """Load ``knowledge/coverage_baseline.json`` (registered frozen corpus + gaps)."""
    path = ROOT / BASELINE_RELPATH
    if not path.is_file():
        return None, [f"coverage baseline missing: {path}"]
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"coverage baseline is not valid JSON: {exc}"]
    if not isinstance(doc, dict) or "corpora" not in doc or "coverage" not in doc:
        return None, ["coverage baseline must contain 'corpora' and 'coverage' objects"]
    return doc, []


def _check_baseline(
    baseline: dict[str, Any] | None,
    actual: dict[str, Any],
    failures: list[str],
) -> None:
    """Corpus must match the registered artifact and not add *new* evidence gaps."""
    if baseline is None:
        return
    corpora = baseline.get("corpora", {})
    for domain, data in actual.items():
        if not data:
            continue
        registered = corpora.get(domain)
        if registered is None:
            failures.append(f"{domain}: missing from coverage baseline corpora")
            continue
        digest = _corpus_digest(domain)
        if digest != registered.get("sha256"):
            failures.append(
                f"{domain}: corpus sha256 mismatch with registered baseline "
                f"({digest} != {registered.get('sha256')}); regenerate the corpus and "
                f"update knowledge/{BASELINE_RELPATH.as_posix()} after review"
            )
        counts = {
            "nodes": data["nodes"],
            "relations": data["relations"],
            "references": data["references"],
        }
        if counts != registered.get("counts"):
            failures.append(
                f"{domain}: corpus counts {counts} != registered {registered.get('counts')}"
            )
        if _source_digests(domain) != registered.get("source_digests"):
            failures.append(
                f"{domain}: source_digests mismatch with registered baseline; "
                f"update knowledge/{BASELINE_RELPATH.as_posix()} after review"
            )
        expected = baseline.get("coverage", {}).get(domain, {})
        for key in ("uncovered_nodes", "uncovered_relations"):
            new = sorted(set(data[key]) - set(expected.get(key) or []))
            stale = sorted(set(expected.get(key) or []) - set(data[key]))
            if new:
                failures.append(f"{domain}: {len(new)} new uncovered {key}: {new[:5]}")
            if stale:
                failures.append(f"{domain}: {len(stale)} stale baseline {key} entries: {stale[:5]}")
        evidence = baseline.get("evidence", {}).get(domain, {})
        for key in ("references_missing_anchor", "references_missing_verbatim"):
            if sorted(data[key]) != sorted(evidence.get(key) or []):
                failures.append(
                    f"{domain}: {key} changed vs registered baseline "
                    f"(update knowledge/{BASELINE_RELPATH.as_posix()} after review)"
                )


# -- public API -------------------------------------------------------------


def coverage_report() -> dict[str, Any]:
    """Compute the real coverage numbers (no pass/fail judgement)."""
    registry, _ = load_source_registry()
    domains: dict[str, Any] = {}
    for domain in DOMAINS:
        if not _corpus_dir(domain).is_dir():
            continue
        domains[domain] = _validate_domain(domain, [], [], registry=registry)
    classifications: dict[str, int] = {}
    for entry in registry.values():
        key = _source_classification(entry)
        classifications[key] = classifications.get(key, 0) + 1
    totals = {
        "nodes": sum(d["nodes"] for d in domains.values()),
        "uncovered_nodes": sum(len(d["uncovered_nodes"]) for d in domains.values()),
        "relations": sum(d["relations"] for d in domains.values()),
        "uncovered_relations": sum(len(d["uncovered_relations"]) for d in domains.values()),
        "references": sum(d["references"] for d in domains.values()),
        "references_attributed_source": sum(
            d["references_attributed_source"] for d in domains.values()
        ),
        "references_verbatim_source": sum(
            d["references_verbatim_source"] for d in domains.values()
        ),
        "references_missing_anchor": sum(
            len(d["references_missing_anchor"]) for d in domains.values()
        ),
    }
    return {
        "domains": domains,
        "totals": totals,
        "registry": {"entries": len(registry), "classifications": classifications},
    }


def validate(strict: bool = False) -> list[str]:
    """Return failure messages (empty = PASS under the selected gate).

    Default mode fails on structural errors, unregistered sources, empty
    passages, frozen-corpus drift and *new* evidence gaps. ``strict=True`` also
    fails every known evidence gap (the honest "all nodes referenced" gate).
    """
    failures: list[str] = []
    strict_failures: list[str] = []
    registry, registry_failures = load_source_registry()
    failures.extend(registry_failures)
    actual: dict[str, Any] = {}
    for domain in DOMAINS:
        data = _validate_domain(domain, failures, strict_failures, registry=registry)
        if data:
            actual[domain] = data
    _validate_cross_domain(failures)

    baseline, baseline_failures = load_baseline()
    if baseline is None:
        # A synthetic ROOT (negative-control tests) has no baseline; only the
        # real corpus root is required to carry one.
        if (ROOT / "corpus").is_dir() and (ROOT / REGISTRY_RELPATH).is_file():
            failures.extend(baseline_failures)
    _check_baseline(baseline, actual, failures)
    if strict:
        failures.extend(strict_failures)
    return failures


def _format_report(report: dict[str, Any]) -> str:
    lines = ["KNOWLEDGE COVERAGE REPORT (evidence is NOT complete; gaps are registered)"]
    lines.append(
        f"  {'domain':8s} {'nodes':>6s} {'referenced':>10s} {'relations':>10s} "
        f"{'referenced':>10s} {'refs':>5s} {'verbatim-src':>12s}"
    )
    for domain, data in report["domains"].items():
        lines.append(
            f"  {domain:8s} {data['nodes']:>6d} {data['referenced_nodes']:>10d} "
            f"{data['relations']:>10d} {data['referenced_relations']:>10d} "
            f"{data['references']:>5d} {data['references_verbatim_source']:>12d}"
        )
    totals = report["totals"]
    lines.append(
        f"  TOTAL    {totals['nodes']:>6d} {totals['nodes'] - totals['uncovered_nodes']:>10d} "
        f"{totals['relations']:>10d} {totals['relations'] - totals['uncovered_relations']:>10d} "
        f"{totals['references']:>5d}"
    )
    lines.append(
        f"  entry-level reference gaps: {totals['uncovered_nodes']} nodes / "
        f"{totals['uncovered_relations']} relations"
    )
    lines.append(
        f"  references citing sources without a registered verbatim claim: "
        f"{totals['references_attributed_source']}; classic_text refs missing "
        f"chapter/page anchor: {totals['references_missing_anchor']}"
    )
    lines.append(
        f"  source registry: {report['registry']['entries']} entries "
        f"{report['registry']['classifications']}"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    strict = "--strict" in args
    as_json = "--json" in args
    failures = validate(strict=strict)
    report = coverage_report()
    if as_json:
        print(
            json.dumps(
                {"report": report, "strict": strict, "failures": failures},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(_format_report(report))
        if failures:
            print(f"\nVALIDATION FAILED ({len(failures)}):")
            for failure in failures:
                print(f"  - {failure}")
            raise SystemExit(1)
        if strict:
            print("\nSTRICT EVIDENCE GATE PASSED")
        else:
            gaps = report["totals"]["uncovered_nodes"] + report["totals"]["uncovered_relations"]
            print("\nVALIDATION PASSED (structural + source-registry + registered-coverage gate).")
            print(
                f"  NOT a full-coverage claim: {gaps} known entry-level reference gaps remain "
                f"registered in knowledge/{BASELINE_RELPATH.as_posix()}; run --strict for the "
                "full-evidence gate."
            )


if __name__ == "__main__":
    main()
