/* HTTP 客户端：只调用仓库既有的 FastAPI 端点，所有响应在边界处解析。 */

import { ApiError, asErrorMessage, backendErrorBody } from './errors'
import { parseHealthResponse, parseOrchestrationResponse } from './parse'
import type { HealthResponse, OrchestrationRequest, OrchestrationResponse, Timed } from './types'

export const DEFAULT_TIMEOUT_MS = 90_000

export interface JsonRequestOptions {
  method?: 'GET' | 'POST'
  body?: unknown
  signal?: AbortSignal | null
  timeoutMs?: number
}

export interface RawResponse {
  data: unknown
  status: number
  elapsedMs: number
}

function trimBase(base: string): string {
  return base.trim().replace(/\/+$/, '')
}

async function readBody(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text) as unknown
  } catch {
    return text.slice(0, 2000)
  }
}

/** 发送 JSON 请求。成功返回原始 JSON（未解析），失败统一抛 ApiError。 */
export async function requestJson(
  base: string,
  path: string,
  options: JsonRequestOptions = {},
): Promise<RawResponse> {
  const { method = 'GET', body, signal = null, timeoutMs = DEFAULT_TIMEOUT_MS } = options
  const controller = new AbortController()
  let timedOut = false
  const timer = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, timeoutMs)
  const onExternalAbort = (): void => controller.abort()
  if (signal) {
    if (signal.aborted) controller.abort()
    else signal.addEventListener('abort', onExternalAbort, { once: true })
  }

  const started = performance.now()
  try {
    const headers: Record<string, string> = { Accept: 'application/json' }
    const init: RequestInit = { method, cache: 'no-store', headers, signal: controller.signal }
    if (body !== undefined) {
      headers['Content-Type'] = 'application/json'
      init.body = JSON.stringify(body)
    }
    const response = await fetch(`${trimBase(base)}${path}`, init)
    const elapsedMs = Math.round(performance.now() - started)
    const data = await readBody(response)
    if (!response.ok) {
      const backend = backendErrorBody(data)
      throw new ApiError({
        transport: 'http',
        status: response.status,
        kind: backend?.kind ?? `http_${response.status}`,
        message: backend?.message ?? `HTTP ${response.status}`,
        body: data,
        elapsedMs,
      })
    }
    return { data, status: response.status, elapsedMs }
  } catch (error) {
    if (error instanceof ApiError) throw error
    const elapsedMs = Math.round(performance.now() - started)
    const name = error instanceof Error ? error.name : ''
    if (name === 'AbortError') {
      if (timedOut) {
        throw new ApiError({
          transport: 'timeout',
          message: `请求超时（${Math.round(timeoutMs / 1000)} 秒）`,
          elapsedMs,
        })
      }
      throw new ApiError({ transport: 'cancelled', message: '请求已取消', elapsedMs })
    }
    throw new ApiError({
      transport: 'network',
      message: asErrorMessage(error) || '网络请求失败',
      elapsedMs,
    })
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', onExternalAbort)
  }
}

/** GET /health */
export async function fetchHealth(base: string): Promise<Timed<HealthResponse>> {
  const response = await requestJson(base, '/health', { timeoutMs: 8_000 })
  return { data: parseHealthResponse(response.data), elapsedMs: response.elapsedMs }
}

/** POST /orchestrate —— 页面唯一的分析入口。 */
export async function postOrchestrate(
  base: string,
  request: OrchestrationRequest,
  options: { signal?: AbortSignal | null } = {},
): Promise<Timed<OrchestrationResponse>> {
  const response = await requestJson(base, '/orchestrate', {
    method: 'POST',
    body: request,
    signal: options.signal ?? null,
  })
  return { data: parseOrchestrationResponse(response.data), elapsedMs: response.elapsedMs }
}

/** GET /sessions/{request_id}：返回后端原始会话结构，仅用于展示。 */
export async function fetchSession(base: string, requestId: string): Promise<Timed<unknown>> {
  const response = await requestJson(base, `/sessions/${encodeURIComponent(requestId)}`, {
    timeoutMs: 10_000,
  })
  return { data: response.data, elapsedMs: response.elapsedMs }
}

/** GET /traces/{request_id}：返回后端原始追踪结构，仅用于展示。 */
export async function fetchTraces(base: string, requestId: string): Promise<Timed<unknown>> {
  const response = await requestJson(base, `/traces/${encodeURIComponent(requestId)}`, {
    timeoutMs: 10_000,
  })
  return { data: response.data, elapsedMs: response.elapsedMs }
}

/**
 * 用 no-cors 探测后端是否可达：能拿到 opaque 响应说明 TCP/HTTP 可达，
 * 从而把「跨域被浏览器拦截」与「后端未启动」区分开。
 */
export async function probeReachable(base: string, timeoutMs = 5_000): Promise<boolean> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    await fetch(`${trimBase(base)}/health`, {
      mode: 'no-cors',
      cache: 'no-store',
      signal: controller.signal,
    })
    return true
  } catch {
    return false
  } finally {
    clearTimeout(timer)
  }
}
