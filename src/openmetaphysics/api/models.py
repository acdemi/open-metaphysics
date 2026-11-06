"""HTTP response models for the FastAPI surface.

These models exist only to publish the shapes the endpoints already return in
``/openapi.json`` (and therefore in generated clients). They add no fields, do
not alter computation, and are intentionally minimal: ``/orchestrate`` reuses
``OrchestrationResponse`` from the orchestration layer, and the domain-specific
``result`` payload stays a free-form object because the OpenAPI model tree does
not (yet) carry the four domain charts.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..core.schemas import AgentOutput


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


class KnowledgeSearchChunk(BaseModel):
    """One chunk returned by ``POST /knowledge/search``.

    Mirrors ``rag.retriever.KnowledgeChunk`` as exposed by the route: no
    relevance score is returned by the API (the UI must not invent one).
    """

    id: str
    text: str
    source: str = ""
    tags: list[str] = Field(default_factory=list)


class KnowledgeSearchResponse(BaseModel):
    """``POST /knowledge/search`` — independent frozen-corpus retrieval."""

    query: str
    include_evidence: bool
    chunks: list[KnowledgeSearchChunk]


class KnowledgeCorpusInfo(BaseModel):
    """One frozen corpus entry from ``GET /knowledge/corpora``."""

    corpus_id: str
    status: str | None = None
    version: str | None = None
    counts: dict[str, int] = Field(default_factory=dict)


class KnowledgeCorporaResponse(BaseModel):
    """``GET /knowledge/corpora``."""

    corpora: list[KnowledgeCorpusInfo]


class AgentSchemaResponse(BaseModel):
    """``GET /agents/{name}/schema`` — the agent's own JSON Schemas."""

    name: str
    engine_version: str
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)


class AgentComputeResponse(AgentOutput):
    """``POST /agents/{name}/compute`` — one domain's ``AgentOutput`` envelope.

    ``explain`` is only present when ``?explain=true``; the route serializes
    with ``response_model_exclude_none`` so non-explain responses keep the exact
    pre-existing wire shape (no ``explain: null`` key).
    """

    explain: dict[str, Any] | None = None
