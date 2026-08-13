# Capability Status

> 领域能力成熟度跟踪（Domain Maturity Tracking）— 唯一权威状态登记
> 状态模型与迁移规则: `docs/governance/CAPABILITY_LIFECYCLE.md`
> 登记模板: `docs/governance/DOMAIN_CAPABILITY_TEMPLATE.md`
> 更新: 2026-08-09（Phase 6.0 标准化评审）

---

## 状态矩阵（Domain Status Matrix）

| Domain | Status | Contract | Golden Vectors | Reference | 测试 |
|--------|--------|----------|----------------|-----------|------|
| **Qimen** | **Integration Ready**（Certified Frozen Capability） | v1.0.0 Frozen | 24（Frozen） | Certified（双实现验证） | 全仓库 530 |
| **BaZi** | **Integration Ready**（Certified Capability） | v1.0.0 Frozen | 24（normative） | Certified（24/24 等价） | 11 + 14 + 7 + 6 |
| **Ziwei** | **Integration Ready**（Certified Capability） | v1.0.0 **Frozen**（`ziwei:behavior:v1.0.0`, 2026-08-13） | 24（normative fixtures） | Certified（24/24 等价, `reference/ziwei/`） | 33 + 7 + 4 |
| **Liuyào** | Implemented | 无 | 无 | 无 | 6 |
| Consensus | N/A（非计算域） | — | — | — | — |
| Knowledge Layer | 引用层（不产生计算输出） | Architecture **FROZEN**（KB-001~020）; Pipeline **VALIDATED**（Phase 7.0）; Corpus **PARTIAL**（Ziwei, 41 节点, Phase 7.1.1） | — | — | 10（pipeline 回归） |

