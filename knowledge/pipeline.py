"""Knowledge corpus pipeline -- Phase 7.0 (deterministic, offline).

Loads corpus YAML, validates against the frozen KB contracts via the
normative reference layer (reference/knowledge.py), and emits a merged
deterministic JSON corpus with a SHA-256 checksum.

Determinism: no clock, no random, no network; sort_keys=True output.
Run:  python knowledge/pipeline.py
"""

from __future__ import annotations

import hashlib
import json
import sys
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

ROOT = Path(__file__).resolve().parent
CORPUS_DIR = ROOT / "corpus" / "ziwei"
SOURCES_DIR = ROOT / "sources" / "ziwei"
OUTPUT = ROOT / "ziwei_corpus.json"


def _load_documents() -> tuple[list[dict], list[dict], list[dict]]:
    """Load nodes/relations/references from corpus YAML (normative parse)."""
    nodes: list[dict] = []
    relations: list[dict] = []
    references: list[dict] = []
    for path in sorted((CORPUS_DIR / "nodes").glob("*.yaml")):
        nodes.extend(n.model_dump(mode="json") for n in parse_nodes_file(str(path)))
    for path in sorted((CORPUS_DIR / "relations").glob("*.yaml")):
        relations.extend(r.model_dump(mode="json") for r in parse_relations_file(str(path)))
    for path in sorted((CORPUS_DIR / "references").glob("*.yaml")):
        references.extend(r.model_dump(mode="json") for r in parse_references_file(str(path)))
    return nodes, relations, references


def _source_digests() -> dict[str, str]:
    """SHA-256 of each source metadata file (stable version tracking)."""
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(SOURCES_DIR.glob("*.yaml"))
    }


def build() -> dict:
    """Build the merged corpus document (pure function, deterministic)."""
    nodes, relations, references = _load_documents()
    doc = {
        "metadata": {
            # Phase 7.1.6 Corpus Freeze (2026-09-16): the corpus is no longer a
            # pilot. Any change to nodes/relations/references now goes through
            # the corpus-level review flow (see the 7.1.6 freeze record).
            "corpus_id": "ziwei_corpus",
            "domain": "ziwei",
            "status": "frozen",
            "version": "1.0.0",
            "counts": {
                "nodes": len(nodes),
                "relations": len(relations),
                "references": len(references),
            },
            "source_digests": _source_digests(),
            "pipeline": "knowledge/pipeline.py (Phase 7.0)",
        },
        "nodes": nodes,
        "relations": relations,
        "references": references,
    }
    return doc


def main() -> None:
    doc = build()
    text = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    # newline="\n" pins LF regardless of platform: .gitattributes declares
    # knowledge/**/*.json as text eol=lf, and the checksum below is computed
    # over the LF text. Without it Windows text mode writes CRLF, which dirties
    # the working tree and makes the on-disk bytes disagree with the register.
    OUTPUT.write_text(text, encoding="utf-8", newline="\n")
    checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(
        f"corpus written: {OUTPUT} ({len(doc['nodes'])} nodes, "
        f"{len(doc['relations'])} relations, {len(doc['references'])} references)"
    )
    print(f"sha256: {checksum}")


if __name__ == "__main__":
    main()
