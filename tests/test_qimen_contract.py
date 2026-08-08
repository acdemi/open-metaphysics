"""Qimen Behavior Contract 校验 (Phase 5.6 + Phase 5.8A).

验证 docs/specification/QIMEN_BEHAVIOR_CONTRACT.md (Frozen v1.0.0) 与
docs/qimen/golden_vectors.json (normative fixtures) 的一致性:
- 契约 ID 唯一且完整 (QC-001 ~ QC-014)
- 每个 QC 条款都有 Golden Vector 映射
- 映射引用的向量全部存在
- 版本元数据一致 (契约 / 向量文件 / 引擎)

Phase 5.8A 补充: docs/specification/qimen_contract.schema.json 机器可读
契约定义层 (contract_version + rules[].id/name/status/observable_inputs/
observable_outputs) 的合法性、唯一性、SemVer、与 markdown 快照一致性。
"""

import json
import re
from pathlib import Path

from openmetaphysics.agents.qimen import QimenAgent

ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "docs" / "specification" / "QIMEN_BEHAVIOR_CONTRACT.md"
SCHEMA_PATH = ROOT / "docs" / "specification" / "qimen_contract.schema.json"
VECTORS_PATH = ROOT / "docs" / "qimen" / "golden_vectors.json"

EXPECTED_QC = [f"QC-{i:03d}" for i in range(1, 15)]
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")


def _load_contract() -> str:
    if not CONTRACT_PATH.exists():
        raise FileNotFoundError(f"contract missing: {CONTRACT_PATH}")
    return CONTRACT_PATH.read_text(encoding="utf-8")


def _load_vectors() -> dict:
    if not VECTORS_PATH.exists():
        raise FileNotFoundError(f"vectors missing: {VECTORS_PATH}")
    return json.loads(VECTORS_PATH.read_text(encoding="utf-8"))


def _extract_clause_ids(text: str) -> list[str]:
    return re.findall(r"^### (QC-\d{3}) ", text, flags=re.MULTILINE)


def _extract_mapping(text: str) -> dict[str, list[str]]:
    """解析契约 §3 映射表: | QC-xxx | G1, G2, ... |"""
    mapping: dict[str, list[str]] = {}
    in_section = False
    for line in text.splitlines():
        if line.startswith("## 3."):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.startswith("|"):
            continue
        m = re.match(r"\|\s*(QC-\d{3})\s*\|\s*(.*?)\s*\|", line)
        if m:
            cells = [c.strip() for c in m.group(2).split(",") if c.strip()]
            mapping[m.group(1)] = cells
    return mapping


def _extract_metadata(text: str, key: str) -> str | None:
    """提取元数据: 优先元数据表 (| key | value |), 回退 blockquote 行。"""
    m = re.search(rf"\|\s*{re.escape(key)}\s*\|\s*([^\n|]+?)\s*\|", text)
    if m:
        return m.group(1).strip()
    m = re.search(rf"\*\*{re.escape(key)}\*\*:\s*([^\n*]+)", text)
    if m:
        return m.group(1).strip().split("（")[0].split("(")[0].strip()
    return None


def test_contract_exists_and_frozen():
    text = _load_contract()
    assert "Frozen" in text, "contract status must be Frozen"
    assert _extract_metadata(text, "version") == "1.0.0"
    assert _extract_metadata(text, "engine_version") == "0.3.0"
    assert _extract_metadata(text, "rule_set_version") == "0.3.0"
    assert "qimen:behavior:v1.0.0" in text


def test_contract_ids_unique_and_complete():
    text = _load_contract()
    ids = _extract_clause_ids(text)
    assert len(ids) == len(set(ids)) == 14, f"clause ids: {ids}"
    assert ids == EXPECTED_QC, f"expected {EXPECTED_QC}, got {ids}"


def test_contract_mapping_complete_and_valid():
    text = _load_contract()
    data = _load_vectors()
    all_ids = {v["id"] for v in data["vectors"]}
    mapping = _extract_mapping(text)
    # 每个 QC 都有映射
    assert set(mapping) == set(EXPECTED_QC), f"missing mapping: {set(EXPECTED_QC) - set(mapping)}"
    # 映射引用的向量全部存在 (ALL = 全部)
    for qc, cells in mapping.items():
        if cells == ["ALL"]:
            continue
        missing = set(cells) - all_ids
        assert not missing, f"{qc} references missing vectors: {missing}"


def test_contract_version_metadata_consistent():
    text = _load_contract()
    data = _load_vectors()
    assert data["status"] == "normative_fixtures"
    assert data["contract_reference"] == "docs/specification/QIMEN_BEHAVIOR_CONTRACT.md"
    assert data["promotion_version"] == _extract_metadata(text, "version")
    assert data["engine_version"] == _extract_metadata(text, "engine_version")
    assert data["rule_set_version"] == _extract_metadata(text, "rule_set_version")
    # 向量分类已提升为规范装置
    assert all(v["classification"] == "normative_fixture" for v in data["vectors"]), (
        "all vectors must be normative_fixture"
    )
    # 引擎版本与向量/契约一致
    assert QimenAgent().engine_version == data["engine_version"]


