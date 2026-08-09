"""结构化校验器 (Phase 5.9A).

不依赖 isinstance(TypedDict) (TypedDict 仅静态类型); 采用运行时结构检查:
逐 key 验证存在性与类型 (支持嵌套 object/array 与 enum 约束)。

SPEC 格式 (与 types.py 中的 TYPE_SPECS 一致):
{
  "type": ["object" | "array" | "string" | "integer" | "number" | "boolean" | "null", ...],
  "required": [...],          # object 必填键
  "properties": {...},        # object 子规格
  "items": {...},             # array 元素规格
  "enum": [...]               # 可选枚举约束
}

类型语义: "number" 接受 int 与 float (JSON 数值);
"integer" 严格排除 bool; "boolean" 仅 bool; "null" 仅 None。
"""

from __future__ import annotations

from typing import Any


def type_name(value: Any) -> str:
    """值的运行时类型名 (与 SPEC 词汇一致)."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def type_allowed(observed: str, allowed: list[str]) -> bool:
    if observed in allowed:
        return True
    # JSON 数值: integer 是 number 的子集
    return observed == "integer" and "number" in allowed


def validate_structure(instance: Any, spec: dict, path: str = "$") -> list[str]:
    """校验 instance 是否符合 spec; 返回违规列表 (空 = 合规)."""
    allowed = spec.get("type", [])
    observed = type_name(instance)
    if not type_allowed(observed, allowed):
        return [f"{path}: expected {allowed}, got {observed}"]

    errs: list[str] = []
    if "enum" in spec and observed in ("string", "integer", "number", "boolean"):
        if instance not in spec["enum"]:
            errs.append(f"{path}: {instance!r} not in enum {spec['enum']}")

    if observed == "object" and "object" in allowed:
        props = spec.get("properties", {})
        for key in spec.get("required", []):
            if key not in instance:
                errs.append(f"{path}: missing required '{key}'")
        for key, value in instance.items():
            sub = props.get(key)
            if sub is None:
                errs.append(f"{path}: unexpected property '{key}'")
                continue
            errs += validate_structure(value, sub, f"{path}.{key}")
    elif observed == "array" and "array" in allowed:
        items = spec.get("items")
        if isinstance(items, dict) and items:
            for i, value in enumerate(instance):
                errs += validate_structure(value, items, f"{path}[{i}]")
    return errs


__all__ = ["type_name", "type_allowed", "validate_structure"]
