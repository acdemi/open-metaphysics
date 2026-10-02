"""Phase C5 — unified Production Runtime regression suite.

One place that asserts the whole composed surface still holds together:

    API -> calculation -> evidence -> retrieval -> consensus -> explanation

and the invariants that must never regress:

    question preserved
    facts preserved
    deterministic calculation preserved
    provider failure graceful
    knowledge unavailable graceful

The deeper end-to-end walkthrough lives in
``tests/test_e2e_production_runtime.py``; this module is the fast regression
gate over the same surface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from openmetaphysics.agents.registry import get_registry
from openmetaphysics.api.app import app
from openmetaphysics.rag.retriever import reset_retriever

client = TestClient(app, raise_server_exceptions=False)

PAYLOAD = {
    "request_id": "reg",
    "born_at": "1985-08-15T10:00:00+08:00",
    "gender": "male",
    "born_location": {"latitude": 39.9, "longitude": 116.4, "timezone": "Asia/Shanghai"},
    "question": "事业与财运",
}
REQUEST: dict[str, Any] = {
    "request_id": "reg",
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


def _run(**overrides: Any) -> dict[str, Any]:
    response = client.post("/orchestrate", json={**REQUEST, **overrides})
    assert response.status_code == 200, response.text
    return response.json()


def _strip_timestamps(resp: dict[str, Any]) -> dict[str, Any]:
    clone = {k: v for k, v in resp.items() if k != "outputs"}
    clone["outputs"] = [{k: v for k, v in o.items() if k != "computed_at"} for o in resp["outputs"]]
    if resp.get("consensus"):
        consensus = dict(resp["consensus"])
        consensus.pop("computed_at", None)
        clone["consensus"] = consensus
    return clone


# == The whole chain ==


def test_full_chain_health():
    data = _run()
    assert data["errors"] == []
    assert [o["agent"] for o in data["outputs"]] == ["bazi", "ziwei", "liuyao"]

    # calculation
    assert all(o["result"] for o in data["outputs"])
    assert all(o["reasoning_trace"] for o in data["outputs"])

    # evidence
    for output in data["outputs"]:
        evidence = data["explanation_detail"][output["agent"]]["evidence"]
        assert evidence["result"] == output["result"]
        assert evidence["input_hash"] == output["input_hash"]

    # retrieval
    assert all(data["explanation_detail"][o["agent"]]["knowledge"] for o in data["outputs"])

    # consensus
    assert data["consensus"] is not None
    assert len(data["consensus"]["result"]["contributions"]) == 3

    # explanation
    assert set(data["explanation"]) == {"bazi", "ziwei", "liuyao"}
    assert all(data["explanation"].values())


def test_all_registered_domains_compute():
    for name in get_registry().names():
        body: dict[str, Any] = {
            "request_id": f"reg-{name}",
            "born_at": PAYLOAD["born_at"],
            "gender": "male",
        }
        if name == "liuyao":
            body["casts"] = [7, 7, 8, 8, 7, 8]
        response = client.post(f"/agents/{name}/compute", json=body)
        assert response.status_code == 200, f"{name}: {response.text[:160]}"
        assert response.json()["agent"] == name


def test_consensus_is_absent_below_two_agents():
    data = _run(agents=["bazi"])
    assert data["consensus"] is None
    assert data["outputs"][0]["result"]


# == Question preserved ==


def test_question_preserved_through_the_chain():
    data = _run()
    for output in data["outputs"]:
        assert output["metadata"]["question"] == PAYLOAD["question"]
        assert (
            data["explanation_detail"][output["agent"]]["evidence"]["metadata"]["question"]
            == PAYLOAD["question"]
        )


# == Facts preserved ==


def test_facts_preserved_and_not_rewritten_by_explanation():
    without = _run(explain=False)
    with_explain = _run(explain=True)

    facts = lambda r: [  # noqa: E731
        (o["agent"], o["input_hash"], o["result"], o["confidence"]) for o in r["outputs"]
    ]
    assert facts(without) == facts(with_explain)
    assert without["consensus"]["result"] == with_explain["consensus"]["result"]


def test_explain_does_not_recompute():
    data = _run()
    for output in data["outputs"]:
        detail = data["explanation_detail"][output["agent"]]
        assert detail["evidence"]["result"] == output["result"]
        assert detail["evidence"]["engine_version"] == output["engine_version"]


# == Determinism ==


def test_calculation_is_deterministic():
    first, second = _run(), _run()
    assert _strip_timestamps(first) == _strip_timestamps(second)


# == Graceful degradation ==


def test_provider_failure_is_graceful(monkeypatch):
    class _Failing:
        name = "failing-stub"

        def generate(self, prompt: str, **kwargs: Any) -> str:
            raise RuntimeError("provider exploded")

        def embed(self, text: str, **kwargs: Any) -> list[float]:
            raise RuntimeError("provider exploded")

    monkeypatch.setattr(
        "openmetaphysics.inference.explainer.get_provider", lambda *a, **k: _Failing()
    )

    data = _run()
    assert data["errors"] == []
    assert all(o["result"] for o in data["outputs"]), "calculation must survive"
    assert data["consensus"] is not None
    for output in data["outputs"]:
        detail = data["explanation_detail"][output["agent"]]
        assert detail["degraded"] is True
        assert detail["explanation"]
        assert detail["knowledge"]


def test_knowledge_unavailable_is_graceful(monkeypatch):
    monkeypatch.setattr(
        "openmetaphysics.rag.corpus.DEFAULT_CORPUS_PATH", Path("/nonexistent/corpus.json")
    )
    reset_retriever()

    data = _run()
    assert data["errors"] == []
    assert all(o["result"] for o in data["outputs"])
    assert data["consensus"] is not None
    for output in data["outputs"]:
        detail = data["explanation_detail"][output["agent"]]
        assert detail["knowledge"] == []
        assert detail["explanation"]


# == Structured errors ==


def test_invalid_input_is_a_structured_error():
    response = client.post("/orchestrate", json={**REQUEST, "payload": {"request_id": "bad"}})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_domain_failure_is_a_structured_error(monkeypatch):
    agent = get_registry().get("bazi")

    def _boom(payload: Any) -> Any:
        raise RuntimeError("engine exploded")

    monkeypatch.setattr(agent, "compute", _boom)
    response = client.post("/agents/bazi/compute", json=PAYLOAD)
    assert response.status_code == 500
    error = response.json()["error"]
    assert error["type"] == "RuntimeError"
    assert error["agent"] == "bazi"
