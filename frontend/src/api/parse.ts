/* 运行时解析：把 HTTP 响应当作不可信输入，逐字段收窄成类型。
 *
 * 不在前端做"尽量猜"的兼容：字段缺失或类型不符时抛 ApiError(kind=invalid_response)，
 * 由错误视图如实展示，避免把残缺数据渲染成看似完整的结论。
 */

import { ApiError } from './errors'
import type {
  AgentOutputEnvelope,
  AnyOutput,
  BaziChart,
  BaziDaYun,
  BaziOutput,
  BaziPillar,
  ConfidenceScore,
  ConsensusContribution,
  ConsensusConflict,
  ConsensusOutput,
  ConsensusResult,
  DomainOutput,
  ExplainDetail,
  ExplainErrorInfo,
  ExplainEvidence,
  HealthResponse,
  KnowledgeChunk,
  LiuyaoChart,
  LiuyaoOutput,
  OrchestrationResponse,
  QimenBoard,
  QimenCell,
  QimenOutput,
  ReasoningStep,
  TraceScalar,
  YaoLine,
  ZiweiChart,
  ZiweiOutput,
  ZiweiPalace,
} from './types'

function fail(path: string, detail?: string): never {
  throw new ApiError({
    transport: 'http',
    kind: 'invalid_response',
    status: 200,
    message: `后端响应不符合契约：${path}${detail ? `（${detail}）` : ''}`,
  })
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function asRecord(value: unknown, path: string): Record<string, unknown> {
  if (!isRecord(value)) fail(path, '应为对象')
  return value
}

function asArray(value: unknown, path: string): unknown[] {
  if (!Array.isArray(value)) fail(path, '应为数组')
  return value
}

function asString(value: unknown, path: string): string {
  if (typeof value !== 'string') fail(path, '应为字符串')
  return value
}

function asNumber(value: unknown, path: string): number {
  if (typeof value !== 'number' || Number.isNaN(value)) fail(path, '应为数字')
  return value
}

function asBoolean(value: unknown, path: string): boolean {
  if (typeof value !== 'boolean') fail(path, '应为布尔值')
  return value
}

function asNullableString(value: unknown, path: string): string | null {
  if (value === null || value === undefined) return null
  return asString(value, path)
}

function asStringArray(value: unknown, path: string): string[] {
  return asArray(value, path).map((item, index) => asString(item, `${path}[${index}]`))
}

function asScalarRecord(value: unknown, path: string): Record<string, TraceScalar> {
  const record = asRecord(value, path)
  const out: Record<string, TraceScalar> = {}
  for (const [key, item] of Object.entries(record)) {
    if (typeof item === 'string' || typeof item === 'number' || typeof item === 'boolean') {
      out[key] = item
    } else {
      fail(`${path}.${key}`, '应为 string/number/boolean')
    }
  }
  return out
}

/** 保留标量值、忽略非标量值（后端此字段类型为 dict[str, Any]，只展示标量部分）。 */
function asLenientScalarRecord(value: unknown, path: string): Record<string, TraceScalar> {
  const record = asRecord(value, path)
  const out: Record<string, TraceScalar> = {}
  for (const [key, item] of Object.entries(record)) {
    if (typeof item === 'string' || typeof item === 'number' || typeof item === 'boolean') out[key] = item
  }
  return out
}

function asNumberRecord(value: unknown, path: string): Record<string, number> {
  const record = asRecord(value, path)
  const out: Record<string, number> = {}
  for (const [key, item] of Object.entries(record)) out[key] = asNumber(item, `${path}.${key}`)
  return out
}

function asStringRecord(value: unknown, path: string): Record<string, string> {
  const record = asRecord(value, path)
  const out: Record<string, string> = {}
  for (const [key, item] of Object.entries(record)) out[key] = asString(item, `${path}.${key}`)
  return out
}

function asNullable<T>(value: unknown, path: string, parse: (value: unknown, path: string) => T): T | null {
  if (value === null || value === undefined) return null
  return parse(value, path)
}

/* ----------------------------------------------------------------- 公共块 */
function parseConfidence(value: unknown, path: string): ConfidenceScore {
  const record = asRecord(value, path)
  return {
    value: asNumber(record.value, `${path}.value`),
    method: asString(record.method, `${path}.method`),
    factors: asNumberRecord(record.factors, `${path}.factors`),
  }
}

function parseReasoningStep(value: unknown, path: string): ReasoningStep {
  const record = asRecord(value, path)
  return {
    step: asNumber(record.step, `${path}.step`),
    rule_ref: asString(record.rule_ref, `${path}.rule_ref`),
    description: asString(record.description, `${path}.description`),
    inputs: asScalarRecord(record.inputs, `${path}.inputs`),
    outputs: asScalarRecord(record.outputs, `${path}.outputs`),
  }
}

function parseEnvelopeBase(value: unknown, path: string): AgentOutputEnvelope {
  const record = asRecord(value, path)
  return {
    request_id: asString(record.request_id, `${path}.request_id`),
    agent: asString(record.agent, `${path}.agent`),
    engine_version: asString(record.engine_version, `${path}.engine_version`),
    input_hash: asString(record.input_hash, `${path}.input_hash`),
    computed_at: asString(record.computed_at, `${path}.computed_at`),
    confidence: parseConfidence(record.confidence, `${path}.confidence`),
    reasoning_trace: asArray(record.reasoning_trace, `${path}.reasoning_trace`).map((item, index) =>
      parseReasoningStep(item, `${path}.reasoning_trace[${index}]`),
    ),
    metadata: asScalarRecord(record.metadata, `${path}.metadata`),
    result: record.result,
  }
}

/* ------------------------------------------------------------- 八字 / Bazi */
function parseBaziPillar(value: unknown, path: string): BaziPillar {
  const record = asRecord(value, path)
  const position = asString(record.position, `${path}.position`)
  if (position !== 'year' && position !== 'month' && position !== 'day' && position !== 'hour') {
    fail(`${path}.position`, `未知柱位 ${position}`)
  }
  return {
    position,
    stem: asString(record.stem, `${path}.stem`),
    branch: asString(record.branch, `${path}.branch`),
    stem_index: asNumber(record.stem_index, `${path}.stem_index`),
    branch_index: asNumber(record.branch_index, `${path}.branch_index`),
    hidden_stems: asStringArray(record.hidden_stems, `${path}.hidden_stems`),
    nayin: asString(record.nayin, `${path}.nayin`),
    ten_god: asString(record.ten_god, `${path}.ten_god`),
  }
}

function parseBaziDaYun(value: unknown, path: string): BaziDaYun {
  const record = asRecord(value, path)
  return {
    index: asNumber(record.index, `${path}.index`),
    start_age: asNumber(record.start_age, `${path}.start_age`),
    end_age: asNumber(record.end_age, `${path}.end_age`),
    stem: asString(record.stem, `${path}.stem`),
    branch: asString(record.branch, `${path}.branch`),
    stem_index: asNumber(record.stem_index, `${path}.stem_index`),
    branch_index: asNumber(record.branch_index, `${path}.branch_index`),
    start_at: asString(record.start_at, `${path}.start_at`),
  }
}

function parseBaziChart(value: unknown, path: string): BaziChart {
  const record = asRecord(value, path)
  return {
    day_master: asString(record.day_master, `${path}.day_master`),
    day_master_element: asString(record.day_master_element, `${path}.day_master_element`),
    pillars: asArray(record.pillars, `${path}.pillars`).map((item, index) =>
      parseBaziPillar(item, `${path}.pillars[${index}]`),
    ),
    dayun: asArray(record.dayun, `${path}.dayun`).map((item, index) => parseBaziDaYun(item, `${path}.dayun[${index}]`)),
    ten_gods_map: asStringRecord(record.ten_gods_map, `${path}.ten_gods_map`),
    year_boundary: asString(record.year_boundary, `${path}.year_boundary`),
    month_boundary: asString(record.month_boundary, `${path}.month_boundary`),
    gender_assumed: asBoolean(record.gender_assumed, `${path}.gender_assumed`),
  }
}

/* ------------------------------------------------------------ 紫微 / Ziwei */
function parseZiweiPalace(value: unknown, path: string): ZiweiPalace {
  const record = asRecord(value, path)
  return {
    index: asNumber(record.index, `${path}.index`),
    name: asString(record.name, `${path}.name`),
    earthly_branch: asString(record.earthly_branch, `${path}.earthly_branch`),
    heavenly_stem: asString(record.heavenly_stem, `${path}.heavenly_stem`),
    main_stars: asStringArray(record.main_stars, `${path}.main_stars`),
    auxiliary_stars: asStringArray(record.auxiliary_stars, `${path}.auxiliary_stars`),
    is_fate_palace: asBoolean(record.is_fate_palace, `${path}.is_fate_palace`),
    is_body_palace: asBoolean(record.is_body_palace, `${path}.is_body_palace`),
  }
}

function parseZiweiChart(value: unknown, path: string): ZiweiChart {
  const record = asRecord(value, path)
  return {
    fate_palace_index: asNumber(record.fate_palace_index, `${path}.fate_palace_index`),
    body_palace_index: asNumber(record.body_palace_index, `${path}.body_palace_index`),
    yin_yang: asString(record.yin_yang, `${path}.yin_yang`),
    wuxing_ju: asString(record.wuxing_ju, `${path}.wuxing_ju`),
    palaces: asArray(record.palaces, `${path}.palaces`).map((item, index) =>
      parseZiweiPalace(item, `${path}.palaces[${index}]`),
    ),
    calendar_note: asNullableString(record.calendar_note, `${path}.calendar_note`),
  }
}

/* ------------------------------------------------------------ 奇门 / Qimen */
function parseQimenCell(value: unknown, path: string): QimenCell {
  const record = asRecord(value, path)
  return {
    palace: asNumber(record.palace, `${path}.palace`),
    name: asString(record.name, `${path}.name`),
    sky_plate: asNullableString(record.sky_plate, `${path}.sky_plate`),
    earth_plate: asNullableString(record.earth_plate, `${path}.earth_plate`),
    eight_gods: asNullableString(record.eight_gods, `${path}.eight_gods`),
    nine_stars: asNullableString(record.nine_stars, `${path}.nine_stars`),
    eight_doors: asNullableString(record.eight_doors, `${path}.eight_doors`),
    three_qi: asNullableString(record.three_qi, `${path}.three_qi`),
    is_void: asBoolean(record.is_void, `${path}.is_void`),
    is_central: asBoolean(record.is_central, `${path}.is_central`),
  }
}

function parseQimenBoard(value: unknown, path: string): QimenBoard {
  const record = asRecord(value, path)
  return {
    solar_term: asNullableString(record.solar_term, `${path}.solar_term`),
    ju: asNumber(record.ju, `${path}.ju`),
    dun_type: asString(record.dun_type, `${path}.dun_type`),
    day_of_month: asNumber(record.day_of_month, `${path}.day_of_month`),
    triple_offset: asNumber(record.triple_offset, `${path}.triple_offset`),
    cells: asArray(record.cells, `${path}.cells`).map((item, index) =>
      parseQimenCell(item, `${path}.cells[${index}]`),
    ),
  }
}

/* ------------------------------------------------------------ 六爻 / Liuyao */
function parseYaoLine(value: unknown, path: string): YaoLine {
  const record = asRecord(value, path)
  return {
    position: asNumber(record.position, `${path}.position`),
    is_yin: asBoolean(record.is_yin, `${path}.is_yin`),
    is_changing: asBoolean(record.is_changing, `${path}.is_changing`),
    cast_value: asNumber(record.cast_value, `${path}.cast_value`),
  }
}

function parseYaoLines(value: unknown, path: string): YaoLine[] {
  return asArray(value, path).map((item, index) => parseYaoLine(item, `${path}[${index}]`))
}

function parseLiuyaoChart(value: unknown, path: string): LiuyaoChart {
  const record = asRecord(value, path)
  return {
    original: parseYaoLines(record.original, `${path}.original`),
    changed: parseYaoLines(record.changed, `${path}.changed`),
    mutual: parseYaoLines(record.mutual, `${path}.mutual`),
    original_hexagram: asNumber(record.original_hexagram, `${path}.original_hexagram`),
    changed_hexagram: asNullable<number>(record.changed_hexagram, `${path}.changed_hexagram`, asNumber),
    mutual_hexagram: asNullable<number>(record.mutual_hexagram, `${path}.mutual_hexagram`, asNumber),
    najia: asStringArray(record.najia, `${path}.najia`),
    liu_qin: asStringArray(record.liu_qin, `${path}.liu_qin`),
    liu_shen: asStringArray(record.liu_shen, `${path}.liu_shen`),
    shi_position: asNumber(record.shi_position, `${path}.shi_position`),
    ying_position: asNumber(record.ying_position, `${path}.ying_position`),
    palace: asString(record.palace, `${path}.palace`),
    palace_element: asString(record.palace_element, `${path}.palace_element`),
    yong_shen: asNullableString(record.yong_shen, `${path}.yong_shen`),
  }
}

/* ---------------------------------------------------------------- 输出联合 */
export function parseOutput(value: unknown, path: string): AnyOutput {
  const base = parseEnvelopeBase(value, path)
  switch (base.agent) {
    case 'bazi': {
      const output: BaziOutput = { ...base, agent: 'bazi', result: parseBaziChart(base.result, `${path}.result`) }
      return output
    }
    case 'ziwei': {
      const output: ZiweiOutput = { ...base, agent: 'ziwei', result: parseZiweiChart(base.result, `${path}.result`) }
      return output
    }
    case 'qimen': {
      const output: QimenOutput = { ...base, agent: 'qimen', result: parseQimenBoard(base.result, `${path}.result`) }
      return output
    }
    case 'liuyao': {
      const output: LiuyaoOutput = { ...base, agent: 'liuyao', result: parseLiuyaoChart(base.result, `${path}.result`) }
      return output
    }
    default:
      return { ...base, result: base.result }
  }
}

export function isDomainOutput(output: AnyOutput): output is DomainOutput {
  return output.agent === 'bazi' || output.agent === 'ziwei' || output.agent === 'qimen' || output.agent === 'liuyao'
}

/* ------------------------------- 解释 / 知识证据 / 共识 / orchestrate 响应 */
function parseKnowledgeChunk(value: unknown, path: string): KnowledgeChunk {
  const record = asRecord(value, path)
  const chunk: KnowledgeChunk = {
    id: asString(record.id, `${path}.id`),
    source: asString(record.source, `${path}.source`),
  }
  if (typeof record.text === 'string') chunk.text = record.text
  return chunk
}

function parseExplainEvidence(value: unknown, path: string): ExplainEvidence {
  const record = asRecord(value, path)
  const evidence: ExplainEvidence = {}
  if (record.agent !== undefined) evidence.agent = asString(record.agent, `${path}.agent`)
  if (record.engine_version !== undefined) {
    evidence.engine_version = asString(record.engine_version, `${path}.engine_version`)
  }
  if (record.input_hash !== undefined) evidence.input_hash = asString(record.input_hash, `${path}.input_hash`)
  if (record.confidence !== undefined) evidence.confidence = parseConfidence(record.confidence, `${path}.confidence`)
  if (record.result !== undefined) evidence.result = record.result
  if (record.reasoning_trace !== undefined) {
    evidence.reasoning_trace = asArray(record.reasoning_trace, `${path}.reasoning_trace`).map((item, index) =>
      parseReasoningStep(item, `${path}.reasoning_trace[${index}]`),
    )
  }
  if (record.metadata !== undefined) evidence.metadata = asScalarRecord(record.metadata, `${path}.metadata`)
  return evidence
}

function parseExplainError(value: unknown, path: string): ExplainErrorInfo | null {
  if (value === null || value === undefined) return null
  const record = asRecord(value, path)
  const error: ExplainErrorInfo = { kind: asString(record.kind, `${path}.kind`) }
  if (record.type !== undefined) error.type = asString(record.type, `${path}.type`)
  if (record.message !== undefined) error.message = asString(record.message, `${path}.message`)
  if (record.provider !== undefined) error.provider = asNullableString(record.provider, `${path}.provider`)
  return error
}

export function parseExplainDetail(value: unknown, path: string): ExplainDetail {
  const record = asRecord(value, path)
  return {
    explanation: asString(record.explanation, `${path}.explanation`),
    provider: asNullableString(record.provider, `${path}.provider`),
    degraded: asBoolean(record.degraded, `${path}.degraded`),
    knowledge: asArray(record.knowledge, `${path}.knowledge`).map((item, index) =>
      parseKnowledgeChunk(item, `${path}.knowledge[${index}]`),
    ),
    evidence: parseExplainEvidence(record.evidence, `${path}.evidence`),
    error: parseExplainError(record.error, `${path}.error`),
  }
}

function parseConsensusContribution(value: unknown, path: string): ConsensusContribution {
  const record = asRecord(value, path)
  return {
    agent: asString(record.agent, `${path}.agent`),
    confidence: asNumber(record.confidence, `${path}.confidence`),
    weight: asNumber(record.weight, `${path}.weight`),
    element: asNullableString(record.element, `${path}.element`),
    summary: asString(record.summary, `${path}.summary`),
  }
}

function parseConsensusConflict(value: unknown, path: string): ConsensusConflict {
  const record = asRecord(value, path)
  return {
    agents: asStringArray(record.agents, `${path}.agents`),
    field: asString(record.field, `${path}.field`),
    values: asStringArray(record.values, `${path}.values`),
    severity: asString(record.severity, `${path}.severity`),
  }
}

function parseAgreementMatrix(value: unknown, path: string): Record<string, Record<string, number>> {
  const record = asRecord(value, path)
  const matrix: Record<string, Record<string, number>> = {}
  for (const [rowKey, row] of Object.entries(record)) {
    matrix[rowKey] = asNumberRecord(row, `${path}.${rowKey}`)
  }
  return matrix
}

function parseConsensusResult(value: unknown, path: string): ConsensusResult {
  const record = asRecord(value, path)
  return {
    overall_confidence: asNumber(record.overall_confidence, `${path}.overall_confidence`),
    contributions: asArray(record.contributions, `${path}.contributions`).map((item, index) =>
      parseConsensusContribution(item, `${path}.contributions[${index}]`),
    ),
    agreement_matrix: parseAgreementMatrix(record.agreement_matrix, `${path}.agreement_matrix`),
    conflicts: asArray(record.conflicts, `${path}.conflicts`).map((item, index) =>
      parseConsensusConflict(item, `${path}.conflicts[${index}]`),
    ),
    synthesis: asString(record.synthesis, `${path}.synthesis`),
    recommendation: asNullableString(record.recommendation, `${path}.recommendation`),
  }
}

function parseConsensus(value: unknown, path: string): ConsensusOutput {
  // 注意：ConsensusOutput 不是 AgentOutput 子类，没有 input_hash 字段。
  const record = asRecord(value, path)
  return {
    request_id: asString(record.request_id, `${path}.request_id`),
    agent: 'consensus',
    engine_version: asString(record.engine_version, `${path}.engine_version`),
    computed_at: asString(record.computed_at, `${path}.computed_at`),
    confidence: asNumber(record.confidence, `${path}.confidence`),
    reasoning_trace: asArray(record.reasoning_trace, `${path}.reasoning_trace`).map((item, index) =>
      parseReasoningStep(item, `${path}.reasoning_trace[${index}]`),
    ),
    metadata: asLenientScalarRecord(record.metadata, `${path}.metadata`),
    result: parseConsensusResult(record.result, `${path}.result`),
  }
}

export function parseOrchestrationResponse(value: unknown): OrchestrationResponse {
  const path = 'orchestrate'
  const record = asRecord(value, path)
  const explanationDetail = asRecord(record.explanation_detail, `${path}.explanation_detail`)
  const details: Record<string, ExplainDetail> = {}
  for (const [agent, detail] of Object.entries(explanationDetail)) {
    details[agent] = parseExplainDetail(detail, `${path}.explanation_detail.${agent}`)
  }
  return {
    request_id: asString(record.request_id, `${path}.request_id`),
    outputs: asArray(record.outputs, `${path}.outputs`).map((item, index) =>
      parseOutput(item, `${path}.outputs[${index}]`),
    ),
    consensus: asNullable<ConsensusOutput>(record.consensus, `${path}.consensus`, parseConsensus),
    explanation: asStringRecord(record.explanation, `${path}.explanation`),
    explanation_detail: details,
    errors: asStringArray(record.errors, `${path}.errors`),
  }
}

export function parseHealthResponse(value: unknown): HealthResponse {
  const record = asRecord(value, 'health')
  return {
    status: asString(record.status, 'health.status'),
    agents: asStringArray(record.agents, 'health.agents'),
  }
}
