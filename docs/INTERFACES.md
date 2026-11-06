# OpenMetaphysics — 接口设计

> 层与层之间的契约。本文同时描述 Python Protocol/ABC 契约、HTTP API 与 MCP 传输接口；各节分别标注状态。状态更新 2026-10-24。
> Reference Runtime 接口已实现；Python 生产侧（`src/`）已实现领域 Agent / API / 编排 / RAG / Explain / MCP / 持久化（Phase 0~9 的 Python 路径），其余语言的通用层仍待实现。

## 0. Reference Runtime 接口位置

Reference Runtime（`reference/`）已实现以下接口。这些接口是**行为规范**，
Production Runtime 必须实现等价接口并通过 Conformance Suite 验证。

### 0.1 Rule 层

| 接口 | 文件 | 状态 |
|------|------|------|
| `parse_rule_file(path) -> list[Rule]` | `reference/parser.py` | Reference 完成 |
| `parse_rule_document(yaml) -> list[Rule]` | `reference/parser.py` | Reference 完成 |
| `RuleEngine.evaluate_all(rules, chart) -> list[RuleEvaluation]` | `reference/engine.py` | Reference 完成 |
| `RuleEvaluation` (model) | `reference/models.py` | Reference 完成 |
| Production: `AgentProtocol.compute()` | `src/openmetaphysics/agents/` | **Python 生产侧已实现**；通用跨语言层见 §0.7 注 |

### 0.2 Pattern 层

| 接口 | 文件 | 状态 |
|------|------|------|
| `parse_pattern_file(path) -> Pattern` | `reference/patterns.py` | Reference 完成 |
| `PatternMatcher.match(pattern, evals, system) -> PatternMatch \| None` | `reference/pattern_matcher.py` | Reference 完成 |
| `PatternMatcher.match_cross_system(pattern, evals_by_system) -> PatternMatch \| None` | `reference/pattern_matcher.py` | Reference 完成 |
| `PatternMatch` (model) | `reference/patterns.py` | Reference 完成 |
| Production: Pattern Service | `services/` (Go) | **未实现** |

### 0.3 Evidence 层

| 接口 | 文件 | 状态 |
|------|------|------|
| `EvidenceBuilder.build_all(evals, matches, system) -> list[Evidence]` | `reference/evidence_builder.py` | Reference 完成 |
| `Evidence`, `EvidenceItem` (models) | `reference/evidence.py` | Reference 完成 |
| Production: Evidence Service | `services/` (Go) | **未实现** |

### 0.4 Knowledge 层

| 接口 | 文件 | 状态 |
|------|------|------|
| `KnowledgeStore.execute(query) -> KnowledgeResult` | `reference/knowledge_query.py` | Reference 完成 |
| `load_knowledge_store(nodes, relations, references) -> KnowledgeStore` | `reference/knowledge_query.py` | Reference 完成 |
| `KnowledgeNode`, `KnowledgeRelation`, `KnowledgeReference` (models) | `reference/knowledge.py` | Reference 完成 |
| Production: Knowledge Service (Apache AGE) | `services/` (Go) | **未实现** |

### 0.5 Consensus 层

| 接口 | 文件 | 状态 |
|------|------|------|
| `ConsensusBuilder.build(input) -> ConsensusReport` | `reference/consensus_builder.py` | Reference 完成 |
| `ConsensusConfig`, `ConsensusInput`, `ConsensusReport` (models) | `reference/consensus.py` | Reference 完成 |
| Production: Consensus Service | `services/` (Go) | **未实现** |

### 0.6 Conformance 层

| 接口 | 文件 | 状态 |
|------|------|------|
| `RuntimeAdapter` (Protocol) | `reference/conformance.py` | Reference 完成 |
| `ConformanceRunner.run(adapter, name, version) -> ConformanceResult` | `reference/conformance_runner.py` | Reference 完成 |
| `certify(result) -> ConformanceManifest` | `reference/conformance_runner.py` | Reference 完成 |
| Production: Conformance Runner | 各语言适配器 | **未实现** |

### 0.7 已实现 vs 待实现总览

| 层 | Reference Runtime | Production Runtime（通用跨语言服务） |
|----|-------------------|--------------------------------------|
| Rule | 完成（Python 内存） | 未实现 |
| Pattern | 完成（Python 内存） | 未实现 |
| Evidence | 完成（Python 内存） | 未实现 |
| Knowledge | 完成（Python 内存） | 未实现 |
| Consensus | 完成（Python 内存） | 未实现 |
| Conformance | 完成（Python 内存） | 未实现 |
| Calendar | 未实现（Reference） | 已实现（`src/openmetaphysics/core/calendar.py`） |
| API | 未实现（Reference） | 已实现（FastAPI，路由清单见 §6） |

