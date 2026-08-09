# OpenMetaphysics — 架构设计

> 完全本地运行、隐私保护、多智能体命理推理框架
> 状态：Reference Freeze Candidate (2026-08-09)
> Qimen Domain: **Frozen and Certified**（契约 v1.0.0 + Reference 认证）
> Reference Runtime 已成为行为规范（Normative Reference Implementation）

## 0. 当前架构状态（Reference Freeze Candidate + Qimen Certified）

OpenMetaphysics 项目当前处于 **Reference Freeze Candidate** 阶段。

**Qimen 域已完成完整生命周期**（Domain Calculation Layer → Behavior Contract
Layer → Reference Verification Layer），状态为 **Frozen and Certified**：
- 行为契约 `QIMEN_BEHAVIOR_CONTRACT.md` v1.0.0（Frozen）
- Reference Runtime 认证（`docs/qimen/reference_certification.md`）
- 24 个 Golden Vectors（Frozen Verification Artifacts）
- 双实现验证（Product Runtime 与 Reference Runtime 逐字节一致）

Reference Runtime（`reference/`，Python，内存实现，确定性）已成为整个项目的
**行为规范**（Normative Reference Implementation）。所有正式实现
（Rust / Go / Python / WASM）必须以 Reference Runtime 的 Contract 和 Behavior
为唯一标准。

### Reference Runtime 已完成层

| 层 | 模块 | 文件 | 状态 |
|----|------|------|------|
| Rule | DSL Parser -> RuleEngine -> RuleEvaluation | `reference/parser.py`, `reference/engine.py` | 完成 |
| Pattern | PatternMatcher -> PatternMatch | `reference/pattern_matcher.py` | 完成 |
| Evidence | EvidenceBuilder -> Evidence | `reference/evidence_builder.py` | 完成 |
| Knowledge | KnowledgeStore -> KnowledgeResult | `reference/knowledge_query.py` | 完成 |
| Consensus | ConsensusBuilder -> ConsensusReport | `reference/consensus_builder.py` | 完成 |
| Conformance | ConformanceRunner -> ConformanceResult | `reference/conformance_runner.py` | 完成 |

### Domain Capability Lifecycle（官方架构概念）

领域能力生命周期是**官方架构概念**，完整定义见 §1 与
`docs/governance/CAPABILITY_LIFECYCLE.md`（阶段/状态/迁移规则）、
`docs/governance/CAPABILITY_STATUS.md`（状态登记）。

**当前领域状态**: Qimen 已走完全生命周期 —— **Certified Frozen Capability**
（Integration Ready：契约 v1.0.0 + Reference 认证 + 24 向量双实现验证）。

### Governance 层级

    Reference Runtime (reference/)              ← 最高优先级，行为规范
           ↑ Conformance Suite 验证
    Production Runtime (src/, crates/, services/) ← 必须符合 Reference

- **Reference Runtime 优先于 Production Runtime**。任何正式实现必须以
  Reference Runtime 的 Contract 和 Behavior 为唯一标准。
- 如果正式实现产生不同输出，**实现有 bug**，不是 Reference Runtime。
- Reference Runtime 不得为了适配实现而修改，除非通过 ACP 批准。
- 详见 `docs/specification/REFERENCE_RUNTIME_SPEC.md`。

---

## 1. Domain Capability Lifecycle（官方架构概念）

每个领域（八字/紫微/奇门/六爻）的能力按以下三层生命周期固化，自上而下依赖：

    Domain Calculation Layer     ← 确定性排盘/推演算法（规则驱动，纯函数）
                ↓
    Behavior Contract Layer      ← 冻结契约 + Golden Vectors（行为规范，不可随意修改）
                ↓
    Reference Verification Layer ← Reference Runtime 认证 + 双实现等价验证

- **Domain Calculation Layer**: 领域的确定性计算（如 Qimen 时家转盘排盘）。
  算法冻结后不可随意修改。
- **Behavior Contract Layer**: 领域行为契约（如 `QIMEN_BEHAVIOR_CONTRACT.md`
  v1.0.0）与 Golden Vectors（normative fixtures）。任何变更必须走 **ACP**，
  并递增契约版本、迁移 Golden Vectors。
- **Reference Verification Layer**: Reference Runtime（`reference/`）独立
  实现 + 认证工件（如 `docs/qimen/reference_certification.md`）。验证
  Production 与 Reference 双实现输出一致。

**治理标准**: 生命周期共 5 个阶段（Exploration → Calculation Runtime →
Behavior Contract → Reference Certification → Certified Capability）、
6 个能力状态（Experimental → Implemented → Contract Candidate →
Contract Frozen → Reference Certified → Integration Ready）。阶段要求、
状态治理规则、迁移门槛见 `docs/governance/CAPABILITY_LIFECYCLE.md`；
每域登记模板见 `docs/governance/DOMAIN_CAPABILITY_TEMPLATE.md`；
权威状态登记见 `docs/governance/CAPABILITY_STATUS.md`（只标记实际状态，
不得虚报成熟度）。

