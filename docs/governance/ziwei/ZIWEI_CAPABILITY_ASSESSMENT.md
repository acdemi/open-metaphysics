# Ziwei Domain Capability Assessment

> **Sprint**: Phase 7.0 — Ziwei Capability Migration Assessment（评估与证据盘点, 非实现）
> **日期**: 2026-08-09
> **依据**: 真实仓库审计（`src/openmetaphysics/agents/ziwei.py` 411 行,
> `agents/ziwei/pattern_matcher.py` 108 行, `agents/ziwei_explainer.py` 233 行,
> `tests/test_ziwei.py` 12 例, SCHEMAS.md §3.2）
> **参考流程**: `docs/governance/CAPABILITY_LIFECYCLE.md`（对齐 BaZi Phase 6.1 评估方法）

---

## 1. Current Status

**Implemented**（Stage 1 满足; 未进入 Contract Candidate）

依据:
- 确定性计算入口 ✅（`ZiweiEngine(DeterministicEngine)` v0.2.0, 无 LLM/随机/IO）
- 领域专属输入 Schema ✅（`ZiweiInput` 含 lunar_month/lunar_day 可配重放）
- 领域专属输出 Schema ✅（`ZiweiChart`/`Palace`, `extra="forbid"`）
- 测试 ✅（12 例, 含确定性 replay + 3 例 sxtwl 历法数值断言）
- Contract Candidate 入口条件 ❌（无契约草案 / 无规则裁定 / 无 Freeze Review）

**不升级**: "代码能运行" 不等于 Contract Candidate（生命周期不变式: 状态必须真实）。

---

## 2. Stage Mapping

| Stage | Requirement | Evidence | Status | Missing Artifact |
|-------|-------------|----------|--------|------------------|
| Stage 0 Exploration | domain scope / 非正式规则记录 | ⚠️ 部分: 规则仅存在于代码/测试注释（如 test_fate_palace_canonical 注释记录 命宫公式推导）; 无独立假设文档 | ⚠️ 部分 | ZIWEI_ALGORITHM_ASSUMPTIONS 文档 |
| Stage 1 Calculation Runtime | deterministic engine + schema + tests | ✅ 满足: engine v0.2.0 + ZiweiInput/ZiweiChart + 12 tests（含 replay/边界/canonical） | ✅ | JSON Schema 导出; SCHEMAS.md §3.2 登记勘误（calendar_note 位置） |
| Stage 2 Behavior Contract | frozen rules + versioned contract + golden vectors | ❌ 未开始 | ❌ | 规则裁定文档（ZW-001~017 → 冻结清单）→ 契约草案 → Golden Vectors（→ 覆盖 命宫/五行局/定局/农历/时区/闰月）→ Freeze Review |
| Stage 3 Reference Certification | independent implementation + contract verification + equivalence | ❌ 未开始 | ❌ | `reference/ziwei/` 独立实现（无 src 导入, 含 sxtwl 等价策略裁定）+ 契约审计 + 等价测试 |
| Stage 4 Certified Capability | governance registration + integration ready | ❌ 未开始 | ❌ | CAPABILITY_STATUS.md 注册 + 变更政策 |

---

## 3. Calculation Layer 审计

| 项 | 状态 | 证据 |
|----|------|------|
| 确定性计算入口 | ✅ | `ZiweiEngine.calculate()` 纯函数; `test_replay_identical` 锁定 |
| 输入 Schema | ✅ | `ZiweiInput(AgentInput)` + `lunar_month/lunar_day: int\|None`（用户显式农历重放） |
| 输出 Schema | ✅ | `ZiweiChart{ fate_palace_index, body_palace_index, yin_yang, wuxing_ju, palaces×12, calendar_note }` + `Palace{ index, name, earthly_branch, heavenly_stem, main_stars, auxiliary_stars, is_fate_palace, is_body_palace }`, 全部 `extra="forbid"` |
| 核心数据结构 | ✅ | PALACE_BRANCHES（寅起顺行 12 宫）/ PALACE_NAMES / ZIWEI_POS 定局表（2~6 局 × 30 日）/ 双星系偏移表 |
| 领域规则 | ✅ 部分 | 命宫/身宫/五行局/十四主星/阴阳 —— 已实现; 辅星/四化/大限 —— **未实现**（explicit metadata: star_placement=14_major_stars） |
| 历法基础设施 | ⚠️ 依赖 | `sxtwl`（编译库, 农历转换, compute() 内唯一外部依赖）; `bazi_year_index`（立春, 复用 BaZi B1 原语）; 无真太阳时 |
| 边界条件 | ⚠️ 少 | 测试覆盖 正月寅时 canonical / 春节 / 闰月数值; 未覆盖 时区差 / 子时窗 / 用户农历与公历不一致 / 五行局全类型 |
| 单元测试 | ✅ 12 例 | 详见 TEST_COVERAGE_REVIEW |
| 序列化 | ✅ | `model_dump(mode="json")` 确定性; replay 逐字节 |
| 版本号 | ✅ | engine v0.2.0（metadata 断言） |

**行为分类**:
- 已是确定性规范候选: 命宫/身宫公式、定局表、双星系偏移、五行局映射、年干立春界
- 仅当前实现（隐含假设）: 闰月按月号同值安星、时区回退链（无 UTC 兜底）、性别未使用
- 尚未裁定: 晚子时（无 23:00 换日逻辑, 农历日=民用日）、用户农历覆盖优先序、sxtwl 版本绑定

---

## 4. 规则边界（已提取, 详见 RULE_INVENTORY）

ZW-001~017 十七条（编号为**内部清单**, 不代表冻结）。Scope 不含:
格局/吉凶/用神/Recommendation/Narrative/LLM/RAG/Consensus（后续授权范围）。

---

## 5. Schema 审计摘要

- SCHEMAS.md §3.2 **已存在**且大体匹配实际（lunar_month/lunar_day 输入、ZiweiChart 输出）
- 勘误 1: §3.2 Palace 列表含 `calendar_note` 字段, 实际 `calendar_note` 位于 **ZiweiChart**（Palace 无此字段）
- 缺失: JSON Schema 导出; implicit defaults（gender=UNKNOWN 继承但**未被 engine 使用** —— 见 ZW-017）
- serialization ambiguity: 无（replay 测试锁定）

---

## 6. 结论

Ziwei = **Implemented**, 计算层实质满足 Stage 1（与 BaZi Phase 6.1 评估结论同型）。
→ Contract Candidate 前置: 算法假设文档 + 规则裁定 + 向量草案 + Freeze Review
（全部为治理工件, 不要求算法改动; 待 Phase 7.1+ 授权）。
