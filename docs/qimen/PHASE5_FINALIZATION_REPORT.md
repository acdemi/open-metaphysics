# Phase 5.x Finalization Report

> **Sprint**: Phase 5.x Artifact Finalization（仓库卫生 / 发布准备）
> **日期**: 2026-08-09
> **性质**: 提交边界准备 + 状态快照。不自动提交，不做功能变更。

---

## 1. Lifecycle Summary

Qimen 域完成**首个完整能力生命周期**（见 `docs/governance/CAPABILITY_LIFECYCLE.md`）:

    Stage 0 Exploration      规则记录 + 实验实现（QIMEN_ALGORITHM_ASSUMPTIONS.md）
        ↓
    Stage 1 Calculation      qimen.py 转盘排盘（engine 0.3.0）+ Schema + 测试
        ↓
    Stage 2 Behavior         12 冻结规则 → 契约 v1.0.0 + 24 Golden Vectors
        ↓
    Stage 3 Reference        reference/qimen/ 独立实现 + 14/14 QC + 30/30 等价
        ↓
    Stage 4 Certified        Certified Frozen Capability（Integration Ready）

**最终状态**: Qimen = **Integration Ready**（Certified Frozen Capability）。
BaZi / Ziwei / Liuyào = Implemented（未虚报，见 `CAPABILITY_STATUS.md`）。

---

## 2. Artifact List（42 files, staged）

### 2.1 Phase 5 Qimen implementation（8 files）

| 文件 | 变更 | 内容 |
|------|------|------|
| `src/openmetaphysics/domain/qimen/types.py` | 新增 | 类型边界（TypedDict, 5.9A） |
| `src/openmetaphysics/domain/qimen/structural.py` | 新增 | 结构校验（5.9A） |
| `src/openmetaphysics/domain/qimen/abi.py` | 新增 | ABI 快照验证（5.9A） |
| `src/openmetaphysics/contracts/qimen_contract.schema.json` | 修改 | 契约 Manifest Schema 提取（5.8A: qc_ids / golden_vector_count / deferred_rules） |
| `reference/qimen/__init__.py` | 新增 | Reference 域包 |
| `reference/qimen/astronomy.py` | 新增 | 天文/干支移植（Meeus 同源, 无 src 导入） |
| `reference/qimen/domain.py` | 新增 | 契约实现（依 QC-001~014, 24/24 向量一致） |
| `reference/qimen/CHANGELOG.md` | 新增 | Reference 域变更记录 |

### 2.2 Phase 5 Qimen infrastructure（1 file）

| 文件 | 变更 | 内容 |
|------|------|------|
| `pyproject.toml` | 修改 | `testpaths = ["tests", "reference/tests"]`（独立套件纳入 pytest 默认收集） |

### 2.3 Phase 5 documentation（15 files）

| 文件 | 变更 |
|------|------|
| `docs/qimen/qimen_abi_snapshot.json` | 新增（ABI 快照, 5.9A） |
| `docs/qimen/reference_alignment_proof.md` | 新增（对齐证明, 5.7 对齐） |
| `docs/qimen/reference_certification.md` | 新增（认证记录, E016/E017） |
| `docs/qimen/reference_contract_audit.md` | 新增（14/14 QC 审计） |
| `docs/qimen/reports/PHASE5_7_DELIVERY_REPORT.md` | 新增 |
| `docs/qimen/reports/PHASE5_7_ALIGNMENT_DELIVERY_REPORT.md` | 新增 |
| `docs/qimen/reports/PHASE5_8_DELIVERY_REPORT.md` | 新增 |
| `docs/qimen/reports/PHASE5_8A_DELIVERY_REPORT.md` | 新增 |
| `docs/qimen/reports/PHASE5_8B_DELIVERY_REPORT.md` | 新增 |
| `docs/qimen/reports/PHASE5_8C_DELIVERY_REPORT.md` | 新增 |
| `docs/qimen/reports/PHASE5_9A_DELIVERY_REPORT.md` | 新增 |
| `docs/qimen/reports/PHASE5_9B_DELIVERY_REPORT.md` | 新增 |
| `docs/qimen/reports/README.md` | 修改（5.7~5.9B 索引 + 产物表刷新） |
| `reference/qimen/README.md` | 修改（建模层 → 实现层状态） |
| `reference/qimen/runtime_vs_reference.md` | 修改（对照表刷新） |

### 2.4 Phase 5 tests（7 files）

| 文件 | 变更 | 用例 |
|------|------|------|
| `reference/tests/test_golden_vectors.py` | 新增 | 27（24/24 向量逐字节, E016） |
| `reference/tests/test_contract_boundaries.py` | 新增 | 8 |
| `reference/tests/test_equivalence.py` | 新增 | 3（30/30 抽样等价, E017） |
| `tests/test_qimen_abi.py` | 新增 | 5 |
| `tests/test_qimen_contract_adapter.py` | 新增 | 7 |
| `tests/test_reference_qimen.py` | 新增 | 28 |
| `tests/test_qimen_reference_docs.py` | 修改 | 7（建模层断言 → 实现层断言） |

### 2.5 Phase 6 governance（11 files）

