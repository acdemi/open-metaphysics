"""MCP JSON-RPC parity between the stdio and HTTP transports (Prompt 3A).

Both transports call the same ``handle_message``. This module drives the *real*
paths — a spawned ``python -m openmetaphysics.mcp`` subprocess for stdio and a
FastAPI ``TestClient`` for ``POST /mcp`` — and compares the JSON-RPC documents
produced for the same requests.

Transport-level differences (HTTP status codes, newline framing, HTTP 400 for a
non-JSON body vs JSON-RPC ``-32700``) are asserted explicitly and are *not*
treated as semantic mismatches.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from openmetaphysics.api.app import create_app

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"

BORN = "1990-06-15T08:30:00+09:00"
VOLATILE_KEYS = {"computed_at"}


def _canonical(value: Any) -> Any:
    """Normalise transport-neutral JSON-RPC documents.

    ``tools/call`` results carry a JSON string in ``content[*].text``; parse it so
    nested values (notably the volatile ``computed_at`` timestamp) compare
    structurally instead of as raw text.
    """
    if isinstance(value, dict):
        canonical: dict[str, Any] = {}
        for key, item in value.items():
            if key in VOLATILE_KEYS:
                canonical[key] = "<volatile>"
            elif key == "text" and isinstance(item, str):
                try:
                    canonical[key] = _canonical(json.loads(item))
                except json.JSONDecodeError:
                    canonical[key] = item
            else:
                canonical[key] = _canonical(item)
        return canonical
    if isinstance(value, list):
        return [_canonical(item) for item in value]
    return value


def _stdio_roundtrip(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines = [json.dumps(message, ensure_ascii=False) for message in messages]
    env = {**os.environ, "PYTHONPATH": str(SRC), "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(
        [sys.executable, "-m", "openmetaphysics.mcp"],
        input="\n".join(lines) + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        env=env,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    return [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]


def _http_roundtrip(messages: list[dict[str, Any]]) -> list[tuple[int, Any]]:
    client = TestClient(create_app())
    out: list[tuple[int, Any]] = []
    for message in messages:
        response = client.post("/mcp", json=message)
        body = response.json() if response.content else None
        out.append((response.status_code, body))
    return out


def _requests() -> list[dict[str, Any]]:
    return [
        {"jsonrpc": "2.0", "id": 101, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 102, "method": "ping"},
        {"jsonrpc": "2.0", "id": 103, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 104,
            "method": "tools/call",
            "params": {"name": "list_agents", "arguments": {}},
        },
        {
            "jsonrpc": "2.0",
            "id": 105,
            "method": "tools/call",
            "params": {
                "name": "compute",
                "arguments": {
                    "name": "bazi",
                    "input": {"request_id": "mcp-parity-1", "born_at": BORN, "gender": "male"},
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 106,
            "method": "tools/call",
            "params": {"name": "nope", "arguments": {}},
        },
        {"jsonrpc": "2.0", "id": 107, "method": "does/not/exist"},
        {"jsonrpc": "2.0", "id": 108, "method": "tools/call", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 109,
            "method": "tools/call",
            "params": {"name": "agent_schema", "arguments": {}},
        },
        {"jsonrpc": "2.0", "id": 110, "method": "ping"},
        {
            "jsonrpc": "2.0",
            "id": 111,
            "method": "tools/call",
            "params": {"name": "compute", "arguments": {"name": "bazi", "input": {}}},
        },
    ]


def _invalid_request() -> dict[str, Any]:
    """An otherwise valid call missing ``jsonrpc`` (JSON-RPC -32600)."""
    return {"id": 110, "method": "ping"}


def test_jsonrpc_documents_match_across_transports() -> None:
    requests = _requests()
    requests.append(_invalid_request())

    stdio = _stdio_roundtrip(requests)
    http = _http_roundtrip(requests)

    assert len(stdio) == len(requests), "every request with an id must get one response"
    assert len(http) == len(requests)
    for index, (status, body) in enumerate(http):
        assert status == 200, f"case {index} must be a JSON-RPC 200, got {status}"
        assert _canonical(body) == _canonical(stdio[index]), (
            f"JSON-RPC semantic mismatch for case {index}: "
            f"http={json.dumps(body, ensure_ascii=False)[:200]} "
            f"stdio={json.dumps(stdio[index], ensure_ascii=False)[:200]}"
        )


def test_errors_have_identical_codes_and_messages() -> None:
    requests = [
        {"jsonrpc": "2.0", "id": 201, "method": "does/not/exist"},
        {"jsonrpc": "2.0", "id": 202, "method": "tools/call", "params": {}},
        {"jsonrpc": "2.0", "id": 203, "method": "tools/call",
         "params": {"name": "nope", "arguments": {}}},
    ]
    stdio = _stdio_roundtrip(requests)
    (_, unknown_method), (_, missing_name), (_, unknown_tool) = _http_roundtrip(requests)

    assert unknown_method["error"] == stdio[0]["error"]
    assert unknown_method["error"]["code"] == -32601
    assert missing_name["error"] == stdio[1]["error"]
    assert missing_name["error"]["code"] == -32602
    assert unknown_tool["result"] == stdio[2]["result"]
    assert unknown_tool["result"]["isError"] is True
    assert "unknown tool" in unknown_tool["result"]["content"][0]["text"]


def test_transport_specific_behaviour_is_kept_separate() -> None:
    # Invalid JSON body: HTTP rejects at the HTTP layer (400, flat error body as
    # implemented today), stdio emits JSON-RPC -32700. These are transport
    # differences, not JSON-RPC semantic mismatches.
    client = TestClient(create_app())
    response = client.post(
        "/mcp", content=b"not-json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400
    body = response.json()
    assert body["kind"] == "invalid_request"
    assert body["message"] == "body must be a JSON-RPC object"

    proc = subprocess.run(
        [sys.executable, "-m", "openmetaphysics.mcp"],
        input="not-json\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONIOENCODING": "utf-8"},
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert len(lines) == 1
    parse_error = json.loads(lines[0])
    assert parse_error["jsonrpc"] == "2.0"
    assert parse_error["id"] is None
    assert parse_error["error"]["code"] == -32700


def test_notification_has_no_jsonrpc_response_in_either_transport() -> None:
    notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    client = TestClient(create_app())
    response = client.post("/mcp", json=notification)
    assert response.status_code == 202
    assert response.json() is None, "HTTP transport acknowledges notifications with an empty JSON body"

    proc = subprocess.run(
        [sys.executable, "-m", "openmetaphysics.mcp"],
        input=json.dumps(notification) + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONIOENCODING": "utf-8"},
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    assert [line for line in proc.stdout.splitlines() if line.strip()] == []
