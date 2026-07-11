"""LangGraph orchestration: validate -> route -> fan_out -> consensus -> respond.

Router policy is deterministic (run-all or run-selected). An LLM may be consulted
for *selection* only (config-gated) and never changes any chart's numbers.
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field, SerializeAsAny

from ..agents.consensus import ConsensusAgent, ConsensusOutput
from ..agents.registry import get_registry
from ..core.schemas import AgentInput, AgentOutput


class OrchestrationRequest(BaseModel):
    request_id: str
    payload: AgentInput
    agents: list[str] | None = None  # None -> all registered agents
    strategy: str = "weighted"
    explain: bool = False


class OrchestrationResponse(BaseModel):
    request_id: str
    outputs: list[SerializeAsAny[AgentOutput]] = Field(default_factory=list)
    consensus: ConsensusOutput | None = None
    explanation: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class _State(TypedDict, total=False):
    request: OrchestrationRequest
    payload: AgentInput
    selected: list[str]
    outputs: list[AgentOutput]
    consensus: ConsensusOutput | None
    explanation: dict[str, str]
    errors: list[str]


def _validate(state: _State) -> dict:
    req = state["request"]
    # Pydantic re-validation enforces the tz-aware datetime etc.
    return {"payload": AgentInput.model_validate(req.payload.model_dump()), "errors": []}


def _route(state: _State) -> dict:
    req = state["request"]
    registry = get_registry()
    selected = req.agents if req.agents else registry.names()
    unknown = [a for a in selected if a not in registry.names()]
    errors = list(state.get("errors", [])) + [f"unknown agent: {a}" for a in unknown]
    selected = [a for a in selected if a in registry.names()]
    return {"selected": selected, "errors": errors}


def _fan_out(state: _State) -> dict:
    registry = get_registry()
    payload = state["payload"]
    outputs: list[AgentOutput] = []
    errors = list(state.get("errors", []))
    for name in state["selected"]:
        try:
            outputs.append(registry.get(name).compute(payload))
        except Exception as exc:  # one agent failing must not break the run
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    return {"outputs": outputs, "errors": errors}


def _consensus(state: _State) -> dict:
    outs = state.get("outputs", [])
    if len(outs) < 2:
        return {"consensus": None}
    req = state["request"]
    consensus = ConsensusAgent().compute(
        ConsensusAgent.input_schema(
            request_id=req.request_id,
            agent_outputs=outs,
            strategy=req.strategy,
        )
    )
    return {"consensus": consensus}


def _explain_one(name: str, output: AgentOutput) -> str:
    from ..inference.explainer import get_explainer

    registry = get_registry()
    cls = type(registry.get(name))
    agent = cls()
    agent.explainer = get_explainer()
    return agent.explain(output)


def _respond(state: _State) -> dict:
    req = state["request"]
    outputs = state.get("outputs", [])
    explanation: dict[str, str] = {}
    if req.explain:
        for o in outputs:
            try:
                explanation[o.agent] = _explain_one(o.agent, o)
            except Exception as exc:
                explanation[o.agent] = f"(explain failed: {type(exc).__name__})"
    return {"explanation": explanation}


def _build_graph():
    g = StateGraph(_State)
    g.add_node("validate", _validate)
    g.add_node("route", _route)
    g.add_node("fan_out", _fan_out)
    g.add_node("consensus", _consensus)
    g.add_node("respond", _respond)
    g.add_edge(START, "validate")
    g.add_edge("validate", "route")
    g.add_edge("route", "fan_out")
    g.add_edge("fan_out", "consensus")
    g.add_edge("consensus", "respond")
    g.add_edge("respond", END)
    return g.compile()


_GRAPH = None


def _graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = _build_graph()
    return _GRAPH


class Orchestrator:
    def run(self, request: OrchestrationRequest) -> OrchestrationResponse:
        result = _graph().invoke({"request": request})
        return OrchestrationResponse(
            request_id=request.request_id,
            outputs=result.get("outputs", []),
            consensus=result.get("consensus"),
            explanation=result.get("explanation", {}),
            errors=result.get("errors", []),
        )


def orchestrate(request: OrchestrationRequest) -> OrchestrationResponse:
    return Orchestrator().run(request)
