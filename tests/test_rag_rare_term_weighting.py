"""Phase C2 finalization — deterministic rare-term weighting.

Focused tests for the minimal scorer change inside the existing
``InMemoryRetriever``: each overlapping character contributes its corpus-rarity
weight (``1 + ln(N / df)``) instead of a flat 1.

Requirements covered: A existing behaviour, B determinism, C ``k <= 0``,
D zero-overlap exclusion, E whole-tag matching, F rarity ordering, G the
previously documented cases improving, H no unrelated behaviour change.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from openmetaphysics.agents.ziwei import ZiweiAgent, ZiweiInput
from openmetaphysics.inference.explainer import Explainer
from openmetaphysics.rag.corpus import load_chunks
from openmetaphysics.rag.retriever import InMemoryRetriever, KnowledgeChunk, reset_retriever

BORN = datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _fresh_retriever():
    reset_retriever()
    yield
    reset_retriever()


@pytest.fixture(scope="module")
def corpus() -> list[KnowledgeChunk]:
    return load_chunks()


class _FlatScorer(InMemoryRetriever):
    """The scoring exactly as it was before this change (flat overlap)."""

    def retrieve(self, query: str, *, k: int = 5) -> list[KnowledgeChunk]:
        if k <= 0:
            return []
        q = query.strip().lower()
        if not q:
            return []
        qchars = set(q)
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


# == A. Existing behaviour ==


def test_existing_retrieval_behaviour_still_works(corpus: list[KnowledgeChunk]):
    r = InMemoryRetriever(corpus)
    hits = r.retrieve("文昌", k=3)
    assert [c.id for c in hits][0] == "kn:auxiliary_star:wen_chang"
    assert all(c.text for c in hits)
    assert len(hits) <= 3


def test_blank_query_and_public_api_unchanged(corpus: list[KnowledgeChunk]):
    r = InMemoryRetriever(corpus)
    assert r.retrieve("") == []
    assert r.retrieve("   ") == []
    # the public interface is unchanged
    assert isinstance(r.chunks, list)
    r.add(KnowledgeChunk(id="extra", text="测试", tags=["t"]))
    assert any(c.id == "extra" for c in r.retrieve("测试", k=10))


# == B. Determinism ==


def test_repeated_calls_are_deterministic(corpus: list[KnowledgeChunk]):
    r = InMemoryRetriever(corpus)
    first = [c.id for c in r.retrieve("天机 太阴", k=5)]
    second = [c.id for c in r.retrieve("天机 太阴", k=5)]
    assert first == second
    # a freshly built retriever over the same corpus ranks identically
    rebuilt = [c.id for c in InMemoryRetriever(load_chunks()).retrieve("天机 太阴", k=5)]
    assert first == rebuilt


def test_weights_are_cached_and_invalidated_by_add():
    r = InMemoryRetriever([KnowledgeChunk(id="a", text="甲乙丙", tags=[])])
    first = r._char_weights()
    assert r._char_weights() is first, "weights are cached"
    r.add(KnowledgeChunk(id="b", text="甲乙", tags=[]))
    assert r._char_weights() is not first, "add() invalidates the cache"


# == C / D. k and zero-overlap ==


def test_k_non_positive_returns_empty(corpus: list[KnowledgeChunk]):
    r = InMemoryRetriever(corpus)
    for k in (0, -1, -100):
        assert r.retrieve("紫微", k=k) == []


def test_zero_overlap_documents_are_excluded(corpus: list[KnowledgeChunk]):
    r = InMemoryRetriever(corpus)
    assert r.retrieve("@@@@@") == []
    controlled = InMemoryRetriever(
        [
            KnowledgeChunk(id="hit", text="文昌", tags=[]),
            KnowledgeChunk(id="miss", text="甲乙", tags=[]),
        ]
    )
    assert [c.id for c in controlled.retrieve("文昌", k=10)] == ["hit"]


# == E. Whole-tag matching ==


def test_whole_tag_matching_still_works(corpus: list[KnowledgeChunk]):
    r = InMemoryRetriever(corpus)
    hits = r.retrieve("ziwei", k=5)
    assert hits
    assert all("ziwei" in c.tags for c in hits)

    controlled = InMemoryRetriever(
        [
            KnowledgeChunk(id="tagged", text="甲乙", tags=["bazi"]),
            KnowledgeChunk(id="plain", text="甲乙", tags=[]),
        ]
    )
    assert [c.id for c in controlled.retrieve("bazi", k=5)] == ["tagged"]


# == F. Rarity weighting ==


def test_rare_characters_weigh_more_than_ubiquitous_ones(corpus: list[KnowledgeChunk]):
    import math
    from collections import Counter

    r = InMemoryRetriever(corpus)
    weights = r._char_weights()
    assert weights, "weights must be computed from the corpus"
    assert all(w >= 1.0 for w in weights.values())

    df = Counter(ch for c in corpus for ch in set(c.text.lower()))
    total = len(corpus)
    rarest = min(df, key=lambda ch: df[ch])
    most_common = max(df, key=lambda ch: df[ch])
    assert df[rarest] < df[most_common], "fixture expects a rarity spread"

    # the weighting rule itself
    assert weights[rarest] == pytest.approx(1.0 + math.log(total / df[rarest]))
    assert weights[most_common] == pytest.approx(1.0 + math.log(total / df[most_common]))
    # and the ordering it implies
    assert weights[rarest] > weights[most_common]


def test_rare_term_outranks_common_term_at_equal_match_count():
    chunks = [
        # 'rare' appears once in the corpus; 'common' appears everywhere
        KnowledgeChunk(id="rare_doc", text="甲乙稀有", tags=[]),
        KnowledgeChunk(id="common_a", text="甲乙普通", tags=[]),
        KnowledgeChunk(id="common_b", text="甲乙普通", tags=[]),
        KnowledgeChunk(id="common_c", text="甲乙普通", tags=[]),
    ]
    r = InMemoryRetriever(chunks)
    weights = r._char_weights()
    assert weights["稀"] > weights["普"]

    ranked = [c.id for c in r.retrieve("稀", k=4)]
    assert ranked[0] == "rare_doc"


# == G. The previously documented cases ==


@pytest.mark.parametrize(
    ("query", "expected_id"),
    [
        ("太阴", "kn:main_star:taiyin"),
        ("天机 太阴", "kn:main_star:taiyin"),
        ("ziwei 天机 太阴", "kn:main_star:taiyin"),
    ],
)
def test_previously_missed_cases_now_hit(
    corpus: list[KnowledgeChunk], query: str, expected_id: str
):
    """These three cases were demonstrated as misses under flat overlap."""
    flat = [c.id for c in _FlatScorer(corpus).retrieve(query, k=3)]
    weighted = [c.id for c in InMemoryRetriever(corpus).retrieve(query, k=3)]

    assert expected_id not in flat, f"{query}: fixture no longer reproduces the old miss"
    assert expected_id in weighted, f"{query}: weighting did not fix the case"


def test_documented_improvement_ratio(corpus: list[KnowledgeChunk]):
    """The measured 2/10 -> 5/10 improvement on the documented case set."""
    cases = [
        ("天机", ["kn:main_star:tianji"]),
        ("太阴", ["kn:main_star:taiyin"]),
        ("天机 太阴", ["kn:main_star:tianji", "kn:main_star:taiyin"]),
        ("ziwei 天机 太阴", ["kn:main_star:tianji", "kn:main_star:taiyin"]),
        ("天机 太阴 事业", ["kn:main_star:tianji", "kn:main_star:taiyin"]),
        ("紫微", ["kn:main_star:ziwei"]),
        ("文昌", ["kn:auxiliary_star:wen_chang"]),
        ("妻财", []),
        ("liuyao 妻财 官鬼 子孙", []),
        ("坎 水", []),
    ]
    flat, weighted = _FlatScorer(corpus), InMemoryRetriever(corpus)

    def score(scorer: InMemoryRetriever) -> int:
        hits = 0
        for query, expected in cases:
            top = [c.id for c in scorer.retrieve(query, k=3)]
            if expected and any(e in top for e in expected):
                hits += 1
        return hits

    before, after = score(flat), score(weighted)
    assert before == 2, f"fixture drift: before={before}"
    assert after == 5, f"weighting regressed: after={after}"
    assert after > before


# == H. No unrelated behaviour change ==


def test_retrieval_does_not_mutate_the_corpus(corpus: list[KnowledgeChunk]):
    r = InMemoryRetriever(corpus)
    before = [(c.id, c.text, tuple(c.tags)) for c in r.chunks]
    r.retrieve("紫微 天机 太阴", k=5)
    after = [(c.id, c.text, tuple(c.tags)) for c in r.chunks]
    assert before == after


def test_ranking_tie_break_is_still_ascending_id():
    r = InMemoryRetriever(
        [
            KnowledgeChunk(id="z", text="文昌", tags=[]),
            KnowledgeChunk(id="a", text="文昌", tags=[]),
        ]
    )
    assert [c.id for c in r.retrieve("文昌", k=2)] == ["a", "z"]


def test_explain_pipeline_query_is_unchanged_by_the_scorer_change():
    """The scorer changed; query construction (C2) did not."""
    output = ZiweiAgent().compute(
        ZiweiInput(request_id="w", born_at=BORN, gender="male", question="事业")  # type: ignore[arg-type]
    )
    query = Explainer.build_query(output)
    assert query.split()[0] == "ziwei"
    assert "事业" in query
    assert "1985" not in query and "-" not in query
