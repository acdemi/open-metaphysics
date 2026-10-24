"""MCP stdio server tests (offline, no external MCP SDK required)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from openmetaphysics.mcp.server import (
    PROTOCOL_VERSION,
    SERVER_NAME,
    handle_message,
    list_tools,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"


def test_initialize_declares_tools_capability() -> None:
    response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert response is not None
    result = response["result"]
    assert result["protocolVersion"] == PROTOCOL_VERSION
    assert result["capabilities"]["tools"] == {}
    assert result["serverInfo"]["name"] == SERVER_NAME


def test_tools_list_exposes_six_tools() -> None:
    response = handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert response is not None
    names = [tool["name"] for tool in response["result"]["tools"]]
    assert names == [
        "list_agents",
        "agent_schema",
        "compute",
        "orchestrate",
        "explain",
        "consensus_evidence",
    ]
    assert all("inputSchema" in tool for tool in list_tools())


def test_tools_call_returns_content_text() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "list_agents", "arguments": {}},
        }
    )
    assert response is not None
    content = response["result"]["content"][0]
    assert content["type"] == "text"
    agents = json.loads(content["text"])
    assert any(a["name"] == "bazi" for a in agents)


def test_tools_call_agent_schema() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "agent_schema", "arguments": {"name": "liuyao"}},
        }
    )
    assert response is not None
    schema = json.loads(response["result"]["content"][0]["text"])
    assert "input_schema" in schema and "output_schema" in schema


def test_tools_call_unknown_tool_is_error() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "nope", "arguments": {}},
        }
    )
    assert response is not None
    assert response["result"]["isError"] is True
    assert "unknown tool" in response["result"]["content"][0]["text"]


def test_tools_call_requires_name() -> None:
    response = handle_message({"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {}})
    assert response is not None
    assert response["error"]["code"] == -32602


def test_notification_has_no_response() -> None:
    assert handle_message({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None


def test_invalid_request_and_unknown_method() -> None:
    bad = handle_message({"id": 7, "method": "ping"})
    assert bad is not None and bad["error"]["code"] == -32600
    unknown = handle_message({"jsonrpc": "2.0", "id": 8, "method": "does/not/exist"})
    assert unknown is not None and unknown["error"]["code"] == -32601


def test_ping() -> None:
    response = handle_message({"jsonrpc": "2.0", "id": 9, "method": "ping"})
    assert response is not None and response["result"] == {}


def test_tools_call_consensus_evidence() -> None:
    evidence = {
        "evidence_id": "ev:mcp:1",
        "domain": "career",
        "conclusion": "晋升机会",
        "confidence": 0.8,
        "system": "bazi",
        "items": [
            {
                "evidence_id": "evi:1",
                "source_type": "rule",
                "source_id": "rule:mcp",
                "system": "bazi",
                "domain": "career",
                "confidence": 0.8,
                "conclusion": "晋升机会",
                "weight": 1.0,
                "trace": [],
                "metadata": {},
                "timestamp": None,
                "version": "1.0.0",
            }
        ],
    }
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "consensus_evidence",
                "arguments": {"evidence": [evidence], "config": {"strategy": "retain_all"}},
            },
        }
    )
    assert response is not None
    report = json.loads(response["result"]["content"][0]["text"])
    assert report["report_id"].startswith("cr:")
    assert report["conclusions"][0]["domain"] == "career"


def test_tools_call_explain() -> None:
    computed = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "compute",
                "arguments": {
                    "name": "bazi",
                    "input": {"request_id": "m1", "born_at": "1985-08-15T10:00:00+08:00", "gender": "male"},
                },
            },
        }
    )
    assert computed is not None
    output = json.loads(computed["result"]["content"][0]["text"])

    explained = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {"name": "explain", "arguments": {"agent": "bazi", "output": output}},
        }
    )
    assert explained is not None
    payload = json.loads(explained["result"]["content"][0]["text"])
    assert "explanation" in payload
    assert "degraded" in payload


def test_stdio_transport_end_to_end() -> None:
    lines = [
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
    ]
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    proc = subprocess.run(
        [sys.executable, "-m", "openmetaphysics.mcp"],
        input="\n".join(lines) + "\n",
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    responses = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    assert len(responses) == 2, "notification must not produce a response"
    assert responses[0]["result"]["serverInfo"]["name"] == SERVER_NAME
    assert [t["name"] for t in responses[1]["result"]["tools"]] == [
        "list_agents",
        "agent_schema",
        "compute",
        "orchestrate",
        "explain",
        "consensus_evidence",
    ]
