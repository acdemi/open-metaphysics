"""Evidence Consensus HTTP endpoints (frozen contract, production engine)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from openmetaphysics.api.app import create_app

client = TestClient(create_app())


def _evidence() -> dict:
    return {
        "evidence_id": "ev:api:1",
        "domain": "career",
        "conclusion": "晋升机会",
        "confidence": 0.8,
        "system": "bazi",
        "items": [
            {
                "evidence_id": "evi:1",
                "source_type": "rule",
                "source_id": "rule:api",
                "system": "bazi",
                "domain": "career",
                "confidence": 0.8,
                "conclusion": "晋升机会",
                "weight": 1.0,
                "trace": [],
                "metadata": {},
                "timestamp": None,
                "version": "1.0.0",
            }
        ],
    }


def test_consensus_schema() -> None:
    response = client.get("/consensus/schema")
    assert response.status_code == 200
    body = response.json()
    assert body["input_schema"]["title"] == "ConsensusInput"
    assert body["output_schema"]["title"] == "ConsensusReport"


def test_consensus_evidence_endpoint() -> None:
    response = client.post(
        "/consensus/evidence",
        json={"evidence": [_evidence()], "config": {"strategy": "retain_all"}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["report_id"].startswith("cr:")
    assert body["conclusions"]
    assert body["conclusions"][0]["conclusion_id"].startswith("cc:")
    assert body["conclusions"][0]["domain"] == "career"


def test_consensus_evidence_invalid_422() -> None:
    response = client.post("/consensus/evidence", json={"evidence": [{"bad": 1}]})
    assert response.status_code == 422
    assert response.json()["error"]["kind"] == "invalid_request"
