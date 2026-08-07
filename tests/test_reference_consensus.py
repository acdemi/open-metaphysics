"""Golden tests for the Reference Consensus Layer (Phase 6B Sprint 5)."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from reference.consensus import (
    ConsensusConclusion,
    ConsensusConfig,
    ConsensusInput,
    ConsensusReport,
    ConsensusStrategy,
    make_conclusion_id,
)
from reference.consensus_behavior import ConsensusBehavior
from reference.consensus_builder import (
    CONSENSUS_CONTRACT_PATH,
    ConsensusBuilder,
    export_consensus_contract,
)
from reference.evidence import Evidence, EvidenceItem, EvidenceType
from reference.models import Domain, ResultDirection


def _mi(
    item_id="ev:bazi:id",
    st=EvidenceType.RULE,
    sid="rule:bazi:d:v1",
    sys="bazi",
    dom=Domain.PERSONALITY,
    conf=0.9,
    conc="c",
    dr=ResultDirection.POSITIVE,
):
    return EvidenceItem(
        evidence_id=item_id,
        source_type=st,
        source_id=sid,
        system=sys,
        domain=dom,
        confidence=conf,
        conclusion=conc,
        direction=dr,
        weight=0.8,
        trace=[sid],
    )


def _me(
    ev_id="ev:test:e",
    dom=Domain.PERSONALITY,
    conc="c",
    conf=0.9,
    sys="bazi",
    dr=ResultDirection.POSITIVE,
):
    s = ev_id.split(":")[-1]
    return Evidence(
        evidence_id=ev_id,
        domain=dom,
        conclusion=conc,
        confidence=conf,
        system=sys,
        items=[
            _mi(
                item_id=f"ev:{sys}:{s}_i",
                sid=f"rule:{sys}:{s}:v1",
                sys=sys,
                dom=dom,
                conf=conf,
                conc=conc,
                dr=dr,
            )
        ],
    )


class TestConsensusInput:
    def test_input_accepts_evidence(self):
        ev = _me()
        inp = ConsensusInput(evidence=[ev])
        assert len(inp.evidence) == 1

    def test_input_rejects_non_evidence(self):
        with pytest.raises(ValidationError):
            ConsensusInput(evidence=[{"invalid": "x"}])

    def test_input_default_config(self):
        inp = ConsensusInput(evidence=[])
        assert inp.config.strategy == ConsensusStrategy.RETAIN_ALL
        assert inp.config.cross_system_bonus_per_system == 0.1

    def test_input_custom_config(self):
        cfg = ConsensusConfig(strategy=ConsensusStrategy.HIGHEST_CONFIDENCE)
        inp = ConsensusInput(evidence=[], config=cfg)
        assert inp.config.strategy == ConsensusStrategy.HIGHEST_CONFIDENCE

    def test_input_extra_rejected(self):
        with pytest.raises(ValidationError):
            ConsensusInput(evidence=[], extra=1)


class TestConsensusConfig:
    def test_config_defaults(self):
        cfg = ConsensusConfig()
        assert cfg.strategy == ConsensusStrategy.RETAIN_ALL
        assert cfg.cross_system_bonus_per_system == 0.1
        assert cfg.max_cross_system_bonus == 0.3

    def test_config_strategy_values(self):
        for s in ConsensusStrategy:
            assert ConsensusConfig(strategy=s).strategy == s

    def test_config_bounds(self):
        with pytest.raises(ValidationError):
            ConsensusConfig(cross_system_bonus_per_system=1.5)
        with pytest.raises(ValidationError):
            ConsensusConfig(max_cross_system_bonus=-0.1)

    def test_config_extra_rejected(self):
        with pytest.raises(ValidationError):
            ConsensusConfig(unknown=42)


class TestConsensusConclusion:
    def test_creation(self):
        cc = ConsensusConclusion(
            conclusion_id="cc:p:abc",
            domain=Domain.PERSONALITY,
            conclusion="t",
            confidence=0.9,
            evidence_ids=["ev:1"],
            evidence_count=1,
            systems=["bazi"],
        )
        assert cc.confidence == pytest.approx(0.9)
        assert cc.is_conflict is False

    def test_serialization(self):
        cc = ConsensusConclusion(
            conclusion_id="cc:p:abc",
            domain=Domain.PERSONALITY,
            conclusion="t",
            confidence=0.9,
            evidence_ids=["ev:1"],
            evidence_count=1,
            systems=["bazi"],
        )
        j = json.loads(cc.model_dump_json())
        assert j["conclusion_id"] == "cc:p:abc"
        assert j["is_conflict"] is False

    def test_id_deterministic(self):
        i1 = make_conclusion_id("p", "t", ["ev:1", "ev:2"])
        i2 = make_conclusion_id("p", "t", ["ev:2", "ev:1"])
        assert i1 == i2

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            ConsensusConclusion(
                conclusion_id="cc:x:y", domain=Domain.OVERALL, conclusion="x", confidence=1.5
            )


class TestConsensusReport:
    def test_creation(self):
        r = ConsensusReport(
            report_id="cr:abc",
            overall_confidence=0.85,
            domains=[Domain.PERSONALITY],
            conclusions=[],
            conflicts=[],
            evidence_ids=["ev:1"],
        )
        assert r.overall_confidence == pytest.approx(0.85)

    def test_serialization(self):
        r = ConsensusReport(report_id="cr:x", overall_confidence=0.0)
        j = json.loads(r.model_dump_json())
        for f in [
            "report_id",
            "overall_confidence",
            "domains",
            "conclusions",
            "conflicts",
            "evidence_ids",
            "metadata",
            "version",
        ]:
            assert f in j

    def test_empty(self):
        r = ConsensusReport(report_id="cr:e", overall_confidence=0.0)
        assert r.conclusions == []
        assert r.conflicts == []


class TestConsensusBuilderBasic:
    def setup_method(self):
        self.b = ConsensusBuilder()

    def test_single_evidence(self):
        ev = _me(ev_id="ev:t:s1", conc="A", conf=0.9)
        r = self.b.build(ConsensusInput(evidence=[ev]))
        assert len(r.conclusions) == 1
        assert r.conclusions[0].confidence == pytest.approx(0.9)
        assert r.conclusions[0].is_conflict is False

    def test_multiple_different_domains(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:m1", dom=Domain.PERSONALITY, conc="A"),
                    _me(ev_id="ev:t:m2", dom=Domain.CAREER, conc="B"),
                ]
            )
        )
        assert len(r.conclusions) == 2
        assert len(r.domains) == 2

    def test_empty_input(self):
        r = self.b.build(ConsensusInput(evidence=[]))
        assert len(r.conclusions) == 0
        assert r.overall_confidence == 0.0

    def test_dedup_evidence(self):
        ev = _me(ev_id="ev:t:d1", conc="A")
        r = self.b.build(ConsensusInput(evidence=[ev, ev]))
        assert len(r.evidence_ids) == 1
        assert r.metadata["total_evidence"] == 1

    def test_groups_by_domain_conclusion(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:g1", conc="same", conf=0.8),
                    _me(ev_id="ev:t:g2", conc="same", conf=0.9),
                ]
            )
        )
        assert len(r.conclusions) == 1
        assert r.conclusions[0].evidence_count == 2
        assert r.conclusions[0].confidence == pytest.approx(0.9)

    def test_confidence_aggregation(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:c1", conf=0.7, conc="x"),
                    _me(ev_id="ev:t:c2", conf=0.95, conc="x"),
                ]
            )
        )
        assert r.conclusions[0].confidence == pytest.approx(0.95)

    def test_evidence_ids_sorted(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:zz", conc="x"),
                    _me(ev_id="ev:t:aa", conc="y"),
                ]
            )
        )
        assert r.evidence_ids == ["ev:t:aa", "ev:t:zz"]

    def test_overall_confidence(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:o1", dom=Domain.PERSONALITY, conc="A", conf=0.8),
                    _me(ev_id="ev:t:o2", dom=Domain.CAREER, conc="B", conf=0.9),
                ]
            )
        )
        assert r.overall_confidence == pytest.approx(0.85, abs=0.01)


class TestConflictStrategies:
    def setup_method(self):
        self.b = ConsensusBuilder()
        self.a = _me(ev_id="ev:t:ca", dom=Domain.PERSONALITY, conc="gang", conf=0.9)
        self.b2 = _me(ev_id="ev:t:cb", dom=Domain.PERSONALITY, conc="rouan", conf=0.8)

    def test_retain_all_keeps_all(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[self.a, self.b2],
                config=ConsensusConfig(strategy=ConsensusStrategy.RETAIN_ALL),
            )
        )
        assert len(r.conclusions) == 2
        assert len(r.conflicts) == 0

    def test_retain_all_marks_conflict(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[self.a, self.b2],
                config=ConsensusConfig(strategy=ConsensusStrategy.RETAIN_ALL),
            )
        )
        assert all(cc.is_conflict for cc in r.conclusions)

    def test_retain_all_no_drop(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[self.a, self.b2],
                config=ConsensusConfig(strategy=ConsensusStrategy.RETAIN_ALL),
            )
        )
        assert len(r.conflicts) == 0

    def test_highest_keeps_winner(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[self.a, self.b2],
                config=ConsensusConfig(strategy=ConsensusStrategy.HIGHEST_CONFIDENCE),
            )
        )
        assert len(r.conclusions) == 1
        assert r.conclusions[0].conclusion == "gang"

    def test_highest_drops_loser(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[self.a, self.b2],
                config=ConsensusConfig(strategy=ConsensusStrategy.HIGHEST_CONFIDENCE),
            )
        )
        assert len(r.conflicts) == 1
        assert r.conflicts[0].conclusion == "rouan"

    def test_highest_tie_break(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:tx", dom=Domain.HEALTH, conc="BBB", conf=0.8),
                    _me(ev_id="ev:t:ty", dom=Domain.HEALTH, conc="AAA", conf=0.8),
                ],
                config=ConsensusConfig(strategy=ConsensusStrategy.HIGHEST_CONFIDENCE),
            )
        )
        assert r.conclusions[0].conclusion == "AAA"

    def test_majority_keeps_majority(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    self.a,
                    _me(ev_id="ev:t:ca2", dom=Domain.PERSONALITY, conc="gang", conf=0.7),
                    self.b2,
                ],
                config=ConsensusConfig(strategy=ConsensusStrategy.MAJORITY),
            )
        )
        assert len(r.conclusions) == 1
        assert r.conclusions[0].conclusion == "gang"
        assert r.conclusions[0].evidence_count == 2

    def test_majority_drops_minority(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    self.a,
                    _me(ev_id="ev:t:ca2b", dom=Domain.PERSONALITY, conc="gang", conf=0.7),
                    self.b2,
                ],
                config=ConsensusConfig(strategy=ConsensusStrategy.MAJORITY),
            )
        )
        assert len(r.conflicts) == 1
        assert r.conflicts[0].conclusion == "rouan"

    def test_majority_tie_break_confidence(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:mtx", dom=Domain.WEALTH, conc="X", conf=0.7),
                    _me(ev_id="ev:t:mty", dom=Domain.WEALTH, conc="Y", conf=0.9),
                ],
                config=ConsensusConfig(strategy=ConsensusStrategy.MAJORITY),
            )
        )
        assert r.conclusions[0].conclusion == "Y"


class TestCrossSystemBonus:
    def setup_method(self):
        self.b = ConsensusBuilder()

    def test_no_bonus_single_system(self):
        r = self.b.build(
            ConsensusInput(evidence=[_me(ev_id="ev:t:ss", conc="x", conf=0.85, sys="bazi")])
        )
        cc = r.conclusions[0]
        assert cc.metadata["cross_system_bonus"] == 0.0
        assert cc.confidence == pytest.approx(0.85)

    def test_bonus_multi_system(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:ms1", conc="x", conf=0.85, sys="bazi"),
                    _me(ev_id="ev:t:ms2", conc="x", conf=0.80, sys="ziwei"),
                ]
            )
        )
        cc = r.conclusions[0]
        assert cc.metadata["system_count"] == 2
        assert cc.metadata["cross_system_bonus"] == pytest.approx(0.1)
        assert cc.confidence == pytest.approx(0.95)

    def test_bonus_capped(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id=f"ev:t:cap{s}", conc="x", conf=0.5, sys=s)
                    for s in ["bazi", "ziwei", "qimen", "liuyao", "meihua"]
                ]
            )
        )
        cc = r.conclusions[0]
        assert cc.metadata["cross_system_bonus"] == pytest.approx(0.3)
        assert cc.confidence == pytest.approx(0.8)

    def test_bonus_configurable(self):
        cfg = ConsensusConfig(cross_system_bonus_per_system=0.2, max_cross_system_bonus=0.5)
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:cf1", conc="x", conf=0.8, sys="bazi"),
                    _me(ev_id="ev:t:cf2", conc="x", conf=0.8, sys="ziwei"),
                ],
                config=cfg,
            )
        )
        assert r.conclusions[0].metadata["cross_system_bonus"] == pytest.approx(0.2)
        assert r.conclusions[0].confidence == pytest.approx(1.0)

    def test_bonus_zero_disabled(self):
        cfg = ConsensusConfig(cross_system_bonus_per_system=0.0)
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:dz1", conc="x", conf=0.8, sys="bazi"),
                    _me(ev_id="ev:t:dz2", conc="x", conf=0.8, sys="ziwei"),
                ],
                config=cfg,
            )
        )
        assert r.conclusions[0].metadata["cross_system_bonus"] == 0.0


class TestSorting:
    def setup_method(self):
        self.b = ConsensusBuilder()

    def test_domain_sorting(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:d1", dom=Domain.WEALTH, conc="A"),
                    _me(ev_id="ev:t:d2", dom=Domain.CAREER, conc="B"),
                    _me(ev_id="ev:t:d3", dom=Domain.PERSONALITY, conc="C"),
                ]
            )
        )
        dv = [d.value for d in r.domains]
        assert dv == sorted(dv)

    def test_conclusion_by_domain(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:cs1", dom=Domain.WEALTH, conc="Z"),
                    _me(ev_id="ev:t:cs2", dom=Domain.CAREER, conc="A"),
                ]
            )
        )
        assert r.conclusions[0].domain == Domain.CAREER

    def test_conclusion_by_confidence(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:cf1", dom=Domain.HEALTH, conc="lo", conf=0.7),
                    _me(ev_id="ev:t:cf2", dom=Domain.HEALTH, conc="hi", conf=0.9),
                ],
                config=ConsensusConfig(strategy=ConsensusStrategy.RETAIN_ALL),
            )
        )
        assert r.conclusions[0].confidence >= r.conclusions[1].confidence

    def test_conclusion_by_text(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:ct1", dom=Domain.FAMILY, conc="ZZZ", conf=0.8),
                    _me(ev_id="ev:t:ct2", dom=Domain.FAMILY, conc="AAA", conf=0.8),
                ],
                config=ConsensusConfig(strategy=ConsensusStrategy.RETAIN_ALL),
            )
        )
        assert r.conclusions[0].conclusion == "AAA"

    def test_evidence_id_sorting(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id=f"ev:t:e{i}", dom=Domain.OVERALL, conc=f"C{i}")
                    for i in range(5, 0, -1)
                ],
                config=ConsensusConfig(strategy=ConsensusStrategy.RETAIN_ALL),
            )
        )
        assert r.evidence_ids == sorted(r.evidence_ids)


class TestDeterminism:
    def setup_method(self):
        self.b = ConsensusBuilder()

    def test_deterministic_build(self):
        evs = [
            _me(ev_id="ev:t:d1", conc="A", conf=0.9),
            _me(ev_id="ev:t:d2", dom=Domain.CAREER, conc="B", conf=0.8),
        ]
        r1 = self.b.build(ConsensusInput(evidence=evs))
        r2 = self.b.build(ConsensusInput(evidence=evs))
        assert r1.model_dump_json() == r2.model_dump_json()

    def test_deterministic_json(self):
        r = self.b.build(ConsensusInput(evidence=[_me(ev_id="ev:t:dj", conc="x")]))
        assert r.model_dump_json() == r.model_dump_json()

    def test_deterministic_conclusion_id(self):
        evs = [_me(ev_id="ev:t:dc1", conc="x", conf=0.9), _me(ev_id="ev:t:dc2", conc="x", conf=0.8)]
        r1 = self.b.build(ConsensusInput(evidence=evs))
        r2 = self.b.build(ConsensusInput(evidence=list(reversed(evs))))
        assert r1.conclusions[0].conclusion_id == r2.conclusions[0].conclusion_id

    def test_deterministic_report_id(self):
        evs = [_me(ev_id="ev:t:dr", conc="x")]
        r1 = self.b.build(ConsensusInput(evidence=evs))
        r2 = self.b.build(ConsensusInput(evidence=evs))
        assert r1.report_id == r2.report_id

    def test_deterministic_across_strategies(self):
        evs = [
            _me(ev_id="ev:t:das1", dom=Domain.PERSONALITY, conc="A", conf=0.9),
            _me(ev_id="ev:t:das2", dom=Domain.PERSONALITY, conc="B", conf=0.8),
        ]
        for s in ConsensusStrategy:
            r1 = self.b.build(ConsensusInput(evidence=evs, config=ConsensusConfig(strategy=s)))
            r2 = self.b.build(ConsensusInput(evidence=evs, config=ConsensusConfig(strategy=s)))
            assert r1.model_dump_json() == r2.model_dump_json()


class TestEdgeCases:
    def setup_method(self):
        self.b = ConsensusBuilder()

    def test_null_direction(self):
        r = self.b.build(ConsensusInput(evidence=[_me(ev_id="ev:t:nd", conc="x", dr=None)]))
        assert r.conclusions[0].direction is None

    def test_single_no_conflict(self):
        r = self.b.build(ConsensusInput(evidence=[_me(ev_id="ev:t:sc", conc="only")]))
        assert r.conclusions[0].is_conflict is False

    def test_same_domain_diff_conclusion_conflict(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[_me(ev_id="ev:t:sd1", conc="A"), _me(ev_id="ev:t:sd2", conc="B")]
            )
        )
        assert all(cc.is_conflict for cc in r.conclusions)

    def test_diff_domain_same_conclusion_no_conflict(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:cd1", conc="same"),
                    _me(ev_id="ev:t:cd2", dom=Domain.CAREER, conc="same"),
                ]
            )
        )
        assert all(not cc.is_conflict for cc in r.conclusions)

    def test_all_same_system_no_bonus(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id=f"ev:t:as{i}", conc="x", conf=0.8, sys="bazi") for i in range(3)
                ]
            )
        )
        assert r.conclusions[0].metadata["system_count"] == 1
        assert r.conclusions[0].metadata["cross_system_bonus"] == 0.0


class TestContract:
    def test_structure(self):
        c = export_consensus_contract()
        assert c["contract_name"] == "consensus"
        assert c["contract_version"] == "1.0.0"
        assert "ConsensusInput" in c["models"]
        assert "ConsensusReport" in c["models"]
        assert "golden_examples" in c

    def test_determinism(self):
        c1 = export_consensus_contract()
        c2 = export_consensus_contract()
        assert c1 == c2

    def test_file_matches_runtime(self):
        with open(CONSENSUS_CONTRACT_PATH, encoding="utf-8") as f:
            fc = json.load(f)
        assert fc == export_consensus_contract()

    def test_golden_examples(self):
        c = export_consensus_contract()
        assert len(c["golden_examples"]) >= 6
        for ex in c["golden_examples"]:
            assert "name" in ex
            assert "report" in ex

    def test_strategies(self):
        c = export_consensus_contract()
        assert set(c["strategies"]) == {"retain_all", "highest_confidence", "majority"}


class TestBehaviorVerification:
    def setup_method(self):
        self.b = ConsensusBuilder()

    def test_verify_determinism(self):
        ev = _me(ev_id="ev:t:bv", conc="x")
        assert ConsensusBehavior.verify_determinism(self.b, ConsensusInput(evidence=[ev]))

    def test_verify_sorting(self):
        r = self.b.build(
            ConsensusInput(
                evidence=[
                    _me(ev_id="ev:t:bvs1", dom=Domain.WEALTH, conc="A"),
                    _me(ev_id="ev:t:bvs2", dom=Domain.CAREER, conc="B"),
                ]
            )
        )
        assert ConsensusBehavior.verify_conclusion_sorting(r.conclusions)
        assert ConsensusBehavior.verify_domain_sorting(r)

    def test_verify_empty_input(self):
        assert ConsensusBehavior.verify_empty_input(self.b)

    def test_verify_no_reasoning_methods(self):
        assert ConsensusBehavior.verify_no_reasoning_methods()

    def test_full_audit(self):
        audit = ConsensusBehavior.audit(self.b)
        for k, v in audit.items():
            assert v is True, f"Audit failed for {k}"


class TestArchitectureBoundary:
    def test_no_reasoning_methods(self):
        forbidden = [
            "reason",
            "conclude",
            "evaluate_rule",
            "evaluate",
            "match_pattern",
            "query_knowledge",
            "call_llm",
            "run_rule",
            "infer",
        ]
        for n in forbidden:
            assert not hasattr(ConsensusBuilder, n), f"Forbidden: {n}"

    def test_input_only_evidence(self):
        assert ConsensusBehavior.verify_input_only_accepts_evidence()

    def test_does_not_modify_evidence(self):
        ev = _me(ev_id="ev:t:ab", conc="x", conf=0.9)
        orig = ev.model_dump_json()
        ConsensusBuilder().build(ConsensusInput(evidence=[ev]))
        assert ev.model_dump_json() == orig

    def test_methods_consensus_only(self):
        methods = {m for m in dir(ConsensusBuilder) if not m.startswith("__")}
        assert "build" in methods
        forbidden = {"evaluate_rule", "match_pattern", "query_knowledge", "call_llm"}
        assert not (methods & forbidden)


class TestJSONSerialization:
    def setup_method(self):
        self.b = ConsensusBuilder()

    def test_report_roundtrip(self):
        r = self.b.build(ConsensusInput(evidence=[_me(ev_id="ev:t:js1", conc="x")]))
        r2 = ConsensusReport.model_validate_json(r.model_dump_json())
        assert r2.report_id == r.report_id
        assert len(r2.conclusions) == len(r.conclusions)

    def test_conclusion_roundtrip(self):
        r = self.b.build(ConsensusInput(evidence=[_me(ev_id="ev:t:js2", conc="x")]))
        cc = r.conclusions[0]
        cc2 = ConsensusConclusion.model_validate_json(cc.model_dump_json())
        assert cc2.conclusion_id == cc.conclusion_id

    def test_null_fields_serialized(self):
        r = self.b.build(ConsensusInput(evidence=[_me(ev_id="ev:t:js3", conc="x", dr=None)]))
        j = json.loads(r.model_dump_json())
        assert j["conclusions"][0]["direction"] is None
