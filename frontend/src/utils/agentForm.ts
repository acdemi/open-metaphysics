/* 领域独立计算的表单模型：草稿 → 校验 → 后端 AgentInput payload。
 *
 * 字段集合来自后端 `/agents/{name}/schema`（是否存在、required、enum、default），
 * 这里只补充四个领域各自的输入语义（出生时刻、六爻 casts、紫微农历）。
 */

import type { AgentName, Gender } from '../api/types'
import { DEMO_DEFAULTS, GENDER_OPTIONS } from '../config'
import {
  defaultFieldValue,
  enumValues,
  hasField,
  type AgentInputSchema,
} from './agentSchema'
import { zonedToIso } from './timezone'

export interface AgentDraft {
  date: string
  time: string
  timezone: string
  /** 出生地纬度（可空，必须与 longitude 成对出现）。 */
  latitude: string
  /** 出生地经度（可空，必须与 latitude 成对出现）。 */
  longitude: string
  gender: Gender
  question: string
  /** 可选整数种子的文本形式；空串表示不发送（由后端决定）。 */
  seed: string
  /** 八字：大运步数（后端默认 8）。 */
  dayunCount: string
  /** 紫微：农历月/日（必须同时为空或同时填写）。 */
  lunarMonth: string
  lunarDay: string
  /** 六爻：6 个起卦值（6/7/8/9，自下而上），空串表示由后端按 seed 起卦。 */
  casts: string
}

export type AgentFieldErrors = Record<string, string>

export const FIELD_LABELS: Record<string, string> = {
  date: '出生日期',
  time: '出生时间',
  timezone: '时区',
  latitude: '纬度（可选）',
  longitude: '经度（可选）',
  gender: '性别',
  question: '问题（可选）',
  seed: '随机种子（可选）',
  dayun_count: '大运步数',
  lunar_month: '农历月（可选）',
  lunar_day: '农历日（可选）',
  casts: '六爻起卦值（可选）',
}

const CAST_VALUES = [6, 7, 8, 9] as const

/**
 * 出生地/时区语义提示（H5）：`born_at` 按所选 IANA 时区换算为带偏移的 ISO 8601；
 * `born_location.timezone` 保持 IANA 名称，供后端做真太阳时/地方时修正。
 */
export const BORN_LOCATION_HINT =
  '经纬度可选，对真太阳时/地方时计算有意义；出生时刻始终按所选 IANA 时区换算为带偏移的 born_at。经纬度必须同时填写或同时留空。'

export function emptyDraft(): AgentDraft {
  return {
    date: DEMO_DEFAULTS.date,
    time: DEMO_DEFAULTS.time,
    timezone: DEMO_DEFAULTS.timezone,
    latitude: '',
    longitude: '',
    gender: 'unknown',
    question: '',
    seed: '',
    dayunCount: '8',
    lunarMonth: '',
    lunarDay: '',
    casts: '',
  }
}

/** 按 schema 的 enum/default 初始化草稿（切领域时重置为该领域默认值）。 */
export function draftFromSchema(schema: AgentInputSchema | null): AgentDraft {
  const draft = emptyDraft()
  if (!schema) return draft
  const genderDefault = defaultFieldValue(schema, 'gender')
  const genderOptions = enumValues(schema, 'gender')
  if (typeof genderDefault === 'string' && genderOptions.includes(genderDefault)) {
    draft.gender = genderDefault as Gender
  }
  const dayunDefault = defaultFieldValue(schema, 'dayun_count')
  if (typeof dayunDefault === 'number') draft.dayunCount = String(dayunDefault)
  return draft
}

export function parseCasts(text: string): number[] {
  const parts = text
    .split(/[\s,，]+/)
    .map((part) => part.trim())
    .filter((part) => part.length > 0)
  return parts.map((part) => Number(part))
}

export function castsError(text: string): string | null {
  const values = parseCasts(text)
  if (values.length !== 6) return '需要恰好 6 个起卦值（自下而上）'
  if (values.some((value) => !CAST_VALUES.includes(value as (typeof CAST_VALUES)[number]))) {
    return '每个起卦值必须是 6、7、8 或 9'
  }
  return null
}

