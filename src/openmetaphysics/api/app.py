"""FastAPI application exposing agents, orchestration and the explain pipeline.

Route naming is intentionally kept as-is (``/agents/{name}/...``) rather than
restructured into per-domain REST paths; this phase only closes the runtime
composition, it does not redesign the API surface.

Runtime composition exposed here:

    HTTP request
      -> input validation
      -> orchestration (or a single domain agent)
      -> deterministic calculation
      -> evidence (already-computed facts)
      -> knowledge retrieval (Explain chain)
      -> explanation
      -> HTTP response
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from ..agents.registry import get_registry
from ..core.schemas import AgentOutput
from ..inference.explainer import get_explainer_for
from ..orchestration.graph import OrchestrationRequest, orchestrate


class ExplainRequest(BaseModel):
    output: dict[str, Any]


def _error(status: int, kind: str, message: str, **extra: Any) -> JSONResponse:
    """Structured error body shared by every failure path."""
    return JSONResponse(
        status_code=status,
        content={"error": {"type": kind, "message": message, **extra}},
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
            "text": "",
            "provider": None,
            "degraded": True,
            "knowledge": [],
            "evidence": {},
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }
    return {
        "text": result["explanation"],
        "provider": result["provider"],
        "degraded": result["degraded"],
        "knowledge": [{"id": c["id"], "source": c["source"]} for c in result.get("knowledge", [])],
        # the fact layer the explanation was produced from, so a client can
        # verify that the explanation did not rewrite the deterministic result
        "evidence": result["evidence"],
        # provider failure record (kind/type/message), None when the provider ran
        "error": result.get("error"),
    }


def create_app() -> FastAPI:
    app = FastAPI(
        title="OpenMetaphysics",
        version="0.1.0",
        description="Local-first deterministic multi-agent metaphysics framework.",
    )

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "agents": get_registry().names()}

    @app.get("/agents")
    def list_agents() -> dict[str, Any]:
        reg = get_registry()
        return {"agents": [{"name": a.name, "engine_version": a.engine_version} for a in reg.all()]}

    @app.get("/agents/{name}/schema")
    def agent_schema(name: str) -> dict[str, Any]:
        try:
            return get_registry().get(name).schema()
        except KeyError:
            raise HTTPException(status_code=404, detail=f"unknown agent: {name}") from None

    @app.post("/agents/{name}/compute")
    def agent_compute(
        name: str,
        body: dict[str, Any],
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
            raise HTTPException(status_code=404, detail=f"unknown agent: {name}") from None

        try:
            payload = agent.input_schema.model_validate(body)
        except ValidationError as exc:
            return JSONResponse(
                status_code=422,
                content={"detail": jsonable_encoder(exc.errors())},
            )

        try:
            output = agent.compute(payload)
        except Exception as exc:
            return _error(500, type(exc).__name__, str(exc), agent=name)

        data: dict[str, Any] = output.model_dump(mode="json")
        if explain:
            data["explain"] = _explain_payload(name, output, style=style, k=k)
        return data

    @app.post("/agents/{name}/explain")
    def agent_explain(name: str, req: ExplainRequest, style: str = "concise", k: int = 3) -> Any:
        """Explain an already-computed output (no recalculation)."""
        try:
            get_registry().get(name)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"unknown agent: {name}") from None

        try:
            output = AgentOutput.model_validate(req.output)
        except ValidationError as exc:
            return JSONResponse(
                status_code=422,
                content={"detail": jsonable_encoder(exc.errors())},
            )

        payload = _explain_payload(name, output, style=style, k=k)
        return {
            "agent": name,
            "explanation": payload["text"],
            "provider": payload["provider"],
            "degraded": payload["degraded"],
            "knowledge": payload["knowledge"],
            "evidence": payload["evidence"],
            "error": payload.get("error"),
        }

    @app.post("/orchestrate")
    def orchestrate_endpoint(req: OrchestrationRequest) -> Any:
        try:
            resp = orchestrate(req)
        except ValidationError as exc:
            return JSONResponse(
                status_code=422,
                content={"detail": jsonable_encoder(exc.errors())},
            )
        return resp.model_dump(mode="json")

    @app.exception_handler(Exception)
    def unhandled(_: Any, exc: Exception) -> JSONResponse:
        return _error(500, type(exc).__name__, str(exc))

    return app


app = create_app()
