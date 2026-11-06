"""Orchestration runtime-failure semantics (Prompt 3A).

Distinguishes the three cases the graph must treat differently:

* unknown agent name -> request-level 404 when *all* names are unknown, and a
  per-agent ``unknown agent: <name>`` entry in ``errors`` otherwise;
* known agent whose ``compute`` raises -> the run continues, the error is
  recorded as ``<name>: <ExceptionType>: <message>``;
* enough surviving agents -> consensus is built from survivors only.

The all-agents-crash case is asserted as its current behaviour (HTTP 200 with
``outputs=[]`` and per-agent ``errors``); no new status code or response field
is introduced by this task.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from openmetaphysics.agents.registry import get_registry
from openmetaphysics.api.app import create_app
from openmetaphysics.persistence import InMemorySessionStore

BORN = "1990-06-15T08:30:00+09:00"


def _client() -> TestClient:
    app = create_app()
    app.state.session_store = InMemorySessionStore()
    return TestClient(app)


def _post(client: TestClient, request_id: str, agents: list[str], explain: bool = False) -> Any:
    response = client.post(
        "/orchestrate",
        json={
            "request_id": request_id,
            "payload": {
                "request_id": request_id,
                "born_at": BORN,
                "gender": "male",
                "question": "运行期故障测试",
                "seed": 42,
            },
            "agents": agents,
            "explain": explain,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _make_crash(monkeypatch, names: list[str]) -> None:
    def boom(payload: Any) -> Any:
        raise RuntimeError("agent blew up in compute")

    registry = get_registry()
    for name in names:
        monkeypatch.setattr(registry.get(name), "compute", boom)


def test_one_agent_crash_keeps_others_and_consensus(monkeypatch) -> None:
    _make_crash(monkeypatch, ["bazi"])
    client = _client()

    data = _post(client, "orch-crash-1", ["bazi", "ziwei", "liuyao", "qimen"], explain=True)

    assert [output["agent"] for output in data["outputs"]] == ["ziwei", "liuyao", "qimen"]
    assert data["errors"] == ["bazi: RuntimeError: agent blew up in compute"]

    assert data["consensus"] is not None, "2+ survivors must still get consensus"
    report = data["consensus"]["result"]
    contributing = {item["agent"] for item in report["contributions"]}
    assert contributing == {"ziwei", "liuyao", "qimen"}
    assert set(report["agreement_matrix"]) == {"ziwei", "liuyao", "qimen"}
    assert "bazi" not in contributing, "a crashed agent must not contribute to consensus"

    assert set(data["explanation"]) == {"ziwei", "liuyao", "qimen"}
    assert set(data["explanation_detail"]) == {"ziwei", "liuyao", "qimen"}


def test_one_crash_out_of_two_leaves_no_consensus(monkeypatch) -> None:
    _make_crash(monkeypatch, ["bazi"])
    client = _client()

    data = _post(client, "orch-crash-2", ["bazi", "ziwei"])

    assert [output["agent"] for output in data["outputs"]] == ["ziwei"]
    assert data["consensus"] is None
    assert data["errors"] == ["bazi: RuntimeError: agent blew up in compute"]


def test_all_known_agents_crashing_is_a_recorded_batch(monkeypatch) -> None:
    _make_crash(monkeypatch, ["bazi", "ziwei"])
    client = _client()

    data = _post(client, "orch-crash-3", ["bazi", "ziwei"], explain=True)

    # Current contract: the batch still succeeds (HTTP 200) and every failure is visible.
    assert set(data) == {
        "request_id",
        "outputs",
        "consensus",
        "explanation",
        "explanation_detail",
        "errors",
    }
    assert data["request_id"] == "orch-crash-3"
    assert data["outputs"] == []
    assert data["consensus"] is None
    assert data["explanation"] == {}
    assert data["explanation_detail"] == {}
    assert data["errors"] == [
        "bazi: RuntimeError: agent blew up in compute",
        "ziwei: RuntimeError: agent blew up in compute",
    ]


def test_crash_and_unknown_agent_share_batch_semantics(monkeypatch) -> None:
    _make_crash(monkeypatch, ["bazi"])
    client = _client()

    data = _post(client, "orch-crash-4", ["bazi", "nope"])

    assert data["outputs"] == []
    assert data["consensus"] is None
    # Unknown names are recorded during routing, before the fan-out runs.
    assert data["errors"] == [
        "unknown agent: nope",
        "bazi: RuntimeError: agent blew up in compute",
    ]


def test_all_unknown_agents_still_404() -> None:
    client = _client()
    response = client.post(
        "/orchestrate",
        json={
            "request_id": "orch-crash-unknown",
            "payload": {"request_id": "orch-crash-unknown", "born_at": BORN},
            "agents": ["nope", "also-nope"],
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["kind"] == "unknown_agent"
