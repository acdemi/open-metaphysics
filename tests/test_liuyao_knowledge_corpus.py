"""P2.4 — Liuyao Knowledge Corpus: schema, validation, provenance, retrieval.

Drives the real corpus artifact (``knowledge/liuyao_corpus.json``) produced by
the existing deterministic pipeline (``knowledge/pipeline.py``) and validated by
the existing validator (``knowledge/validate.py``) against the frozen KB
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
LIUYAO_DIR = KNOWLEDGE_DIR / "corpus" / "liuyao"
LIUYAO_CORPUS = KNOWLEDGE_DIR / "liuyao_corpus.json"
ZIWEI_CORPUS = KNOWLEDGE_DIR / "ziwei_corpus.json"
BAZI_CORPUS = KNOWLEDGE_DIR / "bazi_corpus.json"
QIMEN_CORPUS = KNOWLEDGE_DIR / "qimen_corpus.json"

# digests recorded at freeze / P2.1 / P2.2 / P2.3-P2.4; Ziwei re-registered by
# ACP-KNOWLEDGE-001 EOL erratum (2026-10-24; content unchanged)
ZIWEI_DIGEST = "93dba0673b8b0c45f083c1760465a08f2444275485c160bb2e1a02c23735257f"
BAZI_DIGEST = "488ce51099c18546aa693d364954cf1adf25b5ddb29921469d1c57a9e195f4ea"
QIMEN_DIGEST = "abdc2080d4f542a8d4a3835085bcb8c185a86c57de32440337660692119c6935"
LIUYAO_DIGEST = "3a09a08eccd72a24363b64fa28fee4d01f80a4bfae8d4a366ae75360e2c8a53b"

REQUIRED_EIGHT_PALACES = {"乾宫", "坎宫", "艮宫", "震宫", "巽宫", "离宫", "坤宫", "兑宫"}
REQUIRED_FIVE_RELATIVES = {"父母", "兄弟", "子孙", "妻财", "官鬼"}
REQUIRED_SIX_SPIRITS = {"青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"}
REQUIRED_FIVE_ELEMENTS = {"木", "火", "土", "金", "水"}
REQUIRED_CONCEPTS = {
    "本卦",
    "变卦",
    "动爻",
    "世应",
    "纳甲",
    "月建",
    "日辰",
    "旬空",
    "六冲卦",
    "六合卦",
    "三合局",
    "三刑",
    "仇神",
    "用神",
    "元神",
    "忌神",
    "暗动",
    "动散",
    "反吟",
    "伏吟",
    "生旺墓绝",
    "应期",
    "游魂",
    "归魂",
    "月破",
    "飞神",
    "伏神",
    "进神",
    "退神",
    "随鬼入墓",
    "独发",
    "独静",
    "两现",
    "卦变回头生克",
}

# the concept queries the sprint requires retrieval to hit (measured; the
# char-overlap scorer is deterministic, so this mapping is exact).
REQUIRED_QUERY_HITS = {
    "六亲 父母 兄弟 子孙 妻财 官鬼": "kn:ten_god:liuyao_liuqin",
    "父母": "kn:ten_god:liuyao_fumu",
    "官鬼": "kn:ten_god:liuyao_guangui",
    "青龙 甲乙日": "kn:shen_sha:liuyao_qinglong",
    "玄武 壬癸日": "kn:shen_sha:liuyao_xuanwu",
    "世应": "kn:pattern:liuyao_shiying",
    "纳甲": "kn:pattern:liuyao_najia",
    "月建": "kn:pattern:liuyao_yuejian",
    "日辰 日建": "kn:pattern:liuyao_richen",
    "旬空": "kn:pattern:liuyao_xunkong",
    "用神 所测之事": "kn:yong_shen:liuyao_yongshen",
    "元神": "kn:xi_shen:liuyao_yuanshen",
    "忌神": "kn:ji_shen:liuyao_jishen",
    "仇神": "kn:pattern:liuyao_choushen",
    "六冲卦": "kn:pattern:liuyao_liuchong_gua",
    "六合卦": "kn:pattern:liuyao_liuhe_gua",
    "三合局": "kn:pattern:liuyao_sanhe_ju",
    "三刑": "kn:pattern:liuyao_sanxing",
    "暗动 静爻旺相": "kn:pattern:liuyao_andong",
    "动散 冲散": "kn:pattern:liuyao_dongsan",
    "反吟 卦变": "kn:pattern:liuyao_fanyin",
    "伏吟 忧郁": "kn:pattern:liuyao_fuyin",
    "生旺墓绝 金长生在巳": "kn:pattern:liuyao_shengwang_mujue",
    "应期 远事年月": "kn:pattern:liuyao_yingqi",
    "游魂 迁改不常": "kn:pattern:liuyao_youhun",
    "归魂 第八卦": "kn:pattern:liuyao_guihun",
    "月破 逐月之破日": "kn:pattern:liuyao_yuepo",
    "飞神 飞来生伏": "kn:pattern:liuyao_feishen",
    "伏神 终不得出": "kn:pattern:liuyao_fushen",
    "进神 亥化子": "kn:pattern:liuyao_jinshen",
    "退神 子化亥": "kn:pattern:liuyao_tuishen",
    "随鬼入墓 日墓": "kn:pattern:liuyao_suigui_rumu",
    "独发 一爻独动": "kn:pattern:liuyao_dufa",
    "独静 静爻旺衰": "kn:pattern:liuyao_dujing",
    "两现 用神两现": "kn:pattern:liuyao_liangxian",
    "卦变 回头克": "kn:pattern:liuyao_guabian_huitu",
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
    return json.loads(LIUYAO_CORPUS.read_text(encoding="utf-8"))


def _liuyao_node_ids() -> set[str]:
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


def test_liuyao_corpus_artifact_exists_and_loads() -> None:
    doc = _corpus()
    meta = doc["metadata"]
    assert meta["corpus_id"] == "liuyao_corpus"
    assert meta["domain"] == "liuyao"
    assert meta["status"] == "frozen", "Liuyao corpus was frozen at v1.0.0 (2026-10-24)"
    assert meta["version"] == "1.0.0"
    assert meta["counts"] == {"nodes": 61, "relations": 66, "references": 41}
    assert len(doc["nodes"]) == 61
    assert len(doc["relations"]) == 66
    assert len(doc["references"]) == 41


def test_liuyao_corpus_is_self_contained() -> None:
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
    assert types == {
        "wuxing",
        "ten_god",
        "shen_sha",
        "palace",
        "pattern",
        "yong_shen",
        "xi_shen",
        "ji_shen",
    }
    assert types <= FROZEN_NODE_TYPES, sorted(types - FROZEN_NODE_TYPES)


def test_relation_types_are_frozen_kb007_values() -> None:
    """KB-007: relation_type must stay inside the frozen 15-value enum."""
    for rel in _corpus()["relations"]:
        assert rel["relation_type"] in FROZEN_RELATION_TYPES, rel["id"]


def test_nodes_carry_frozen_fields_and_liuyao_system() -> None:
    for node in _corpus()["nodes"]:
        assert node["systems"] == ["liuyao"], node["id"]
        assert node["id"].startswith(f"kn:{node['node_type']}:liuyao_"), node["id"]
        assert node["name_cn"] and node["name_en"] and node["interpretation"]
        assert 0.0 <= node["confidence"] <= 1.0


def test_liuyao_ids_do_not_collide_across_domains() -> None:
    """All four domains share one retriever: ids must stay globally unique."""
    ziwei = {n["id"] for n in json.loads(ZIWEI_CORPUS.read_text(encoding="utf-8"))["nodes"]}
    bazi = {n["id"] for n in json.loads(BAZI_CORPUS.read_text(encoding="utf-8"))["nodes"]}
    qimen = {n["id"] for n in json.loads(QIMEN_CORPUS.read_text(encoding="utf-8"))["nodes"]}
    liuyao = _liuyao_node_ids()

    for other, label in ((ziwei, "ziwei"), (bazi, "bazi"), (qimen, "qimen")):
        assert not liuyao & other, (label, sorted(liuyao & other))


# == 2. Required Knowledge coverage ==


def test_required_palaces_relations_spirits_and_elements_present() -> None:
    by_type: dict[str, set[str]] = {}
    for node in _corpus()["nodes"]:
        by_type.setdefault(node["node_type"], set()).add(node["name_cn"])

    assert REQUIRED_EIGHT_PALACES <= by_type["palace"]
    assert "八宫" in by_type["palace"]
    assert REQUIRED_FIVE_RELATIVES <= by_type["ten_god"]
    assert "六亲" in by_type["ten_god"]
    assert REQUIRED_SIX_SPIRITS <= by_type["shen_sha"]
    assert "六神" in by_type["shen_sha"]
    assert REQUIRED_FIVE_ELEMENTS <= by_type["wuxing"]


def test_required_concepts_present() -> None:
    names = {n["name_cn"] for n in _corpus()["nodes"]}
    assert REQUIRED_CONCEPTS <= names, sorted(REQUIRED_CONCEPTS - names)


def test_palace_tables_match_the_deterministic_engine() -> None:
    """The reference layer must agree with the engine's fixed 八宫 tables.

    This asserts *consistency with* the engine; it never feeds back into it.
    """
    from openmetaphysics.agents.liuyao import BA_GONG, SHI_BY_POS

    nodes = {
        n["name_cn"]: n
        for n in _corpus()["nodes"]
        if n["node_type"] == "palace" and n["name_cn"].endswith("宫")
    }
    for palace, numbers in BA_GONG:
        node = nodes[f"{palace}宫"]
        assert node["attributes"]["hexagram_numbers"] == numbers, palace
        assert node["attributes"]["shi_positions"] == [SHI_BY_POS[i] for i in range(1, 9)]


def test_spirit_and_relation_tables_match_the_deterministic_engine() -> None:
    """六神起例 / 六亲配属 must match the engine's fixed tables."""
    from openmetaphysics.agents.liuyao import (
        LIU_QIN_BY_RELATION,
        SIX_SPIRITS,
        SPIRIT_START_BY_STEM,
    )

    doc = _corpus()
    liushen = next(n for n in doc["nodes"] if n["id"] == "kn:shen_sha:liuyao_liushen")
    assert liushen["attributes"]["order"] == SIX_SPIRITS

    # 甲乙->青龙(0), 丙丁->朱雀(1), 戊->勾陈(2), 己->螣蛇(3), 庚辛->白虎(4), 壬癸->玄武(5)
    expected_start = {0: 0, 1: 0, 2: 1, 3: 1, 4: 2, 5: 3, 6: 4, 7: 4, 8: 5, 9: 5}
    assert SPIRIT_START_BY_STEM == expected_start
    for spirit_index in expected_start.values():
        assert SIX_SPIRITS[spirit_index] == liushen["attributes"]["order"][spirit_index]

    liushen_nodes = {
        n["name_cn"]: n
        for n in doc["nodes"]
        if n["node_type"] == "shen_sha" and n["name_cn"] in REQUIRED_SIX_SPIRITS
    }
    for spirit in SIX_SPIRITS:
        assert spirit in liushen_nodes

    liuqin = next(n for n in doc["nodes"] if n["id"] == "kn:ten_god:liuyao_liuqin")
    assert liuqin["attributes"]["relation_to_self"] == {
        "同我": LIU_QIN_BY_RELATION["same"],
        "我生": LIU_QIN_BY_RELATION["sheng"],
        "生我": LIU_QIN_BY_RELATION["being_sheng"],
        "我克": LIU_QIN_BY_RELATION["ke"],
        "克我": LIU_QIN_BY_RELATION["being_ke"],
    }