> **只标记实际状态**: 本表仅反映已完成的工件与验证。未达到的阶段不得
> 标注为已完成。
> **Phase 6.1**: BaZi 迁移评估完成（`docs/governance/bazi/Bazi_CAPABILITY_ASSESSMENT.md`）,
> 状态维持 Implemented（无虚报）。模板领域无关性审查:
> `docs/governance/CAPABILITY_TEMPLATE_REVIEW.md`。
> **Phase 6.4**: BaZi **Freeze Review PASS**（`BAZI_FREEZE_REVIEW.md`, B1~B6 冻结,
> Deferred 项裁定, 24 向量充分）→ 契约草案
> （`docs/bazi/BAZI_BEHAVIOR_CONTRACT_DRAFT.md`, `bazi:behavior:0.1.0-draft`）→
> 状态升级 **Contract Candidate**（契约尚未正式冻结）。
> **Phase 6.5**: BaZi 契约正式冻结 **v1.0.0**（`BAZI_BEHAVIOR_CONTRACT.md`）+
> Reference 独立实现（`reference/bazi/`, 无 src 导入）+ 14/14 BC 审计 +
> **24/24 Production == Reference 等价** → 状态升级 **Reference Certified**。
> **Phase 6.6**: BaZi Schema 登记（SCHEMAS.md §3.1）+ 变更政策生效 +
> 集成边界审查 7/7（`BAZI_INTEGRATION_READINESS.md`）→ 状态升级
> **Integration Ready**（完整生命周期完成）。
> **Phase 7.0**: Ziwei 迁移评估完成（`docs/governance/ziwei/` 4 份工件）;
> 状态维持 **Implemented**（无虚报）; Framework 可零修改复用（结论:
> Reusable without modification）。
> **Phase 6.7.1**: Ziwei 算法稳定化完成（2026-08-13）—— 审计
> `ZIWEI_ALGORITHM_AUDIT.md` + 假设 `ZIWEI_ALGORITHM_ASSUMPTIONS.md` +
> 规则裁定 `ZIWEI_RULE_DECISION.md`（14 Freeze Candidate / 3 Deferred）+
> 跨域边界 `ZIWEI_CROSS_DOMAIN_BOUNDARIES.md` + 向量设计
> `ZIWEI_GOLDEN_VECTOR_READINESS.md` + 补测 +21（12→33, 全绿）。
> 状态维持 **Implemented**; 未创建契约/向量/Reference。
> **Phase 6.7.1.5**: 决策解决（2026-08-13）—— 四项裁定全部 **REVISED +
> ACP Required（未执行）**: A-1 定局表（统一生成规则）、A-2 廉贞 -8、
> ZW-001 输入校验、sxtwl 固定 `2.0.7`。完整记录
> `docs/governance/ziwei/ZIWEI_DECISION_RESOLUTION.md`; 状态维持
> **Implemented**; Phase 6.7.2 向量生成必须等待 ACP 执行。
> **Phase 6.7.1.6**: ACP 实施（2026-08-13）—— ACP-ZW-001（定局表生成式,
> 统一规则 起宫 丑/辰/亥/午/酉 + 步长 2/3/3/3/3）、ACP-ZW-002（廉贞 -8）、
> ACP-ZW-003（输入校验显式化）、ACP-ZW-004（sxtwl==2.0.7 pin）全部
> **IMPLEMENTED**（记录: `docs/governance/ACP/`）; Engine **v0.3.0**;
> 快照/校验测试迁移; 全仓库 578/578 全绿; Ziwei 规则集无 ACP 阻塞,
> Phase 6.7.2 向量生成可按修订规则集启动。状态维持 **Implemented**。
> **Phase 6.7.2**: Golden Vector 生成（2026-08-13）—— 24 个规范性向量
> `docs/ziwei/golden_vectors.json`（Engine v0.3.0 输出生成, status=candidate,
> 17/17 规则覆盖 + A-1/A-2 专项 PASS）+ 回归测试 7 例; 全仓库 585/585 全绿。
> 状态维持 **Implemented**。
> **Phase 6.7.3**: Freeze Review & Gate（2026-08-13）—— 证据审查 6/6 PASS;
> 边界裁定 A-3/A-4/A-6/A-7 全部 **FROZEN**（显式声明）; 17 规则终态
> （3 IMPLEMENTED + 14 FROZEN）; Verdict **PASS** → 契约草案
> `docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT_DRAFT.md`（BC-001~014）。
> 状态维持 **Implemented**。
> **Phase 6.7.4**: Reference Certification（2026-08-13）—— `reference/ziwei/`
> 独立实现（tables/astronomy/domain, 无 src 导入, 显式复用 reference/bazi
> 共享原语）+ **24/24 Golden Vector 等价** + 4 例等价测试 + 14/14 BC 审计 +
> 认证记录 → 状态升级 **Reference Certified**。
> **Phase 6.7.5**: Integration Ready Closure（2026-08-13）—— 契约正式冻结
> **`ziwei:behavior:v1.0.0`**（BC-001~014, 2026-08-13）+ Freeze Integrity
> Check 8/8 + Schema 登记确认（SCHEMAS.md §3.2）+ 变更政策生效 +
> 集成边界审查 7/7（`ZIWEI_INTEGRATION_READINESS.md`）→ 状态升级
> **Integration Ready**（完整生命周期完成, 与 Qimen/BaZi 并列）。
> **Phase 7.0**: Knowledge Pipeline Validation（2026-08-13）—— `knowledge/`
> 试点语料（Ziwei 20 节点/12 关系/3 引用）+ 确定性 Pipeline + KB-001~020
> 校验 + 10 回归测试（报告:
> `docs/governance/knowledge/KNOWLEDGE_SPRINT_0_REPORT.md`）→
> Knowledge Layer 状态: Architecture **FROZEN**（未变）/ Pipeline
> **VALIDATED** / Corpus **PARTIAL**（仅指针更新, 不升级——引用层不产生
> 计算输出）。
> **Phase 7.1.1**: Ziwei Core Vocabulary（2026-08-13）—— 新增 21 节点
> （main_star +9 / palace +7 / ten_god +5, 均 Tier 1 来源, 武曲/贪狼含
> 中州派 SchoolView）+ Pilot 20 节点正式化 → **41/41 节点完成**,
> 校验/确定性通过（报告: `docs/governance/knowledge/KNOWLEDGE_PHASE_7.1.1_REPORT.md`）。
> Corpus: **PARTIAL**（Ziwei, 41 节点; 关系/引用待 7.1.2/7.1.3; 仍为引用层, 不升级）。
> **Phase 7.1.0**: Ziwei Corpus Scope & Source Freeze（2026-08-13）——
> 7 份治理工件（Scope / Source Registry / Admission Policy / Pilot Audit /
> Coverage Matrix / Build Plan / Gaps）→ Corpus 范围与来源策略**已冻结**
> （第一波: 41 节点 + 24 关系 + 8 引用; 构建序列 7.1.1~7.1.6）。
> Knowledge Layer 状态: Architecture **FROZEN** / Pipeline **VALIDATED** /
> Corpus **PARTIAL**（Scope 已冻结, 语料数量未变; 仍为引用层, 不升级）。

