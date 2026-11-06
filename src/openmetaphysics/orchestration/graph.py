"""LangGraph orchestration: validate -> route -> fan_out -> consensus -> respond.

Router policy is deterministic (run-all or run-selected). An LLM may be consulted
for *selection* only (config-gated) and never changes any chart's numbers.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializeAsAny,
    ValidationError,
    field_validator,
)

from ..agents.consensus import ConsensusAgent, ConsensusOutput
from ..agents.registry import get_registry
from ..core.schemas import AgentInput, AgentOutput


class OrchestrationPayload(AgentInput):
    """Common envelope that may also carry domain fields for per-agent dispatch.

    The shared ``payload`` is typed as ``AgentInput`` by the single-agent
    endpoints. For orchestration the domain fields (``casts``/``seed`` for
    Liuyao, ``lunar_month``/``lunar_day`` for Ziwei, ``dayun_count`` for Bazi,
    ...) are allowed on the payload and copied only to the agents whose input
    schema declares them, so a request can stay "one envelope + selected
    agents". Per-agent ``agent_params`` take precedence over these fields.
    """

    model_config = ConfigDict(extra="allow")


class OrchestrationRequest(BaseModel):
    """A batch request over the shared ``payload`` envelope.

    Domain-specific fields (``casts``/``seed`` for Liuyao, ``lunar_month`` /
    ``lunar_day`` for Ziwei, ``dayun_count`` for Bazi, ...) are not part of the
    common ``AgentInput`` contract. They can be supplied in either of two ways:

    * directly on ``payload`` -- dispatched to every selected agent whose input
      schema declares the field;
    * per agent in ``agent_params``, which is merged over ``payload`` for that
      agent only and wins on conflicts::

          {"request_id": "r", "payload": {...},
           "agents": ["bazi", "liuyao"],
           "agent_params": {"bazi": {"dayun_count": 6},
                            "liuyao": {"casts": [7, 7, 8, 8, 7, 8]}}}

    Both are optional: requests without them keep the previous behaviour (the
    common envelope only).
    """

    request_id: str
    payload: OrchestrationPayload
    agents: list[str] | None = None  # None -> all registered agents
    agent_params: dict[str, dict[str, Any]] = Field(default_factory=dict)
    strategy: str = "weighted"
    explain: bool = False

    @field_validator("payload", mode="before")
    @classmethod
    def _accept_plain_envelope(cls, value: Any) -> Any:
        """Accept a plain ``AgentInput`` from existing in-process callers."""
        if isinstance(value, AgentInput):
            return value.model_dump()
        return value


class OrchestrationResponse(BaseModel):
    request_id: str
    outputs: list[SerializeAsAny[AgentOutput]] = Field(default_factory=list)
    consensus: ConsensusOutput | None = None
    explanation: dict[str, str] = Field(default_factory=dict)
    explanation_detail: dict[str, dict[str, Any]] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class _State(TypedDict, total=False):
    request: OrchestrationRequest
    payload: OrchestrationPayload
    selected: list[str]
    outputs: list[AgentOutput]
    consensus: ConsensusOutput | None
    explanation: dict[str, str]
    explanation_detail: dict[str, dict[str, Any]]
    errors: list[str]


_COMMON_FIELDS = frozenset(AgentInput.model_fields)


def _split_payload(payload: OrchestrationPayload) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split the payload into the common envelope and domain-specific extras."""
    data = payload.model_dump()
    common = {key: value for key, value in data.items() if key in _COMMON_FIELDS}
    extras = {key: value for key, value in data.items() if key not in _COMMON_FIELDS}
    return common, extras


def _validate(state: _State) -> dict:
    req = state["request"]
    # Pydantic re-validation enforces the tz-aware datetime etc. while keeping
    # the domain-specific payload extras usable by the fan-out step.
    return {"payload": OrchestrationPayload.model_validate(req.payload.model_dump()), "errors": []}


def _route(state: _State) -> dict:
    req = state["request"]
    registry = get_registry()
    selected = req.agents if req.agents else registry.names()
    unknown = [a for a in selected if a not in registry.names()]
    errors = list(state.get("errors", [])) + [f"unknown agent: {a}" for a in unknown]
    selected = [a for a in selected if a in registry.names()]
    errors += [
        f"unknown agent in agent_params: {name}"
        for name in sorted(req.agent_params)
        if name not in registry.names()
    ]
    return {"selected": selected, "errors": errors}


def _fan_out(state: _State) -> dict:
    registry = get_registry()
    payload = state["payload"]
    params = state["request"].agent_params
    selected = state["selected"]
    common, extras = _split_payload(payload)
    accepted_fields = {
        field for name in selected for field in registry.get(name).input_schema.model_fields
    }
    errors = list(state.get("errors", []))
    unmatched = sorted(set(extras) - accepted_fields)
    if unmatched:
        errors.append("payload field(s) not accepted by selected agents: " + ", ".join(unmatched))
    outputs: list[AgentOutput] = []
    for name in selected:
        agent = registry.get(name)
        accepted = set(agent.input_schema.model_fields)
        # Domain fields are merged over the common envelope and validated with
        # the agent's own schema, so a bad field is reported per agent instead
        # of failing the whole batch (matching the batch error semantics).
        merged = {
            **common,
            **{key: value for key, value in extras.items() if key in accepted},
            **params.get(name, {}),
        }
        try:
            agent_input = agent.input_schema.model_validate(merged)
        except ValidationError as exc:
            details = "; ".join(
                f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
                for error in exc.errors()
            )
            errors.append(f"{name}: invalid agent_params: {details}")
            continue
        except Exception as exc:  # defensive: never let one agent break the run
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
            continue
        try:
            outputs.append(agent.compute(agent_input))
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


def _explain_detail(name: str, output: AgentOutput) -> dict[str, Any]:
    """Run the explain chain for one agent and return prose plus provenance."""
    from ..inference.explainer import get_explainer_for

    result = get_explainer_for(name).explain(output)
    return {
        "explanation": result["explanation"],
        "provider": result["provider"],
        "degraded": result["degraded"],
        "knowledge": [
            {"id": c["id"], "source": c["source"], "text": c["text"]}
            for c in result.get("knowledge", [])
        ],
        # the fact layer the explanation was produced from (E2E verifiability)
        "evidence": result["evidence"],
        # provider failure record (kind/type/message), None when the provider ran
        "error": result.get("error"),
    }


def _explain_one(name: str, output: AgentOutput) -> str:
    return str(_explain_detail(name, output)["explanation"])


def _respond(state: _State) -> dict:
    req = state["request"]
    outputs = state.get("outputs", [])
    explanation: dict[str, str] = {}
    detail: dict[str, dict[str, Any]] = {}
    if req.explain:
        for o in outputs:
            try:
                info = _explain_detail(o.agent, o)
            except Exception as exc:
                explanation[o.agent] = f"(explain failed: {type(exc).__name__})"
                continue
            explanation[o.agent] = str(info["explanation"])
            detail[o.agent] = info
    return {"explanation": explanation, "explanation_detail": detail}


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
            explanation_detail=result.get("explanation_detail", {}),
            errors=result.get("errors", []),
        )


def orchestrate(request: OrchestrationRequest) -> OrchestrationResponse:
    return Orchestrator().run(request)
