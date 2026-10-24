"""End-to-end acceptance paths for the production runtime.

Minimal, cross-surface acceptance checks (complementing the focused suites):

    1. four-domain compute over HTTP (structure, determinism, errors)
    2. knowledge retrieval + explain provenance (traceable, nodes-only explain)
    3. evidence consensus (strategies, conflict reporting, empty/error paths)
    4. API / MCP / CLI consistency for the same operation
    5. persistence surviving an application restart (SQLite store)
    6. service surface (root/health/OpenAPI, entry points)
"""

from __future__ import annotations

import json
from typing import Any

from fastapi.testclient import TestClient

from openmetaphysics.api.app import create_app
from openmetaphysics.cli import main as cli_main
from openmetaphysics.mcp.server import handle_message
from openmetaphysics.persistence import SqlAlchemySessionStore
from openmetaphysics.rag.corpus import resolve_corpus_paths
from openmetaphysics.rag.retriever import get_evidence_retriever, reset_retriever

client = TestClient(create_app())

BORN = "1985-08-15T10:00:00+08:00"
PAYLOAD: dict[str, Any] = {"request_id": "acc", "born_at": BORN, "gender": "male"}

# minimal result structure per domain (acceptance level, not a golden vector)
RESULT_SHAPE: dict[str, set[str]] = {
    "bazi": {"pillars", "day_master", "ten_gods_map"},
    "ziwei": {"palaces", "wuxing_ju", "fate_palace_index"},
    "qimen": {"cells", "dun_type", "ju"},
    "liuyao": {"original_hexagram", "changed_hexagram", "najia"},
}


def _mcp_tool_call(name: str, arguments: dict[str, Any]) -> Any:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
    )
    assert response is not None
    return json.loads(response["result"]["content"][0]["text"])


# == Path 1: four-domain compute ==


def test_path1_agents_and_schemas() -> None:
    agents = client.get("/agents").json()["agents"]
    assert {a["name"] for a in agents} == {"bazi", "ziwei", "qimen", "liuyao"}

    for name in RESULT_SHAPE:
        body = client.get(f"/agents/{name}/schema")
        assert body.status_code == 200, name
        schema = body.json()
        assert schema["name"] == name
        assert schema["input_schema"]["title"].lower().startswith(name)
        assert schema["output_schema"]["title"].lower().startswith(name)
        assert schema["engine_version"]


def test_path1_compute_all_domains_structured_and_deterministic() -> None:
    for name, keys in RESULT_SHAPE.items():
        body = {**PAYLOAD, "request_id": f"acc-{name}"}
        if name == "liuyao":
            body["casts"] = [7, 6, 8, 9, 7, 8]  # explicit deterministic casting

        first = client.post(f"/agents/{name}/compute", json=body)
        second = client.post(f"/agents/{name}/compute", json=body)
        assert first.status_code == 200, f"{name}: {first.text[:200]}"
        assert second.status_code == 200, name

        a, b = first.json(), second.json()
        assert a["agent"] == name
        assert keys <= set(a["result"]), f"{name}: missing {keys - set(a['result'])}"
        assert a["reasoning_trace"], f"{name}: deterministic trace expected"
        assert 0.0 <= a["confidence"]["value"] <= 1.0
        assert a["result"] == b["result"], f"{name}: not deterministic"
        assert a["input_hash"] == b["input_hash"]


def test_path1_invalid_inputs_return_structured_422() -> None:
    for name in RESULT_SHAPE:
        response = client.post(f"/agents/{name}/compute", json={"request_id": "bad"})
        assert response.status_code == 422, name
        assert response.json()["error"]["kind"] == "invalid_request", name

    bad_casts = client.post(
        "/agents/liuyao/compute", json={**PAYLOAD, "casts": [7, 7, 7]}
    )
    assert bad_casts.status_code == 422
    assert bad_casts.json()["error"]["kind"] == "invalid_request"


# == Path 2: knowledge retrieval + explain ==


def _frozen_evidence_ids() -> set[str]:
    ids: set[str] = set()
    for path in resolve_corpus_paths():
        if not path.is_file():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        ids.update(str(r["id"]) for r in doc.get("relations", []))
        ids.update(str(r["reference_id"]) for r in doc.get("references", []))
    return ids


def test_path2_evidence_recall_is_traceable_and_reproducible() -> None:
    frozen = _frozen_evidence_ids()
    assert frozen, "frozen corpora must expose relations/references"

    saw_evidence = False
    for query in ("帝座", "紫微天府", "暗动"):
        body = {"query": query, "k": 8, "include_evidence": True}
        first = client.post("/knowledge/search", json=body).json()["chunks"]
        second = client.post("/knowledge/search", json=body).json()["chunks"]
        assert [c["id"] for c in first] == [c["id"] for c in second], query

        for chunk in first:
            if chunk["id"].startswith("kn:"):
                continue
            saw_evidence = True
            assert chunk["id"] in frozen, f"unattributable evidence: {chunk['id']}"
            assert chunk["text"].strip()
            assert chunk["source"], f"evidence without source label: {chunk['id']}"
    assert saw_evidence, "queries must recall at least one evidence chunk"


