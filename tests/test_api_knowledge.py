"""Knowledge retrieval HTTP endpoint (frozen corpora, offline)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from openmetaphysics.api.app import app, create_app

client = TestClient(create_app())


def test_knowledge_search_returns_chunks() -> None:
    response = client.post("/knowledge/search", json={"query": "紫微", "k": 3})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "紫微"
    assert 1 <= len(body["chunks"]) <= 3
    for chunk in body["chunks"]:
        assert {"id", "text", "source", "tags"} <= set(chunk)


def test_knowledge_search_empty_query() -> None:
    response = client.post("/knowledge/search", json={"query": "   ", "k": 3})
    assert response.status_code == 200
    assert response.json()["chunks"] == []


def test_knowledge_corpora_stats() -> None:
    response = client.get("/knowledge/corpora")
    assert response.status_code == 200
    corpora = response.json()["corpora"]
    assert {c["corpus_id"] for c in corpora} == {
        "ziwei_corpus",
        "bazi_corpus",
        "qimen_corpus",
        "liuyao_corpus",
    }
    assert all(c["status"] == "frozen" for c in corpora)
    assert all(c["counts"]["nodes"] > 0 for c in corpora)


def test_knowledge_search_invalid_422() -> None:
    response = client.post("/knowledge/search", json={"k": 3})
    assert response.status_code == 422
    assert response.json()["error"]["kind"] == "invalid_request"


def test_knowledge_search_contract_shape() -> None:
    """Response model pins the exact wire shape; no relevance score is invented."""
    body: dict[str, Any] = client.post("/knowledge/search", json={"query": "紫微", "k": 3}).json()
    assert set(body) == {"query", "include_evidence", "chunks"}
    assert body["query"] == "紫微"
    assert body["include_evidence"] is False
    assert 1 <= len(body["chunks"]) <= 3
    for chunk in body["chunks"]:
        assert set(chunk) == {"id", "text", "source", "tags"}
        assert isinstance(chunk["id"], str) and chunk["id"].startswith("kn:")
        assert isinstance(chunk["text"], str) and chunk["text"].strip()
        assert isinstance(chunk["source"], str)
        assert isinstance(chunk["tags"], list)
        assert all(isinstance(tag, str) for tag in chunk["tags"])
        assert "score" not in chunk, "the API does not return a relevance score"


def test_knowledge_search_include_evidence_flag_round_trips() -> None:
    body = client.post(
        "/knowledge/search", json={"query": "紫微", "k": 2, "include_evidence": True}
    ).json()
    assert body["include_evidence"] is True
    assert isinstance(body["chunks"], list)


def test_knowledge_corpora_contract_shape() -> None:
    body: dict[str, Any] = client.get("/knowledge/corpora").json()
    assert set(body) == {"corpora"}
    assert body["corpora"], "at least one frozen corpus must be registered"
    for corpus in body["corpora"]:
        assert set(corpus) == {"corpus_id", "status", "version", "counts"}
        assert isinstance(corpus["corpus_id"], str)
        assert corpus["status"] is None or isinstance(corpus["status"], str)
        assert corpus["version"] is None or isinstance(corpus["version"], str)
        assert isinstance(corpus["counts"], dict)
        assert all(isinstance(value, int) for value in corpus["counts"].values())


def test_knowledge_routes_publish_response_models() -> None:
    paths = app.openapi()["paths"]
    assert paths["/knowledge/search"]["post"]["responses"]["200"]["content"]["application/json"][
        "schema"
    ] == {"$ref": "#/components/schemas/KnowledgeSearchResponse"}
    assert paths["/knowledge/corpora"]["get"]["responses"]["200"]["content"]["application/json"][
        "schema"
    ] == {"$ref": "#/components/schemas/KnowledgeCorporaResponse"}
    schemas = app.openapi()["components"]["schemas"]
    for name in (
        "KnowledgeSearchResponse",
        "KnowledgeSearchChunk",
        "KnowledgeCorporaResponse",
        "KnowledgeCorpusInfo",
    ):
        assert name in schemas
