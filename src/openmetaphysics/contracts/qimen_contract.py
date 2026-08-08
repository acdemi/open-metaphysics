"""Qimen Contract Adapter — 机器可验证的契约适配层 (Phase 5.8).

职责:
- 承载契约 v1.0.0 的机器可读清单 (MANIFEST), 由 qimen_contract.schema.json 校验
- validate_input: 校验输入满足契约前置条件
- validate_output: 校验输出满足契约可观察要求 (QC-001~014)
- validate_golden_vectors: 24 规范向量 → 运行时逐字节复算比对

纪律:
- 不修改运行时 (agents.qimen 只读导入)
- 不新增任何 Qimen 规则 (校验项全部源自契约条款)
- 不改变运行时行为

已知漂移 (非阻塞, warning):
- golden_vectors.json 为冻结前产物, 其 deferred_rules 仍为 ['D2','D14'];
  契约 v1.0.0 已裁定两者为规范 (frozen D1-D14)。向量元数据对齐需后续授权
  Sprint (本 Sprint 禁止修改 golden_vectors.json)。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..agents.qimen import (
    EIGHT_DOORS,
    EIGHT_GODS,
    NINE_STARS,
    PALACE_NAMES_9,
    SANQI,
    QimenBoard,
    QimenInput,
)
from ..core.schemas import GeoPoint

__version__ = "0.3.0"

_CONTRACT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _CONTRACT_DIR.parents[2]

# ---------------------------------------------------------------------------
# 契约清单 (机器可读; 与 qimen_contract.schema.json 严格一致)
# ---------------------------------------------------------------------------
MANIFEST: dict[str, Any] = {
    "contract_id": "qimen:behavior:v1.0.0",
    "version": "1.0.0",
    "status": "Frozen",
    "system": "qimen",
    "engine_version": "0.3.0",
    "rule_set_version": "0.3.0",
    "frozen_rules": [
        "D1",
        "D3",
        "D4",
        "D5",
        "D6",
        "D7",
        "D8",
        "D9",
        "D10",
        "D11",
        "D12",
        "D13",
        "D14",
    ],
    "deferred_rules": [],
    "qc_ids": [f"QC-{i:03d}" for i in range(1, 15)],
    "golden_vector_count": 24,
    "vector_classification": "normative_fixture",
    "vector_store": "docs/qimen/golden_vectors.json",
    "contract_doc": "docs/specification/QIMEN_BEHAVIOR_CONTRACT.md",
}

_BOARD_KEY_ORDER = ["solar_term", "ju", "dun_type", "day_of_month", "triple_offset", "cells"]
_CELL_KEY_ORDER = [
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
]
_PLATE_SET = {"戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"}


# ---------------------------------------------------------------------------
# 轻量 JSON Schema 子集校验器 (const/enum/type/required/items/minItems/
# uniqueItems/maxItems/properties/additionalProperties)
# ---------------------------------------------------------------------------
def _schema_errors(instance: Any, schema: dict, path: str) -> list[str]:
    errs: list[str] = []
    if "const" in schema and instance != schema["const"]:
        errs.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errs.append(f"{path}: {instance!r} not in enum {schema['enum']}")
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
            errs += _schema_errors(value, sub, f"{path}.{key}")
    elif typ == "array" and isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errs.append(f"{path}: minItems {schema['minItems']} violated")
        if len(instance) > schema.get("maxItems", 1 << 30):
            errs.append(f"{path}: maxItems {schema['maxItems']} violated")
        if schema.get("uniqueItems") and len(instance) != len(set(instance)):
            errs.append(f"{path}: items must be unique")
        item_schema = schema.get("items", {})
        if isinstance(item_schema, dict) and item_schema:
            for i, item in enumerate(instance):
                errs += _schema_errors(item, item_schema, f"{path}[{i}]")
    elif typ is not None and typ not in ("object", "array"):
        if (
            not isinstance(instance, (str, int, float, bool))
            or (typ == "string" and not isinstance(instance, str))
            or (typ == "integer" and not isinstance(instance, int))
        ):
            errs.append(f"{path}: expected type {typ}")
    return errs


class QimenContractAdapter:
    """契约 ↔ Runtime 适配层 (v1.0.0 Frozen)."""

    contract_id = MANIFEST["contract_id"]
    version = MANIFEST["version"]
    status = MANIFEST["status"]
    engine_version = MANIFEST["engine_version"]
    rule_set_version = MANIFEST["rule_set_version"]
    qc_ids = list(MANIFEST["qc_ids"])

    def __init__(self, vectors_path: str | Path | None = None) -> None:
        self._schema_path = _CONTRACT_DIR / "qimen_contract.schema.json"
        self._vectors_path = (
            Path(vectors_path) if vectors_path else _REPO_ROOT / MANIFEST["vector_store"]
        )

    # -- 资源 ---------------------------------------------------------------
    def load_schema(self) -> dict:
        return json.loads(self._schema_path.read_text(encoding="utf-8"))

    def load_vectors(self) -> dict:
        if not self._vectors_path.exists():
            raise FileNotFoundError(f"vectors missing: {self._vectors_path}")
        return json.loads(self._vectors_path.read_text(encoding="utf-8"))

    # -- schema / manifest --------------------------------------------------
    def validate_manifest(self, manifest: dict | None = None) -> list[str]:
        """清单须满足 qimen_contract.schema.json (version/QC/frozen status)."""
        target = manifest if manifest is not None else MANIFEST
        return _schema_errors(target, self.load_schema(), "$")

    # -- 运行时对齐 ----------------------------------------------------------
    def validate_runtime_alignment(self) -> list[str]:
        """适配层符号表与运行时符号表一致 (单一真源)."""
        errs: list[str] = []
        if set(NINE_STARS.values()) != _STAR_SET:
            errs.append("nine_stars set mismatch with contract")
        if set(EIGHT_DOORS.values()) - {None} != set(_DOOR_SET):
            errs.append("eight_doors set mismatch with contract")
        if set(EIGHT_GODS) != set(_GOD_SET):
            errs.append("eight_gods set mismatch with contract")
        if set(SANQI) != set(_SANQI_SET):
            errs.append("sanqi set mismatch with contract")
        if set(PALACE_NAMES_9.values()) != set(_PALACE_NAME_SET):
            errs.append("palace names mismatch with contract")
        return errs

    # -- 输入校验 (契约前置条件) ----------------------------------------------
    def validate_input(self, payload: Any) -> list[str]:
        """QC-001 前置: 合法 QimenInput 且 born_at tz-aware."""
        if isinstance(payload, dict):
            try:
                payload = QimenInput.model_validate(payload)
            except Exception as exc:  # pydantic ValidationError
                return [f"QC-001: invalid input: {exc}"]
        if not isinstance(payload, QimenInput):
            return ["QC-001: input must be QimenInput or a compatible dict"]
        errs: list[str] = []
        if payload.born_at.tzinfo is None:
            errs.append("QC-001: born_at must be timezone-aware")
        loc = payload.born_location
        if loc is not None and not isinstance(loc, GeoPoint):
            errs.append("QC-001: born_location must be a GeoPoint")
        return errs

    # -- 输出校验 (契约可观察要求) ---------------------------------------------
    def validate_output(self, board: Any) -> list[str]:
        """QC-002 ~ QC-014 可观察不变量 (机器可检查部分)."""
        if isinstance(board, QimenBoard):
            board = board.model_dump(mode="json")
        if not isinstance(board, dict) or "cells" not in board:
            return ["QC-002: output must be a QimenBoard with cells"]

        errs: list[str] = []
        cells = board["cells"]
        # QC-001/002: 序列化键序稳定 + 9 宫唯一
        if list(board.keys()) != _BOARD_KEY_ORDER:
            errs.append("QC-001/002: board key order unstable")
        if len(cells) != 9:
            errs.append(f"QC-002: expected 9 cells, got {len(cells)}")
        palaces = [c.get("palace") for c in cells]
        if palaces != list(range(1, 10)):
            errs.append(f"QC-002: palaces must be 1..9 unique, got {palaces}")
        # QC-003/004: 遁/局/三元
        if board.get("dun_type") not in ("yang", "yin"):
            errs.append(f"QC-003: dun_type {board.get('dun_type')!r} invalid")
        if not isinstance(board.get("ju"), int) or not 1 <= board["ju"] <= 9:
            errs.append(f"QC-004: ju {board.get('ju')!r} out of [1,9]")
        if board.get("triple_offset") not in (0, 3, 6):
            errs.append(f"QC-004: triple_offset {board.get('triple_offset')!r} invalid")
        if board.get("solar_term") is None:
            errs.append("QC-003: solar_term missing")

        sky = [c.get("sky_plate") for c in cells]
        earth = [c.get("earth_plate") for c in cells]
        stars = [c.get("nine_stars") for c in cells]
        doors = [c.get("eight_doors") for c in cells]
        gods = [c.get("eight_gods") for c in cells]
        # QC-005/006: 天地盘
        for name, plates in (("sky_plate", sky), ("earth_plate", earth)):
            if None in plates or set(plates) != _PLATE_SET or len(set(plates)) != 9:
                errs.append(f"QC-005/006: {name} must be 9 distinct 六仪三奇")
        # QC-009: 九星
        if None in stars or set(stars) != _STAR_SET or len(set(stars)) != 9:
            errs.append("QC-009: nine_stars must be 9 distinct")
        # QC-010/011: 门神 — None 仅限中宫, 其余 8 个互异
        for name, items, full in (
            ("eight_doors", doors, _DOOR_SET),
            ("eight_gods", gods, _GOD_SET),
        ):
            non_none = [x for x in items if x is not None]
            if len(non_none) != 8 or len(set(non_none)) != 8 or set(non_none) != full:
                errs.append(f"QC-010/011: {name} must be 8 distinct, got {non_none}")
            for c in cells:
                if c.get("is_central") and c.get(name) is not None:
                    errs.append(f"QC-010/011: central palace must have no {name}")
                if not c.get("is_central") and c.get(name) is None:
                    errs.append(f"QC-010/011: non-central palace missing {name}")
        # QC-012: 三奇
        sanqi = [c.get("three_qi") for c in cells if c.get("three_qi") is not None]
        if len(sanqi) != 3 or set(sanqi) != _SANQI_SET or len(set(sanqi)) != 3:
            errs.append(f"QC-012: three_qi must be exactly 乙丙丁, got {sanqi}")
        # QC-013: 空亡 1~2 宫
        void = [c.get("palace") for c in cells if c.get("is_void")]
        if not 1 <= len(void) <= 2:
            errs.append(f"QC-013: void palaces must be 1-2, got {void}")
        # QC-014: 中宫
        central = [c.get("palace") for c in cells if c.get("is_central")]
        if central != [5]:
            errs.append(f"QC-014: is_central must be exactly palace 5, got {central}")
        return errs

    # -- 向量校验 --------------------------------------------------------------
    def validate_vector(self, vector: dict) -> tuple[list[str], list[str]]:
        """单个规范向量: 元数据一致 + expected_board 不变量 + 运行时复算。"""
        errs: list[str] = []
        warns: list[str] = []
        vid = vector.get("id", "?")
        required = (
            "id",
            "input",
            "expected_board",
            "engine_version",
            "rule_set_version",
            "frozen_rules",
            "deferred_rules",
            "assumptions_reference",
            "decision_reference",
            "classification",
        )
        for key in required:
            if key not in vector:
                errs.append(f"{vid}: missing metadata '{key}'")
        if vector.get("engine_version") != self.engine_version:
            errs.append(
                f"{vid}: engine_version {vector.get('engine_version')!r} != {self.engine_version}"
            )
        if vector.get("rule_set_version") != self.rule_set_version:
            errs.append(
                f"{vid}: rule_set_version {vector.get('rule_set_version')!r} != {self.rule_set_version}"
            )
        if vector.get("classification") != "normative_fixture":
            errs.append(
                f"{vid}: classification {vector.get('classification')!r} != normative_fixture"
            )
        if vector.get("deferred_rules"):
            warns.append(
                f"{vid}: deferred_rules {vector['deferred_rules']} drift vs contract "
                "(D2/D14 resolved in v1.0.0; vector metadata pre-freeze — alignment needs authorization)"
            )
        errs += [f"{vid}: {e}" for e in self.validate_output(vector.get("expected_board"))]
        # 运行时复算 + 确定性
        try:
            payload = QimenInput.model_validate(vector["input"])
        except Exception as exc:
            return errs + [f"{vid}: input invalid: {exc}"], warns
        from ..agents.qimen import QimenAgent

        agent = QimenAgent()
        out1 = agent.compute(payload)
        out2 = agent.compute(payload)
        if out1.result.model_dump(mode="json") != vector["expected_board"]:
            errs.append(f"{vid}: runtime board != expected_board")
        if out2.result.model_dump(mode="json") != out1.result.model_dump(mode="json"):
            errs.append(f"{vid}: non-deterministic replay")
        return errs, warns

    def validate_golden_vectors(self) -> dict[str, Any]:
        """全部 24 规范向量校验。"""
        data = self.load_vectors()
        report: dict[str, Any] = {"total": 0, "ok": 0, "errors": {}, "warnings": {}}
        for vector in data["vectors"]:
            errs, warns = self.validate_vector(vector)
            report["total"] += 1
            if not errs:
                report["ok"] += 1
            else:
                report["errors"][vector["id"]] = errs
            if warns:
                report["warnings"][vector["id"]] = warns
        return report


# 契约符号集 (QC-002/009/010/011/012 机器表达; 与运行时表一致性由
# validate_runtime_alignment 强制)
_STAR_SET = {"天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"}
_DOOR_SET = {"休门", "死门", "伤门", "杜门", "开门", "惊门", "生门", "景门"}
_GOD_SET = {"值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"}
_SANQI_SET = set(SANQI)
_PALACE_NAME_SET = set(PALACE_NAMES_9.values())


def load_manifest() -> dict[str, Any]:
    """契约清单 (深拷贝, 防外部修改)."""
    return json.loads(json.dumps(MANIFEST))