---

## Qimen

**Status**:

Integration Ready — **Certified Frozen Capability**（完整生命周期 Stage 0→4）

**Contract**:

v1.0.0（`docs/specification/QIMEN_BEHAVIOR_CONTRACT.md`, `contract_id: qimen:behavior:v1.0.0`）

**Reference**:

Certified（`docs/qimen/reference_certification.md`, 2026-08-09）
Independent Implementation, 双实现验证（Product == Reference, 30/30 等价）

**Verification**:

24 Golden Vectors（`docs/qimen/golden_vectors.json`, Frozen Verification Artifacts, 机器回归 24/24）

**Change Policy**:

ACP Required（ACP + 契约版本递增 + Golden Vector 迁移 + Reference 重新认证）

**冻结工件（Frozen Artifacts）**:

- Qimen Behavior Contract v1.0.0
- Golden Vector 数据集（24 向量）
- Reference Certification Report

**Constraints / Forbidden**:

- 禁止修改 `src/openmetaphysics/domain/qimen/` 算法代码
- 禁止修改 `reference/qimen/` 算法文件
- 禁止修改测试（除文档校验类测试）
- 禁止修改 Behavior Contract
- 禁止修改 Golden Vector 数据
- 禁止添加解释规则（Interpretation）
- 禁止添加新依赖

**范围之外（不属于冻结能力）**:

Interpretation / Recommendation / Narrative Generation / Belief Scoring /
LLM Reasoning / RAG Knowledge / Consensus Decision。Qimen 域只产生
确定性观测结果。

---

## BaZi（八字）

**Status**:

**Integration Ready** — Certified Capability（Phase 6.6, 2026-08-09）
—— 完整生命周期 Stage 0→4 完成: 契约 v1.0.0 Frozen + Reference Certified +
Schema 登记 + 变更政策生效 + 集成边界审查 PASS（
`docs/bazi/BAZI_INTEGRATION_READINESS.md`, 7/7）。
> 评估依据: `docs/governance/bazi/Bazi_CAPABILITY_ASSESSMENT.md`（Phase 6.1）
> Phase 6.2 稳定化工件（Draft, 未冻结）: `docs/bazi/BAZI_ALGORITHM_ASSUMPTIONS.md` /
> `docs/bazi/BAZI_RULE_DECISION.md` / `docs/bazi/BAZI_GOLDEN_VECTOR_PLAN.md` /
> `docs/bazi/BAZI_TEST_COVERAGE_REVIEW.md`
> Phase 6.3 证据（Candidate）: **24 向量**（`docs/bazi/golden_vectors.json`,
> engine 0.1.0, status=candidate）+ `BAZI_FREEZE_BOUNDARY.md` +
> `tests/test_bazi_golden_vectors.py`（7 例）+ `BAZI_GOLDEN_VECTOR_REPORT.md`
> Phase 6.4 冻结: `BAZI_FREEZE_REVIEW.md`（B1~B6 FROZEN, Deferred 裁定,
> 向量充分）+ `BAZI_CROSS_DOMAIN_BOUNDARIES.md` +
> `BAZI_BEHAVIOR_CONTRACT_DRAFT.md`（DRAFT）+ `tests/test_bazi_units.py`（14 例）
> Phase 6.5 认证: `BAZI_BEHAVIOR_CONTRACT.md`（**v1.0.0 Frozen**）+
> `reference/bazi/` 独立实现 + `BAZI_REFERENCE_AUDIT.md`（14/14 PASS）+
> `reference/tests/test_bazi_equivalence.py`（**24/24 等价**）+
> `BAZI_REFERENCE_CERTIFICATION.md`
> Phase 6.6 闭环: SCHEMAS.md §3.1 登记 + `BAZI_INTEGRATION_READINESS.md`（7/7）

**Calculation Layer**:

