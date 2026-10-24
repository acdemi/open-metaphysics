"""Qdrant retriever hardening tests (offline, no qdrant server required).

Covers ingestion (create_collection + upsert), ``query_points`` retrieval with
legacy ``search`` fallback, deterministic point ids, and the in-memory
fallback when the optional qdrant-client or an inference provider is missing.
"""

from __future__ import annotations

import sys
import types
import uuid

import pytest

from openmetaphysics.core.config import reset_settings
from openmetaphysics.rag.corpus import load_all_chunks
from openmetaphysics.rag.retriever import (
    InMemoryRetriever,
    QdrantRetriever,
    _point_id,
    get_retriever,
    reset_retriever,
)


class _Point:
    def __init__(self, point_id: str, payload: dict) -> None:
        self.id = point_id
        self.payload = payload
        self.score = 1.0


class _BaseClient:
    instances: list[_BaseClient] = []

    def __init__(self, url: str) -> None:
        self.url = url
        self.collections: set[str] = set()
        self.points: list[_Point] = []
        self.upsert_calls = 0
        _BaseClient.instances.append(self)

    def collection_exists(self, name: str) -> bool:
        return name in self.collections

    def create_collection(self, collection_name: str, vectors_config: dict) -> None:
        assert vectors_config.get("size", 0) > 0
        self.collections.add(collection_name)

    def upsert(self, collection_name: str, points: list[dict]) -> None:
        self.upsert_calls += 1
        for point in points:
            self.points.append(_Point(point["id"], point["payload"]))


class _QueryClient(_BaseClient):
    query_points_calls = 0

    def query_points(self, collection_name: str, query: list[float], limit: int):
        self.query_points_calls += 1
        assert query, "query vector must not be empty"
        return types.SimpleNamespace(points=self.points[:limit])


class _LegacyClient(_BaseClient):
    search_calls = 0

    def search(self, collection_name: str, query_vector: list[float], limit: int):
        self.search_calls += 1
        return self.points[:limit]


class _FakeProvider:
    name = "fake"

    def generate(self, prompt: str, **kwargs: object) -> str:
        return "ok"

    def embed(self, text: str, *, model: str) -> list[float]:
        return [float(len(text) % 7), 0.5, 0.25]


def _install_fake_qdrant(monkeypatch: pytest.MonkeyPatch, client_cls) -> None:
    fake = types.ModuleType("qdrant_client")
    fake.QdrantClient = client_cls  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "qdrant_client", fake)


def _enable_qdrant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OM_RAG_ENABLED", "true")
    monkeypatch.setenv("OM_QDRANT_URL", "http://qdrant:6333")
    reset_settings()
    reset_retriever()
    _BaseClient.instances.clear()


def _fake_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "openmetaphysics.inference.providers.get_provider",
        lambda settings=None: _FakeProvider(),
    )


@pytest.fixture(autouse=True)
def _cleanup_state():
    yield
    reset_settings()
    reset_retriever()


def test_qdrant_ingests_corpus_and_retrieves_via_query_points(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_qdrant(monkeypatch, _QueryClient)
    _fake_provider(monkeypatch)
    _enable_qdrant(monkeypatch)

    retriever = get_retriever()
    assert isinstance(retriever, QdrantRetriever)
    client = _QueryClient.instances[-1]
    assert client.collections == {"openmetaphysics"}
    assert client.upsert_calls == len(load_all_chunks())

    results = retriever.retrieve("紫微", k=3)
    assert len(results) == 3
    assert client.query_points_calls == 1
    assert all(r.id.startswith("kn:") for r in results)


def test_qdrant_point_ids_are_deterministic_uuids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_qdrant(monkeypatch, _QueryClient)
    _fake_provider(monkeypatch)
    _enable_qdrant(monkeypatch)

    get_retriever()
    client = _QueryClient.instances[-1]
    ids = [p.id for p in client.points]
    assert ids
    assert all(uuid.UUID(i).version == 5 for i in ids)
    first_chunk_id = load_all_chunks()[0].id
    assert _point_id(first_chunk_id) in ids
    assert _point_id(first_chunk_id) == _point_id(first_chunk_id)


def test_qdrant_falls_back_to_inmemory_without_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_qdrant(monkeypatch, _QueryClient)
    monkeypatch.setattr(
        "openmetaphysics.inference.providers.get_provider",
        lambda settings=None: None,
    )
    _enable_qdrant(monkeypatch)

    retriever = get_retriever()
    assert isinstance(retriever, InMemoryRetriever)
    assert retriever.retrieve("紫微", k=1), "fallback must not be silently empty"


def test_qdrant_falls_back_when_client_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "qdrant_client", None)
    _fake_provider(monkeypatch)
    _enable_qdrant(monkeypatch)

    retriever = get_retriever()
    assert isinstance(retriever, InMemoryRetriever)
    assert retriever.retrieve("紫微", k=1)


def test_qdrant_retrieve_supports_legacy_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_qdrant(monkeypatch, _LegacyClient)
    _fake_provider(monkeypatch)
    _enable_qdrant(monkeypatch)

    retriever = get_retriever()
    client = _LegacyClient.instances[-1]
    results = retriever.retrieve("紫微", k=2)
    assert len(results) == 2
    assert client.search_calls == 1
