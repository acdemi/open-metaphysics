"""MCP stdio server — exposes the deterministic agents as MCP tools.

Transport is a dependency-free JSON-RPC 2.0 server over newline-delimited
stdin/stdout, which is the MCP stdio transport framing. The official ``mcp``
SDK is intentionally not required so the server stays offline-testable; the
tool surface is the same one clients would consume.

Run: ``python -m openmetaphysics.mcp`` or ``openmetaphysics-mcp``.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from ..agents.registry import get_registry
from ..consensus import ConsensusEngine, ConsensusInput
from ..core.schemas import agent_output_from_envelope
from ..inference.explainer import get_explainer_for
from ..orchestration.graph import OrchestrationRequest, orchestrate

SERVER_NAME = "openmetaphysics"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"

_EMPTY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}


def list_tools() -> list[dict[str, Any]]:
    """MCP tool definitions (name/description/inputSchema)."""
    return [
        {
            "name": "list_agents",
            "description": "List available agents and engine versions.",
            "inputSchema": _EMPTY_SCHEMA,
        },
        {
            "name": "agent_schema",
            "description": "Get JSON Schema for an agent's input/output.",
            "inputSchema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
                "additionalProperties": False,
            },
        },
        {
            "name": "compute",
            "description": "Run one agent deterministically (no LLM).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "input": {"type": "object"},
                },
                "required": ["name", "input"],
                "additionalProperties": False,
            },
        },
        {
            "name": "orchestrate",
            "description": "Run multiple agents + consensus.",
            "inputSchema": {
                "type": "object",
                "properties": {"request": {"type": "object"}},
                "required": ["request"],
                "additionalProperties": False,
            },
        },
        {
            "name": "explain",
            "description": "Explain an already-computed agent output (LLM optional).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string"},
                    "output": {"type": "object"},
                    "style": {"type": "string"},
                    "k": {"type": "integer"},
                },
                "required": ["agent", "output"],
                "additionalProperties": False,
            },
        },
        {
            "name": "consensus_evidence",
            "description": "Evidence[] + config -> ConsensusReport (frozen contract).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "evidence": {"type": "array"},
                    "config": {"type": "object"},
                },
                "required": ["evidence"],
                "additionalProperties": False,
            },
        },
        {
            "name": "knowledge_search",
            "description": "Search the frozen knowledge corpora (offline retrieval).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "k": {"type": "integer"},
                    "include_evidence": {"type": "boolean"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
        {
            "name": "knowledge_stats",
            "description": "List frozen corpus metadata (status/version/counts).",
            "inputSchema": _EMPTY_SCHEMA,
        },
    ]


def call_tool(name: str, args: dict[str, Any]) -> Any:
    reg = get_registry()
    if name == "list_agents":
        return [{"name": a.name, "engine_version": a.engine_version} for a in reg.all()]
    if name == "agent_schema":
        return reg.get(args["name"]).schema()
    if name == "compute":
        agent = reg.get(args["name"])
        payload = agent.input_schema.model_validate(args["input"])
        return agent.compute(payload).model_dump(mode="json")
    if name == "orchestrate":
        req = OrchestrationRequest.model_validate(args["request"])
        return orchestrate(req).model_dump(mode="json")
    if name == "explain":
        output = agent_output_from_envelope(args["output"])
        result = get_explainer_for(args["agent"]).explain(
            output, style=args.get("style", "concise"), k=int(args.get("k", 3))
        )
        return {
            "explanation": result["explanation"],
            "provider": result["provider"],
            "degraded": result["degraded"],
            "knowledge": [{"id": c["id"], "source": c["source"]} for c in result.get("knowledge", [])],
            "evidence": result["evidence"],
            "error": result.get("error"),
        }
    if name == "consensus_evidence":
        payload = ConsensusInput.model_validate(
            {"evidence": args.get("evidence", []), "config": args.get("config", {})}
        )
        return ConsensusEngine().build(payload).model_dump(mode="json")
    if name == "knowledge_search":
        from ..rag.retriever import search_knowledge

        chunks = search_knowledge(
            str(args["query"]),
            k=int(args.get("k", 5)),
            include_evidence=bool(args.get("include_evidence", False)),
        )
        return [
            {"id": c.id, "text": c.text, "source": c.source, "tags": c.tags} for c in chunks
        ]
    if name == "knowledge_stats":
        from ..rag.corpus import corpus_stats

        return corpus_stats()
    raise ValueError(f"unknown tool: {name}")


def _error_response(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def _tool_result(value: Any) -> dict[str, Any]:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return {"content": [{"type": "text", "text": text}]}


def handle_message(message: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC message; returns None for notifications."""
    message_id = message.get("id")
    if message.get("jsonrpc") != "2.0" or "method" not in message:
        return _error_response(message_id, -32600, "invalid request")
    if "id" not in message:  # notification (e.g. notifications/initialized)
        return None

    method = message["method"]
    if method == "initialize":
        result: dict[str, Any] = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        }
    elif method == "tools/list":
        result = {"tools": list_tools()}
    elif method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        if not isinstance(name, str):
            return _error_response(message_id, -32602, "invalid params: name required")
        try:
            value = call_tool(name, args)
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "content": [{"type": "text", "text": str(exc)}],
                    "isError": True,
                },
            }
        result = _tool_result(value)
    elif method == "ping":
        result = {}
    else:
        return _error_response(message_id, -32601, f"method not found: {method}")

    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def main() -> None:
    """Read newline-delimited JSON-RPC from stdin, write responses to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            response = _error_response(None, -32700, "parse error")
        else:
            response = handle_message(message)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