def test_path2_corpus_stats_match_frozen_files() -> None:
    stats = {s["corpus_id"]: s for s in client.get("/knowledge/corpora").json()["corpora"]}
    for path in resolve_corpus_paths():
        if not path.is_file():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        corpus_id = doc["metadata"]["corpus_id"]
        assert stats[corpus_id]["status"] == "frozen"
        counts = stats[corpus_id]["counts"]
        assert counts["nodes"] == len(doc.get("nodes", [])), corpus_id
        assert counts["relations"] == len(doc.get("relations", [])), corpus_id
        assert counts["references"] == len(doc.get("references", [])), corpus_id


def test_path2_explain_stays_nodes_only_and_attributed() -> None:
    reset_retriever()
    get_evidence_retriever()  # prime the opt-in corpus first
    try:
        response = client.post("/agents/bazi/compute?explain=true", json=PAYLOAD)
        assert response.status_code == 200
        knowledge = response.json()["explain"]["knowledge"]
        assert knowledge, "explain must carry retrieved knowledge"
        assert all(k["id"].startswith("kn:") for k in knowledge)
        assert all(k["source"] for k in knowledge)
    finally:
        reset_retriever()


# == Path 3: consensus ==


def _evidence(evidence_id: str, conclusion: str, confidence: float, system: str) -> dict:
    return {
        "evidence_id": evidence_id,
        "domain": "career",
        "conclusion": conclusion,
        "confidence": confidence,
        "system": system,
        "items": [
            {
                "evidence_id": f"{evidence_id}:i",
                "source_type": "rule",
                "source_id": "rule:acc",
                "system": system,
                "domain": "career",
                "confidence": confidence,
                "conclusion": conclusion,
                "weight": 1.0,
                "trace": [],
                "metadata": {},
                "timestamp": None,
                "version": "1.0.0",
            }
        ],
    }


def test_path3_consensus_strategies_and_conflict_reporting() -> None:
    evidence = [
        _evidence("e1", "晋升", 0.8, "bazi"),
        _evidence("e2", "降职", 0.6, "ziwei"),
    ]
    reports: dict[str, dict] = {}
    for strategy in ("retain_all", "highest_confidence", "majority"):
        response = client.post(
            "/consensus/evidence",
            json={"evidence": evidence, "config": {"strategy": strategy}},
        )
        assert response.status_code == 200, strategy
        report = response.json()
        reports[strategy] = report
        assert report["report_id"].startswith("cr:")
        assert report["metadata"]["strategy"] == strategy
        assert report["conclusions"], strategy
        assert 0.0 <= report["overall_confidence"] <= 1.0

    retain = reports["retain_all"]
    assert {c["conclusion"] for c in retain["conclusions"]} == {"晋升", "降职"}
    assert retain["conflicts"] == []
    assert all(c["is_conflict"] for c in retain["conclusions"])

    highest = reports["highest_confidence"]
    assert [c["conclusion"] for c in highest["conclusions"]] == ["晋升"]
    assert [c["conclusion"] for c in highest["conflicts"]] == ["降职"]


def test_path3_consensus_empty_and_error_paths() -> None:
    empty = client.post("/consensus/evidence", json={"evidence": []})
    assert empty.status_code == 200
    body = empty.json()
    assert body["conclusions"] == []
    assert body["conflicts"] == []
    assert body["overall_confidence"] == 0.0

    bad_strategy = client.post(
        "/consensus/evidence", json={"evidence": [], "config": {"strategy": "nope"}}
    )
    assert bad_strategy.status_code == 422
    assert bad_strategy.json()["error"]["kind"] == "invalid_request"

    bad_evidence = client.post("/consensus/evidence", json={"evidence": [{"bad": 1}]})
    assert bad_evidence.status_code == 422
    assert bad_evidence.json()["error"]["kind"] == "invalid_request"


# == Path 4: API / MCP / CLI consistency ==


def test_path4_compute_consistent_across_api_mcp_cli(capsys) -> None:
    payload = {**PAYLOAD, "request_id": "consistency"}

    via_api = client.post("/agents/bazi/compute", json=payload).json()
    via_mcp = _mcp_tool_call("compute", {"name": "bazi", "input": payload})

    assert cli_main(["compute", "bazi", "--input", json.dumps(payload)]) == 0
    via_cli = json.loads(capsys.readouterr().out)

    for surface in (via_mcp, via_cli):
        assert surface["agent"] == "bazi"
        assert surface["result"] == via_api["result"]
        assert surface["input_hash"] == via_api["input_hash"]
        assert surface["confidence"] == via_api["confidence"]


def test_path4_knowledge_search_consistent_across_surfaces(capsys) -> None:
    query = {"query": "紫微", "k": 3}
    via_api = [c["id"] for c in client.post("/knowledge/search", json=query).json()["chunks"]]
    via_mcp = [
        c["id"] for c in _mcp_tool_call("knowledge_search", {"query": "紫微", "k": 3})
    ]

    assert cli_main(["knowledge", "--query", "紫微", "--k", "3"]) == 0
    via_cli = [c["id"] for c in json.loads(capsys.readouterr().out)]

    assert via_api == via_mcp == via_cli


