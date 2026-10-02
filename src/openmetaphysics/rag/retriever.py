"""RAG retriever. Qdrant when configured; in-memory fallback keeps tests offline."""

from __future__ import annotations

import math
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
    """Deterministic keyword-overlap scorer over a local chunk list.

    Scoring is character overlap plus whole-tag matching, weighted so that
    characters which are rare across the indexed corpus count for more than
    ubiquitous ones (Phase C2 finalization). Same retriever, same public API,
    same architecture -- no embeddings, no external service.
    """

    def __init__(self, chunks: list[KnowledgeChunk] | None = None) -> None:
        self.chunks = chunks or []
        self._weights: dict[str, float] | None = None

    def add(self, chunk: KnowledgeChunk) -> None:
        self.chunks.append(chunk)
        self._weights = None

    def _char_weights(self) -> dict[str, float]:
        """Rare-term weights over the indexed corpus: ``1 + ln(N / df(ch))``.

        A character occurring in every chunk weighs ``1.0``; one occurring in a
        single chunk weighs ``1 + ln(N)``. Deterministic and cached;
        invalidated by ``add``.
        """
        if self._weights is None:
            total = len(self.chunks)
            document_frequency: dict[str, int] = {}
            for chunk in self.chunks:
                for ch in set(chunk.text.lower()):
                    document_frequency[ch] = document_frequency.get(ch, 0) + 1
            self._weights = {
                ch: 1.0 + math.log(total / count) for ch, count in document_frequency.items()
            }
        return self._weights

    def retrieve(self, query: str, *, k: int = 5) -> list[KnowledgeChunk]:
        """Deterministic keyword retrieval: weighted character overlap + whole-tag match.

        Strategy is unchanged (no embeddings, no external service). The scoring
        change is that each overlapping character contributes its corpus-rarity
        weight instead of a flat 1, so query expansion no longer dilutes rare
        semantic terms. Whole-tag matching, ``k <= 0`` and the ``score > 0``
        filter behave as before. Ranking is by descending score then ascending
        chunk id, so results are stable for a given corpus and query.
        """
        if k <= 0:
            return []
        q = query.strip().lower()
        if not q:
            return []
        qchars = set(q)  # CJK char-level overlap
        weights = self._char_weights()
        scored = []
        for c in self.chunks:
            # sorted() keeps the float summation order stable across processes
            score = sum(weights.get(ch, 1.0) for ch in sorted(qchars & set(c.text.lower())))
            for tag in c.tags:
                label = tag.strip().lower()
                if label and label in q:
                    score += 1.0
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
