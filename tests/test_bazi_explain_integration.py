"""P2.1 — BaZi Explain integration and HTTP E2E.

    BaZi calculation -> deterministic result -> BaZi knowledge retrieval
        -> explanation context -> POST /agents/bazi/explain -> HTTP response

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

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.api.app import app
from openmetaphysics.core.schemas import AgentOutput, Gender
from openmetaphysics.inference.explainer import (
    PROMPT_FACTS_HEADER,
    PROMPT_KNOWLEDGE_HEADER,
    Explainer,
    get_explainer_for,
)
from openmetaphysics.rag.retriever import reset_retriever

ROOT = Path(__file__).resolve().parents[1]
BAZI_CORPUS = ROOT / "knowledge" / "bazi_corpus.json"

BORN = datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc)
BORN_ISO = "1985-08-15T10:00:00+08:00"
QUESTION = "事业与财运"
BODY: dict[str, Any] = {
    "request_id": "p21",
    "born_at": BORN_ISO,
    "gender": "male",
    "question": QUESTION,
}

client = TestClient(app, raise_server_exceptions=False)


def _bazi_ids() -> set[str]:
    return {n["id"] for n in json.loads(BAZI_CORPUS.read_text(encoding="utf-8"))["nodes"]}


BAZI_IDS = _bazi_ids()

# The deterministic char-overlap scorer favours broad 干支 coverage (the
# documented Phase C ranking limitation), so on the auto-derived BaZi query the
# frozen corpus's 神煞 nodes lead and the BaZi corpus enters the returned
# knowledge at rank 9. ``K_WITH_BAZI`` is the measured k at which BaZi
# knowledge participates; the behaviour is locked by
# ``test_default_k_context_and_bazi_entry_rank``.
K_WITH_BAZI = 10


@pytest.fixture(autouse=True)
def _fresh_retriever():
    reset_retriever()
    yield
    reset_retriever()


class _CapturingProvider:
    """Deterministic stub provider; records the prompt it was handed."""

    name = "capturing-stub"

    def __init__(self, reply: str = "八字解释文本") -> None:
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
    return BaziAgent().compute(
        BaziInput(request_id="b1", born_at=BORN, gender=Gender.MALE, question=QUESTION)
    )


# == 1. BaZi result + BaZi knowledge -> explanation ==


def test_explain_uses_retrieved_bazi_knowledge() -> None:
    output = _output()
    explainer = get_explainer_for("bazi", provider=None)

    result = explainer.explain(output, k=K_WITH_BAZI)
    assert result["agent"] == "bazi"
    assert result["degraded"] is True and result["provider"] is None
    assert result["error"] is None, "offline is not a provider failure"
    assert result["explanation"]

    knowledge = result["knowledge"]
    assert knowledge, "the corpus must supply explanation context"
    assert any(k["id"] in BAZI_IDS for k in knowledge), [k["id"] for k in knowledge]
    assert all(k["source"] for k in knowledge), "citations must be preserved"
    assert "[knowledge:" in result["explanation"], "offline prose cites the retrieved knowledge"

    # FACTS stay authoritative: the evidence is exactly the engine's fact layer
    assert result["evidence"]["result"] == output.result.model_dump(mode="json")
    assert result["evidence"]["input_hash"] == output.input_hash
    assert result["evidence"]["metadata"]["question"] == QUESTION


def test_default_k_context_and_bazi_entry_rank() -> None:
    """Locks the measured retrieval behaviour of the auto-derived BaZi query.

    The frozen corpus's broad 神煞 nodes still lead at the API default k=3 (the
    documented Phase C char-overlap breadth bias); the P2.1 BaZi corpus enters
    the returned knowledge at k >= 9. Both facts are asserted so the ranking
    cannot drift silently, and so the integration claim stays measured rather
    than assumed.
    """
    output = _output()
    explainer = get_explainer_for("bazi")

    shallow = explainer.retrieve(output, k=3)
    assert shallow, "real explanation context must always be retrieved"
    assert all(c.id.startswith("kn:") for c in shallow)
    assert all(c.source for c in shallow)

    deep_ids = [c.id for c in explainer.retrieve(output, k=25)]
    assert deep_ids, "retrieval must execute"
    first_bazi = next((i for i, cid in enumerate(deep_ids, 1) if cid in BAZI_IDS), None)
    assert first_bazi is not None, "the BaZi corpus must be reachable for a BaZi query"
    assert first_bazi <= K_WITH_BAZI, f"BaZi corpus entered later than expected: rank {first_bazi}"


def test_query_is_derived_from_the_bazi_result() -> None:
    output = _output()
    query = Explainer(retriever=get_explainer_for("bazi").retriever).build_query(output)
    assert query.split()[0] == "bazi"
    assert output.result.day_master in query
    assert output.result.day_master_element in query


def test_retrieved_bazi_knowledge_enters_the_provider_prompt() -> None:
    output = _output()
    provider = _CapturingProvider()
    result = get_explainer_for("bazi", provider=provider).explain(output, k=K_WITH_BAZI)

    assert provider.prompt is not None
    assert PROMPT_FACTS_HEADER in provider.prompt
    assert PROMPT_KNOWLEDGE_HEADER in provider.prompt, "no knowledge context was injected"
    assert output.result.day_master in provider.prompt, "the FACTS carry the engine result"
    assert QUESTION in provider.prompt, "the user question reaches the prompt"
    assert result["knowledge"][0]["text"][:12] in provider.prompt
    assert result["knowledge"][0]["source"] in provider.prompt
    # the P2.1 BaZi knowledge itself is injected as authoritative context
    bazi_chunk = next(k for k in result["knowledge"] if k["id"] in BAZI_IDS)
    assert bazi_chunk["text"][:12] in provider.prompt
    assert bazi_chunk["source"] in provider.prompt
    assert result["explanation"] == "八字解释文本"


# == 2. Facts are never modified by knowledge or explanation ==


def test_explain_does_not_modify_the_deterministic_result() -> None:
    output = _output()
    before = output.model_dump(mode="json")
    before_result = output.result.model_dump(mode="json")

    result = get_explainer_for("bazi", provider=_CapturingProvider()).explain(output, k=3)

    assert output.model_dump(mode="json") == before
    assert output.result.model_dump(mode="json") == before_result
    assert result["evidence"]["result"] == before_result


def test_same_input_yields_same_result_facts_and_knowledge() -> None:
    first, second = _output(), _output()
    assert first.result.model_dump(mode="json") == second.result.model_dump(mode="json")
    assert first.input_hash == second.input_hash

    explainer = get_explainer_for("bazi")
    one = explainer.explain(first, k=3)
    two = explainer.explain(second, k=3)
    assert one["evidence"]["result"] == two["evidence"]["result"]
    assert one["evidence"]["input_hash"] == two["evidence"]["input_hash"]
    assert [k["id"] for k in one["knowledge"]] == [k["id"] for k in two["knowledge"]]


# == 3. HTTP: POST /agents/bazi/explain ==


def test_http_bazi_explain_e2e() -> None:
    computed = client.post("/agents/bazi/compute", json=BODY)
    assert computed.status_code == 200, computed.text
    output = computed.json()

    explained = client.post(f"/agents/bazi/explain?k={K_WITH_BAZI}", json={"output": output})
    assert explained.status_code == 200, explained.text
    data = explained.json()

    assert data["agent"] == "bazi"
    assert data["explanation"], "an explanation is required"
    assert data["degraded"] is True and data["provider"] is None
    assert data["error"] is None

    knowledge = data["knowledge"]
    assert knowledge, "BaZi knowledge retrieval must run over HTTP"
    assert any(k["id"] in BAZI_IDS for k in knowledge), [k["id"] for k in knowledge]
    assert all(k["id"].startswith("kn:") and k["source"] for k in knowledge)

    # deterministic calculation completed and is preserved verbatim
    assert output["result"] and output["reasoning_trace"] and output["input_hash"]
    assert data["evidence"]["result"] == output["result"]
    assert data["evidence"]["input_hash"] == output["input_hash"]
    assert data["evidence"]["confidence"]["value"] == output["confidence"]["value"]


def test_http_bazi_explain_default_k_still_returns_context() -> None:
    """The published default (k=3) keeps working over HTTP, BaZi or not."""
    output = client.post("/agents/bazi/compute", json=BODY).json()
    data = client.post("/agents/bazi/explain", json={"output": output}).json()
    assert data["knowledge"], "the default request must still return explanation context"
    assert data["explanation"] and data["evidence"]["result"] == output["result"]


def test_http_bazi_compute_explain_switch_preserves_the_result() -> None:
    plain = client.post("/agents/bazi/compute", json=BODY).json()
    explained = client.post(f"/agents/bazi/compute?explain=true&k={K_WITH_BAZI}", json=BODY).json()

    assert explained["result"] == plain["result"]
    assert explained["input_hash"] == plain["input_hash"]
    assert explained["confidence"] == plain["confidence"]
    assert explained["explain"]["evidence"]["result"] == plain["result"]
    assert explained["explain"]["knowledge"]
    assert any(k["id"] in BAZI_IDS for k in explained["explain"]["knowledge"])


def test_http_bazi_explain_is_reproducible() -> None:
    output = client.post("/agents/bazi/compute", json=BODY).json()
    first = client.post("/agents/bazi/explain", json={"output": output}).json()
    second = client.post("/agents/bazi/explain", json={"output": output}).json()

    assert first["evidence"] == second["evidence"]
    assert first["explanation"] == second["explanation"]
    assert [k["id"] for k in first["knowledge"]] == [k["id"] for k in second["knowledge"]]


def test_http_bazi_explain_respects_k() -> None:
    output = client.post("/agents/bazi/compute", json=BODY).json()
    assert (
        len(client.post("/agents/bazi/explain?k=1", json={"output": output}).json()["knowledge"])
        == 1
    )
    assert (
        client.post("/agents/bazi/explain?k=0", json={"output": output}).json()["knowledge"] == []
    )


# == 4. Provider failure keeps HTTP 200 and the deterministic result ==


def test_http_provider_failure_does_not_become_a_calculation_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "openmetaphysics.inference.explainer.get_provider", lambda *a, **k: _FailingProvider()
    )
    response = client.post("/agents/bazi/compute?explain=true", json=BODY)
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


# == 5. Knowledge unavailable degrades without failing ==


def test_bazi_explain_survives_an_unavailable_corpus(monkeypatch) -> None:
    monkeypatch.setattr(
        "openmetaphysics.rag.corpus.DEFAULT_CORPUS_PATH", Path("/nonexistent/corpus.json")
    )
    reset_retriever()

    response = client.post("/agents/bazi/compute?explain=true", json=BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["result"], "calculation must survive an unavailable corpus"
    assert data["explain"]["knowledge"] == []
    assert data["explain"]["explanation"]
    assert data["explain"]["error"] is None
