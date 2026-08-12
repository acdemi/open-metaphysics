# AGENTS.md — OpenMetaphysics

> This file is loaded automatically by Codex CLI on every session.
> It is the **long-term rule set** for all work in this repository.
> Scope: entire repository tree.

---

## Project Overview

**OpenMetaphysics** — local-first, privacy-preserving multi-agent Chinese
metaphysics reasoning framework. Deterministic rule engines for
八字/紫微/奇门/六爻/梅花/大六壬, optional LLM for explanation only.

- **Rule First. Knowledge Second. LLM Last.**
- Reference Runtime (Python, in-memory, deterministic) is the normative
  behavior standard for all formal implementations (Rust / Go / Python / WASM).
- All behavior is governed by Architecture Contracts and Behavior Contracts
  under `docs/specification/`.

---

## Sprint Discipline (MANDATORY — applies to every Sprint)

These rules are **non-negotiable**. Every Sprint MUST satisfy ALL of the
following:

### 1. One Domain Per Sprint

Only implement **one** domain per Sprint. Do not mix Knowledge, Consensus,
Explain, RAG, or any other layer in the same Sprint unless explicitly
instructed.

### 2. No Cross-Domain Modification

Do NOT modify code, models, schemas, or contracts outside the current
Sprint's domain. Specifically:

- If the Sprint is about Knowledge → do NOT touch Rule / Pattern / Evidence.
- If the Sprint is about Evidence → do NOT touch Knowledge / Consensus.
- If the Sprint is about Consensus → do NOT touch Rule / Knowledge logic.

Cross-domain reads are allowed. Cross-domain writes are **forbidden**.

### 3. No Premature Implementation

Do NOT implement content from future Sprints. If the user says "Sprint N",
only do Sprint N. Even if you know Sprint N+1 will need something, do NOT
add it. Wait for the user to explicitly start Sprint N+1.

### 4. No Speculative Abstraction

Do NOT add abstraction "because it might be useful later." No interfaces,
protocols, base classes, hooks, or extension points unless the current
Sprint explicitly requires them. YAGNI (You Aren't Gonna Need It) is the
rule.

### 5. Design Deficiency → ACP, Not Direct Modification

If you discover that the current design is insufficient during
implementation:

- **STOP**.
- Do NOT modify the design yourself.
- Output an **Architecture Change Proposal (ACP)** describing:
  - What is insufficient.
  - Why it is insufficient.
  - Proposed change.
  - Impact on existing Behavior Contracts.
- Wait for user approval before proceeding.

This applies to: Rule, Pattern, Evidence, Knowledge, DSL, Schema, Behavior
Contracts, and any normative specification.

### 6. Prefer Mature Open Source (No Reinventing Wheels)

Before implementing any non-core module, evaluate existing open source
projects with:

- **License**: MIT, Apache-2.0, or BSD only.
- **Maintenance**: actively maintained, reasonable release frequency.
- **Community**: meaningful star count and contributor base.

Only self-build modules that are **core competitive advantage**:
Rule DSL, Pattern Engine, Evidence Engine, Consensus Engine, Explain Engine.

For everything else (calendar, astronomy, lunar, database drivers, graph DB,
vector DB, embedding, RAG, workflow, agent framework, MCP SDK), prefer
reuse. See `docs/engineering/12_open_source_evaluation.md`.

### 7. Reference Runtime Supremacy

The **Reference Runtime** (`reference/`) always takes priority over any
production implementation (`src/`, `crates/`, `services/`, `packages/`).

- Any formal implementation MUST conform to Reference Runtime Contracts
  and Behavior Contracts.
- If a formal implementation produces different output, the **implementation
  is buggy**, not the Reference Runtime.
- The Reference Runtime is never modified to match an implementation without
  an approved ACP.
- See: `docs/specification/REFERENCE_RUNTIME_SPEC.md`

---

## Completion Rule

**完成立即停止。等待下一 Sprint。**

When the current Sprint's deliverables are complete and all tests pass:

1. Stop working.
2. Summarize what was done.
3. Do NOT start the next Sprint.
4. Wait for the user to explicitly initiate the next Sprint.

---

## Conversation Workflow Convention (MANDATORY — every conversation)

**每次对话都必须遵守以下约定：**

### 1. 输出归档

每次对话（每轮会话）结束前，MUST 将本轮输出追加记录到 `context/归档.md`：

- 记录内容：日期、分支名、本轮产出文件清单（代码/文档/配置）、各自状态（待合并 / 已合并）、遗留事项。
- 格式：追加式，每次对话追加一条记录（`## 2026-XX-XX <主题>` 小节），不覆盖历史。
- 归档记录本身也是产出，必须先写归档再结束对话。

### 2. 分支工作流

- 每次对话的所有代码/文档输出 MUST 在独立分支上进行，命名：`work/<领域>/<主题>`。
- 禁止直接在主分支（main）上做代码或文档输出。
- 分支上的工作可以 commit，但 **禁止 merge 到 main**。

### 3. 用户把控合并

- 每轮对话结束汇报：分支名、变更文件、diff 摘要、建议（合并/关闭）。
- **是否合并、是否进入下一步，由用户决定。** 未获明确指令不得合并、不得推送。
- 用户同意后，合并由用户执行或明确授权后执行。

---

## Quick Reference: Key Directories

| Path | Purpose |
|------|---------|
| `reference/` | Normative Reference Runtime (Python, in-memory, deterministic) |
| `reference/contracts/` | Auto-generated Architecture Contracts (JSON) |
| `reference/examples/` | Golden example data (YAML) |
| `docs/design/phase6/` | Phase 6 Architecture Freeze (immutable) |
| `docs/engineering/` | Engineering Freeze + Technology Selection |
| `docs/specification/` | Normative specifications (Behavior, Contract, Governance) |
| `tests/` | Golden Tests (Reference Runtime verification) |
| `src/` | Production Python code (not Reference Runtime) |
| `crates/` | Production Rust code |
| `services/` | Production Go code |

## Quick Reference: Specification Documents

| Document | Scope |
|----------|-------|
| `docs/specification/REFERENCE_RUNTIME_SPEC.md` | Reference Runtime authority + ACP process |
| `docs/specification/BEHAVIOR_SPEC.md` | 35 Behavior Contracts (Rule/Pattern/Evidence) |
| `docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md` | 20 Knowledge Behavior Contracts |
| `docs/specification/CONSENSUS_BEHAVIOR_SPEC.md` | 25 Consensus Behavior Contracts |
| `docs/specification/CONFORMANCE_SPEC.md` | 20 Conformance Rules (CF-001~020) |
| `docs/specification/RUNTIME_CONTRACT.md` | Contract lifecycle + merge gate |
| `docs/specification/CONTRACT_VERSIONING.md` | Version bump rules + ACP matrix |
| `docs/specification/IMPLEMENTATION_GUIDE.md` | Production Runtime implementation guide |



Sprint 完成
      │
      ▼
运行 Unified Architecture Governance Review
      │
      ▼
生成 Review Report
      │
      ▼
人工确认
      │
      ▼
Documentation Refresh（如需要）
      │
      ▼
Commit
      │
      ▼
进入下一 Sprint