> 表中 Rule/Pattern/Evidence/Knowledge/Consensus/Conformance 的“Production 未实现”
> 仅指 **Rust / Go / WASM 通用跨语言服务**；Python 生产侧已通过各域 Agent、
> `openmetaphysics.consensus` Evidence 引擎与 Qimen/Consensus 契约适配器覆盖域内实现。
> 不得将本表读成“Python 生产侧未实现”。

---

## 1. 智能体契约

每个智能体都实现 AgentProtocol。两个严格分离的接口：
compute()（确定性，无大语言模型）和 explain()（可选大语言模型，仅文本）。

```python
class AgentProtocol(Protocol):
    name: str
    engine_version: str
    input_schema: type[AgentInput]
    output_schema: type[AgentOutput]

    def compute(self, payload: AgentInput) -> AgentOutput: ...
    def explain(self, output: AgentOutput, style: str = "concise") -> str: ...
    def schema(self) -> dict: ...      # {input_schema, output_schema, engine_version}
```

BaseAgent 提供共享机制，因此具体智能体只需要实现 _compute_result() 和（可选）_explain()：

```python
class BaseAgent(ABC):
    name: str
    engine_version: str
    input_schema: type[AgentInput]
    output_schema: type[AgentOutput]
    engine: DeterministicEngine
    explainer: Explainer | None = None

    def compute(self, payload) -> AgentOutput:
        self._validate(payload)
        trace = TraceRecorder()
        result = self._compute_result(payload, trace)
        confidence = self._confidence(result, trace)
        return AgentOutput(
            request_id=payload.request_id,
            agent=self.name,
            engine_version=self.engine_version,
            input_hash=hash_input(payload),
            computed_at=now_utc(),
            confidence=confidence,
            reasoning_trace=trace.steps,
            metadata=self._metadata(),
            result=result,
        )

    @abstractmethod
    def _compute_result(self, payload, trace) -> dict: ...

    def explain(self, output, style="concise") -> str:
        if self.explainer is None:
            return self._fallback_explain(output)   # 确定性模板文本
        return self.explainer.render(output, style=style)
```

这种分离通过测试强制：compute() 不能碰任何 InferenceProvider；explain() 不能修改 output.result。

## 2. 确定性引擎接口

```python
class DeterministicEngine(ABC):
    version: str

    @abstractmethod
    def calculate(self, payload: AgentInput) -> dict: ...

    # 纯函数保证：无 I/O，无挂钟时间，无无种子随机数。
    # 子类在 RuleRegistry 中注册规则，便于追踪。
```

RuleRegistry 将
rule_ref 字符串映射到可调用对象；每个规则调用追加一个 ReasoningStep。这使得引擎逻辑可以逐条检查和测试，并自动生成
reasoning_trace。

## 3. 推理提供者接口（隔离）

```python
class InferenceProvider(Protocol):
    name: str                       # "ollama" | "qwen" | "deepseek"
    def generate(self, prompt: str, *, model: str, temperature: float = 0.2,
                 max_tokens: int = 512) -> str: ...
    def embed(self, text: str, *, model: str) -> list[float]: ...

class Explainer(Protocol):
    provider: InferenceProvider | None
    def render(self, output: AgentOutput, *, style: str) -> str: ...
```

保证：
- 解释器仅接收序列化后的 AgentOutput；除了 output 暴露的内容，它对引擎或原始输入没有引用。
- temperature 默认较低；结果后验证确保永远不包含与数值字段矛盾的声明（这是检查步骤，不是重新计算）。
- 如果 provider is None，
render() 返回确定性模板文本，因此系统在完全没有大语言模型时也完全可用。

## 4. RAG 检索器接口

```python
class KnowledgeRetriever(Protocol):
    def retrieve(self, query: str, *, k: int = 5) -> list[KnowledgeChunk]: ...
```

仅被 explain()/解释用于注入权威引用。它不能改变排盘数字。本地由 Qdrant 支持；内存后备保证测试无依赖。

## 5. 编排接口 (LangGraph)

```python
class Orchestrator:
    graph: CompiledGraph
    def run(self, request: OrchestrationRequest) -> OrchestrationResponse: ...

class OrchestrationRequest(BaseModel):
    request_id: str
    payload: AgentInput
    agents: list[str] | None = None      # None → 路由选择
    strategy: str = "weighted"
    explain: bool = False                # 启用大语言模型文本层
```

图节点：validate → route → fan_out(agents) → consensus → (explain?) → respond。
状态是 Pydantic 模型；边是确定性的（路由可以咨询大语言模型进行*选择*，由配置控制）。

## 6. API 接口 (FastAPI)

> Productization P1 已按实现校订本节（旧文曾称错误用 RFC7807 ProblemDetail —— 与实际不符）。

### 6.1 路由