- 算法: `src/openmetaphysics/agents/bazi.py`（BaziEngine v0.1.0: 四柱, 十神/藏干/纳音/大运）
- 确定性: 是（无 LLM 参与；determinism 测试覆盖）
- Schema: 领域专属 `BaziInput`/`BaziChart`/`Pillar`/`DaYun`（`extra="forbid"`,
  位于 `agents/bazi.py`）；**未登记 SCHEMAS.md / 未导出 JSON Schema**
- 测试: `tests/test_bazi.py`（11）+ `tests/test_bazi_units.py`（14, Phase 6.4 补齐）

**Contract Layer**:

- 契约: **Frozen v1.0.0** `docs/bazi/BAZI_BEHAVIOR_CONTRACT.md`
  （`bazi:behavior:v1.0.0`; Draft 历史保留于 BAZI_BEHAVIOR_CONTRACT_DRAFT.md）
- 冻结规则: **B1~B6 FROZEN**（`BAZI_FREEZE_REVIEW.md` PASS）
- Golden Vectors: 24（**normative fixtures**, 机器回归 7 例通过）
- 政策裁定: 晚子时 23:00 换日; 大运 round(x.5) 银行家舍入

**Reference Layer**:

- 独立实现: `reference/bazi/`（tables/astronomy/domain, **无 src 导入**, 测试强制）
- 认证: **Certified** `docs/bazi/BAZI_REFERENCE_CERTIFICATION.md`
  （14/14 BC 审计 + 24/24 Production == Reference 精确等价）
- 变更政策: 任何变更须 ACP + 契约版本递增 + 向量迁移 + Reference 重新认证

**下一步（Reference Certified 退出条件 → Integration Ready）**:

- ~~Stage 4 治理注册完成~~ ✅（本表登记 + `BAZI_INTEGRATION_READINESS.md` 7/7, Phase 6.6）
- ~~变更政策生效~~ ✅（契约 §5 + 本表, 与 CAPABILITY_LIFECYCLE.md §5 一致）
- ~~SCHEMAS.md 登记~~ ✅（§3.1, 按冻结契约 BC-013 实际结构）
- 可选: JSON Schema 导出（`Model.model_json_schema()`, 未实现, 不影响状态）

---

## Ziwei（紫微斗数）

**Status**:

**Integration Ready** — Certified Capability（Phase 6.7.5, 2026-08-13）
—— 完整生命周期 Stage 0→4 完成: 契约 v1.0.0 Frozen + Reference Certified +
Schema 登记 + 变更政策生效 + 集成边界审查 PASS（
`docs/governance/ziwei/ZIWEI_INTEGRATION_READINESS.md`, 7/7 + Freeze Integrity 8/8）。
> Phase 7.0 评估（2026-08-09）: `docs/governance/ziwei/ZIWEI_CAPABILITY_ASSESSMENT.md`
> + `ZIWEI_RULE_INVENTORY.md`（ZW-001~017）+ `ZIWEI_TEST_COVERAGE_REVIEW.md`
> + `ZIWEI_CROSS_DOMAIN_PRECHECK.md`（ZB-01~09 / ZQ-01~04 差异登记）

**Calculation Layer**:

- 算法: `src/openmetaphysics/agents/ziwei.py`（ZiweiEngine **v0.3.0**:
  命宫/身宫, 五行局, 十四主星定局, 农历转换; 辅星/四化/大限未实现;
  Phase 6.7.1.6: 定局表统一生成规则 + 廉贞 -8 + 输入校验）
- 确定性: 是（无 LLM; replay 测试锁定）
- Schema: **领域专属** `ZiweiInput`（lunar_month/lunar_day 显式重放）/
  `ZiweiChart`/`Palace`（`extra="forbid"`）; SCHEMAS.md §3.2 已登记
  （Phase 6.7.1 完成勘误: calendar_note 位于 ZiweiChart; 未导出 JSON Schema）
- 测试: `tests/test_ziwei.py`（**33 例** = 12 基线 + 21 Phase 6.7.1 补测:
  定局表 150 组合快照 / 全 5 局 / 星曜位置 / 时区链 / 时辰窗 / 闰月 /
  立春界 / 序列化; 覆盖矩阵见 `ZIWEI_TEST_COVERAGE_REVIEW.md` §5）

**Contract Layer**:

