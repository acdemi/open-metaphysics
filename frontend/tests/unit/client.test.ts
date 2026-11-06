import { afterEach, describe, expect, it, vi } from 'vitest'

import { fetchHealth, requestJson } from '../../src/api/client'
import { ApiError } from '../../src/api/errors'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('requestJson', () => {
  it('把 HTTP 错误归一为 ApiError，并保留后端 error.kind / status', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse(
          {
            detail: 'x',
            error: { kind: 'invalid_request', message: 'request validation failed', fields: [['born_at']] },
          },
          422,
        ),
      ),
    )
    const error = await requestJson('http://backend', '/orchestrate', { method: 'POST', body: {} }).catch(
      (caught: unknown) => caught,
    )
    expect(error).toBeInstanceOf(ApiError)
    if (!(error instanceof ApiError)) return
    expect(error.transport).toBe('http')
    expect(error.kind).toBe('invalid_request')
    expect(error.status).toBe(422)
  })

  it('网络失败归一为 transport=network', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )
    const error = await requestJson('http://backend', '/health').catch((caught: unknown) => caught)
    expect(error).toBeInstanceOf(ApiError)
    if (error instanceof ApiError) expect(error.transport).toBe('network')
  })

  it('取消信号归一为 cancelled', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (_url: string, init?: RequestInit) => {
        if (init?.signal?.aborted) {
          throw new DOMException('The operation was aborted.', 'AbortError')
        }
        return jsonResponse({ status: 'ok', agents: [] })
      }),
    )
    const controller = new AbortController()
    controller.abort()
    const error = await requestJson('http://backend', '/orchestrate', {
      method: 'POST',
      body: {},
      signal: controller.signal,
    }).catch((caught: unknown) => caught)
    expect(error).toBeInstanceOf(ApiError)
    if (error instanceof ApiError) expect(error.kind).toBe('cancelled')
  })
})

describe('fetchHealth', () => {
  it('解析健康检查响应', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ status: 'ok', agents: ['bazi', 'ziwei'] })))
    const health = await fetchHealth('http://backend')
    expect(health.data.status).toBe('ok')
    expect(health.data.agents).toEqual(['bazi', 'ziwei'])
  })

  it('结构不符时抛 invalid_response', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ status: 'ok' })))
    const error = await fetchHealth('http://backend').catch((caught: unknown) => caught)
    expect(error).toBeInstanceOf(ApiError)
    if (error instanceof ApiError) expect(error.kind).toBe('invalid_response')
  })
})
