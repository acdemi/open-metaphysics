# ACP-REF-002 — Reference Runtime 范围扩张追认与契约层补全

> **Status**: **IMPLEMENTED**（2026-10-24 人工批准、实施并合并 `275fb88`）
> **触发**: 2026-09-16 全项目审计 §2.7（`docs/PROJECT_REVIEW_2026-09-16.md`）
> **范围**: `docs/specification/REFERENCE_RUNTIME_SPEC.md`（冻结规范）+ `reference/` 契约层
> **Approved by**: 用户（2026-10-24，选项 A，含最终冻结推进）
> **纪律**: 依 H3 —— 冻结工件/规范变更须 ACP + 人工批准

---

## 1. 问题（实测证据）

1. **规范与现状冲突**：`REFERENCE_RUNTIME_SPEC.md` §3.2（L93-107）**明确**将
   **KnowledgeStore 实现**与 **Consensus Engine** 列为 *Out of Scope*，并写明
   **"MUST NOT be added without ACP"**。而二者**均已实现并各有 v1.0.0 契约**：

   | 组件 | 实现 | 契约 |
   |------|------|------|
   | KnowledgeStore | `reference/knowledge_query.py`（526 行）+ `reference/knowledge.py`（177 行） | `reference/contracts/knowledge_contract.json`（v1.0.0） |
   | Consensus Engine | `reference/consensus_builder.py`（483 行）+ `reference/consensus.py`（140 行） | `reference/contracts/consensus_contract.json`（v1.0.0） |
   | Conformance | `reference/conformance_runner.py`（526 行） | （无独立契约） |

2. **无 ACP 留痕**：`docs/governance/ACP/` 现 6 文件（ZW-001~004 IMPLEMENTED、SCHEMA-001 撤回、
   SCHEMA-001 自审），**无任何 Reference Runtime 范围或冻结相关提案**；
   `REFERENCE_RUNTIME_SPEC.md` §10 Revision History **仅 1 条**（2026-07-12）。

3. **契约层不完整**：`reference/contracts/` 缺 **`rule_contract.json`** 与 **`pattern_contract.json`**
   （`RUNTIME_CONTRACT.md` §10 L468-469 与 `reference/contracts/README.md` L81-82 仍标 Planned）；
   相应生成器与 `test_contract_file_matches_runtime` 等价 diff 测试亦缺。Conformance 的
   `supported_contracts` 因此只有 3 层（evidence/knowledge/consensus）。

4. **无冻结退出标准**：`CAPABILITY_STATUS.md` 只有 Qimen/BaZi/Ziwei/Liuyào/Knowledge 五行，
   **无 Reference Runtime 登记行**；`CAPABILITY_LIFECYCLE.md` 的 6 状态模型为**域级**，
   不覆盖 Reference Runtime 整体 → 路线图的 "Reference Freeze Candidate → Frozen" **无判据**。

## 2. 影响

- 任何按 §3.2 阅读的人都会得出「KnowledgeStore / Consensus 不应存在于 Reference Runtime」的结论，
  与仓库现状（且已被 Conformance 与域认证依赖）直接冲突。
- 无 ACP 留痕意味着该范围扩张的**决策时点与依据不可追溯**（实际发生在 Sprint 4/5/5.5）。
- 契约层缺 2 份 + 无 Reference 级冻结判据 → Reference Runtime **无法进入 Frozen**。

## 3. 选项

| 选项 | 内容 | 评价 |
|------|------|------|
| **A（推荐）** | **追认**：出具本 ACP 记录该范围扩张（决策时点 Sprint 4/5/5.5、依据、影响），并据此**修订** `REFERENCE_RUNTIME_SPEC.md` §3.1/§3.2/§6.1 与 §10 Revision History；同批补 `rule`/`pattern` 契约 | 消除规范-现状冲突；为最终冻结提供前提 |
| B | **收缩**：把 `knowledge_query.py` / `consensus_builder.py` 移出 Reference Runtime | **不可行** —— 已被 Conformance（3 层契约）与域认证依赖 |
| C | 仅内部补记、不改规范 | **不可接受** —— 规范与现状继续冲突，读者被误导 |

