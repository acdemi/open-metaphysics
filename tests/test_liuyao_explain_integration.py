"""P2.3 — Liuyao Explain integration and HTTP E2E.

    Liuyao deterministic calculation -> deterministic result
        -> Liuyao knowledge retrieval -> explanation context
        -> POST /agents/liuyao/explain -> HTTP response

Real engine, real corpus, real retriever; the only stand-in is the LLM provider
(a deterministic stub), as no commercial API may be used here. FACTS stay
authoritative: knowledge is context only and never changes the deterministic
result, and a provider failure never becomes an HTTP error.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput
from openmetaphysics.agents.liuyao_explainer import LiuyaoExplainer
from openmetaphysics.api.app import app
from openmetaphysics.core.models import HEXAGRAMS
from openmetaphysics.core.schemas import AgentOutput
from openmetaphysics.inference.explainer import (
    PROMPT_FACTS_HEADER,
    PROMPT_KNOWLEDGE_HEADER,
    PROMPT_QUESTION_HEADER,
    PROMPT_RULES,
    Explainer,
    get_explainer_for,
)
from openmetaphysics.rag.retriever import reset_retriever

ROOT = Path(__file__).resolve().parents[1]
LIUYAO_CORPUS = ROOT / "knowledge" / "liuyao_corpus.json"

BORN = datetime(1990, 5, 17, 2, 30, tzinfo=timezone.utc)
BORN_ISO = "1990-05-17T10:30:00+08:00"
QUESTION = "事业与财运"
CASTS = [7, 8, 7, 8, 7, 8]
BODY: dict[str, Any] = {
    "request_id": "p23",
    "born_at": BORN_ISO,
    "gender": "male",
    "casts": CASTS,
    "question": QUESTION,
}

client = TestClient(app, raise_server_exceptions=False)


def _liuyao_ids() -> set[str]:
    return {n["id"] for n in json.loads(LIUYAO_CORPUS.read_text(encoding="utf-8"))["nodes"]}


LIUYAO_IDS = _liuyao_ids()


@pytest.fixture(autouse=True)
def _fresh_retriever():
    reset_retriever()
    yield
    reset_retriever()


class _CapturingProvider:
    """Deterministic stub provider; records the prompt it was handed."""

    name = "capturing-stub"

    def __init__(self, reply: str = "六爻解释文本") -> None:
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
        raise TimeoutError("read timed out")

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        raise TimeoutError("read timed out")


def _output() -> AgentOutput:
    return LiuyaoAgent().compute(
        LiuyaoInput(
            request_id="q1",
            born_at=BORN,
            casts=CASTS,
            question=QUESTION,
        )
    )


# == 1. Liuyao result + Liuyao knowledge -> explanation ==


def test_explain_uses_retrieved_liuyao_knowledge() -> None:
    output = _output()
    explainer = get_explainer_for("liuyao", provider=None)

    result = explainer.explain(output, k=3)
    assert result["agent"] == "liuyao"
    assert result["degraded"] is True and result["provider"] is None
    assert result["error"] is None, "offline is not a provider failure"
    assert result["explanation"]

    knowledge = result["knowledge"]
    assert knowledge, "the corpus must supply explanation context"
    assert all(k["id"] in LIUYAO_IDS for k in knowledge), [k["id"] for k in knowledge]
    assert all(k["source"] for k in knowledge), "citations must be preserved"
    assert "[knowledge:" in result["explanation"], "offline prose cites the retrieved knowledge"

    # FACTS stay authoritative: the evidence is exactly the engine's fact layer
    assert result["evidence"]["result"] == output.result.model_dump(mode="json")
    assert result["evidence"]["input_hash"] == output.input_hash
    assert result["evidence"]["metadata"]["question"] == QUESTION


def test_query_is_derived_from_the_liuyao_result() -> None:
    output = _output()
    query = get_explainer_for("liuyao", provider=None, retriever=None).build_query(output)

    assert query.split()[0] == "liuyao"
    # 卦名/宫/用神/六神 never entered the generic query (measured) -> must be here
    original = HEXAGRAMS[output.result.original_hexagram - 1]["name"]
    assert original in query, "本卦卦名 must enter the query"
    assert f"{output.result.palace}宫" in query, "宫位 must enter the query"
    assert output.result.palace_element in query
    assert output.result.yong_shen in query, "用神 must enter the query"
    # 用神爻与世爻是断卦焦点: 其六亲/六神必须进入查询
    focus = [output.result.shi_position - 1]
    if output.result.yong_shen in output.result.liu_qin:
        focus.insert(0, output.result.liu_qin.index(output.result.yong_shen))
    for index in focus:
        assert output.result.liu_qin[index] in query, "focus-line 六亲 must enter the query"
        assert output.result.liu_shen[index] in query, "focus-line 六神 must enter the query"
    assert QUESTION in query, "the user question is preserved"


def test_query_omits_structure_terms_that_generic_query_already_had() -> None:
    """The generic query is preserved as a fallback; the domain one is a superset."""
    output = _output()
    generic = Explainer.build_query(output)
    domain = LiuyaoExplainer.build_query(output)

    for token in ("liuyao", QUESTION):
        assert token in generic
        assert token in domain

    # the six 六亲 values used to fill the 6-slot limit, starving everything else
    assert len(generic.split()) <= 12
    assert len(domain.split()) > len(generic.split())


def test_the_query_carries_the_hexagram_not_just_the_palace() -> None:
    """Regression: 卦名 was never in the generic query, so a 既济 chart was
    explained with 坎宫 prose only. Measured, then fixed by the domain explainer."""
    retriever = get_explainer_for("liuyao", provider=None).retriever
    assert retriever is not None

    output = _output()
    query = get_explainer_for("liuyao", provider=None, retriever=retriever).build_query(output)
    ids = [c.id for c in retriever.retrieve(query, k=10)]  # type: ignore[union-attr]

    assert output.result.palace_element in query
    assert "kn:palace:liuyao_kan" in ids, ids
    assert any(i.startswith("kn:ten_god:liuyao_") for i in ids), ids


def test_retrieved_liuyao_knowledge_enters_the_provider_prompt() -> None:
    output = _output()
    provider = _CapturingProvider()
    result = get_explainer_for("liuyao", provider=provider).explain(output, k=3)

    assert provider.prompt is not None
    assert PROMPT_FACTS_HEADER in provider.prompt
    assert PROMPT_KNOWLEDGE_HEADER in provider.prompt, "no knowledge context was injected"
    assert PROMPT_QUESTION_HEADER in provider.prompt
    assert PROMPT_RULES in provider.prompt, "the FACTS > KNOWLEDGE contract is stated"
    assert output.result.palace in provider.prompt, "the FACTS carry the engine result"
    assert QUESTION in provider.prompt, "the user question reaches the prompt"
    assert result["knowledge"][0]["text"][:12] in provider.prompt
    assert result["knowledge"][0]["source"] in provider.prompt
    assert result["explanation"] == "六爻解释文本"


# == 2. Facts are never modified by knowledge or explanation ==


def test_explain_does_not_modify_the_deterministic_result() -> None:
    output = _output()
    before = output.model_dump(mode="json")
    before_result = output.result.model_dump(mode="json")

    result = get_explainer_for("liuyao", provider=_CapturingProvider()).explain(output, k=3)

    assert output.model_dump(mode="json") == before
    assert output.result.model_dump(mode="json") == before_result
    assert result["evidence"]["result"] == before_result


def test_same_input_yields_the_same_result_facts_and_knowledge() -> None:
    first, second = _output(), _output()
    assert first.result.model_dump(mode="json") == second.result.model_dump(mode="json")
    assert first.input_hash == second.input_hash

    explainer = get_explainer_for("liuyao")
    one = explainer.explain(first, k=3)
    two = explainer.explain(second, k=3)
    assert one["evidence"]["result"] == two["evidence"]["result"]
    assert one["evidence"]["input_hash"] == two["evidence"]["input_hash"]
    assert [k["id"] for k in one["knowledge"]] == [k["id"] for k in two["knowledge"]]


def test_knowledge_availability_does_not_change_the_calculation(monkeypatch) -> None:
    """The Knowledge layer is read-only: it can never feed back into the engine."""
    with_knowledge = _output()

    monkeypatch.setattr(
        "openmetaphysics.rag.corpus.DEFAULT_CORPUS_PATH", Path("/nonexistent/corpus.json")
    )
    reset_retriever()

    without_knowledge = _output()

    assert without_knowledge.result.model_dump(mode="json") == with_knowledge.result.model_dump(
        mode="json"
    )
    assert without_knowledge.input_hash == with_knowledge.input_hash
    assert without_knowledge.confidence.model_dump(
        mode="json"
    ) == with_knowledge.confidence.model_dump(mode="json")
    assert [s.model_dump(mode="json") for s in without_knowledge.reasoning_trace] == [
        s.model_dump(mode="json") for s in with_knowledge.reasoning_trace
    ]


def test_explainer_never_recomputes_the_chart() -> None:
    """The explainer only reads what the engine already put into the output."""
    output = _output()
    recomputed = _output()
    assert output.result.model_dump(mode="json") == recomputed.result.model_dump(mode="json")
    assert output.input_hash == recomputed.input_hash

    before = output.result.model_dump(mode="json")
    Explainer(retriever=None).build_query(output)
    get_explainer_for("liuyao", provider=None, retriever=None).build_query(output)
    assert output.result.model_dump(mode="json") == before


# == 3. HTTP: POST /agents/liuyao/explain ==


def test_http_liuyao_explain_e2e() -> None:
    computed = client.post("/agents/liuyao/compute", json=BODY)
    assert computed.status_code == 200, computed.text
    output = computed.json()

    explained = client.post("/agents/liuyao/explain?k=3", json={"output": output})
    assert explained.status_code == 200, explained.text
    data = explained.json()

    assert data["agent"] == "liuyao"
    assert data["explanation"], "an explanation is required"
    assert data["degraded"] is True and data["provider"] is None
    assert data["error"] is None

    knowledge = data["knowledge"]
    assert knowledge, "Liuyao knowledge retrieval must run over HTTP"
    assert all(k["id"] in LIUYAO_IDS for k in knowledge), [k["id"] for k in knowledge]
    assert all(k["id"].startswith("kn:") and k["source"] for k in knowledge)

    # deterministic calculation completed and is preserved verbatim
    assert output["result"] and output["reasoning_trace"] and output["input_hash"]
    assert data["evidence"]["result"] == output["result"]
    assert data["evidence"]["input_hash"] == output["input_hash"]
    assert data["evidence"]["confidence"]["value"] == output["confidence"]["value"]
    assert data["evidence"]["metadata"]["question"] == QUESTION


def test_http_liuyao_compute_and_explain_return_the_same_calculation() -> None:
    plain = client.post("/agents/liuyao/compute", json=BODY).json()
    explained = client.post("/agents/liuyao/compute?explain=true&k=3", json=BODY).json()

    assert explained["result"] == plain["result"]
    assert explained["input_hash"] == plain["input_hash"]
    assert explained["confidence"] == plain["confidence"]
    assert explained["explain"]["evidence"]["result"] == plain["result"]
    assert explained["explain"]["knowledge"]
    assert all(k["id"] in LIUYAO_IDS for k in explained["explain"]["knowledge"])


def test_http_liuyao_explain_is_reproducible() -> None:
    output = client.post("/agents/liuyao/compute", json=BODY).json()
    first = client.post("/agents/liuyao/explain", json={"output": output}).json()
    second = client.post("/agents/liuyao/explain", json={"output": output}).json()

    assert first["evidence"] == second["evidence"]
    assert first["explanation"] == second["explanation"]
    assert [k["id"] for k in first["knowledge"]] == [k["id"] for k in second["knowledge"]]


def test_http_liuyao_explain_respects_k() -> None:
    output = client.post("/agents/liuyao/compute", json=BODY).json()
    assert (
        len(client.post("/agents/liuyao/explain?k=1", json={"output": output}).json()["knowledge"])
        == 1
    )
    assert (
        len(client.post("/agents/liuyao/explain?k=3", json={"output": output}).json()["knowledge"])
        == 3
    )
    assert (
        client.post("/agents/liuyao/explain?k=0", json={"output": output}).json()["knowledge"] == []
    )


# == 4. Provider failure keeps HTTP 200 and the deterministic result ==


def test_http_provider_failure_does_not_become_a_calculation_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "openmetaphysics.inference.explainer.get_provider", lambda *a, **k: _FailingProvider()
    )
    response = client.post("/agents/liuyao/compute?explain=true", json=BODY)
    assert response.status_code == 200, "a provider failure must never be an HTTP error"
    data = response.json()

    assert data["result"] and data["input_hash"], "deterministic result must stay intact"
    assert "error" not in data or data["error"] is None

    explain = data["explain"]
    assert explain["degraded"] is True
    assert explain["explanation"], "offline fallback prose expected"
    assert explain["error"]["kind"] == "timeout", "the provider failure is classified"
    assert explain["error"]["provider"] == "failing-stub"
    assert explain["knowledge"], "knowledge retrieval is independent of the provider"


def test_http_liuyao_explain_endpoint_provider_failure_is_recorded(monkeypatch) -> None:
    monkeypatch.setattr(
        "openmetaphysics.inference.explainer.get_provider", lambda *a, **k: _FailingProvider()
    )
    output = client.post("/agents/liuyao/compute", json=BODY).json()
    response = client.post("/agents/liuyao/explain", json={"output": output})

    assert response.status_code == 200
    data = response.json()
    assert data["evidence"]["result"] == output["result"]
    assert data["error"]["kind"] == "timeout"
    assert data["knowledge"], "retrieval ran even though the provider failed"


# == 5. Knowledge unavailable degrades without failing ==


def test_liuyao_explain_survives_an_unavailable_corpus(monkeypatch) -> None:
    monkeypatch.setattr(
        "openmetaphysics.rag.corpus.DEFAULT_CORPUS_PATH", Path("/nonexistent/corpus.json")
    )
    reset_retriever()

    response = client.post("/agents/liuyao/compute?explain=true", json=BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["result"], "calculation must survive an unavailable corpus"
    assert data["explain"]["knowledge"] == []
    assert data["explain"]["explanation"]
    assert data["explain"]["error"] is None


def test_liuyao_explain_http_endpoint_survives_an_unavailable_corpus(monkeypatch) -> None:
    output = client.post("/agents/liuyao/compute", json=BODY).json()

    monkeypatch.setattr(
        "openmetaphysics.rag.corpus.DEFAULT_CORPUS_PATH", Path("/nonexistent/corpus.json")
    )
    reset_retriever()

    response = client.post("/agents/liuyao/explain", json={"output": output})
    assert response.status_code == 200
    data = response.json()
    assert data["knowledge"] == []
    assert data["explanation"], "explanation still completes without knowledge"
    assert data["evidence"]["result"] == output["result"]
