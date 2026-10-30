"""HTTP response models for the FastAPI surface.

These models exist only to publish the shapes the endpoints already return in
``/openapi.json`` (and therefore in generated clients). They add no fields, do
not alter computation, and are intentionally minimal: ``/orchestrate`` reuses
``OrchestrationResponse`` from the orchestration layer, and the domain-specific
``result`` payload stays a free-form object because the OpenAPI model tree does
not (yet) carry the four domain charts.
"""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """``GET /health`` — liveness plus the registered agent names."""

    status: str
    agents: list[str]


class AgentInfo(BaseModel):
    """One registered agent as listed by ``GET /agents``."""

    name: str
    engine_version: str


class AgentsResponse(BaseModel):
    """``GET /agents``."""

    agents: list[AgentInfo]