以下为 `src/openmetaphysics/api/app.py` 中由 `@app` 显式注册的 HTTP 路由；
按用途分为服务/发现、单域计算、知识与共识、MCP 协议与会话追踪。
FastAPI 自动提供的 `/docs`、`/redoc`、`/openapi.json` 未列入本表。

| 方法 | 路径 | 用途 |
|------|------|------|
| GET  | `/` | 服务名称、版本、文档与健康入口 |
| GET  | `/health` | 存活 + 已注册 agent 列表 |
| GET  | `/agents` | 列出 agent + engine 版本 |
| GET  | `/agents/{name}/schema` | 输入/输出 JSON Schema |
| POST | `/agents/{name}/compute` | 单域确定性计算（可选解释） |
| POST | `/agents/{name}/explain` | 对**既有**输出做解释（不重算） |
| GET  | `/knowledge/corpora` | 已加载语料的状态、版本与计数 |
| POST | `/knowledge/search` | 冻结语料检索（可选 relation/reference evidence） |
| POST | `/mcp` | MCP JSON-RPC over HTTP（与 stdio 共用处理器） |
| GET  | `/consensus/schema` | Evidence Consensus 输入/输出 Schema |
| POST | `/consensus/evidence` | Evidence[] + config → ConsensusReport |
| POST | `/orchestrate` | 多 agent + 共识（可选解释） |
| GET  | `/sessions` | 列出持久化会话（可选分页） |
| GET  | `/sessions/{request_id}` | 读取单个会话 |
| GET  | `/traces/{request_id}` | 读取单个会话的推理追踪 |

#### API 保护与分页（P2.2，默认关闭）

- **鉴权（opt-in）**：未设置 `OM_API_KEY` 时完全不鉴权，行为与旧版本一致；设置后
  `/sessions*`、`/traces/*`、`/orchestrate`、`/agents/{name}/compute|explain`
  需要 `Authorization: Bearer <key>` 或 `X-API-Key: <key>`（缺失 401、错误 403）。
- **限流**：仅在设置 `OM_API_KEY` 后生效，按 key/IP 计数；默认
  `OM_RATE_LIMIT_PER_MINUTE=60`（`0`=关闭），超限返回 429 + `Retry-After`。
  实现是**进程内内存滑动窗口**：多 worker/多副本**不共享**计数，不是分布式限流。
- **分页**：`GET /sessions?limit=50&offset=0`（`limit` 1–200，默认 50；`offset` ≥0）
  返回 `{sessions,total,limit,offset}`；**不带 limit/offset 时保留旧信封**
  `{sessions}`，旧客户端不受影响。列表只含 `request_id` / `created_at`，不含出生信息。
- **出生信息**：`GET /sessions/{id}` 默认保留 `born_at` / `born_location`（兼容）；
  `OM_SESSION_REDACT_BIRTH=true` 时从会话/追踪响应中递归移除这两个字段。出生信息属
  **敏感数据**：公网部署应先启用 `OM_API_KEY`，再按需决定是否暴露。

`{name} ∈ {bazi, ziwei, qimen, liuyao}`。**四个域的接口形状一致**（见 6.2）。

### 6.2 请求

统一信封 `AgentInput`：

| 字段 | 必填 | 说明 |
|------|------|------|
| `request_id` | 是 | 回显于响应 |
| `born_at` | 是 | **必须时区感知**（naive → 422） |
| `gender` / `born_location` / `question` / `locale` / `seed` / `client_nonce` | 否 | 域内可选；`question` 会进入解释链路 |

域专属附加：`liuyao` 可传 `casts`（恰好 6 个，取值 ∈ {6,7,8,9}；缺省则由 `seed` 确定性起卦）。

`compute` 查询参数：`explain`（bool，默认 `false`）、`style`（默认 `concise`）、`k`（检索条数，默认 3）。
`explain`/`k` 非法值 → 422。

### 6.3 响应

`compute` 返回 `AgentOutput` 信封：`request_id`、`agent`、`engine_version`、`input_hash`、
`computed_at`、`confidence`、`reasoning_trace`、`metadata`、`result`。

- `result` 是**确定性事实**，与 `explain` 是否开启无关。
- `computed_at` 是**信封字段**（墙钟），不属于事实层；事实、共识与解释均不依赖它。
- `metadata` 携带 `question`（若提供），供解释链路使用。
- `confidence` 当前是**声明式基线**（`value=0.95`, `method="placeholder_baseline"`,
  `factors["calibrated"]=0.0`）：**不是统计概率，也不是规则覆盖率**。API 与 Consensus
  保留该字段/数值以维持兼容；不得在 UI/解释中把它展示为可信度百分比。未来若引入
  校准评分，会同时修改 method 与数值，并重算 Consensus 权重。

`?explain=true` 追加一个块（四个域形状相同）：

