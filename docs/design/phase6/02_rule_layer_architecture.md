# Rule Layer Architecture（规则层架构）

> 状态：设计 v1 (2026-07-11)
> 层级定位：Layer 2.5 - 位于基础层之上，知识层之下
> 原则：凡是规则能表达的，禁止交给 LLM。

## 1. 设计目标

规则层将命理推理中的**确定性规则**从引擎代码中显式提取为结构化 Rule 对象，
实现规则的**可查询、可审计、可版本化、可冲突检测**。

核心职责：
- 每条规则可独立表示：条件（conditions）-> 结果（results），附带优先级、适用范围、冲突规则。
- 规则引擎（RuleEngine）对排盘结构化数据执行规则匹配，输出 `RuleEvaluation`。
- 规则的 `rule_ref` 与现有 `ReasoningStep.rule_ref` 对齐--现有引擎的推理步骤可追溯到此层规则。
- 规则不执行计算--计算仍由确定性引擎完成。规则在**计算结果之上**做语义推断。

## 2. 规则生命周期

```
 定义阶段                  匹配阶段                      输出阶段
┌──────────┐         ┌──────────────────┐         ┌─────────────────┐
│ Rule     │  注册->  │ RuleEngine       │  评估->  │ RuleEvaluation  │
│ (Schema) │         │ .evaluate(chart) │         │ {rule_id,       │
│          │         │                  │         │  matched,       │
│ conditions│        │ 遍历条件         │         │  results,       │
│ results  │         │ 检查优先级       │         │  evidence_refs} │
│ priority │         │ 冲突消解         │         │                 │
│ scope    │         │                  │         │                 │
└──────────┘         └──────────────────┘         └─────────────────┘
```

## 3. 规则类型（RuleType 枚举）

| rule_type                | 说明                   | 示例                              |
|--------------------------|------------------------|-----------------------------------|
| `pattern_recognition`    | 格局/模式识别          | 伤官佩印、紫府同宫                |
| `relation_derivation`    | 关系推导               | 天干五合、地支三合                |
| `ten_god_determination`  | 十神判定               | 日主甲木见庚金->偏官              |
| `yong_shen_determination`| 用神判定               | 身强取克泄耗，身弱取生扶          |
| `element_balance`        | 五行平衡分析           | 木旺缺金->需金制                  |
| `domain_inference`       | 领域推断               | 伤官佩印->适合科研（career 领域） |
| `conflict_resolution`    | 冲突消解               | 两规则冲突时优先级高者胜出        |
| `da_yun_analysis`        | 大运分析               | 某步大运与日主关系->吉凶          |

## 4. 条件系统（Condition）

每条规则包含一组条件，全部满足时规则触发。

### 4.1 条件操作符

| operator        | 说明             | 示例值                    |
|-----------------|------------------|---------------------------|
| `equals`        | 等于             | "甲"                       |
| `not_equals`    | 不等于           | "壬"                       |
| `contains`      | 列表中包含       | "伤官"（在十神列表中）     |
| `not_contains`  | 列表中不包含     | "七杀"                     |
| `in`            | 值在集合中       | ["甲", "乙"]               |
| `not_in`        | 值不在集合中     | ["庚", "辛"]               |
| `greater_than`  | 大于             | 0.7（五行权重）            |
| `less_than`     | 小于             | 0.3                        |
| `exists`        | 字段存在         | -                          |
| `not_exists`    | 字段不存在       | -                          |
| `matches`       | 正则/模式匹配    | "^水.*局$"                 |

### 4.2 条件结构

```
RuleCondition:
  field: string           # 排盘结构化数据的路径，如 "pillars[0].ten_gods_stem"
  operator: Operator      # 上表操作符之一
  value: any              # 比较值
  negate: bool = false    # 是否取反
  description: string     # 人类可读说明
```

条件中的 `field` 路径指向**已计算的排盘结构**（BaziChart / ZiweiChart / QimenBoard / LiuyaoChart），
不触发任何重新计算。

## 5. 结果系统（RuleResult）

规则触发后产出一组结果，每个结果指向一个领域结论。

```
RuleResult:
  domain: string          # "career" | "personality" | "marriage" | "health" | "wealth" | ...
  conclusion: string      # 结论文本，如 "适合科研"
  conclusion_node_id: string | None   # 关联的知识节点 ID（可选）
  weight: float [0,1]     # 该结果的可信度权重
  direction: Literal["positive", "negative", "neutral"] = "positive"
```

## 6. 优先级与冲突消解

### 6.1 优先级

- `priority`：整数，0-100。数值越高优先级越高。
- 同一领域、同一体系内多条规则同时触发时，高优先级规则的结果权重更大。
- 默认优先级 50。

### 6.2 冲突规则

- `conflicts`：声明与本规则冲突的规则 ID 列表。
- 冲突消解策略（`conflict_strategy` 枚举）：
  - `highest_priority_wins`：优先级最高者生效，其余降级。
  - `retain_all`：全部保留，由 Consensus Agent 在证据聚合阶段处理。
  - `merge`：结果合并取加权平均。
- 默认策略：`retain_all`--符合 Evidence Based Consensus 原则（不提前丢弃证据）。

## 7. 适用范围（Scope）

```
RuleScope:
  systems: list[string]       # 适用体系 ["bazi", "ziwei"]
  gender: list[Gender] | None # 性别限制，None=不限
  age_range: tuple[int,int] | None  # 年龄限制
  lunar_month_range: tuple[int,int] | None  # 农历月份限制
```

## 8. 规则引用来源（SourceRef）

每条规则必须标注经典出处，确保可审计：

```
SourceRef:
  text: string               # 典籍名称，如 "滴天髓"
  chapter: string | None     # 篇章
  author: string | None      # 作者/注者
  page: int | None           # 页码
  url: string | None         # 在线引用 URL
  credibility: float [0,1]   # 来源可信度
```

## 9. 与现有架构的集成

- 现有引擎的 `ReasoningStep.rule_ref` 字符串映射到 `Rule.id`。
- `RuleRegistry`（已存在于 `core.engines`）扩展为注册 `Rule` 对象而非仅可调用对象。
- 规则评估发生在引擎 `calculate()` **之后**，消费排盘结果，不修改排盘数字。
- AgentOutput 的 `metadata` 可新增 `evaluated_rules` 字段，记录触发的规则 ID 列表。
- **不修改**现有 `DeterministicEngine.calculate()` 的纯函数契约。

## 10. 规则版本化

- 每条规则有 `version`（语义版本）。
- `Rule.id` 包含版本后缀：`rule:bazi:shang_guan_pei_yin:v1`。
- 规则变更时版本递增，旧版本保留以支持历史结果重放。
