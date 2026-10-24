"""MCP JSON-RPC over HTTP (FastAPI transport)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from openmetaphysics.api.app import create_app

client = TestClient(create_app())


def test_http_initialize() -> None:
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["serverInfo"]["name"] == "openmetaphysics"


def test_http_tools_list() -> None:
    response = client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert response.status_code == 200
    names = [tool["name"] for tool in response.json()["result"]["tools"]]
    assert "compute" in names
    assert "knowledge_search" in names


def test_http_notification_returns_202() -> None:
    response = client.post(
        "/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"}
    )
    assert response.status_code == 202


def test_http_invalid_body_400() -> None:
    response = client.post("/mcp", json=["not", "an", "object"])
    assert response.status_code == 400
