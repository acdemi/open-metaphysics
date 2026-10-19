"""六爻 — 解释层 (Liuyao explainer).

P2.3 Liuyao Knowledge Integration. 与 `BaziExplainer` / `ZiweiExplainer` /
`QimenExplainer` 同构: 继承既有 `Explainer`, **只**负责把 deterministic
result 变成检索语义, 不重算卦盘、不改结果、不引入第二套 Knowledge/RAG/Explain
架构。

存在的理由（实测）:

* 通用 `Explainer.build_query` 对 liuyao 的 `_QUERY_FIELDS` 只取
  `palace` / `palace_element` / `yong_shen`, 余下语义串由
  `_iter_semantic_strings` 从结果里取前 6 个 —— 恰好被 `liu_qin` 的六个值占满,
  因此 **卦名、六神、世应、纳甲永不进入查询**。
* 例如 `casts=[7,8,7,8,7,8]` 的既济卦, 通用查询为
  `liuyao 坎 水 妻财 事业与财运 子孙 官鬼 兄弟 父母`: 六神与卦名缺失,
  解释上下文无法覆盖本卦的结构语义。

本类仅覆写 `build_query`; prompt 契约与离线 fallback 沿用通用实现, 因此
FACTS > KNOWLEDGE 的分离不变。
"""

from __future__ import annotations

from ..core.models import HEXAGRAMS
from ..core.schemas import AgentOutput
from ..inference.explainer import Explainer
from .liuyao import LiuyaoChart

# 六爻盘面结构术语（固定解释语境, 与任何具体卦盘无关）。
# 这些概念节点承载「六亲/六神/世应/纳甲/用神」的定义, 是解释任何一卦
# 都需要的基础语境。
_STRUCTURE_TERMS: tuple[str, ...] = (
    "六爻",
    "六亲",
    "六神",
    "世应",
    "纳甲",
    "用神",
)


class LiuyaoExplainer(Explainer):
    """Liuyao 专用检索查询构造（与通用 Explainer 共用同一解释链路）。"""

    @staticmethod
    def _chart(output: AgentOutput) -> LiuyaoChart | None:
        """Read the already-computed chart; never recompute it."""
        result = output.result
        if isinstance(result, LiuyaoChart):
            return result
        if isinstance(result, dict):
            try:
                return LiuyaoChart(**result)
            except Exception:
                return None
        return None

    @staticmethod
    def _hexagram_name(number: int | None) -> str | None:
        if not number or not 1 <= number <= len(HEXAGRAMS):
            return None
        return str(HEXAGRAMS[number - 1]["name"])

    @staticmethod
    def build_query(output: AgentOutput) -> str:
        """Deterministic Liuyao query: 卦名/宫/用神/六亲/六神 + 结构术语 + 问题.

        只读 `output.result`（已算好的确定性结果）, 不做任何推算; 结果不可解析
        时退回通用查询, 保证解释链路永不因查询构造失败。
        """
        chart = LiuyaoExplainer._chart(output)
        if chart is None:
            return Explainer.build_query(output)

        parts: list[str] = ["liuyao", *_STRUCTURE_TERMS]

        for number in (chart.original_hexagram, chart.changed_hexagram):
            name = LiuyaoExplainer._hexagram_name(number)
            if name:
                parts.append(name)
        if chart.palace:
            parts.append(f"{chart.palace}宫")
        if chart.palace_element:
            parts.append(chart.palace_element)
        if chart.yong_shen:
            parts.append(chart.yong_shen)

        # 用神爻与世爻是断卦的两个焦点: 取其六亲/六神作为检索语义。
        focus_lines: list[int] = [chart.shi_position - 1]
        if chart.yong_shen in chart.liu_qin:
            focus_lines.insert(0, chart.liu_qin.index(chart.yong_shen))
        for index in focus_lines:
            if 0 <= index < len(chart.liu_qin):
                parts.append(chart.liu_qin[index])
            if 0 <= index < len(chart.liu_shen):
                parts.append(chart.liu_shen[index])

        question = output.metadata.get("question")
        if isinstance(question, str) and question.strip():
            parts.append(question.strip())

        seen: set[str] = set()
        ordered = [p for p in parts if p and not (p in seen or seen.add(p))]
        return " ".join(ordered)
