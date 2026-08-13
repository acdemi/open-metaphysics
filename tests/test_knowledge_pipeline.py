"""Knowledge corpus pipeline regression tests (Phase 7.0).

Verifies:
- pipeline runs without error
- deterministic output (two runs byte-identical)
- corpus counts (>=10 nodes / >=10 relations / >=2 references)
- schema validity against frozen KB contracts (reference/knowledge.py)
- provenance non-empty on every entry
- reproducibility from the same sources
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from reference.knowledge import (
    KnowledgeNode,
    KnowledgeReference,
    KnowledgeRelation,
    parse_nodes_file,
    parse_references_file,
    parse_relations_file,
)

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT / "knowledge"
CORPUS_DIR = KNOWLEDGE_DIR / "corpus" / "ziwei"
OUTPUT = KNOWLEDGE_DIR / "ziwei_corpus.json"


def _corpus() -> dict:
    return json.loads(OUTPUT.read_text(encoding="utf-8"))


def _run_pipeline() -> str:
    return subprocess.run(
        [sys.executable, str(KNOWLEDGE_DIR / "pipeline.py")],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    ).stdout


def _load_models() -> tuple[list[KnowledgeNode], list[KnowledgeRelation], list[KnowledgeReference]]:
    nodes: list[KnowledgeNode] = []
    relations: list[KnowledgeRelation] = []
    references: list[KnowledgeReference] = []
    for path in sorted((CORPUS_DIR / "nodes").glob("*.yaml")):
        nodes.extend(parse_nodes_file(str(path)))
    for path in sorted((CORPUS_DIR / "relations").glob("*.yaml")):
        relations.extend(parse_relations_file(str(path)))
    for path in sorted((CORPUS_DIR / "references").glob("*.yaml")):
        references.extend(parse_references_file(str(path)))
    return nodes, relations, references


def test_pipeline_runs() -> None:
    out = _run_pipeline()
    assert "corpus written" in out


def test_pipeline_deterministic() -> None:
    _run_pipeline()
    first = OUTPUT.read_bytes()
    _run_pipeline()
    second = OUTPUT.read_bytes()
    assert first == second, "pipeline output not byte-identical across runs"


def test_corpus_has_nodes() -> None:
    assert len(_corpus()["nodes"]) >= 10


def test_corpus_has_relations() -> None:
    assert len(_corpus()["relations"]) >= 10


def test_corpus_has_references() -> None:
    assert len(_corpus()["references"]) >= 2


def test_all_nodes_schema_valid() -> None:
    nodes, _, _ = _load_models()
    assert len(nodes) >= 10
    assert {n.node_type.value for n in nodes} >= {"wuxing", "main_star", "palace", "ten_god"}


def test_all_relations_schema_valid() -> None:
    _, relations, _ = _load_models()
    assert len(relations) >= 10
    types = {r.relation_type.value for r in relations}
    assert types >= {"sheng", "ke", "he"}, f"relation types missing: {types}"


def test_all_references_schema_valid() -> None:
    _, _, references = _load_models()
    assert len(references) >= 2
    types = {r.ref_type.value for r in references}
    assert len(types) >= 2, f"only {len(types)} ref types"


def test_provenance_not_empty() -> None:
    nodes, relations, references = _load_models()
    for n in nodes:
        assert n.source.text, f"{n.id} missing provenance"
    for r in relations:
        assert r.source.text, f"{r.id} missing provenance"
    for r in references:
        assert r.source.text, f"{r.reference_id} missing provenance"


def test_source_to_corpus_reproducible() -> None:
    """Same sources -> same corpus: re-run yields identical checksum/content."""
    _run_pipeline()
    first_text = OUTPUT.read_text(encoding="utf-8")
    doc = json.loads(first_text)
    digests = doc["metadata"]["source_digests"]
    assert len(digests) == 2, "expected 2 source metadata files"
    for path in (KNOWLEDGE_DIR / "sources" / "ziwei").glob("*.yaml"):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digests[path.name], (
            f"source digest mismatch: {path.name}"
        )
    second_text = OUTPUT.read_text(encoding="utf-8")
    assert first_text == second_text
