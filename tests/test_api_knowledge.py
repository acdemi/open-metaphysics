"""Knowledge retrieval HTTP endpoint (frozen corpora, offline)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from openmetaphysics.api.app import create_app

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
