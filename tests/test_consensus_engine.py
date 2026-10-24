"""Production Consensus Layer — engine + contract adapter tests.

Covers the frozen Consensus contract v1.0.0 observable behavior
(CS-001 ~ CS-025) on the Production Runtime side.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from openmetaphysics.consensus import (
    ConsensusEngine,
    ConsensusInput,
    ConsensusStrategy,
    Domain,
)
from openmetaphysics.contracts.consensus_contract import ConsensusContractAdapter

REPO_ROOT = Path(__file__).resolve().parents[1]


def _item(eid: str, system: str, domain: str, conclusion: str, conf: float, direction=None):
    return {
        "evidence_id": eid,
        "source_type": "rule",
        "source_id": f"rule:{eid}",
        "system": system,
        "domain": domain,
        "confidence": conf,
        "conclusion": conclusion,
        "direction": direction,
        "weight": 1.0,
        "trace": [],
        "metadata": {},
        "timestamp": None,
        "version": "1.0.0",
    }


def _evidence(eid: str, system: str, domain: str, conclusion: str, conf: float, direction=None):
    return {
        "evidence_id": eid,
        "domain": domain,
        "conclusion": conclusion,
        "confidence": conf,
        "system": system,
        "items": [_item(f"{eid}#i1", system, domain, conclusion, conf, direction)],
        "version": "1.0.0",
    }


def _build(evidence: list[dict], strategy: str = "retain_all", **cfg):
    payload = {
        "evidence": evidence,
        "config": {"strategy": strategy, **cfg},
    }
    return ConsensusEngine().build(ConsensusInput(**payload))


# == Basic behavior ==


def test_empty_input_produces_empty_report():
    report = _build([])
    assert report.conclusions == []
    assert report.conflicts == []
    assert report.domains == []
    assert report.evidence_ids == []
    assert report.overall_confidence == 0.0
    assert report.report_id.startswith("cr:")
    assert report.metadata["total_evidence"] == 0


def test_single_evidence_produces_one_conclusion():
    ev = _evidence("ev:personality:a", "bazi", "personality", "性格刚毅", 0.9)
    report = _build([ev])
    assert len(report.conclusions) == 1
    cc = report.conclusions[0]
    assert cc.conclusion == "性格刚毅"
    assert cc.confidence == 0.9
    assert cc.evidence_count == 1
    assert cc.systems == ["bazi"]
    assert cc.is_conflict is False
    assert cc.conclusion_id.startswith("cc:personality:")
    assert report.overall_confidence == 0.9


def test_duplicate_evidence_id_is_deduplicated():
    ev1 = _evidence("ev:dup:1", "bazi", "career", "上升", 0.4)
    ev2 = _evidence("ev:dup:1", "bazi", "career", "上升", 0.9)
    report = _build([ev1, ev2])
    assert report.metadata["total_evidence"] == 1
    assert report.evidence_ids == ["ev:dup:1"]
    # first occurrence wins
    assert report.conclusions[0].confidence == 0.4


def test_same_domain_conclusion_is_grouped():
    evs = [
        _evidence("ev:g1", "bazi", "career", "上升", 0.3),
        _evidence("ev:g2", "bazi", "career", "上升", 0.8),
    ]
    report = _build(evs)
    assert len(report.conclusions) == 1
    cc = report.conclusions[0]
    assert cc.evidence_ids == ["ev:g1", "ev:g2"]
    assert cc.evidence_count == 2
    assert cc.confidence == 0.8  # base = max, single system -> no bonus


def test_cross_system_bonus_applied_and_capped():
    evs = [
        _evidence("ev:b", "bazi", "career", "上升", 0.5),
        _evidence("ev:q", "qimen", "career", "上升", 0.5),
    ]
    report = _build(evs, cross_system_bonus_per_system=0.1, max_cross_system_bonus=0.5)
    assert report.conclusions[0].systems == ["bazi", "qimen"]
    assert report.conclusions[0].confidence == 0.6

    evs3 = evs + [_evidence("ev:z", "ziwei", "career", "上升", 0.5)]
    capped = _build(evs3, cross_system_bonus_per_system=0.3, max_cross_system_bonus=0.2)
    assert capped.conclusions[0].confidence == 0.7  # 0.5 + min(0.6, 0.2)


def test_confidence_clamped_by_config():
    evs = [_evidence("ev:c1", "bazi", "career", "上升", 0.95)]
    report = _build(evs, max_confidence=0.5)
    assert report.conclusions[0].confidence == 0.5

    report2 = _build(evs, min_confidence=0.99)
    assert report2.conclusions[0].confidence == 0.99


def test_direction_propagates_from_items():
    ev = _evidence("ev:d1", "bazi", "career", "上升", 0.6, direction="positive")
    assert _build([ev]).conclusions[0].direction == "positive"
    ev_none = _evidence("ev:d2", "bazi", "career", "上升", 0.6)
    assert _build([ev_none]).conclusions[0].direction is None


# == Conflict strategies ==


def _conflict_evidence():
    return [
        _evidence("ev:c_a", "bazi", "personality", "性格刚毅", 0.9),
        _evidence("ev:c_b", "ziwei", "personality", "性格柔顺", 0.8),
    ]


def test_retain_all_keeps_all_and_marks_conflict():
    report = _build(_conflict_evidence(), "retain_all")
    assert len(report.conclusions) == 2
    assert report.conflicts == []
    assert all(c.is_conflict for c in report.conclusions)


def test_highest_confidence_keeps_winner_and_drops_loser():
    report = _build(_conflict_evidence(), "highest_confidence")
    assert len(report.conclusions) == 1
    assert report.conclusions[0].conclusion == "性格刚毅"
    assert [c.conclusion for c in report.conflicts] == ["性格柔顺"]
    assert report.conclusions[0].is_conflict is True
    assert report.conflicts[0].is_conflict is True


def test_majority_keeps_conclusion_with_most_evidence():
    evs = [
        _evidence("ev:m1", "bazi", "career", "上升", 0.4),
        _evidence("ev:m2", "ziwei", "career", "上升", 0.4),
        _evidence("ev:m3", "qimen", "career", "下降", 0.9),
    ]
    report = _build(evs, "majority")
    assert len(report.conclusions) == 1
    assert report.conclusions[0].conclusion == "上升"
    assert report.conclusions[0].evidence_count == 2
    assert [c.conclusion for c in report.conflicts] == ["下降"]


def test_non_conflicting_domain_not_marked():
    evs = [
        _evidence("ev:n1", "bazi", "career", "上升", 0.6),
        _evidence("ev:n2", "bazi", "health", "健康", 0.7),
    ]
    report = _build(evs, "highest_confidence")
    assert report.conflicts == []
    assert all(c.is_conflict is False for c in report.conclusions)


# == Sorting / aggregation invariants ==


def test_domains_and_evidence_ids_sorted_and_overall_is_mean():
    evs = [
        _evidence("ev:z9", "bazi", "wealth", "财旺", 0.8),
        _evidence("ev:a1", "bazi", "career", "上升", 0.4),
    ]
    report = _build(evs)
    assert report.domains == [Domain.CAREER, Domain.WEALTH]
    assert report.evidence_ids == ["ev:a1", "ev:z9"]
    assert report.overall_confidence == round((0.4 + 0.8) / 2, 6)


def test_conclusions_sorted_by_domain_then_confidence_desc():
    evs = [
        _evidence("ev:s1", "bazi", "wealth", "财旺", 0.3),
        _evidence("ev:s2", "bazi", "career", "上升", 0.5),
        _evidence("ev:s3", "bazi", "career", "转行", 0.9),
    ]
    report = _build(evs, "retain_all")
    keys = [(c.domain.value, -c.confidence, c.conclusion) for c in report.conclusions]
    assert keys == sorted(keys)


def test_evidence_ids_include_dropped_evidence():
    report = _build(_conflict_evidence(), "highest_confidence")
    assert report.evidence_ids == ["ev:c_a", "ev:c_b"]


# == Determinism ==


def test_determinism_and_json_stability():
    evs = _conflict_evidence()
    r1 = _build(evs, "majority")
    r2 = _build(evs, "majority")
    assert r1.model_dump_json() == r2.model_dump_json()
    assert r1.report_id == r2.report_id


@pytest.mark.parametrize("strategy", [s.value for s in ConsensusStrategy])
def test_all_strategies_deterministic(strategy):
    out1 = _build(_conflict_evidence(), strategy).model_dump(mode="json")
    out2 = _build(_conflict_evidence(), strategy).model_dump(mode="json")
    assert json.dumps(out1, sort_keys=True) == json.dumps(out2, sort_keys=True)


# == Contract adapter ==


def test_manifest_and_contract_alignment():
    adapter = ConsensusContractAdapter()
    assert adapter.validate_manifest() == []
    assert adapter.validate_contract_alignment() == []
    assert adapter.validate_runtime_alignment() == []


def test_frozen_vectors_replay_byte_identical():
    result = ConsensusContractAdapter().validate_golden_vectors()
    assert result["errors"] == {}
    assert result["ok"] == result["total"] == 3


def test_validate_output_rejects_unsorted_report():
    adapter = ConsensusContractAdapter()
    bad = {
        "report_id": "cr:deadbeef",
        "overall_confidence": 0.5,
        "domains": ["wealth", "career"],
        "conclusions": [],
        "conflicts": [],
        "evidence_ids": ["ev:b", "ev:a"],
        "metadata": {},
        "version": "1.0.0",
    }
    errs = adapter.validate_output(bad)
    assert any("CS-011" in e for e in errs)
    assert any("CS-023" in e for e in errs)


# == Independence ==


def test_production_consensus_does_not_import_reference():
    """等价性必须建立在独立实现之上: Production 层不得导入 reference。"""
    pattern = re.compile(r"^\s*(?:from|import)\s+reference\b", re.MULTILINE)
    sources = sorted((REPO_ROOT / "src" / "openmetaphysics" / "consensus").glob("*.py"))
    assert sources, "consensus package not found"
    for path in sources:
        text = path.read_text(encoding="utf-8")
        assert not pattern.search(text), f"{path.name} imports reference"


def test_adapter_build_consensus_matches_frozen_vector():
    """ConsensusContractAdapter satisfies the RuntimeAdapter consensus method."""
    adapter = ConsensusContractAdapter()
    vector = adapter.load_vectors()[0]
    actual = adapter.build_consensus(
        json.dumps(vector["input"]["evidence"], ensure_ascii=False),
        json.dumps(vector["input"]["config"], ensure_ascii=False),
    )
    expected = json.dumps(vector["expected_output"], ensure_ascii=False, sort_keys=True)
    assert actual == expected
