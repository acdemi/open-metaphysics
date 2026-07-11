# Implementation Roadmap（Phase 6 ~ Phase 9）

> 状态：设计 v1 (2026-07-11)
> 注意：Phase 6 为纯设计阶段，以下 Phase 7-9 为实现规划，需架构确认后方可启动。

## Phase 6 - 规则层与知识层架构设计（当前阶段）

**性质**：纯设计，禁止编码。
**交付物**：10 项设计文档（本文档集）。

| 子任务 | 状态 |
|--------|------|
| Rule Schema 设计 | ✅ 完成 |
| Knowledge Schema 设计 | ✅ 完成 |
| Relation Schema 设计 | ✅ 完成 |
| Evidence Schema 设计 | ✅ 完成 |
| Pattern Layer 设计 | ✅ 完成 |
| Evidence-Based Consensus 设计 | ✅ 完成 |
| JSON Schema + Pydantic 模型 | ✅ 完成 |
| ER 图 + 流程图 | ✅ 完成 |
| ADR + 风险分析 + 测试计划 | ✅ 完成 |

**完成标准**：架构评审通过，全部 Schema 可通过 `model_json_schema()` 导出。

---

## Phase 7 - 规则层与知识层实现（模型 + 内存存储）

**性质**：代码实现，不引入数据库。

| 子任务 | 说明 |
|--------|------|
| 创建 `src/openmetaphysics/rules/` 包 | schemas.py + rule_engine.py + rule_registry.py |
| 创建 `src/openmetaphysics/knowledge/` 包 | schemas.py + knowledge_store.py（内存实现） |
| 实现 RuleEngine.evaluate() | 消费排盘结构，执行条件匹配 |
| 实现 KnowledgeStore（内存） | 节点/关系查询，find_path |
| 实现 PatternMatcher | 规则 + 知识 -> 格局匹配 |
| 实现 EvidenceBuilder | 组装 Evidence |
| 为八字接入规则评估 | 不修改 BaziAgent.calculate()，追加后处理 |
| 为紫微接入规则评估 | 同上 |
| 单元测试 + 黄金向量 | 规则匹配、知识查询、格局识别 |

**完成标准**：八字 + 紫微智能体可输出 Evidence + PatternMatch，全部测试绿色。

---

## Phase 8 - Evidence-Based Consensus 实现 + RAG 集成

**性质**：代码实现，升级共识智能体。

| 子任务 | 说明 |
|--------|------|
| 重设计 ConsensusAgent | 从 Weighted Average 升级为 Evidence Aggregation |
| 实现 EvidenceConsensusReport | 多结论并存，按 Domain 分组 |
| 实现跨体系 Pattern 检测 | 多 Agent 识别同一 Pattern 时增强置信度 |
| 实现 Conflict 检测 + retain_all | 保留全部证据 |
| RAG 检索器集成 KnowledgeStore | 解释时注入知识节点引用 |
| Explain Agent 集成 | 解释渲染时引用证据和经典出处 |
| 单元测试 + 端到端测试 | 多智能体共识场景 |

**完成标准**：`/orchestrate` 端点返回 EvidenceConsensusReport，离线 + Ollama 均可工作。

---

## Phase 9 - 持久化 + 运维 + 扩展体系

**性质**：引入数据库 + 运维 + 新体系接入。

| 子任务 | 说明 |
|--------|------|
| PostgreSQL 持久化 | 规则、知识节点、关系、格局存储 |
| Neo4j 图数据库（可选） | 知识图谱关系查询优化 |
| Qdrant RAG 知识库导入 | 经典文献向量化检索 |
| Docker Compose 运维 | Postgres + Neo4j + Qdrant + Ollama |
| MCP 工具接口 | 暴露规则/知识查询为 MCP 工具 |
| 梅花易数接入 | 新 BaseAgent 子类 + 规则/知识注册 |
| 大六壬接入 | 新 BaseAgent 子类 + 规则/知识注册 |
| 全部六体系共识测试 | 端到端多体系共识 |

**完成标准**：`docker compose up` + 六体系共识冒烟测试通过。

## 里程碑总览

```
Phase 6 (设计)          Phase 7 (模型实现)       Phase 8 (共识升级)       Phase 9 (持久化+扩展)
┌──────────────┐       ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│ Schema 定义   │  ->    │ Rule+Knowledge│  ->     │ Evidence     │  ->     │ Database     │
│ 架构图       │       │ 内存存储      │        │ Consensus    │        │ Docker       │
│ ADR          │       │ Pattern Match │        │ RAG 集成     │        │ MCP          │
│ 测试计划     │       │ 八字+紫微接入 │        │ 端到端测试   │        │ 梅花+六壬    │
└──────────────┘       └──────────────┘        └──────────────┘        └──────────────┘
   当前阶段              架构确认后               共识升级                持久化+扩展
```
