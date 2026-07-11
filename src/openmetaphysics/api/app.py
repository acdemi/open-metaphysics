"""FastAPI application exposing agents and orchestration."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from ..agents.registry import get_registry
from ..core.schemas import AgentOutput
from ..inference.explainer import get_explainer
from ..orchestration.graph import OrchestrationRequest, orchestrate


class ExplainRequest(BaseModel):
    output: dict[str, Any]


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
    def agent_compute(name: str, body: dict[str, Any]) -> dict[str, Any]:
        reg = get_registry()
        try:
            agent = reg.get(name)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"unknown agent: {name}") from None
        try:
            payload = agent.input_schema.model_validate(body)
        except ValidationError as exc:
            return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})
        output = agent.compute(payload)
        return output.model_dump(mode="json")

    @app.post("/agents/{name}/explain")
    def agent_explain(name: str, req: ExplainRequest) -> dict[str, str]:
        reg = get_registry()
        try:
            agent = reg.get(name)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"unknown agent: {name}") from None
        try:
            output = AgentOutput.model_validate(req.output)
        except ValidationError as exc:
            return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})
        fresh = type(agent)()
        fresh.explainer = get_explainer()
        return {"agent": name, "explanation": fresh.explain(output)}

    @app.post("/orchestrate")
    def orchestrate_endpoint(req: OrchestrationRequest) -> dict[str, Any]:
        try:
            resp = orchestrate(req)
        except ValidationError as exc:
            return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})
        return resp.model_dump(mode="json")

    @app.exception_handler(Exception)
    def unhandled(_: Any, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"type": "about:blank", "title": str(exc)})

    return app


app = create_app()