| 文件 | 变更 |
|------|------|
| `docs/governance/CAPABILITY_LIFECYCLE.md` | 新增（生命周期标准） |
| `docs/governance/CAPABILITY_STATUS.md` | 新增（状态矩阵） |
| `docs/governance/DOMAIN_CAPABILITY_TEMPLATE.md` | 新增（登记模板） |
| `docs/ARCHITECTURE.md` | 修改（§1 官方生命周期概念） |
| `docs/PROJECT_STATUS.md` | 修改（状态同步） |
| `docs/ROADMAP.md` | 修改（路线图同步） |
| `context/当前阶段.md` / `项目状态.md` / `下一阶段.md` / `已完成功能.md` | 修改（上下文同步） |
| `README.md` | 修改（Qimen Certified 标注） |

### 2.6 Unrelated changes

**无**。未发现与 Qimen/治理无关的变更。

---

## 3. Contract Version

| 项 | 值 |
|----|-----|
| Behavior Contract | **v1.0.0**（`docs/specification/QIMEN_BEHAVIOR_CONTRACT.md`, **Frozen**, 已提交） |
| contract_id | `qimen:behavior:v1.0.0` |
| 条款 | QC-001 ~ QC-014（14 条, 审计 14/14 通过） |
| 冻结规则 | D1, D3~D14（12 条）；D2 政策裁定（日号近似为规范） |
| engine / rule_set version | 0.3.0 |
| Manifest Schema | `src/openmetaphysics/contracts/qimen_contract.schema.json`（本次批次含提取字段） |

## 4. Golden Vector Count

- **24 个规范向量**（`docs/qimen/golden_vectors.json`, **Frozen** / normative fixtures, 已提交）
- 本批次**无 Golden Vector 变更**（向量数据未在本批次 staged 文件中）
- 机器回归: 24/24 逐字节一致（`test_reference_qimen.py` + `reference/tests/test_golden_vectors.py`）

## 5. Certification Status

| 项 | 值 |
|----|-----|
| 认证 | **Certified**（`docs/qimen/reference_certification.md`, 2026-08-09） |
| Reference 实现 | `reference/qimen/`（独立实现, 源码独立性检查通过: 无 `from/import openmetaphysics`） |
| 契约审计 | 14/14 QC Full（`reference_contract_audit.md`） |
| 确定性等价 | 30/30 抽样逐字节一致（E017, 固定种子 2024） |
| Evidence | E015（5.9B 24/24）/ E016（5.7 自包含 + 独立性）/ E017（5.7 等价） |

## 6. Test Verification

| 范围 | 用例数 | 结果 |
|------|--------|------|
| **全仓库** | **530** | **全部通过** |
| Qimen 排盘 | 33（`tests/test_qimen.py`） | 通过 |
| Qimen 契约 | 8（`tests/test_qimen_contract.py`） | 通过 |
| Qimen 回归 | 26（`tests/test_qimen_regression.py`, 24/24 向量） | 通过 |
| Qimen 适配器 | 7 + 7（adapter / contract_adapter） | 通过 |
| Qimen ABI | 5（`tests/test_qimen_abi.py`） | 通过 |
| Qimen Reference | 28（`tests/test_reference_qimen.py`） | 通过 |
| Qimen Reference 文档 | 7（`tests/test_qimen_reference_docs.py`） | 通过 |
| Reference 独立套件 | 38（reference/tests: 27+8+3） | 通过 |
| ruff check / format | — | 通过 / 已格式化 |

---

## 7. Commit Boundary（建议, 不自动提交）

> **Commit 0（已存在）**: `12dfb79` — 含 Phase 5.7 建模层 + 契约等既有提交历史。
> 以下分组针对**当前 staged 的 42 个文件**，按依赖顺序提交。

**Commit 1 — Qimen Runtime + tests**（9 files）
`src/openmetaphysics/domain/qimen/{types,structural,abi}.py` +
`src/openmetaphysics/contracts/qimen_contract.schema.json` +
`tests/test_qimen_abi.py` + `tests/test_qimen_contract_adapter.py` +
`tests/test_qimen_reference_docs.py`（该文件依赖 reference/qimen 实现层，可并入 Commit 1 或 3）

**Commit 2 — Reference Qimen implementation + tests**（11 files）
`reference/qimen/{__init__,astronomy,domain}.py` + `reference/qimen/CHANGELOG.md` +
`reference/tests/*.py` + `tests/test_reference_qimen.py` + `pyproject.toml`（testpaths）

**Commit 3 — Reference Certification + docs**（15 files）
`docs/qimen/reference_certification.md` + `reference_contract_audit.md` +
`reference_alignment_proof.md` + `qimen_abi_snapshot.json` +
`docs/qimen/reports/PHASE5_7~5.9B_*.md` + `docs/qimen/reports/README.md` +
`reference/qimen/README.md` + `reference/qimen/runtime_vs_reference.md`

**Commit 4 — Governance synchronization**（11 files）
`docs/governance/*` + `docs/ARCHITECTURE.md` + `docs/PROJECT_STATUS.md` +
`docs/ROADMAP.md` + `context/*` + `README.md`

**建议顺序**: Commit 1 → 2 → 3 → 4（依赖: Runtime → Reference → 认证工件 → 治理）。
每步提交前重跑 `pytest` + `ruff`（当前全绿）。

---

## 8. 验证记录

| 检查 | 结果 |
|------|------|
| `git status` | 42 files staged（本批次）+ 0 untracked + 0 unstaged |
| `pytest` | **530 passed** |
| `ruff check src/ tests/ reference/` | All checks passed |
| `ruff format --check` | 99 files already formatted |
| 范围核查 | 全部变更 ∈ {src/qimen, reference/qimen, tests/qimen, docs/qimen, docs/governance/*}；无无关域 / 无关契约 / proto 变更 |
