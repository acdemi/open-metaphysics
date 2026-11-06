# Reference Runtime Freeze Review（Reference 级冻结审查）

> **Status**: **PASS / FROZEN**（2026-10-24，`ACP-REF-002` 批准并实施）
> **Conformance strength（H11/H12，2026-10-31 更正）**: **contract-conformant, checks partial**
> —— 176 checks: `passed=106 / partial=13 / skipped=57 / failed=0`；
> `certified=False`（57 项派生检查无第二实现，13 项 enum 检查无枚举字段可验证）；
> `contract_conformant=True`（0 failure + 行为覆盖 52/52）；conformance 运行已改为**只读**。
> **Date**: 2026-10-24
> **Scope**: Reference Runtime 整体（7 模块家族 + 4 域 Reference + 5 层契约/向量）
> **Inputs**: `REFERENCE_RUNTIME_SPEC.md` v1.1.0、`CONFORMANCE_SPEC.md` v1.1.0、
> `RUNTIME_CONTRACT.md` v1.1.0、`reference/contracts/`、`reference/conformance/golden/`
> **Approval**: 用户（2026-10-24，批准实施 ACP-REF-002）

---

## 1. 冻结判据（ACP-REF-002 §5 对账）

| # | 判据 | 结果 | 证据 |
|---|------|------|------|
| 1 | 追认与规范修订 | PASS | `REFERENCE_RUNTIME_SPEC.md` §3.1/§3.2/§6.1/§10；Spec v1.1.0 |
| 2 | ACP-REF-001 认证口径定稿（D-16） | PASS | `CONFORMANCE_SPEC.md` v1.1.0：CF-015 “executed representation” |
| 3 | 契约层 5 份齐平 | PASS | `rule/pattern/evidence/knowledge/consensus_contract.json`（各 1.0.0）+ 5 个 diff 测试 |
| 4 | CAPABILITY_STATUS 登记行 + 退出判据 | PASS | `CAPABILITY_STATUS.md` Reference Runtime 行 + 判据表 |
| 5 | Reference 级冻结审查工件 | PASS | 本文件 |
| 6 | 门槛验证 | PASS | §2 回执 |

---

## 2. 验证回执（2026-10-24）

| 检查 | 结果 |
|------|------|
| Reference 核心 + 域 + 契约测试 | **373 passed**（`test_reference_{rules,patterns,evidence,knowledge,consensus,conformance,behavior_coverage}.py` + `reference/tests`） |
| 全仓回归 | **1030 collected / 1028 passed + 2 skipped** |
| ConformanceRunner（ReferenceAdapter） | **contract-conformant（H11/H12）**：176 checks = passed 106 / partial 13 / skipped 57 / **failed 0**；`certified=False`，`contract_conformant=True`，`behavior_coverage=1.0`（52/52）；CF-016~CF-019 已执行；运行只读，golden 文件字节/mtime 不变 |
| 契约层 | 5 契约（rule/pattern/evidence/knowledge/consensus）均 1.0.0；`supported_contracts` 5 项；CF-CONTRACT-* 逐模型比对 `required`/`field_types` 与 Reference pydantic 模型 |
| Golden Vectors | 5 层 / 19 向量；`build_golden_vectors()` 内存重生成与 committed **逐字节一致**（LF）；`ConformanceRunner.run()` **不写文件**（H11 前会重写，已修复） |
| 独立实现 | `reference/` 非测试源码无 `openmetaphysics` 导入；生产 `src/` 无 `reference` 导入 |
| 规范版本 | `REFERENCE_RUNTIME_SPEC` v1.1.0、`CONFORMANCE_SPEC` v1.1.0、`RUNTIME_CONTRACT` v1.1.0 |
| EOL | `reference/contracts/**` 与 `reference/conformance/golden/**` 固定 LF，写入器显式 `newline="\n"` |
| ruff | `ruff check src reference tests tools` PASS |

---

## 3. 覆盖清单

### 3.1 核心模块（8 家族）