def test_relations_cover_membership_and_role_subtypes() -> None:
    subtypes: dict[str, int] = {}
    for rel in _corpus()["relations"]:
        for cond in rel.get("conditions", []):
            if cond.get("field") == "relation_subtype":
                subtypes[str(cond["value"])] = subtypes.get(str(cond["value"]), 0) + 1

    assert subtypes["bagong_member"] == 8
    assert subtypes["palace_element"] == 8
    assert subtypes["liuqin_member"] == 5
    assert subtypes["liushen_member"] == 6
    assert subtypes["wuxing_sheng"] == 5
    assert subtypes["wuxing_ke"] == 5
    assert subtypes["yuanshen_role"] == 1
    assert subtypes["jishen_role"] == 1
    assert subtypes["choushen_role"] == 2
    assert subtypes["yuejian_rule"] == 1
    assert subtypes["richen_rule"] == 1
    assert subtypes["yuejian_chong"] == 1
    assert subtypes["feifu"] == 1
    assert subtypes["donghua_jintui"] == 2
    assert subtypes["bagong_position"] == 2
    assert subtypes["guabian_fanyin"] == 1
    assert subtypes["guabian_fuyin"] == 1
    assert subtypes["richen_chong"] == 1
    assert subtypes["liangxian_selection"] == 1
    assert subtypes["guabian_huitu"] == 1
    assert subtypes["suigui"] == 1


