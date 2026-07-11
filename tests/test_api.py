"""FastAPI endpoints via TestClient."""

from fastapi.testclient import TestClient

from openmetaphysics.api.app import app

client = TestClient(app, raise_server_exceptions=False)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert "bazi" in r.json()["agents"]


def test_list_agents():
    r = client.get("/agents")
    names = [a["name"] for a in r.json()["agents"]]
    assert names == ["bazi", "liuyao", "qimen", "ziwei"]


def test_agent_schema():
    r = client.get("/agents/liuyao/schema")
    assert r.status_code == 200
    s = r.json()
    assert "input_schema" in s and "output_schema" in s


def test_compute_bazi():
    r = client.post(
        "/agents/bazi/compute",
        json={"request_id": "a", "born_at": "1985-08-15T10:00:00+08:00", "gender": "male"},
    )
    assert r.status_code == 200
    assert len(r.json()["result"]["pillars"]) == 4


def test_compute_unknown_agent_404():
    r = client.post(
        "/agents/nope/compute", json={"request_id": "a", "born_at": "2024-01-01T00:00:00+00:00"}
    )
    assert r.status_code == 404


def test_compute_naive_datetime_422():
    r = client.post(
        "/agents/bazi/compute", json={"request_id": "a", "born_at": "2024-01-01T00:00:00"}
    )
    assert r.status_code == 422


def test_orchestrate():
    r = client.post(
        "/orchestrate",
        json={
            "request_id": "o",
            "payload": {
                "request_id": "o",
                "born_at": "2024-03-01T06:00:00+00:00",
                "gender": "female",
            },
            "agents": ["bazi", "liuyao"],
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert [o["agent"] for o in data["outputs"]] == ["bazi", "liuyao"]
    assert data["consensus"] is not None