`models.py` / `parser.py` / `engine.py` / `patterns.py` / `pattern_matcher.py` /
`evidence.py` + `evidence_builder.py` / `knowledge.py` + `knowledge_query.py` /
`consensus.py` + `consensus_builder.py` + `consensus_behavior.py` /
`conformance.py` + `conformance_runner.py`。

### 3.2 域 Reference（4 域）

`reference/qimen/`、`reference/bazi/`、`reference/ziwei/`、`reference/liuyao/`
（自包含；由各域等价套件与认证工件验证）。

### 3.3 契约与向量（5 层）

| 层 | 契约 | Golden 向量数 |
|----|------|---------------|
| Rule | `rule_contract.json` | 6 |
| Pattern | `pattern_contract.json` | 5 |
| Evidence | `evidence_contract.json` | 1 |
| Knowledge | `knowledge_contract.json` | 4 |
| Consensus | `consensus_contract.json` | 3 |

---

## 4. 已知边界与 Deferred（不阻塞冻结）

| 项 | 说明 | 处置 |
|----|------|------|
| Derived checks（D-13） | `CF-SORT/CF-HASH/CF-NULL` 无第二实现/独立 oracle；`CF-ENUM` 改为真实枚举序列化属性检查（13 向量无枚举字段 → partial） | **H11 处置**：前三项标 `skipped`、后一项 `partial/passed`，均不计入 `certified`；不再硬编码 `passed=True`。独立验证需第二套实现，另立 Sprint/ACP |
| CF-015 范围 | 显式要求 52 个行为 ID；35 个 BC 中仅 7 个被 CF-015 点名 | 本次以 `CONFORMANCE_SPEC` v1.1.0 固定为 52 个；扩大范围需新 ACP |
| 多语言实现 | Rust/Go/WASM 生产实现仍未落地 | 属 Phase 9+ 产品范围，不在 Reference 冻结面 |
| Explain / RAG / LLM | 明确排除在 Reference Runtime 之外 | 规范 §3.2 保持不变（已移出 Knowledge/Consensus，仅保留排除项） |

---

## 5. 结论

**PASS（contract-conformant; conformance checks partial）**：Reference Runtime 的范围、契约、
Golden Vectors、Conformance 与规范版本已一致收口，满足 ACP-REF-002 §5 的全部 6 条完成条件。
自本审查生效，`reference/` 行为实现、5 层契约与规范文档的变更 **MUST** 经 ACP。

**H11/H12 更正（2026-10-31）**：本文件不再宣称 "176/176 certified"。
真实状态是 **contract-conformant, checks partial**：

- Conformance 运行**只读**：`ConformanceRunner.run()` 不再调用生成器写 golden；
  `_check_golden_reproducibility` 在内存重生成并逐字节比较，drift 会 **fail 而不是被静默修复**；
  空 golden 目录也不会被自动生成（`CF-GOLDEN-MISSING` failed）。
- 派生检查不再伪装 passed：`CF-SORT/CF-HASH/CF-NULL` = `skipped`（无第二实现/独立 oracle）；
  `CF-ENUM` = 真实枚举序列化属性检查（有枚举字段 → passed；无 → partial；非法 → failed）。
- 检查强度已结构化：`ConformanceCheckResult.status ∈ {passed, failed, partial, skipped}`，
  `ConformanceResult.{partial, skipped, contract_conformant}`；`certified` 需 100% full pass
  （与冻结 `CONFORMANCE_SPEC` 的 `failed==0 && coverage==1.0` 一致）。
- `CF-CONTRACT-*` 从"键存在"升级为逐模型 `required`/`field_types` 对 Reference 模型字段的真实 diff；
  `CF-ARCH-001` 增加 adapter 模块源码 import 扫描（无源码时 partial，不冒充 passed）。

> 这仍不是"独立验证"：golden 期望值由 Reference 自身生成，`CF-SORT/HASH/NULL` 无第二套实现；
> 只有域级等价套件（Qimen 30/30、BaZi 24/24、Ziwei 24/24 等）才是双实现比对。
