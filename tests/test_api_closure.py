"""Phase A4 — API / orchestration closure.

Covers the runtime composition exposed over HTTP:

    HTTP request -> orchestration -> deterministic calculation -> evidence
    -> knowledge retrieval -> explanation -> HTTP response

Route names are the pre-existing ``/agents/{name}/...`` ones; this phase added
only the ``?explain=true`` option and structured error bodies.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from openmetaphysics.api.app import app

client = TestClient(app, raise_server_exceptions=False)

BAZI_BODY: dict[str, Any] = {
    "request_id": "a",
    "born_at": "1985-08-15T10:00:00+08:00",
    "gender": "male",
}
ZIWEI_BODY: dict[str, Any] = {
    "request_id": "z",
    "born_at": "1985-08-15T10:00:00+08:00",
    "gender": "male",
}


# == Valid request ==


def test_compute_valid_request():
    r = client.post("/agents/bazi/compute", json=BAZI_BODY)
    assert r.status_code == 200
    assert len(r.json()["result"]["pillars"]) == 4


def test_compute_all_domain_agents():
    for name, body in (
        ("bazi", BAZI_BODY),
        ("ziwei", ZIWEI_BODY),
        ("qimen", BAZI_BODY),
        ("liuyao", {**BAZI_BODY, "casts": [7, 7, 7, 7, 7, 7]}),
    ):
        r = client.post(f"/agents/{name}/compute", json=body)
        assert r.status_code == 200, f"{name}: {r.text[:200]}"
        assert r.json()["agent"] == name


# == Invalid request ==


def test_compute_invalid_request_422():
    r = client.post(
        "/agents/bazi/compute",
        json={"request_id": "a", "born_at": "2024-01-01T00:00:00"},  # naive datetime
    )
    assert r.status_code == 422
    assert "detail" in r.json()


def test_compute_unknown_agent_404():
    r = client.post("/agents/nope/compute", json=BAZI_BODY)
    assert r.status_code == 404


def test_explain_unknown_agent_404():
    r = client.post("/agents/nope/explain", json={"output": {}})
    assert r.status_code == 404


def test_explain_invalid_output_422():
    r = client.post("/agents/ziwei/explain", json={"output": {"not": "an output"}})
    assert r.status_code == 422
    assert "detail" in r.json()


# == Deterministic response ==


def test_compute_response_is_deterministic():
    first = client.post("/agents/bazi/compute", json=BAZI_BODY).json()
    second = client.post("/agents/bazi/compute", json=BAZI_BODY).json()

    assert first["input_hash"] == second["input_hash"]
    assert first["result"] == second["result"]
    # the calculation payload is reproducible byte-for-byte; only the
    # wall-clock envelope timestamp varies
    a, b = dict(first), dict(second)
    a.pop("computed_at")
    b.pop("computed_at")
    assert a == b


# == Explain response ==


def test_compute_with_explain_returns_chain():
    r = client.post("/agents/ziwei/compute?explain=true", json=ZIWEI_BODY)
    assert r.status_code == 200
    data = r.json()

    # calculation result is still present and unchanged
    assert data["result"]["wuxing_ju"]
    # explanation ran against the already-computed output
    explain = data["explain"]
    assert explain["text"]
    assert explain["degraded"] is True  # no LLM provider configured
    # knowledge retrieval is part of the response, with citations
    assert explain["knowledge"], "explain response must carry retrieved knowledge"
    assert all(k["id"].startswith("kn:") for k in explain["knowledge"])
    assert all(k["source"] for k in explain["knowledge"])


def test_explain_option_does_not_change_the_calculation():
    plain = client.post("/agents/ziwei/compute", json=ZIWEI_BODY).json()
    explained = client.post("/agents/ziwei/compute?explain=true", json=ZIWEI_BODY).json()

    assert explained["result"] == plain["result"]
    assert explained["confidence"] == plain["confidence"]
    assert explained["input_hash"] == plain["input_hash"]


def test_explain_endpoint_explains_an_already_computed_output():
    output = client.post("/agents/ziwei/compute", json=ZIWEI_BODY).json()
    r = client.post("/agents/ziwei/explain", json={"output": output})
    assert r.status_code == 200
    data = r.json()
    assert data["agent"] == "ziwei"
    assert data["explanation"]
    assert data["knowledge"]


# == Error response ==


def test_domain_calculation_error_is_structured(monkeypatch):
    from openmetaphysics.agents.registry import get_registry

    agent = get_registry().get("bazi")

    def _boom(payload: Any) -> Any:
        raise RuntimeError("engine exploded")

    monkeypatch.setattr(agent, "compute", _boom)

    r = client.post("/agents/bazi/compute", json=BAZI_BODY)
    assert r.status_code == 500
    error = r.json()["error"]
    assert error["type"] == "RuntimeError"
    assert error["message"] == "engine exploded"
    assert error["agent"] == "bazi"


def test_explain_failure_does_not_break_the_calculation(monkeypatch):
    import openmetaphysics.api.app as app_module

    def _boom(agent_name: str) -> Any:
        raise RuntimeError("explainer exploded")

    monkeypatch.setattr(app_module, "get_explainer_for", _boom)

    r = client.post("/agents/bazi/compute?explain=true", json=BAZI_BODY)
    assert r.status_code == 200, "an explain failure must not turn into a request failure"
    data = r.json()
    assert data["result"]["pillars"], "deterministic result must survive an explain failure"
    assert data["explain"]["error"]["type"] == "RuntimeError"
    assert data["explain"]["degraded"] is True


# == End-to-end over HTTP ==


def test_http_orchestration_to_explanation_end_to_end():
    r = client.post(
        "/orchestrate",
        json={
            "request_id": "e2e",
            "payload": {
                "request_id": "e2e",
                "born_at": "1985-08-15T10:00:00+08:00",
                "gender": "male",
            },
            "agents": ["ziwei"],
            "explain": True,
        },
    )
    assert r.status_code == 200
    data = r.json()

    # calculation
    assert [o["agent"] for o in data["outputs"]] == ["ziwei"]
    assert data["outputs"][0]["result"]["wuxing_ju"]

    # explanation + knowledge provenance
    assert data["explanation"]["ziwei"]
    detail = data["explanation_detail"]["ziwei"]
    assert detail["knowledge"], "orchestration explain must expose retrieved knowledge"
    assert all(k["id"].startswith("kn:") for k in detail["knowledge"])
    assert all(k["source"] for k in detail["knowledge"])
    assert detail["degraded"] is True
