# OpenMetaphysics — 接口设计

> 层与层之间的契约。下面每个接口都是 Python Protocol/ABC，由 Pydantic 模型实现，并覆盖测试。状态更新 2026-10-24。
> Reference Runtime 接口已实现；Python 生产侧（`src/`）已实现领域 Agent / API / 编排 / RAG / Explain（Phase 0~8），其余语言的通用层仍待实现。

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
| Production: `AgentProtocol.compute()` | `src/openmetaphysics/agents/` | **未实现** |

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

| 层 | Reference Runtime | Production Runtime |
|----|-------------------|--------------------|
| Rule | 完成（Python 内存） | 未实现 |
| Pattern | 完成（Python 内存） | 未实现 |
| Evidence | 完成（Python 内存） | 未实现 |
| Knowledge | 完成（Python 内存） | 未实现 |
| Consensus | 完成（Python 内存） | 未实现 |
| Conformance | 完成（Python 内存） | 未实现 |
| Calendar | 未实现（Reference） | 已实现（`src/core/calendar.py`） |
| API | 未实现（Reference） | 已实现（FastAPI 6 端点，`src/openmetaphysics/api/`） |

> 表中 Rule/Pattern/Evidence/Knowledge/Consensus/Conformance 的「Production 未实现」
> 指 **通用跨语言层**；Python 生产侧已通过各域 Agent 与 Qimen/Consensus 契约适配器
> 覆盖域内等价，通用层的生产化仍以 Reference 为规范。

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

| 方法 | 路径 | 用途 |
|------|------|------|
| GET  | `/health` | 存活 + 已注册 agent 列表 |
| GET  | `/agents` | 列出 agent + engine 版本 |
| GET  | `/agents/{name}/schema` | 输入/输出 JSON Schema |
| POST | `/agents/{name}/compute` | 单域确定性计算（可选解释） |
| POST | `/agents/{name}/explain` | 对**既有**输出做解释（不重算） |
| POST | `/orchestrate` | 多 agent + 共识（可选解释） |

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

每个失败响应都带**一个机器可读** `error` 对象，`kind` 为稳定判别键；FastAPI 既有 `detail` 保留。

| HTTP | `error.kind` | 触发 |
|------|--------------|------|
| 404 | `unknown_agent` | 未知 `{name}`；`/orchestrate` 显式指定的 agent **全部**未知 |
| 422 | `invalid_request` | 请求体/查询/路径校验失败（含 FastAPI 层校验） |
| 500 | `calculation_failed` | 确定性计算抛错（附 `type`、`agent`） |
| 500 | `internal_error` | 未预期异常兜底 |
| 200 | （块内 `explain.error.kind`） | provider 失败：`timeout` / `rate_limit` / `unavailable` / `invalid_response` / `error` |

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

## 8. MCP 扩展点（未来）

mcp/server.py 桩将把智能体 compute/schema 暴露为 MCP 工具，因此外部 MCP 兼容客户端可以调用 OpenMetaphysics。v1 仅发布接口契约；不包含传输层。
