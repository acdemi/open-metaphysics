"""单域独立计算契约（Prompt 8A）：GET /agents、GET /agents/{name}/schema、POST /agents/{name}/compute。

核心断言：单域 compute 返回与 /orchestrate 的 outputs[] 相同的 AgentOutput 信封与结果；
它不产生共识、不包含其他领域；错误形状与既有公开错误模型一致。
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from openmetaphysics.api.app import app, create_app

client = TestClient(create_app())
BORN = "1990-06-15T08:30:00+09:00"
DOMAINS = ("bazi", "ziwei", "qimen", "liuyao")
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


def _payload(request_id: str, **extra: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "request_id": request_id,
        "born_at": BORN,
        "gender": "male",
        "question": "独立计算契约",
        "seed": 42,
    }
    body.update(extra)
    return body


def _compute(domain: str, body: dict[str, Any], **params: Any) -> Any:
    return client.post(f"/agents/{domain}/compute", json=body, params=params)


def test_agents_list_contains_exactly_the_four_domains() -> None:
    response = client.get("/agents")
    assert response.status_code == 200
    agents = response.json()["agents"]
    assert [item["name"] for item in agents] == ["bazi", "liuyao", "qimen", "ziwei"]
    assert all(
        isinstance(item["engine_version"], str) and item["engine_version"] for item in agents
    )


def test_agent_schema_is_json_schema_envelope() -> None:
    for domain in DOMAINS:
        response = client.get(f"/agents/{domain}/schema")
        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"name", "engine_version", "input_schema", "output_schema"}
        assert body["name"] == domain
        schema = body["input_schema"]
        assert schema["type"] == "object"
        assert set(schema["required"]) == {"request_id", "born_at"}
        assert "properties" in schema and "request_id" in schema["properties"]
        assert body["output_schema"]["type"] == "object"


def test_agent_schema_contains_domain_specific_fields() -> None:
    bazi = client.get("/agents/bazi/schema").json()["input_schema"]["properties"]
    assert bazi["dayun_count"]["type"] == "integer"
    assert bazi["dayun_count"]["default"] == 8

    ziwei = client.get("/agents/ziwei/schema").json()["input_schema"]["properties"]
    assert "lunar_month" in ziwei and "lunar_day" in ziwei

    liuyao = client.get("/agents/liuyao/schema").json()["input_schema"]["properties"]
    assert "casts" in liuyao
    assert liuyao["casts"]["default"] is None

    qimen = client.get("/agents/qimen/schema").json()["input_schema"]["properties"]
    assert "casts" not in qimen and "lunar_month" not in qimen and "dayun_count" not in qimen


def test_compute_returns_single_agent_output_envelope() -> None:
    for domain in DOMAINS:
        body = _compute(domain, _payload(f"compute-{domain}"))
        assert body.status_code == 200, body.text
        data = body.json()
        assert set(data) == ENVELOPE_KEYS
        assert data["agent"] == domain
        assert data["request_id"] == f"compute-{domain}"
        assert data["engine_version"] == "0.1.0" or isinstance(data["engine_version"], str)
        assert isinstance(data["result"], dict) and data["result"]
        assert isinstance(data["reasoning_trace"], list) and data["reasoning_trace"]
        assert "consensus" not in data
        assert "errors" not in data
        assert "explain" not in data


def test_compute_matches_orchestration_output_for_same_input() -> None:
    payload = _payload("parity-1")
    for domain in DOMAINS:
        computed = _compute(domain, dict(payload))
        assert computed.status_code == 200, computed.text
        orchestrated = client.post(
            "/orchestrate",
            json={
                "request_id": "parity-1",
                "payload": payload,
                "agents": [domain],
                "explain": False,
            },
        )
        assert orchestrated.status_code == 200, orchestrated.text
        outputs = orchestrated.json()["outputs"]
        assert [output["agent"] for output in outputs] == [domain]
        output = outputs[0]
        computed_data = computed.json()
        assert computed_data["result"] == output["result"]
        assert computed_data["confidence"] == output["confidence"]
        assert computed_data["input_hash"] == output["input_hash"]


def test_compute_validation_errors_and_unknown_agent() -> None:
    missing_born_at = _compute("bazi", {"request_id": "bad-1", "gender": "male"})
    assert missing_born_at.status_code == 422
    assert missing_born_at.json()["error"]["kind"] == "invalid_request"
    assert missing_born_at.json()["error"]["fields"]

    bad_casts = _compute("liuyao", _payload("bad-casts", casts=[1, 2, 3, 4, 5, 6]))
    assert bad_casts.status_code == 422
    assert bad_casts.json()["error"]["kind"] == "invalid_request"

    lunar_only = _compute("ziwei", _payload("bad-lunar", lunar_month=5))
    assert lunar_only.status_code == 422
    assert lunar_only.json()["error"]["kind"] == "invalid_request"

    unknown = _compute("nope", _payload("bad-agent"))
    assert unknown.status_code == 404
    assert unknown.json()["error"]["kind"] == "unknown_agent"


def test_compute_explain_flag_is_optional() -> None:
    plain = _compute("qimen", _payload("explain-off"))
    assert "explain" not in plain.json()

    explained = _compute("qimen", _payload("explain-on"), explain=True)
    assert explained.status_code == 200
    explain = explained.json()["explain"]
    assert set(explain) >= {"explanation", "provider", "degraded", "knowledge", "evidence"}


def test_agent_routes_publish_response_models() -> None:
    paths = app.openapi()["paths"]
    assert paths["/agents/{name}/compute"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"] == {"$ref": "#/components/schemas/AgentComputeResponse"}
    assert paths["/agents/{name}/schema"]["get"]["responses"]["200"]["content"]["application/json"][
        "schema"
    ] == {"$ref": "#/components/schemas/AgentSchemaResponse"}
    schemas = app.openapi()["components"]["schemas"]
    assert {"AgentComputeResponse", "AgentSchemaResponse"} <= set(schemas)