/** 校验草稿；返回按字段聚合的错误（空对象代表可提交）。 */
export function validateDraft(schema: AgentInputSchema | null, draft: AgentDraft): AgentFieldErrors {
  const errors: AgentFieldErrors = {}

  try {
    zonedToIso(draft.date, draft.time, draft.timezone)
  } catch (caught) {
    const message = caught instanceof Error ? caught.message : String(caught)
    if (message.includes('时区')) errors.timezone = message
    else if (message.includes('时间')) errors.time = message
    else errors.date = message
  }

  const genderOptions = schema ? enumValues(schema, 'gender') : GENDER_OPTIONS.map((item) => item.value)
  if (genderOptions.length > 0 && !genderOptions.includes(draft.gender)) {
    errors.gender = '请选择后端支持的性别值'
  }

  // 出生地经纬度（H5）：可空，但必须成对；范围与后端 GeoPoint 一致。
  // born_at 的时区偏移由 draft.timezone 决定，born_location.timezone 只是 IANA 名称。
  const latitudeText = draft.latitude.trim()
  const longitudeText = draft.longitude.trim()
  if ((latitudeText === '') !== (longitudeText === '')) {
    errors.latitude = '纬度与经度必须同时填写或同时留空'
    errors.longitude = '纬度与经度必须同时填写或同时留空'
  } else if (latitudeText !== '') {
    const latitude = Number(latitudeText)
    const longitude = Number(longitudeText)
    if (!Number.isFinite(latitude) || latitude < -90 || latitude > 90) {
      errors.latitude = '纬度必须是 -90 到 90 之间的数字'
    }
    if (!Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
      errors.longitude = '经度必须是 -180 到 180 之间的数字'
    }
  }

  const seed = draft.seed.trim()
  if (seed !== '' && !/^-?\d+$/.test(seed)) errors.seed = '随机种子必须是整数'

  if (schema && hasField(schema, 'dayun_count')) {
    const raw = draft.dayunCount.trim()
    if (raw === '') errors.dayun_count = '请填写大运步数（后端默认 8）'
    else if (!/^\d+$/.test(raw)) errors.dayun_count = '大运步数必须是非负整数'
  }

  const hasMonth = draft.lunarMonth.trim() !== ''
  const hasDay = draft.lunarDay.trim() !== ''
  if (hasMonth !== hasDay) {
    errors.lunar_month = '农历月与农历日必须同时填写或同时留空'
    errors.lunar_day = '农历月与农历日必须同时填写或同时留空'
  } else if (hasMonth) {
    const month = Number(draft.lunarMonth)
    const day = Number(draft.lunarDay)
    if (!Number.isInteger(month) || month < 1 || month > 12) {
      errors.lunar_month = '农历月必须是 1–12 的整数'
    }
    if (!Number.isInteger(day) || day < 1 || day > 30) {
      errors.lunar_day = '农历日必须是 1–30 的整数'
    }
  }

  if (draft.casts.trim() !== '') {
    const message = castsError(draft.casts)
    if (message) errors.casts = message
  }

  return errors
}

export interface AgentPayloadResult {
  payload: Record<string, unknown>
  errors: AgentFieldErrors
}

/** 构造后端 `AgentInput` 子类可接受的 payload；只包含 schema 声明过的领域字段。 */
export function buildAgentPayload(
  draft: AgentDraft,
  requestId: string,
  schema: AgentInputSchema | null,
): AgentPayloadResult {
  const errors = validateDraft(schema, draft)
  if (Object.keys(errors).length > 0) return { payload: {}, errors }

  const bornAt = zonedToIso(draft.date, draft.time, draft.timezone).iso
  const payload: Record<string, unknown> = {
    request_id: requestId,
    born_at: bornAt,
    gender: draft.gender,
  }
  // born_at 已按 draft.timezone 换算为带偏移的 ISO 8601（H5）；
  // born_location.timezone 保持 IANA 名称，供后端做真太阳时/地方时修正。
  if (
    schema &&
    hasField(schema, 'born_location') &&
    draft.latitude.trim() !== '' &&
    draft.longitude.trim() !== ''
  ) {
    payload.born_location = {
      latitude: Number(draft.latitude),
      longitude: Number(draft.longitude),
      timezone: draft.timezone,
    }
  }
  const question = draft.question.trim()
  if (question !== '') payload.question = question
  const seed = draft.seed.trim()
  if (seed !== '') payload.seed = Number(seed)

  if (schema && hasField(schema, 'dayun_count')) {
    payload.dayun_count = Number(draft.dayunCount)
  }
  if (schema && hasField(schema, 'lunar_month') && draft.lunarMonth.trim() !== '') {
    payload.lunar_month = Number(draft.lunarMonth)
    payload.lunar_day = Number(draft.lunarDay)
  }
  if (schema && hasField(schema, 'casts') && draft.casts.trim() !== '') {
    payload.casts = parseCasts(draft.casts)
  }
  return { payload, errors: {} }
}

/** 结果展示用：领域名 → 中文名（沿用 config 的 DOMAINS 也可，但这里避免组件依赖）。 */
export function isAgentName(value: string): value is AgentName {
  return value === 'bazi' || value === 'ziwei' || value === 'qimen' || value === 'liuyao'
}
