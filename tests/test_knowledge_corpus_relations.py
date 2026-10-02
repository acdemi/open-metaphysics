"""Knowledge corpus regression — Phase 7.1.3 补齐（yinyong 5 + shuyu 5 关系）.

Phase 7.1.3 的 Build Plan / Coverage Matrix 规划了 `yinyong(5) + shuyu(5)`，
实际生产长期为 0（Coverage Matrix §2 一直标「需新增 5」）。本回归锁定该补齐：

- 两类关系各 5 条、端点存在、方向为 directed
- 每条关系至少 1 条 evidence，description 内含「…」逐字引文（来源可回溯）
- 计数下限（单调递增，不锁精确值）

规范: KR-001~003 / KB-007（15 类 relation_type）/ reference/knowledge.py
证据: docs/governance/knowledge/KNOWLEDGE_PHASE_7.1.3_COMPLETION_REPORT.md
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from reference.knowledge import parse_nodes_file, parse_relations_file

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "knowledge" / "corpus" / "ziwei"
OUTPUT = ROOT / "knowledge" / "ziwei_corpus.json"

COMPLETED_TYPES = ("shuyu", "yinyong")
QUOTE_RE = re.compile(r"「([^」]+)」")


def _corpus() -> dict:
    return json.loads(OUTPUT.read_text(encoding="utf-8"))


def _nodes():
    out = []
    for path in sorted((CORPUS_DIR / "nodes").glob("*.yaml")):
        out.extend(parse_nodes_file(str(path)))
    return out


def _relations():
    out = []
    for path in sorted((CORPUS_DIR / "relations").glob("*.yaml")):
        out.extend(parse_relations_file(str(path)))
    return out


def test_corpus_counts_floor() -> None:
    """Phase 7.1.3 补齐后语料不得低于本轮水位（102 节点 / 47 关系 / 41 引用）。"""
    counts = _corpus()["metadata"]["counts"]
    assert counts["nodes"] >= 102, counts
    assert counts["relations"] >= 47, counts
    assert counts["references"] >= 41, counts


def test_completed_relation_types_present() -> None:
    by_type = {}
    for r in _relations():
        by_type.setdefault(r.relation_type.value, []).append(r)
    for rel_type in COMPLETED_TYPES:
        assert len(by_type.get(rel_type, [])) >= 5, f"{rel_type}: {len(by_type.get(rel_type, []))}"


def test_completed_relation_endpoints_exist() -> None:
    node_ids = {n.id for n in _nodes()}
    for r in _relations():
        if r.relation_type.value not in COMPLETED_TYPES:
            continue
        assert r.source_node_id in node_ids, r.id
        assert r.target_node_id in node_ids, r.id


def test_completed_relations_are_directed() -> None:
    for r in _relations():
        if r.relation_type.value not in COMPLETED_TYPES:
            continue
        assert r.direction.value == "directed", r.id


def test_completed_relations_carry_quoted_evidence() -> None:
    """每条关系必须带证据，且 description 内含「…」逐字引文（来源可回溯）。"""
    for r in _relations():
        if r.relation_type.value not in COMPLETED_TYPES:
            continue
        assert r.evidence, f"{r.id} has no evidence"
        assert r.source.text, r.id
        assert any(QUOTE_RE.search(ev.description or "") for ev in r.evidence), r.id


def test_relation_ids_unique() -> None:
    ids = [r.id for r in _relations()]
    assert len(ids) == len(set(ids))
