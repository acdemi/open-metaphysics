# AGENTS.md — OpenMetaphysics

> 本文件是仓库的**长期规则集**（每次会话自动加载）。
> **2026-09-15 精简版**：删除重复的仪式性流程，保留安全与正确性门控。
> 变更记录见文末「规则变更记录」。

---

## 0. Project Overview

**OpenMetaphysics** — local-first、隐私优先的多智能体中国术数推理框架。
八字/紫微/奇门/六爻等的**确定性规则引擎**；LLM 仅用于解释层。

- **Rule First. Knowledge Second. LLM Last.**
- **Reference Runtime**（`reference/`，Python、内存、确定性）是所有正式实现
  （Rust / Go / Python / WASM）的**行为标准**。
- 行为由 `docs/specification/` 下的 Architecture Contract 与 Behavior Contract 治理。

---

## 1. 硬规则（Hard Rules — 不可协商）

| # | 规则 | 要点 |
|---|------|------|
| **H1** | **单域单 Sprint** | 一个 Sprint 只做一个域/一件事。不混做 Knowledge + Consensus + Explain。 |
| **H2** | **跨域写禁止** | 不得修改当前 Sprint 域之外的代码/模型/Schema/契约；**跨域读允许**。 |
| **H3** | **冻结工件只经 ACP 变更** | Behavior Contract、Golden Vector、`reference/contracts/*.json`、`reference/` 行为实现、`docs/specification/*` 的变更须走 **ACP**（Architecture Change Proposal）并等人工批准。发现设计不足 → **停止并出 ACP**，不得自行改设计。 |
| **H4** | **Reference Runtime 至上** | 实现与 Reference 不一致时，**实现是错的**；不得为迁就实现而改 Reference（除非已批准 ACP）。 |
| **H5** | **证据不虚构** | 知识条目必须可回指已登记来源的原文（条目级 passage/章节）；**不可核实 → 记 GAP，不生产**；禁止以"网上常见""训练知识"充当证据。 |
| **H6** | **真人/付费/外网实验须授权** | 涉及真实 API、计费、外部主体的实验（如 Phase 4 ACIS）：须人工授权 + 冻结窗口 + 证据保全（SHA-256 登记）+ 零 retry/窗外请求。 |
| **H7** | **合并门槛** | 只有**测试全绿 + 确定性可复现**的分支才可合并；合并用 `git merge --no-ff`；**合并需用户授权**（一次性预授权可覆盖一批已完成的 Sprint）。 |
| **H8** | **完成即停** | Sprint 交付完成 → 汇报并停止（不自动开下一个 Sprint），除非用户预授权连续推进。遇阻塞/需决策 → 出报告停在门口。 |

---

## 2. 效率规则（Efficiency — 替代原重复条款）

### E1 决策分级（哪些事不用问）

- **自主执行（无需请示）**：证据获取与逐字核验、文档、测试、内部重构、
  GAP 登记、状态指针刷新、确定性/性能/可读性改进、清理已合并分支。
- **必须请示**：冻结工件或规范变更（H3，走 ACP）、跨域写、**合并到 main**
  （除非已预授权）、付费或使用真实外部主体的实验、对外发布/推送。

### E2 一个 Sprint 一份报告

Sprint 结束只写**一份报告**（模板见 E5）。不再要求同一 Sprint 同步产出
多份状态文档、成功标准清单、执行记录等仪式性文档。

### E3 状态指针单一权威 + 轻量归档

| 文档 | 何时更新 | 篇幅 |
|------|----------|------|
| `docs/governance/CAPABILITY_STATUS.md` | **唯一能力/语料指针**；合并时更新 | 1~3 行/次 |
| `docs/PROJECT_STATUS.md` | 只在**阶段边界**更新（不逐 Sprint） | 按需 |
| `context/归档.md` | **合并或 Sprint 完成**时追加 | **≤15 行**（分支/产出/验证/决策），只读或分析型会话不写 |

### E4 轻量变更可直推 main

以下可**跳过分支流程**直接提交 main：归档记录、状态指针刷新、错别字与
GAP 编号修正、已合并分支清理、纯格式/注释修正。
其余（代码、数据、契约、报告、实验工件）走 `work/<领域>/<主题>` 分支。

### E5 报告模板（5 节，建议 ≤80 行）

~~~text
# <Sprint> 报告
1. 结果         —— 一句话结论 + 关键数字（做了什么 / 没做什么）
2. 证据与复现   —— 命令、digest、断言回执、可复现步骤
3. 边界与零触碰 —— 未触碰的冻结工件/域；git diff 证据
4. GAP 与决策点 —— 状态变更 + 需人工裁定的事项（编号 D-1..）
5. 产出物清单   —— 文件 + 状态
~~~

