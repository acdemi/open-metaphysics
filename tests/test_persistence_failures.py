"""Persistence failure-path behaviour (Prompt 3A).

Two guarantees are asserted here:

* a failed session write must never break or alter the calculation response
  (the existing best-effort contract), and
* the failure must be observable in the server log, without leaking request
  payloads, DSNs or credentials.

These tests were written before the logging fix: on the old code the response
assertions passed but the observability assertions failed (the write error was
silently swallowed).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi.testclient import TestClient

from openmetaphysics.api.app import create_app
from openmetaphysics.core.config import Settings
from openmetaphysics.persistence import InMemorySessionStore, create_store
from openmetaphysics.persistence import store as store_module

BORN = "1990-06-15T08:30:00+09:00"
SECRET_QUESTION = "私密问题：我的银行卡密码与出生信息 123456"
SECRET_DSN = "postgresql://om:supersecret@127.0.0.1:5432/om"
SECRETS = ("supersecret", "123456", "银行卡", "postgresql://", "postgres")


class FailingStore:
    """A ``SessionStore`` whose writes fail (reads return empty)."""

    def __init__(self) -> None:
        self.save_calls = 0

    def save_session(
        self,
        request_id: str,
        request: dict[str, Any],
        response: dict[str, Any],
        traces: list[dict[str, Any]] | None = None,
    ) -> None:
        self.save_calls += 1
        raise RuntimeError(f"store unavailable while writing to {SECRET_DSN}")

    def get_session(self, request_id: str) -> dict[str, Any] | None:
        return None

    def get_traces(self, request_id: str) -> list[dict[str, Any]]:
        return []

    def list_sessions(self) -> list[dict[str, Any]]:
        return []


def _app_with_store(store: Any) -> TestClient:
    app = create_app()
    app.state.session_store = store
    return TestClient(app, raise_server_exceptions=False)


def _compute_body(request_id: str) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "born_at": BORN,
        "gender": "male",
        "question": SECRET_QUESTION,
    }


def _without_computed_at(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: ("<volatile>" if key == "computed_at" else _without_computed_at(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_without_computed_at(item) for item in value]
    return value


def test_failed_session_write_is_logged_without_payload(caplog) -> None:
    store = FailingStore()
    client = _app_with_store(store)

    with caplog.at_level(logging.WARNING):
        response = client.post("/agents/bazi/compute", json=_compute_body("fail-log-1"))

    assert response.status_code == 200, response.text
    assert store.save_calls == 1

    records = [record for record in caplog.records if "persistence" in record.getMessage()]
    assert records, "a failed session write must be observable in the server log"
    assert all(record.levelno == logging.WARNING for record in records)
    messages = "\n".join(record.getMessage() for record in records)
    assert "RuntimeError" in messages, "the log must name the failure class"
    for secret in SECRETS:
        assert secret not in messages, f"persistence log leaked sensitive content: {secret!r}"


def test_compute_response_contract_is_unchanged_when_write_fails() -> None:
    # Same request id: ``input_hash`` is derived from it, so only ``computed_at`` may differ.
    healthy = _app_with_store(InMemorySessionStore()).post(
        "/agents/bazi/compute", json=_compute_body("fail-contract")
    )
    failing = _app_with_store(FailingStore()).post(
        "/agents/bazi/compute", json=_compute_body("fail-contract")
    )
    assert healthy.status_code == failing.status_code == 200
    assert _without_computed_at(healthy.json()) == _without_computed_at(failing.json()), (
        "a persistence failure must not change the calculation response"
    )


def test_orchestrate_keeps_consensus_when_write_fails(caplog) -> None:
    store = FailingStore()
    client = _app_with_store(store)
    body = {
        "request_id": "fail-orch-1",
        "payload": {
            "request_id": "fail-orch-1",
            "born_at": BORN,
            "gender": "male",
            "question": SECRET_QUESTION,
            "seed": 42,
        },
        "agents": ["bazi", "ziwei"],
        "explain": True,
    }

    with caplog.at_level(logging.WARNING):
        response = client.post("/orchestrate", json=body)

    assert response.status_code == 200, response.text
    payload = response.json()
    assert [output["agent"] for output in payload["outputs"]] == ["bazi", "ziwei"]
    assert payload["consensus"] is not None, "consensus must not depend on persistence"
    assert payload["errors"] == []
    assert store.save_calls == 1

    records = [record for record in caplog.records if "persistence" in record.getMessage()]
    assert records, "a failed orchestrate write must be observable"
    for secret in SECRETS:
        assert secret not in "\n".join(record.getMessage() for record in records)

    # The session was not persisted: reads still return the documented 404 shape.
    missing = client.get("/sessions/fail-orch-1")
    assert missing.status_code == 404
    assert missing.json()["error"]["kind"] == "not_found"


def test_successful_write_is_not_logged(caplog) -> None:
    client = _app_with_store(InMemorySessionStore())
    with caplog.at_level(logging.WARNING):
        response = client.post("/agents/bazi/compute", json=_compute_body("fail-log-healthy"))
    assert response.status_code == 200
    assert not [record for record in caplog.records if "persistence" in record.getMessage()]


def test_create_store_logs_fallback_on_bad_dsn(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        store = create_store(Settings(postgres_dsn="bogus://om:supersecret@127.0.0.1:1/db"))

    assert isinstance(store, InMemorySessionStore)
    records = [record for record in caplog.records if record.name == store_module.__name__]
    assert records, "a degraded store initialization must be observable"
    messages = "\n".join(record.getMessage() for record in records)
    assert "falling back" in messages
    for secret in SECRETS:
        assert secret not in messages


def test_create_store_logs_fallback_when_sqlalchemy_missing(caplog, monkeypatch) -> None:
    monkeypatch.setattr(store_module, "SQLALCHEMY_AVAILABLE", False)
    with caplog.at_level(logging.WARNING):
        store = create_store(Settings(postgres_dsn=SECRET_DSN))

    assert isinstance(store, InMemorySessionStore)
    records = [record for record in caplog.records if record.name == store_module.__name__]
    assert records, "a missing persist extra must be observable when a DSN is configured"
    messages = "\n".join(record.getMessage() for record in records)
    assert "SQLAlchemy" in messages
    for secret in SECRETS:
        assert secret not in messages
