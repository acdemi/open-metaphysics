"""Qimen Runtime ABI snapshot (Phase 5.9A).

从 types.py 的 TYPE_SPECS 自动生成 ABI 快照 (JSON), 作为未来跨语言实现的
类型边界参考。快照文件: docs/qimen/qimen_abi_snapshot.json。
freshness 由 tests/test_qimen_abi.py 强制 (重新生成并比对)。
"""

from __future__ import annotations

import json
from pathlib import Path

from .structural import type_name
from .types import TYPE_SPECS

_REPO_ROOT = Path(__file__).resolve().parents[4]

SNAPSHOT_PATH = _REPO_ROOT / "docs" / "qimen" / "qimen_abi_snapshot.json"


def build_abi_snapshot() -> dict:
    """从 types.py 自动生成 ABI 快照 (含契约与运行时版本)。"""
    from ...agents.qimen import QimenAgent

    return {
        "abi": "qimen_runtime_abi",
        "contract_version": "1.0.0",  # QIMEN_BEHAVIOR_CONTRACT.md v1.0.0
        "runtime_version": QimenAgent().engine_version,
        "source": "src/openmetaphysics/domain/qimen/types.py",
        "types": TYPE_SPECS,
    }


def load_abi_snapshot(path: str | Path | None = None) -> dict:
    """读取已生成快照。"""
    target = Path(path) if path else SNAPSHOT_PATH
    if not target.exists():
        raise FileNotFoundError(f"abi snapshot missing: {target}")
    return json.loads(target.read_text(encoding="utf-8"))


def write_abi_snapshot(path: str | Path | None = None) -> Path:
    """生成/刷新快照文件 (测试仅比对, 不写文件)。"""
    target = Path(path) if path else SNAPSHOT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_abi_snapshot(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    return target


def build_structure_inventory(objects: list[dict]) -> dict[str, list[str]]:
    """从实际对象集合提取结构 inventory: {path: [observed types]}.

    path 形如 "$.cells[].sky_plate"; 数组元素以 "[]" 表示。
    """
    inv: dict[str, set[str]] = {}

    def walk(value: object, path: str) -> None:
        inv.setdefault(path, set()).add(type_name(value))
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, f"{path}.{key}")
        elif isinstance(value, list):
            for item in value:
                walk(item, f"{path}[]")

    for obj in objects:
        walk(obj, "$")
    return {path: sorted(types) for path, types in sorted(inv.items())}


__all__ = [
    "SNAPSHOT_PATH",
    "build_abi_snapshot",
    "load_abi_snapshot",
    "write_abi_snapshot",
    "build_structure_inventory",
]
