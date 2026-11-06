/* 后端契约类型。
 *
 * 静态形状优先来自 OpenAPI 生成类型（`./generated.ts`，由
 * `npm run gen:api` 从 `frontend/openapi.json` 生成，后者由
 * `uv run python scripts/export_openapi.py` 从 FastAPI app 导出）。
 * 生成命令与更新方式见 `frontend/README.md`。
 *
 * 仍然手写的部分（以及原因）：
 *   - 四个域的 `result` 图表：OpenAPI 中 `AgentOutput.result` 只是 free-form
 *     object（各域 Output 模型未注册为 response），生成类型无法表达。
 *   - `explanation_detail`：OpenAPI 中为 `dict[str, dict[str, Any]]`，没有逐字段契约。
 *   - 错误响应体：路由直接返回 `JSONResponse`，未纳入 OpenAPI response model。
 *
 * 运行时校验在 `parse.ts`：这里只是静态形状，不能假设响应一定符合。
 */

import type { components } from './generated'

export type Schemas = components['schemas']

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue }

/* ------------------------------------------------------- 生成类型（OpenAPI） */
export type Gender = Schemas['Gender']
export type GeoPoint = Schemas['GeoPoint']
/* The OpenAPI document now publishes the shared orchestration envelope as
 * `OrchestrationPayload` (the `AgentInput` fields plus optional per-agent
 * domain fields), so the alias points there; `AgentInput` alone is no longer a
 * component because no request body references it anymore. */
export type AgentInput = Schemas['OrchestrationPayload']
export type OrchestrationRequest = Schemas['OrchestrationRequest']
export type ConfidenceScore = Schemas['ConfidenceScore']
export type HealthResponse = Schemas['HealthResponse']
export type AgentsResponse = Schemas['AgentsResponse']
export type AgentInfo = Schemas['AgentInfo']

/* ------------------------------------------------- 知识检索（OpenAPI 已描述，7A） */
export type KnowledgeCorpusInfo = Schemas['KnowledgeCorpusInfo']
export type KnowledgeCorporaResponse = Schemas['KnowledgeCorporaResponse']
export type KnowledgeSearchChunk = Schemas['KnowledgeSearchChunk']
export type KnowledgeSearchResponse = Schemas['KnowledgeSearchResponse']

/* ------------------------------------------- 领域 Agent 独立计算（OpenAPI 已描述，8A） */
export type AgentSchemaResponse = Schemas['AgentSchemaResponse']
export type AgentComputeResponse = Schemas['AgentComputeResponse']

export const AGENT_NAMES = ['bazi', 'ziwei', 'qimen', 'liuyao'] as const

export type AgentName = (typeof AGENT_NAMES)[number]

/* --------------------------------------------------------- 信封（生成类型） */
export type TraceScalar = string | number | boolean

/** Pydantic 把 `inputs`/`outputs` 标成可选（有默认值），实际总有值；解析后必填。 */
export type ReasoningStep = Required<Schemas['ReasoningStep']>

export type OutputMetadata = NonNullable<Schemas['AgentOutput']['metadata']>

/** 生成类型把有默认值的字段标为可选；`/orchestrate` 实际总是返回它们。 */
export type AgentOutputEnvelope = Omit<Required<Schemas['AgentOutput']>, 'reasoning_trace'> & {
  reasoning_trace: ReasoningStep[]
}

/* ------------------------------------------------------------- 八字 / Bazi */
export type PillarPosition = 'year' | 'month' | 'day' | 'hour'

export interface BaziPillar {
  position: PillarPosition
  stem: string
  branch: string
  stem_index: number
  branch_index: number
  hidden_stems: string[]
  nayin: string
  ten_god: string
}

export interface BaziDaYun {
  index: number
  start_age: number
  end_age: number
  stem: string
  branch: string
  stem_index: number
  branch_index: number
  start_at: string
}

/** agents/bazi.py::BaziChart（OpenAPI 中 result 为 free-form，故手写） */
export interface BaziChart {
  day_master: string
  day_master_element: string
  pillars: BaziPillar[]
  dayun: BaziDaYun[]
  ten_gods_map: Record<string, string>
  year_boundary: string
  month_boundary: string
  gender_assumed: boolean
}

/* ------------------------------------------------------------ 紫微 / Ziwei */
export interface ZiweiPalace {
  index: number
  name: string
  earthly_branch: string
  heavenly_stem: string
  main_stars: string[]
  auxiliary_stars: string[]
  is_fate_palace: boolean
  is_body_palace: boolean
}

/** agents/ziwei.py::ZiweiChart（OpenAPI 中 result 为 free-form，故手写） */
export interface ZiweiChart {
  fate_palace_index: number
  body_palace_index: number
  yin_yang: string
  wuxing_ju: string
  palaces: ZiweiPalace[]
  calendar_note: string | null
}

/* ------------------------------------------------------------ 奇门 / Qimen */
export interface QimenCell {
  palace: number
  name: string
  sky_plate: string | null
  earth_plate: string | null
  eight_gods: string | null
  nine_stars: string | null
  eight_doors: string | null
  three_qi: string | null
  is_void: boolean
  is_central: boolean
}

/** agents/qimen.py::QimenBoard（OpenAPI 中 result 为 free-form，故手写） */
export interface QimenBoard {
  solar_term: string | null
  ju: number
  dun_type: string
  day_of_month: number
  triple_offset: number
  cells: QimenCell[]
}

/* ------------------------------------------------------------ 六爻 / Liuyao */
export interface YaoLine {
  position: number
  is_yin: boolean
  is_changing: boolean
  /** 6 老阴 / 7 少阳 / 8 少阴 / 9 老阳 */
  cast_value: number
}

