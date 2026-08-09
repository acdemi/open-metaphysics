# Domain Capability Lifecycle

> **标准**: OpenMetaphysics 领域能力生命周期规范（Domain Capability Standard）
> **来源**: 从 Qimen 域完整生命周期（Phase 5 系列）提炼的标准化流程
> **状态**: v1.0（正式架构概念，见 `docs/ARCHITECTURE.md` §1）
> **更新**: 2026-08-09
> **治理**: 所有领域（八字/紫微/奇门/六爻）的能力演进必须遵守本文档；
> 契约冻结后的一切变更须 **ACP**（见 §6）。

---

## 1. 目的

Qimen 域完成了首个完整能力生命周期（计算层 → 契约层 → Reference 验证层 →
Certified Frozen Capability）。本文档将该过程标准化为所有未来领域的
**强制性流程**，定义：

- 生命周期阶段（Stage）及其要求（§2）
- 能力状态模型（Status）及其治理规则（§3）
- 阶段 ↔ 状态映射（§4）
- 迁移规则（§5）
- 治理影响（§6）

---

## 2. 生命周期阶段（从 Qimen 流程提炼）

每个领域依次经过 5 个阶段。**必选（Mandatory）** 为该阶段进入下一阶段的
门槛；**可选（Optional）** 为推荐但非强制的工作。

### Stage 0 — Exploration（探索）

| 类别 | 项 | 说明 |
|------|----|------|
| **必选** | 非正式规则（informal rules） | 规则以文档/笔记形式记录（可含流派分歧、待裁定项） |
| **必选** | 实验性实现（experimental implementation） | 可运行的实验代码，无稳定性承诺 |
| 可选 | 算法假设记录 | 近似/简化的显式声明（如 Qimen D2 日号近似） |

**Qimen 实例**: `QIMEN_ALGORITHM_ASSUMPTIONS.md`、早期 `qimen.py` 实验实现。

### Stage 1 — Calculation Runtime（计算运行时就绪）

| 类别 | 项 | 说明 |
|------|----|------|
| **必选** | 确定性算法 | 纯函数，相同输入 ⇒ 相同输出；无随机/时钟/IO/LLM |
| **必选** | Schema 定义 | 领域输入/输出 Pydantic 模型（含 JSON Schema 导出） |
| **必选** | 测试可用 | 单元测试 + 确定性/回放测试 |
| 可选 | RuntimeAdapter / ABI / 类型边界 | 跨语言或多实现适配（Qimen 5.8/5.9A 已落地） |

**Qimen 实例**: `qimen.py`（engine 0.3.0）+ `SCHEMAS.md §3.3`（QimenInput/QimenBoard）+ `test_qimen.py`。

### Stage 2 — Behavior Contract（行为契约）

| 类别 | 项 | 说明 |
|------|----|------|
| **必选** | 可观测规则冻结（rule freeze） | 冻结规则清单，逐条核对 定义→实现→测试→向量 覆盖 |
| **必选** | 版本化契约 | 版本化 Behavior Contract 文档（如 `qimen:behavior:v1.0.0`） |
| **必选** | Golden Vectors | 规范回归装置（normative fixtures），逐字节比对 |
| **必选** | Freeze Review | 契约冻结前评审（规则一致性 + 向量充分性 + 边界核查） |
| 可选 | 政策裁定文档 | 流派分歧的显式裁定（如 Qimen D2/D14） |
| 可选 | 机器回归 | 向量自动回归防护网（Qimen E014） |

**Qimen 实例**: 12 条冻结规则 → `QIMEN_BEHAVIOR_CONTRACT.md` v1.0.0 → 24 规范向量 → `QIMEN_FREEZE_REVIEW.md` PASS。

### Stage 3 — Reference Certification（Reference 认证）

| 类别 | 项 | 说明 |
|------|----|------|
| **必选** | 独立实现 | `reference/<domain>/` 自包含实现（不得导入 `src/`） |
| **必选** | 契约验证 | 独立实现通过契约全部条款审计（如 14/14 QC Full） |
| **必选** | 等价测试 | Product 与 Reference 双实现抽样逐字节等价 |
| 可选 | 认证工件 | 认证报告（certification report）+ 独立性源码检查 |
| 可选 | 独立测试套件 | `reference/tests/` 独立测试集 |

**Qimen 实例**: `reference/qimen/` + `reference_contract_audit.md`（14/14 QC）+ `test_equivalence.py`（30/30）+ `reference_certification.md`（E015/E016/E017）。

### Stage 4 — Certified Capability（认证能力 = 集成就绪）

