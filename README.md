# OpenMetaphysics 开放形而上学

**完全本地运行、隐私保护、多智能体命理推理框架。**

**核心原则：** **大语言模型永远不参与历法计算、排盘、推演。所有这些输出都来自确定性规则引擎，完全可重复。大语言模型仅用于可选的自然语言解释，并且与计算核心严格隔离。**

**Rule First. Knowledge Second. LLM Last.**

---

## 当前实现状态（2026-10-24）

本仓库以 **Python 实现为主**：`src/`（生产代码）+ `reference/`（规范性 Reference Runtime）。
Rust / Go / TypeScript 目录当前为占位骨架，属未来阶段（见 `docs/engineering/14_polyglot_architecture.md`）。

| 组成部分 | 位置 | 状态 |
|----------|------|------|
| Reference Runtime（行为规范） | `reference/` | 完成：Rule/Pattern/Evidence/Knowledge/Consensus/Conformance 全套 |
| 生产代码（确定性引擎 + API） | `src/openmetaphysics/` | Qimen/BaZi/Ziwei/Liuyao/Consensus 智能体 + FastAPI |
| 测试 | `tests/` + `reference/tests/` | **1087 passed + 2 skipped**（2026-10-24；含 Qimen 24/24、BaZi 24/24、Liuyao 21/21 + 40/40 等价） |
| Rust crates | `crates/om-calendar/` | 占位（Phase 7+） |
| Go 服务 | `services/gateway/` | 占位（Phase 9+） |
| Frontend / Python 服务 / Proto | `frontend/` `python/` `proto/` | 占位 / IDL 定义 |

## 智能体（均已实现确定性引擎）

| 智能体 | 状态 | 说明 |
|--------|------|------|
| **奇门遁甲 (Qimen)** | ✅ **Frozen + Certified** | 契约 `qimen:behavior:v1.0.0` + Reference 认证 + 24 向量双实现验证 |
| **八字 (Bazi)** | ✅ **Integration Ready** | 契约 `bazi:behavior:v1.0.0` Frozen + Reference 独立实现 + 24/24 等价 |
| **紫微斗数 (Ziwei)** | ✅ **Integration Ready** | 契约 `ziwei:behavior:v1.0.0` Frozen + Reference Certified（24/24）；辅星/四化/大限属 ZW-017 边界 |
| **六爻 (Liuyao)** | ✅ **Integration Ready** | 契约 `liuyao:behavior:v1.0.0` Frozen + 25 Frozen 向量 + Reference Certified（21/21 + 40/40） |
| **共识 (Consensus)** | Reference 完成 | Evidence 聚合，多结论并存（`reference/consensus*.py`） |

> 能力状态登记与生命周期：`docs/governance/CAPABILITY_STATUS.md`。
> 生命周期标准：`docs/governance/CAPABILITY_LIFECYCLE.md`。

## 代码结构

```
open-metaphysics/
├── src/openmetaphysics/     # 生产代码（Python）
│   ├── agents/              # 智能体：bazi / qimen / liuyao / ziwei / consensus + explainer
│   ├── core/                # calendar（农历/节气/干支）、solar_time（真太阳时）、
│   │                        # engines（BaseAgent）、models、schemas、config
│   ├── domain/qimen/        # Qimen 域建模（types / abi / adapter / structural）
│   ├── contracts/           # qimen_contract.py + JSON Schema
│   ├── api/                 # FastAPI（health/agents/schema/compute/explain/orchestrate/knowledge/sessions/traces/consensus）+ CLI
│   ├── inference/           # LLM 解释层（与计算核心严格隔离）
│   ├── orchestration/       # LangGraph 编排
│   ├── rag/                 # 检索器（Qdrant 可选，内存后备）
│   └── mcp/                 # MCP stdio server（JSON-RPC，无外部 SDK）
├── reference/               # 规范性 Reference Runtime（行为规范，权威）
│   ├── engine.py / parser.py / patterns.py / pattern_matcher.py
│   ├── evidence*.py / knowledge*.py / consensus*.py / conformance*.py
│   ├── qimen/               # Qimen 域 Reference 实现（domain + astronomy + concepts）
│   ├── bazi/                # BaZi 域 Reference 独立实现（domain + astronomy + tables）
│   ├── contracts/           # 自动生成契约 JSON（v1.0.0）
│   ├── conformance/golden/  # 自动生成 Golden Vectors
│   ├── examples/            # 示例数据（YAML）
│   └── tests/               # Reference 独立测试套件
├── tests/                   # 生产测试（1089 collected / 1087 passed + 2 skipped）
├── docs/                    # 文档（见下节）
├── context/                 # 对话归档与项目状态
├── crates/om-calendar/      # Rust 占位（Phase 7+）
├── services/gateway/        # Go 占位（Phase 9+）
└── proto/                   # Protobuf IDL（规划）
```

## 开发环境搭建

| 工具 | 版本 | 说明 |
|------|------|------|
| Python | 3.11（`.python-version` 固定） | sxtwl 2.0.7 仅提供 3.11 的 Windows wheel |
| uv | 0.5+ | 包管理（`uv.lock` 锁定） |

