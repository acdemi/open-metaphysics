"""Knowledge corpus loader — frozen corpus JSON -> KnowledgeChunk[].

Real-data ingestion path for the in-memory RAG MVP:

    knowledge/ziwei_corpus.json
        -> load_corpus()
        -> node_to_chunk()
        -> KnowledgeChunk[]
        -> Retriever.add()

The corpus is the frozen Knowledge artifact (``corpus_id: ziwei_corpus``,
``status: frozen``, ``version: 1.0.0``). This loader is read-only: it does
not modify the corpus and does not re-implement Knowledge behavior.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .retriever import KnowledgeChunk, KnowledgeRetriever

# repository root: src/openmetaphysics/rag/corpus.py -> parents[3]
DEFAULT_CORPUS_PATH = Path(__file__).resolve().parents[3] / "knowledge" / "ziwei_corpus.json"


def resolve_corpus_path(path: str | Path | None = None) -> Path:
    """Return the corpus path (explicit override or the repository default)."""
    return Path(path) if path is not None else DEFAULT_CORPUS_PATH


def load_corpus(path: str | Path | None = None) -> dict[str, Any]:
    """Load the raw frozen corpus JSON."""
    return json.loads(resolve_corpus_path(path).read_text(encoding="utf-8"))


def node_to_chunk(node: dict[str, Any]) -> KnowledgeChunk:
    """Map one KnowledgeNode to a KnowledgeChunk.

    ``text`` carries the searchable prose (Chinese name + interpretation), which
    is what the character-level scorer compares against. ``tags`` carry the
    exact-match labels: node_type, systems, node tags and the English alias, so
    a system query such as ``"ziwei"`` or an exact alias query matches without
    polluting character overlap with ASCII. ``source`` carries the citation.
    """
    name_cn = str(node.get("name_cn", ""))
    name_en = str(node.get("name_en", ""))
    interpretation = str(node.get("interpretation", ""))

    source = node.get("source") or {}
    source_label = str(source.get("text", ""))
    chapter = source.get("chapter")
    if chapter:
        source_label = f"{source_label} · {chapter}" if source_label else str(chapter)

    tags: list[str] = []
    node_type = node.get("node_type")
    if node_type:
        tags.append(str(node_type))
    for system in node.get("systems", []) or []:
        tags.append(str(system))
    for tag in node.get("tags", []) or []:
        tags.append(str(tag))
    if name_en:
        tags.append(name_en)

    text = " ".join(part for part in (name_cn, interpretation) if part)
    return KnowledgeChunk(
        id=str(node.get("id", "")),
        text=text,
        source=source_label,
        tags=tags,
    )


def load_chunks(path: str | Path | None = None) -> list[KnowledgeChunk]:
    """Load the frozen corpus and return one KnowledgeChunk per KnowledgeNode.

    Ordering follows the corpus order (which the pipeline emits sorted), so the
    result is deterministic.
    """
    corpus = load_corpus(path)
    return [node_to_chunk(node) for node in corpus.get("nodes", [])]


def load_into(
    retriever: KnowledgeRetriever,
    path: str | Path | None = None,
) -> int:
    """Load the corpus into a retriever; returns the number of chunks added."""
    chunks = load_chunks(path)
    for chunk in chunks:
        retriever.add(chunk)  # type: ignore[attr-defined]
    return len(chunks)
