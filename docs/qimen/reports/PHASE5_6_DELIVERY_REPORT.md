# Phase 5.6 — Qimen Behavior Contract Freeze 交付报告（存档）

> **归档日期**: 2026-08-09
> **原始场景**: Specification Governance — Contract Finalization
> **状态**: 已交付 — **Qimen 正式冻结（Frozen Contract v1.0.0）**

---

## 1. Executive Summary

Qimen 从 Candidate Freeze 正式转入 **Frozen Contract** 状态：三个冻结阻塞项全部关闭（D2 政策裁定 Option A、D14 行为裁定不换日柱、契约批准），契约草稿 0.1.0-draft → **`docs/specification/QIMEN_BEHAVIOR_CONTRACT.md` v1.0.0（Frozen）**，24 向量从 candidate normative **提升为 normative regression fixtures**。新增契约校验测试 4 项。算法零修改，408 tests passing。

## 2. D2 Decision

**Option A — 冻结当前实现为规范行为**（"Qimen Runtime v0.3.0 定义日号三元近似为规范行为"）：

- 依据：行为稳定（24 向量 + 33 测试锁定）、近似已显式文档化（非隐藏）、本 Sprint 禁止实现变更
- 生效：契约 QC-004 冻结日号近似（1-10/11-20/21-30 → 0/3/6）
- 改判路径：真拆补法 = 未来 ACP + 契约主版本递增 v1.0.0 → v2.0.0 + 24 向量迁移（`QIMEN_D2_IMPACT_ANALYSIS.md`）→ 分类为 future extension

## 3. D14 Decision

**冻结"晚子时（23:00-24:00）不换日柱"**为规范行为：

- 向量 `N_late_zishi`（2024-05-15 23:30，day_of_month=15）锁定行为
- 改判 = ACP + 主版本递增 + 向量重生成（future extension）

## 4. Contract Changes

| 项 | 草稿 (0.1.0-draft) | 正式 (v1.0.0 Frozen) |
|----|---------------------|----------------------|
| 位置 | docs/qimen/QIMEN_BEHAVIOR_CONTRACT_DRAFT.md | **docs/specification/QIMEN_BEHAVIOR_CONTRACT.md** |
| 状态 | Draft | **Frozen** |
| 条款 | QC-001~014 | QC-001~014（每条款含 Definition/Preconditions/Deterministic requirement/Observable output/Related rules/Golden vectors/Test references 七要素） |
| D2 | Deferred rule dependency | **政策裁定 Option A**（QC-004 冻结） |
| D14 | Deferred | **冻结（不换日柱）** |
| 映射 | 缩写 id | 全量 id（机器可校验） |
| 版本政策 | - | 新增 §6（1.0.x / 次版本 / 主版本规则） |

## 5. Golden Vector Status

- 24 向量 `classification`: candidate_normative → **normative_fixture**
- 文件头新增: `status: normative_fixtures`、`contract_reference`、`promotion_version: 1.0.0`、`immutable: true`
- 不可变、版本钉定（rule_set_version 0.3.0 / engine_version 0.3.0）、迁移须 ACP

## 6. Modified Files

| 文件 | 变更 |
|------|------|
| `docs/specification/QIMEN_BEHAVIOR_CONTRACT.md` | **新增** — 正式冻结契约 v1.0.0 |
| `docs/qimen/golden_vectors.json` | 24 向量提升为 normative fixtures + 头部元数据 |
| `docs/qimen/QIMEN_FREEZE_GAP.md` | 4 缺口全部 Closed；剩余风险分类（frozen/limitation/extension） |
| `docs/qimen/QIMEN_BEHAVIOR_CONTRACT_DRAFT.md` | 标记 Superseded |
| `docs/qimen/QIMEN_RULE_DECISION.md` / `QIMEN_FREEZE_REVIEW.md` | 状态更新（D2/D14 裁定、评审升级 PASS） |
| `tests/test_qimen_contract.py` | **新增** — 契约校验 4 测试 |
| `tests/test_qimen.py` | 分类断言扩展（normative_fixture） |
| `src/openmetaphysics/agents/qimen.py` | **零修改** |

## 7. Test Results

```
ruff check            ✅ All checks passed
ruff format --check   ✅ 68 files already formatted
pytest                ✅ 408 passed (404 + 4 contract tests)
契约校验              ✅ IDs 唯一/映射完整/向量存在/版本一致
Golden validation     ✅ 24/24 通过 (full-board/metadata/determinism/serialization)
```

## 8. Remaining Risks

| 类别 | 内容 |
|------|------|
| 已冻结行为 | 日号三元近似（D2 Option A）、晚子时不换日（D14）、12 冻结规则（QC-001~014 覆盖） |
| 已知局限 | 与主流拆补法系统性差异；天禽不寄宫简化；八神阴遁不逆布；13/24 节气向量覆盖 |
| 未来扩展 | 真拆补法（v2.0.0 路径）、格局/用神/暗干、RAG/Consensus、Reference Qimen 域、跨语言 RuntimeAdapter |

## 9. Next Recommended Sprint

- **Reference Runtime Qimen Domain Sprint**：以契约 v1.0.0 + 24 规范向量为对齐基线，在 `reference/` 实现奇门域
- 或 **功能扩展 Sprint**（格局判断 / 用神，需新授权）
- 或跨语言实现（Rust/Go，届时引入 RuntimeAdapter）

## Governance Compliance

```
qimen 算法 未修改 ✅   Schema 未修改 ✅   reference/ 未修改 ✅
其他域契约未创建 ✅   无解释层/RAG/Consensus ✅
D2 实现未变更（仅政策裁定）✅   契约正式冻结 ✅
```
