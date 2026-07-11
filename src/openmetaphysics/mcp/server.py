"""MCP server stub — exposes agents as tool surface (transport is Phase 9).

This module defines the tool contracts an MCP-compatible client would call.
v1 ships the interface only; no transport is wired.
"""

from __future__ import annotations

from typing import Any

from ..agents.registry import get_registry
from ..orchestration.graph import OrchestrationRequest, orchestrate


def list_tools() -> list[dict[str, Any]]:
    return [
        {"name": "list_agents", "description": "List available agents and engine versions."},
        {
            "name": "agent_schema",
            "description": "Get JSON Schema for an agent's input/output.",
            "args": {"name": "str"},
        },
        {
            "name": "compute",
            "description": "Run one agent deterministically.",
            "args": {"name": "str", "input": "dict"},
        },
        {
            "name": "orchestrate",
            "description": "Run multiple agents + consensus.",
            "args": {"request": "dict"},
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
    raise ValueError(f"unknown tool: {name}")
