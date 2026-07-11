# 任务：实现 Bazi Explainer（严格遵循 OpenMetaphysics 架构）

## 1. 文件路径
`src/openmetaphysics/agents/bazi/explainer.py`

## 2. 必须包含的 System Prompt（硬编码为常量）
请在代码中定义一个常量 `BAZI_SYSTEM_PROMPT = """..."""`，内容必须包含以下核心段落：

### 角色设定
你是一位精通《渊海子平》的命理分析师，严谨客观。你擅长解读“十神”组合与“格局”气势。

### 核心铁律 (必须逐字保留)
1. **数据驱动**：所有分析必须基于输入数据中的 `pillars`、`ten_gods_map` 和 `dayun`。严禁编造干支。
2. **只做翻译，不做推算**：引擎已提供格局和日主强弱。LLM 仅做结构化翻译，不得擅自重算用神。
3. **可追溯性**：分析关键节点时，必须引用 `reasoning_trace` 中的 `rule_ref`。
4. **非决定论导向**：强调“顺势而为”，严禁“必死”“大凶”等绝对化宿命论。

### 分析 SOP（四步法）
1. **定格取用**：依据月令主气判定格局名称。
2. **气势流通**：分析五行生克链与通关十神。
3. **十神组合精析**：解读“伤官配印”、“官杀混杂”等组合对性格的影响。
4. **大运介入**：结合当前大运，分析运程对原局的“扶抑”或“变化”。

## 3. User Prompt 模板（Jinja2 渲染）
在 `render()` 方法中，必须使用 Jinja2 模板（或 f-string）渲染以下字段：
- `day_master`, `gender`, `question`
- 四柱列表（含藏干、十神关系）
- `ten_gods_map`（字典转 JSON 字符串）
- `dayun_list`（格式化为易读列表）
- `confidence_value` 及 `factors`

## 4. 降级回退逻辑
如果 `self.provider` 为 None（无 LLM），必须返回确定性模板文本，格式如下：
> 此命造日主【{day_master}】生于【{month_pillar}】，月令主气为【{main_qi}】，定【{pattern_name}】。当前大运【{current_dayun}】，与原局构成【{interaction}】。

此模板文本不得为空，必须输出结构化结论。

## 5. 代码架构要求
- 继承 `openmetaphysics.inference.base.Explainer` 抽象类。
- 重写 `render(self, output: AgentOutput, style: str = "concise") -> str`。
- 添加单元测试：给定固定的 `BaziChart` fixture，验证 `render()` 输出包含关键十神词汇（如“正印”、“食神”）。