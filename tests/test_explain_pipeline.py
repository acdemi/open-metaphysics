"""Explain pipeline closure: calculation -> evidence -> knowledge -> explain.

Every test drives the REAL deterministic engines and the REAL frozen knowledge
corpus; the only stand-in is the LLM provider (a deterministic stub), which is
explicitly allowed by the phase rules since no commercial API may be used here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.agents.bazi_explainer import BaziExplainer
from openmetaphysics.agents.liuyao_explainer import LiuyaoExplainer
from openmetaphysics.agents.qimen_explainer import QimenExplainer
from openmetaphysics.agents.ziwei import ZiweiAgent, ZiweiInput
from openmetaphysics.agents.ziwei_explainer import ZiweiExplainer
from openmetaphysics.core.schemas import AgentOutput, Gender
from openmetaphysics.inference.explainer import (
    PROMPT_KNOWLEDGE_HEADER,
    Explainer,
    get_explainer_for,
)
from openmetaphysics.rag.retriever import reset_retriever

BORN = datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _reset_global_retriever():
    reset_retriever()
    yield
    reset_retriever()


class _CapturingProvider:
    """Deterministic stub provider; records the prompt it was handed."""

    name = "capturing-stub"

    def __init__(self, reply: str = "解释文本") -> None:
        self.prompt: str | None = None
        self.reply = reply

    def generate(self, prompt: str, **kwargs: Any) -> str:
        self.prompt = prompt
        return self.reply

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        return [0.0]


class _FailingProvider:
    name = "failing-stub"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        raise RuntimeError("provider exploded")

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        raise RuntimeError("provider exploded")


def _bazi_output() -> AgentOutput:
    return BaziAgent().compute(BaziInput(request_id="b1", born_at=BORN, gender=Gender.MALE))


def _ziwei_output() -> AgentOutput:
    return ZiweiAgent().compute(
        ZiweiInput(request_id="z1", born_at=BORN, gender="male")  # type: ignore[arg-type]
    )


# == Calculation -> Explain ==


def test_deterministic_result_enters_explain():
    output = _bazi_output()
    provider = _CapturingProvider()
    result = Explainer(provider=provider, retriever=None).explain(output)

    assert result["agent"] == "bazi"
    assert result["explanation"] == "解释文本"
    # the deterministic facts are carried into the explain request verbatim
    evidence = result["evidence"]
    assert evidence["result"] == output.result.model_dump(mode="json")
    assert evidence["input_hash"] == output.input_hash
    assert evidence["confidence"]["value"] == output.confidence.value
    assert evidence["reasoning_trace"][0]["rule_ref"]
    # and the provider saw the deterministic Result JSON
    assert provider.prompt is not None
    assert output.result.day_master in provider.prompt


def test_ziwei_deterministic_result_enters_explain():
    output = _ziwei_output()
    result = get_explainer_for("ziwei", provider=_CapturingProvider()).explain(output)
    assert result["evidence"]["result"]["wuxing_ju"] == output.result.wuxing_ju


# == Knowledge -> Explain ==


def test_retrieved_knowledge_enters_explain():
    output = _ziwei_output()
    provider = _CapturingProvider()
    result = Explainer(provider=provider, retriever=get_explainer_for("ziwei").retriever).explain(
        output, k=3
    )

    assert result["knowledge"], "no knowledge retrieved from the frozen corpus"
    ids = [c["id"] for c in result["knowledge"]]
    assert all(i.startswith("kn:") for i in ids)
    assert all(c["source"] for c in result["knowledge"]), "citations must be preserved"
    # retrieved knowledge reaches the LLM prompt as authoritative context
    assert provider.prompt is not None
    assert PROMPT_KNOWLEDGE_HEADER in provider.prompt
    assert result["knowledge"][0]["text"][:12] in provider.prompt


def test_offline_explanation_cites_retrieved_knowledge():
    output = _ziwei_output()
    result = get_explainer_for("ziwei", provider=None).explain(output, k=3)
    assert result["knowledge"]
    assert result["degraded"] is True
    assert "[knowledge:" in str(result["explanation"])


def test_query_is_derived_from_the_deterministic_result():
    output = _ziwei_output()
    expl = Explainer(retriever=get_explainer_for("ziwei").retriever)
    query = expl.build_query(output)
    assert "ziwei" in query
    assert output.result.wuxing_ju in query


# == No knowledge ==


def test_explain_without_retriever_still_works():
    output = _bazi_output()
    provider = _CapturingProvider()
    result = Explainer(provider=provider, retriever=None).explain(output)

    assert result["knowledge"] == []
    assert result["explanation"] == "解释文本"
    assert "Authoritative context" not in (provider.prompt or "")


def test_explain_with_empty_corpus_still_works():
    from openmetaphysics.rag.retriever import InMemoryRetriever

    output = _ziwei_output()
    result = Explainer(provider=None, retriever=InMemoryRetriever()).explain(output)
    assert result["knowledge"] == []
    assert result["explanation"]


# == Provider failure ==


def test_provider_failure_does_not_break_pipeline_or_calculation():
    output = _bazi_output()
    before = output.model_dump(mode="json")

    result = Explainer(provider=_FailingProvider(), retriever=None).explain(output, style="concise")

    assert result["degraded"] is True
    assert result["explanation"], "fallback prose expected"
    assert output.model_dump(mode="json") == before, "calculation result must be untouched"


def test_failing_domain_explainer_degrades_without_raising():
    output = _ziwei_output()
    result = get_explainer_for("ziwei", provider=_FailingProvider()).explain(output)
    assert result["explanation"]
    assert result["degraded"] is True


# == Fact preservation ==


def test_explain_does_not_modify_evidence():
    output = _ziwei_output()
    before = output.model_dump(mode="json")
    before_result = output.result.model_dump(mode="json")

    expl = get_explainer_for("ziwei", provider=_CapturingProvider())
    explained = expl.explain(output, k=3)

    assert output.model_dump(mode="json") == before
    assert output.result.model_dump(mode="json") == before_result
    assert explained["evidence"]["result"] == before_result
    # the facts a reader sees are the engine's facts
    assert explained["evidence"]["result"]["wuxing_ju"] == output.result.wuxing_ju


# == Wiring ==


def test_domain_explainers_are_wired():
    assert isinstance(get_explainer_for("bazi"), BaziExplainer)
    assert isinstance(get_explainer_for("ziwei"), ZiweiExplainer)
    # P2.2: Qimen joined the same chain. It only overrides the *query*
    # construction (遁/局/节气/值符 never entered the generic query), so the
    # prompt contract and the offline fallback stay the generic ones.
    qimen = get_explainer_for("qimen")
    assert isinstance(qimen, QimenExplainer)
    assert type(qimen)._llm_render is Explainer._llm_render
    assert type(qimen)._fallback is Explainer._fallback
    # P2.3: Liuyao joined the same chain, also query-construction only.
    liuyao = get_explainer_for("liuyao")
    assert isinstance(liuyao, LiuyaoExplainer)
    assert type(liuyao)._llm_render is Explainer._llm_render
    assert type(liuyao)._fallback is Explainer._fallback
    assert type(get_explainer_for(None)) is Explainer


def test_ziwei_explainer_no_longer_degrades_to_generic_json_dump():
    output = _ziwei_output()
    text = get_explainer_for("ziwei", provider=None).render(output)
    assert "此紫微命盘为" in text
    assert output.result.wuxing_ju in text
    assert "deterministic result (engine" not in text


def test_bazi_explainer_fallback_contract_preserved():
    output = _bazi_output()
    text = BaziExplainer(provider=None).render(output)
    assert "日主" in text and "月令" in text and "格局" in text
    assert output.result.day_master in text


def test_orchestration_explain_uses_the_chain():
    from openmetaphysics.core.schemas import AgentInput
    from openmetaphysics.orchestration.graph import OrchestrationRequest, orchestrate

    resp = orchestrate(
        OrchestrationRequest(
            request_id="o1",
            payload=AgentInput(
                request_id="o1",
                born_at=BORN,
                gender=Gender.MALE,
                question="事业",
            ),
            agents=["ziwei"],
            explain=True,
        )
    )
    assert resp.explanation["ziwei"]
    assert isinstance(resp.explanation["ziwei"], str)
