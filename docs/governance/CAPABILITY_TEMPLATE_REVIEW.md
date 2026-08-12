# Capability Template Review

> **Sprint**: Phase 6.1 — Template Validation（框架领域无关性验证）
> **日期**: 2026-08-09
> **对象**: `docs/governance/CAPABILITY_LIFECYCLE.md`、
> `docs/governance/DOMAIN_CAPABILITY_TEMPLATE.md`、
> `docs/governance/CAPABILITY_STATUS.md`
> **方法**: 逐节标注 Domain Independent / Qimen Specific；以 BaZi 审计
> （`docs/governance/bazi/Bazi_CAPABILITY_ASSESSMENT.md`）为验证实例。

---

## 1. 结论（TL;DR）

**框架领域无关（Domain Independent）**。三个治理文档中 Qimen 特定内容仅
存在于示例（instance）层面，全部位于可替换的 `Qimen 实例` 列或各域自己的
状态条目中；标准条款、阶段要求、状态定义、迁移规则、模板字段本身
**零 Qimen 绑定**。BaZi 映射验证通过（见 `Bazi_CAPABILITY_ASSESSMENT.md` §3）。

**建议**: 无需修改任何模板字段。仅两处可选强化（§5），不阻塞使用。

---

## 2. 逐文档审查

### 2.1 CAPABILITY_LIFECYCLE.md

| 节 | 内容 | 判定 | 说明 |
|----|------|------|------|
| §1 目的 | 标准化流程定义 | ✅ Domain Independent | 无领域绑定 |
| §2 阶段表（必选/可选） | 5 阶段要求 | ✅ Domain Independent | 要求为流程性（确定性/schema/契约/向量/等价/注册），无命理内容 |
| §2 阶段 Qimen 实例列 | `QIMEN_ALGORITHM_ASSUMPTIONS.md` 等 | ⚠️ **Qimen Specific（示例）** | 仅实例引用，结构上为可替换列；BaZi 映射时替换为自身工件即可 |
| §3 状态模型（6 状态） | 修改权/工件/退出标准 | ✅ Domain Independent | 状态定义纯治理性 |
| §4 阶段↔状态映射 | 映射表 | ✅ Domain Independent | |
| §5 迁移规则 | ACP/版本递增/向量迁移 | ✅ Domain Independent | 对齐 CONTRACT_VERSIONING.md |
| §6 治理影响 | 新领域强制标准 | ✅ Domain Independent | |

### 2.2 DOMAIN_CAPABILITY_TEMPLATE.md

| 字段 | 判定 | 说明 |
|------|------|------|
| Domain Metadata（name/version/status） | ✅ Domain Independent | |
| Calculation Layer（algorithm source / determinism / schema） | ✅ Domain Independent | `qimen` 仅出现在示例值 |
| Contract Layer（contract version / golden vectors） | ✅ Domain Independent | 不规定向量内容/数量 |
| Reference Layer（independent implementation / verification） | ✅ Domain Independent | |
| Integration Layer（evidence output / consensus compatibility） | ✅ Domain Independent | |
| 变更政策（ACP 四步） | ✅ Domain Independent | |

### 2.3 CAPABILITY_STATUS.md

| 节 | 判定 | 说明 |
|----|------|------|
| 状态矩阵表结构 | ✅ Domain Independent | |
| Qimen 条目 | ⚠️ Qimen Specific（数据） | 属状态数据，非模板结构 |
| BaZi/Ziwei/Liuyào 条目 | ⚠️ 各域数据 | 各域独立状态条目 |

---

## 3. Qimen Specific 内容清单（全部为数据/示例，非结构）

| 位置 | 内容 | 性质 |
|------|------|------|
| LIFECYCLE §2 各阶段 | `QIMEN_*` 文档名 / `reference/qimen/` / QC-001~014 / D2/D14 / E014~E017 | 实例列 |
| TEMPLATE 各表 | `qimen:behavior:v1.0.0` 等示例值 | 示例 |
| STATUS Qimen 节 | 24 向量 / v1.0.0 / 30/30 等价 | 状态数据 |
| LIFECYCLE 提及的九宫/值符等 | 仅 Qimen 契约文本中（**不**在本框架文档中） | — |

> 未发现九宫规则、宫位映射、奇门向量假设被写入任何框架条款。

---

## 4. 以 BaZi 验证框架可用性（Domain Independence Proof）

| 框架要求 | BaZi 对照 | 结论 |
|----------|-----------|------|
| Stage 1: 确定性 + schema + 测试 | BaziEngine v0.1.0 + BaziInput/BaziChart + 11 tests | ✅ 条款直接适用 |
| Stage 2: 冻结规则 + 契约 + 向量 + Freeze Review | 缺（规则清单可枚举: 立春界/晚子时/五虎遁/五鼠遁/十神/大运） | ✅ 流程适用，缺工件是域内工作量 |
| Stage 3: 独立实现 + 等价 | 缺（reference/bazi/ 不存在） | ✅ 流程适用 |
| Stage 4: 注册 + 变更政策 | 未到 | ✅ 流程适用 |

**结论**: 框架对 BaZi 的映射不存在任何"Qimen 特有假设"阻塞；
五阶段/六状态可直接复用，无需框架修改。

---

## 5. 可选强化建议（不阻塞，可延后）

1. **LIFECYCLE §2**: 可将阶段表"Qimen 实例"列更名为"参考实例"（列数据
   保持 Qimen 示例 + 指向各域评估文档），降低被误读为 Qimen 专属流程的风险。
2. **TEMPLATE**: 可在 Calculation Layer 增加"边界用例文档"建议项
   （Qimen 有 QIMEN_FREEZE_REVIEW 向量充分性审查；BaZi 审计发现边界
   用例文档化缺失）。此项为**建议字段**，非必选，纳入需人工确认。

> 按 Phase 6.1 约束（仅评估，不改框架），本文档未对模板做任何修改。
