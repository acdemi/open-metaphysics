"""Minimal-viable-product demo: one representative user task, end to end.

The task: a client born 1990-06-15 08:30 (+08:00) asks

    "事业与财运如何？" (career and wealth)

and the runtime must answer repeatably:

    input -> multi-domain deterministic charts -> evidence -> knowledge
    citations (traceable to the frozen corpus) -> consensus synthesis ->
    offline explanation -> persisted session (readable after restart)

Nothing here is mocked: real engines, real frozen corpora, real persistence.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from openmetaphysics.api.app import create_app
from openmetaphysics.cli import main as cli_main
from openmetaphysics.persistence import SqlAlchemySessionStore
from openmetaphysics.rag.corpus import resolve_corpus_paths

BORN = "1990-06-15T08:30:00+08:00"
QUESTION = "事业与财运如何？"
AGENTS = ["bazi", "ziwei"]

RESULT_SHAPE: dict[str, set[str]] = {
    "bazi": {"pillars", "day_master"},
    "ziwei": {"palaces", "wuxing_ju"},
}


def _payload(request_id: str) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "born_at": BORN,
        "gender": "male",
        "question": QUESTION,
    }


def _orch_request(request_id: str) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "payload": _payload(request_id),
        "agents": AGENTS,
        "strategy": "weighted",
        "explain": True,
    }


def _frozen_citation_ids() -> set[str]:
    ids: set[str] = set()
    for path in resolve_corpus_paths():
        if not path.is_file():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        ids.update(str(n.get("id", "")) for n in doc.get("nodes", []))
        ids.update(str(r.get("id", "")) for r in doc.get("relations", []))
        ids.update(str(r.get("reference_id", "")) for r in doc.get("references", []))
    return ids


def _run_demo(client: TestClient, request_id: str) -> dict[str, Any]:
    response = client.post("/orchestrate", json=_orch_request(request_id))
    assert response.status_code == 200, response.text
    return response.json()


# == the demo task, twice, byte-stable ==


def test_demo_task_runs_repeatably_over_http() -> None:
    client = TestClient(create_app())
    frozen = _frozen_citation_ids()
    assert frozen

    first = _run_demo(client, "demo-repeat")
    second = _run_demo(client, "demo-repeat")  # same request -> same input hash

    for run in (first, second):
        assert run["errors"] == []
        assert [o["agent"] for o in run["outputs"]] == AGENTS

        for output in run["outputs"]:
            assert RESULT_SHAPE[output["agent"]] <= set(output["result"])
            assert output["metadata"]["question"] == QUESTION, "question must persist"
            assert output["reasoning_trace"], "charts must emit an audit trail"

        # every citation is traceable to the frozen corpus with a human-readable source
        for agent, detail in run["explanation_detail"].items():
            knowledge = detail["knowledge"]
            assert knowledge, "the explanation must cite the frozen knowledge base"
            for citation in knowledge:
                assert citation["id"] in frozen, f"untraceable citation: {citation['id']}"
                assert citation["source"], "citations must carry their source"
            # the explanation did not rewrite the deterministic facts
            corresponding = next(o for o in run["outputs"] if o["agent"] == agent)
            assert detail["evidence"]["result"] == corresponding["result"]
            assert detail["evidence"]["input_hash"] == corresponding["input_hash"]

        consensus = run["consensus"]["result"]
        assert {c["agent"] for c in consensus["contributions"]} == set(AGENTS)
        assert consensus["synthesis"]
        assert 0.0 <= consensus["overall_confidence"] <= 1.0
        assert all(run["explanation"][a] for a in AGENTS)

    # repeatability: same input -> same numbers, same consensus, same words
    assert [o["result"] for o in first["outputs"]] == [o["result"] for o in second["outputs"]]
    assert [o["input_hash"] for o in first["outputs"]] == [
        o["input_hash"] for o in second["outputs"]
    ]
    assert first["consensus"]["result"] == second["consensus"]["result"]
    assert first["explanation"] == second["explanation"]


# == persisted demo: readable after a restart ==


def test_demo_session_survives_restart(tmp_path: Path) -> None:
    dsn = f"sqlite:///{tmp_path / 'demo.db'}"

    live_app = create_app()
    live_app.state.session_store = SqlAlchemySessionStore(dsn)
    live_client = TestClient(live_app)
    run = _run_demo(live_client, "demo-persist")
    assert run["errors"] == []

    restarted_app = create_app()
    restarted_app.state.session_store = SqlAlchemySessionStore(dsn)
    restarted_client = TestClient(restarted_app)

    session = restarted_client.get("/sessions/demo-persist")
    assert session.status_code == 200, session.text
    body = session.json()
    assert body["request"]["payload"]["question"] == QUESTION
    assert [o["agent"] for o in body["response"]["outputs"]] == AGENTS
    assert body["response"]["consensus"]["result"]["synthesis"]
    assert body["response"]["explanation"]["bazi"]

    traces = restarted_client.get("/traces/demo-persist")
    assert traces.status_code == 200
    assert {t["agent"] for t in traces.json()["traces"]} == set(AGENTS)

    listing = restarted_client.get("/sessions")
    assert any(s["request_id"] == "demo-persist" for s in listing.json()["sessions"])


# == the same task over the offline CLI ==


def test_demo_task_over_cli_matches_http(capsys) -> None:
    http_client = TestClient(create_app())
    via_http = _run_demo(http_client, "demo-cli")

    request = json.dumps(_orch_request("demo-cli"), ensure_ascii=False)
    assert cli_main(["orchestrate", "--input", request]) == 0
    via_cli = json.loads(capsys.readouterr().out)

    assert via_cli["errors"] == []
    assert [o["agent"] for o in via_cli["outputs"]] == AGENTS
    for http_out, cli_out in zip(via_http["outputs"], via_cli["outputs"], strict=True):
        assert cli_out["result"] == http_out["result"]
        assert cli_out["input_hash"] == http_out["input_hash"]
        assert cli_out["confidence"] == http_out["confidence"]
    assert via_cli["consensus"]["result"] == via_http["consensus"]["result"]
    assert via_cli["explanation"] == via_http["explanation"]
    assert via_cli["explanation_detail"]["bazi"]["knowledge"] == (
        via_http["explanation_detail"]["bazi"]["knowledge"]
    )
