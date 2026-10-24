"""P2.2 — Qimen Knowledge Corpus: schema, validation, provenance, retrieval.

Drives the real corpus artifact (``knowledge/qimen_corpus.json``) produced by
the existing deterministic pipeline (``knowledge/pipeline.py``) and validated
by the existing validator (``knowledge/validate.py``) against the frozen KB
contracts. No mocks, no embeddings, no second architecture, no second retriever.
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
QIMEN_DIR = KNOWLEDGE_DIR / "corpus" / "qimen"
QIMEN_CORPUS = KNOWLEDGE_DIR / "qimen_corpus.json"
BAZI_CORPUS = KNOWLEDGE_DIR / "bazi_corpus.json"
ZIWEI_CORPUS = KNOWLEDGE_DIR / "ziwei_corpus.json"

# digests recorded at freeze / P2.1 (must not change in P2.2; Ziwei digest
# re-registered by ACP-KNOWLEDGE-001 EOL erratum, 2026-10-24, content unchanged)
ZIWEI_DIGEST = "93dba0673b8b0c45f083c1760465a08f2444275485c160bb2e1a02c23735257f"
BAZI_DIGEST = "488ce51099c18546aa693d364954cf1adf25b5ddb29921469d1c57a9e195f4ea"

REQUIRED_NINE_PALACES = {
    "坎一宫",
    "坤二宫",
    "震三宫",
    "巽四宫",
    "中五宫",
    "乾六宫",
    "兑七宫",
    "艮八宫",
    "离九宫",
}
REQUIRED_EIGHT_DOORS = {"休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"}
REQUIRED_NINE_STARS = {
    "天蓬",
    "天芮",
    "天冲",
    "天辅",
    "天禽",
    "天心",
    "天柱",
    "天任",
    "天英",
}
REQUIRED_EIGHT_GODS = {"值符神", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"}
REQUIRED_CONCEPTS = {
    "九宫",
    "八门",
    "九星",
    "八神",
    "阳遁",
    "阴遁",
    "值符",
    "值使",
    "六仪",
    "三奇",
    "旬首",
    "空亡",
}

# the eight terms the sprint requires retrieval to hit, and the node each one is
# about (measured; the char-overlap scorer is deterministic, so this is exact).
REQUIRED_QUERY_HITS = {
    "九宫": "kn:palace:qimen_jiugong",
    "八门": "kn:shen_sha:qimen_bamen",
    "九星": "kn:main_star:qimen_jiuxing",
    "八神": "kn:shen_sha:qimen_bashen",
    "阴遁": "kn:pattern:qimen_yindun",
    "阳遁": "kn:pattern:qimen_yangdun",
    "值符": "kn:pattern:qimen_zhifu",
    "值使": "kn:pattern:qimen_zhishi",
}

FROZEN_NODE_TYPES = {
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
FROZEN_RELATION_TYPES = {
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


def _corpus() -> dict:
    return json.loads(QIMEN_CORPUS.read_text(encoding="utf-8"))


def _qimen_node_ids() -> set[str]:
    return {n["id"] for n in _corpus()["nodes"]}


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


def test_qimen_corpus_artifact_exists_and_loads() -> None:
    doc = _corpus()
    meta = doc["metadata"]
    assert meta["corpus_id"] == "qimen_corpus"
    assert meta["domain"] == "qimen"
    assert meta["status"] == "candidate", "P2.2 first batch is a candidate, not frozen"
    assert meta["version"] == "0.1.0"
    assert meta["counts"] == {"nodes": 47, "relations": 60, "references": 15}
    assert len(doc["nodes"]) == 47
    assert len(doc["relations"]) == 60
    assert len(doc["references"]) == 15


def test_qimen_corpus_is_self_contained() -> None:
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
    types = {n["node_type"] for n in _corpus()["nodes"]}
    assert types == {"palace", "shen_sha", "main_star", "pattern"}
    assert types <= FROZEN_NODE_TYPES, sorted(types - FROZEN_NODE_TYPES)


def test_relation_types_are_frozen_kb007_values() -> None:
    """KB-007: relation_type must stay inside the frozen 15-value enum."""
    for rel in _corpus()["relations"]:
        assert rel["relation_type"] in FROZEN_RELATION_TYPES, rel["id"]


def test_nodes_carry_frozen_fields_and_qimen_system() -> None:
    for node in _corpus()["nodes"]:
        assert node["systems"] == ["qimen"], node["id"]
        assert node["id"].startswith(f"kn:{node['node_type']}:qimen_"), node["id"]
        assert node["name_cn"] and node["name_en"] and node["interpretation"]
        assert 0.0 <= node["confidence"] <= 1.0


def test_qimen_ids_do_not_collide_across_domains() -> None:
    """Ziwei / BaZi / Qimen share one retriever: ids must stay globally unique."""
    ziwei = {n["id"] for n in json.loads(ZIWEI_CORPUS.read_text(encoding="utf-8"))["nodes"]}
    bazi = {n["id"] for n in json.loads(BAZI_CORPUS.read_text(encoding="utf-8"))["nodes"]}
    qimen = _qimen_node_ids()

    assert not qimen & ziwei, sorted(qimen & ziwei)
    assert not qimen & bazi, sorted(qimen & bazi)
    assert not ziwei & bazi, sorted(ziwei & bazi)


# == 2. Required Knowledge coverage ==


def test_required_nine_palaces_and_container_present() -> None:
    names = {n["name_cn"] for n in _corpus()["nodes"] if n["node_type"] == "palace"}
    assert REQUIRED_NINE_PALACES <= names
    assert "九宫" in names


def test_required_eight_doors_and_container_present() -> None:
    names = {n["name_cn"] for n in _corpus()["nodes"] if n["node_type"] == "shen_sha"}
    assert REQUIRED_EIGHT_DOORS <= names
    assert "八门" in names


def test_required_nine_stars_and_container_present() -> None:
    names = {n["name_cn"] for n in _corpus()["nodes"] if n["node_type"] == "main_star"}
    assert REQUIRED_NINE_STARS <= names
    assert "九星" in names


def test_required_eight_gods_and_container_present() -> None:
    names = {n["name_cn"] for n in _corpus()["nodes"] if n["node_type"] == "shen_sha"}
    assert REQUIRED_EIGHT_GODS <= names
    assert "八神" in names


def test_required_concepts_present() -> None:
    names = {n["name_cn"] for n in _corpus()["nodes"]}
    assert REQUIRED_CONCEPTS <= names, sorted(REQUIRED_CONCEPTS - names)


def test_palace_star_door_attributes_match_the_deterministic_engine() -> None:
    """The reference layer must agree with the engine's fixed 地盘配属 tables.

    This asserts *consistency with* the engine; it never feeds back into it.
    """
    from openmetaphysics.agents.qimen import EIGHT_DOORS, NINE_STARS, PALACE_NAMES_9

    by_number = {
        n["attributes"]["palace_number"]: n
        for n in _corpus()["nodes"]
        if n["node_type"] == "palace" and "palace_number" in n["attributes"]
    }
    assert set(by_number) == set(range(1, 10))

    for palace, bagua in PALACE_NAMES_9.items():
        node = by_number[palace]
        expected_prefix = "中" if bagua == "中宫" else bagua
        assert node["name_cn"].startswith(expected_prefix), node["name_cn"]
        assert node["attributes"]["fixed_star"] == NINE_STARS[palace]
        assert node["attributes"]["fixed_door"] == EIGHT_DOORS[palace]


def test_relations_cover_membership_and_earth_plate_pairing() -> None:
    subtypes: dict[str, int] = {}
    for rel in _corpus()["relations"]:
        for cond in rel.get("conditions", []):
            if cond.get("field") == "relation_subtype":
                subtypes[str(cond["value"])] = subtypes.get(str(cond["value"]), 0) + 1

    assert subtypes["jiugong_member"] == 9
    assert subtypes["bamen_member"] == 8
    assert subtypes["jiuxing_member"] == 9
    assert subtypes["bashen_member"] == 8
    assert subtypes["dipan_star"] == 9
    assert subtypes["dipan_door"] == 8, "中五宫不开门, 地盘配门只有 8 组"
    assert subtypes["zhifu_subsystem"] == 1
    assert subtypes["zhishi_subsystem"] == 1


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


def test_sources_are_registered_and_digested() -> None:
    assert sorted(QIMEN_DIR.rglob("*.yaml")), "the Qimen corpus YAML must exist"
    source_files = sorted((KNOWLEDGE_DIR / "sources" / "qimen").glob("*.yaml"))
    assert len(source_files) == 2

    # Source digests are raw-byte hashes (EOL-sensitive), so rebuild first and
    # then compare the register with the on-disk sources.
    _run_pipeline("qimen")
    digests = _corpus()["metadata"]["source_digests"]
    for path in source_files:
        assert path.name in digests
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digests[path.name]

    used = {ref["source"]["text"] for ref in _corpus()["references"]}
    registered = {"奇门遁甲统宗", "烟波钓叟歌"}
    assert used <= registered, f"unregistered source used: {sorted(used - registered)}"
    assert used == registered, "both registered sources must actually be cited"


def test_provenance_does_not_claim_verbatim_verification() -> None:
    """Qimen references stay book-level attributed; H6 pinned the source only.

    Source metadata records the revision pin (H6, 2026-10-24), but corpus
    passages must not claim a verbatim verification that has not been performed.
    """
    source_01 = (KNOWLEDGE_DIR / "sources" / "qimen" / "source_qimen_01.yaml").read_text(
        encoding="utf-8"
    )
    assert "revision_pinned" in source_01
    assert "VERBATIM_VERIFIED" not in source_01

    for ref in _corpus()["references"]:
        assert "非逐字核验" in ref["passage"] or "不据以做逐字核验" in ref["passage"], ref[
            "reference_id"
        ]
        assert "VERBATIM_VERIFIED" not in ref["passage"]


def test_chapters_are_the_verified_section_names() -> None:
    chapters = {(n["source"]["text"], n["source"].get("chapter")) for n in _corpus()["nodes"]}
    assert ("奇门遁甲统宗", "卷之一·遁甲起例") in chapters
    assert ("奇门遁甲统宗", "卷之二·八门所主") in chapters
    assert ("奇门遁甲统宗", "卷之二·九星所主") in chapters
    assert ("奇门遁甲统宗", "卷之二·以旬首取符使法") in chapters


# == 4. Existing validator (KB-001~020) ==


def test_existing_validator_passes_for_all_domains() -> None:
    validator = _load_validator()
    assert validator.validate() == []


def test_validator_covers_the_qimen_domain() -> None:
    validator = _load_validator()
    assert "qimen" in validator.DOMAINS


def test_validator_catches_a_broken_qimen_endpoint(tmp_path, monkeypatch) -> None:
    """Negative control: the shared validator really checks the Qimen corpus."""
    validator = _load_validator()
    doc = _corpus()
    broken = dict(doc["relations"][0])
    broken["target_node_id"] = "kn:pattern:does_not_exist"

    for name in ("nodes", "relations", "references"):
        (tmp_path / "corpus" / "qimen" / name).mkdir(parents=True)
    (tmp_path / "corpus" / "qimen" / "relations" / "broken.yaml").write_text(
        json.dumps({"relations": [broken]}, ensure_ascii=False), encoding="utf-8"
    )

    monkeypatch.setattr(validator, "ROOT", tmp_path)
    failures = validator.validate()
    assert any("does_not_exist" in f for f in failures), failures


def test_validator_catches_a_cross_domain_id_collision(tmp_path, monkeypatch) -> None:
    """P2.2 must not introduce an id that another domain already uses."""
    validator = _load_validator()
    colliding = json.loads(QIMEN_CORPUS.read_text(encoding="utf-8"))["nodes"][0]
    colliding = dict(colliding, id="kn:heavenly_stem:jia")

    (tmp_path / "corpus" / "qimen" / "nodes").mkdir(parents=True)
    (tmp_path / "corpus" / "ziwei" / "nodes").mkdir(parents=True)
    (tmp_path / "corpus" / "qimen" / "nodes" / "collide.yaml").write_text(
        json.dumps({"nodes": [colliding]}, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "corpus" / "ziwei" / "nodes" / "collide.yaml").write_text(
        json.dumps({"nodes": [colliding]}, ensure_ascii=False), encoding="utf-8"
    )

    monkeypatch.setattr(validator, "ROOT", tmp_path)
    failures = validator.validate()
    assert any("cross-domain duplicate node id" in f for f in failures), failures


# == 5. Pipeline determinism (existing pipeline, new domain) ==


def test_pipeline_emits_three_domains_deterministically() -> None:
    out = _run_pipeline()
    assert out.count("corpus written") == 4, "Ziwei + BaZi + Qimen + Liuyao"

    first = QIMEN_CORPUS.read_bytes()
    assert _run_pipeline().count("corpus written") == 4
    assert QIMEN_CORPUS.read_bytes() == first, "qimen corpus is not byte-stable"

    _run_pipeline("qimen")
    assert QIMEN_CORPUS.read_bytes() == first


def test_frozen_and_p21_corpora_are_untouched_by_p22() -> None:
    """P2.2 must not change the frozen Ziwei artifact or the P2.1 BaZi artifact."""
    ziwei_before = ZIWEI_CORPUS.read_bytes()
    bazi_before = BAZI_CORPUS.read_bytes()

    _run_pipeline()

    assert ZIWEI_CORPUS.read_bytes() == ziwei_before
    assert BAZI_CORPUS.read_bytes() == bazi_before
    # knowledge/**/*.yaml is EOL-pinned (ACP-KNOWLEDGE-001, 2026-10-24):
    # canonical digests on every checkout, asserted unconditionally.
    assert hashlib.sha256(ziwei_before).hexdigest() == ZIWEI_DIGEST
    assert hashlib.sha256(bazi_before).hexdigest() == BAZI_DIGEST


def test_qimen_corpus_has_no_ascii_in_searchable_node_text() -> None:
    """Regression guard for the char-level scorer.

    ``node_to_chunk`` searches ``name_cn + interpretation``. Latin words there
    become extremely rare "characters" under the Phase C rare-term weighting
    (``1 + ln(N/df)``) and would outrank real Chinese term matches. Technical
    identifiers belong in ``attributes``/``tags``/``name_en``, not in prose.
    """
    import re

    ascii_word = re.compile(r"[A-Za-z]{2,}")
    for node in _corpus()["nodes"]:
        assert not ascii_word.search(node["interpretation"]), node["id"]
        assert not ascii_word.search(node["name_cn"]), node["id"]


# == 6. Retrieval ==


def test_required_qimen_queries_hit_their_knowledge_node() -> None:
    """Every term the sprint requires must retrieve its own Qimen node first."""
    retriever = InMemoryRetriever(load_all_chunks())
    for query, expected in REQUIRED_QUERY_HITS.items():
        hits = retriever.retrieve(query, k=5)
        assert hits, f"{query} returned nothing from the combined corpus"
        assert hits[0].id == expected, f"{query} -> {hits[0].id} (expected {expected})"
        assert hits[0].source, "citations must be preserved"


@pytest.mark.parametrize(
    "query",
    [
        "九宫",
        "八门",
        "九星",
        "八神",
        "阴遁",
        "阳遁",
        "值符",
        "值使",
        "三奇",
        "六仪",
        "空亡",
        "三元",
    ],
)
def test_qimen_queries_retrieve_qimen_knowledge(query: str) -> None:
    retriever = InMemoryRetriever(load_all_chunks())
    hits = retriever.retrieve(query, k=5)
    assert hits, f"{query} returned nothing"
    qimen_ids = _qimen_node_ids()
    assert any(c.id in qimen_ids for c in hits), [c.id for c in hits]


def test_focused_qimen_queries_resolve_to_the_right_concept() -> None:
    retriever = InMemoryRetriever(load_all_chunks())

    assert retriever.retrieve("坎一宫 坎宫 正北", k=1)[0].id == "kn:palace:qimen_kan"
    assert retriever.retrieve("休门 吉门 坎一宫", k=1)[0].id == "kn:shen_sha:qimen_men_xiu"
    assert retriever.retrieve("天蓬 凶星 坎一宫", k=1)[0].id == "kn:main_star:qimen_tianpeng"
    assert retriever.retrieve("螣蛇 螣蛇 虚耗", k=1)[0].id == "kn:shen_sha:qimen_shen_tengshe"


def test_top_k_behaviour() -> None:
    retriever = InMemoryRetriever(load_all_chunks())
    assert len(retriever.retrieve("九宫", k=1)) == 1
    assert len(retriever.retrieve("九宫", k=3)) == 3
    assert retriever.retrieve("九宫", k=0) == []
    assert retriever.retrieve("九宫", k=-1) == []


def test_qimen_retrieval_is_deterministic_across_retrievers() -> None:
    for query in ("九宫", "八门", "九星", "八神", "阴遁", "阳遁", "值符", "值使"):
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
    assert not isinstance(retriever, QdrantRetriever), "P2.2 stays on the deterministic retriever"
    hits = retriever.retrieve("九宫 八门 九星 八神", k=5)
    assert any(c.id in _qimen_node_ids() for c in hits)
