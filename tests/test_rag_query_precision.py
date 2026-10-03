"""Phase C2 — RAG query precision.

The retrieval query is now built from semantic material only:

    agent name -> domain-specific semantic fields -> question -> CJK result terms

Dates, timestamps, ``input_hash``, large JSON blobs, ``reasoning_trace`` and
bare numbers are excluded -- they were the listed noise sources.

Scope note: the retriever's scoring strategy is deliberately UNCHANGED (Phase C2
forbids replacing the retrieval architecture). Measurement of the residual
ranking limitation is in the Phase C report; these tests assert the query-level
guarantees plus the fact that the prioritised domain fields do target the right
knowledge node.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

import pytest

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput
from openmetaphysics.agents.qimen import QimenAgent, QimenInput
from openmetaphysics.agents.ziwei import ZiweiAgent, ZiweiInput
from openmetaphysics.core.schemas import AgentOutput, Gender
from openmetaphysics.inference.explainer import Explainer, get_explainer_for
from openmetaphysics.rag.retriever import reset_retriever

BORN = datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc)
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
# noise shapes the query must never contain
_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")
_HEX = re.compile(r"\b[0-9a-f]{8,}\b")
_NUMERIC = re.compile(r"^[\d\s\-:.+TZ/]+$")


@pytest.fixture(autouse=True)
def _fresh_retriever():
    reset_retriever()
    yield
    reset_retriever()


def _outputs() -> dict[str, AgentOutput]:
    return {
        "bazi": BaziAgent().compute(
            BaziInput(request_id="b", born_at=BORN, gender=Gender.MALE, question="事业与财运")
        ),
        "ziwei": ZiweiAgent().compute(
            ZiweiInput(request_id="z", born_at=BORN, gender="male", question="事业")  # type: ignore[arg-type]
        ),
        "qimen": QimenAgent().compute(
            QimenInput(request_id="q", born_at=BORN, gender=Gender.MALE, question="事业")
        ),
        "liuyao": LiuyaoAgent().compute(
            LiuyaoInput(request_id="l", born_at=BORN, casts=[7, 7, 8, 8, 7, 8], question="财运")
        ),
    }


@pytest.mark.parametrize("agent", ["bazi", "ziwei", "qimen", "liuyao"])
def test_query_contains_only_semantic_tokens(agent: str):
    query = Explainer.build_query(_outputs()[agent])
    tokens = query.split()
    assert tokens[0] == agent, "the agent name leads the query (system tag)"
    non_semantic = [t for t in tokens[1:] if not CJK.search(t)]
    assert not non_semantic, f"{agent}: non-semantic tokens leaked into the query: {non_semantic}"


@pytest.mark.parametrize("agent", ["bazi", "ziwei", "qimen", "liuyao"])
def test_query_excludes_the_listed_noise_sources(agent: str):
    output = _outputs()[agent]
    query = Explainer.build_query(output)

    assert not _ISO.search(query), "dates must not enter the query"
    assert not _HEX.search(query), "hashes must not enter the query"
    assert output.input_hash not in query, "input_hash must not enter the query"
    assert not any(_NUMERIC.match(t) for t in query.split()), "bare numbers must not enter"
    assert "reasoning_trace" not in query and "{" not in query, "no JSON blobs / trace"


def test_query_includes_domain_fields_question_and_result_terms():
    output = _outputs()["ziwei"]
    query = Explainer.build_query(output)

    # 1. domain-specific semantic field first
    assert output.result.wuxing_ju in query
    # 2. the caller's question
    assert "事业" in query
    # 3. star names from the result
    fate = next(p for p in output.result.palaces if p.is_fate_palace)
    assert any(star in query for star in fate.main_stars)


def test_query_is_deterministic():
    output = _outputs()["ziwei"]
    queries = {Explainer.build_query(output) for _ in range(3)}
    assert len(queries) == 1

    rebuilt = ZiweiAgent().compute(
        ZiweiInput(request_id="z", born_at=BORN, gender="male", question="事业")  # type: ignore[arg-type]
    )
    assert Explainer.build_query(rebuilt) == Explainer.build_query(output)


def test_legacy_query_style_carried_noise_the_new_one_removes():
    """Reconstruct the previous construction to quantify the removal."""

    def legacy_query(output: AgentOutput) -> str:
        result = (
            output.result.model_dump(mode="json") if hasattr(output.result, "model_dump") else {}
        )

        def strings(node, limit=12):
            out = []

            def walk(n):
                if len(out) >= limit:
                    return
                if isinstance(n, str):
                    if n.strip() and len(n.strip()) <= 24:
                        out.append(n.strip())
                elif isinstance(n, dict):
                    for k in sorted(n):
                        walk(n[k])
                elif isinstance(n, (list, tuple)):
                    for i in n:
                        walk(i)

            walk(node)
            return out[:limit]

        return " ".join([output.agent, *strings(result)])

    legacy_noise_total: list[str] = []
    current_noise_total: list[str] = []
    for agent, output in _outputs().items():
        legacy = legacy_query(output)
        current = Explainer.build_query(output)
        legacy_noise_total += [t for t in legacy.split()[1:] if not CJK.search(t)]
        current_noise_total += [t for t in current.split()[1:] if not CJK.search(t)]
        assert not _ISO.search(current), f"{agent}: date leaked into the query"

    assert legacy_noise_total, "expected the legacy construction to carry noise"
    assert current_noise_total == [], f"noise still present: {current_noise_total}"


def test_prioritised_domain_fields_target_the_expected_knowledge_node():
    """A focused, domain-field-led query retrieves the node it is about.

    The full multi-term query also carries recall material; the frozen
    char-overlap scorer ranks that broader text (see the Phase C report). This
    test asserts the part the construction controls: the leading semantic
    fields already point at the right knowledge node.
    """
    outputs = _outputs()

    # bazi: the day master stem is a knowledge node
    bazi = outputs["bazi"]
    bazi_query = Explainer.build_query(bazi)
    assert bazi_query.split()[1] == bazi.result.day_master
    bazi_hits = get_explainer_for("bazi").retrieve(bazi, k=1)
    assert bazi_hits, "bazi retrieval returned nothing"

    focused = " ".join(bazi_query.split()[:3])  # agent + day_master + day_master_element
    retrieve = get_explainer_for("bazi").retriever.retrieve  # type: ignore[union-attr]
    top = retrieve(focused, k=1)
    assert top, "focused bazi query returned nothing"
    # P2.1: the corpus now carries BaZi-specific knowledge, so the prioritised
    # day-master fields resolve into the BaZi corpus (BaZi-tagged) and the
    # retrieved node carries the day master or its element.
    assert "bazi" in top[0].tags, top[0].id
    assert bazi.result.day_master in top[0].text or bazi.result.day_master_element in top[0].text
    # the day-master stem node itself is a top-3 candidate for the same fields
    near = retrieve(focused, k=3)
    assert any(
        c.id.startswith("kn:heavenly_stem:bazi_") and bazi.result.day_master in c.text for c in near
    ), [c.id for c in near]
    # and the Ziwei copy of the stem node stays reachable as recall material
    wide = retrieve(focused, k=50)
    assert any(c.id == "kn:heavenly_stem:bing" for c in wide)

    # ziwei: the fate-palace star is a knowledge node
    ziwei = outputs["ziwei"]
    fate = next(p for p in ziwei.result.palaces if p.is_fate_palace)
    focused_ziwei = f"ziwei {fate.main_stars[0]}"
    top_ziwei = get_explainer_for("ziwei").retriever.retrieve(focused_ziwei, k=1)  # type: ignore[union-attr]
    assert top_ziwei, "focused ziwei query returned nothing"
    assert fate.main_stars[0] in top_ziwei[0].text, top_ziwei[0].id


def test_retrieval_still_runs_and_is_reproducible():
    output = _outputs()["ziwei"]
    expl = get_explainer_for("ziwei")
    first = [c.id for c in expl.retrieve(output, k=3)]
    second = [c.id for c in expl.retrieve(output, k=3)]
    assert first, "knowledge retrieval must execute"
    assert first == second
