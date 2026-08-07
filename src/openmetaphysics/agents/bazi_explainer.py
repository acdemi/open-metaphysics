from __future__ import annotations

import json
from typing import Any

from jinja2 import Template

from ..core.schemas import AgentOutput, Gender
from ..inference.explainer import Explainer
from .bazi import BaziChart

BAZI_SYSTEM_PROMPT = """# 角色设定 (Role)
你是一位精通《渊海子平》与《子平真诠》的命理分析师，严谨、客观、不宿命论。你擅长解读“十神”组合与“格局”气势。

# 核心铁律 (Golden Rules)
1. **数据驱动**：你的所有分析必须严格基于【输入数据】中提供的 pillars（四柱）、	en_gods_map（十神映射）和 dayun（大运）。**严禁**凭空编造干支或十神关系。
2. **只做翻译，不做推算**：引擎已经计算好了“身强/身弱”和“格局”。如果输入数据中未明确给出“用神”，请基于“平衡/调候”原理进行逻辑推导，但必须明确标注“此为引擎推算之外的辅助建议”。
3. **可追溯性**：在分析关键节点（如“七杀格”成立）时，必须引用 
easoning_trace 中的规则名（如 
ule_ref: bazi.month_pillar.ten_god），以体现可解释性。
4. **非决定论导向**：最终建议必须强调“顺势而为”和“后天人事调整”，严禁给出“必死”“大凶”等绝对化宿命论断语。

# 分析结构化流程 (SOP)
请按以下四步逻辑组织你的回答（必须包含小标题）：
1. **定格取用**：基于月令主气与天干透出，判定格局名称。
2. **气势流通**：分析八字中五行生克链，找出最强/最弱的气场，以及关键的“通关”或“制衡”十神。
3. **十神组合精析**：解读关键组合（如“伤官配印”、“官杀混杂”、“食神生财”）对性格/运势的影响。
4. **大运介入**：结合当前输入的大运，分析运程对原局格局的“扶抑”或“变化”作用。

# 十神底层逻辑速查 (Contextual Aid)
- **正官/七杀 (官杀)**：代表事业、压力。官杀混杂需取清，身弱逢杀需印化（杀印相生）。
- **正印/偏印 (印星)**：代表学识、长辈。印星过重则懒散，印星受损则学业受阻。
- **食神/伤官 (食伤)**：代表才华、表达。食神生财主富，伤官见官主口舌是非，伤官配印主智慧。
- **正财/偏财 (财星)**：代表财富、父亲/妻子。财星喜藏，也喜食伤来生，忌比劫夺财。
- **比肩/劫财 (比劫)**：代表同辈、竞争者。身弱喜比劫帮身，身强忌比劫夺财。

**格局判定核心**：
- 定格以 **月令（月支主气）** 为第一优先。若月令主气透出天干，则以该十神定格局（如甲木生于酉月，酉藏辛金为甲之正官，为正官格）。
- 若月令藏干不透，则看天干中得根最强的十神，或视情况取“外格”（如从财格、从杀格）。
"""


USER_PROMPT_TEMPLATE = Template("""
请分析以下八字数据：

【基础信息】
日主 (Day Master)：{{day_master}}（{{day_master_element}}）
出生性别：{{gender_text}}
当前输入问题：{{question}}

【四柱排盘 (Pillars)】
年柱：{{year_pillar}} | 藏干：{{year_hidden}} | 十神关系：{{year_god}}
月柱：{{month_pillar}} | 藏干：{{month_hidden}} | 十神关系：{{month_god}}  <- 关键（格神所在）
日柱：{{day_pillar}} | 藏干：{{day_hidden}} | 十神关系：{{day_god}}
时柱：{{hour_pillar}} | 藏干：{{hour_hidden}} | 十神关系：{{hour_god}}

月令为【{{month_earthly_branch}}】，藏干为【{{month_hidden_stems}}】，其中主气【{{dominant_hidden}}】透于天干【{{if_transparent}}】，故以【{{pattern_ten_god}}】定格。

【十神全映射 (Ten Gods Map)】
{{ten_gods_map_json}}

【大运走势 (Da Yun)】
{{dayun_list}}  (注：请重点关注距离当前年龄最近的那组干支)

【引擎计算置信度】
Confidence Score: {{confidence_value}}
计算因子：{{confidence_factors}}

{% if confidence_value < 0.6 %}
【关键警告】
由于本次排盘置信度低于阈值（Confidence < 0.6），可能是由于出生时间不精确或处于节气交接时刻。
请在回答开篇声明：“此局边界模糊，以下分析需结合具体大运流年及面诊核实，请谨慎参考。”
{% endif %}

---
请严格按照 System Prompt 的 SOP 展开分析，输出 300-500 字的结构化解读。
""")


