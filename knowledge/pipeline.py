"""Knowledge corpus pipeline -- Phase 7.0 (deterministic, offline).

Loads corpus YAML, validates against the frozen KB contracts via the
normative reference layer (reference/knowledge.py), and emits a merged
deterministic JSON corpus with a SHA-256 checksum.

Determinism: no clock, no random, no network; sort_keys=True output.
Run:  python knowledge/pipeline.py [domain ...]

Domains (P2.1 added the second domain and P2.2 the third, without changing the
existing ones):

* ``ziwei`` -- the frozen corpus (``ziwei_corpus.json``, status ``frozen``).
  Its output is byte-identical to the pre-P2.1 pipeline: same metadata fields,
  same source_digests key set (``sources/ziwei/*.yaml``), same ordering.
* ``bazi``  -- the P2.1 BaZi corpus (``bazi_corpus.json``, status ``candidate``).
* ``qimen`` -- the P2.2 Qimen corpus (``qimen_corpus.json``, status ``candidate``).
* ``liuyao`` -- the P2.3 Liuyao corpus (``liuyao_corpus.json``, status ``candidate``).

``build()`` keeps its Phase 7.0 signature and still returns the Ziwei document
by default, so existing callers are unaffected.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from reference.knowledge import (  # noqa: E402  (sys.path bootstrap above)
    parse_nodes_file,
    parse_references_file,
    parse_relations_file,
)


@dataclass(frozen=True)
class DomainSpec:
    """How one corpus domain is laid out and labelled."""

    corpus_id: str
    status: str
    version: str
    pipeline: str


DOMAINS: dict[str, DomainSpec] = {
    "ziwei": DomainSpec(
        corpus_id="ziwei_corpus",
        status="frozen",
        version="1.0.0",
        # Phase 7.1.6 Corpus Freeze (2026-09-16): the corpus is no longer a
        # pilot. Any change to nodes/relations/references now goes through
        # the corpus-level review flow (see the 7.1.6 freeze record).
        pipeline="knowledge/pipeline.py (Phase 7.0)",
    ),
    "bazi": DomainSpec(
        corpus_id="bazi_corpus",
        status="frozen",
        version="1.0.0",
        # 2026-10-24 bounded freeze: 9/14 refs verbatim; 5 convention-level
        # (see BAZI_CORPUS_FREEZE_REVIEW.md). Changes now go through review.
        pipeline="knowledge/pipeline.py (P2.1 BaZi Knowledge Integration; frozen v1.0.0)",
    ),
    "qimen": DomainSpec(
        corpus_id="qimen_corpus",
        status="frozen",
        version="1.0.0",
        # 2026-10-24 bounded freeze: 10/15 refs verbatim; 5 summaries
        # (see QIMEN_CORPUS_FREEZE_REVIEW.md). Changes now go through review.
        pipeline="knowledge/pipeline.py (P2.2 Qimen Knowledge Integration; frozen v1.0.0)",
    ),
    "liuyao": DomainSpec(
        corpus_id="liuyao_corpus",
        status="frozen",
        version="1.0.0",
        # 2026-10-24 Corpus Freeze: revision-pinned verbatim evidence; any
        # node/relation/reference change now goes through corpus-level review.
        pipeline="knowledge/pipeline.py (P2.4 Liuyao Knowledge Enrichment II; frozen v1.0.0)",
    ),
}
DEFAULT_DOMAIN = "ziwei"


def corpus_dir(domain: str) -> Path:
    return ROOT / "corpus" / domain


def sources_dir(domain: str) -> Path:
    return ROOT / "sources" / domain


def output_path(domain: str) -> Path:
    return ROOT / f"{DOMAINS[domain].corpus_id}.json"


def _load_documents(domain: str) -> tuple[list[dict], list[dict], list[dict]]:
    """Load nodes/relations/references from corpus YAML (normative parse)."""
    base = corpus_dir(domain)
    nodes: list[dict] = []
    relations: list[dict] = []
    references: list[dict] = []
    for path in sorted((base / "nodes").glob("*.yaml")):
        nodes.extend(n.model_dump(mode="json") for n in parse_nodes_file(str(path)))
    for path in sorted((base / "relations").glob("*.yaml")):
        relations.extend(r.model_dump(mode="json") for r in parse_relations_file(str(path)))
    for path in sorted((base / "references").glob("*.yaml")):
        references.extend(r.model_dump(mode="json") for r in parse_references_file(str(path)))
    return nodes, relations, references


def _source_digests(domain: str) -> dict[str, str]:
    """SHA-256 of each source metadata file (stable version tracking)."""
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(sources_dir(domain).glob("*.yaml"))
    }


def build(domain: str = DEFAULT_DOMAIN) -> dict:
    """Build one domain's merged corpus document (pure, deterministic)."""
    spec = DOMAINS[domain]
    nodes, relations, references = _load_documents(domain)
    doc = {
        "metadata": {
            "corpus_id": spec.corpus_id,
            "domain": domain,
            "status": spec.status,
            "version": spec.version,
            "counts": {
                "nodes": len(nodes),
                "relations": len(relations),
                "references": len(references),
            },
            "source_digests": _source_digests(domain),
            "pipeline": spec.pipeline,
        },
        "nodes": nodes,
        "relations": relations,
        "references": references,
    }
    return doc


def write(domain: str) -> tuple[Path, str, dict]:
    """Serialise one domain deterministically; returns (path, sha256, doc)."""
    doc = build(domain)
    text = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    # newline="\n" pins LF regardless of platform: .gitattributes declares
    # knowledge/**/*.json as text eol=lf, and the checksum below is computed
    # over the LF text. Without it Windows text mode writes CRLF, which dirties
    # the working tree and makes the on-disk bytes disagree with the register.
    out = output_path(domain)
    out.write_text(text, encoding="utf-8", newline="\n")
    checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return out, checksum, doc


def main(argv: list[str] | None = None) -> None:
    requested = list(argv if argv is not None else sys.argv[1:])
    domains = requested or list(DOMAINS)
    for domain in domains:
        if domain not in DOMAINS:
            raise SystemExit(f"unknown corpus domain: {domain} (known: {', '.join(DOMAINS)})")
    for domain in domains:
        out, checksum, doc = write(domain)
        print(
            f"corpus written: {out} ({len(doc['nodes'])} nodes, "
            f"{len(doc['relations'])} relations, {len(doc['references'])} references)"
        )
        print(f"sha256: {checksum}")


if __name__ == "__main__":
    main()
