"""Qimen Runtime 数据类型边界 (Phase 5.9A).

TypedDict 定义 + 结构 SPEC (机器可校验), 为未来跨语言实现提供 ABI 参考。
全部字段来自现有 Runtime 实际输出 (golden_vectors.json 与
`model_dump(mode="json")` 的结构 inventory), 不根据概念臆造。

形态约定: 类型定义采用 JSON 形态 (跨语言边界形态);
运行时原生形态 (如 born_at 为 tz-aware datetime) 在注释中注明。
"""

from __future__ import annotations

from typing import NotRequired, TypedDict


class GeoPointDict(TypedDict):
    """出生地坐标 (JSON 形态)."""

    latitude: float
    longitude: float
    elevation_m: NotRequired[float | None]
    timezone: NotRequired[str | None]


class QimenInput(TypedDict):
    """奇门排盘输入信封 (JSON 形态; 运行时 born_at 为 tz-aware datetime)."""

    request_id: str
    born_at: str  # ISO 8601
    born_location: NotRequired[GeoPointDict | None]
    gender: str  # "male" | "female" | "unknown"
    question: NotRequired[str | None]
    locale: NotRequired[str]
    seed: NotRequired[int | None]
    client_nonce: NotRequired[str | None]


class QimenPalace(TypedDict):
    """九宫中的一宫 (QimenCell JSON 形态)."""

    palace: int  # 1..9 洛书宫位
    name: str  # 坎坤震巽中宫乾兑艮离
    sky_plate: str | None
    earth_plate: str | None
    eight_gods: str | None
    nine_stars: str | None
    eight_doors: str | None
    three_qi: str | None
    is_void: bool
    is_central: bool


class QimenOutput(TypedDict):
    """排盘结果 (QimenBoard JSON 形态; 即 agent 信封的 result 字段)."""

    solar_term: str | None
    ju: int  # 1..9
    dun_type: str  # "yang" | "yin"
    day_of_month: int
    triple_offset: int  # 0 | 3 | 6
    cells: list[QimenPalace]  # 恒 9 宫


# ---------------------------------------------------------------------------
# 结构 SPEC (机器可校验; 与 TypedDict 同源, 供 structural validator 与
# ABI snapshot 使用)
# ---------------------------------------------------------------------------
_GEO_POINT_SPEC: dict = {
    "type": ["object"],
    "required": ["latitude", "longitude"],
    "properties": {
        "latitude": {"type": ["number"]},
        "longitude": {"type": ["number"]},
        "elevation_m": {"type": ["number", "null"]},
        "timezone": {"type": ["string", "null"]},
    },
}

QIMEN_INPUT_SPEC: dict = {
    "type": ["object"],
    "required": ["request_id", "born_at", "gender"],
    "properties": {
        "request_id": {"type": ["string"]},
        "born_at": {"type": ["string"]},
        "born_location": {
            "type": ["object", "null"],
            "properties": _GEO_POINT_SPEC["properties"],
            "required": _GEO_POINT_SPEC["required"],
        },
        "gender": {"type": ["string"], "enum": ["male", "female", "unknown"]},
        "question": {"type": ["string", "null"]},
        "locale": {"type": ["string"]},
        "seed": {"type": ["integer", "null"]},
        "client_nonce": {"type": ["string", "null"]},
    },
}

QIMEN_PALACE_SPEC: dict = {
    "type": ["object"],
    "required": [
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
    ],
    "properties": {
        "palace": {"type": ["integer"]},
        "name": {"type": ["string"]},
        "sky_plate": {"type": ["string", "null"]},
        "earth_plate": {"type": ["string", "null"]},
        "eight_gods": {"type": ["string", "null"]},
        "nine_stars": {"type": ["string", "null"]},
        "eight_doors": {"type": ["string", "null"]},
        "three_qi": {"type": ["string", "null"]},
        "is_void": {"type": ["boolean"]},
        "is_central": {"type": ["boolean"]},
    },
}

QIMEN_OUTPUT_SPEC: dict = {
    "type": ["object"],
    "required": ["solar_term", "ju", "dun_type", "day_of_month", "triple_offset", "cells"],
    "properties": {
        "solar_term": {"type": ["string", "null"]},
        "ju": {"type": ["integer"]},
        "dun_type": {"type": ["string"], "enum": ["yang", "yin"]},
        "day_of_month": {"type": ["integer"]},
        "triple_offset": {"type": ["integer"]},
        "cells": {"type": ["array"], "items": QIMEN_PALACE_SPEC},
    },
}

# 类型规格注册表 (ABI snapshot 与测试使用)
TYPE_SPECS: dict[str, dict] = {
    "QimenInput": QIMEN_INPUT_SPEC,
    "QimenPalace": QIMEN_PALACE_SPEC,
    "QimenOutput": QIMEN_OUTPUT_SPEC,
}

__all__ = [
    "GeoPointDict",
    "QimenInput",
    "QimenPalace",
    "QimenOutput",
    "QIMEN_INPUT_SPEC",
    "QIMEN_PALACE_SPEC",
    "QIMEN_OUTPUT_SPEC",
    "TYPE_SPECS",
]
