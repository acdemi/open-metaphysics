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
| **BaZi** | Implemented | 无 | 无 | 无 | 11 |
| **Ziwei** | Implemented | 无 | 无 | 无 | 12 |
| **Liuyào** | Implemented | 无 | 无 | 无 | 6 |
| Consensus | N/A（非计算域） | — | — | — | — |

> **只标记实际状态**: 本表仅反映已完成的工件与验证。未达到的阶段不得
> 标注为已完成。

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

Implemented（Stage 1 完成；未进入 Contract Candidate）

**Calculation Layer**:

- 算法: `src/openmetaphysics/agents/bazi.py`（四柱引擎, 十神/藏干/纳音/大运）
- 确定性: 是（无 LLM 参与；determinism 测试覆盖）
- Schema: 共享 `AgentInput`/`AgentOutput` 信封（`src/openmetaphysics/core/schemas.py`）；
  无领域专属 Schema
- 测试: `tests/test_bazi.py`（11 例通过）

**Contract Layer**:

无（无契约、无 Golden Vectors、无冻结规则）

**Reference Layer**:

无（无 `reference/bazi/` 独立实现）

**下一步（迁移前置）**:

- 领域专属 Schema 定义（Stage 1 退出标准）
- 规则清单 + 向量草案 → Freeze Review → 契约化（复用 Qimen 流程,
  见 `CAPABILITY_LIFECYCLE.md` §5）

---

## Ziwei（紫微斗数）

**Status**:

Implemented（Stage 1 完成；未进入 Contract Candidate）

**Calculation Layer**:

- 算法: `src/openmetaphysics/agents/ziwei/`（宫位 + 十四主星 + 五行局 + 农历转换）
- 确定性: 是
- Schema: 共享 `AgentInput`/`AgentOutput` 信封；无领域专属 Schema
- 测试: `tests/test_ziwei.py`（12 例通过）

**Contract Layer**:

无（无契约、无 Golden Vectors）

**Reference Layer**:

无（无 `reference/ziwei/` 独立实现）

**下一步（迁移前置）**:

- 领域专属 Schema 定义
- 规则清单 + 向量草案 → Freeze Review → 契约化

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