def test_yong_shen_chain_matches_the_classic_definitions() -> None:
    """元神生用神、忌神克用神、仇神克元神而生忌神 (relations, not prose)."""
    rels = {(r["source_node_id"], r["relation_type"], r["target_node_id"]) for r in _corpus()["relations"]}
    assert ("kn:xi_shen:liuyao_yuanshen", "sheng", "kn:yong_shen:liuyao_yongshen") in rels
    assert ("kn:ji_shen:liuyao_jishen", "ke", "kn:yong_shen:liuyao_yongshen") in rels
    assert ("kn:pattern:liuyao_choushen", "ke", "kn:xi_shen:liuyao_yuanshen") in rels
    assert ("kn:pattern:liuyao_choushen", "sheng", "kn:ji_shen:liuyao_jishen") in rels


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
    assert sorted(LIUYAO_DIR.rglob("*.yaml")), "the Liuyao corpus YAML must exist"
    source_files = sorted((KNOWLEDGE_DIR / "sources" / "liuyao").glob("*.yaml"))
    assert len(source_files) == 1

    _run_pipeline("liuyao")
    digests = _corpus()["metadata"]["source_digests"]
    for path in source_files:
        assert path.name in digests
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digests[path.name]

    used = {ref["source"]["text"] for ref in _corpus()["references"]}
    assert used == {"增刪卜易"}, f"unregistered source used: {sorted(used)}"


