/* 表单校验与请求构造：唯一入口，供表单与「请求体预览」共用。 */

import type { AgentName, Gender, GeoPoint, OrchestrationRequest } from '../api/types'
import { DOMAINS } from '../config'
import { isValidTimeZone, zonedToIso } from './timezone'

export interface FormValues {
  domains: AgentName[]
  date: string
  time: string
  timezone: string
  gender: Gender
  question: string
  seed: string
  lat: string
  lon: string
  nonce: string
}

export type FieldKey =
  | 'domains'
  | 'date'
  | 'time'
  | 'timezone'
  | 'question'
  | 'seed'
  | 'lat'
  | 'lon'
  | 'gender'

export interface FieldError {
  field: FieldKey | null
  message: string
}

export interface BuildRequestSuccess {
  errors: []
  payload: OrchestrationRequest
  bornAt: string
}

export interface BuildRequestFailure {
  errors: FieldError[]
}

export type BuildRequestResult = BuildRequestSuccess | BuildRequestFailure

const GENDERS: readonly Gender[] = ['male', 'female', 'unknown']

export function makeRequestId(): string {
  return `ui-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
}

function parseSeed(raw: string): { value?: number; error?: string } {
  if (!raw) return {}
  if (!/^-?\d+$/.test(raw)) return { error: '起卦种子必须是整数。' }
  const value = Number(raw)
  if (!Number.isSafeInteger(value)) return { error: '起卦种子超出安全整数范围。' }
  return { value }
}

/** 构造 `/orchestrate` 请求体；请求 id 由调用方传入，便于预览与重试保持一致。 */
export function buildRequest(values: FormValues, requestId: string): BuildRequestResult {
  const errors: FieldError[] = []

  const domains = values.domains.filter((domain) => DOMAINS.some((meta) => meta.id === domain))
  if (domains.length === 0) errors.push({ field: 'domains', message: '至少选择一个分析领域。' })
  if (!values.date) errors.push({ field: 'date', message: '请填写出生日期。' })
  if (!values.time) errors.push({ field: 'time', message: '请填写出生时间。' })
  if (!values.timezone) {
    errors.push({ field: 'timezone', message: '请填写 IANA 时区。' })
  } else if (!isValidTimeZone(values.timezone)) {
    errors.push({
      field: 'timezone',
      message: `浏览器无法识别时区「${values.timezone}」，请使用 IANA 名称，如 Asia/Shanghai。`,
    })
  }
  if (values.question.length > 500) errors.push({ field: 'question', message: '问题请控制在 500 字以内。' })
  if (!GENDERS.includes(values.gender)) errors.push({ field: 'gender', message: '性别取值非法。' })

  let bornAt: string | null = null
  if (!errors.some((error) => error.field === 'date' || error.field === 'time' || error.field === 'timezone')) {
    try {
      bornAt = zonedToIso(values.date, values.time, values.timezone).iso
    } catch (error) {
      errors.push({
        field: 'date',
        message: `无法转换出生时间：${error instanceof Error ? error.message : String(error)}`,
      })
    }
  }

  const seed = parseSeed(values.seed)
  if (seed.error) errors.push({ field: 'seed', message: seed.error })

  let bornLocation: GeoPoint | null = null
  if (values.lat || values.lon) {
    if (!values.lat || !values.lon) {
      errors.push({ field: 'lat', message: '经度与纬度需同时填写，或同时留空。' })
    } else {
      const latitude = Number(values.lat)
      const longitude = Number(values.lon)
      if (!Number.isFinite(latitude) || latitude < -90 || latitude > 90) {
        errors.push({ field: 'lat', message: '纬度必须在 -90 ~ 90 之间。' })
      }
      if (!Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
        errors.push({ field: 'lon', message: '经度必须在 -180 ~ 180 之间。' })
      }
      if (!errors.some((error) => error.field === 'lat' || error.field === 'lon')) {
        bornLocation = { latitude, longitude, timezone: values.timezone }
      }
    }
  }

  if (errors.length > 0 || bornAt === null) return { errors }

  const payload: OrchestrationRequest = {
    request_id: requestId,
    payload: {
      request_id: requestId,
      born_at: bornAt,
      gender: values.gender,
      locale: 'zh-CN',
    },
    agents: domains,
    strategy: 'weighted',
    explain: true,
  }
  if (values.question) payload.payload.question = values.question
  if (seed.value !== undefined) payload.payload.seed = seed.value
  if (values.nonce) payload.payload.client_nonce = values.nonce
  if (bornLocation) payload.payload.born_location = bornLocation

  return { errors: [], payload, bornAt }
}
