"""Root route and optional CORS configuration."""

from __future__ import annotations

from fastapi.testclient import TestClient

from openmetaphysics.api.app import create_app
from openmetaphysics.core.config import reset_settings


def test_root_returns_service_info() -> None:
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "OpenMetaphysics"
    assert body["docs"] == "/docs"


def test_cors_disabled_by_default() -> None:
    client = TestClient(create_app())
    response = client.get("/health", headers={"Origin": "http://example.com"})
    assert "access-control-allow-origin" not in response.headers


def test_cors_enabled_with_env(monkeypatch) -> None:
    monkeypatch.setenv("OM_CORS_ORIGINS", "http://a.example, http://b.example")
    reset_settings()
    try:
        client = TestClient(create_app())
        response = client.get("/health", headers={"Origin": "http://a.example"})
        assert response.headers.get("access-control-allow-origin") == "http://a.example"
    finally:
        reset_settings()
