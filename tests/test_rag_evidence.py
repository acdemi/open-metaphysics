"""Relation/reference retrieval (opt-in evidence chunks)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from openmetaphysics.api.app import create_app
from openmetaphysics.rag.corpus import load_evidence_chunks
from openmetaphysics.rag.retriever import (
    get_evidence_retriever,
    get_retriever,
    reset_retriever,
    search_knowledge,
)

client = TestClient(create_app())


def _node(node_id: str, name: str) -> dict:
    return {
        "id": node_id,
        "node_type": "main_star",
        "name_cn": name,
        "name_en": node_id.rsplit(":", 1)[-1],
        "systems": ["ziwei"],
        "source": {"text": "某书", "chapter": "卷"},
        "interpretation": f"{name}的释义",
    }


def _corpus(nodes: list[dict], relations: list[dict] | None = None, references: list[dict] | None = None) -> dict:
    return {
        "metadata": {
            "corpus_id": "ziwei_corpus",
            "domain": "ziwei",
            "status": "frozen",
            "version": "1.0.0",
            "counts": {"nodes": len(nodes), "relations": len(relations or []), "references": len(references or [])},
        },
        "nodes": nodes,
        "relations": relations or [],
        "references": references or [],
    }


# == default path stays node-only (explain compatibility) ==


def test_default_search_is_nodes_only() -> None:
    reset_retriever()
    assert all(c.id.startswith("kn:") for c in getattr(get_retriever(), "chunks", []))
    assert all(c.id.startswith("kn:") for c in search_knowledge("紫微", k=5))


def test_evidence_retriever_does_not_leak_into_default() -> None:
    reset_retriever()
    get_evidence_retriever()
    assert all(c.id.startswith("kn:") for c in getattr(get_retriever(), "chunks", []))
    reset_retriever()


# == evidence chunk construction ==


def test_evidence_chunks_are_deterministic_and_unique() -> None:
    first = load_evidence_chunks()
    second = load_evidence_chunks()
    ids = [c.id for c in first]
    assert ids == [c.id for c in second]
    assert len(ids) == len(set(ids))
    assert any(i.startswith("rel:") for i in ids)
    assert any(i.startswith("ref:") for i in ids)
    assert all(c.text.strip() for c in first)


def test_include_evidence_recalls_relation_and_reference() -> None:
    reset_retriever()
    try:
        relation_hits = search_knowledge("紫微天府", k=10, include_evidence=True)
        assert any(c.id.startswith("rel:") for c in relation_hits)

        reference_hits = search_knowledge("帝座", k=10, include_evidence=True)
        assert any(c.id.startswith("ref:") for c in reference_hits)

        again = search_knowledge("帝座", k=10, include_evidence=True)
        assert [c.id for c in reference_hits] == [c.id for c in again]
    finally:
        reset_retriever()


def test_invalid_entries_are_skipped(tmp_path: Path) -> None:
    doc = _corpus(
        nodes=[_node("kn:a", "甲")],
        relations=[
            {"id": "rel:he:broken", "source_node_id": "kn:a", "target_node_id": "kn:missing", "relation_type": "he", "evidence": [], "conditions": [], "source": {}},
            {"id": "rel:he:valid", "source_node_id": "kn:a", "target_node_id": "kn:a", "relation_type": "he", "evidence": [{"description": "自合"}], "conditions": [], "source": {"text": "契约"}},
        ],
        references=[
            {"reference_id": "ref:empty", "target_type": "node", "target_id": "kn:a", "ref_type": "classic_text", "passage": "", "source": {}},
            {"reference_id": "ref:valid", "target_type": "node", "target_id": "kn:a", "ref_type": "classic_text", "passage": "甲为帝座。", "source": {"text": "某书", "chapter": "卷"}},
        ],
    )
    path = tmp_path / "ziwei_corpus.json"
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    chunks = load_evidence_chunks(path)
    assert [c.id for c in chunks] == ["rel:he:valid", "ref:valid"]


def test_duplicate_ids_are_deduped(tmp_path: Path) -> None:
    reference = {
        "reference_id": "ref:dup",
        "target_type": "node",
        "target_id": "kn:a",
        "ref_type": "classic_text",
        "passage": "重复引用。",
        "source": {"text": "某书"},
    }
    for name, corpus_id in (("ziwei_corpus.json", "ziwei_corpus"), ("bazi_corpus.json", "bazi_corpus")):
        doc = _corpus(nodes=[_node("kn:a", "甲")], references=[reference])
        doc["metadata"]["corpus_id"] = corpus_id
        (tmp_path / name).write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    chunks = load_evidence_chunks(tmp_path / "ziwei_corpus.json")
    assert [c.id for c in chunks] == ["ref:dup"]


# == API surface ==


def test_api_include_evidence_flag() -> None:
    default = client.post("/knowledge/search", json={"query": "帝座", "k": 10})
    assert default.status_code == 200
    assert all(c["id"].startswith("kn:") for c in default.json()["chunks"])

    enriched = client.post(
        "/knowledge/search", json={"query": "帝座", "k": 10, "include_evidence": True}
    )
    assert enriched.status_code == 200
    body = enriched.json()
    assert body["include_evidence"] is True
    assert any(c["id"].startswith("ref:") for c in body["chunks"])
