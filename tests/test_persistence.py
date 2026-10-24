"""Session / trace persistence tests (offline; SQLite for the SQL store)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from openmetaphysics.api.app import create_app
from openmetaphysics.core.config import Settings
from openmetaphysics.persistence import (
    InMemorySessionStore,
    SqlAlchemySessionStore,
    create_store,
)

BORN = "1985-08-15T10:00:00+08:00"


def test_inmemory_roundtrip() -> None:
    store = InMemorySessionStore()
    store.save_session("r1", {"in": 1}, {"out": 2}, [{"agent": "bazi", "steps": [{"step": 1}]}])
    assert store.get_session("r1")["request"] == {"in": 1}
    assert store.get_session("r1")["response"] == {"out": 2}
    assert store.get_traces("r1") == [{"agent": "bazi", "steps": [{"step": 1}]}]
    assert store.get_session("missing") is None
    assert store.get_traces("missing") == []
    assert [s["request_id"] for s in store.list_sessions()] == ["r1"]


def test_sqlalchemy_sqlite_persists_across_instances(tmp_path) -> None:
    dsn = f"sqlite:///{tmp_path / 'om.db'}"
    first = SqlAlchemySessionStore(dsn)
    first.save_session(
        "r2",
        {"request_id": "r2"},
        {"request_id": "r2", "value": 3},
        [{"agent": "ziwei", "steps": [{"step": 1}, {"step": 2}]}],
    )

    second = SqlAlchemySessionStore(dsn)
    session = second.get_session("r2")
    assert session is not None
    assert session["response"]["value"] == 3
    assert second.get_traces("r2") == [{"agent": "ziwei", "steps": [{"step": 1}, {"step": 2}]}]
    assert [s["request_id"] for s in second.list_sessions()] == ["r2"]


def test_create_store_defaults_to_memory() -> None:
    assert isinstance(create_store(Settings()), InMemorySessionStore)


def test_compute_persists_session_and_traces() -> None:
    app = create_app()
    app.state.session_store = InMemorySessionStore()
    client = TestClient(app)

    response = client.post(
        "/agents/bazi/compute",
        json={"request_id": "p1", "born_at": BORN, "gender": "male"},
    )
    assert response.status_code == 200

    session = app.state.session_store.get_session("p1")
    assert session is not None
    assert session["request"]["request_id"] == "p1"
    traces = app.state.session_store.get_traces("p1")
    assert traces and traces[0]["agent"] == "bazi"
    assert traces[0]["steps"], "reasoning trace must be persisted"

    assert client.get("/sessions/p1").status_code == 200
    listing = client.get("/sessions")
    assert listing.status_code == 200
    assert listing.json()["sessions"][0]["request_id"] == "p1"
    trailer = client.get("/traces/p1")
    assert trailer.status_code == 200
    assert trailer.json()["traces"][0]["agent"] == "bazi"


def test_orchestrate_persists_session() -> None:
    app = create_app()
    app.state.session_store = InMemorySessionStore()
    client = TestClient(app)

    response = client.post(
        "/orchestrate",
        json={
            "request_id": "o1",
            "payload": {"request_id": "o1", "born_at": BORN, "gender": "male"},
            "agents": ["bazi"],
        },
    )
    assert response.status_code == 200
    assert app.state.session_store.get_session("o1") is not None
    traces = app.state.session_store.get_traces("o1")
    assert traces and traces[0]["agent"] == "bazi"


def test_missing_session_and_traces_return_404() -> None:
    app = create_app()
    app.state.session_store = InMemorySessionStore()
    client = TestClient(app)
    assert client.get("/sessions/nope").status_code == 404
    assert client.get("/traces/nope").status_code == 404
