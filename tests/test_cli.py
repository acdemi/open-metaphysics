"""Offline CLI tests (agents / compute / explain)."""

from __future__ import annotations

import json

from openmetaphysics.cli import main

BORN = "1985-08-15T10:00:00+08:00"


def test_agents(capsys) -> None:
    assert main(["agents"]) == 0
    names = {a["name"] for a in json.loads(capsys.readouterr().out)}
    assert names == {"bazi", "liuyao", "qimen", "ziwei"}


def test_compute(capsys) -> None:
    payload = json.dumps({"request_id": "c1", "born_at": BORN, "gender": "male"})
    assert main(["compute", "bazi", "--input", payload]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["agent"] == "bazi"
    assert data["request_id"] == "c1"


def test_compute_with_explain(capsys) -> None:
    payload = json.dumps({"request_id": "c2", "born_at": BORN, "gender": "male"})
    assert main(["compute", "bazi", "--input", payload, "--explain"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "explain" in data
    assert "degraded" in data["explain"]


def test_explain(capsys) -> None:
    payload = json.dumps({"request_id": "c3", "born_at": BORN, "gender": "male"})
    assert main(["compute", "bazi", "--input", payload]) == 0
    output = json.loads(capsys.readouterr().out)
    assert main(["explain", "bazi", "--output", json.dumps(output)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "explanation" in data


def test_unknown_agent(capsys) -> None:
    assert main(["compute", "nope", "--input", "{}"]) == 2
    assert "unknown agent" in capsys.readouterr().err


def test_knowledge(capsys) -> None:
    assert main(["knowledge", "--query", "紫微", "--k", "2"]) == 0
    chunks = json.loads(capsys.readouterr().out)
    assert chunks
    assert all(chunk["id"].startswith("kn:") for chunk in chunks)


def test_consensus(capsys) -> None:
    evidence = {
        "evidence_id": "ev:cli:1",
        "domain": "career",
        "conclusion": "晋升机会",
        "confidence": 0.8,
        "system": "bazi",
        "items": [
            {
                "evidence_id": "evi:1",
                "source_type": "rule",
                "source_id": "rule:cli",
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
    payload = json.dumps({"evidence": [evidence], "config": {"strategy": "retain_all"}})
    assert main(["consensus", "--input", payload]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["report_id"].startswith("cr:")
    assert report["conclusions"][0]["domain"] == "career"