**Qimen 已完成完整生命周期**（Stage 0→4, **Integration Ready**）:
契约 v1.0.0 + Reference 认证 + 24 向量双实现验证。其他领域处于
**Implemented**，按标准流程逐步契约化。

### 领域边界（Domain Boundary）

Domain Layer 产生:

- **确定性观测结果**（deterministic observations，如排盘/推演输出）

Domain Layer **不产生**:

- Interpretation（解释）
- Recommendation（建议）
- Narrative Generation（叙述生成）
- Belief Scoring（信念评分）
- LLM Reasoning（大语言模型推理）
- RAG Knowledge（知识检索）
- Consensus Decision（共识决策）

领域计算与解释/建议/叙述/评分层严格隔离；上述能力属于未来 Sprint 的
其他层，不得混入冻结的领域计算能力。任何领域只能输出可由输入单独
重现的确定性观测。

---

## 2. 目标与原则

OpenMetaphysics 通过 **确定性规则引擎** 计算中国命理图表（八字、紫微、奇门、六爻），并使用可选的本地大语言模型层进行推理。核心不变原则：

> **大语言模型永远不参与历法计算、排盘、推演。**
> 所有数值/结构输出都可以从输入单独重现。
> 大语言模型仅限于对已经计算好的结构进行自然语言渲染/解释，并且与计算核心严格隔离。

架构原则（来自需求）：**模块化、可测试、确定性、可解释、可扩展。**

非目标 (v1)：云端遥测、用户账户、移动端。一切都运行在用户机器上；除非用户显式将（可选的）大语言模型提供者指向远程端点，否则不会有请求离开主机。

## 3. 分层架构

`
┌──────────────────────────────────────────────────────────────────────┐
│ 5. API / 编排层        FastAPI + LangGraph 状态机                  │
│    POST /agents/{name}/compute   POST /orchestrate   GET /agents      │
├──────────────────────────────────────────────────────────────────────┤
│ 4. 智能体层         八字 | 紫微 | 奇门 | 六爻 | 共识                 │
│    每个智能体 = 确定性引擎 + (可选) 大语言模型解释器                 │
├──────────────────────────────────────────────────────────────────────┤
│ 3. 推理层             提供者抽象: Ollama/Qwen/DeepSeek              │
│                   (严格隔离)     Qdrant 上的 RAG。仅用于自然语言解释。│
├──────────────────────────────────────────────────────────────────────┤
│ 2. 基础层             Schema (Pydantic) | 领域模型                 │
│                          历法/节气 | 确定性引擎                     │
├──────────────────────────────────────────────────────────────────────┤
│ 1. 持久化             PostgreSQL (会话/追踪) | Qdrant (RAG)         │
└──────────────────────────────────────────────────────────────────────┘
`

数据流（单次请求）：

`
请求(JSON)
  → Pydantic 对比 AgentInput schema 验证
  → LangGraph 路由到一个或多个智能体
  → 每个智能体.run():
        engine.calculate(input)   # 纯函数，确定性，无大语言模型
        → AgentOutput{ result, confidence, reasoning_trace, metadata }
  → 共识智能体.aggregate(outputs)  # 交叉验证 + 加权
  → 可选 大语言模型解释器.render(output)   # 仅返回文本，不能修改结果
  → 对比 AgentOutput schema 验证 → JSON 响应
`

## 4. 确定性契约

计算纯度是结构性强制的，不仅仅是约定：

- DeterministicEngine 是抽象基类，其 calculate() 是 **纯函数**：相同输入 ⇒ 字节相同的输出，无I/O，无时钟，除了种子PRNG（种子来自输入，例如六爻起卦）之外没有随机数。
- 智能体暴露两个严格分离的方法：
  - compute(input) -> AgentOutput — 仅确定性计算。
  - explain(output, style) -> str — 可选，大语言模型支持；接收*已经计算好*的 AgentOutput，只能返回散文。它无法访问引擎。
- metadata.engine_version + metadata.input_hash 使每个结果都可审计、可重放。@frozen_engine 装饰器冻结引擎配置，版本变更必须显式。
- 测试包含 **黄金向量/重放套件**：记录的（输入，输出）对每次运行都断言，捕捉非确定性或回归。

## 5. 智能体重拓扑

智能体相互独立，**仅**通过验证过的 Pydantic 模型 / JSON Schema 通信。没有智能体导入另一个智能体的内部实现；跨智能体数据流通过共识智能体，它消费 AgentOutput 信封。

`
            ┌─────────┐
 请求 ────▶│ 路由  │──┬──▶ 八字智能体 ────┐
            └─────────┘  ├──▶ 紫微智能体 ───┤
                         ├──▶ 奇门智能体 ───┤──▶ 共识智能体 ──▶ 响应
                         ├──▶ 六爻智能体 ───┤
                         └──────────────────┘
`

路由策略可配置：运行全部、运行选中、或大语言模型建议选择（仅选择元数据 — 选择不会改变图表数字）。

## 6. 本地优先与隐私

