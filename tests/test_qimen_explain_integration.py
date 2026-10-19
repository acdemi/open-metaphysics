"""P2.2 — Qimen Explain integration and HTTP E2E.

    Qimen deterministic calculation -> deterministic result
        -> Qimen knowledge retrieval -> explanation context
        -> POST /agents/qimen/explain -> HTTP response

Real engine, real corpus, real retriever; the only stand-in is the LLM
provider (a deterministic stub), as no commercial API may be used here.
FACTS stay authoritative: knowledge is context only and never changes the
deterministic result, and a provider failure never becomes an HTTP error.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from openmetaphysics.agents.qimen import QimenAgent, QimenInput
from openmetaphysics.api.app import app
from openmetaphysics.core.schemas import AgentOutput, Gender
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
QIMEN_CORPUS = ROOT / "knowledge" / "qimen_corpus.json"

BORN = datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc)
BORN_ISO = "1985-08-15T10:00:00+08:00"
QUESTION = "事业与财运"
BODY: dict[str, Any] = {
    "request_id": "p22",
    "born_at": BORN_ISO,
    "gender": "male",
    "question": QUESTION,
}

client = TestClient(app, raise_server_exceptions=False)


def _qimen_ids() -> set[str]:
    return {n["id"] for n in json.loads(QIMEN_CORPUS.read_text(encoding="utf-8"))["nodes"]}


QIMEN_IDS = _qimen_ids()


@pytest.fixture(autouse=True)
def _fresh_retriever():
    reset_retriever()
    yield
    reset_retriever()


class _CapturingProvider:
    """Deterministic stub provider; records the prompt it was handed."""

    name = "capturing-stub"

    def __init__(self, reply: str = "奇门解释文本") -> None:
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
    return QimenAgent().compute(
        QimenInput(request_id="q1", born_at=BORN, gender=Gender.MALE, question=QUESTION)
    )


# == 1. Qimen result + Qimen knowledge -> explanation ==


def test_explain_uses_retrieved_qimen_knowledge() -> None:
    output = _output()
    explainer = get_explainer_for("qimen", provider=None)

    result = explainer.explain(output, k=3)
    assert result["agent"] == "qimen"
    assert result["degraded"] is True and result["provider"] is None
    assert result["error"] is None, "offline is not a provider failure"
    assert result["explanation"]

    knowledge = result["knowledge"]
    assert knowledge, "the corpus must supply explanation context"
    assert all(k["id"] in QIMEN_IDS for k in knowledge), [k["id"] for k in knowledge]
    assert all(k["source"] for k in knowledge), "citations must be preserved"
    assert "[knowledge:" in result["explanation"], "offline prose cites the retrieved knowledge"

    # FACTS stay authoritative: the evidence is exactly the engine's fact layer
    assert result["evidence"]["result"] == output.result.model_dump(mode="json")
    assert result["evidence"]["input_hash"] == output.input_hash
    assert result["evidence"]["metadata"]["question"] == QUESTION


def test_query_is_derived_from_the_qimen_result() -> None:
    output = _output()
    query = get_explainer_for("qimen", provider=None, retriever=None).build_query(output)

    assert query.split()[0] == "qimen"
    assert output.result.solar_term in query, "节气 must enter the query"
    assert f"{output.result.ju}局" in query, "局数 must enter the query"
    # the 遁 type is the single most important semantic of a Qimen plate
    assert ("阴遁" if output.result.dun_type == "yin" else "阳遁") in query
    assert QUESTION in query, "the user question is preserved"


def test_the_query_matches_the_plate_dun_type_not_the_opposite_one() -> None:
    """Regression: the generic query never carried 遁 type, so a 阴遁 plate
    retrieved 阳遁 first. Measured, then fixed by the domain explainer."""
    retriever = get_explainer_for("qimen", provider=None).retriever
    assert retriever is not None

    for born_iso, expected in (
        ("1985-08-15T10:00:00+08:00", "yin"),  # 夏至后
        ("1985-01-15T10:00:00+08:00", "yang"),  # 冬至后
    ):
        output = QimenAgent().compute(
            QimenInput(
                request_id="q",
                born_at=datetime.fromisoformat(born_iso).astimezone(timezone.utc),
                gender=Gender.MALE,
                question=QUESTION,
            )
        )
        assert output.result.dun_type == expected

        query = get_explainer_for("qimen", provider=None, retriever=retriever).build_query(output)
        ids = [c.id for c in retriever.retrieve(query, k=10)]  # type: ignore[union-attr]
        matching = f"kn:pattern:qimen_{'yindun' if expected == 'yin' else 'yangdun'}"
        opposite = f"kn:pattern:qimen_{'yangdun' if expected == 'yin' else 'yindun'}"
        assert matching in ids, ids
        assert ids.index(matching) < (ids.index(opposite) if opposite in ids else len(ids)), ids


def test_retrieved_qimen_knowledge_enters_the_provider_prompt() -> None:
    output = _output()
    provider = _CapturingProvider()
    result = get_explainer_for("qimen", provider=provider).explain(output, k=3)

    assert provider.prompt is not None
    assert PROMPT_FACTS_HEADER in provider.prompt
    assert PROMPT_KNOWLEDGE_HEADER in provider.prompt, "no knowledge context was injected"
    assert PROMPT_QUESTION_HEADER in provider.prompt
    assert PROMPT_RULES in provider.prompt, "the FACTS > KNOWLEDGE contract is stated"
    assert output.result.solar_term in provider.prompt, "the FACTS carry the engine result"
    assert QUESTION in provider.prompt, "the user question reaches the prompt"
    assert result["knowledge"][0]["text"][:12] in provider.prompt
    assert result["knowledge"][0]["source"] in provider.prompt
    assert result["explanation"] == "奇门解释文本"


# == 2. Facts are never modified by knowledge or explanation ==


def test_explain_does_not_modify_the_deterministic_result() -> None:
    output = _output()
    before = output.model_dump(mode="json")
    before_result = output.result.model_dump(mode="json")

    result = get_explainer_for("qimen", provider=_CapturingProvider()).explain(output, k=3)

    assert output.model_dump(mode="json") == before
    assert output.result.model_dump(mode="json") == before_result
    assert result["evidence"]["result"] == before_result


def test_same_input_yields_the_same_result_facts_and_knowledge() -> None:
    first, second = _output(), _output()
    assert first.result.model_dump(mode="json") == second.result.model_dump(mode="json")
    assert first.input_hash == second.input_hash

    explainer = get_explainer_for("qimen")
    one = explainer.explain(first, k=3)
    two = explainer.explain(second, k=3)
    assert one["evidence"]["result"] == two["evidence"]["result"]
    assert one["evidence"]["input_hash"] == two["evidence"]["input_hash"]
    assert [k["id"] for k in one["knowledge"]] == [k["id"] for k in two["knowledge"]]


def test_knowledge_availability_does_not_change_the_calculation(monkeypatch) -> None:
    """The Knowledge layer is read-only: it can never feed back into the engine.

    This locks the dependency direction -- Qimen calculation -> knowledge, never
    the reverse -- by computing the same input with every corpus available and
    with none available. (The engine takes no retriever at all; the test guards
    against future wiring that would break that.)
    """
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


def test_explainer_never_recomputes_the_board() -> None:
    """The explainer only reads what the engine already put into the output.

    ``computed_at`` is a wall-clock field on the envelope, so determinism is
    asserted on the fact layer (result + input_hash), exactly as the engine
    promises it.
    """
    output = _output()
    recomputed = _output()
    assert output.result.model_dump(mode="json") == recomputed.result.model_dump(mode="json")
    assert output.input_hash == recomputed.input_hash

    # build_query must not mutate the output either
    before = output.result.model_dump(mode="json")
    Explainer(retriever=None).build_query(output)
    get_explainer_for("qimen", provider=None, retriever=None).build_query(output)
    assert output.result.model_dump(mode="json") == before


# == 3. HTTP: POST /agents/qimen/explain ==


def test_http_qimen_explain_e2e() -> None:
    computed = client.post("/agents/qimen/compute", json=BODY)
    assert computed.status_code == 200, computed.text
    output = computed.json()

    explained = client.post("/agents/qimen/explain?k=3", json={"output": output})
    assert explained.status_code == 200, explained.text
    data = explained.json()

    assert data["agent"] == "qimen"
    assert data["explanation"], "an explanation is required"
    assert data["degraded"] is True and data["provider"] is None
    assert data["error"] is None

    knowledge = data["knowledge"]
    assert knowledge, "Qimen knowledge retrieval must run over HTTP"
    assert all(k["id"] in QIMEN_IDS for k in knowledge), [k["id"] for k in knowledge]
    assert all(k["id"].startswith("kn:") and k["source"] for k in knowledge)

    # deterministic calculation completed and is preserved verbatim
    assert output["result"] and output["reasoning_trace"] and output["input_hash"]
    assert data["evidence"]["result"] == output["result"]
    assert data["evidence"]["input_hash"] == output["input_hash"]
    assert data["evidence"]["confidence"]["value"] == output["confidence"]["value"]
    assert data["evidence"]["metadata"]["question"] == QUESTION


def test_http_qimen_compute_and_explain_return_the_same_calculation() -> None:
    plain = client.post("/agents/qimen/compute", json=BODY).json()
    explained = client.post("/agents/qimen/compute?explain=true&k=3", json=BODY).json()

    assert explained["result"] == plain["result"]
    assert explained["input_hash"] == plain["input_hash"]
    assert explained["confidence"] == plain["confidence"]
    assert explained["explain"]["evidence"]["result"] == plain["result"]
    assert explained["explain"]["knowledge"]
    assert all(k["id"] in QIMEN_IDS for k in explained["explain"]["knowledge"])


def test_http_qimen_explain_is_reproducible() -> None:
    output = client.post("/agents/qimen/compute", json=BODY).json()
    first = client.post("/agents/qimen/explain", json={"output": output}).json()
    second = client.post("/agents/qimen/explain", json={"output": output}).json()

    assert first["evidence"] == second["evidence"]
    assert first["explanation"] == second["explanation"]
    assert [k["id"] for k in first["knowledge"]] == [k["id"] for k in second["knowledge"]]


def test_http_qimen_explain_respects_k() -> None:
    output = client.post("/agents/qimen/compute", json=BODY).json()
    assert (
        len(client.post("/agents/qimen/explain?k=1", json={"output": output}).json()["knowledge"])
        == 1
    )
    assert (
        len(client.post("/agents/qimen/explain?k=3", json={"output": output}).json()["knowledge"])
        == 3
    )
    assert (
        client.post("/agents/qimen/explain?k=0", json={"output": output}).json()["knowledge"] == []
    )


# == 4. Provider failure keeps HTTP 200 and the deterministic result ==


def test_http_provider_failure_does_not_become_a_calculation_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "openmetaphysics.inference.explainer.get_provider", lambda *a, **k: _FailingProvider()
    )
    response = client.post("/agents/qimen/compute?explain=true", json=BODY)
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


def test_http_qimen_explain_endpoint_provider_failure_is_recorded(monkeypatch) -> None:
    monkeypatch.setattr(
        "openmetaphysics.inference.explainer.get_provider", lambda *a, **k: _FailingProvider()
    )
    output = client.post("/agents/qimen/compute", json=BODY).json()
    response = client.post("/agents/qimen/explain", json={"output": output})

    assert response.status_code == 200
    data = response.json()
    assert data["evidence"]["result"] == output["result"]
    assert data["error"]["kind"] == "timeout"
    assert data["knowledge"], "retrieval ran even though the provider failed"


# == 5. Knowledge unavailable degrades without failing ==


def test_qimen_explain_survives_an_unavailable_corpus(monkeypatch) -> None:
    monkeypatch.setattr(
        "openmetaphysics.rag.corpus.DEFAULT_CORPUS_PATH", Path("/nonexistent/corpus.json")
    )
    reset_retriever()

    response = client.post("/agents/qimen/compute?explain=true", json=BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["result"], "calculation must survive an unavailable corpus"
    assert data["explain"]["knowledge"] == []
    assert data["explain"]["explanation"]
    assert data["explain"]["error"] is None


def test_qimen_explain_http_endpoint_survives_an_unavailable_corpus(monkeypatch) -> None:
    output = client.post("/agents/qimen/compute", json=BODY).json()

    monkeypatch.setattr(
        "openmetaphysics.rag.corpus.DEFAULT_CORPUS_PATH", Path("/nonexistent/corpus.json")
    )
    reset_retriever()

    response = client.post("/agents/qimen/explain", json={"output": output})
    assert response.status_code == 200
    data = response.json()
    assert data["knowledge"] == []
    assert data["explanation"], "explanation still completes without knowledge"
    assert data["evidence"]["result"] == output["result"]