def test_source_records_revision_pinned_verbatim_verification() -> None:
    """P2.4 did perform revision-pinned verbatim verification; record it."""
    source_01 = (KNOWLEDGE_DIR / "sources" / "liuyao" / "source_liuyao_01.yaml").read_text(
        encoding="utf-8"
    )
    assert "revision_pinned_verbatim_verified" in source_01
    assert "2572918" in source_01, "the main-page revision pin must be recorded"

    # every subpage used by a chapter-attributed entry is pinned with a digest
    chapters = {n["source"].get("chapter") for n in _corpus()["nodes"]}
    for chapter in chapters - {None}:
        assert chapter in source_01, chapter


def test_transcription_variants_are_registered_not_silently_rewritten() -> None:
    source_01 = (KNOWLEDGE_DIR / "sources" / "liuyao" / "source_liuyao_01.yaml").read_text(
        encoding="utf-8"
    )
    # /4 辰 -> 艮, /6 天地觀 -> 風地觀, /18 元武/滕蛇/靑龍, /20 𨿽, /5 原劍按
    for marker in ("艮在內", "天地觀", "风地观", "元武", "滕蛇", "靑龍", "𨿽", "原劍按"):
        assert marker in source_01, marker

    najia = next(n for n in _corpus()["nodes"] if n["id"] == "kn:pattern:liuyao_najia")
    assert najia["attributes"]["transcription_variant"]
    liushen = next(n for n in _corpus()["nodes"] if n["id"] == "kn:shen_sha:liuyao_liushen")
    variants = {
        n["attributes"].get("transcription_variant")
        for n in _corpus()["nodes"]
        if n["node_type"] == "shen_sha" and n["name_cn"] in REQUIRED_SIX_SPIRITS
    }
    assert {"靑龍", "滕蛇", "元武"} <= variants
    assert liushen


def test_reference_passages_are_exact_classic_text() -> None:
    """No fabricated quotations: passages must read as the classic's own text.

    The raw wikitext is fetched outside the repository, so this asserts the
    verifiable properties that can be checked offline: the passage carries the
    classic's transcription characters (not modernised ones) and never claims
    a modern editorial layer as the classic's words.
    """
    refs = _corpus()["references"]
    passages = [r["passage"] for r in refs]
    joined = "".join(passages)

    # 转录异体字保留 => 未被改写成现代字形
    assert "𨿽" in joined, "the classic's 雖 variant must be preserved verbatim"
    assert "爲" in joined and "無" in joined and "卽" in joined

    # 现代编辑层（原劍增訂）不得作为典籍原文引用
    for passage in passages:
        assert "原劍" not in passage
        assert "納甲歌" not in passage
        assert "起六神訣" not in passage

    # 章节归属必须与语料来源一致，且每条引用都可回指到已登记章节
    chapters = {r["source"].get("chapter") for r in refs}
    assert "六沖章第二十" in chapters
    assert "八宮圖第三" in chapters
    assert all(chapter for chapter in chapters)


