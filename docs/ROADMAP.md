# OpenMetaphysics — 开发路线图

> 分阶段交付。每个阶段都可以独立测试，交付后仓库保持可运行状态。设计 v1 (2026-07-04)。

## Phase 0 — 脚手架
- pyproject.toml (PEP 621, src 布局), uff + pytest, .gitignore。
- src/openmetaphysics/ 下的包骨架，空的 	ests/。
- **完成标准：** python -m pip install -e . 成功，pytest 可以运行（0 测试）。

## Phase 1 — 基础
- core.schemas: 共享模型（§SCHEMAS 2.x）+ JSON Schema 导出。
- core.models: 领域原语（天干地支，八卦，六十四卦，二十四节气，六十甲子）。
- core.calendar: 确定性阴阳历法 + 节气分界（立春年分界，节月分界）。纯函数。
- core.engines: DeterministicEngine ABC + RuleRegistry + TraceRecorder。
- core.config: 类型化配置（Ollama/Qwen/DeepSeek/Qdrant/PG 端点）。
- **完成标准：** 日历/天干单元测试通过 + 黄金重放框架运行。

## Phase 2 — 六爻（完整参考智能体）
- 卦表，纳甲，六亲，六神，世应，用神规则。
- 种子起卦（从 seed 得到六爻）；本/变/互卦。
- LiuyaoAgent + 黄金向量（标准起卦 → 期望图表）。
- **完成标准：** 重放测试绿色；不涉及大语言模型。

## Phase 3 — 八字
- 基于节气分界的四柱引擎（年/月/日/时）。
- 藏干，纳音，十神，大运（性别驱动方向）。
- BaziAgent + 跨越年界（立春）边界情况的黄金向量。
- **完成标准：** 柱子测试绿色，包括立春前后和时区情况。

## Phase 4 — 紫微斗数（骨架 → 部分完成）
- 命局/五行局，十二宫，紫微星排布规则。
- v1: 宫位骨架 + 紫微/天府排布；剩余星分步完成。
- ✅ **完成：** 宫位布局 + 十四主星 紫微定局测试绿色。农历转换 via sxtwl。

## Phase 5 — 奇门遁甲（骨架 → 部分完成）
- 时家奇门: 节气 → 阴/阳遁 → 局(1..9)，天/地盘，八神/九星/八门/三奇。
- v1: 盘骨架 + 宫位/神煞 placement 核心。
- **完成标准：** 遁类型/局数 + 盘结构测试绿色。

## Phase 6 — 共识智能体
- ConsensusAgent: 加权聚合，一致矩阵，冲突检测。
- 确定性综合模板。
- **完成标准：** 多智能体共识测试绿色。

## Phase 7 — 编排 + API
- LangGraph Orchestrator (validate→route→fan_out→consensus→respond)。
- FastAPI app 带所有端点 + OpenAPI。
- **完成标准：** /orchestrate 端到端测试绿色。

## Phase 8 — 推理 + RAG（隔离）
- OllamaProvider（+ 通义千问/DeepSeek 通过相同接口，可选远程）。
- Explainer 带确定性后备；KnowledgeRetriever (Qdrant + 内存)。
- **完成标准：** 离线解释工作（后备），Ollama 存在时也工作。

## Phase 9 — 运维 + 可扩展性
- Docker Compose (Postgres/Qdrant/Ollama) + 会话/追踪持久化。
- mcp/server.py 工具接口桩。
- 文档合并，示例。
- **完成标准：** docker compose up + 冒烟测试通过。

## 当前交付范围

当前迭代完整执行 Phases 0-4，Phase 5 进行中，Consensus + API 作为可运行垂直切片（六爻从 /orchestrate 端到端），八字、紫微斗数核心完成。奇门遁甲以 Schema 完整骨架交付，核心 placement 逻辑，明确标记为 Phase 5 待完成。所有重型服务保持可选；核心完全可以离线测试。

