"""QimenContractAdapter — Runtime ↔ Contract 显式验证层 (Phase 5.8B).

职责: 输入合规性 / 输出合规性 / Golden Vector 回归验证。
**不负责计算逻辑** —— 仅做类型、范围、结构校验; 排盘计算委托现有 runtime
(`src/openmetaphysics/agents/qimen.py`), 不修改也不复制其算法。

纪律:
- 不修改 qimen.py 核心算法 / QIMEN_BEHAVIOR_CONTRACT.md / golden_vectors.json
- 不调用任何 LLM 或外部推理 API
- 轻量: 校验输入为原始 dict (year/month/day/hour), 输出为 QimenBoard JSON

与 `src/openmetaphysics/contracts/qimen_contract.py` (Phase 5.8, 契约清单/
schema 校验) 分工: 本模块面向运行时输入/输出/回归, contracts 包面向契约
元数据与清单。两者均不参与排盘计算。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 校验范围常量 (仅类型/范围/结构)
# ---------------------------------------------------------------------------
_YEAR_RANGE = (1900, 2100)
_MONTH_RANGE = (1, 12)
_DAY_RANGE = (1, 31)
_HOUR_RANGE = (0, 23)

_BOARD_FIELDS = ("solar_term", "ju", "dun_type", "day_of_month", "triple_offset", "cells")
_CELL_FIELDS = (
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
)


def _is_int(value: Any) -> bool:
    """严格整数 (排除 bool)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _in_range(value: int, lo: int, hi: int) -> bool:
    return lo <= value <= hi


class QimenContractAdapter:
    """契约 v1.0.0 的显式验证层 (类型/范围/结构, 无排盘计算)."""

    contract_version = "1.0.0"  # 硬编码: QIMEN_BEHAVIOR_CONTRACT.md v1.0.0

    def __init__(self, vectors_path: str | Path | None = None) -> None:
        self._vectors_path = Path(vectors_path) if vectors_path else None
        self._verified_count = 0

    # -- 输入合规性 -----------------------------------------------------------
    def validate_input(self, raw_input: dict) -> bool:
        """校验原始输入字段完整性: year/month/day/hour 存在且合法。

        仅检查类型与范围 (含真实日期合法性), 不做任何排盘计算。
        """
        if not isinstance(raw_input, dict):
            return False
        for key in ("year", "month", "day", "hour"):
            if key not in raw_input:
                return False
        values = raw_input
        if not (
            _is_int(values["year"])
            and _is_int(values["month"])
            and _is_int(values["day"])
            and _is_int(values["hour"])
        ):
            return False
        if not (
            _in_range(values["year"], *_YEAR_RANGE)
            and _in_range(values["month"], *_MONTH_RANGE)
            and _in_range(values["day"], *_DAY_RANGE)
            and _in_range(values["hour"], *_HOUR_RANGE)
        ):
            return False
        try:
            datetime(values["year"], values["month"], values["day"], values["hour"])
        except ValueError:
            return False  # 真实日期校验 (如 2 月 30 日)
        return True

    # -- 输出合规性 -----------------------------------------------------------
    def validate_output(self, raw_output: dict) -> bool:
        """校验输出结构包含契约承诺字段 (QimenBoard JSON, 类型/范围/结构)。"""
        if not isinstance(raw_output, dict):
            return False
        for key in _BOARD_FIELDS:
            if key not in raw_output:
                return False
        if not isinstance(raw_output["solar_term"], str) or not raw_output["solar_term"]:
            return False
        if not _is_int(raw_output["ju"]) or not _in_range(raw_output["ju"], 1, 9):
            return False
        if raw_output["dun_type"] not in ("yang", "yin"):
            return False
        if not _is_int(raw_output["day_of_month"]) or not _in_range(
            raw_output["day_of_month"], 1, 31
        ):
            return False
        if raw_output["triple_offset"] not in (0, 3, 6):
            return False
        cells = raw_output["cells"]
        if not isinstance(cells, list) or len(cells) != 9:
            return False
        palaces: list[int] = []
        for cell in cells:
            if not isinstance(cell, dict):
                return False
            for key in _CELL_FIELDS:
                if key not in cell:
                    return False
            if not _is_int(cell["palace"]) or not _in_range(cell["palace"], 1, 9):
                return False
            palaces.append(cell["palace"])
            if not isinstance(cell["name"], str):
                return False
            for key in (
                "sky_plate",
                "earth_plate",
                "eight_gods",
                "nine_stars",
                "eight_doors",
                "three_qi",
            ):
                if cell[key] is not None and not isinstance(cell[key], str):
                    return False
            for key in ("is_void", "is_central"):
                if not isinstance(cell[key], bool):
                    return False
        return len(set(palaces)) == 9  # 宫位唯一 (结构完整性)

    # -- Golden Vector 回归验证 -----------------------------------------------
    def verify_golden_vector(self, vector: dict) -> bool:
        """对比计算值是否符合预期: 委托现有 runtime 计算, 与 expected_board 比对。

        不修改 runtime; 计算失败或结果不一致均返回 False。
        """
        try:
            from ...agents.qimen import QimenAgent, QimenInput
            from ...core.schemas import GeoPoint

            inp = dict(vector["input"])
            inp["born_at"] = datetime.fromisoformat(inp["born_at"])
            inp["born_location"] = GeoPoint(**inp["born_location"])
            payload = QimenInput.model_validate(inp)
            result = QimenAgent().compute(payload).result.model_dump(mode="json")
        except Exception:
            return False
        ok = result == vector.get("expected_board")
        if ok:
            self._verified_count += 1
        return ok

    def load_golden_vectors(self) -> list[dict]:
        """读取规范向量 (可选; 不校验时无需调用)."""
        path = self._vectors_path
        if path is None:
            path = Path(__file__).resolve().parents[3] / "docs" / "qimen" / "golden_vectors.json"
        if not path.exists():
            raise FileNotFoundError(f"vectors missing: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return data["vectors"]

    # -- 契约状态 -------------------------------------------------------------
    def get_contract_status(self) -> dict[str, Any]:
        """返回当前实现的契约版本与合规状态。"""
        from ...agents.qimen import QimenAgent

        return {
            "contract_id": "qimen:behavior:v1.0.0",
            "contract_version": self.contract_version,
            "status": "Frozen",
            "engine_version": QimenAgent().engine_version,
            "rule_set_version": "0.3.0",
            "adapter": "domain.qimen.adapter",
            "golden_vectors_verified": self._verified_count,
        }