def test_path4_explain_accepts_responses_with_attached_explain(capsys) -> None:
    """A compute?explain=true response must round-trip into every explain surface."""
    payload = {**PAYLOAD, "request_id": "roundtrip"}
    computed = client.post("/agents/bazi/compute?explain=true", json=payload).json()
    assert "explain" in computed

    via_endpoint = client.post("/agents/bazi/explain", json={"output": computed})
    assert via_endpoint.status_code == 200, via_endpoint.text
    assert via_endpoint.json()["explanation"]

    via_mcp = _mcp_tool_call("explain", {"agent": "bazi", "output": computed})
    assert via_mcp["explanation"]

    assert cli_main(["explain", "bazi", "--output", json.dumps(computed)]) == 0
    via_cli = json.loads(capsys.readouterr().out)
    assert via_cli["explanation"]

    # strictness is preserved: genuinely unknown keys are still rejected
    poisoned = {**computed, "bogus": 1}
    assert client.post("/agents/bazi/explain", json={"output": poisoned}).status_code == 422


def test_path4_mcp_http_and_stdio_share_the_same_tool_surface() -> None:
    stdio_list = handle_message({"jsonrpc": "2.0", "id": 5, "method": "tools/list"})
    http_list = client.post(
        "/mcp", json={"jsonrpc": "2.0", "id": 5, "method": "tools/list"}
    )
    assert http_list.status_code == 200
    assert http_list.json() == stdio_list

    payload = {**PAYLOAD, "request_id": "mcp-parity"}
    via_stdio = _mcp_tool_call("compute", {"name": "ziwei", "input": payload})
    http_call = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "compute", "arguments": {"name": "ziwei", "input": payload}},
        },
    )
    via_http = json.loads(http_call.json()["result"]["content"][0]["text"])
    assert via_http["result"] == via_stdio["result"]
    assert via_http["input_hash"] == via_stdio["input_hash"]


# == Path 5: persistence across restart ==


def test_path5_sqlite_session_survives_restart_over_http(tmp_path) -> None:
    dsn = f"sqlite:///{tmp_path / 'acceptance.db'}"

    first_app = create_app()
    first_app.state.session_store = SqlAlchemySessionStore(dsn)
    first_client = TestClient(first_app)
    body = {"request_id": "restart-1", "born_at": BORN, "gender": "male"}
    assert first_client.post("/agents/bazi/compute", json=body).status_code == 200

    # second app instance == restarted service against the same database
    second_app = create_app()
    second_app.state.session_store = SqlAlchemySessionStore(dsn)
    second_client = TestClient(second_app)

    session = second_client.get("/sessions/restart-1")
    assert session.status_code == 200
    assert session.json()["response"]["result"]["pillars"]

    traces = second_client.get("/traces/restart-1")
    assert traces.status_code == 200
    assert traces.json()["traces"][0]["agent"] == "bazi"

    listing = second_client.get("/sessions")
    assert any(s["request_id"] == "restart-1" for s in listing.json()["sessions"])


def test_path5_store_failure_does_not_break_compute() -> None:
    class _BrokenStore:
        def save_session(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("store down")

        def get_session(self, request_id: str) -> None:
            return None

        def get_traces(self, request_id: str) -> list:
            return []

        def list_sessions(self) -> list:
            return []

    app = create_app()
    app.state.session_store = _BrokenStore()
    local = TestClient(app)

    response = local.post(
        "/agents/bazi/compute", json={**PAYLOAD, "request_id": "broken-store"}
    )
    assert response.status_code == 200
    assert response.json()["result"]["pillars"]
    assert local.get("/sessions/broken-store").status_code == 404


# == Path 6: service surface ==


def test_path6_service_surface_and_openapi() -> None:
    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["name"] == "OpenMetaphysics"

    health = client.get("/health").json()
    assert health["status"] == "ok"
    assert set(health["agents"]) == {"bazi", "ziwei", "qimen", "liuyao"}

    paths = set(client.get("/openapi.json").json()["paths"])
    expected = {
        "/",
        "/health",
        "/agents",
        "/agents/{name}/schema",
        "/agents/{name}/compute",
        "/agents/{name}/explain",
        "/orchestrate",
        "/knowledge/corpora",
        "/knowledge/search",
        "/mcp",
        "/consensus/schema",
        "/consensus/evidence",
        "/sessions",
        "/sessions/{request_id}",
        "/traces/{request_id}",
    }
    assert expected <= paths


def test_path6_entry_points_are_importable() -> None:
    from openmetaphysics.api.__main__ import main as api_main
    from openmetaphysics.cli import main as cli_entry
    from openmetaphysics.mcp.server import main as mcp_entry

    assert callable(api_main)
    assert callable(cli_entry)
    assert callable(mcp_entry)

    import openmetaphysics.api.app as app_module

    assert app_module.app is not None, "uvicorn target openmetaphysics.api.app:app must exist"
