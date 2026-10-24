"""RAG retriever. Qdrant when configured; in-memory fallback keeps tests offline."""

from __future__ import annotations

import math
import uuid
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


def _point_id(chunk_id: str) -> str:
    """Deterministic Qdrant point id (UUIDv5) for a chunk id.

    Qdrant point ids must be UUIDs or unsigned integers; chunk ids are
    ``kn:<type>:<name>`` strings, so a namespaced UUIDv5 keeps them stable.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"openmetaphysics:{chunk_id}"))


class QdrantRetriever:
    """Qdrant-backed retriever with ingestion and deterministic point ids.

    Lazily imports ``qdrant_client`` (optional ``[rag]`` extra) and requires an
    inference provider for embeddings. ``get_retriever`` falls back to the
    in-memory retriever when either is unavailable, so enabling Qdrant never
    yields a silently empty knowledge path.
    """

    def __init__(self, url: str, collection: str) -> None:
        self.url = url
        self.collection = collection
        self._client = None
        self._vector_size: int | None = None

    def _ensure(self):
        if self._client is None:
            from qdrant_client import QdrantClient  # type: ignore

            self._client = QdrantClient(url=self.url)
        return self._client

    def _ensure_collection(self, size: int) -> None:
        """Create the collection on first ingest (idempotent per size)."""
        if self._vector_size == size:
            return
        client = self._ensure()
        if hasattr(client, "collection_exists"):
            exists = client.collection_exists(self.collection)
        else:  # pragma: no cover - legacy client path
            names = {c.name for c in client.get_collections().collections}
            exists = self.collection in names
        if not exists:
            client.create_collection(
                collection_name=self.collection,
                vectors_config={"size": size, "distance": "Cosine"},
            )
        self._vector_size = size

    def add(self, chunk: KnowledgeChunk) -> None:
        """Embed and upsert one chunk; raises when no provider is configured."""
        client = self._ensure()
        from ..inference.providers import get_provider  # local import to avoid cycle

        provider = get_provider()
        if provider is None:
            raise RuntimeError("Qdrant ingestion requires an inference provider")
        vec = list(provider.embed(chunk.text, model=get_settings().ollama_model))
        if not vec:
            raise RuntimeError(f"empty embedding for chunk {chunk.id}")
        self._ensure_collection(len(vec))
        client.upsert(
            collection_name=self.collection,
            points=[
                {
                    "id": _point_id(chunk.id),
                    "vector": vec,
                    "payload": chunk.model_dump(),
                }
            ],
        )

    def retrieve(self, query: str, *, k: int = 5) -> list[KnowledgeChunk]:
        client = self._ensure()
        from ..inference.providers import get_provider  # local import to avoid cycle

        provider = get_provider()
        if provider is None:
            return []
        vec = list(provider.embed(query, model=get_settings().ollama_model))
        if not vec:
            return []
        if hasattr(client, "query_points"):
            response = client.query_points(
                collection_name=self.collection, query=vec, limit=k
            )
            points = getattr(response, "points", response)
        else:  # pragma: no cover - legacy client path
            points = client.search(
                collection_name=self.collection, query_vector=vec, limit=k
            )
        out = []
        for p in points:
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
_default_evidence: KnowledgeRetriever | None = None


def _load_default_corpus(retriever: InMemoryRetriever) -> int:
    """Load the frozen Knowledge corpora into the in-memory retriever.

    P2.1: every registered domain corpus (Ziwei + BaZi) is indexed into the
    same retriever -- no second retriever and no architecture change. Degrades
    to an empty retriever when the corpora are unavailable, so the offline
    default path never raises; a missing domain corpus simply contributes no
    chunks to the others.
    """
    try:
        from .corpus import load_all_into

        return load_all_into(retriever)
    except Exception:
        return 0


def get_retriever() -> KnowledgeRetriever:
    global _default
    if _default is None:
        s = get_settings()
        if s.rag_enabled and s.qdrant_url:
            qdrant = QdrantRetriever(s.qdrant_url, s.qdrant_collection)
            try:
                from .corpus import load_all_into

                load_all_into(qdrant)
                _default = qdrant
            except Exception:
                # No qdrant-client, no provider, or no reachable server:
                # degrade to the populated in-memory retriever instead of an
                # empty knowledge path.
                retriever = InMemoryRetriever()
                _load_default_corpus(retriever)
                _default = retriever
        else:
            retriever = InMemoryRetriever()
            _load_default_corpus(retriever)
            _default = retriever
    return _default


def get_evidence_retriever() -> KnowledgeRetriever:
    """Node + relation/reference retrieval (opt-in; explain keeps nodes only)."""
    global _default_evidence
    if _default_evidence is None:
        from .corpus import load_all_chunks

        retriever = InMemoryRetriever(load_all_chunks(include_evidence=True))
        if not retriever.chunks:
            # corpus unavailable: fall back to the populated default retriever
            return get_retriever()
        _default_evidence = retriever
    return _default_evidence


def search_knowledge(
    query: str, *, k: int = 5, include_evidence: bool = False
) -> list[KnowledgeChunk]:
    """Retrieve knowledge chunks; nodes only by default, evidence opt-in."""
    if include_evidence:
        return get_evidence_retriever().retrieve(query, k=k)
    return get_retriever().retrieve(query, k=k)


def reset_retriever() -> None:
    global _default, _default_evidence
    _default = None
    _default_evidence = None
