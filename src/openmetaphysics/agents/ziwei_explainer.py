from __future__ import annotations

import json
from typing import Any, Dict, List

from jinja2 import Template

from ..core.schemas import AgentOutput, Gender
from ..inference.explainer import Explainer
from .ziwei import ZiweiChart, Palace


# 辅星权重映射，值越小优先级越高
AUX_STAR_WEIGHT: Dict[str, int] = {
    # 四化
    "化禄": 1,
    "化权": 2,
    "化科": 3,
    "化忌": 4,
    # 吉星
    "左辅": 5,
    "右弼": 6,
    "文昌": 7,
    "文曲": 8,
    "天魁": 9,
    "天钺": 10,
    "禄存": 11,
    "天马": 12,
    # 煞星
    "擎羊": 13,
    "陀罗": 14,
    "火星": 15,
    "铃星": 16,
    "地空": 17,
    "地劫": 18,
}


def _sort_aux_stars(stars: List[str]) -> List[str]:
    """按权重优先级排序辅星，高优先级在前"""
    return sorted(stars, key=lambda s: AUX_STAR_WEIGHT.get(s, 999))


def _format_aux_stars(stars: List[str]) -> str:
    """格式化辅星展示：取前3个高优先级，超过3个显示等X颗"""
    if not stars:
        return "无"
    sorted_stars = _sort_aux_stars(stars)
    if len(sorted_stars) <= 3:
        return "、".join(sorted_stars)
    return f"{sorted_stars[0]}、{sorted_stars[1]}、{sorted_stars[2]}等{len(sorted_stars)}颗"


ZIWEI_SYSTEM_PROMPT = """# 角色设定 (Role)
你是一位精通紫微斗数的命理分析师，严谨、客观、不宿命论。你擅长解读14主星和宫位组合的运势含义。

# 核心铁律 (Golden Rules)
1. **数据驱动**：你的所有分析必须严格基于输入提供的排盘结果：宫位、主星、五行局、命宫/身宫、格局、辅星信息。严禁凭空编造任何星曜、位置或格局。
2. **只做翻译，不做推算**：排盘结果已经由确定性引擎计算完成，你只需解读现有结果，绝对不能重新排盘或修改任何计算结果。
3. **可追溯性**：在提到关键星曜组合、格局时，必须明确说明来源，例如"命宫紫微贪狼主桃花"、"格局为杀破狼主变动"。
4. **非决定论导向**：最终建议必须强调"顺势而为"和"后天努力调整"，严禁给出"必死""大凶""必定发大财"等绝对化宿命论断语。
5. **格局优先**：解读时必须首先提及排盘结果patterns字段中所有识别到的格局名称，说明该格局的基本含义和特点。

# 分析结构化流程 (SOP)
请按以下四步逻辑组织你的回答（必须包含小标题）：
1. **命盘概览**：说明五行局、识别到的所有格局、命宫主星组合、身宫位置，给出整体性格和运势基调。
2. **核心宫位解读**：重点分析命宫、财帛、官禄、夫妻、迁移五大核心宫位的主星+辅星组合含义，按权重先讲重要辅星。
3. **格局特点分析**：详细解读所有识别到的格局的优缺点、适合发展方向。
4. **运势建议**：给出符合星曜和格局特点的发展建议，强调后天可调整的方向。

# 星曜含义速查表 (Contextual Aid)
## 紫微星系
- 紫微：帝星，主官贵、领导力
- 天机：主智慧、变动、策划
- 太阳：主光明、事业、男性贵人
- 武曲：主财帛、武勇、金融
- 天同：主享受、福气、温和
- 廉贞：主桃花、复杂、官非
## 天府星系
- 天府：财库星，主储蓄、稳定
- 太阴：主财、女性贵人、情绪
- 贪狼：主桃花、欲望、偏财运
- 巨门：主口舌、是非、口才
- 天相：主印星、辅助、中介
- 天梁：主荫星、贵人、医药
- 七杀：主变动、冲劲、风险
- 破军：主破旧立新、变化、消费

## 辅星权重优先级（从高到低，解读时优先提及）
1. 吉星权重：化禄 > 化权 > 化科 > 化忌 > 左辅 > 右弼 > 文昌 > 文曲 > 天魁 > 天钺 > 禄存 > 天马
2. 煞星权重：擎羊 > 陀罗 > 火星 > 铃星 > 地空 > 地劫
"""


