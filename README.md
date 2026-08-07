# OpenMetaphysics 开放形而上学

**完全本地运行、隐私保护、多智能体命理推理框架。**

**核心原则：** **大语言模型永远不参与历法计算、排盘、推演。所有这些输出都来自确定性规则引擎，完全可重复。大语言模型仅用于可选的自然语言解释，并且与计算核心严格隔离。**

## 智能体

- **八字 (Bazi)** - 基于二十四节气分界的八字排盘，支持大运
- **紫微斗数 (Ziwei)** - 紫微斗数十二宫、十四主星定局
- **奇门遁甲 (Qimen)** - 时家奇门排盘
- **六爻 (Liuyao)** - 六爻起卦，确定性纳甲
- **共识 (Consensus)** - Evidence-Based 证据聚合，多结论并存

## 技术栈

Polyglot Monorepo -- 四语言协作：

| 语言 | 职责 | 确定性 |
|------|------|--------|
| **Rust** | 历法计算 · 真太阳时 · 规则引擎 · 格局匹配 | ✅ 确定性 |
| **Go** | API Gateway · 共识服务 · 知识服务 · Worker | ✅ 确定性 |
| **Python** | LLM 解释 · RAG 检索 · LangGraph 编排 · DSL 解析 | ❌ 非确定性 |
| **TypeScript** | Frontend · CLI | - |

详见 `docs/engineering/14_polyglot_architecture.md`。

## 开发环境搭建

### 前置条件

| 工具 | 最低版本 | 安装 |
|------|----------|------|
| Python | 3.11+ | [python.org](https://python.org) |
| uv | 0.5+ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Rust | 1.75+ | [rustup.rs](https://rustup.rs) |
| Go | 1.23+ | [go.dev](https://go.dev/dl/) |
| Docker | 24+ | [docker.com](https://docker.com) |
| make | any | 系统自带（Windows 需额外安装或使用 `task`） |

### 一键启动

```bash
# 1. 克隆仓库
git clone https://github.com/open-metaphysics/open-metaphysics.git
cd open-metaphysics

# 2. 安装全部依赖（Python / Rust / Go / pre-commit hooks）
make bootstrap
# Windows 替代: ./scripts/setup-dev.ps1

# 3. 启动基础设施服务（PostgreSQL+AGE / Qdrant / Valkey）
docker compose up -d

# 4. （可选）启动本地 LLM
docker compose --profile llm up -d

# 5. 运行测试
make test
```

全新开发者从 `git clone` 到 `make test` 全部成功，即验证环境搭建完成。

### 快速启动 API

```bash
# 启动 FastAPI 开发服务器
uvicorn openmetaphysics.api.app:app --reload

# 或通过 uv
uv run uvicorn openmetaphysics.api.app:app --reload
```

核心计算不依赖任何外部服务。PostgreSQL / Qdrant / Valkey / Ollama 都是**可选**的。

## 目录说明

```
open-metaphysics/
├── apps/               # 可部署应用入口（Go Gateway / Worker，Phase 9+）
├── services/           # Go 微服务
│   └── gateway/        # API Gateway（Phase 9+，当前为 placeholder）
├── crates/             # Rust crates（workspace）
│   └── om-calendar/    # 历法计算核心（Phase 7+，当前为 placeholder）
├── packages/           # 跨语言共享包（proto-go / ts-client，Phase 9+）
├── python/             # Python 服务包（Explain Agent / RAG，Phase 9+）
├── frontend/           # TypeScript Frontend（React，Phase 10+）
├── proto/              # Protobuf IDL 定义
│   └── openmetaphysics/v1/  # gRPC 服务接口契约
├── scripts/            # 工具脚本（setup-dev.sh / setup-dev.ps1）
├── tools/              # 开发工具（知识导入 / 规则校验，Phase 7+）
├── docs/               # 全部文档
│   ├── engineering/    # 工程设计文档（Phase 6.5 / 6.6）
│   └── design/phase6/  # 架构设计文档（Phase 6）
├── src/                # Python 源码（openmetaphysics 包）
├── tests/              # Python 测试
├── Cargo.toml          # Rust workspace 根配置
├── go.work             # Go workspace 配置
├── pyproject.toml      # Python 项目配置（uv 兼容）
├── Taskfile.yml        # Task Runner（跨平台，推荐 Windows 使用）
├── Makefile            # GNU Make（Unix/macOS，GitHub Actions）
├── docker-compose.yml  # 基础设施服务编排
├── buf.yaml            # Protobuf lint 配置
├── buf.gen.yaml        # Protobuf 代码生成配置
├── .pre-commit-config.yaml  # 统一 pre-commit hooks
└── .github/workflows/  # CI/CD（lint / build / test）
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `make bootstrap` | 安装全部依赖 |
| `make test` | 运行全部测试（Python + Rust + Go） |
| `make lint` | 运行全部 linter |
| `make fmt` | 格式化全部代码 |
| `make proto` | 从 .proto 生成代码 |
| `make clean` | 清理构建产物 |
| `make docker-up` | 启动基础设施服务 |
| `make docker-down` | 停止基础设施服务 |
| `task <name>` | 跨平台替代（需安装 [Task](https://taskfile.dev)） |

## 文档

| 文档 | 内容 |
|------|------|
| `docs/engineering/01_rule_dsl.md` | Rule DSL 设计（Phase 6.5） |
| `docs/engineering/12_open_source_evaluation.md` | 开源项目评估（Phase 6.6） |
| `docs/engineering/13_component_decision_matrix.md` | 组件决策矩阵（Phase 6.6） |
| `docs/engineering/14_polyglot_architecture.md` | 多语言协作架构（Phase 6.6） |
| `docs/design/phase6/` | Phase 6 架构设计（10 份文档） |
| `docs/ARCHITECTURE.md` | 系统架构概览 + Governance |
| `docs/ROADMAP.md` | 开发路线图（双时间线） |
| `docs/SCHEMAS.md` | Schema 设计 + 跨语言契约 |
| `docs/INTERFACES.md` | 接口设计 + Reference Runtime 接口位置 |
| `docs/PROJECT_STATUS.md` | 项目状态总览 |
| `docs/specification/` | 行为规范 + Contract 治理（7 份文档） |

## License

MIT
