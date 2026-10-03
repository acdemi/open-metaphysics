"""奇门遁甲 — 解释层 (Qimen explainer).

P2.2 Qimen Knowledge Integration. 与 `BaziExplainer` / `ZiweiExplainer` 同构:
继承既有 `Explainer`, **只**负责把 deterministic result 变成检索语义,
不重算盘面、不改结果、不引入第二套 Knowledge/RAG/Explain 架构。

存在的理由（实测, 见 P2.2 报告）:

* 通用 `Explainer.build_query` 对 qimen 只能取到 `dun_type`（ASCII `yang`/`yin`）
  与 `ju`（整数）, 二者都被 `_semantic_token` 过滤; 余下语义串一律取
  `cells[0]`（字典序 `cells` 最先）的前 6 个, 因此 **阴遁/阳遁、节气、局数、
  值符、值使永不进入查询**。
* 结果为 `dun_type == "yin"` 的盘面, 在既有查询下首位命中的却是「阳遁」节点 ——
  知识上下文与盘面语义不符（FACTS 仍权威, 但解释上下文质量受损）。

本类仅覆写 `build_query`; prompt 契约 (`_build_prompt`) 与离线 fallback
沿用通用实现, 因此 FACTS > KNOWLEDGE 的分离不变。
"""

from __future__ import annotations

from ..core.schemas import AgentOutput
from ..inference.explainer import Explainer
from .qimen import QimenBoard

# Qimen 盘面结构术语（固定解释语境, 与任何具体盘面无关）。
# 这些概念节点承载「九宫/八门/九星/八神/值符/值使/三奇/六仪」的定义,
# 是解释任何一张奇门盘都需要的基础语境。
_STRUCTURE_TERMS: tuple[str, ...] = (
    "奇门遁甲",
    "九宫",
    "八门",
    "九星",
    "八神",
    "值符",
    "值使",
    "三奇",
    "六仪",
    "旬首",
)

_DUN_TERMS = {"yang": "阳遁", "yin": "阴遁"}


class QimenExplainer(Explainer):
    """Qimen 专用检索查询构造（与通用 Explainer 共用同一解释链路）。"""

    @staticmethod
    def _board(output: AgentOutput) -> QimenBoard | None:
        """Read the already-computed board; never recompute it."""
        result = output.result
        if isinstance(result, QimenBoard):
            return result
        if isinstance(result, dict):
            try:
                return QimenBoard(**result)
            except Exception:
                return None
        return None

    @staticmethod
    def build_query(output: AgentOutput) -> str:
        """Deterministic Qimen query: 遁/局/节气/值符 + 盘面结构术语 + 用户问题.

        只读 `output.result`（已算好的确定性结果）, 不做任何推算; 结果不可解
        析时退回通用查询, 保证解释链路永不因查询构造失败。

        与 `Explainer.build_query` 同为 staticmethod, 保持同一个调用形态。
        """
        board = QimenExplainer._board(output)
        if board is None:
            return Explainer.build_query(output)

        parts: list[str] = ["qimen", *_STRUCTURE_TERMS]
        dun = _DUN_TERMS.get(board.dun_type)
        if dun:
            parts.append(dun)
        parts.append(f"{board.ju}局")
        if board.solar_term:
            parts.append(board.solar_term)

        # 值符：八神之值符所落之宫, 其九星即值符星（engine 已算好, 此处仅读取）
        for cell in board.cells:
            if cell.eight_gods == "值符":
                parts.append(cell.name)
                if cell.nine_stars:
                    parts.append(cell.nine_stars)
                break

        question = output.metadata.get("question")
        if isinstance(question, str) and question.strip():
            parts.append(question.strip())

        seen: set[str] = set()
        ordered = [p for p in parts if p and not (p in seen or seen.add(p))]
        return " ".join(ordered)
