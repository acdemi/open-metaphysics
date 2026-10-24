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
| **`ACP-REF-001`** | **Conformance 行为覆盖与"空转检查"处置** | **IMPLEMENTED**（选项 A） | 2026-09-16 | `reference/conformance_runner.py`、`knowledge_behavior.py`、`consensus_behavior.py`、`conformance.py`（**CF-015 规范未改**） |
| **`ACP-REF-002`** | **Reference Runtime 范围扩张追认与契约层补全** | **PROPOSED** | 2026-09-16 | `REFERENCE_RUNTIME_SPEC` §3.1/§3.2/§6.1/§10、`reference/contracts/` |
| **`ACP-LIUYAO-001`** | **六爻行为契约冻结与 Reference 认证** | **IMPLEMENTED** | 2026-10-23 | `docs/liuyao/` 契约/25 向量、`reference/liuyao/`、`CAPABILITY_STATUS.md` |
| **`ACP-KNOWLEDGE-001`** | **知识语料 EOL 固定与跨平台 digest 复现性修复** | **PROPOSED** | 2026-10-24 | `knowledge/**/*.yaml`、`knowledge/ziwei_corpus.json`、语料 digest 登记 |

## 已实施（IMPLEMENTED）

- **`ACP-REF-001`**（2026-09-16，**选项 A · 补齐实现**；含同日勘误）：`_check_behavior_coverage`
  原硬编码 **17/52** 个 CF-015 所需 ID 且不校验代表物 → 现已改为**逐 ID 执行代表物**，
  并补齐缺失验证器：KB-001~011（11 条）与 CS-002~007/008/009/010/018/019/022/024（13 条）。
  **结果：检查 135 → 170、行为覆盖 52/52、`behavior_coverage = 1.0`、`unrepresented = []`、
  `certified = True`（强度已如实）**；`CONFORMANCE_SPEC` **零修改**（走 A 而非 B）。
  测试 618 → **627**（含 2 个负向对照锁定机制非空转）。
  ⚠ 待你确认一点：CF-015 原文用词是 "at least one **golden vector**"，本次代表物为**可执行行为验证器**
  （更强、执行真实断言），若要求字面一致需再出一次小 ACP。

## 待批准（PROPOSED）

- **`ACP-REF-002`**：`REFERENCE_RUNTIME_SPEC` §3.2 把 KnowledgeStore / Consensus 列为
  *Out of Scope*「MUST NOT be added without ACP」，而二者**已实现且有 v1.0.0 契约**；
  同时缺 `rule_contract.json` / `pattern_contract.json`。需裁定：追认 + 修订规范 + 补契约。
- **`ACP-KNOWLEDGE-001`**：固定 `knowledge/**/*.yaml` 为 LF；在 LF 工作区重新登记
  `ziwei_corpus` digest（`69d6e2a6…` → `93dba067…`，内容零变化）；修复 Linux/LF 下
  测试重写冻结语料与门控方向；补 BaZi/Qimen/Liuyao 全量 digest 锚定。
> `ACP-REF-001` 已实施且**未触碰 CF-015 规范**；`ACP-REF-002` 与
> `ACP-KNOWLEDGE-001` 均未实施：获批前仓库对 `docs/specification/` 与
> `knowledge/ziwei_corpus.json`（冻结件）保持零改动。

### `ACP-LIUYAO-001`（2026-10-23，D1-D4 批准并实施）

- 契约 `liuyao:behavior:v1.0.0`（30 条款）与 25 Golden Vectors 已 **Frozen**。
- `reference/liuyao/` v0.1.0 **Certified**；tz-naive 修正与自动 seed 冻结外
  声明一并生效。
- Liuyao 已升级为 **Integration Ready（Certified Frozen Capability）**；全量
  回归 1024 passed + 2 skipped。
- **合并状态**：已获 H7 授权并合并（`7a6d7bb`）；归档 `930ae70`；EOL 固定 `a27bb4a`；未推送 origin。