```bash
# 1. 安装依赖（自动创建 .venv）
uv sync

# 2. 运行全部测试（1087 passed + 2 skipped，2026-10-24）
uv run pytest -q

# 3. 启动 API（FastAPI, http://127.0.0.1:8000）
uv run openmetaphysics
#   或: uv run uvicorn openmetaphysics.api.app:app --reload
```

**可选环境变量**：

| 变量 | 用途 |
|------|------|
| `OM_ENABLE_EXPLAINER` | 启用 LLM 解释（默认关闭；离线确定性后备） |
| `OM_INFERENCE_PROVIDER` | `ollama` / `qwen` / `deepseek` |
| `OM_RAG_ENABLED` / `OM_QDRANT_URL` | 启用 Qdrant 检索（默认 InMemory） |
| `OM_POSTGRES_DSN` | 会话/追踪持久化（缺省回退内存） |
| `OM_CORS_ORIGINS` | 允许跨域来源（逗号分隔；默认关闭） |

**无外部依赖**：计算核心不依赖任何数据库 / 向量库 / LLM 服务，可完全离线运行。
`docker-compose.yml` 提供 PostgreSQL / Qdrant / Valkey / Ollama 等可选服务；
`--profile app` 可构建并启动 API（含 Postgres 会话/追踪持久化）。
Valkey 当前为**预留**（无消费者）；Dockerfile 已本地构建验证，容器 `/health` 冒烟通过。

### 快速体验

```bash
# Reference Runtime 演示：DSL → Rule → Evaluate → JSON
uv run python -m reference.demo

# API 示例（排八字）
curl -X POST http://127.0.0.1:8000/agents/bazi/compute -H "Content-Type: application/json" -d '{"request_id":"demo","born_at":"1990-06-15T08:30:00+08:00","gender":"male"}'

# 离线 CLI（无需启动服务器）
uv run openmetaphysics-cli agents
uv run openmetaphysics-cli compute bazi --input '{"request_id":"demo","born_at":"1990-06-15T08:30:00+08:00","gender":"male"}'
uv run openmetaphysics-cli compute bazi --input '{"request_id":"demo","born_at":"1990-06-15T08:30:00+08:00","gender":"male"}' --explain
uv run openmetaphysics-cli knowledge --query 紫微 --k 3
uv run openmetaphysics-cli knowledge --query 帝座 --include-evidence
uv run openmetaphysics-cli consensus --input '{"evidence":[]}'

# MCP over HTTP（与 stdio 相同的工具面）
curl -X POST http://127.0.0.1:8000/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `uv sync` | 安装依赖 |
| `uv run pytest -q` | 全量测试（1087 passed + 2 skipped，2026-10-24） |
| `uv run ruff check src/ tests/ reference/` | lint |
| `uv run ruff format --check src/ tests/ reference/` | 格式检查 |
| `uv run openmetaphysics` | 启动 API |
| `uv run python -m reference.demo` | Reference 演示 |
| `uv run openmetaphysics-mcp` | MCP stdio server（JSON-RPC） |
| `uv run openmetaphysics-cli compute bazi --input '{...}'` | 离线计算（`--explain` 附解释链） |
| `make test` / `make lint` | 兼容入口（Rust/Go 部分为占位） |

## 规范与治理

| 文档 | 内容 |
|------|------|
| `AGENTS.md` | 长期规则（H1~H8 硬规则 + E1~E7 效率规则） |
| `docs/specification/` | 行为规范：BEHAVIOR_SPEC（35 条）/ KNOWLEDGE（20 条）/ CONSENSUS（25 条）/ CONFORMANCE（20 条）+ Contract 治理 |
| `docs/governance/` | 能力生命周期 + 状态登记（CAPABILITY_STATUS）+ 各域审计工件 |
| `docs/ARCHITECTURE.md` | 系统架构概览 |
| `docs/SCHEMAS.md` | Schema 设计 + 跨语言契约 |
| `docs/INTERFACES.md` | 接口设计 |
| `docs/ROADMAP.md` | 开发路线图 |
| `docs/PROJECT_STATUS.md` | 项目状态总览 |
| `docs/design/phase6/` | Phase 6 架构冻结（不可修改） |
| `docs/engineering/` | 工程冻结 + 技术选型（12/13/14 多语言架构） |
| `reference/contracts/` | 自动生成契约 JSON（v1.0.0） |
| `reference/conformance/golden/` | 自动生成 Golden Vectors |

## 领域文档（冻结工件）

| 域 | 文档 |
|----|------|
| Qimen | `docs/qimen/`（契约、认证、向量、Freeze 记录） |
| BaZi | `docs/bazi/`（契约 v1.0.0、认证、黄金向量、集成就绪审查） |
| Ziwei | `docs/governance/ziwei/`（规则清单、算法假设、审计、决策解析） |
| Liuyao | `docs/liuyao/`（契约 v1.0.0、Freeze Review、认证、25 向量、集成就绪审查） |

## License

MIT