```json
"explain": {
  "explanation": "…自然语言解释…",
  "provider": null,            // 离线时为 null
  "degraded": true,            // 无 provider 或 provider 失败
  "knowledge": [{"id": "kn:…", "source": "…"}],
  "evidence": { "result": …, "input_hash": …, "reasoning_trace": …, "metadata": … },
  "error": null                // provider 失败时为 {kind,type,message,provider}
}
```

`/agents/{name}/explain` 返回同一组字段（外加 `agent`），**不重算**。
`/orchestrate` 返回 `outputs[]`、`consensus`、`explanation`（`{agent: 文本}`）与
`explanation_detail`（`{agent: 上述块}`）。

### 6.4 错误模型

本节所列 FastAPI 业务路由的失败响应（404/422/500）带**一个机器可读** `error` 对象，`kind` 为稳定判别键；FastAPI 既有 `detail` 保留。MCP 协议错误体（§8.2）与框架级 405 等不使用该 `error` 包装。

| HTTP | `error.kind` | 触发 |
|------|--------------|------|
| 404 | `unknown_agent` | 未知 `{name}`；`/orchestrate` 显式指定的 agent **全部**未知 |
| 404 | `not_found` | `GET /sessions/{request_id}` 或 `GET /traces/{request_id}` 目标不存在 |
| 422 | `invalid_request` | 请求体/查询/路径校验失败（含 FastAPI 层校验） |
| 401 | （`detail`，无 `error` 包装） | 仅启用 `OM_API_KEY` 时：受保护路由缺少 API key；响应带 `WWW-Authenticate: Bearer` |
| 403 | （`detail`，无 `error` 包装） | 仅启用 `OM_API_KEY` 时：API key 错误 |
| 429 | （`detail`，无 `error` 包装） | 仅启用 `OM_API_KEY` 时：超过限流阈值；响应带 `Retry-After`（秒） |
| 500 | `calculation_failed` | 确定性计算抛错（附 `type`、`agent`） |
| 500 | `consensus_failed` | `POST /consensus/evidence` 构建共识失败（附 `type`） |
| 500 | `internal_error` | 未预期异常兜底 |
| 200 | （块内 `explain.error.kind`） | provider 失败：`timeout` / `rate_limit` / `unavailable` / `invalid_response` / `error` |
| 200 | `explain_failed`（解释结果内） | `/agents/{name}/explain` 顶层或 compute 的 `explain` 块内；解释器链内部异常兜底，不是 HTTP 错误 |

**关键语义**：provider / 解释失败**不是** HTTP 错误 —— 仍返回 200，确定性 `result` 完好，
失败记录在 `explain.error`，因此 provider 错误不会冒充计算错误。
`/orchestrate` 中部分 agent 未知时保持批处理语义（200，逐 agent 记入 `errors`）。

### 6.5 Provider 行为

默认离线（`enable_explainer=false`）：`provider=null`、`degraded=true`、`error=null`，解释为
确定性渲染 + 知识引文。仅在显式配置（`OM_*` 环境变量）后启用真实 provider；密钥不落代码/仓库。


## 7. 注册与发现

```python
class AgentRegistry:
    def register(self, agent: AgentProtocol) -> None: ...
    def get(self, name: str) -> AgentProtocol: ...
    def all(self) -> list[AgentProtocol]: ...
    def schemas(self) -> dict[str, dict]: ...
```

智能体在导入时自我注册；API 和编排器按名称解析。这是唯一扩展点：新的命理方式 = 新的 BaseAgent 子类 + 注册。

## 8. MCP 传输接口（已实现）

MCP 是**协议接口**，不是 REST 业务路由的替代物；其传输层与 HTTP API 共享同一组工具处理器。

### 8.1 stdio

`src/openmetaphysics/mcp/server.py` 实现依赖零外部 MCP SDK 的 JSON-RPC 2.0
newline-delimited stdio server，入口为 `openmetaphysics-mcp` 或
`python -m openmetaphysics.mcp`。支持 `initialize`、`tools/list`、`tools/call`、
`ping` 与 notifications。

当前工具面：`list_agents`、`agent_schema`、`compute`、`orchestrate`、`explain`、
`consensus_evidence`、`knowledge_search`、`knowledge_stats`。

### 8.2 HTTP

FastAPI 的 `POST /mcp` 将同一 JSON-RPC 消息交给 `handle_message()`：

- 普通 JSON-RPC 请求 → 200 + JSON-RPC 响应；
- notification → 202，响应体为 JSON `null`（不返回 JSON-RPC 响应对象）；
- 非 JSON object 请求体 → 400 + 顶层 `kind=invalid_request`；该 MCP 协议错误体没有 `error` 包装对象。

stdio 与 HTTP 只是传输方式不同，工具语义一致；不要把 `/mcp` 当作独立业务 REST 端点。
