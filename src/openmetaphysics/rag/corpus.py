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

P2.1 BaZi Knowledge Integration
-------------------------------

Each domain has its own deterministic corpus artifact in the same directory
(``ziwei_corpus.json``, ``bazi_corpus.json``). ``load_all_chunks`` /
``load_all_into`` index every registered domain into the same retriever --
one retriever, no second architecture, no embeddings and no external service.
The single-corpus API (``load_corpus`` / ``load_chunks`` / ``load_into``)
keeps its original meaning: the default corpus (Ziwei), unchanged.

P2.2 Qimen Knowledge Integration adds ``qimen_corpus.json`` to the same list.
No second loader, no second retriever, no scoring change.

P2.3 Liuyao Knowledge Integration adds ``liuyao_corpus.json`` the same way.

Cross-domain node ids are kept unique by the corpus validator
(``knowledge/validate.py``), so indexing every domain introduces no duplicate
chunk ids.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .retriever import KnowledgeChunk, KnowledgeRetriever

# repository root: src/openmetaphysics/rag/corpus.py -> parents[3]
DEFAULT_CORPUS_PATH = Path(__file__).resolve().parents[3] / "knowledge" / "ziwei_corpus.json"

# Every domain corpus indexed by the default retriever, in deterministic order.
# The file names are resolved relative to the default corpus directory, so an
# explicit path override (or a test patch of DEFAULT_CORPUS_PATH) still applies.
DOMAIN_CORPUS_FILES: tuple[str, ...] = (
    "ziwei_corpus.json",
    "bazi_corpus.json",
    "qimen_corpus.json",
    "liuyao_corpus.json",
)


def resolve_corpus_path(path: str | Path | None = None) -> Path:
    """Return the corpus path (explicit override or the repository default)."""
    return Path(path) if path is not None else DEFAULT_CORPUS_PATH


def resolve_corpus_paths(base: str | Path | None = None) -> list[Path]:
    """Return every registered domain corpus path, in deterministic order.

    ``base`` overrides the default corpus file (its directory is used); the
    default is read from ``DEFAULT_CORPUS_PATH`` at call time so that patching
    it (as the degradation tests do) also applies to the multi-domain path.
    """
    directory = (Path(base) if base is not None else DEFAULT_CORPUS_PATH).parent
    return [directory / name for name in DOMAIN_CORPUS_FILES]


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
    """Load one frozen corpus and return one KnowledgeChunk per KnowledgeNode.

    Ordering follows the corpus order (which the pipeline emits sorted), so the
    result is deterministic.
    """
    corpus = load_corpus(path)
    return [node_to_chunk(node) for node in corpus.get("nodes", [])]


def load_all_chunks(base: str | Path | None = None) -> list[KnowledgeChunk]:
    """Load every available domain corpus into one deterministic chunk list.

    A domain whose corpus file is absent is skipped (offline degradation), so a
    missing BaZi corpus never disables the frozen Ziwei corpus and vice versa.
    """
    chunks: list[KnowledgeChunk] = []
    for path in resolve_corpus_paths(base):
        if path.is_file():
            chunks.extend(load_chunks(path))
    return chunks


def load_into(
    retriever: KnowledgeRetriever,
    path: str | Path | None = None,
) -> int:
    """Load the default corpus into a retriever; returns the number of chunks added."""
    chunks = load_chunks(path)
    for chunk in chunks:
        retriever.add(chunk)  # type: ignore[attr-defined]
    return len(chunks)


def load_all_into(retriever: KnowledgeRetriever, base: str | Path | None = None) -> int:
    """Load every available domain corpus into a retriever.

    Returns the number of chunks added. One retriever serves all domains: the
    domain distinction is carried by the chunk tags (``systems``), which the
    existing scorer already uses for exact-match filtering.
    """
    chunks = load_all_chunks(base)
    for chunk in chunks:
        retriever.add(chunk)  # type: ignore[attr-defined]
    return len(chunks)
