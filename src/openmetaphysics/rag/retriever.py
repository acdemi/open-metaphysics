"""RAG retriever. Qdrant when configured; in-memory fallback keeps tests offline."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from ..core.config import get_settings


class KnowledgeChunk(BaseModel):
    id: str
    text: str
    source: str = ""
    tags: list[str] = []


@runtime_checkable
class KnowledgeRetriever(Protocol):
    def retrieve(self, query: str, *, k: int = 5) -> list[KnowledgeChunk]: ...


class InMemoryRetriever:
    """Deterministic keyword-overlap scorer over a local chunk list."""

    def __init__(self, chunks: list[KnowledgeChunk] | None = None) -> None:
        self.chunks = chunks or []

    def add(self, chunk: KnowledgeChunk) -> None:
        self.chunks.append(chunk)

    def retrieve(self, query: str, *, k: int = 5) -> list[KnowledgeChunk]:
        q = set(query)  # CJK char-level overlap
        scored = []
        for c in self.chunks:
            hay = set(c.text) | set(c.tags)
            score = len(q & hay)
            scored.append((score, c))
        scored.sort(key=lambda t: (-t[0], t[1].id))
        return [c for _, c in scored[:k] if _ > 0] or []


class QdrantRetriever:
    """Qdrant-backed retriever. Lazily imports qdrant_client; degrades on failure."""

    def __init__(self, url: str, collection: str) -> None:
        self.url = url
        self.collection = collection
        self._client = None

    def _ensure(self):
        if self._client is None:
            from qdrant_client import QdrantClient  # type: ignore

            self._client = QdrantClient(url=self.url)
        return self._client

    def retrieve(self, query: str, *, k: int = 5) -> list[KnowledgeChunk]:
        client = self._ensure()
        from ..inference.providers import get_provider  # local import to avoid cycle

        provider = get_provider()
        if provider is None:
            return []
        vec = provider.embed(query, model=get_settings().ollama_model)
        res = client.search(collection_name=self.collection, query_vector=vec, limit=k)
        out = []
        for p in res:
            payload = p.payload or {}
            out.append(
                KnowledgeChunk(
                    id=str(payload.get("id", p.id)),
                    text=str(payload.get("text", "")),
                    source=str(payload.get("source", "")),
                    tags=list(payload.get("tags", [])),
                )
            )
        return out


_default: KnowledgeRetriever | None = None


def get_retriever() -> KnowledgeRetriever:
    global _default
    if _default is None:
        s = get_settings()
        if s.rag_enabled and s.qdrant_url:
            _default = QdrantRetriever(s.qdrant_url, s.qdrant_collection)
        else:
            _default = InMemoryRetriever()
    return _default


def reset_retriever() -> None:
    global _default
    _default = None
