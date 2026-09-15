"""Knowledge corpus regression — Phase 7.2B-R2（三命通會卷三 其余神煞）.

锁定 Phase 7.2B-R / R2 的产出，防止后续 Sprint 静默丢失或改写：

- 语料计数下限（单调递增，不锁精确值，避免后续扩展时脆断）
- R2 的 7 类 shen_sha 节点存在、来源指向 卷三、且带**连续**原文关键句
- R2 引用条目可解析且 target 均存在
- R2 引用 passage 不含省略号（证据纪律: 连续原文）

规范: KN-001~003 / KREF-001~004 / reference/knowledge.py
证据: docs/governance/knowledge/KNOWLEDGE_PHASE_7.2B_R2_REPORT.md
"""

from __future__ import annotations

import json
from pathlib import Path

from reference.knowledge import parse_nodes_file, parse_references_file

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "knowledge" / "corpus" / "ziwei"
OUTPUT = ROOT / "knowledge" / "ziwei_corpus.json"

R2_NODE_IDS = {
    "kn:shen_sha:kong_wang",
    "kn:shen_sha:yuan_chen",
    "kn:shen_sha:zai_sha",
    "kn:shen_sha:liu_e",
    "kn:shen_sha:gou_jiao",
    "kn:shen_sha:tian_luo_di_wang",
    "kn:shen_sha:shi_e_da_bai",
}

ELLIPSIS = ("\u2026", "...")  # … / ...


def _corpus() -> dict:
    return json.loads(OUTPUT.read_text(encoding="utf-8"))


def _shen_sha_nodes():
    return list(parse_nodes_file(str(CORPUS_DIR / "nodes" / "shen_sha.yaml")))


def _r2_references():
    return list(parse_references_file(str(CORPUS_DIR / "references" / "phase_7.2b_r2.yaml")))


def test_corpus_counts_floor() -> None:
    """Phase 7.2B-R2 之后语料不得低于本轮水位（86→93 节点 / 22→32 引用）。"""
    doc = _corpus()
    counts = doc["metadata"]["counts"]
    assert counts["nodes"] >= 93, counts
    assert counts["relations"] >= 37, counts
    assert counts["references"] >= 32, counts


def test_r2_nodes_present() -> None:
    ids = {n.id for n in _shen_sha_nodes()}
    assert R2_NODE_IDS <= ids, R2_NODE_IDS - ids
    assert len([i for i in ids if i.startswith("kn:shen_sha:")]) >= 18


def test_r2_nodes_provenance_is_juan3() -> None:
    for n in _shen_sha_nodes():
        if n.id not in R2_NODE_IDS:
            continue
        assert n.source.text == "三命通会", n.id
        assert "卷三" in (n.source.chapter or ""), n.id
        assert (n.source.url or "").endswith("三命通會/卷三"), n.id


def test_r2_nodes_key_quote_is_continuous_and_nonempty() -> None:
    for n in _shen_sha_nodes():
        if n.id not in R2_NODE_IDS:
            continue
        quote = (n.attributes or {}).get("原文关键句", "")
        assert quote, f"{n.id} missing 原文关键句"
        assert not any(e in quote for e in ELLIPSIS), f"{n.id} key quote contains ellipsis"


def test_r2_reference_targets_exist() -> None:
    node_ids = {n.id for n in _shen_sha_nodes()}
    refs = _r2_references()
    assert len(refs) >= 7
    for r in refs:
        assert r.target_type.value == "node", r.reference_id
        assert r.target_id in node_ids, f"{r.reference_id} -> {r.target_id} missing"


def test_r2_passages_are_verbatim_continuous() -> None:
    """passage 必须是连续原文（无省略号），且逐字非空。"""
    for r in _r2_references():
        assert r.passage.strip(), r.reference_id
        assert not any(e in r.passage for e in ELLIPSIS), f"{r.reference_id} passage has ellipsis"
        assert r.source.text == "三命通会", r.reference_id