- **契约**: **v1.0.0 Frozen**（`docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT.md`,
  `contract_id: ziwei:behavior:v1.0.0`, 2026-08-13, BC-001~014）
- **Golden Vectors**: `docs/ziwei/golden_vectors.json`（**24**, normative
  fixtures, Engine v0.3.0 生成, 机器回归 24/24）
- **变更政策**: ACP Required（ACP + 契约版本递增 + Golden Vector 迁移 +
  Reference 重新认证; 契约 §1/§6 + 本表 Ziwei 节 + INTEGRATION_READINESS §2）
- 规则裁定工件: `ZIWEI_ALGORITHM_ASSUMPTIONS.md`（ZW-A1~A15）/
  `ZIWEI_RULE_DECISION.md`（ZW-001~017: **3 IMPLEMENTED + 14 FROZEN**）/
  `ZIWEI_DECISION_RESOLUTION.md` + `docs/governance/ACP/ACP-ZW-001~004.md` /
  `ZIWEI_CROSS_DOMAIN_BOUNDARIES.md`（ZB-01~09 / ZQ-01~04）/
  `ZIWEI_GOLDEN_VECTOR_READINESS.md`

**Reference Layer**:

- `reference/ziwei/`（tables / astronomy / domain, **独立实现, 无 src 导入**;
  共享原语显式复用 `reference/bazi/*`——立春界/干支/纳音）
- `reference/tests/test_ziwei_equivalence.py`（4 例: 24/24 等价 / 独立性 /
  确定性 / 序列化）
- 审计: `docs/governance/ziwei/ZIWEI_REFERENCE_AUDIT.md`（**14/14 PASS**）;
  认证: `ZIWEI_REFERENCE_CERTIFICATION.md`

**冻结工件（Frozen Artifacts）**:

- Ziwei Behavior Contract v1.0.0（`docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT.md`）
- Golden Vector 数据集（24 向量, `docs/ziwei/golden_vectors.json`）
- Reference 独立实现 + 认证记录（`reference/ziwei/` +
  `ZIWEI_REFERENCE_CERTIFICATION.md`）
- 集成边界审查（`ZIWEI_INTEGRATION_READINESS.md`, 7/7）

**约束（Constraints / Forbidden）**:

- 禁止修改 `src/openmetaphysics/agents/ziwei.py` 算法代码
- 禁止修改 `reference/ziwei/` 算法文件
- 禁止修改 Behavior Contract / Golden Vector 数据
- 禁止添加解释规则 / 新依赖（须 ACP）

**范围之外（不属于冻结能力）**:

辅星/杂曜/四化/大限/流年 / 格局分析 / 解释层 / 叙述 / 建议 / LLM / RAG /
Consensus（契约 §4 显式排除; 任何新增能力须 ACP）

**下一步**:

- 无（Integration Ready = 完整生命周期终点, 对齐 Qimen/BaZi）。
- 未来能力扩展（功能 Sprint）与契约化升级须经 ACP + 用户授权。

---

## Liuyào（六爻）

**Status**:

Implemented（Stage 1 完成；未进入 Contract Candidate）

**Calculation Layer**:

- 算法: `src/openmetaphysics/agents/liuyao.py`（起卦/纳甲/静卦/动卦, 种子确定性）
- 确定性: 是（PRNG 种子来自输入）
- Schema: 共享 `AgentInput`/`AgentOutput` 信封；无领域专属 Schema
- 测试: `tests/test_liuyao.py`（6 例通过）

**Contract Layer**:

无（无契约、无 Golden Vectors）

**Reference Layer**:

无（无 `reference/liuyao/` 独立实现）

**下一步（迁移前置）**:

- 领域专属 Schema 定义
- 规则清单 + 向量草案 → Freeze Review → 契约化

---

## Consensus（共识 — 非计算域）

**Status**: N/A

Consensus 是**跨领域聚合层**（Evidence → ConsensusReport），不属于命理
计算领域，不适用领域能力生命周期。其自身行为由
`CONSENSUS_BEHAVIOR_SPEC.md`（25 条, Frozen）治理。

---

## 生命周期参考

领域能力按三层生命周期固化：Domain Calculation Layer → Behavior Contract
Layer → Reference Verification Layer（状态模型见 `CAPABILITY_LIFECYCLE.md`，
架构定位见 `docs/ARCHITECTURE.md` §1）。
