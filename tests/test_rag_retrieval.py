"""RAG runtime wiring — corpus -> chunks -> retriever -> consumer.

Uses the frozen Knowledge corpus (``knowledge/ziwei_corpus.json``) as the real
data source; no mocks and no external vector store.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from openmetaphysics.agents.ziwei import ZiweiAgent, ZiweiInput
from openmetaphysics.inference.explainer import PROMPT_KNOWLEDGE_HEADER, Explainer
from openmetaphysics.rag.corpus import load_chunks, load_corpus, load_into, node_to_chunk
from openmetaphysics.rag.retriever import (
    InMemoryRetriever,
    KnowledgeChunk,
    get_retriever,
    reset_retriever,
)

BORN = datetime(1985, 8, 15, 2, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _reset_global_retriever():
    reset_retriever()
    yield
    reset_retriever()


# == Corpus loading ==


def test_corpus_loads_real_knowledge_data():
    corpus = load_corpus()
    assert corpus["metadata"]["corpus_id"] == "ziwei_corpus"
    assert corpus["metadata"]["status"] == "frozen"

    chunks = load_chunks()
    assert chunks, "real corpus produced no chunks"
    assert len(chunks) == len(corpus["nodes"]) == corpus["metadata"]["counts"]["nodes"]
    assert len(chunks) >= 100

    ids = [c.id for c in chunks]
    assert len(set(ids)) == len(ids), "chunk ids must be unique"
    assert all(c.text.strip() for c in chunks), "every chunk needs searchable text"
    assert all(c.id.startswith("kn:") for c in chunks)


def test_node_to_chunk_maps_contract_fields():
    node = load_corpus()["nodes"][0]
    chunk = node_to_chunk(node)
    assert chunk.id == node["id"]
    assert node["name_cn"] in chunk.text
    assert node["interpretation"][:20] in chunk.text
    # node_type / systems / tags / english alias are exact-match labels
    assert node["node_type"] in chunk.tags
    assert node["name_en"] in chunk.tags
    for system in node["systems"]:
        assert system in chunk.tags
    assert chunk.source, "citation text should be carried through"


def test_load_into_returns_chunk_count_and_populates_retriever():
    r = InMemoryRetriever()
    assert r.retrieve("文昌") == []
    added = load_into(r)
    assert added == len(r.chunks) == 102


# == Retrieval ==


def test_real_query_returns_real_knowledge_chunks():
    r = InMemoryRetriever(load_chunks())
    hits = r.retrieve("文昌", k=3)
    assert hits, "a real corpus query must return chunks"
    assert hits[0].id == "kn:auxiliary_star:wen_chang"
    assert "昌" in hits[0].text
    assert hits[0].source  # citation preserved


def test_system_tag_query_matches_tagged_chunks():
    r = InMemoryRetriever(load_chunks())
    hits = r.retrieve("ziwei", k=5)
    assert hits
    assert all("ziwei" in c.tags for c in hits)


def test_single_chunk_retriever():
    r = InMemoryRetriever()
    r.add(KnowledgeChunk(id="c1", text="天乙贵人", tags=["shen_sha"]))
    assert [c.id for c in r.retrieve("天乙")] == ["c1"]
    assert r.retrieve("zzzz") == []


def test_multiple_chunks_ranked_deterministically():
    r = InMemoryRetriever(
        [
            KnowledgeChunk(id="b", text="文昌"),
            KnowledgeChunk(id="a", text="文昌"),
            KnowledgeChunk(id="c", text="文"),
        ]
    )
    hits = r.retrieve("文昌", k=5)
    # equal score -> ascending id
    assert [c.id for c in hits[:2]] == ["a", "b"]
    assert hits[2].id == "c"


# == Empty / no result ==


def test_empty_corpus_returns_nothing():
    assert InMemoryRetriever().retrieve("文昌") == []


def test_query_with_no_overlap_returns_nothing():
    r = InMemoryRetriever(load_chunks())
    # '@' does not occur anywhere in the corpus text or tags
    assert r.retrieve("@@@@@") == []


def test_blank_query_returns_nothing():
    r = InMemoryRetriever(load_chunks())
    assert r.retrieve("") == []
    assert r.retrieve("   ") == []


# == k ==


def test_k_limits_result_count():
    r = InMemoryRetriever(load_chunks())
    assert len(r.retrieve("紫微", k=1)) == 1
    assert len(r.retrieve("紫微", k=3)) == 3
    # larger k never returns fewer results, and never more than the corpus
    big = r.retrieve("紫微", k=1000)
    assert len(big) > 3
    assert len(big) <= len(r.chunks)
    # only chunks with a positive score are returned
    assert len(big) < len(r.chunks)
    assert r.retrieve("紫微", k=0) == []
    assert r.retrieve("紫微", k=-1) == []


# == Determinism ==


def test_determinism_same_corpus_and_query():
    r = InMemoryRetriever(load_chunks())
    first = [c.id for c in r.retrieve("紫微 天府", k=10)]
    second = [c.id for c in r.retrieve("紫微 天府", k=10)]
    assert first == second

    rebuilt = [c.id for c in InMemoryRetriever(load_chunks()).retrieve("紫微 天府", k=10)]
    assert first == rebuilt, "reloading the same corpus must give the same ranking"


# == Consumer wiring (corpus -> retriever -> explainer context) ==


def test_get_retriever_is_populated_from_frozen_corpus():
    """P2.1/P2.2: the default retriever indexes *every* domain corpus.

    The frozen Ziwei corpus keeps its 102 nodes, loaded first and unchanged;
    the P2.1 BaZi and P2.2 Qimen corpora are indexed alongside it in the same
    retriever (same architecture, no second retriever), and chunk ids stay
    globally unique.
    """
    r = get_retriever()
    ids = [c.id for c in getattr(r, "chunks", [])]

    ziwei_ids = [c.id for c in load_chunks()]
    assert len(ziwei_ids) == 102
    assert ids[: len(ziwei_ids)] == ziwei_ids, "the frozen corpus loads first, unchanged"
    assert any(i.startswith("kn:wuxing:bazi_") for i in ids), "the BaZi corpus must be indexed"
    assert any(i.startswith("kn:ten_god:bazi_") for i in ids)
    assert any(i.startswith("kn:palace:qimen_") for i in ids), "the Qimen corpus must be indexed"
    assert any(i.startswith("kn:pattern:qimen_") for i in ids)
    assert len(set(ids)) == len(ids), "chunk ids must be unique across domains"


def test_explainer_receives_real_context():
    class _CapturingProvider:
        def __init__(self) -> None:
            self.prompt: str | None = None

        def generate(self, prompt: str, **kwargs: object) -> str:
            self.prompt = prompt
            return "ok"

    provider = _CapturingProvider()
    output = ZiweiAgent().compute(
        ZiweiInput(request_id="z1", born_at=BORN, gender="male")  # type: ignore[arg-type]
    )
    Explainer(provider=provider, retriever=get_retriever()).render(output)

    assert provider.prompt is not None
    assert PROMPT_KNOWLEDGE_HEADER in provider.prompt, "retriever produced no context"
    # the injected context must be real corpus prose, not a placeholder.
    # Phase A3: the pipeline derives the query from the deterministic result,
    # so assert against the same query the pipeline uses.
    expl = Explainer(provider=provider, retriever=get_retriever())
    chunks = expl.retrieve(output, k=3)
    assert chunks
    assert chunks[0].text[:12] in provider.prompt