- 默认配置指向 http://localhost:11434 (Ollama)。没有出站调用。
- 通过相同的 InferenceProvider 接口支持通义千问 / DeepSeek，可以每次调用选择。仅通过环境变量/配置选择远程端点。
- PII（出生日时分/地点）永远不会离开进程进行计算；只有可选的解释器可能传输，而且只传输用户启用的最小结构化负载。
- RAG 知识库（Qdrant）是本地集合；导入是 CLI 命令。

## 7. 技术选型

| 关注点         | 选型           | 理由                                       |
|----------------|----------------|--------------------------------------------|
| 语言           | Python 3.11    | 要求；丰富的类型提示 + Pydantic            |
| 环境管理       | uv              | 标准环境（`.python-version` + `uv.lock`），`uv sync --all-extras` 一键搭建 |
| API            | FastAPI        | 异步，自动 OpenAPI/JSON Schema             |
| 编排           | LangGraph      | 显式状态图，可观测                         |
| 验证           | Pydantic v2    | Schema + JSON Schema 导出                  |
| 大语言模型推理 | Ollama         | 本地；通义千问/DeepSeek 通过相同提供者     |
| 向量数据库(RAG)| Qdrant         | 本地，快速 ANN                             |
| 关系数据库     | PostgreSQL     | 会话，推理追踪，审计                        |
| 可扩展性       | MCP            | 未来工具/插件接口（已占位）                |

重型依赖（Postgres/Qdrant/Ollama）都是**可选**的：核心计算不依赖任何外部服务，可以完全测试。集成优雅降级，通过配置启用。

## 8. 打包与目录结构

`
open-metaphysics/                    # Monorepo（单仓多语言）
├── .python-version                  # 固定 Python 3.11（标准环境）
├── pyproject.toml                   # Python 工作区 + uv 锁文件 (uv.lock)
├── AGENTS.md                        # 长期规则（Sprint Discipline 等）
├── context/                         # 项目状态笔记（快速参考）
├── docs/
│   ├── design/phase6/               # Phase 6 架构冻结（不可修改）
│   ├── engineering/                 # 工程冻结 + 技术选型
│   ├── governance/                  # 领域能力成熟度跟踪（CAPABILITY_STATUS.md）
│   └── specification/               # 行为规范 + Contract 治理
├── reference/                       # ★ 行为规范（Normative Reference Runtime）
│   ├── contracts/                   # 自动生成 Architecture Contract (JSON)
│   ├── conformance/golden/          # 自动生成 Golden Vectors
│   └── *.py                         # Rule/Pattern/Evidence/Knowledge/Consensus/Conformance
├── src/openmetaphysics/             # Production Python
│   ├── core/                        # schemas, models, calendar, engines, config
│   ├── agents/                      # base + bazi/ziwei/qimen/liuyao/consensus
│   ├── inference/                   # providers (ollama/qwen/deepseek), explainer
│   ├── rag/                         # qdrant client + retriever
│   ├── orchestration/               # langgraph graph
│   ├── api/                         # fastapi app + routes
│   └── mcp/                         # future MCP server stub
├── crates/                          # Production Rust（om-calendar 等）
├── services/                        # Production Go
├── proto/                           # gRPC/Protobuf 契约
├── packages/  apps/  frontend/      # 其他语言/应用（占位）
├── tests/                           # Golden Tests + unit + replay + API
└── scripts/  tools/                 # 工具脚本
`

## 9. 可观测性与可解释性

- 每个 AgentOutput 都携带 reasoning_trace：有序的 ReasoningStep 记录（规则引用、输入、输出、描述）。这是审计追踪。
- confidence 被分解 (ConfidenceScore: 值 + 方法 + 因子)，因此用户可以看到为什么一个数字是例如 0.82，而不仅仅知道它是。
- LangGraph 将状态转换作为事件发出，用于追踪/调试。

## 10. 安全边界

- API 边缘输入验证 (Pydantic) 拒绝格式错误/过大输入。
- 出生地点是可选的；如果缺失，时区来自 born_at 的偏移或提供的 timezone 字符串（永远不通过大语言模型推断）。
- 解释器是唯一可联网的路径，默认关闭。
---

## 11. Architecture Governance

### 11.1 Reference Runtime Supremacy

Reference Runtime 拥有**最高优先级**。

| 层级 | 职责 | 优先级 |
|------|------|--------|
| Reference Runtime | 行为规范、Contract、Behavior | 最高 |
| Conformance Suite | 验证 Production Runtime | 高 |
| Production Runtime | 正式实现 | 服从 Reference |

### 11.2 ACP（Architecture Change Proposal）

如果实现过程中发现 Reference Runtime 存在问题：

1. **停止**修改。
2. 输出 ACP，描述不足之处、原因、提议修改、对 Behavior Contract 的影响。
3. 等待批准后，Reference Runtime 先修改，随后所有实现同步修改。

### 11.3 Merge Gate

任何 Production Runtime 实现合并前必须：

1. Golden Tests 通过（`tests/test_reference_*.py`）。
2. Contract Diff 无意外变化。
3. Conformance Suite 100% 通过。
4. Behavior Validation 确认无 Behavior Contract 违规。

详见 `docs/specification/CONFORMANCE_SPEC.md` Section 8。
