# Architecture Decision Records（ADR）

> 状态：设计 v1 (2026-07-11)

---

## ADR-001：采用 Evidence-Based Consensus 取代 Weighted Average

**状态**：Accepted
**日期**：2026-07-11

### 背景

现有 ConsensusAgent 使用 Weighted Average 策略：按各智能体 confidence 加权平均，
辅以五行一致性矩阵。问题：
1. 只输出单一 confidence 数值，丢失了「为什么」。
2. 不同体系结论不同时（如八字建议科研、紫微建议管理），旧方案只能降低 confidence，无法表达「两者都对」。
3. 无法追溯到具体规则和经典出处。

### 决策

采用 Evidence-Based Consensus：
- 共识不是投票，而是 Evidence Aggregation。
- 每个结论附带全部支持证据（规则 ID、格局 ID、知识节点 ID、来源、权重）。
- 同一领域内多个不同结论可并存，按置信度降序排列。
- 跨体系通过共同 Pattern 比较而非直接比较 JSON。

### 影响

- ConsensusReport 升级为 EvidenceConsensusReport（旧模型保留 legacy 兼容）。
- 智能体需在 compute() 后输出 Evidence（通过规则评估 + 格局匹配）。
- 最终响应信息量增大，但可解释性显著提升。

---

## ADR-002：知识层为只读参考层，不参与计算

**状态**：Accepted
**日期**：2026-07-11

### 背景

知识层包含五行、十神、主星、神煞等命理知识。若让知识层参与计算，
将破坏现有确定性引擎的纯函数契约（相同输入->字节相同输出）。

### 决策

知识层是**只读参考层**：
- 确定性引擎的 `calculate()` 逻辑不变，不查询知识层。
- 知识层用于：规则匹配时的知识查询、解释渲染时的引用注入、RAG 检索增强。
- `KnowledgeStore` 接口仅暴露查询方法（get/query/find_path），无写入方法。

### 影响

- 现有引擎代码零修改。
- 知识层可独立演进、独立版本化。
- 计算确定性得到保障。

---

## ADR-003：规则在计算结果之上评估，不替代引擎

**状态**：Accepted
**日期**：2026-07-11

### 背景

规则可以表达「伤官佩印->适合科研」这类推断。若规则参与排盘计算，
会引入非确定性风险（规则版本变更导致排盘结果变化）。

### 决策

规则评估发生在引擎 `calculate()` **之后**：
- 引擎先产出排盘结构（BaziChart 等），这是确定性的。
- 规则引擎消费排盘结构，执行条件匹配，产出 RuleEvaluation。
- 规则变更不影响排盘数字，只影响语义推断。

### 影响

- ReasoningStep.rule_ref 现可映射到结构化 Rule.id。
- 规则可独立版本化，旧结果可重放。
- 排盘结果与推断结果分离，各自可审计。

---

## ADR-004：Pattern 作为跨体系共识的比较单元

**状态**：Accepted
**日期**：2026-07-11

### 背景

不同体系的输出结构差异大（BaziChart vs ZiweiChart），直接比较 JSON 字段不可行。
旧方案仅比较五行一致性，粒度太粗。

### 决策

引入 Pattern Layer：
- Pattern 是跨体系的语义单元（如「伤官佩印」「紫府同宫」）。
- 多个 Agent 可识别同一 Pattern。
- Consensus Agent 比较的是 Pattern，不是 JSON 字段。
- 跨体系识别同一 Pattern 时，置信度增强。

### 影响

- 新增 Pattern 和 PatternMatch 模型。
- 需要为每个体系定义 Pattern 识别规则。
- 共识质量提升：从「五行是否一致」升级为「格局是否印证」。

---

## ADR-005：知识节点采用多态设计（node_type + attributes）

**状态**：Accepted
**日期**：2026-07-11

### 背景

知识节点涵盖 20 种不同类型（五行、十神、主星、神煞...），
每种类型的属性差异很大。若为每种类型定义独立模型，会导致模型爆炸。

### 决策

采用多态设计：
- 所有节点共享基础字段（id, name_cn, name_en, systems, source, interpretation, tags, confidence, schools）。
- 通过 `node_type` 枚举区分类型。
- 类型特定属性放在 `attributes` dict 中，键集合按 node_type 预定义。
- `attributes` 的键是**有记录的**（每种 node_type 有 schema 约束），不是自由 dict。

### 影响

- 单一 KnowledgeNode 模型覆盖全部 20 种类型。
- 可扩展性强（新类型只需新增枚举值 + 属性键集合）。
- 查询统一化（按 node_type 过滤）。

---

## ADR-006：冲突默认策略为 retain_all

**状态**：Accepted
**日期**：2026-07-11

### 背景

命理规则中存在大量看似冲突的规则（如「伤官佩印->科研」vs「伤官见杀->创业」）。
若在规则层就消解冲突，会丢失证据。

### 决策

默认冲突策略为 `retain_all`：
- 冲突规则的结果全部保留。
- 冲突消解推迟到 Consensus Agent 的证据聚合阶段。
- 仅在明确需要时（如互斥规则）使用 `highest_priority_wins`。

### 影响

- Consensus Agent 看到全部证据，可呈现多结论。
- 用户可以看到「科研 0.81 vs 管理 0.72 vs 创业 0.69」的完整画面。
- 不丢失任何有来源的证据。

---

## ADR-007：Phase 6 仅设计不实现数据库

**状态**：Accepted
**日期**：2026-07-11

### 背景

知识层和规则层最终需要持久化（PostgreSQL/Neo4j），
但在模型设计未确认前实现数据库会导致返工。

### 决策

Phase 6 严格禁止：
- 实现数据库持久化（Postgres/Neo4j）。
- 编写运行时业务代码。
- 修改已稳定的八字、紫微模块。

仅输出 Pydantic Schema 定义和架构设计文档。

### 影响

- 设计文档先行，架构确认后才进入实现。
- 实现阶段（Phase 7-9）再选型数据库。
- 避免设计未定就实现的返工成本。
