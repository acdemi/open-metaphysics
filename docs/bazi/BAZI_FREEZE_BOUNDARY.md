# BaZi Freeze Boundary

> **状态**: Candidate —— 冻结边界定义（Phase 6.3A）
> **日期**: 2026-08-09
> **性质**: 定义未来契约冻结（Phase 6.4 Freeze Review）的**边界**：
> 什么纳入冻结范围，什么显式延后。
> **依据**: `docs/bazi/BAZI_RULE_DECISION.md`（B1~B6, Draft）

---

## 1. 纳入冻结范围（IN SCOPE — 确定性排盘）

以下输出为**确定性计算**，是 Golden Vectors 断言对象，契约化时纳入冻结:

| 项 | 规则 | 冻结内容 |
|----|------|----------|
| 年柱 | B1 | stem/branch（立春 UTC 边界） |
| 月柱 | B2 | stem/branch（12 节 + 五虎遁） |
| 日柱 | B3 | stem/branch（JDN+49, 23:00 本地换日） |
| 时柱 | B4 | stem/branch（子时 23:00~00:59, 五鼠遁, 钟表时） |
| 十神映射 | — | 全部柱干 + 藏干 vs 日主的十神映射表（ten_gods_map） |
| 藏干 | — | 各柱支的藏干列表（`BRANCH_HIDDEN_STEMS`） |
| 纳音 | — | 各柱干支纳音（`NAYIN` 表） |
| 大运 | B5 | 方向（阳男/阴女顺, 其余逆）、起运年龄（`round(days/3)`, banker's rounding）、步进（+10 岁/步, 默认 8 步, `dayun_count` 可配）、`start_at`（2/29 → 2/28 降级） |
| 性别回退 | B6 | `gender_assumed` 标记（UNKNOWN 按男处理） |

**冻结语义**: 上述输出在固定输入下必须**逐字节可复现**（对齐 Qimen QC-001 确定性条款）；Golden Vectors（24）为规范回归装置，变更须 ACP + 契约版本递增 + 向量迁移。

---

## 2. 显式延后（DEFERRED — 不在本次冻结范围）

以下能力**明确不纳入** Phase 6.3/6.4 冻结，属未来授权 Sprint:

| 项 | 说明 | 延后原因 |
|----|------|----------|
| 格局分析（Pattern） | 正官格/伤官佩印等 | 需 Rule DSL + Pattern 层（Phase 6.5+） |
| 用神（Useful God） | 扶抑/调候用神 | 流派分歧大, 需单独裁定 |
| 强弱分析（Strength） | 日主旺衰/身强身弱 | 判定标准需裁定 |
| 神煞（Shen Sha） | 天乙贵人/桃花等 | 未实现, 不属排盘 |
| 流年/流月 | 岁运推断 | 依赖大运冻结后 |
| 解释层（Interpretation） | BaziExplainer/LLM | Domain Boundary（ARCHITECTURE.md §1） |
| 叙事生成 / 建议 | 任何自然语言输出 | Domain Boundary |
| LLM / RAG / Consensus | 推理/检索/聚合 | Domain Boundary |

> **边界原则**: 冻结只覆盖"可由输入单独重现的确定性观测"。
> 上述延后项即使未来实现，也**不得**改变已冻结的排盘输出。

---

## 3. 与 Qimen 边界对照

| 维度 | BaZi（本域） | Qimen（契约 v1.0.0） |
|------|--------------|----------------------|
| 冻结范围 | 四柱/十神/藏干/纳音/大运 | 九宫盘（星/门/神/地盘/天盘/空亡/中宫） |
| 延后项 | 格局/用神/强弱 | 格局判断/用神/应期 |
| 确定性条款 | 待契约（对齐 QC-001） | QC-001 已冻结 |
| 排他声明 | 解释/建议/叙述/LLM/RAG/Consensus | 同左（领域边界通用） |

---

## 4. 边界不变式

1. 冻结范围外的一切输出**不作为** Golden Vector 断言对象。
2. 已冻结输出在后续 Sprint（格局/用神等）中**保持字节级不变**。
3. 任何对冻结范围的修改必须走 ACP + 契约版本递增 + 向量迁移。
