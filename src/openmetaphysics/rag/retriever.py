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
        """Deterministic keyword retrieval: character overlap + whole-tag match.

        Strategy is unchanged from the original (no embeddings, no external
        service); the fixes are that tags are matched as whole labels instead of
        being folded into single characters, and ``k <= 0`` returns nothing.
        Ranking is by descending score then ascending chunk id, so results are
        stable for a given corpus and query.
        """
        if k <= 0:
            return []
        q = query.strip().lower()
        if not q:
            return []
        qchars = set(q)  # CJK char-level overlap
        scored = []
        for c in self.chunks:
            score = len(qchars & set(c.text.lower()))
            for tag in c.tags:
                label = tag.strip().lower()
                if label and label in q:
                    score += 1
            scored.append((score, c))
        scored.sort(key=lambda t: (-t[0], t[1].id))
        return [c for score, c in scored[:k] if score > 0]


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


def _load_default_corpus(retriever: InMemoryRetriever) -> int:
    """Load the frozen Knowledge corpus into the in-memory retriever.

    Degrades to an empty retriever when the corpus is unavailable, so the
    offline default path never raises.
    """
    try:
        from .corpus import load_into

        return load_into(retriever)
    except Exception:
        return 0


def get_retriever() -> KnowledgeRetriever:
    global _default
    if _default is None:
        s = get_settings()
        if s.rag_enabled and s.qdrant_url:
            _default = QdrantRetriever(s.qdrant_url, s.qdrant_collection)
        else:
            retriever = InMemoryRetriever()
            _load_default_corpus(retriever)
            _default = retriever
    return _default


def reset_retriever() -> None:
    global _default
    _default = None
