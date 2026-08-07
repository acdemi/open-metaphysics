# OpenMetaphysics — 接口设计

> 层与层之间的契约。下面每个接口都是 Python Protocol/ABC，由 Pydantic 模型实现，并覆盖测试。Reference Freeze Candidate (2026-07-14)。
> Reference Runtime 接口已实现，Production Runtime 接口待实现。

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
| Calendar | 未实现（Reference） | 部分实现（`src/`） |
| API | 未实现（Reference） | 部分实现（`src/`） |

---

## 1. 智能体契约

每个智能体都实现 AgentProtocol。两个严格分离的接口：
compute()（确定性，无大语言模型）和 xplain()（可选大语言模型，仅文本）。

`python
class AgentProtocol(Protocol):
    name: str
    engine_version: str
    input_schema: type[AgentInput]
    output_schema: type[AgentOutput]

    def compute(self, payload: AgentInput) -> AgentOutput: ...
    def explain(self, output: AgentOutput, style: str = "concise") -> str: ...
    def schema(self) -> dict: ...      # {input_schema, output_schema, engine_version}
`

BaseAgent 提供共享机制，因此具体智能体只需要实现 _compute_result() 和（可选）_explain()：

`python
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
`

这种分离通过测试强制：compute() 不能碰任何 InferenceProvider；xplain() 不能修改 output.result。

## 2. 确定性引擎接口

`python
class DeterministicEngine(ABC):
    version: str

    @abstractmethod
    def calculate(self, payload: AgentInput) -> dict: ...

    # 纯函数保证：无 I/O，无挂钟时间，无无种子随机数。
    # 子类在 RuleRegistry 中注册规则，便于追踪。
`

RuleRegistry 将 
ule_ref 字符串映射到可调用对象；每个规则调用追加一个 ReasoningStep。这使得引擎逻辑可以逐条检查和测试，并自动生成 
easoning_trace。

## 3. 推理提供者接口（隔离）

`python
class InferenceProvider(Protocol):
    name: str                       # "ollama" | "qwen" | "deepseek"
    def generate(self, prompt: str, *, model: str, temperature: float = 0.2,
                 max_tokens: int = 512) -> str: ...
    def embed(self, text: str, *, model: str) -> list[float]: ...

class Explainer(Protocol):
    provider: InferenceProvider | None
    def render(self, output: AgentOutput, *, style: str) -> str: ...
`

保证：
- 解释器仅接收序列化后的 AgentOutput；除了 output 暴露的内容，它对引擎或原始输入没有引用。
- 	emperature 默认较低；结果后验证确保永远不包含与数值字段矛盾的声明（这是检查步骤，不是重新计算）。
- 如果 provider is None，
ender() 返回确定性模板文本，因此系统在完全没有大语言模型时也完全可用。

## 4. RAG 检索器接口

`python
class KnowledgeRetriever(Protocol):
    def retrieve(self, query: str, *, k: int = 5) -> list[KnowledgeChunk]: ...
`

仅被 xplain()/解释用于注入权威引用。它不能改变排盘数字。本地由 Qdrant 支持；内存后备保证测试无依赖。

## 5. 编排接口 (LangGraph)

`python
class Orchestrator:
    graph: CompiledGraph
    def run(self, request: OrchestrationRequest) -> OrchestrationResponse: ...

class OrchestrationRequest(BaseModel):
    request_id: str
    payload: AgentInput
    agents: list[str] | None = None      # None → 路由选择
    strategy: str = "weighted"
    explain: bool = False                # 启用大语言模型文本层
`

图节点：alidate → route → fan_out(agents) → consensus → (explain?) → respond。
状态是 Pydantic 模型；边是确定性的（路由可以咨询大语言模型进行*选择*，由配置控制）。

## 6. API 接口 (FastAPI)

| 方法   | 路径                              | 用途                               |
|--------|-----------------------------------|------------------------------------|
| GET    | /health                         | 存活 + 依赖探针                    |
| GET    | /agents                         | 列出智能体 + 引擎版本              |
| GET    | /agents/{name}/schema           | 输入/输出 JSON Schema              |
| POST   | /agents/{name}/compute          | 单智能体确定性运行                 |
| POST   | /orchestrate                    | 多智能体 + 共识                    |
| POST   | /agents/{name}/explain          | 对之前的输出进行大语言模型解释      |

所有 POST 主体/响应都对照发布的 schema 验证。错误使用 RFC7807 风格 ProblemDetail。

## 7. 注册与发现

`python
class AgentRegistry:
    def register(self, agent: AgentProtocol) -> None: ...
    def get(self, name: str) -> AgentProtocol: ...
    def all(self) -> list[AgentProtocol]: ...
    def schemas(self) -> dict[str, dict]: ...
`

智能体在导入时自我注册；API 和编排器按名称解析。这是唯一扩展点：新的命理方式 = 新的 BaseAgent 子类 + 注册。

## 8. MCP 扩展点（未来）

mcp/server.py 桩将把智能体 compute/schema 暴露为 MCP 工具，因此外部 MCP 兼容客户端可以调用 OpenMetaphysics。v1 仅发布接口契约；不包含传输层。