# ===========================================================================
# Phase 5.8A — Contract Schema Extraction
# 机器可读契约定义层: docs/specification/qimen_contract.schema.json
# ===========================================================================


# JSON Schema 子集校验器 (const/enum/type/pattern/required/properties/
# additionalProperties/items/minItems/uniqueItems) — 仅覆盖本 schema 使用的
# 关键字, 自包含无依赖。
def _check(instance, schema, path):
    errs = []
    if "const" in schema and instance != schema["const"]:
        errs.append(f"{path}: const {schema['const']!r} != {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errs.append(f"{path}: {instance!r} not in enum {schema['enum']}")
    if (
        "pattern" in schema
        and isinstance(instance, str)
        and not re.fullmatch(schema["pattern"], instance)
    ):
        errs.append(f"{path}: {instance!r} does not match {schema['pattern']}")
    typ = schema.get("type")
    if typ == "object" and isinstance(instance, dict):
        for prop in schema.get("required", []):
            if prop not in instance:
                errs.append(f"{path}: missing required '{prop}'")
        for key, value in instance.items():
            sub = schema.get("properties", {}).get(key)
            if sub is None:
                if schema.get("additionalProperties") is False:
                    errs.append(f"{path}: unexpected property '{key}'")
                continue
            errs += _check(value, sub, f"{path}.{key}")
    elif typ == "array" and isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errs.append(f"{path}: minItems {schema['minItems']} violated")
        if schema.get("uniqueItems") and len(instance) != len(
            {json.dumps(i, sort_keys=True) for i in instance}
        ):
            errs.append(f"{path}: items must be unique")
        item_schema = schema.get("items", {})
        if isinstance(item_schema, dict) and item_schema:
            for i, item in enumerate(instance):
                errs += _check(item, item_schema, f"{path}[{i}]")
    elif typ is not None and typ not in ("object", "array"):
        ok = (
            (typ == "string" and isinstance(instance, str))
            or (typ == "integer" and isinstance(instance, int) and not isinstance(instance, bool))
            or (typ == "boolean" and isinstance(instance, bool))
            or (
                typ == "number"
                and isinstance(instance, (int, float))
                and not isinstance(instance, bool)
            )
        )
        if not ok:
            errs.append(f"{path}: expected type {typ}")
    return errs


def _load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"schema missing: {SCHEMA_PATH}")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _extracted() -> dict:
    """x-contract 注解中的提取产物 (contract_version + rules)."""
    schema = _load_schema()
    assert "x-contract" in schema, "schema must embed x-contract extraction annotation"
    return schema["x-contract"]


def test_contract_schema_is_valid():
    """schema 文件本身合法: $schema/title/description/properties/required 齐备。"""
    schema = _load_schema()
    for key in ("$schema", "title", "description", "properties", "required"):
        assert key in schema, f"schema missing '{key}'"
    assert schema["$schema"].startswith("https://json-schema.org/draft/")
    props = schema["properties"]
    assert "contract_version" in props and "rules" in props
    rule_status_enum = props["rules"]["items"]["properties"]["status"]["enum"]
    assert rule_status_enum == ["frozen", "draft", "deprecated"]
    rule_required = props["rules"]["items"]["required"]
    assert rule_required == ["id", "name", "status", "observable_inputs", "observable_outputs"]
    # 提取产物必须通过 schema 校验
    assert not _check(_extracted(), schema, "$"), "x-contract instance invalid against schema"


def test_contract_identifiers_unique():
    """所有 QC-xxx 编号唯一 (schema 枚举 + 提取产物)。"""
    schema = _load_schema()
    enum_ids = schema["properties"]["rules"]["items"]["properties"]["id"]["enum"]
    assert len(enum_ids) == len(set(enum_ids)) == 14, f"schema id enum: {enum_ids}"
    extracted_ids = [r["id"] for r in _extracted()["rules"]]
    assert len(extracted_ids) == len(set(extracted_ids)) == 14
    assert extracted_ids == EXPECTED_QC == enum_ids


def test_contract_version_format():
    """契约版本符合 SemVer。"""
    version = _extracted()["contract_version"]
    assert SEMVER_RE.match(version), f"version {version!r} not SemVer"
    # 与 markdown 元数据一致
    assert version == _extract_metadata(_load_contract(), "version")


def test_contract_matches_markdown_snapshot():
    """schema 中 rule 数量/名称与 markdown 条目一致 (提取基于文档, 不臆造)。"""
    text = _load_contract()
    md_ids = _extract_clause_ids(text)
    md_names = re.findall(r"^### (QC-\d{3}) (.+)$", text, flags=re.MULTILINE)
    extracted = _extracted()
    assert len(md_ids) == len(extracted["rules"]) == 14
    for rule in extracted["rules"]:
        assert rule["status"] == "frozen"  # 契约整体 Frozen
        md_name = dict(md_names)[rule["id"]]
        assert rule["name"] == md_name, (
            f"{rule['id']} name mismatch: {rule['name']!r} vs {md_name!r}"
        )
