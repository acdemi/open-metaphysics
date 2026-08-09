"""Qimen Runtime 类型边界测试 (Phase 5.9A).

验证:
- types (SPEC) 与结构 inventory 一致 (字段/嵌套/基础类型来自实际输出)
- types 与 runtime 实际输出一致
- 24 Golden Vectors 结构验证 (输入/盘面/宫)
- ABI snapshot 新鲜度 (自动生成 vs 已存文件) 与元数据
"""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from openmetaphysics.agents.qimen import QimenAgent, QimenInput
from openmetaphysics.core.schemas import GeoPoint
from openmetaphysics.domain.qimen.abi import (
    build_abi_snapshot,
    build_structure_inventory,
    load_abi_snapshot,
)
from openmetaphysics.domain.qimen.structural import type_allowed, validate_structure
from openmetaphysics.domain.qimen.types import (
    QIMEN_INPUT_SPEC,
    QIMEN_OUTPUT_SPEC,
    QIMEN_PALACE_SPEC,
    TYPE_SPECS,
)

ROOT = Path(__file__).resolve().parent.parent
VECTORS_PATH = ROOT / "docs" / "qimen" / "golden_vectors.json"
SHANGHAI = ZoneInfo("Asia/Shanghai")


def _load_vectors() -> list[dict]:
    return json.loads(VECTORS_PATH.read_text(encoding="utf-8"))["vectors"]


def _vector_input(vector: dict) -> QimenInput:
    inp = dict(vector["input"])
    inp["born_at"] = datetime.fromisoformat(inp["born_at"])
    inp["born_location"] = GeoPoint(**inp["born_location"])
    return QimenInput.model_validate(inp)


def _spec_paths(spec: dict, prefix: str = "$") -> dict[str, list[str]]:
    """规格 → {path: allowed types} (与 inventory 同形)。"""
    paths = {prefix: list(spec.get("type", []))}
    if "object" in spec.get("type", []):
        for key, sub in spec.get("properties", {}).items():
            paths.update(_spec_paths(sub, f"{prefix}.{key}"))
    elif "array" in spec.get("type", []):
        items = spec.get("items")
        if isinstance(items, dict) and items:
            paths.update(_spec_paths(items, f"{prefix}[]"))
    return paths


def _inventory_compatible(inv_types: list[str], allowed: list[str]) -> bool:
    return all(type_allowed(t, allowed) for t in inv_types)


# ---------------------------------------------------------------------------
# 1) types ↔ inventory 一致
# ---------------------------------------------------------------------------
def test_types_consistent_with_inventory():
    """SPEC 字段/类型必须与 golden 向量 + runtime dump 的实测结构一致。"""
    vectors = _load_vectors()
    boards = [v["expected_board"] for v in vectors]
    # 含 runtime 全量输入 dump (覆盖可选字段 question/locale/seed/client_nonce/elevation_m)
    extra = QimenInput(
        request_id="inv",
        born_at=datetime(2024, 5, 1, 12, 0, tzinfo=SHANGHAI),
        gender="unknown",
        born_location=GeoPoint(latitude=39.9, longitude=116.4, timezone="Asia/Shanghai"),
    )
    inputs = [v["input"] for v in vectors] + [extra.model_dump(mode="json")]

    input_inv = build_structure_inventory(inputs)
    board_inv = build_structure_inventory(boards)

    for spec, inv, label in (
        (QIMEN_INPUT_SPEC, input_inv, "QimenInput"),
        (QIMEN_OUTPUT_SPEC, board_inv, "QimenOutput"),
    ):
        spec_paths = _spec_paths(spec)
        # 观测到的路径 ⊆ 规格路径; 类型兼容
        for path, observed in inv.items():
            assert path in spec_paths, f"{label}: inventory path {path!r} not in spec"
            assert _inventory_compatible(observed, spec_paths[path]), (
                f"{label}: {path} observed {observed} not allowed by spec {spec_paths[path]}"
            )
        # 必填键必须被观测到
        for required in spec.get("required", []):
            assert f"$.{required}" in inv, f"{label}: required '{required}' missing from inventory"

    # 宫结构单独核对 (board inventory 的 cells[] 路径)
    cell_prefix = "$.cells[]"
    palace_spec_paths = _spec_paths(QIMEN_PALACE_SPEC, prefix=cell_prefix)
    for path, allowed in palace_spec_paths.items():
        assert path in board_inv, f"QimenPalace: {path} missing from inventory"
        assert _inventory_compatible(board_inv[path], allowed), (
            f"QimenPalace: {path} observed {board_inv[path]} not allowed by {allowed}"
        )


# ---------------------------------------------------------------------------
# 2) types ↔ runtime 实际输出一致
# ---------------------------------------------------------------------------
def test_types_consistent_with_runtime_output():
    agent = QimenAgent()
    for vector in _load_vectors():
        payload = _vector_input(vector)
        out = agent.compute(payload)
        # 输入 dump 必须满足 QimenInput SPEC
        assert not validate_structure(payload.model_dump(mode="json"), QIMEN_INPUT_SPEC), vector[
            "id"
        ]
        # 输出 dump 必须满足 QimenOutput SPEC
        assert not validate_structure(out.result.model_dump(mode="json"), QIMEN_OUTPUT_SPEC), (
            vector["id"]
        )


# ---------------------------------------------------------------------------
# 3) Golden Vectors 结构验证
# ---------------------------------------------------------------------------
def test_golden_vectors_structural_validation():
    for vector in _load_vectors():
        assert not validate_structure(vector["input"], QIMEN_INPUT_SPEC), vector["id"]
        board = vector["expected_board"]
        assert not validate_structure(board, QIMEN_OUTPUT_SPEC), vector["id"]
        for cell in board["cells"]:
            assert not validate_structure(cell, QIMEN_PALACE_SPEC), vector["id"]


# ---------------------------------------------------------------------------
# 4) ABI snapshot: 新鲜度 + 元数据
# ---------------------------------------------------------------------------
def test_abi_snapshot_freshness():
    """快照必须与 types.py 当前生成结果一致 (过期即失败)。"""
    assert build_abi_snapshot() == load_abi_snapshot(), (
        "ABI snapshot is stale — regenerate docs/qimen/qimen_abi_snapshot.json"
    )


def test_abi_snapshot_metadata():
    snapshot = load_abi_snapshot()
    assert snapshot["abi"] == "qimen_runtime_abi"
    assert snapshot["contract_version"] == "1.0.0"
    assert snapshot["runtime_version"] == QimenAgent().engine_version == "0.3.0"
    assert set(snapshot["types"]) == {"QimenInput", "QimenPalace", "QimenOutput"}
    assert snapshot["types"] == TYPE_SPECS
    assert snapshot["source"] == "src/openmetaphysics/domain/qimen/types.py"
