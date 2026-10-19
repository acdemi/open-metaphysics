"""P2.1 — BaZi Knowledge Corpus: schema, validation, provenance, retrieval.

Drives the real corpus artifact (``knowledge/bazi_corpus.json``) produced by
the existing deterministic pipeline (``knowledge/pipeline.py``) and validated
by the existing validator (``knowledge/validate.py``) against the frozen KB
contracts. No mocks, no embeddings, no second architecture.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from openmetaphysics.rag.corpus import load_all_chunks, load_chunks
from openmetaphysics.rag.retriever import InMemoryRetriever, reset_retriever

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT / "knowledge"
BAZI_DIR = KNOWLEDGE_DIR / "corpus" / "bazi"
BAZI_CORPUS = KNOWLEDGE_DIR / "bazi_corpus.json"
ZIWEI_CORPUS = KNOWLEDGE_DIR / "ziwei_corpus.json"

# the frozen Ziwei digest recorded at Corpus Freeze v1.0.0 (must not change)
ZIWEI_DIGEST = "69d6e2a6b2f82d58292bfd11847aa7d26e2cd75eabda8cdbbbb67d4f6cc5f73d"

REQUIRED_TEN_GODS = {
    "比肩",
    "劫财",
    "食神",
    "伤官",
    "正财",
    "偏财",
    "正官",
    "七杀",
    "正印",
    "偏印",
}
REQUIRED_WUXING = {"木", "火", "土", "金", "水"}
REQUIRED_RELATION_SUBTYPES = {
    "wuxing_sheng",
    "wuxing_ke",
    "wu_he",
    "liu_he",
    "liu_chong",
    "san_he",
    "san_hui",
    "wu_en_zhi_xing",
    "shi_shi_zhi_xing",
    "wu_li_zhi_xing",
    "zi_xing",
    "liu_hai",
    "po",
}


def _corpus() -> dict:
    return json.loads(BAZI_CORPUS.read_text(encoding="utf-8"))


def _bazi_node_ids() -> set[str]:
    return {n["id"] for n in _corpus()["nodes"]}


def _subtypes() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for rel in _corpus()["relations"]:
        for cond in rel.get("conditions", []):
            if cond.get("field") == "relation_subtype":
                out.setdefault(str(cond["value"]), []).append(rel["id"])
    return out


def _corpus_yaml_files() -> list[Path]:
    return sorted(BAZI_DIR.rglob("*.yaml"), key=str)


def _run_pipeline(*args: str) -> str:
    return subprocess.run(
        [sys.executable, str(KNOWLEDGE_DIR / "pipeline.py"), *args],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    ).stdout


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "knowledge_validate", KNOWLEDGE_DIR / "validate.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _fresh_retriever():
    reset_retriever()
    yield
    reset_retriever()


# == 1. Corpus presence / shape ==


def test_bazi_corpus_artifact_exists_and_loads() -> None:
    doc = _corpus()
    meta = doc["metadata"]
    assert meta["corpus_id"] == "bazi_corpus"
    assert meta["domain"] == "bazi"
    assert meta["status"] == "candidate", "P2.1 first batch is a candidate, not frozen"
    assert meta["version"] == "0.1.0"
    assert meta["counts"] == {"nodes": 40, "relations": 67, "references": 14}
    assert len(doc["nodes"]) == 40
    assert len(doc["relations"]) == 67
    assert len(doc["references"]) == 14


def test_bazi_corpus_is_self_contained() -> None:
    """Every relation endpoint and reference target lives inside this corpus."""
    doc = _corpus()
    node_ids = {n["id"] for n in doc["nodes"]}
    rel_ids = {r["id"] for r in doc["relations"]}

    for rel in doc["relations"]:
        assert rel["source_node_id"] in node_ids, rel["id"]
        assert rel["target_node_id"] in node_ids, rel["id"]
    for ref in doc["references"]:
        if ref["target_type"] == "node":
            assert ref["target_id"] in node_ids, ref["reference_id"]
        else:
            assert ref["target_id"] in rel_ids, ref["reference_id"]


def test_node_types_are_frozen_kb002_values() -> None:
    """KB-002: node_type must be one of the 20 frozen enum values."""
    allowed = {
        "wuxing",
        "ten_god",
        "heavenly_stem",
        "earthly_branch",
        "palace",
        "main_star",
        "auxiliary_star",
        "shen_sha",
        "pattern",
        "career",
        "personality",
        "marriage",
        "health",
        "wealth",
        "annual_fortune",
        "major_luck",
        "yong_shen",
        "xi_shen",
        "ji_shen",
        "tiao_hou",
    }
    types = {n["node_type"] for n in _corpus()["nodes"]}
    assert types == {"wuxing", "ten_god", "heavenly_stem", "earthly_branch"}
    assert types <= allowed


def test_nodes_carry_frozen_fields_and_bazi_system() -> None:
    for node in _corpus()["nodes"]:
        assert node["systems"] == ["bazi"], node["id"]
        assert node["id"].startswith(f"kn:{node['node_type']}:bazi_"), node["id"]
        assert node["name_cn"] and node["name_en"] and node["interpretation"]
        assert 0.0 <= node["confidence"] <= 1.0


# == 2. Required Knowledge coverage ==


def test_required_wuxing_and_foundation_nodes_present() -> None:
    nodes = {n["name_cn"]: n for n in _corpus()["nodes"]}
    assert REQUIRED_WUXING <= set(nodes)
    assert "旺衰" in nodes
    assert "日主" in nodes
    assert "月令" in nodes
    assert "十神" in nodes["日主"]["interpretation"], "日主 must explain the ten-god baseline"
    assert "旺衰" in nodes["月令"]["interpretation"], "月令 must explain its role in 旺衰"


def test_all_ten_gods_present_with_relation_attributes() -> None:
    gods = {n["name_cn"]: n for n in _corpus()["nodes"] if n["node_type"] == "ten_god"}
    assert set(gods) == REQUIRED_TEN_GODS
    for god in gods.values():
        assert god["attributes"]["relation_to_day_master"] in {
            "同我",
            "我生",
            "我克",
            "克我",
            "生我",
        }
        assert god["attributes"]["yin_yang"] in {"同", "异"}


def test_heavenly_stems_and_earthly_branches_are_complete() -> None:
    stems = [n for n in _corpus()["nodes"] if n["node_type"] == "heavenly_stem"]
    branches = [n for n in _corpus()["nodes"] if n["node_type"] == "earthly_branch"]
    assert len([s for s in stems if s["name_cn"] != "日主"]) == 10
    assert len([b for b in branches if b["name_cn"] != "月令"]) == 12
    for branch in branches:
        if branch["name_cn"] != "月令":
            assert branch["attributes"]["hidden_stems"], branch["id"]
            assert 0 <= branch["attributes"]["branch_index"] <= 11


def test_relation_groups_cover_the_required_combinations() -> None:
    subtypes = _subtypes()
    missing = REQUIRED_RELATION_SUBTYPES - set(subtypes)
    assert not missing, f"missing relation groups: {sorted(missing)}"

    assert len(subtypes["wu_he"]) == 5, "天干五合"
    assert len(subtypes["liu_he"]) == 6, "地支六合"
    assert len(subtypes["liu_chong"]) == 6, "地支六冲"
    assert len(subtypes["san_he"]) == 8, "地支三合（每局 2 边）"
    assert len(subtypes["san_hui"]) == 8, "地支三会（每局 2 边）"
    assert len(subtypes["liu_hai"]) == 6, "地支六害"
    assert len(subtypes["po"]) == 6, "地支六破"
    assert len(subtypes["zi_xing"]) == 4, "自刑 辰/午/酉/亥"


def test_frozen_relation_types_only() -> None:
    """KB-007: relation_type must stay inside the frozen 15-value enum."""
    allowed = {
        "sheng",
        "ke",
        "chong",
        "xing",
        "he",
        "hai",
        "fuzhu",
        "zhiyue",
        "duiying",
        "yingxiang",
        "zengqiang",
        "xueroo",
        "zhixiang",
        "shuyu",
        "yinyong",
    }
    for rel in _corpus()["relations"]:
        assert rel["relation_type"] in allowed, rel["id"]


# == 3. Provenance ==


def test_every_entry_has_provenance() -> None:
    doc = _corpus()
    for node in doc["nodes"]:
        assert node["source"]["text"], node["id"]
    for rel in doc["relations"]:
        assert rel["source"]["text"], rel["id"]
        assert rel["evidence"] and all(e["description"] for e in rel["evidence"]), rel["id"]
    for ref in doc["references"]:
        assert ref["source"]["text"] and ref["passage"], ref["reference_id"]


def test_sources_are_registered_tier1_and_digested() -> None:
    assert _corpus_yaml_files(), "the BaZi corpus YAML must exist"
    source_files = sorted((KNOWLEDGE_DIR / "sources" / "bazi").glob("*.yaml"))
    assert len(source_files) == 2

    # Source digests are raw-byte hashes (EOL-sensitive), so rebuild first and
    # then compare the register with the on-disk sources.
    _run_pipeline("bazi")
    digests = _corpus()["metadata"]["source_digests"]
    for path in source_files:
        assert path.name in digests
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digests[path.name]

    used = {ref["source"]["text"] for ref in _corpus()["references"]}
    registered = {"渊海子平", "三命通会"}
    assert used <= registered, f"unregistered source used: {sorted(used - registered)}"


def test_corroborated_chapters_are_the_verified_ones() -> None:
    """The 刑/害/五合 items reuse the chapters verified for the frozen corpus."""
    chapters = {
        (rel["source"]["text"], rel["source"].get("chapter")) for rel in _corpus()["relations"]
    }
    assert ("三命通会", "卷二·论六害") in chapters
    assert ("三命通会", "卷二·论三刑") in chapters
    assert ("三命通会", "卷二·论十干化气") in chapters
    assert ("渊海子平", "论大运") in chapters


# == 4. Existing validator (KB-001~020) ==


def test_existing_validator_passes_for_all_domains() -> None:
    validator = _load_validator()
    assert validator.validate() == []


def test_validator_catches_a_broken_endpoint(tmp_path, monkeypatch) -> None:
    """Negative control: the shared validator really checks the BaZi corpus."""
    validator = _load_validator()
    doc = _corpus()
    broken = dict(doc["relations"][0])
    broken["target_node_id"] = "kn:wuxing:does_not_exist"

    for name in ("nodes", "relations", "references"):
        (tmp_path / "corpus" / "bazi" / name).mkdir(parents=True)
    (tmp_path / "corpus" / "bazi" / "relations" / "broken.yaml").write_text(
        json.dumps({"relations": [broken]}, ensure_ascii=False), encoding="utf-8"
    )

    monkeypatch.setattr(validator, "ROOT", tmp_path)
    failures = validator.validate()
    assert any("does_not_exist" in f for f in failures), failures


# == 5. Pipeline determinism (existing pipeline, new domain) ==


def test_pipeline_writes_all_domains_and_is_deterministic() -> None:
    out = _run_pipeline()
    assert "corpus written" in out
    # P2.1 emitted two domains; P2.2 added Qimen as the third, P2.3 Liuyao the fourth.
    assert out.count("corpus written") == 4, "every registered domain is emitted"

    first = BAZI_CORPUS.read_bytes()
    assert _run_pipeline().count("corpus written") == 4
    assert BAZI_CORPUS.read_bytes() == first, "bazi corpus is not byte-stable"

    _run_pipeline("bazi")
    assert BAZI_CORPUS.read_bytes() == first


def test_ziwei_corpus_is_byte_identical_to_the_freeze() -> None:
    """P2.1 must not change the frozen Ziwei artifact in any way."""
    before = ZIWEI_CORPUS.read_bytes()

    # The source digests embedded in the artifact are raw-byte hashes of the
    # source YAML, and only knowledge/**/*.json is EOL-pinned by .gitattributes.
    # On a CRLF working copy the register legitimately differs from the recorded
    # freeze digest, so the exact digest is asserted for LF sources only.
    lf_sources = all(
        b"\r\n" not in path.read_bytes()
        for path in (KNOWLEDGE_DIR / "sources" / "ziwei").glob("*.yaml")
    )
    if lf_sources:
        assert hashlib.sha256(before).hexdigest() == ZIWEI_DIGEST

    _run_pipeline()
    after = ZIWEI_CORPUS.read_bytes()
    assert after == before, "the multi-domain pipeline must not rewrite the frozen corpus"

    meta = json.loads(after)["metadata"]
    assert meta["corpus_id"] == "ziwei_corpus"
    assert meta["status"] == "frozen" and meta["version"] == "1.0.0"
    assert sorted(meta["source_digests"]) == ["source_01.yaml", "source_02.yaml", "source_03.yaml"]


# == 6. Retrieval ==


@pytest.mark.parametrize(
    "query",
    [
        "五行",
        "十神",
        "日主",
        "月令",
        "合冲刑害",
        "天干五合",
        "地支六合",
        "地支六冲",
        "三合",
        "六害",
        "相破",
    ],
)
def test_bazi_queries_hit_bazi_knowledge(query: str) -> None:
    retriever = InMemoryRetriever(load_all_chunks())  # both corpora, as the app loads them
    hits = retriever.retrieve(query, k=5)
    assert hits, f"{query} returned nothing from the combined corpus"
    bazi_ids = _bazi_node_ids()
    assert any(c.id in bazi_ids for c in hits), f"{query} retrieved no BaZi knowledge"


def test_focused_bazi_queries_resolve_to_the_right_concept() -> None:
    retriever = InMemoryRetriever(load_all_chunks())

    assert retriever.retrieve("日主 日干 命主", k=1)[0].id == "kn:heavenly_stem:bazi_day_master"
    assert retriever.retrieve("月令 月支 提纲", k=1)[0].id == "kn:earthly_branch:bazi_month_order"
    assert retriever.retrieve("五行旺衰 旺相休囚死", k=1)[0].id == "kn:wuxing:bazi_wangshuai"
    top = retriever.retrieve("十神 比肩 劫财", k=3)
    assert any(c.id.startswith("kn:ten_god:bazi_") for c in top), [c.id for c in top]


def test_retrieval_is_deterministic_across_retrievers() -> None:
    for query in ("五行", "日主", "地支六冲", "相破"):
        first = [c.id for c in InMemoryRetriever(load_all_chunks()).retrieve(query, k=5)]
        second = [c.id for c in InMemoryRetriever(load_all_chunks()).retrieve(query, k=5)]
        assert first == second, query


def test_frozen_ziwei_corpus_still_loads_alone() -> None:
    """The single-corpus API keeps its original meaning (Ziwei, 102 nodes)."""
    chunks = load_chunks()
    assert len(chunks) == 102
    assert all(c.id.startswith("kn:") for c in chunks)


def test_default_retriever_stays_deterministic_and_local() -> None:
    from openmetaphysics.rag.retriever import QdrantRetriever, get_retriever

    retriever = get_retriever()
    assert not isinstance(retriever, QdrantRetriever), "P2.1 stays on the deterministic retriever"
    hits = retriever.retrieve("日主 月令 十神", k=5)
    bazi_ids = _bazi_node_ids()
    assert any(c.id in bazi_ids for c in hits)
