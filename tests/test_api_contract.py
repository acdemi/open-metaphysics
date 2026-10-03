"""Productization P1 — public API contract tests (black-box HTTP).

Covers the four domain operations, the explain switch, the error model, the
provider/knowledge degradation paths, question propagation, fact preservation,
response-shape stability and a full runtime E2E over HTTP.

Only the LLM provider is ever substituted; calculation, evidence, retrieval and
consensus run for real. No external service is used.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from openmetaphysics.api.app import app
from openmetaphysics.rag.retriever import reset_retriever

client = TestClient(app, raise_server_exceptions=False)

BORN = "1985-08-15T10:00:00+08:00"
QUESTION = "事业与财运"
DOMAINS = ("bazi", "ziwei", "qimen", "liuyao")

# the four domain operations accept the same core request envelope
COMMON: dict[str, Any] = {"born_at": BORN, "gender": "male", "question": QUESTION}


def body_for(domain: str, request_id: str = "p1") -> dict[str, Any]:
    payload = {"request_id": request_id, **COMMON}
    if domain == "liuyao":
        payload["casts"] = [7, 7, 8, 8, 7, 8]
    return payload


@pytest.fixture(autouse=True)
def _fresh_retriever():
    reset_retriever()
    yield
    reset_retriever()


class _FailingProvider:
    name = "failing-stub"

    def generate(self, prompt: str, **kwargs: Any) -> str:
        raise TimeoutError("read timed out")

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        raise TimeoutError("read timed out")


# == 1 + 2. each domain, valid calculation ==


@pytest.mark.parametrize("domain", DOMAINS)
def test_valid_calculation_per_domain(domain: str):
    r = client.post(f"/agents/{domain}/compute", json=body_for(domain))
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["agent"] == domain
    assert data["request_id"] == "p1"
    assert data["result"], "a deterministic result is required"
    assert data["confidence"]["value"] >= 0.0
    assert data["reasoning_trace"], "the deterministic engines emit a trace"
    assert data["input_hash"]


@pytest.mark.parametrize("domain", DOMAINS)
def test_request_id_and_question_propagate_per_domain(domain: str):
    r = client.post(f"/agents/{domain}/compute", json=body_for(domain, request_id="abc-123"))
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["request_id"] == "abc-123"
    assert data["metadata"]["question"] == QUESTION


# == 3. invalid input ==


@pytest.mark.parametrize("domain", DOMAINS)
def test_invalid_input_is_the_same_error_family(domain: str):
    # a tz-naive timestamp is invalid for every domain
    r = client.post(
        f"/agents/{domain}/compute", json={"request_id": "x", "born_at": "2024-01-01T00:00:00"}
    )
    assert r.status_code == 422
    payload = r.json()
    assert "detail" in payload
    assert payload["error"]["kind"] == "invalid_request"


def test_invalid_casts_are_rejected_for_liuyao():
    payload = body_for("liuyao")
    payload["casts"] = [5, 7, 7, 7, 7, 7]
    r = client.post("/agents/liuyao/compute", json=payload)
    assert r.status_code == 422
    assert r.json()["error"]["kind"] == "invalid_request"


# == 4 + 5. explain switch ==


@pytest.mark.parametrize("domain", DOMAINS)
def test_explain_defaults_to_off(domain: str):
    data = client.post(f"/agents/{domain}/compute", json=body_for(domain)).json()
    assert "explain" not in data


@pytest.mark.parametrize("domain", DOMAINS)
def test_explain_on_adds_one_uniform_block(domain: str):
    data = client.post(f"/agents/{domain}/compute?explain=true", json=body_for(domain)).json()
    explain = data["explain"]
    assert set(explain) == {
        "explanation",
        "provider",
        "degraded",
        "knowledge",
        "evidence",
        "error",
    }
    assert explain["explanation"]
    assert explain["provider"] is None and explain["degraded"] is True
    assert explain["error"] is None, "offline is not a provider failure"
    assert explain["knowledge"], "knowledge retrieval must run"
    assert all(k["id"].startswith("kn:") and k["source"] for k in explain["knowledge"])


@pytest.mark.parametrize("domain", DOMAINS)
def test_explain_parameters_behave_consistently(domain: str):
    one = client.post(f"/agents/{domain}/compute?explain=true&k=1", json=body_for(domain)).json()
    assert len(one["explain"]["knowledge"]) == 1

    none = client.post(f"/agents/{domain}/compute?explain=true&k=0", json=body_for(domain)).json()
    assert none["explain"]["knowledge"] == []

    bad_style = client.post(f"/agents/{domain}/compute?explain=bogus", json=body_for(domain))
    assert bad_style.status_code == 422

    bad_k = client.post(f"/agents/{domain}/compute?explain=true&k=abc", json=body_for(domain))
    assert bad_k.status_code == 422


# == 6. provider failure ==


@pytest.mark.parametrize("domain", DOMAINS)
def test_provider_failure_degrades_without_failing_the_request(domain: str, monkeypatch):
    monkeypatch.setattr(
        "openmetaphysics.inference.explainer.get_provider", lambda *a, **k: _FailingProvider()
    )
    r = client.post(f"/agents/{domain}/compute?explain=true", json=body_for(domain))
    assert r.status_code == 200, "a provider failure must not become an HTTP error"
    data = r.json()

    # calculation is intact
    assert data["result"] and data["input_hash"]
    # the explanation degraded and recorded the failure, classified
    explain = data["explain"]
    assert explain["degraded"] is True
    assert explain["explanation"], "fallback prose expected"
    assert explain["error"]["kind"] == "timeout"
    assert explain["error"]["provider"] == "failing-stub"
    # a provider error never masquerades as a calculation error
    assert "error" not in data or data.get("error") is None


# == 7. knowledge unavailable ==


def test_knowledge_unavailable_degrades_without_failing(monkeypatch):
    monkeypatch.setattr(
        "openmetaphysics.rag.corpus.DEFAULT_CORPUS_PATH", Path("/nonexistent/corpus.json")
    )
    reset_retriever()

    r = client.post("/agents/ziwei/compute?explain=true", json=body_for("ziwei"))
    assert r.status_code == 200
    data = r.json()
    assert data["result"], "calculation must survive an unavailable corpus"
    assert data["explain"]["knowledge"] == []
    assert data["explain"]["explanation"]
    assert data["explain"]["error"] is None


# == 8. question propagation ==


@pytest.mark.parametrize("domain", DOMAINS)
def test_question_reaches_the_explain_evidence(domain: str):
    data = client.post(f"/agents/{domain}/compute?explain=true", json=body_for(domain)).json()
    assert data["explain"]["evidence"]["metadata"]["question"] == QUESTION


# == 9. deterministic result preservation ==


@pytest.mark.parametrize("domain", DOMAINS)
def test_explain_never_changes_the_deterministic_result(domain: str):
    plain = client.post(f"/agents/{domain}/compute", json=body_for(domain)).json()
    explained = client.post(f"/agents/{domain}/compute?explain=true", json=body_for(domain)).json()

    assert explained["result"] == plain["result"]
    assert explained["confidence"] == plain["confidence"]
    assert explained["input_hash"] == plain["input_hash"]
    assert explained["explain"]["evidence"]["result"] == plain["result"]


@pytest.mark.parametrize("domain", DOMAINS)
def test_calculation_is_reproducible(domain: str):
    first = client.post(f"/agents/{domain}/compute", json=body_for(domain)).json()
    second = client.post(f"/agents/{domain}/compute", json=body_for(domain)).json()
    assert first["result"] == second["result"]
    assert first["input_hash"] == second["input_hash"]
    # computed_at stays an envelope field and is the only volatile value
    volatile = {"computed_at"}
    assert {k: v for k, v in first.items() if k not in volatile} == {
        k: v for k, v in second.items() if k not in volatile
    }
    assert "computed_at" not in first["result"]


# == 10. response shape stability ==


@pytest.mark.parametrize("domain", DOMAINS)
def test_response_shape_is_stable(domain: str):
    data = client.post(f"/agents/{domain}/compute", json=body_for(domain)).json()
    assert set(data) == {
        "request_id",
        "agent",
        "engine_version",
        "input_hash",
        "computed_at",
        "confidence",
        "reasoning_trace",
        "metadata",
        "result",
    }
    assert set(data["confidence"]) == {"value", "method", "factors"}


# == error model ==


def test_unknown_agent_is_404_with_a_stable_kind():
    r = client.post("/agents/nope/compute", json=body_for("bazi"))
    assert r.status_code == 404
    assert r.json()["error"]["kind"] == "unknown_agent"

    r = client.post("/agents/nope/explain", json={"output": {}})
    assert r.status_code == 404
    assert r.json()["error"]["kind"] == "unknown_agent"

    assert client.get("/agents/nope/schema").status_code == 404


def test_fastapi_level_validation_shares_the_422_shape():
    """A body rejected before the handler runs still carries ``error.kind``."""
    r = client.post("/agents/bazi/explain", json={"wrong": "shape"})
    assert r.status_code == 422
    assert r.json()["error"]["kind"] == "invalid_request"


def test_orchestrate_all_unknown_agents_is_404():
    r = client.post(
        "/orchestrate",
        json={"request_id": "x", "payload": body_for("bazi"), "agents": ["nope", "also_nope"]},
    )
    assert r.status_code == 404
    error = r.json()["error"]
    assert error["kind"] == "unknown_agent"
    assert error["agents"] == ["also_nope", "nope"]


def test_orchestrate_partial_unknown_keeps_batch_semantics():
    r = client.post(
        "/orchestrate",
        json={"request_id": "x", "payload": body_for("bazi"), "agents": ["bazi", "nope"]},
    )
    assert r.status_code == 200
    data = r.json()
    assert [o["agent"] for o in data["outputs"]] == ["bazi"]
    assert any("nope" in e for e in data["errors"])


def test_calculation_failure_is_500_with_a_stable_kind(monkeypatch):
    from openmetaphysics.agents.registry import get_registry

    agent = get_registry().get("bazi")

    def _boom(payload: Any) -> Any:
        raise RuntimeError("engine exploded")

    monkeypatch.setattr(agent, "compute", _boom)
    r = client.post("/agents/bazi/compute", json=body_for("bazi"))
    assert r.status_code == 500
    error = r.json()["error"]
    assert error["kind"] == "calculation_failed"
    assert error["type"] == "RuntimeError"
    assert error["agent"] == "bazi"


# == P1.6 full runtime E2E over HTTP ==


def test_full_runtime_e2e_over_http():
    r = client.post(
        "/orchestrate",
        json={
            "request_id": "e2e-p1",
            "payload": body_for("bazi"),
            "agents": ["bazi", "ziwei", "liuyao"],
            "explain": True,
        },
    )
    assert r.status_code == 200
    data = r.json()

    # validation + calculation
    assert data["errors"] == []
    assert [o["agent"] for o in data["outputs"]] == ["bazi", "ziwei", "liuyao"]
    assert all(o["result"] and o["reasoning_trace"] for o in data["outputs"])
    assert all(o["metadata"]["question"] == QUESTION for o in data["outputs"])

    # evidence is exactly the deterministic fact layer
    for output in data["outputs"]:
        evidence = data["explanation_detail"][output["agent"]]["evidence"]
        assert evidence["result"] == output["result"]
        assert evidence["input_hash"] == output["input_hash"]

    # retrieval ran for every explained agent
    assert all(data["explanation_detail"][o["agent"]]["knowledge"] for o in data["outputs"])

    # consensus ran over the real outputs
    assert data["consensus"] is not None
    assert len(data["consensus"]["result"]["contributions"]) == 3

    # explanation produced
    assert set(data["explanation"]) == {"bazi", "ziwei", "liuyao"}
    assert all(data["explanation"].values())
