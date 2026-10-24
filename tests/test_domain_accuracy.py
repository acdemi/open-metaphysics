"""Minimal domain-accuracy evaluation set (reuses frozen assets only).

Every expected value comes from an existing frozen artifact:

    docs/{bazi,ziwei,liuyao,qimen}/golden_vectors.json  -- frozen charts
    knowledge/*_corpus.json                             -- frozen citations
    src/openmetaphysics/{agents/qimen,agents/ziwei}.py  -- documented scope

Categories are kept separate on purpose (test names carry the prefix):

    calc_*          production output == frozen Golden Vector
    boundary_*      time/input boundary behavior == frozen vector + domain rule
    evidence_*      citations exist, sources are exact, references target real nodes
    explain_*       prose restates computed facts; citations appear in the prose
    consensus_*     support bonus / conflict strategies / empty & missing evidence
    undetermined_*  cases with no authoritative expectation (documented, not judged)

``calc_*`` / ``boundary_*`` establish contract conformance, NOT that the
domain conclusion is the only defensible one. School-dependent conventions are
listed in ``UNDETERMINED_CASES`` and must not be treated as universal truth.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from openmetaphysics.api.app import create_app
from openmetaphysics.core.schemas import agent_output_from_envelope
from openmetaphysics.inference.explainer import get_explainer_for
from openmetaphysics.rag.retriever import get_retriever

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "docs"
KNOWLEDGE = ROOT / "knowledge"

client = TestClient(create_app())

BORN = "1985-08-15T10:00:00+08:00"
QUESTION = "事业与财运"

UNDETERMINED_CASES: list[dict[str, str]] = [
    {
        "case": "ziwei.auxiliary_stars",
        "reason": "辅星/杂曜/四化/大限属 ZW-017 未实现边界，流派差异大，无权威单一答案",
        "artifact": "docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT.md",
    },
    {
        "case": "qimen.zhirun",
        "reason": "实现采用拆补法近似；超神接气/置闰法未实现，置闰法结果无冻结预期",
        "artifact": "src/openmetaphysics/agents/qimen.py",
    },
    {
        "case": "bazi.late_zi_day_rollover",
        "reason": "23:00 换日属晚子时流派约定；冻结向量锁定项目约定，非唯一真解",
        "artifact": "docs/bazi/golden_vectors.json",
    },
    {
        "case": "ziwei.leap_month_placement",
        "reason": "闰月安星存在流派差异；实现按『月号同值』处理并在 calendar_note 标注，属项目约定",
        "artifact": "docs/ziwei/golden_vectors.json",
    },
    {
        "case": "liuyao.yong_shen_selection",
        "reason": "用神取法存在流派差异；实现按关键词优先级取用神，属项目约定",
        "artifact": "docs/liuyao/golden_vectors.json",
    },
]


# == asset loading (no new expected values) ==


def _golden(domain: str, vector_id: str) -> dict[str, Any]:
    doc = json.loads((GOLDEN / domain / "golden_vectors.json").read_text(encoding="utf-8"))
    return next(v for v in doc["vectors"] if v["id"] == vector_id)


def _api_body(domain: str, vector: dict[str, Any]) -> dict[str, Any]:
    body = dict(vector["input"])
    body["request_id"] = f"eval-{vector['id']}"
    if domain == "bazi":
        location = body.get("born_location") or {}
        body["born_location"] = {
            "latitude": 0.0,
            "longitude": 0.0,
            "timezone": location.get("timezone", "Asia/Shanghai"),
        }
        for key in ("year", "month", "day", "hour", "timezone"):
            body.pop(key, None)
    return body


def _compute(domain: str, vector: dict[str, Any]) -> dict[str, Any]:
    response = client.post(f"/agents/{domain}/compute", json=_api_body(domain, vector))
    assert response.status_code == 200, f"{domain}/{vector['id']}: {response.text[:300]}"
    return response.json()["result"]


def _pillar(pillar: dict[str, Any]) -> tuple[str, str]:
    return str(pillar["stem"]), str(pillar["branch"])


def _corpus_index() -> dict[str, tuple[str, dict[str, Any]]]:
    index: dict[str, tuple[str, dict[str, Any]]] = {}
    for path in sorted(KNOWLEDGE.glob("*_corpus.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for node in doc.get("nodes", []):
            index[str(node["id"])] = ("node", node)
        for reference in doc.get("references", []):
            index[str(reference["reference_id"])] = ("reference", reference)
        for relation in doc.get("relations", []):
            index[str(relation["id"])] = ("relation", relation)
    return index


def _source_label(entry: dict[str, Any]) -> str:
    source = entry.get("source") or {}
    label = str(source.get("text", ""))
    chapter = source.get("chapter")
    if chapter:
        label = f"{label} · {chapter}" if label else str(chapter)
    return label


# == CALC: production == frozen Golden Vectors ==


def test_calc_bazi_matches_frozen_vector() -> None:
    vector = _golden("bazi", "B_tz_001")
    expected = vector["expected"]
    result = _compute("bazi", vector)

    assert [_pillar(p) for p in result["pillars"]] == [
        _pillar(expected[key])
        for key in ("year_pillar", "month_pillar", "day_pillar", "hour_pillar")
    ]
    assert result["day_master"] == expected["day_pillar"]["stem"]


def test_calc_ziwei_matches_frozen_vector() -> None:
    vector = _golden("ziwei", "ZV-ref-002")
    expected = vector["expected"]["chart"]
    result = _compute("ziwei", vector)

    assert result["wuxing_ju"] == expected["wuxing_ju"]
    assert result["fate_palace_index"] == expected["fate_palace_index"]
    assert result["body_palace_index"] == expected["body_palace_index"]
    assert [
        (p["name"], p["earthly_branch"], p["main_stars"]) for p in result["palaces"]
    ] == [
        (p["name"], p["earthly_branch"], p["main_stars"]) for p in expected["palaces"]
    ]


def test_calc_liuyao_matches_frozen_vector() -> None:
    vector = _golden("liuyao", "LY_norm_001")
    expected = vector["expected"]
    result = _compute("liuyao", vector)

    for key in (
        "original_hexagram",
        "changed_hexagram",
        "palace",
        "palace_element",
        "shi_position",
        "mutual_hexagram",
    ):
        assert result[key] == expected[key], key


def test_calc_qimen_matches_frozen_vector() -> None:
    vector = _golden("qimen", "G1")
    expected = vector["expected_board"]
    result = _compute("qimen", vector)

    for key in ("solar_term", "ju", "dun_type", "day_of_month", "triple_offset"):
        assert result[key] == expected[key], key

    cell_keys = (
        "palace",
        "name",
        "sky_plate",
        "earth_plate",
        "eight_gods",
        "nine_stars",
        "eight_doors",
        "three_qi",
        "is_void",
        "is_central",
    )
    assert [{k: c.get(k) for k in cell_keys} for c in result["cells"]] == [
        {k: c.get(k) for k in cell_keys} for c in expected["cells"]
    ]


def test_calc_qimen_matches_reference_runtime_directly() -> None:
    """The production board and the Reference Runtime agree on the same input."""
    from reference.qimen.domain import compute as reference_compute

    vector = _golden("qimen", "G1")
    reference = reference_compute(vector["input"])
    assert reference == vector["expected_board"], "frozen vector drifted from Reference"
    assert _compute("qimen", vector) == reference


# == BOUNDARY: time / input boundaries ==


def test_boundary_bazi_lichun_switches_year_and_month() -> None:
    before = _golden("bazi", "B_term_001")
    after = _golden("bazi", "B_term_002")
    result_before = _compute("bazi", before)
    result_after = _compute("bazi", after)

    for result, vector in ((result_before, before), (result_after, after)):
        expected = vector["expected"]
        assert _pillar(result["pillars"][0]) == _pillar(expected["year_pillar"])
        assert _pillar(result["pillars"][1]) == _pillar(expected["month_pillar"])

    # 立春 boundary: the year pillar and the month pillar both switch
    assert _pillar(result_before["pillars"][0]) != _pillar(result_after["pillars"][0])
    assert _pillar(result_before["pillars"][1]) != _pillar(result_after["pillars"][1])


def test_boundary_bazi_late_zi_rolls_the_day() -> None:
    before = _golden("bazi", "B_late_001")  # 22:59
    after = _golden("bazi", "B_late_002")  # 23:00
    result_before = _compute("bazi", before)
    result_after = _compute("bazi", after)

    day_before, day_after = result_before["pillars"][2], result_after["pillars"][2]
    hour_before, hour_after = result_before["pillars"][3], result_after["pillars"][3]
    assert _pillar(day_before) != _pillar(day_after), "23:00 must roll the day pillar"
    assert hour_before["branch"] == "亥" and hour_after["branch"] == "子"
    assert _pillar(day_after) == _pillar(after["expected"]["day_pillar"])


def test_boundary_ziwei_hour_window_changes_fate_palace() -> None:
    before = _golden("ziwei", "ZV-hour-001")  # 22:59 亥时末
    after = _golden("ziwei", "ZV-hour-002")  # 23:00 子时初
    result_before = _compute("ziwei", before)
    result_after = _compute("ziwei", after)

    assert result_before["fate_palace_index"] == before["expected"]["chart"]["fate_palace_index"]
    assert result_after["fate_palace_index"] == after["expected"]["chart"]["fate_palace_index"]
    assert abs(
        result_before["fate_palace_index"] - result_after["fate_palace_index"]
    ) == 1, "the 23:00 hour window must move the fate palace by one"


def test_boundary_ziwei_leap_month_is_flagged() -> None:
    vector = _golden("ziwei", "ZV-lun-003")  # 2023-03-22, leap second month
    expected = vector["expected"]["chart"]
    result = _compute("ziwei", vector)

    assert result["calendar_note"] == expected["calendar_note"]
    assert result["calendar_note"] and "leap month 2" in result["calendar_note"]
    assert result["wuxing_ju"] == expected["wuxing_ju"]


def test_boundary_qimen_solstice_switches_dun() -> None:
    before = _golden("qimen", "B_summer_before")
    after = _golden("qimen", "B_summer_after")
    result_before = _compute("qimen", before)
    result_after = _compute("qimen", after)

    assert (result_before["dun_type"], result_before["solar_term"]) == ("yang", "芒种")
    assert (result_after["dun_type"], result_after["solar_term"]) == ("yin", "夏至")
    assert result_before["ju"] == before["expected_board"]["ju"]
    assert result_after["ju"] == after["expected_board"]["ju"]


def test_boundary_liuyao_rejects_invalid_casts() -> None:
    for vector_id in ("LY_inv_001", "LY_inv_002", "LY_inv_003"):
        vector = _golden("liuyao", vector_id)
        response = client.post("/agents/liuyao/compute", json=_api_body("liuyao", vector))
        assert response.status_code == 422, vector_id
        assert response.json()["error"]["kind"] == "invalid_request", vector_id


def test_boundary_liuyao_all_changing_lines() -> None:
    vector = _golden("liuyao", "LY_norm_003")  # all nine -> 乾 changing to 坤
    expected = vector["expected"]
    result = _compute("liuyao", vector)

    assert all(line["is_changing"] for line in result["original"])
    assert result["changed_hexagram"] == expected["changed_hexagram"] == 2


# == EVIDENCE: existence, exact source, applicability ==


def test_evidence_explain_citations_are_traceable_and_applicable() -> None:
    payload = {
        "request_id": "eval-evidence-bazi",
        "born_at": BORN,
        "gender": "male",
        "question": QUESTION,
    }
    response = client.post("/agents/bazi/compute?explain=true", json=payload)
    assert response.status_code == 200
    data = response.json()
    citations = data["explain"]["knowledge"]
    assert citations, "the explain chain must return citations"

    index = _corpus_index()
    output = agent_output_from_envelope(data)
    query = get_explainer_for("bazi").build_query(output)
    recalled = {chunk.id for chunk in get_retriever().retrieve(query, k=10**6)}

    for citation in citations:
        assert citation["id"] in index, f"citation not in frozen corpora: {citation['id']}"
        kind, entry = index[citation["id"]]
        assert kind == "node", f"explain must cite nodes, got {kind}"
        assert citation["source"] == _source_label(entry), "source label must be exact"
        assert "bazi" in entry.get("systems", []), "citation must apply to the bazi domain"
        assert citation["id"] in recalled, "citation must be recalled by the explain query"


@pytest.mark.parametrize(
    ("agent", "extra"),
    [
        ("bazi", {}),
        ("ziwei", {}),
        ("qimen", {}),
        ("liuyao", {"casts": [7, 7, 7, 7, 7, 7]}),
    ],
)
def test_evidence_explain_citations_stay_in_domain(agent: str, extra: dict[str, Any]) -> None:
    payload = {
        "request_id": f"eval-domain-{agent}",
        "born_at": BORN,
        "gender": "male",
        "question": QUESTION,
        **extra,
    }
    response = client.post(f"/agents/{agent}/compute?explain=true", json=payload)
    assert response.status_code == 200
    citations = response.json()["explain"]["knowledge"]
    assert citations, f"{agent}: the explain chain must return citations"

    index = _corpus_index()
    for citation in citations:
        _, entry = index[citation["id"]]
        assert agent in entry.get("systems", []), (
            f"{agent} explanation cites {citation['id']} from {entry.get('systems')}"
        )


def test_evidence_references_support_existing_nodes() -> None:
    response = client.post(
        "/knowledge/search", json={"query": "帝座", "k": 6, "include_evidence": True}
    )
    assert response.status_code == 200
    references = [c for c in response.json()["chunks"] if c["id"].startswith("ref:")]
    assert references, "the query must recall at least one reference"

    index = _corpus_index()
    for chunk in references:
        kind, entry = index[chunk["id"]]
        assert kind == "reference"
        assert chunk["text"] == entry["passage"], "citation text must be the verbatim passage"
        assert chunk["source"] == _source_label(entry)
        assert entry["target_type"] == "node"
        target_kind, _ = index[entry["target_id"]]
        assert target_kind == "node", "reference must point at an existing node"


# == EXPLAIN: fidelity to computed facts ==


def test_explain_bazi_restates_computed_facts() -> None:
    payload = {
        "request_id": "eval-explain-bazi",
        "born_at": BORN,
        "gender": "male",
        "question": QUESTION,
    }
    data = client.post("/agents/bazi/compute?explain=true", json=payload).json()
    result = data["result"]
    text = data["explain"]["explanation"]

    day_master = re.search(r"日主【(.+?)】", text)
    month_pillar = re.search(r"生于【(.+?)】", text)
    assert day_master and day_master.group(1) == result["day_master"]
    assert month_pillar and month_pillar.group(1) == (
        result["pillars"][1]["stem"] + result["pillars"][1]["branch"]
    )

    assert data["explain"]["evidence"]["result"] == result
    assert data["explain"]["evidence"]["input_hash"] == data["input_hash"]
    assert data["explain"]["degraded"] is True
    assert data["explain"]["provider"] is None
    for citation in data["explain"]["knowledge"]:
        assert citation["source"] in text, "every citation must appear in the prose"


def test_explain_ziwei_restates_computed_facts() -> None:
    payload = {
        "request_id": "eval-explain-ziwei",
        "born_at": BORN,
        "gender": "male",
        "question": QUESTION,
    }
    data = client.post("/agents/ziwei/compute?explain=true", json=payload).json()
    result = data["result"]
    text = data["explain"]["explanation"]

    wuxing_ju = re.search(r"为(.+?局)", text)
    assert wuxing_ju and wuxing_ju.group(1) == result["wuxing_ju"]
    assert data["explain"]["evidence"]["result"] == result
    for citation in data["explain"]["knowledge"]:
        assert citation["source"] in text


def test_explain_bazi_reports_the_current_dayun() -> None:
    payload = {
        "request_id": "eval-explain-dayun",
        "born_at": BORN,
        "gender": "male",
    }
    data = client.post("/agents/bazi/compute?explain=true", json=payload).json()
    text = data["explain"]["explanation"]
    computed_at = datetime.fromisoformat(data["computed_at"])
    dayun = data["result"]["dayun"]
    started = [d for d in dayun if datetime.fromisoformat(d["start_at"]) <= computed_at]
    assert started, "the computation instant must fall inside the dayun sequence"

    expected = started[-1]
    parsed = re.search(r"当前大运【(.+?)】", text)
    assert parsed, "the fallback must state the current dayun"
    assert parsed.group(1) == expected["stem"] + expected["branch"]
    assert parsed.group(1) != dayun[0]["stem"] + dayun[0]["branch"], (
        "must not report the childhood step as the current dayun"
    )


def test_explain_ziwei_reports_palace_locations() -> None:
    payload = {
        "request_id": "eval-explain-ziwei-location",
        "born_at": BORN,
        "gender": "male",
    }
    data = client.post("/agents/ziwei/compute?explain=true", json=payload).json()
    text = data["explain"]["explanation"]
    palaces = data["result"]["palaces"]
    fate = next(p for p in palaces if p["is_fate_palace"])
    body = next(p for p in palaces if p["is_body_palace"])

    assert f"命宫在{fate['earthly_branch']}宫" in text
    assert "命宫在命宫" not in text, "palace location must not repeat the palace name"
    assert f"身宫在{body['name']}宫（{body['earthly_branch']}）" in text
    assert "入庙" not in text, "brightness (庙旺) is not computed and must not be claimed"


# == CONSENSUS: support / conflict / empty & missing evidence ==


def _evidence(
    evidence_id: str,
    conclusion: str,
    confidence: float,
    system: str,
) -> dict[str, Any]:
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
                "source_id": f"rule:{evidence_id}",
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


def _consensus(evidence: list[dict[str, Any]], strategy: str = "retain_all") -> dict[str, Any]:
    response = client.post(
        "/consensus/evidence",
        json={"evidence": evidence, "config": {"strategy": strategy}},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_consensus_support_uses_cross_system_bonus() -> None:
    report = _consensus(
        [
            _evidence("s1", "晋升", 0.6, "bazi"),
            _evidence("s2", "晋升", 0.7, "ziwei"),
        ]
    )
    assert len(report["conclusions"]) == 1
    conclusion = report["conclusions"][0]
    # max(0.6, 0.7) + default 0.1 bonus for the second system == 0.8
    assert conclusion["confidence"] == pytest.approx(0.8)
    assert conclusion["systems"] == ["bazi", "ziwei"]
    assert conclusion["evidence_count"] == 2
    assert report["conflicts"] == []


def test_consensus_conflict_strategy_is_explicit() -> None:
    evidence = [
        _evidence("c1", "晋升", 0.8, "bazi"),
        _evidence("c2", "降职", 0.5, "ziwei"),
    ]

    retain = _consensus(evidence, "retain_all")
    assert {c["conclusion"] for c in retain["conclusions"]} == {"晋升", "降职"}
    assert all(c["is_conflict"] for c in retain["conclusions"])
    assert retain["conflicts"] == []

    highest = _consensus(evidence, "highest_confidence")
    assert [c["conclusion"] for c in highest["conclusions"]] == ["晋升"]
    assert [c["conclusion"] for c in highest["conflicts"]] == ["降职"]


def test_consensus_majority_prefers_more_evidence() -> None:
    report = _consensus(
        [
            _evidence("m1", "晋升", 0.6, "bazi"),
            _evidence("m2", "晋升", 0.6, "ziwei"),
            _evidence("m3", "降职", 0.9, "qimen"),
        ],
        "majority",
    )
    assert [c["conclusion"] for c in report["conclusions"]] == ["晋升"]
    assert [c["conclusion"] for c in report["conflicts"]] == ["降职"]


def test_consensus_empty_and_missing_evidence() -> None:
    empty = _consensus([])
    assert empty["conclusions"] == [] and empty["overall_confidence"] == 0.0

    # a single system cannot produce cross-modal consensus: no synthesis, no crash
    response = client.post(
        "/orchestrate",
        json={
            "request_id": "eval-single-agent",
            "payload": {
                "request_id": "eval-single-agent",
                "born_at": BORN,
                "gender": "male",
            },
            "agents": ["bazi"],
            "explain": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["errors"] == []
    assert [o["agent"] for o in data["outputs"]] == ["bazi"]
    assert data["consensus"] is None, "cross-modal consensus requires at least two outputs"


# == UNDETERMINED: recorded, never asserted as domain truth ==


def test_undetermined_cases_reference_existing_artifacts() -> None:
    assert UNDETERMINED_CASES, "school-dependent cases must be recorded, not hidden"
    for case in UNDETERMINED_CASES:
        assert (ROOT / case["artifact"]).is_file(), f"stale artifact: {case['case']}"
