"""Production ↔ Reference Consensus equivalence proof.

固定种子生成合法 Evidence 输入, 分别经:
1. Production Runtime (src/openmetaphysics/consensus, 独立实现, 只读导入)
2. Reference Runtime (reference/consensus_builder.py)

比较输出: 完整 ConsensusReport JSON (canonical form, 逐字节一致)。

本文件为等价对照脚本, 因此允许同时导入 src 与 reference —— 与
reference/tests/test_equivalence.py (Qimen) 同一范式。
Production 层的独立性由 tests/test_consensus_engine.py 的导入检查强制。
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from openmetaphysics.consensus import ConsensusEngine
from openmetaphysics.consensus import ConsensusInput as ProductInput
from reference.consensus import ConsensusInput as ReferenceInput
from reference.consensus_builder import ConsensusBuilder

ROOT = Path(__file__).resolve().parents[2]
VECTOR_PATH = ROOT / "reference" / "conformance" / "golden" / "consensus_vectors.json"

SYSTEMS = ["bazi", "ziwei", "qimen", "liuyao"]
DOMAINS = [
    "career",
    "personality",
    "marriage",
    "health",
    "wealth",
    "education",
    "family",
    "travel",
    "legal",
    "overall",
]
CONCLUSIONS = ["上升", "下降", "性格刚毅", "性格柔顺", "财旺", "财弱"]
STRATEGIES = ["retain_all", "highest_confidence", "majority"]


def _canonical(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


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


def _explicit_cases() -> list[dict]:
    """边界与结构性用例 (确保各分支被覆盖)。"""
    cases: list[dict] = []

    # empty
    cases.append({"evidence": [], "config": {"strategy": "retain_all"}})

    # single evidence
    cases.append(
        {
            "evidence": [_evidence("ev:p:1", "bazi", "personality", "性格刚毅", 0.9, "positive")],
            "config": {"strategy": "retain_all"},
        }
    )

    # duplicate evidence_id (dedup keeps first)
    cases.append(
        {
            "evidence": [
                _evidence("ev:dup:1", "bazi", "career", "上升", 0.3),
                _evidence("ev:dup:1", "ziwei", "career", "上升", 0.9),
            ],
            "config": {"strategy": "retain_all"},
        }
    )

    # cross-system bonus (2 and 3 systems) + cap
    for systems, bonus, cap in (
        (["bazi", "qimen"], 0.1, 0.3),
        (["bazi", "qimen", "ziwei"], 0.1, 0.3),
        (["bazi", "qimen", "ziwei", "liuyao"], 0.3, 0.2),
    ):
        cases.append(
            {
                "evidence": [_evidence(f"ev:bonus:{s}", s, "wealth", "财旺", 0.5) for s in systems],
                "config": {
                    "strategy": "retain_all",
                    "cross_system_bonus_per_system": bonus,
                    "max_cross_system_bonus": cap,
                },
            }
        )

    # conflicts under all three strategies
    conflict = [
        _evidence("ev:c:1", "bazi", "personality", "性格刚毅", 0.9),
        _evidence("ev:c:2", "ziwei", "personality", "性格柔顺", 0.8),
        _evidence("ev:c:3", "qimen", "personality", "性格柔顺", 0.4),
    ]
    for strategy in STRATEGIES:
        cases.append({"evidence": conflict, "config": {"strategy": strategy}})

    # multi-domain + sorting
    cases.append(
        {
            "evidence": [
                _evidence("ev:s:z", "bazi", "wealth", "财旺", 0.8),
                _evidence("ev:s:a", "bazi", "career", "上升", 0.4),
                _evidence("ev:s:m", "ziwei", "career", "转行", 0.6),
            ],
            "config": {"strategy": "retain_all"},
        }
    )

    # confidence clamping
    cases.append(
        {
            "evidence": [_evidence("ev:clamp:1", "bazi", "health", "健康", 0.95)],
            "config": {"strategy": "retain_all", "max_confidence": 0.5, "min_confidence": 0.2},
        }
    )

    # boundary confidences
    cases.append(
        {
            "evidence": [
                _evidence("ev:b:0", "bazi", "legal", "诉讼", 0.0),
                _evidence("ev:b:1", "bazi", "travel", "出行", 1.0),
            ],
            "config": {"strategy": "retain_all"},
        }
    )
    return cases


def _generate_inputs(seed: int, count: int) -> list[dict]:
    """固定种子生成 count 个合法输入 (与显式用例合并)。"""
    rng = random.Random(seed)
    inputs: list[dict] = []
    for i in range(count):
        n = rng.randrange(1, 7)
        evidence: list[dict] = []
        # 至少一个域同时出现两个结论, 以触发冲突路径
        conflict_domain = rng.choice(DOMAINS)
        evidence.append(
            _evidence(
                f"ev:g{i}:a",
                rng.choice(SYSTEMS),
                conflict_domain,
                rng.choice(CONCLUSIONS),
                round(rng.random(), 3),
            )
        )
        evidence.append(
            _evidence(
                f"ev:g{i}:b",
                rng.choice(SYSTEMS),
                conflict_domain,
                rng.choice(CONCLUSIONS),
                round(rng.random(), 3),
            )
        )
        for j in range(n):
            domain = rng.choice(DOMAINS)
            conclusion = rng.choice(CONCLUSIONS)
            system = rng.choice(SYSTEMS)
            conf = round(rng.random(), 3)
            direction = rng.choice([None, "positive", "negative", "neutral"])
            evidence.append(_evidence(f"ev:g{i}:{j}", system, domain, conclusion, conf, direction))
        # 偶发重复 evidence_id
        if rng.random() < 0.3 and evidence:
            evidence.append(dict(evidence[0]))
        inputs.append(
            {
                "evidence": evidence,
                "config": {
                    "strategy": rng.choice(STRATEGIES),
                    "cross_system_bonus_per_system": round(rng.choice([0.0, 0.1, 0.3]), 3),
                    "max_cross_system_bonus": round(rng.choice([0.0, 0.2, 0.3]), 3),
                },
            }
        )
    return inputs


def _both(payload: dict) -> tuple[str, str]:
    product = ConsensusEngine().build(ProductInput(**payload)).model_dump(mode="json")
    reference = ConsensusBuilder().build(ReferenceInput(**payload)).model_dump(mode="json")
    return _canonical(product), _canonical(reference)


SEED = 20260916
COUNT = 40
ALL_INPUTS = _explicit_cases() + _generate_inputs(SEED, COUNT)


def test_frozen_vectors_equivalent():
    """3 条冻结 conformance 向量: Production == Reference (逐字节)。"""
    vectors = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))
    assert len(vectors) == 3
    mismatched: list[str] = []
    for vector in vectors:
        product, reference = _both(vector["input"])
        if product != reference:
            mismatched.append(vector["name"])
        # 冻结期望值亦须一致
        assert product == _canonical(vector["expected_output"]), vector["name"]
    assert not mismatched, f"equivalence failure: {mismatched}"


def test_generated_inputs_equivalent():
    """固定种子生成的合法输入: Production == Reference (逐字节)。"""
    mismatched: list[str] = []
    for i, payload in enumerate(ALL_INPUTS):
        product, reference = _both(payload)
        if product != reference:
            mismatched.append(f"case#{i}")
    print(
        f"[Consensus Equivalence] {len(ALL_INPUTS) - len(mismatched)}/{len(ALL_INPUTS)} inputs byte-identical"
    )
    assert not mismatched, f"equivalence failure: {mismatched}"


def test_coverage_of_structural_branches():
    """等价样本须覆盖: 空输入 / 冲突 / 多系统 / 多域 / 去重。"""
    reports = [ConsensusEngine().build(ProductInput(**p)) for p in ALL_INPUTS]
    assert any(r.metadata["total_evidence"] == 0 for r in reports), "empty case missing"
    assert any(r.conflicts for r in reports), "conflict case missing"
    assert any(any(len(c.systems) > 1 for c in r.conclusions) for r in reports), (
        "cross-system case missing"
    )
    assert any(len(r.domains) > 1 for r in reports), "multi-domain case missing"
    has_dedup = any(
        r.metadata["total_evidence"] < len(payload["evidence"])
        for payload, r in zip(ALL_INPUTS, reports, strict=True)
    )
    assert has_dedup, "dedup case missing"
    assert any(c.is_conflict for r in reports for c in r.conclusions), "conflict marking missing"


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_each_strategy_equivalence(strategy):
    """三种冲突策略各自逐字节等价。"""
    payloads = [p for p in ALL_INPUTS if p["config"].get("strategy") == strategy]
    assert payloads, f"no sample for strategy {strategy}"
    for payload in payloads:
        product, reference = _both(payload)
        assert product == reference, strategy
