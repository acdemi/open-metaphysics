"""会话历史 API 契约：GET /sessions、GET /sessions/{id}、GET /traces/{id}。

这是前端「历史会话 → 结果恢复 → Trace 查看」业务闭环所依赖的后端契约：
列表 → 会话信封（request/response）→ 追踪，且 request_id 在三个端点间一致。
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from openmetaphysics.api.app import create_app
from openmetaphysics.persistence import InMemorySessionStore

BORN = "1990-06-15T08:30:00+09:00"


def _client() -> tuple[Any, TestClient]:
    app = create_app()
    app.state.session_store = InMemorySessionStore()
    return app, TestClient(app, raise_server_exceptions=False)


def _orchestrate(client: TestClient, request_id: str, agents: list[str]) -> dict[str, Any]:
    response = client.post(
        "/orchestrate",
        json={
            "request_id": request_id,
            "payload": {
                "request_id": request_id,
                "born_at": BORN,
                "gender": "male",
                "question": "历史会话契约测试",
                "seed": 42,
            },
            "agents": agents,
            "explain": True,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_empty_sessions_list() -> None:
    _, client = _client()
    response = client.get("/sessions")
    assert response.status_code == 200
    assert response.json() == {"sessions": []}


def test_orchestrate_session_is_listed_and_restorable() -> None:
    _, client = _client()
    fresh = _orchestrate(client, "history-1", ["bazi", "ziwei"])

    listing = client.get("/sessions")
    assert listing.status_code == 200
    sessions = listing.json()["sessions"]
    assert [item["request_id"] for item in sessions] == ["history-1"]
    assert isinstance(sessions[0]["created_at"], str) and sessions[0]["created_at"]

    stored_response = client.get("/sessions/history-1")
    assert stored_response.status_code == 200
    stored = stored_response.json()
    assert set(stored) == {"request_id", "created_at", "request", "response"}
    assert stored["request_id"] == "history-1"
    assert stored["request"]["request_id"] == "history-1"
    assert stored["request"]["payload"]["born_at"] == BORN
    # 存储的 response 必须与当次 /orchestrate 返回一致（可被前端 parseOrchestrationResponse 还原）
    assert stored["response"]["request_id"] == "history-1"
    assert stored["response"]["outputs"] == fresh["outputs"]
    assert stored["response"]["consensus"] == fresh["consensus"]
    assert stored["response"]["errors"] == []
    assert set(stored["response"]) == {
        "request_id",
        "outputs",
        "consensus",
        "explanation",
        "explanation_detail",
        "errors",
    }

    traces = client.get("/traces/history-1")
    assert traces.status_code == 200
    trace_payload = traces.json()
    assert trace_payload["request_id"] == "history-1"
    assert [item["agent"] for item in trace_payload["traces"]] == ["bazi", "ziwei"]
    assert all(item["steps"] for item in trace_payload["traces"])


def test_unknown_session_and_traces_are_404_with_error_shape() -> None:
    _, client = _client()

    session = client.get("/sessions/does-not-exist")
    assert session.status_code == 404
    assert set(session.json()) == {"detail", "error"}
    assert session.json()["error"]["kind"] == "not_found"

    traces = client.get("/traces/does-not-exist")
    assert traces.status_code == 404
    assert set(traces.json()) == {"detail", "error"}
    assert traces.json()["error"]["kind"] == "not_found"


def test_single_domain_session_round_trips() -> None:
    _, client = _client()
    _orchestrate(client, "history-single", ["bazi"])

    stored = client.get("/sessions/history-single").json()
    assert [output["agent"] for output in stored["response"]["outputs"]] == ["bazi"]
    assert stored["response"]["consensus"] is None

    traces = client.get("/traces/history-single").json()
    assert [item["agent"] for item in traces["traces"]] == ["bazi"]
