"""Offline CLI: agents / compute / explain without running a server.

Examples::

    openmetaphysics-cli agents
    openmetaphysics-cli compute bazi --input '{"request_id":"c1","born_at":"1985-08-15T10:00:00+08:00","gender":"male"}'
    openmetaphysics-cli compute bazi --input '{...}' --explain
    openmetaphysics-cli explain bazi --output '{...}'
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .agents.registry import get_registry
from .consensus import ConsensusEngine, ConsensusInput
from .core.schemas import AgentOutput, agent_output_from_envelope
from .inference.explainer import get_explainer_for


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _load(text: str) -> Any:
    return json.loads(text)


def _explain_payload(agent: str, output: AgentOutput, *, k: int = 3) -> dict[str, Any]:
    result = get_explainer_for(agent).explain(output, style="concise", k=k)
    return {
        "explanation": result["explanation"],
        "provider": result["provider"],
        "degraded": result["degraded"],
        "knowledge": [{"id": c["id"], "source": c["source"]} for c in result.get("knowledge", [])],
        "evidence": result["evidence"],
        "error": result.get("error"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="openmetaphysics-cli")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("agents", help="list registered agents")

    compute = sub.add_parser("compute", help="run one agent deterministically")
    compute.add_argument("agent")
    compute.add_argument("--input", required=True, help="agent input JSON object")
    compute.add_argument("--explain", action="store_true", help="attach explain chain")
    compute.add_argument("--k", type=int, default=3, help="knowledge chunks for explain")

    explain = sub.add_parser("explain", help="explain an already-computed output")
    explain.add_argument("agent")
    explain.add_argument("--output", required=True, help="agent output JSON object")
    explain.add_argument("--k", type=int, default=3)

    knowledge = sub.add_parser("knowledge", help="search the frozen knowledge corpora")
    knowledge.add_argument("--query", required=True)
    knowledge.add_argument("--k", type=int, default=5)
    knowledge.add_argument(
        "--include-evidence",
        action="store_true",
        help="also search relation/reference chunks",
    )

    consensus = sub.add_parser("consensus", help="Evidence[] + config -> ConsensusReport")
    consensus.add_argument("--input", required=True, help="JSON with evidence[] and config")

    args = parser.parse_args(argv)
    registry = get_registry()

    if args.command == "agents":
        _print([{"name": a.name, "engine_version": a.engine_version} for a in registry.all()])
        return 0

    if args.command == "compute":
        try:
            agent = registry.get(args.agent)
        except KeyError:
            print(f"unknown agent: {args.agent}", file=sys.stderr)
            return 2
        try:
            payload = agent.input_schema.model_validate(_load(args.input))
            output = agent.compute(payload)
        except Exception as exc:
            print(f"invalid input: {exc}", file=sys.stderr)
            return 2
        data = output.model_dump(mode="json")
        if args.explain:
            data["explain"] = _explain_payload(args.agent, output, k=args.k)
        _print(data)
        return 0

    if args.command == "explain":
        try:
            output = agent_output_from_envelope(_load(args.output))
        except Exception as exc:
            print(f"invalid output: {exc}", file=sys.stderr)
            return 2
        _print(_explain_payload(args.agent, output, k=args.k))
        return 0

    if args.command == "knowledge":
        from .rag.retriever import search_knowledge

        chunks = search_knowledge(
            args.query, k=args.k, include_evidence=args.include_evidence
        )
        _print(
            [
                {"id": c.id, "text": c.text, "source": c.source, "tags": c.tags}
                for c in chunks
            ]
        )
        return 0

    if args.command == "consensus":
        try:
            payload = ConsensusInput.model_validate(_load(args.input))
        except Exception as exc:
            print(f"invalid input: {exc}", file=sys.stderr)
            return 2
        _print(ConsensusEngine().build(payload).model_dump(mode="json"))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
