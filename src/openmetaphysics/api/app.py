"""FastAPI application exposing agents, orchestration and the explain pipeline.

Route naming is intentionally kept as-is (``/agents/{name}/...``) rather than
restructured into per-domain REST paths.

Runtime composition exposed here:

    HTTP request
      -> input validation
      -> orchestration (or a single domain agent)
      -> deterministic calculation
      -> evidence (already-computed facts)
      -> knowledge retrieval (Explain chain)
      -> explanation
      -> HTTP response

Public error model (Productization P1): every failure carries one machine
readable ``error`` object with a stable ``kind`` -- ``invalid_request`` (422),
``unknown_agent`` (404) or ``calculation_failed`` / ``internal_error`` (500).
FastAPI's ``detail`` is preserved alongside it for compatibility.

An explanation or provider failure is **not** an HTTP error: the deterministic
result is still returned with HTTP 200 and the failure is recorded in the
``explain.error`` block, so provider errors can never masquerade as calculation
errors.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from ..agents.registry import get_registry
from ..consensus import ConsensusEngine, ConsensusInput, ConsensusReport
from ..core.config import get_settings
from ..core.schemas import AgentOutput
from ..inference.explainer import get_explainer_for
from ..orchestration.graph import OrchestrationRequest, orchestrate
from ..persistence import SessionStore, create_store


class ExplainRequest(BaseModel):
    output: dict[str, Any]


class KnowledgeSearchRequest(BaseModel):
    query: str
    k: int = 5


# -- public error model ----------------------------------------------------


def _error_body(kind: str, message: str, **extra: Any) -> dict[str, Any]:
    """The stable machine-readable error object (``kind`` is the discriminator)."""
    return {"kind": kind, "message": message, **extra}


def _error(status: int, kind: str, message: str, **extra: Any) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": _error_body(kind, message, **extra)})


def _unknown_agent(name: str) -> JSONResponse:
    message = f"unknown agent: {name}"
    return JSONResponse(
        status_code=404,
        content={"detail": message, "error": _error_body("unknown_agent", message, agent=name)},
    )


def _invalid_request(exc: ValidationError) -> JSONResponse:
    """422 for a body or query that failed the published schema.

    Used both for handler-level validation and for FastAPI's own request
    validation, so a validation failure has one shape wherever it comes from.
    """
    errors = jsonable_encoder(exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "detail": errors,
            "error": _error_body(
                "invalid_request",
                "request validation failed",
                fields=[list(e.get("loc", [])) for e in exc.errors()],
            ),
        },
    )


def _explain_payload(
    agent_name: str,
    output: AgentOutput,
    *,
    style: str = "concise",
    k: int = 3,
) -> dict[str, Any]:
    """Run the explain chain for an already-computed output.

    An explain failure must never hide or alter the deterministic result, so
    this returns a structured ``error`` note instead of raising.
    """
    try:
        result = get_explainer_for(agent_name).explain(output, style=style, k=k)
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "explanation": "",
            "provider": None,
            "degraded": True,
            "knowledge": [],
            "evidence": {},
            "error": _error_body("explain_failed", str(exc), type=type(exc).__name__),
        }
    return {
        "explanation": result["explanation"],
        "provider": result["provider"],
        "degraded": result["degraded"],
        "knowledge": [{"id": c["id"], "source": c["source"]} for c in result.get("knowledge", [])],
        # the fact layer the explanation was produced from, so a client can
        # verify that the explanation did not rewrite the deterministic result
        "evidence": result["evidence"],
        # provider failure record (kind/type/message), None when the provider ran
        "error": result.get("error"),
    }


def _persist_session(
    store: SessionStore | None,
    request_id: str,
    request: dict[str, Any],
    response: dict[str, Any],
    outputs: list[Any],
) -> None:
    """Best-effort persistence; a store failure never affects the response."""
    if store is None:
        return
    traces = [
        {
            "agent": out.agent,
            "steps": [step.model_dump(mode="json") for step in out.reasoning_trace],
        }
        for out in outputs
    ]
    try:
        store.save_session(request_id, request, response, traces)
    except Exception:
        return


def create_app() -> FastAPI:
    app = FastAPI(
        title="OpenMetaphysics",
        version="0.1.0",
        description="Local-first deterministic multi-agent metaphysics framework.",
    )
    app.state.session_store = create_store()

    origins = [o.strip() for o in (get_settings().cors_origins or "").split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/")
    def root() -> dict[str, Any]:
        return {
            "name": "OpenMetaphysics",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "agents": get_registry().names()}

    @app.get("/agents")
    def list_agents() -> dict[str, Any]:
        reg = get_registry()
        return {"agents": [{"name": a.name, "engine_version": a.engine_version} for a in reg.all()]}

    @app.get("/agents/{name}/schema")
    def agent_schema(name: str) -> Any:
        try:
            return get_registry().get(name).schema()
        except KeyError:
            return _unknown_agent(name)

    @app.post("/agents/{name}/compute")
    def agent_compute(
        name: str,
        body: dict[str, Any],
        http_request: Request,
        explain: bool = False,
        style: str = "concise",
        k: int = 3,
    ) -> Any:
        """Calculate (and optionally explain) with one domain agent.

        ``?explain=true`` adds the explanation, with its knowledge provenance,
        under an ``explain`` key; the calculation result itself is unchanged.
        """
        reg = get_registry()
        try:
            agent = reg.get(name)
        except KeyError:
            return _unknown_agent(name)

        try:
            payload = agent.input_schema.model_validate(body)
        except ValidationError as exc:
            return _invalid_request(exc)

        try:
            output = agent.compute(payload)
        except Exception as exc:
            return _error(
                500,
                "calculation_failed",
                str(exc),
                type=type(exc).__name__,
                agent=name,
            )

        data: dict[str, Any] = output.model_dump(mode="json")
        _persist_session(http_request.app.state.session_store, output.request_id, body, data, [output])
        if explain:
            data["explain"] = _explain_payload(name, output, style=style, k=k)
        return data

    @app.post("/agents/{name}/explain")
    def agent_explain(name: str, req: ExplainRequest, style: str = "concise", k: int = 3) -> Any:
        """Explain an already-computed output (no recalculation)."""
        try:
            get_registry().get(name)
        except KeyError:
            return _unknown_agent(name)

        try:
            output = AgentOutput.model_validate(req.output)
        except ValidationError as exc:
            return _invalid_request(exc)

        payload = _explain_payload(name, output, style=style, k=k)
        return {"agent": name, **payload}

    @app.post("/knowledge/search")
    def knowledge_search(req: KnowledgeSearchRequest) -> dict[str, Any]:
        """Deterministic frozen-corpus retrieval (offline; optional Qdrant)."""
        from ..rag.retriever import get_retriever

        chunks = get_retriever().retrieve(req.query, k=req.k)
        return {
            "query": req.query,
            "chunks": [
                {"id": c.id, "text": c.text, "source": c.source, "tags": c.tags} for c in chunks
            ],
        }

    @app.get("/consensus/schema")
    def consensus_schema() -> dict[str, Any]:
        return {
            "input_schema": ConsensusInput.model_json_schema(),
            "output_schema": ConsensusReport.model_json_schema(),
        }

    @app.post("/consensus/evidence")
    def consensus_evidence(req: ConsensusInput) -> Any:
        """Evidence[] + config -> ConsensusReport (frozen Reference contract)."""
        try:
            report = ConsensusEngine().build(req)
        except Exception as exc:
            return _error(500, "consensus_failed", str(exc), type=type(exc).__name__)
        return report.model_dump(mode="json")

    @app.post("/orchestrate")
    def orchestrate_endpoint(req: OrchestrationRequest, http_request: Request) -> Any:
        # Request-level check: if the caller explicitly named agents and none of
        # them exist there is nothing to orchestrate -> 404, matching the
        # single-agent operations. Partially-unknown requests keep the batch
        # semantics (200 with per-agent entries in ``errors``).
        if req.agents:
            known = set(get_registry().names())
            unknown = sorted(a for a in req.agents if a not in known)
            if unknown and len(unknown) == len(req.agents):
                message = "unknown agent(s): " + ", ".join(unknown)
                return JSONResponse(
                    status_code=404,
                    content={
                        "detail": message,
                        "error": _error_body("unknown_agent", message, agents=unknown),
                    },
                )

        try:
            resp = orchestrate(req)
        except ValidationError as exc:
            return _invalid_request(exc)
        payload = resp.model_dump(mode="json")
        _persist_session(
            http_request.app.state.session_store,
            req.request_id,
            req.model_dump(mode="json"),
            payload,
            resp.outputs,
        )
        return payload

    @app.get("/sessions")
    def list_sessions(http_request: Request) -> dict[str, Any]:
        return {"sessions": http_request.app.state.session_store.list_sessions()}

    @app.get("/sessions/{request_id}")
    def get_session(request_id: str, http_request: Request) -> Any:
        session = http_request.app.state.session_store.get_session(request_id)
        if session is None:
            message = f"session not found: {request_id}"
            return JSONResponse(
                status_code=404,
                content={"detail": message, "error": _error_body("not_found", message)},
            )
        return session

    @app.get("/traces/{request_id}")
    def get_traces(request_id: str, http_request: Request) -> Any:
        traces = http_request.app.state.session_store.get_traces(request_id)
        if not traces:
            message = f"no traces: {request_id}"
            return JSONResponse(
                status_code=404,
                content={"detail": message, "error": _error_body("not_found", message)},
            )
        return {"request_id": request_id, "traces": traces}

    @app.exception_handler(RequestValidationError)
    def request_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        """FastAPI-level (body / query / path) validation shares the 422 shape."""
        return _invalid_request(exc)  # type: ignore[arg-type]

    @app.exception_handler(Exception)
    def unhandled(_: Any, exc: Exception) -> JSONResponse:
        return _error(500, "internal_error", str(exc), type=type(exc).__name__)

    return app


app = create_app()