def test_chapters_are_the_verified_section_names() -> None:
    chapters = {(n["source"]["text"], n["source"].get("chapter")) for n in _corpus()["nodes"]}
    for expected in (
        "卦象圖第二",
        "八宮圖第三",
        "渾天甲子章第四",
        "六親歌章第五",
        "世應章第六",
        "動變章第七",
        "用神章第八",
        "用神元神忌神仇神章第九",
        "月將章第十六",
        "日辰章第十七",
        "六神章第十八",
        "六合章第十九",
        "暗動章第二十二",
        "動散章第二十三",
        "卦變生克墓絕章第二十四",
        "反伏章第二十五",
        "旬空章第二十六",
        "生旺墓絕章第又二十六",
        "各門類應期總注章第又二十六",
        "歸魂遊魂章第又二十六",
        "月破章第二十七",
        "飛伏神章第二十八",
        "進神退神章第二十九",
        "隨鬼入墓章第三十",
        "獨發章第三十一",
        "兩現章第三十二",
    ):
        assert ("增刪卜易", expected) in chapters, expected


# == 4. Existing validator (KB-001~020) ==


def test_existing_validator_passes_for_all_domains() -> None:
    validator = _load_validator()
    assert validator.validate() == []


def test_validator_covers_the_liuyao_domain() -> None:
    validator = _load_validator()
    assert "liuyao" in validator.DOMAINS


def test_validator_catches_a_broken_liuyao_endpoint(tmp_path, monkeypatch) -> None:
    """Negative control: the shared validator really checks the Liuyao corpus."""
    validator = _load_validator()
    doc = _corpus()
    broken = dict(doc["relations"][0])
    broken["target_node_id"] = "kn:pattern:does_not_exist"

    for name in ("nodes", "relations", "references"):
        (tmp_path / "corpus" / "liuyao" / name).mkdir(parents=True)
    (tmp_path / "corpus" / "liuyao" / "relations" / "broken.yaml").write_text(
        json.dumps({"relations": [broken]}, ensure_ascii=False), encoding="utf-8"
    )

    monkeypatch.setattr(validator, "ROOT", tmp_path)
    failures = validator.validate()
    assert any("does_not_exist" in f for f in failures), failures