## 4. 建议

**选项 A**，并分两批：

- **A-1（治理）**：追认 + 修订 `REFERENCE_RUNTIME_SPEC.md`（§3.1/§3.2/§6.1/§10）+ 在
  `CAPABILITY_STATUS.md` 增加 **Reference Runtime 登记行**（含状态与退出判据指针）。
- **A-2（契约）**：补 `export_rule_contract` / `export_pattern_contract` + `rule_contract.json` /
  `pattern_contract.json` + 两份 diff 测试，使 5 层契约齐平。

> 注意：A-1 修改 `docs/specification/*`（冻结规范）→ 须**版本递增**；A-2 修改 `reference/`（冻结域）→ 同样须 ACP 授权。

## 5. 与最终冻结的关联

Reference Runtime 进入 **Frozen** 的完成条件（本 ACP 提案的判据部分）：

1. ACP-REF-002 的追认与规范修订完成（本文件）；
2. ACP-REF-001 的认证口径定稿并落地（`certified` 语义可信）；
3. 契约层 5 份齐平（A-2）；
4. `CAPABILITY_STATUS.md` 有 Reference Runtime 登记行 + 退出判据；
5. 新增 `docs/governance/REFERENCE_FREEZE_REVIEW.md`（Reference 级冻结审查工件，覆盖 7 模块 + 3 域 + 5 层向量）；
6. 门槛验证：`pytest -q reference/tests` 48 passed；`pytest -q` 618 收集 exit 0；
   `ConformanceRunner` 在新口径下如实报告；`generate_golden_vectors()` 重生成 5 文件逐字节一致；
   3（或 5）份契约 `export_*_contract()` 与 committed 逐字节一致。

## 6. 待批准事项

- [x] 选项 A（追认 + 规范修订 + 契约补全）
- [x] 授权修订 `REFERENCE_RUNTIME_SPEC.md`（v1.1.0）并在 `CAPABILITY_STATUS.md` 增加 Reference Runtime 行
- [x] 授权同批补 `rule`/`pattern` 契约与生成器（`reference/` 冻结域）
- [x] 最终冻结在本批一并推进（`REFERENCE_FREEZE_REVIEW.md`）

---

## 7. 实施记录（2026-10-24）

| 项 | 交付 | 状态 |
|----|------|------|
| A-1 规范追认 | `REFERENCE_RUNTIME_SPEC.md` v1.1.0（§3.1/§3.2/§6.1/§10）；`CONFORMANCE_SPEC.md` v1.1.0（CF-015 措辞 + 修订历史）；`RUNTIME_CONTRACT.md` v1.1.0（5 层 inventory） | DONE |
| A-2 契约补全 | `export_rule_contract` / `export_pattern_contract` + `rule_contract.json` / `pattern_contract.json` + 2 个 diff/determinism 测试 | DONE |
| 契约齐平 | 5 层契约（rule/pattern/evidence/knowledge/consensus）；`ConformanceRunner.certify().supported_contracts` 动态 5 项 | DONE |
| Conformance 收口 | CF-016~CF-019 实装；D-16 裁定（executed representation）；`generate_golden_vectors` 固定 LF | DONE |
| 冻结审查 | `docs/governance/REFERENCE_FREEZE_REVIEW.md`（PASS） | DONE |
| 状态登记 | `CAPABILITY_STATUS.md` Reference Runtime 行 + 6 条判据 | DONE |
| 验证 | Reference 373 passed；Conformance 176/176 certified；全仓 1028+2；5 层 golden 重生成逐字节一致；ruff PASS | DONE |
| H7 合并到 main | `275fb88`（2026-10-24） | DONE |

> 本批未改变任何 Reference 运行时行为：新增契约导出、conformance 检查与
> EOL 固定均为非行为性变更；5 层契约版本维持 1.0.0。