禁止复制历史报告的样板段落；禁止用章节数量充数。

### E6 复用优先

非核心模块（日历/天文/数据库驱动/图数据库/向量库/RAG/工作流/Agent 框架/MCP SDK）
优先复用成熟开源（MIT / Apache-2.0 / BSD，活跃维护）。
自建仅限**核心竞争优势**：Rule DSL、Pattern Engine、Evidence Engine、
Consensus Engine、Explain Engine、各计算域内核。

### E7 不过度设计（YAGNI）

不实现未来 Sprint 的内容；不加"以后可能有用"的接口/抽象/钩子。
当前 Sprint 不需要的能力一律不加。

---

## 3. 合并与发布

1. 分支命名：`work/<领域>/<主题>`；分支基于 `main`（或说明基点的原因）。
2. 合并：`git merge --no-ff <branch>`，合并提交信息含**范围 + 验证结论**。
3. 合并后：删除或保留分支由用户决定；**不推送 origin**（除非明确授权）。
4. 紧急/低风险变更按 E4 直推 main。

---

## 4. 关键目录

| Path | Purpose |
|------|---------|
| `reference/` | 规范 Reference Runtime（Python、内存、确定性） |
| `reference/contracts/` | 自动生成的 Architecture Contract（JSON，冻结） |
| `docs/design/phase6/`, `docs/engineering/` | 架构/工程冻结（不可修改） |
| `docs/specification/` | 规范文档（Behavior / Contract / Governance） |
| `knowledge/` | 知识语料（sources / corpus / pipeline / validate） |
| `src/`, `crates/`, `services/` | 正式实现（Production Runtime） |
| `tests/`, `reference/tests/` | Golden Tests / Reference 独立套件 |

## 5. 规范文档索引

| Document | Scope |
|----------|-------|
| `docs/specification/REFERENCE_RUNTIME_SPEC.md` | Reference Runtime 权威 + ACP 流程 |
| `docs/specification/BEHAVIOR_SPEC.md` | 35 Behavior Contracts（Rule/Pattern/Evidence） |
| `docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md` | 20 Knowledge Behavior Contracts（KB-001~020） |
| `docs/specification/CONSENSUS_BEHAVIOR_SPEC.md` | 25 Consensus Behavior Contracts |
| `docs/specification/CONFORMANCE_SPEC.md` | 20 Conformance Rules（CF-001~020） |
| `docs/specification/RUNTIME_CONTRACT.md` | 契约生命周期 + 合并门 |
| `docs/specification/CONTRACT_VERSIONING.md` | 版本递增规则 + ACP 矩阵 |
| `docs/specification/IMPLEMENTATION_GUIDE.md` | 生产实现指南 |
| `docs/governance/CAPABILITY_LIFECYCLE.md` | 领域能力 5 阶段 / 6 状态 |
| `docs/governance/CAPABILITY_STATUS.md` | 能力状态唯一权威登记 |

---

## 规则变更记录

### 2026-09-15 — 精简（用户指示：删减不必要的规则，提高开发效率）

**删除/合并**：

- 「每次对话必须归档 `context/归档.md`」→ 改为 **E3**：仅合并/Sprint 完成时追加 ≤15 行。
- 「每次对话所有输出必须在独立分支」→ 改为 **E4**：轻量变更直推 main，其余走分支。
- 「每 Sprint 同步更新多份状态文档 + 成功标准清单 + 执行记录」→ 改为 **E2/E3**：1 份报告 + 1 个能力指针。
- 「Sprint 完成 → Unified Architecture Governance Review → Review Report → 人工确认 → Documentation Refresh → Commit」五步仪式 → 并入 **H7/E2**：验证 → 1 份报告 → 合并。
- Sprint Discipline 原 7 条（含重复的"不要提前实现""不要投机抽象"）→ 合并为 **H1/H2/H3/E6/E7**。

**新增**：

- **E1 决策分级**：明确"无须请示"的自主范围（证据/文档/测试/重构），减少无谓等待；
  同时收敛"必须请示"清单（冻结工件、跨域写、合并、真实实验）。
- **E5 报告模板**（5 节 ≤80 行）。

**保留（安全与正确性关键，未删减）**：H1~H8 全部；证据不虚构（H5）；
冻结工件 ACP（H3）；Reference 至上（H4）；外网/付费实验授权与窗口纪律（H6）；
测试与确定性合并门（H7）。

**理由（实测）**：Phase 7.2A / 7.2B / 7.3 三个 Sprint **产出 0 个知识节点**，
却各自产生 143 / 210 / 180 行报告，且每次都要同步
`CAPABILITY_STATUS` + `PROJECT_STATUS` + `SOURCE_STATUS` + `GAPS` 四类指针；
`context/归档.md` 已逾 1000 行 —— 流程本身成为主要工作量。