def test_validator_catches_a_cross_domain_id_collision(tmp_path, monkeypatch) -> None:
    """P2.4 must not introduce an id that another domain already uses."""
    validator = _load_validator()
    colliding = dict(_corpus()["nodes"][0], id="kn:heavenly_stem:jia")

    (tmp_path / "corpus" / "liuyao" / "nodes").mkdir(parents=True)
    (tmp_path / "corpus" / "ziwei" / "nodes").mkdir(parents=True)
    (tmp_path / "corpus" / "liuyao" / "nodes" / "collide.yaml").write_text(
        json.dumps({"nodes": [colliding]}, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "corpus" / "ziwei" / "nodes" / "collide.yaml").write_text(
        json.dumps({"nodes": [colliding]}, ensure_ascii=False), encoding="utf-8"
    )

    monkeypatch.setattr(validator, "ROOT", tmp_path)
    failures = validator.validate()
    assert any("cross-domain duplicate node id" in f for f in failures), failures


# == 5. Pipeline determinism (existing pipeline, new domain) ==


def test_pipeline_emits_four_domains_deterministically() -> None:
    out = _run_pipeline()
    assert out.count("corpus written") == 4, "Ziwei + BaZi + Qimen + Liuyao"

    first = LIUYAO_CORPUS.read_bytes()
    assert _run_pipeline().count("corpus written") == 4
    assert LIUYAO_CORPUS.read_bytes() == first, "liuyao corpus is not byte-stable"

    _run_pipeline("liuyao")
    assert LIUYAO_CORPUS.read_bytes() == first


def test_existing_corpora_are_untouched_by_p24() -> None:
    """P2.4 must not change the frozen Ziwei artifact or the P2.1/P2.2 artifacts."""
    before = {
        ZIWEI_CORPUS: ZIWEI_CORPUS.read_bytes(),
        BAZI_CORPUS: BAZI_CORPUS.read_bytes(),
        QIMEN_CORPUS: QIMEN_CORPUS.read_bytes(),
        LIUYAO_CORPUS: LIUYAO_CORPUS.read_bytes(),
    }

    _run_pipeline()

    for path, payload in before.items():
        assert path.read_bytes() == payload, f"{path.name} changed"

    # knowledge/**/*.yaml is EOL-pinned (ACP-KNOWLEDGE-001, 2026-10-24):
    # canonical digests on every checkout, asserted unconditionally; this also
    # anchors the Liuyao corpus digest in governance.
    assert hashlib.sha256(before[ZIWEI_CORPUS]).hexdigest() == ZIWEI_DIGEST
    assert hashlib.sha256(before[BAZI_CORPUS]).hexdigest() == BAZI_DIGEST
    assert hashlib.sha256(before[QIMEN_CORPUS]).hexdigest() == QIMEN_DIGEST
    assert hashlib.sha256(before[LIUYAO_CORPUS]).hexdigest() == LIUYAO_DIGEST


def test_liuyao_corpus_has_no_ascii_in_searchable_node_text() -> None:
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


def test_required_liuyao_queries_hit_their_knowledge_node() -> None:
    """Every concept the sprint requires must retrieve its own Liuyao node first."""
    retriever = InMemoryRetriever(load_all_chunks())
    for query, expected in REQUIRED_QUERY_HITS.items():
        hits = retriever.retrieve(query, k=5)
        assert hits, f"{query} returned nothing from the combined corpus"
        assert hits[0].id == expected, f"{query} -> {hits[0].id} (expected {expected})"
        assert hits[0].source, "citations must be preserved"


@pytest.mark.parametrize(
    "query",
    [
        "六爻",
        "六亲",
        "六神",
        "父母",
        "兄弟",
        "子孙",
        "妻财",
        "官鬼",
        "青龙",
        "朱雀",
        "勾陈",
        "螣蛇",
        "白虎",
        "玄武",
        "八宫",
        "乾宫",
        "坎宫",
        "世应",
        "纳甲",
        "月建",
        "日辰",
        "旬空",
        "用神",
        "元神",
        "忌神",
        "仇神",
        "六冲卦",
        "六合卦",
        "三合局",
        "三刑",
        "暗动",
        "动散",
        "反吟",
        "伏吟",
        "生旺墓绝",
        "应期",
        "游魂",
        "归魂",
        "月破",
        "飞神",
        "伏神",
        "进神",
        "退神",
        "随鬼入墓",
        "独发",
        "独静",
        "两现",
        "卦变回头生克",
    ],
)
def test_liuyao_queries_retrieve_liuyao_knowledge(query: str) -> None:
    retriever = InMemoryRetriever(load_all_chunks())
    hits = retriever.retrieve(query, k=5)
    assert hits, f"{query} returned nothing"
    liuyao_ids = _liuyao_node_ids()
    assert any(c.id in liuyao_ids for c in hits), [c.id for c in hits]


def test_focused_liuyao_queries_resolve_to_the_right_concept() -> None:
    retriever = InMemoryRetriever(load_all_chunks())

    assert retriever.retrieve("青龙 甲乙日 吉神", k=1)[0].id == "kn:shen_sha:liuyao_qinglong"
    assert retriever.retrieve("玄武 壬癸日 盗贼", k=1)[0].id == "kn:shen_sha:liuyao_xuanwu"
    assert retriever.retrieve("父母 生我者", k=1)[0].id == "kn:ten_god:liuyao_fumu"
    assert retriever.retrieve("官鬼 克我者", k=1)[0].id == "kn:ten_god:liuyao_guangui"
    assert retriever.retrieve("乾宫 属金", k=1)[0].id == "kn:palace:liuyao_qian"
    assert retriever.retrieve("坎宫 属水", k=1)[0].id == "kn:palace:liuyao_kan"


def test_top_k_behaviour() -> None:
    retriever = InMemoryRetriever(load_all_chunks())
    assert len(retriever.retrieve("六爻", k=1)) == 1
    assert len(retriever.retrieve("六爻", k=3)) == 3
    assert retriever.retrieve("六爻", k=0) == []
    assert retriever.retrieve("六爻", k=-1) == []


def test_liuyao_retrieval_is_deterministic_across_retrievers() -> None:
    for query in ("六亲", "六神", "世应", "纳甲", "用神", "六冲卦", "三合局"):
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
    assert not isinstance(retriever, QdrantRetriever), "P2.4 stays on the deterministic retriever"
    hits = retriever.retrieve("六爻 六亲 六神 世应 纳甲", k=5)
    assert any(c.id in _liuyao_node_ids() for c in hits)
