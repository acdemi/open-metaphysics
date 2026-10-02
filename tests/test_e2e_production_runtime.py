"""Phase A5 — Production Runtime end-to-end closure.

Drives the real stack over HTTP through ``TestClient``:

    Client -> API -> input validation -> orchestration -> BaZi agent ->
    deterministic calculation -> evidence -> knowledge retrieval -> consensus
    -> explain -> response

Nothing in the middle is mocked: the deterministic engines, the RAG retriever
over the frozen corpus and the consensus agent all execute for real. Only the
LLM provider is substituted (the phase rules allow a deterministic/stub
provider), and the "knowledge unavailable" case is produced by pointing at a
missing corpus, i.e. the real degradation path.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from openmetaphysics.api.app import app
from openmetaphysics.rag.retriever import reset_retriever

client = TestClient(app, raise_server_exceptions=False)

PAYLOAD: dict[str, Any] = {
    "request_id": "e2e-a5",
    "born_at": "1985-08-15T10:00:00+08:00",
    "gender": "male",
    "born_location": {
        "latitude": 39.9,
        "longitude": 116.4,
        "timezone": "Asia/Shanghai",
    },
    "question": "事业与财运",
}
REQUEST: dict[str, Any] = {
    "request_id": "e2e-a5",
    "payload": PAYLOAD,
    "agents": ["bazi", "ziwei", "liuyao"],
    "strategy": "weighted",
    "explain": True,
}


@pytest.fixture(autouse=True)
def _fresh_retriever():
    reset_retriever()
    yield
    reset_retriever()


def _orchestrate(**overrides: Any) -> dict[str, Any]:
    request = {**REQUEST, **overrides}
    response = client.post("/orchestrate", json=request)
    assert response.status_code == 200, response.text
    return response.json()


# == The full chain ==


def test_e2e_full_chain_over_http():
    data = _orchestrate()

    # 1. input parsed
    assert data["errors"] == []
    assert [o["agent"] for o in data["outputs"]] == ["bazi", "ziwei", "liuyao"]
    bazi_out = data["outputs"][0]
    assert bazi_out["request_id"] == "e2e-a5"
    assert bazi_out["input_hash"]

    # 2. deterministic calculation succeeded
    assert len(bazi_out["result"]["pillars"]) == 4
    assert bazi_out["result"]["day_master"]
    assert bazi_out["reasoning_trace"], "deterministic engines must emit a trace"

    # 3. evidence exists and IS the deterministic fact layer
    detail = data["explanation_detail"]["bazi"]
    evidence = detail["evidence"]
    assert evidence, "explanation must carry its evidence"
    assert evidence["result"] == bazi_out["result"]
    assert evidence["input_hash"] == bazi_out["input_hash"]
    assert evidence["confidence"]["value"] == bazi_out["confidence"]["value"]
    assert evidence["reasoning_trace"], "evidence must include the rule trace"

    # 4. knowledge retrieval executed against the real corpus
    knowledge = detail["knowledge"]
    assert knowledge, "knowledge retrieval returned nothing"
    assert all(k["id"].startswith("kn:") for k in knowledge)
    assert all(k["source"] for k in knowledge), "citations must be preserved"

    # 5. consensus succeeded (real ConsensusAgent over the real outputs)
    consensus = data["consensus"]
    assert consensus is not None
    report = consensus["result"]
    assert 0.0 <= report["overall_confidence"] <= 1.0
    assert len(report["contributions"]) == 3
    assert {c["agent"] for c in report["contributions"]} == {"bazi", "ziwei", "liuyao"}
    assert report["synthesis"]

    # 6. explain succeeded for every agent
    assert set(data["explanation"]) == {"bazi", "ziwei", "liuyao"}
    assert all(data["explanation"][a] for a in data["explanation"])
    assert detail["provider"] is None
    assert detail["degraded"] is True  # no LLM configured -> offline prose


def test_e2e_single_agent_compute_with_explain_carries_evidence():
    response = client.post("/agents/bazi/compute?explain=true", json=PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    explain = data["explain"]
    assert explain["evidence"]["result"] == data["result"]
    assert explain["knowledge"], "knowledge retrieval must run on the compute path"
    assert explain["text"]


# == Fact layer integrity ==


def test_e2e_explanation_does_not_rewrite_the_facts():
    without = _orchestrate(explain=False)
    with_explain = _orchestrate(explain=True)

    assert without["explanation"] == {}
    assert with_explain["explanation"]

    def facts(resp: dict[str, Any]) -> list[tuple[Any, Any, Any]]:
        return [(o["agent"], o["input_hash"], o["result"]) for o in resp["outputs"]]

    assert facts(without) == facts(with_explain), "explain must not change results"
    assert without["consensus"]["result"] == with_explain["consensus"]["result"]

    # the evidence the explanation saw is exactly the deterministic result
    for output in with_explain["outputs"]:
        detail = with_explain["explanation_detail"][output["agent"]]
        assert detail["evidence"]["result"] == output["result"]
        assert detail["evidence"]["input_hash"] == output["input_hash"]


def test_e2e_deterministic_across_calls():
    first = _orchestrate()
    second = _orchestrate()

    assert [o["result"] for o in first["outputs"]] == [o["result"] for o in second["outputs"]]
    assert [o["input_hash"] for o in first["outputs"]] == [
        o["input_hash"] for o in second["outputs"]
    ]
    assert first["consensus"]["result"] == second["consensus"]["result"]
    assert first["explanation"] == second["explanation"]


# == Error paths ==


def test_e2e_invalid_input_returns_structured_api_error():
    response = client.post("/orchestrate", json={**REQUEST, "payload": {"request_id": "bad"}})
    assert response.status_code == 422
    assert "detail" in response.json()

    per_agent = client.post(
        "/agents/bazi/compute",
        json={"request_id": "a", "born_at": "2024-01-01T00:00:00"},  # naive datetime
    )
    assert per_agent.status_code == 422
    assert "detail" in per_agent.json()


def test_e2e_knowledge_unavailable_degrades_gracefully(monkeypatch):
    """Point the loader at a missing corpus: the real degradation path."""
    monkeypatch.setattr(
        "openmetaphysics.rag.corpus.DEFAULT_CORPUS_PATH",
        Path("/nonexistent/ziwei_corpus.json"),
    )
    reset_retriever()

    data = _orchestrate()
    assert data["errors"] == []
    assert data["outputs"][0]["result"]["day_master"], "calculation must still succeed"
    detail = data["explanation_detail"]["bazi"]
    assert detail["knowledge"] == [], "no knowledge available"
    assert detail["explanation"], "explanation must still be produced"
    assert data["consensus"] is not None


def test_e2e_provider_failure_keeps_deterministic_result(monkeypatch):
    class _FailingProvider:
        name = "failing-stub"

        def generate(self, prompt: str, **kwargs: Any) -> str:
            raise RuntimeError("provider exploded")

        def embed(self, text: str, **kwargs: Any) -> list[float]:
            raise RuntimeError("provider exploded")

    # only the LLM provider is substituted; the rest of the chain stays real
    monkeypatch.setattr(
        "openmetaphysics.inference.explainer.get_provider",
        lambda *a, **k: _FailingProvider(),
    )

    data = _orchestrate()
    assert data["errors"] == []
    output = data["outputs"][0]
    assert output["result"]["day_master"], "deterministic result must remain available"

    detail = data["explanation_detail"]["bazi"]
    assert detail["degraded"] is True
    assert detail["explanation"], "fallback prose expected"
    assert detail["evidence"]["result"] == output["result"]
    # retrieval still ran even though the provider failed
    assert detail["knowledge"]


def test_e2e_response_shape_is_stable():
    data = _orchestrate()
    assert set(data) >= {
        "request_id",
        "outputs",
        "consensus",
        "explanation",
        "explanation_detail",
        "errors",
    }
    assert set(data["explanation_detail"]["bazi"]) == {
        "explanation",
        "provider",
        "degraded",
        "knowledge",
        "evidence",
        "error",
    }
    # sanity: the runtime is local and clock-independent apart from computed_at
    assert datetime.now(timezone.utc).year >= 2024