class BaziExplainer(Explainer):
    """Bazi-specific explainer with specialized prompt engineering for 十神/格局 analysis.

    Follows strict separation of concerns: Engine computes, LLM only translates
    structured results to natural language. Never modifies the computed result.
    """

    def _get_pattern_info(self, chart: BaziChart) -> dict[str, Any]:
        """Extract pattern information from the chart for prompt injection."""
        month_pillar = next(p for p in chart.pillars if p.position == "month")
        hidden_stems = month_pillar.hidden_stems
        dominant_hidden = hidden_stems[0] if hidden_stems else ""
        pattern_ten_god = chart.ten_gods_map.get(dominant_hidden, "未知")
        is_transparent = dominant_hidden in [p.stem for p in chart.pillars]
        return {
            "month_earthly_branch": month_pillar.branch,
            "month_hidden_stems": "、".join(hidden_stems),
            "dominant_hidden": dominant_hidden,
            "if_transparent": "是" if is_transparent else "否",
            "pattern_ten_god": pattern_ten_god,
        }

    def _llm_render(self, output: AgentOutput, style: str) -> str:
        chart = (
            output.result if isinstance(output.result, BaziChart) else BaziChart(**output.result)
        )
        pillars_by_pos = {p.position: p for p in chart.pillars}

        gender_text = (
            "男"
            if output.input_payload.get("gender") == Gender.MALE
            else "女"
            if output.input_payload.get("gender") == Gender.FEMALE
            else "未知"
        )
        question = output.input_payload.get("question", "分析此八字")

        # Format pillars
        yp = pillars_by_pos["year"]
        mp = pillars_by_pos["month"]
        dp = pillars_by_pos["day"]
        hp = pillars_by_pos["hour"]

        pattern_info = self._get_pattern_info(chart)

        prompt_data = {
            "day_master": chart.day_master,
            "day_master_element": chart.day_master_element,
            "gender_text": gender_text,
            "question": question,
            "year_pillar": f"{yp.stem}{yp.branch}",
            "year_hidden": "、".join(yp.hidden_stems),
            "year_god": yp.ten_god,
            "month_pillar": f"{mp.stem}{mp.branch}",
            "month_hidden": "、".join(mp.hidden_stems),
            "month_god": mp.ten_god,
            "day_pillar": f"{dp.stem}{dp.branch}",
            "day_hidden": "、".join(dp.hidden_stems),
            "day_god": dp.ten_god,
            "hour_pillar": f"{hp.stem}{hp.branch}",
            "hour_hidden": "、".join(hp.hidden_stems),
            "hour_god": hp.ten_god,
            "ten_gods_map_json": json.dumps(chart.ten_gods_map, ensure_ascii=False, indent=2),
            "dayun_list": "\n".join(
                [f"- {d.stem}{d.branch} ({d.start_age}-{d.end_age}岁)" for d in chart.dayun]
            ),
            "confidence_value": output.confidence.value,
            "confidence_factors": ", ".join(output.confidence.factors),
            **pattern_info,
        }

        user_prompt = USER_PROMPT_TEMPLATE.render(prompt_data)

        if self.provider is None:
            return self._fallback(output, style)

        s = self.provider.settings
        return self.provider.generate(
            BAZI_SYSTEM_PROMPT + "\n\n" + user_prompt,
            model=s.ollama_model,
            temperature=s.explain_temperature,
            max_tokens=s.explain_max_tokens,
        )

    @staticmethod
    def _fallback(output: AgentOutput, style: str, note: str = "") -> str:
        """Deterministic fallback when LLM is not available or fails."""
        try:
            chart = (
                output.result
                if isinstance(output.result, BaziChart)
                else BaziChart(**output.result)
            )
            pillars_by_pos = {p.position: p for p in chart.pillars}
            mp = pillars_by_pos["month"]
            hidden_stems = mp.hidden_stems
            dominant_hidden = hidden_stems[0] if hidden_stems else ""
            pattern_ten_god = chart.ten_gods_map.get(dominant_hidden, "未知格局")

            # Find current dayun (first entry is the first, approximate)
            current_dayun = f"{chart.dayun[0].stem}{chart.dayun[0].branch}" if chart.dayun else "无"

            fallback = (
                f"此命造日主【{chart.day_master}】生于【{mp.stem}{mp.branch}】，"
                f"月令主气为【{dominant_hidden}】，定【{pattern_ten_god}】格局。"
                f"当前大运【{current_dayun}】。"
            )
            if note:
                fallback += f" ({note})"
            return fallback
        except Exception:
            # Ultimate fallback to generic output
            return Explainer._fallback(output, style, note)
