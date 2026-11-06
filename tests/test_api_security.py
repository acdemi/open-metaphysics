"""P2.2 API protection tests: auth, rate limiting, pagination, birth redaction.

Compatibility contract under test: with ``Settings.api_key`` unset (the
default), auth/rate limiting are no-ops and ``GET /sessions`` keeps the legacy
``{"sessions": [...]}`` envelope. Pagination is opt-in via ``limit``/``offset``.

Rate limiting uses an injectable clock (``app.state.rate_limiter.now``) so the
429 path is deterministic instead of sleeping 60 seconds.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from openmetaphysics.api.app import create_app
from openmetaphysics.core.config import Settings
from openmetaphysics.persistence import (
    InMemorySessionStore,
    SqlAlchemySessionStore,
)

BORN = "1990-06-15T08:30:00+09:00"


def _client(settings: Settings | None = None) -> tuple[Any, TestClient]:
    app = create_app(settings or Settings())
    app.state.session_store = InMemorySessionStore()
    return app, TestClient(app, raise_server_exceptions=False)


def _seed_sessions(store: InMemorySessionStore, count: int) -> None:
    for index in range(count):
        store.save_session(
            f"s{index}",
            {"request_id": f"s{index}", "born_at": BORN},
            {"request_id": f"s{index}"},
            [{"agent": "bazi", "steps": [{"step": 1, "inputs": {"born_at": BORN}}]}],
        )


# -- backwards compatibility (no API key) ----------------------------------


def test_without_api_key_auth_is_disabled_and_responses_are_legacy() -> None:
    _, client = _client()
    listing = client.get("/sessions")
    assert listing.status_code == 200
    assert listing.json() == {"sessions": []}

    # no auth required anywhere; no rate limiting when no key is configured
    for _ in range(100):
        response = client.get("/sessions")
        assert response.status_code == 200
    assert client.get("/sessions/missing").status_code == 404
    assert client.get("/traces/missing").status_code == 404
    assert client.get("/health").status_code == 200
    assert client.get("/agents").status_code == 200


def test_unprotected_routes_never_require_a_key() -> None:
    _, client = _client(Settings(api_key="secret"))
    assert client.get("/health").status_code == 200
    assert client.get("/agents").status_code == 200
    assert client.get("/agents/bazi/schema").status_code == 200


# -- auth matrix ------------------------------------------------------------


PROTECTED_REQUESTS: list[tuple[str, str, dict[str, Any] | None]] = [
    ("GET", "/sessions", None),
    ("GET", "/sessions/whatever", None),
    ("GET", "/traces/whatever", None),
    ("POST", "/orchestrate", {"request_id": "x", "payload": {"request_id": "x"}}),
    ("POST", "/agents/bazi/compute", {"request_id": "x", "born_at": BORN}),
    ("POST", "/agents/bazi/explain", {"output": {}}),
]


@pytest.mark.parametrize(("method", "path", "body"), PROTECTED_REQUESTS)
def test_missing_key_returns_401(method: str, path: str, body: dict[str, Any] | None) -> None:
    _, client = _client(Settings(api_key="secret"))
    response = client.request(method, path, json=body)
    assert response.status_code == 401, response.text
    assert response.headers.get("www-authenticate") == "Bearer"


@pytest.mark.parametrize(("method", "path", "body"), PROTECTED_REQUESTS)
def test_wrong_key_returns_403(method: str, path: str, body: dict[str, Any] | None) -> None:
    _, client = _client(Settings(api_key="secret"))
    response = client.request(method, path, json=body, headers={"X-API-Key": "wrong"})
    assert response.status_code == 403, response.text


@pytest.mark.parametrize(
    "headers",
    [
        {"X-API-Key": "secret"},
        {"Authorization": "Bearer secret"},
    ],
)
def test_correct_key_unlocks_protected_routes(headers: dict[str, str]) -> None:
    _, client = _client(Settings(api_key="secret"))
    assert client.get("/sessions", headers=headers).status_code == 200
    assert client.get("/health").status_code == 200


# -- rate limiting ----------------------------------------------------------


def test_rate_limit_returns_429_and_recovers_after_window() -> None:
    app, client = _client(Settings(api_key="secret", rate_limit_per_minute=2))
    app.state.rate_limiter.now = lambda: 0.0  # injectable clock
    headers = {"X-API-Key": "secret"}

    assert client.get("/sessions", headers=headers).status_code == 200
    assert client.get("/sessions", headers=headers).status_code == 200
    limited = client.get("/sessions", headers=headers)
    assert limited.status_code == 429, limited.text
    assert limited.headers.get("retry-after") == "60"

    app.state.rate_limiter.now = lambda: 61.0
    assert client.get("/sessions", headers=headers).status_code == 200


def test_rate_limit_zero_disables_limiting() -> None:
    _, client = _client(Settings(api_key="secret", rate_limit_per_minute=0))
    headers = {"X-API-Key": "secret"}
    for _ in range(10):
        assert client.get("/sessions", headers=headers).status_code == 200


def test_rate_limit_does_not_apply_without_api_key() -> None:
    _, client = _client(Settings(rate_limit_per_minute=1))
    for _ in range(5):
        assert client.get("/sessions").status_code == 200


# -- pagination -------------------------------------------------------------


def test_paginated_envelope_and_boundaries() -> None:
    app, client = _client()
    _seed_sessions(app.state.session_store, 3)

    page = client.get("/sessions?limit=2&offset=0").json()
    assert set(page) == {"sessions", "total", "limit", "offset"}
    assert [item["request_id"] for item in page["sessions"]] == ["s0", "s1"]
    assert page["total"] == 3 and page["limit"] == 2 and page["offset"] == 0

    tail = client.get("/sessions?limit=2&offset=2").json()
    assert [item["request_id"] for item in tail["sessions"]] == ["s2"]

    empty = client.get("/sessions?limit=2&offset=99").json()
    assert empty["sessions"] == [] and empty["total"] == 3

    # offset without limit defaults to 50
    offset_only = client.get("/sessions?offset=1").json()
    assert offset_only["limit"] == 50
    assert [item["request_id"] for item in offset_only["sessions"]] == ["s1", "s2"]

    # legacy envelope must stay byte-shape compatible
    legacy = client.get("/sessions").json()
    assert set(legacy) == {"sessions"}
    assert len(legacy["sessions"]) == 3


@pytest.mark.parametrize("query", ["limit=0", "limit=201", "offset=-1"])
def test_invalid_pagination_query_is_422(query: str) -> None:
    _, client = _client()
    response = client.get(f"/sessions?{query}")
    assert response.status_code == 422, response.text


def test_pagination_does_not_leak_birth_data() -> None:
    app, client = _client()
    _seed_sessions(app.state.session_store, 2)
    page = client.get("/sessions?limit=1&offset=0").json()
    for item in page["sessions"]:
        assert set(item) == {"request_id", "created_at"}
        assert "born_at" not in item and "born_location" not in item

    detail = client.get("/sessions/s0").json()
    # default (redact=false) keeps the stored birth fields for compatibility
    assert detail["request"]["born_at"] == BORN


# -- birth redaction --------------------------------------------------------


def test_session_redact_birth_defaults_false() -> None:
    app, client = _client()
    app.state.session_store.save_session(
        "r1",
        {"request_id": "r1", "born_at": BORN, "born_location": {"latitude": 31.2}},
        {"request_id": "r1"},
    )
    detail = client.get("/sessions/r1").json()
    assert detail["request"]["born_at"] == BORN
    assert "born_location" in detail["request"]


def test_session_redact_birth_removes_birth_fields_from_session_and_trace() -> None:
    app, client = _client(Settings(session_redact_birth=True))
    app.state.session_store.save_session(
        "r2",
        {
            "request_id": "r2",
            "born_at": BORN,
            "born_location": {"latitude": 31.2, "longitude": 121.5},
        },
        {"request_id": "r2"},
        [{"agent": "bazi", "steps": [{"step": 1, "inputs": {"born_at": BORN}}]}],
    )
    detail = client.get("/sessions/r2").json()
    assert "born_at" not in detail["request"]
    assert "born_location" not in detail["request"]
    trace = client.get("/traces/r2").json()
    assert "born_at" not in trace["traces"][0]["steps"][0]["inputs"]


# -- SQLAlchemy store pagination (Postgres branch mocked, no PG needed) -----


def _fake_connection(rows: list[Any]) -> Any:
    class _Result:
        def all(self) -> list[Any]:
            return rows

        def scalar_one(self) -> int:
            return len(rows)

    class _Connection:
        def __init__(self) -> None:
            self.statements: list[str] = []

        def __enter__(self) -> _Connection:
            return self

        def __exit__(self, *exc: object) -> None:
            return None

        def execute(self, statement: Any) -> _Result:
            self.statements.append(str(statement))
            return _Result()

    return _Connection()


def test_sqlalchemy_store_pagination_compiles_limit_offset(tmp_path: Any) -> None:
    store = SqlAlchemySessionStore(f"sqlite:///{tmp_path / 'p2.db'}")
    for index in range(3):
        store.save_session(f"s{index}", {"request_id": f"s{index}"}, {}, [])
    assert store.count_sessions() == 3
    assert [row["request_id"] for row in store.list_sessions(limit=2, offset=1)] in (
        ["s1", "s2"],
        ["s1", "s0"],
    )
    assert store.list_sessions(limit=0, offset=0) == []

    # Mock the SQLAlchemy connection: no PostgreSQL server is available here.
    fake = _fake_connection(
        [SimpleNamespace(request_id="s9", created_at="2026-01-01T00:00:00+00:00")]
    )
    store._engine.connect = lambda: fake  # type: ignore[method-assign]
    rows = store.list_sessions(limit=2, offset=4)
    assert [row["request_id"] for row in rows] == ["s9"]
    assert any("LIMIT" in statement and "OFFSET" in statement for statement in fake.statements)
    assert store.count_sessions() == 1
    assert any("count" in statement.lower() for statement in fake.statements)
