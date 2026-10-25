/* 后端契约类型（手写，来源见每个类型注释）。
 *
 * 依据：
 *   - `src/openmetaphysics/core/schemas.py`（AgentInput / AgentOutput / ConfidenceScore / ReasoningStep / GeoPoint / Gender）
 *   - `src/openmetaphysics/agents/{bazi,ziwei,qimen,liuyao}.py`（各域 result 模型）
 *   - `src/openmetaphysics/agents/consensus.py`、`src/openmetaphysics/consensus/models.py`
 *   - `src/openmetaphysics/orchestration/graph.py`（OrchestrationRequest / Response）
 *   - `src/openmetaphysics/api/app.py`（/health、/orchestrate、/agents/{name}/explain 的 explain 块、错误模型）
 *   - 实际 HTTP 响应（本轮迁移前对运行中的后端逐端点采样核对）
 *
 * 运行时校验在 `parse.ts`：这里只是静态形状，不能假设响应一定符合。
 */

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue }

export type Gender = 'male' | 'female' | 'unknown'

export const AGENT_NAMES = ['bazi', 'ziwei', 'qimen', 'liuyao'] as const

export type AgentName = (typeof AGENT_NAMES)[number]

export interface GeoPoint {
  latitude: number
  longitude: number
  elevation_m?: number | null
  timezone?: string | null
}

/** core/schemas.py::AgentInput */
export interface AgentInput {
  request_id: string
  /** ISO 8601，必须带时区偏移 */
  born_at: string
  born_location?: GeoPoint | null
  gender?: Gender
  question?: string | null
  locale?: string
  seed?: number | null
  client_nonce?: string | null
}

/** orchestration/graph.py::OrchestrationRequest */
export interface OrchestrationRequest {
  request_id: string
  payload: AgentInput
  agents?: AgentName[] | null
  strategy?: string
  explain?: boolean
}

export interface ConfidenceScore {
  value: number
  method: string
  factors: Record<string, number>
}

export type TraceScalar = string | number | boolean

export interface ReasoningStep {
  step: number
  rule_ref: string
  description: string
  inputs: Record<string, TraceScalar>
  outputs: Record<string, TraceScalar>
}

export type OutputMetadata = Record<string, TraceScalar>

/** core/schemas.py::AgentOutput —— 所有域共用的信封。 */
export interface AgentOutputEnvelope {
  request_id: string
  agent: string
  engine_version: string
  input_hash: string
  computed_at: string
  confidence: ConfidenceScore
  reasoning_trace: ReasoningStep[]
  metadata: OutputMetadata
  result: unknown
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

/** agents/bazi.py::BaziChart */
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

/** agents/ziwei.py::ZiweiChart */
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

/** agents/qimen.py::QimenBoard */
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

/** agents/liuyao.py::LiuyaoChart */
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
export interface BaziOutput extends AgentOutputEnvelope {
  agent: 'bazi'
  result: BaziChart
}

export interface ZiweiOutput extends AgentOutputEnvelope {
  agent: 'ziwei'
  result: ZiweiChart
}

export interface QimenOutput extends AgentOutputEnvelope {
  agent: 'qimen'
  result: QimenBoard
}

export interface LiuyaoOutput extends AgentOutputEnvelope {
  agent: 'liuyao'
  result: LiuyaoChart
}

/** 未知域（后端注册了但前端暂无专用渲染器）——保留原始 result。 */
export interface GenericOutput extends AgentOutputEnvelope {
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

/** 后端 explain 块的统一形状（compute?explain / explain / orchestrate.detail）。 */
export interface ExplainDetail {
  explanation: string
  provider: string | null
  degraded: boolean
  knowledge: KnowledgeChunk[]
  evidence: ExplainEvidence
  error: ExplainErrorInfo | null
}

export interface ConsensusContribution {
  agent: string
  confidence: number
  weight: number
  element: string | null
  summary: string
}

export interface ConsensusConflict {
  agents: string[]
  field: string
  values: string[]
  severity: string
}

export interface ConsensusResult {
  overall_confidence: number
  contributions: ConsensusContribution[]
  agreement_matrix: Record<string, Record<string, number>>
  conflicts: ConsensusConflict[]
  synthesis: string
  recommendation: string | null
}

/** 后端 ConsensusAgent 的 metadata 是自由标量字典（含 strategy / agent_count）。 */
export type ConsensusMetadata = Record<string, TraceScalar>

/** agents/consensus.py::ConsensusOutput（result 为 ConsensusResult）。 */
export interface ConsensusOutput {
  request_id: string
  agent: 'consensus'
  engine_version: string
  computed_at: string
  /** 注意：后端 ConsensusOutput.confidence 是 float（不是 ConfidenceScore 对象）。 */
  confidence: number
  reasoning_trace: ReasoningStep[]
  metadata: ConsensusMetadata
  result: ConsensusResult
}

/** orchestration/graph.py::OrchestrationResponse */
export interface OrchestrationResponse {
  request_id: string
  outputs: AnyOutput[]
  consensus: ConsensusOutput | null
  explanation: Record<string, string>
  explanation_detail: Record<string, ExplainDetail>
  errors: string[]
}

/* ------------------------------------------------------------- 其他端点 */
/** api/app.py::health */
export interface HealthResponse {
  status: string
  agents: string[]
}

export interface Timed<T> {
  data: T
  elapsedMs: number
}

/** error 对象的稳定判别键（api/app.py 的公开错误模型）。 */
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