USER_PROMPT_TEMPLATE = Template("""
请分析以下紫微斗数排盘数据：

【基础信息】
五行局：{{wuxing_ju}}
命宫位置：{{fate_palace_name}}，干支：{{fate_palace_ganzhi}}，主星：{{fate_palace_stars}}
身宫位置：{{body_palace_name}}，主星：{{body_palace_stars}}
出生性别：{{gender_text}}
当前输入问题：{{question}}

【格局信息】
识别到的格局：{{patterns_list}}

【核心宫位信息】
{% for palace in core_palaces %}
- {{palace.name}}宫：主星{{palace.stars}}，辅星{{palace.aux_stars}}，干支{{palace.ganzhi}}
{% endfor %}

【14主星分布】
{{stars_distribution}}

【引擎计算置信度】
Confidence Score: {{confidence_value}}
计算因子：{{confidence_factors}}

{% if confidence_value < 0.6 %}
【关键警告】
由于本次排盘置信度低于阈值（Confidence < 0.6），可能是由于出生时间不精确或处于节气交接时刻。
请在回答开篇声明："此局边界模糊，以下分析需结合具体流年及面诊核实，请谨慎参考。"
{% endif %}

---
请严格按照 System Prompt 的 SOP 展开分析，输出 300-500 字的结构化解读。必须首先提及所有识别到的格局。
""")


class ZiweiExplainer(Explainer):
    """Ziwei specific explainer with specialized prompt engineering for 紫微斗数 analysis.

    Follows strict separation of concerns: Engine computes, LLM only translates
    structured results to natural language. Never modifies the computed result.
    """

    def _prepare_prompt_data(self, output: AgentOutput) -> dict[str, Any]:
        """Prepare structured data for prompt injection."""
        chart = ZiweiChart(**output.result)
        pillars_by_pos = {p.name: p for p in chart.palaces}
        fate_palace = next(p for p in chart.palaces if p.is_fate_palace)
        body_palace = next(p for p in chart.palaces if p.is_body_palace)

        # 处理格局列表
        patterns_list = "、".join(chart.patterns) if chart.patterns else "无特殊格局"

        # 核心宫位：命宫、财帛、官禄、夫妻、迁移
        core_palace_names = ["命宫", "财帛", "官禄", "夫妻", "迁移"]
        core_palaces = []
        for name in core_palace_names:
            p = pillars_by_pos[name]
            core_palaces.append({
                "name": name,
                "stars": "、".join(p.main_stars) if p.main_stars else "无主星",
                "aux_stars": _format_aux_stars(p.auxiliary_stars),
                "ganzhi": p.heavenly_stem + p.earthly_branch
            })

        # 星曜分布
        stars_dist = []
        for p in chart.palaces:
            if p.main_stars:
                stars_dist.append(f"{p.name}: {'、'.join(p.main_stars)}")
        stars_distribution = "\n".join(stars_dist)

        # 性别
        gender_text = "男" if output.input_payload.get("gender") == Gender.MALE else "女" if output.input_payload.get("gender") == Gender.FEMALE else "未知"
        question = output.input_payload.get("question", "分析此紫微斗数命盘")

        return {
            "wuxing_ju": chart.wuxing_ju,
            "fate_palace_name": fate_palace.name,
            "fate_palace_ganzhi": fate_palace.heavenly_stem + fate_palace.earthly_branch,
            "fate_palace_stars": "、".join(fate_palace.main_stars) if fate_palace.main_stars else "无主星",
            "body_palace_name": body_palace.name,
            "body_palace_stars": "、".join(body_palace.main_stars) if body_palace.main_stars else "无主星",
            "patterns_list": patterns_list,
            "gender_text": gender_text,
            "question": question,
            "core_palaces": core_palaces,
            "stars_distribution": stars_distribution,
            "confidence_value": output.confidence.value,
            "confidence_factors": ", ".join(output.confidence.factors.keys()),
        }

    def _llm_render(self, output: AgentOutput, style: str) -> str:
        prompt_data = self._prepare_prompt_data(output)
        user_prompt = USER_PROMPT_TEMPLATE.render(prompt_data)

        if self.provider is None:
            return self._fallback(output, style)

        s = self.provider.settings
        return self.provider.generate(
            ZIWEI_SYSTEM_PROMPT + "\n\n" + user_prompt,
            model=s.ollama_model,
            temperature=s.explain_temperature,
            max_tokens=s.explain_max_tokens,
        )

    @staticmethod
    def _fallback(output: AgentOutput, style: str, note: str = "") -> str:
        """Deterministic fallback when LLM is not available or fails."""
        try:
            chart = ZiweiChart(**output.result)
            fate_palace = next(p for p in chart.palaces if p.is_fate_palace)
            fate_stars = "、".join(fate_palace.main_stars) if fate_palace.main_stars else "无主星"
            body_palace = next(p for p in chart.palaces if p.is_body_palace)
            body_stars = "、".join(body_palace.main_stars) if body_palace.main_stars else "无主星"
            total_stars = len([s for p in chart.palaces for s in p.main_stars])
            patterns_text = "、".join(chart.patterns) if chart.patterns else "无特殊格局"

            fallback = (
                f"此紫微命盘为{chart.wuxing_ju} | 格局：{patterns_text} | 命宫在{fate_palace.name}，主星[{fate_stars}] | "
                f"身宫在{body_palace.name}，主星[{body_stars}] | 共{total_stars}颗主星入庙。"
            )
            if note:
                fallback += f" ({note})"
            return fallback
        except Exception:
            # Ultimate fallback to generic output
            return Explainer._fallback(output, style, note)
