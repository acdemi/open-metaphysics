/* HTTP / 网络错误归一化：所有失败都以 ApiError 表达，界面只消费这一种错误。 */

import type { BackendErrorBody } from './types'

export type TransportFailure = 'network' | 'timeout' | 'cancelled' | 'http'

export interface ApiErrorInit {
  transport: TransportFailure
  message: string
  /** 后端 error.kind（若有），否则由 transport 派生 */
  kind?: string
  status?: number
  body?: unknown
  elapsedMs?: number
}

export class ApiError extends Error {
  readonly transport: TransportFailure
  readonly kind: string
  readonly status: number
  readonly body: unknown
  readonly elapsedMs: number

  constructor(init: ApiErrorInit) {
    super(init.message)
    this.name = 'ApiError'
    this.transport = init.transport
    this.kind = init.kind ?? init.transport
    this.status = init.status ?? 0
    this.body = init.body ?? null
    this.elapsedMs = init.elapsedMs ?? 0
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}

export function asErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  if (typeof error === 'string') return error
  try {
    return JSON.stringify(error)
  } catch {
    return String(error)
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/** 从任意响应体中取出后端公开错误对象（`{ error: { kind, message, ... } }`）。 */
export function backendErrorBody(body: unknown): BackendErrorBody | null {
  if (!isRecord(body)) return null
  const error = body.error
  if (!isRecord(error)) return null
  if (typeof error.kind !== 'string' || typeof error.message !== 'string') return null
  const parsed: BackendErrorBody = { kind: error.kind, message: error.message }
  if (typeof error.agent === 'string') parsed.agent = error.agent
  if (Array.isArray(error.agents) && error.agents.every((item) => typeof item === 'string')) {
    parsed.agents = [...error.agents]
  }
  if (Array.isArray(error.fields)) {
    parsed.fields = error.fields
      .filter((field): field is (string | number)[] => Array.isArray(field))
      .map((field) => field.filter((part): part is string | number => typeof part === 'string' || typeof part === 'number'))
  }
  if (typeof error.type === 'string') parsed.type = error.type
  return parsed
}

/** 从 FastAPI 的 422 `detail` 中提取可读字段信息。 */
export function validationDetailMessages(body: unknown): string[] {
  if (!isRecord(body)) return []
  const detail = body.detail
  if (!Array.isArray(detail)) return []
  const messages: string[] = []
  for (const item of detail) {
    if (!isRecord(item)) continue
    const location = Array.isArray(item.loc) ? item.loc.map((part) => String(part)).join('.') : ''
    const message = typeof item.msg === 'string' ? item.msg : ''
    if (location || message) messages.push(location ? `${location}: ${message}` : message)
  }
  return messages
}
