import { ref } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '../../src/api/errors'
import { parseSessionList, parseStoredSession } from '../../src/api/parse'
import type { StoredSession } from '../../src/api/types'
import { useAnalysis } from '../../src/composables/useAnalysis'
import { useSessionHistory } from '../../src/composables/useSessionHistory'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

function baziOutput(): Record<string, unknown> {
  return {
    request_id: 'hist-1',
    agent: 'bazi',
    engine_version: '0.1.0',
    input_hash: 'abc',
    computed_at: '2026-01-01T00:00:00Z',
    confidence: { value: 0.95, method: 'rule_coverage', factors: {} },
    reasoning_trace: [
      { step: 1, rule_ref: 'bazi.year_pillar', description: 'sexagenary year', inputs: {}, outputs: {} },
    ],
    metadata: {},
    result: {
      day_master: '辛',
      day_master_element: '金',
      pillars: [],
      dayun: [],
      ten_gods_map: {},
      year_boundary: '1990-02-04T02:11:40Z',
      month_boundary: '芒种',
      gender_assumed: false,
    },
  }
}

function orchestration(): Record<string, unknown> {
  return {
    request_id: 'hist-1',
    outputs: [baziOutput()],
    consensus: null,
    explanation: {},
    explanation_detail: {},
    errors: [],
  }
}

function storedSession(overrides: Record<string, unknown> = {}): StoredSession {
  return {
    request_id: 'hist-1',
    created_at: '2026-10-30T05:00:00+00:00',
    request: {
      request_id: 'hist-1',
      payload: { request_id: 'hist-1', born_at: '1990-06-15T08:30:00+09:00' },
      agents: ['bazi'],
      explain: true,
    },
    response: orchestration(),
    ...overrides,
  }
}

describe('parseSessionList', () => {
  it('解析会话列表', () => {
    const parsed = parseSessionList({
      sessions: [
        { request_id: 'a', created_at: '2026-10-30T05:00:00+00:00' },
        { request_id: 'b', created_at: '2026-10-30T05:01:00+00:00' },
      ],
    })
    expect(parsed.sessions.map((item) => item.request_id)).toEqual(['a', 'b'])
  })

  it('解析分页信封（total/limit/offset 为可选字段）', () => {
    const parsed = parseSessionList({
      sessions: [{ request_id: 'a', created_at: '2026-10-30T05:00:00+00:00' }],
      total: 7,
      limit: 1,
      offset: 3,
    })
    expect(parsed.total).toBe(7)
    expect(parsed.limit).toBe(1)
    expect(parsed.offset).toBe(3)
  })

  it('字段缺失抛 invalid_response', () => {
    expect(() => parseSessionList({ sessions: [{ request_id: 'a' }] })).toThrowError(ApiError)
  })
})

describe('parseStoredSession', () => {
  it('解析会话信封（request/response 保留原始 JSON）', () => {
    const parsed = parseStoredSession(storedSession())
    expect(parsed.request_id).toBe('hist-1')
    expect(parsed.created_at).toContain('2026-10-30')
    expect(parsed.request).toMatchObject({ request_id: 'hist-1' })
    expect(parsed.response).toMatchObject({ request_id: 'hist-1' })
  })

  it('response 不是对象时抛 invalid_response', () => {
    expect(() => parseStoredSession(storedSession({ response: 'not-an-object' }))).toThrowError(
      ApiError,
    )
  })
})

describe('useAnalysis.restoreSession', () => {
  it('用合法会话恢复结果视图并标记历史来源', () => {
    const analysis = useAnalysis(ref('http://127.0.0.1:8000'))
    const outcome = analysis.restoreSession(storedSession())

    expect(outcome.ok).toBe(true)
    expect(analysis.view.value).toBe('results')
    expect(analysis.result.value?.request_id).toBe('hist-1')
    expect(analysis.result.value?.outputs[0]?.agent).toBe('bazi')
    expect(analysis.restoredFrom.value).toMatchObject({ request_id: 'hist-1' })
    expect(analysis.restoredRequest.value).toMatchObject({ request_id: 'hist-1' })
    expect(analysis.lastPayload.value).toBeNull()
    expect(analysis.elapsedMs.value).toBe(0)
    expect(analysis.activeTab.value).toBe('calculation')
  })

  it('无法还原的 response 返回失败原因且不污染当前视图', () => {
    const analysis = useAnalysis(ref('http://127.0.0.1:8000'))
    const broken = storedSession({ response: { request_id: 'hist-1' } })

    const outcome = analysis.restoreSession(broken)

    expect(outcome.ok).toBe(false)
    if (!outcome.ok) expect(outcome.message).toContain('后端响应不符合契约')
    expect(analysis.view.value).toBe('empty')
    expect(analysis.result.value).toBeNull()
    expect(analysis.restoredFrom.value).toBeNull()
  })

  it('重置演示会清除历史来源标记', () => {
    const analysis = useAnalysis(ref('http://127.0.0.1:8000'))
    analysis.restoreSession(storedSession())
    analysis.resetDemo()

    expect(analysis.view.value).toBe('empty')
    expect(analysis.restoredFrom.value).toBeNull()
    expect(analysis.restoredRequest.value).toBeNull()
  })
})

describe('useSessionHistory', () => {
  it('加载列表：loading 状态翻转，成功后写入 sessions', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({
          sessions: [{ request_id: 'hist-1', created_at: '2026-10-30T05:00:00+00:00' }],
        }),
      ),
    )
    const history = useSessionHistory(ref('http://backend'))
    const pending = history.refresh()
    expect(history.loading.value).toBe(true)
    await pending
    expect(history.loading.value).toBe(false)
    expect(history.error.value).toBeNull()
    expect(history.sessions.value).toHaveLength(1)
  })

  it('列表响应结构不符：记录可见错误，不静默吞掉', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ nope: true })))
    const history = useSessionHistory(ref('http://backend'))
    await history.refresh()
    expect(history.sessions.value).toEqual([])
    expect(history.error.value).toContain('会话响应格式不符合契约')
  })

  it('分页请求带 limit/offset，并记录 total', async () => {
    const fetchMock = vi.fn(async (_url: string, _init?: RequestInit) =>
      jsonResponse({
        sessions: [{ request_id: 'hist-2', created_at: '2026-10-30T05:02:00+00:00' }],
        total: 9,
        limit: 50,
        offset: 0,
      }),
    )
    vi.stubGlobal('fetch', fetchMock)
    const history = useSessionHistory(ref('http://backend'))
    await history.refresh()
    expect(history.sessions.value.map((item) => item.request_id)).toEqual(['hist-2'])
    expect(history.total.value).toBe(9)
    const url = String(fetchMock.mock.calls[0]?.[0] ?? '')
    expect(url).toContain('/sessions?limit=50&offset=0')
  })

  it('读取会话成功返回会话；响应结构不符时设置 restoreError', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(storedSession())))
    const history = useSessionHistory(ref('http://backend'))
    const session = await history.restore('hist-1')
    expect(session?.request_id).toBe('hist-1')
    expect(history.restoreError.value).toBeNull()

    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ request_id: 'hist-1' })))
    const broken = await history.restore('hist-1')
    expect(broken).toBeNull()
    expect(history.restoreError.value).toContain('会话响应格式不符合契约')
  })

  it('404 会话映射为明确的「已不存在」提示', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse(
          { detail: 'session not found', error: { kind: 'not_found', message: 'session not found' } },
          404,
        ),
      ),
    )
    const history = useSessionHistory(ref('http://backend'))
    const session = await history.restore('gone')
    expect(session).toBeNull()
    expect(history.restoreError.value).toContain('已不存在')
  })
})