| 类别 | 项 | 说明 |
|------|----|------|
| **必选** | 治理注册 | 在 `docs/governance/CAPABILITY_STATUS.md` 登记状态、契约、工件 |
| **必选** | 变更政策声明 | 冻结工件清单 + 变更流程（ACP 强制） |
| **必选** | 集成就绪 | 确定性观测输出可供上层（Evidence/Consensus/API）消费 |
| 可选 | 双实现验证声明 | 持续双实现回归（每次变更后重新认证） |

**Qimen 实例**: `CAPABILITY_STATUS.md` 注册为 **Certified Frozen Capability**。

---

## 3. 能力状态模型（Status Model）

能力状态反映领域当前所处的治理位置，共 6 级，**只允许逐级提升**。

### Status 定义

| Status | 含义 | 允许的修改 | 必备工件 | 退出标准 |
|--------|------|-----------|----------|----------|
| **Experimental** | 探索期 | 自由修改算法/规则/文档 | 非正式规则记录 + 实验实现 | 确定性算法可运行且有测试 |
| **Implemented** | 计算运行时就绪 | 算法可调整，须记录变更 | 确定性算法 + Schema + 测试 | 测试全绿 + 确定性验证通过 + 规则清单完整 |
| **Contract Candidate** | 契约草案评审期 | 仅限契约草案与评审文档修改 | 契约草稿 + 冻结规则清单 + 向量草案 | Freeze Review **PASS** |
| **Contract Frozen** | 契约已冻结 | 仅 ACP 批准的变更（bug fix 亦须 ACP） | 版本化契约 + Frozen Golden Vectors | 契约版本确立 + 向量机器回归通过 |
| **Reference Certified** | Reference 已认证 | 同上 + 认证工件维护 | 独立实现 + 认证报告 + 等价测试 | 契约条款审计通过 + 等价测试通过 |
| **Integration Ready** | 集成就绪（Certified Capability） | 仅 ACP 批准的变更 | 能力状态注册 + 变更政策 + 冻结工件清单 | 治理注册完成 + 变更政策生效 |

### 状态不变式

1. **不可跳级**: 状态只能逐级迁移（Experimental → … → Integration Ready）。
2. **冻结不可逆**: 达到 Contract Frozen 后，未经理事流程（ACP）不得降级或修改。
3. **状态必须真实**: 治理登记只反映实际完成的工作与工件；未完成的阶段
   不得标注为已完成（见 `CAPABILITY_STATUS.md` "只标记实际状态"）。
4. **契约冻结是分水岭**: 冻结前变更自由度高；冻结后一切变更走 ACP。

---

## 4. 阶段 ↔ 状态映射

| Stage | 对应 Status | 核心交付 |
|-------|------------|----------|
| Stage 0 Exploration | Experimental | 规则笔记 + 实验代码 |
| Stage 1 Calculation Runtime | Implemented | 算法 + Schema + 测试 |
| Stage 2 Behavior Contract（草案期） | Contract Candidate | 契约草稿 + 评审 |
| Stage 2 Behavior Contract（冻结期） | Contract Frozen | 契约 vN + Golden Vectors |
| Stage 3 Reference Certification | Reference Certified | 独立实现 + 认证报告 |
| Stage 4 Certified Capability | Integration Ready | 治理注册 + 变更政策 |

---

## 5. 迁移规则

1. **升级门槛**: 每个状态迁移必须满足上一状态的退出标准（§3 表）。
2. **冻结后变更流程（强制）**: 达到 Contract Frozen 后，任何规则/算法/
   向量变更必须完整执行：
   - **ACP**（Architecture Change Proposal，等待人工批准）
   - **契约版本递增**（v1.0.0 → 下一版本）
   - **Golden Vector 迁移**（不可原地修改，须生成新向量集）
   - **Reference Runtime 更新 + 重新认证**（双实现同步）
3. **降级**: 仅经 ACP 批准（如算法错误需回滚）。
4. **评审门**: Contract Candidate → Contract Frozen 必须通过 Freeze Review
   （规则一致性 + 向量充分性 + 架构边界核查）。

---

## 6. 治理影响

1. **新领域强制标准**: 八字/紫微/六爻等未来领域的契约化必须按本文档流程
   执行（参照 `docs/governance/DOMAIN_CAPABILITY_TEMPLATE.md`）。
2. **状态跟踪**: `docs/governance/CAPABILITY_STATUS.md` 是唯一权威状态登记。
3. **禁止抄近路**: 不允许跳过 Stage 2/3 直接宣称 Certified；不允许以
   "能力已实现" 名义修改已冻结工件。
4. **领域边界**: 能力生命周期只覆盖**确定性计算**。Interpretation /
   Recommendation / Narrative / Belief Scoring / LLM Reasoning / RAG /
   Consensus 不属于领域能力范围，不得混入（见 `docs/ARCHITECTURE.md` §1）。
