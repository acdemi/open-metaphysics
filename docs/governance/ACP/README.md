# ACP 索引（Architecture Change Proposal）

> **流程定义**: `docs/specification/REFERENCE_RUNTIME_SPEC.md` §8.2（触发矩阵 + 流程图）
> **用途**: 冻结工件/规范的变更必须经 ACP + 人工批准（AGENTS.md **H3**）。
> **本索引**: 由 2026-09-16 全项目审计补建（此前该目录**无索引/模板**）。

## 状态图例

| 状态 | 含义 |
|------|------|
| `PROPOSED` | 已起草，**待人工批准**；批准前不得实施任何变更 |
| `APPROVED` | 已批准，待实施 |
| `IMPLEMENTED` | 已实施并验证 |
| `NOT REQUIRED` / `WITHDRAWN` | 经审计判定无需变更 |

## 登记表

| ID | 标题 | 状态 | 日期 | 涉及冻结面 |
|----|------|------|------|-----------|
| `ACP-ZW-001` | 紫微定局表生成式（START/STEP 统一规则） | IMPLEMENTED | 2026-08-13 | Ziwei 契约/算法 |
| `ACP-ZW-002` | 廉贞偏移修正（-9 → -8） | IMPLEMENTED | 2026-08-13 | Ziwei 算法 |
| `ACP-ZW-003` | 输入校验显式化（KeyError → ValueError） | IMPLEMENTED | 2026-08-13 | Ziwei 算法 |
| `ACP-ZW-004` | sxtwl 精确锁定 `==2.0.7` | IMPLEMENTED | 2026-08-13 | 依赖/环境 |
| `ACP-SCHEMA-001` | earthly_branch Schema 归位审计 | NOT REQUIRED（撤回） | 2026-08-13 | KB Schema（无需变更） |
| `ACP-SCHEMA-001`（自审） | 门 A 审计自审 8/8 | —（记录） | 2026-08-13 | KB Schema |
| **`ACP-REF-001`** | **Conformance 行为覆盖与"空转检查"处置** | **PROPOSED** | 2026-09-16 | `reference/conformance_runner.py`、`CONFORMANCE_SPEC` CF-015 |
| **`ACP-REF-002`** | **Reference Runtime 范围扩张追认与契约层补全** | **PROPOSED** | 2026-09-16 | `REFERENCE_RUNTIME_SPEC` §3.1/§3.2/§6.1/§10、`reference/contracts/` |

## 待批准（PROPOSED）

- **`ACP-REF-001`**：现状 `certified=True / coverage=1.0` 含 **83/100 个行为合约 ID 未验证**，
  且 `_check_ordering` / `_check_hash` / `_check_null` / `_check_enum` 为**无条件通过**。
  需裁定：补齐实现（选项 A）还是经 ACP 修订 CF-015（选项 B）；以及 `certified` 的最终判定口径。
- **`ACP-REF-002`**：`REFERENCE_RUNTIME_SPEC` §3.2 把 KnowledgeStore / Consensus 列为
  *Out of Scope*「MUST NOT be added without ACP」，而二者**已实现且有 v1.0.0 契约**；
  同时缺 `rule_contract.json` / `pattern_contract.json`。需裁定：追认 + 修订规范 + 补契约。

> 两份提案均**未实施**；在获批前，仓库对 `reference/` 与 `docs/specification/` 保持零改动。
