"""OpenAPI contract tests for the HTTP surface (Prompt 2A).

The contracts asserted here are intentionally narrow:

* ``POST /orchestrate`` publishes ``OrchestrationResponse`` (with the
  ``AgentOutput`` envelope and ``ConsensusOutput`` / ``ConsensusReport``);
* ``GET /health`` and ``GET /agents`` publish minimal response models;
* ``AgentOutput.result`` stays a free-form object — the four domain charts are
  *not* fabricated into the OpenAPI model tree, so generated clients cannot
  pretend to have per-domain type safety;
* the committed ``frontend/openapi.json`` snapshot is byte-identical to a fresh
  deterministic export, which is what ``npm run gen:api`` consumes.

Every response-shape assertion below is also a compatibility guard: adding a
``response_model`` must not drop, rename or reshape fields that the running
handlers already returned.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from openmetaphysics.api.app import app

client = TestClient(app, raise_server_exceptions=False)

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "frontend" / "openapi.json"

BORN = "1990-06-15T08:30:00+09:00"

ENVELOPE_KEYS = {
    "request_id",
    "agent",
    "engine_version",
    "input_hash",
    "computed_at",
    "confidence",
    "reasoning_trace",
    "metadata",
    "result",
}
CONSENSUS_KEYS = {
    "request_id",
    "agent",
    "engine_version",
    "computed_at",
    "confidence",
    "reasoning_trace",
    "metadata",
    "result",
}
DETAIL_KEYS = {"explanation", "provider", "degraded", "knowledge", "evidence", "error"}


def _openapi() -> dict:
    return app.openapi()


def _orchestrate(request_id: str, agents: list[str], explain: bool = False) -> dict:
    response = client.post(
        "/orchestrate",
        json={
            "request_id": request_id,
            "payload": {
                "request_id": request_id,
                "born_at": BORN,
                "gender": "male",
                "question": "契约测试固定问题",
                "seed": 42,
            },
            "agents": agents,
            "explain": explain,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


# -- published models -------------------------------------------------------


def test_orchestration_components_are_published():
    schemas = _openapi()["components"]["schemas"]
    for name in (
        "OrchestrationResponse",
        "AgentOutput",
        "ConsensusOutput",
        "ConsensusReport",
        "AgentContribution",
        "Conflict",
        "ConfidenceScore",
        "ReasoningStep",
        "HealthResponse",
        "AgentsResponse",
        "AgentInfo",
    ):
        assert name in schemas, f"missing OpenAPI component: {name}"


def test_orchestrate_and_simple_routes_reference_models():
    paths = _openapi()["paths"]
    assert paths["/orchestrate"]["post"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/OrchestrationResponse"
    }
    assert paths["/health"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthResponse"
    }
    assert paths["/agents"]["get"]["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/AgentsResponse"
    }


def test_orchestration_response_fields_are_exact():
    schema = _openapi()["components"]["schemas"]["OrchestrationResponse"]
    assert set(schema["properties"]) == {
        "request_id",
        "outputs",
        "consensus",
        "explanation",
        "explanation_detail",
        "errors",
    }
    # the model only requires what the handler always returns
    assert schema["required"] == ["request_id"]
    assert schema["properties"]["outputs"]["items"] == {"$ref": "#/components/schemas/AgentOutput"}
    assert schema["properties"]["consensus"]["anyOf"] == [
        {"$ref": "#/components/schemas/ConsensusOutput"},
        {"type": "null"},
    ]


def test_agent_envelope_keeps_result_free_form():
    """``result`` is documented as an object, not faked into domain-chart types."""
    schema = _openapi()["components"]["schemas"]["AgentOutput"]
    assert set(schema["properties"]) == ENVELOPE_KEYS
    assert schema["properties"]["result"] == {
        "additionalProperties": True,
        "title": "Result",
        "type": "object",
    }
    assert schema["properties"]["confidence"] == {"$ref": "#/components/schemas/ConfidenceScore"}


def test_health_and_agents_models_match_responses():
    health = client.get("/health").json()
    assert set(health) == {"status", "agents"}
    assert health["status"] == "ok"
    assert sorted(health["agents"]) == ["bazi", "liuyao", "qimen", "ziwei"]

    agents = client.get("/agents").json()
    assert set(agents) == {"agents"}
    for item in agents["agents"]:
        assert set(item) == {"name", "engine_version"}
        assert isinstance(item["name"], str) and isinstance(item["engine_version"], str)


# -- live response shape compatibility --------------------------------------


def test_single_domain_orchestrate_keeps_envelope_shape():
    data = _orchestrate("contract-shape-single", ["bazi"], explain=True)
    assert set(data) == {
        "request_id",
        "outputs",
        "consensus",
        "explanation",
        "explanation_detail",
        "errors",
    }
    assert data["consensus"] is None
    assert data["errors"] == []
    assert len(data["outputs"]) == 1
    output = data["outputs"][0]
    assert set(output) == ENVELOPE_KEYS
    assert output["agent"] == "bazi"
    # the free-form payload still carries the real (untyped) chart
    assert "pillars" in output["result"] and "day_master" in output["result"]
    assert set(data["explanation_detail"]["bazi"]) == DETAIL_KEYS


def test_multi_domain_orchestrate_keeps_consensus_shape():
    data = _orchestrate(
        "contract-shape-consensus", ["bazi", "ziwei", "liuyao", "qimen"], explain=True
    )
    assert [o["agent"] for o in data["outputs"]] == ["bazi", "ziwei", "liuyao", "qimen"]
    assert data["consensus"] is not None
    assert set(data["consensus"]) == CONSENSUS_KEYS
    assert isinstance(data["consensus"]["confidence"], float)
    report = data["consensus"]["result"]
    assert {
        "overall_confidence",
        "contributions",
        "agreement_matrix",
        "conflicts",
        "synthesis",
    } <= set(report)
    assert len(report["contributions"]) == 4


def test_partial_unknown_agent_keeps_batch_semantics():
    data = _orchestrate("contract-shape-partial", ["bazi", "nope"])
    assert [o["agent"] for o in data["outputs"]] == ["bazi"]
    assert data["errors"] == ["unknown agent: nope"]
    assert data["consensus"] is None


def test_error_shapes_unchanged():
    unknown = client.post(
        "/orchestrate",
        json={
            "request_id": "contract-shape-unknown",
            "payload": {"request_id": "contract-shape-unknown", "born_at": BORN},
            "agents": ["nope"],
        },
    )
    assert unknown.status_code == 404
    assert set(unknown.json()) == {"detail", "error"}
    assert unknown.json()["error"]["kind"] == "unknown_agent"

    invalid = client.post(
        "/orchestrate",
        json={"request_id": "contract-shape-invalid", "payload": {"request_id": "x"}},
    )
    assert invalid.status_code == 422
    assert set(invalid.json()) == {"detail", "error"}
    assert invalid.json()["error"]["kind"] == "invalid_request"


# -- generated-type snapshot ------------------------------------------------


def test_frontend_openapi_snapshot_is_current():
    """The snapshot consumed by ``npm run gen:api`` must match a fresh export."""
    assert SNAPSHOT.exists(), (
        "frontend/openapi.json missing: run `uv run python scripts/export_openapi.py`"
    )
    expected = json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    assert SNAPSHOT.read_text(encoding="utf-8") == expected, (
        "frontend/openapi.json is stale: run `uv run python scripts/export_openapi.py`"
    )