/** agents/liuyao.py::LiuyaoChart（OpenAPI 中 result 为 free-form，故手写） */
export interface LiuyaoChart {
  original: YaoLine[]
  changed: YaoLine[]
  mutual: YaoLine[]
  original_hexagram: number
  changed_hexagram: number | null
  mutual_hexagram: number | null
  najia: string[]
  liu_qin: string[]
  liu_shen: string[]
  shi_position: number
  ying_position: number
  palace: string
  palace_element: string
  yong_shen: string | null
}

/* --------------------------------------------------------- 领域输出联合体 */
export type BaziOutput = Omit<AgentOutputEnvelope, 'agent' | 'result'> & {
  agent: 'bazi'
  result: BaziChart
}

export type ZiweiOutput = Omit<AgentOutputEnvelope, 'agent' | 'result'> & {
  agent: 'ziwei'
  result: ZiweiChart
}

export type QimenOutput = Omit<AgentOutputEnvelope, 'agent' | 'result'> & {
  agent: 'qimen'
  result: QimenBoard
}

export type LiuyaoOutput = Omit<AgentOutputEnvelope, 'agent' | 'result'> & {
  agent: 'liuyao'
  result: LiuyaoChart
}

/** 未知域（后端注册了但前端暂无专用渲染器）——保留原始 result。 */
export type GenericOutput = Omit<AgentOutputEnvelope, 'agent' | 'result'> & {
  agent: string
  result: unknown
}

export type DomainOutput = BaziOutput | ZiweiOutput | QimenOutput | LiuyaoOutput
export type AnyOutput = DomainOutput | GenericOutput

/* ----------------------------------------------------------- 解释与共识 */
export interface KnowledgeChunk {
  id: string
  source: string
  /** /orchestrate 的 explanation_detail 带原文；部分单域接口会剥离。 */
  text?: string
}

export interface ExplainEvidence {
  agent?: string
  engine_version?: string
  input_hash?: string
  confidence?: ConfidenceScore
  result?: unknown
  reasoning_trace?: ReasoningStep[]
  metadata?: OutputMetadata
}

export interface ExplainErrorInfo {
  kind: string
  type?: string
  message?: string
  provider?: string | null
}

/** 后端 explain 块的统一形状；OpenAPI 中该块是 `dict[str, Any]`，故手写。 */
export interface ExplainDetail {
  explanation: string
  provider: string | null
  degraded: boolean
  knowledge: KnowledgeChunk[]
  evidence: ExplainEvidence
  error: ExplainErrorInfo | null
}

/**
 * `POST /agents/{name}/explain`：与 orchestration 的 `explanation_detail[agent]` 同一 explain 块，
 * 多一个 `agent` 字段。注意：单域 explain 的 `knowledge` 后端只投影 `{id, source}`（无 text），
 * 前端不得补造原文；orchestration 的 `explanation_detail` 才带 text。
 */
export interface AgentExplainResponse extends ExplainDetail {
  agent: string
}

/* 共识结果直接使用生成类型（ConsensusOutput / ConsensusReport / AgentContribution / Conflict）。 */
export type ConsensusContribution = Schemas['AgentContribution']
export type ConsensusConflict = Schemas['Conflict']

/** 后端 ConsensusAgent 的 metadata 是自由标量字典（含 strategy / agent_count）。 */
export type ConsensusMetadata = Record<string, TraceScalar>

/** ConsensusReport 的 `recommendation` 在 OpenAPI 中有默认值（可选），实际总是返回。 */
export type ConsensusResult = Required<Schemas['ConsensusReport']>

/** agents/consensus.py::ConsensusOutput；confidence 是 float，不是 ConfidenceScore。 */
export type ConsensusOutput = Omit<
  Required<Schemas['ConsensusOutput']>,
  'reasoning_trace' | 'metadata'
> & {
  reasoning_trace: ReasoningStep[]
  metadata: ConsensusMetadata
}

/** `/orchestrate` 的实际响应：outputs 已按域窄化、explanation_detail 已解析。 */
export type OrchestrationResponse = Omit<
  Required<Schemas['OrchestrationResponse']>,
  'outputs' | 'consensus' | 'explanation_detail'
> & {
  outputs: AnyOutput[]
  consensus: ConsensusOutput | null
  explanation_detail: Record<string, ExplainDetail>
}

/* ------------------------------------------------- 会话历史（OpenAPI 未描述，手写） */
/** `GET /sessions` 的一项：持久化层只投影 request_id / created_at。 */
export interface SessionSummary {
  request_id: string
  created_at: string
}

/** `GET /sessions` */
export interface SessionListResponse {
  sessions: SessionSummary[]
  /** P2.2: present when the request used the paginated envelope (`limit`/`offset`). */
  total?: number
  limit?: number
  offset?: number
}

/** `GET /sessions/{request_id}`：request/response 为后端存储的原始 JSON。 */
export interface StoredSession {
  request_id: string
  created_at: string
  request: unknown
  response: unknown
}

/* ------------------------------------------------------------- 其他端点 */
export interface Timed<T> {
  data: T
  elapsedMs: number
}

/** error 对象的稳定判别键（api/app.py 的公开错误模型；OpenAPI 未描述，故手写）。 */
export type BackendErrorKind =
  | 'invalid_request'
  | 'unknown_agent'
  | 'calculation_failed'
  | 'internal_error'
  | 'not_found'
  | 'invalid_response'

export interface BackendErrorBody {
  kind: BackendErrorKind | string
  message: string
  agent?: string
  agents?: string[]
  fields?: (string | number)[][]
  type?: string
}
