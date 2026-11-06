import { afterEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

import { ApiError } from '../../src/api/errors'
import { parseAgentExplainResponse } from '../../src/api/parse'
import type { AnyOutput } from '../../src/api/types'
import { useAgentExplain } from '../../src/composables/useAgentExplain'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function explainBody(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    agent: 'bazi',
    explanation: '日主为辛金，生于午月；本解释来自确定性后备（未配置 LLM provider）。',
    provider: null,
    degraded: true,
    knowledge: [
      { id: 'kn:shen_sha:de_xiu', source: '三命通会 · 卷三·论德秀' },
      { id: 'kn:shen_sha:tai_ji_gui_ren', source: '三命通会 · 卷三·论太极贵' },
    ],
    evidence: {
      agent: 'bazi',
      input_hash: 'abc',
      result: { day_master: '辛' },
    },
    error: null,
    ...overrides,
  }
}

function baziOutput(): AnyOutput {
  return {
    request_id: 'agent-r1',
    agent: 'bazi',
    engine_version: '0.1.0',
    input_hash: 'abc',
    computed_at: '2026-01-01T00:00:00Z',
    confidence: { value: 0.95, method: 'rule_coverage', factors: {} },
    reasoning_trace: [],
    metadata: {},
    result: {
      day_master: '辛',
      day_master_element: '金',
      pillars: [],
      dayun: [],
      ten_gods_map: {},
      year_boundary: '1990-02-04T02:11:40Z',
      month_boundary: '芒种',
      gender_assumed: true,
    },
  }
}

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((res) => {
    resolve = res
  })
  return { promise, resolve }
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('parseAgentExplainResponse', () => {
  it('解析解释与知识引用（单域接口只返回 id/source）', () => {
    const parsed = parseAgentExplainResponse(explainBody())
    expect(parsed.agent).toBe('bazi')
    expect(parsed.explanation).toContain('辛金')
    expect(parsed.provider).toBeNull()
    expect(parsed.degraded).toBe(true)
    expect(parsed.knowledge).toHaveLength(2)
    expect(parsed.knowledge[0]?.id).toBe('kn:shen_sha:de_xiu')
    expect(parsed.knowledge[0]?.source).toContain('三命通会')
    expect(parsed.knowledge[0]?.text).toBeUndefined()
    expect(parsed.error).toBeNull()
  })

  it('允许空解释与空知识引用', () => {
    const parsed = parseAgentExplainResponse(explainBody({ explanation: '', knowledge: [] }))
    expect(parsed.explanation).toBe('')
    expect(parsed.knowledge).toEqual([])
  })

  it('来源缺失时解析为空串（由 UI 显示缺失，不补造）', () => {
    const parsed = parseAgentExplainResponse(
      explainBody({ knowledge: [{ id: 'kn:x' }] }),
    )
    expect(parsed.knowledge[0]?.source).toBe('')
  })

  it('解析 provider 错误记录', () => {
    const parsed = parseAgentExplainResponse(
      explainBody({
        provider: 'openai',
        degraded: true,
        error: { kind: 'provider_timeout', type: 'TimeoutError', message: 'boom', provider: 'openai' },
      }),
    )
    expect(parsed.provider).toBe('openai')
    expect(parsed.error?.kind).toBe('provider_timeout')
    expect(parsed.error?.provider).toBe('openai')
  })

  it('非法响应抛 invalid_response', () => {
    expect(() => parseAgentExplainResponse({ explanation: 'x' })).toThrowError(ApiError)
    expect(() =>
      parseAgentExplainResponse(explainBody({ knowledge: [{ source: 'x' }] })),
    ).toThrowError(ApiError)
    expect(() => parseAgentExplainResponse(explainBody({ knowledge: 'nope' }))).toThrowError(
      ApiError,
    )
    expect(() => parseAgentExplainResponse(explainBody({ explanation: 42 }))).toThrowError(ApiError)
  })
})

describe('useAgentExplain', () => {
  it('成功：loading → success，回填解释与知识引用', async () => {
    const pending = deferred<Response>()
    vi.stubGlobal('fetch', vi.fn(() => pending.promise))
    const explain = useAgentExplain(ref('http://backend'))
    const running = explain.explain('bazi', baziOutput())
    expect(explain.status.value).toBe('loading')
    pending.resolve(jsonResponse(explainBody()))
    await running
    expect(explain.status.value).toBe('success')
    expect(explain.result.value?.agent).toBe('bazi')
    expect(explain.result.value?.knowledge).toHaveLength(2)
    expect(explain.error.value).toBeNull()
  })

  it('HTTP 422 错误展示后端字段信息', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse(
          {
            detail: [{ loc: ['body', 'output'], msg: 'field required' }],
            error: { kind: 'invalid_request', message: 'request validation failed' },
          },
          422,
        ),
      ),
    )
    const explain = useAgentExplain(ref('http://backend'))
    await explain.explain('bazi', baziOutput())
    expect(explain.status.value).toBe('error')
    expect(explain.error.value).toContain('参数未通过后端校验')
    expect(explain.error.value).toContain('output')
    expect(explain.result.value).toBeNull()
  })

  it('失败时不清空已展示的解释（重新解释失败仍保留旧解释）', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(explainBody())))
    const explain = useAgentExplain(ref('http://backend'))
    await explain.explain('bazi', baziOutput())
    expect(explain.result.value).not.toBeNull()

    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )
    await explain.explain('bazi', baziOutput())
    expect(explain.status.value).toBe('error')
    expect(explain.result.value?.agent).toBe('bazi')
  })

  it('重复点击只发出一次请求', async () => {
    const pending = deferred<Response>()
    const handler = vi.fn(() => pending.promise)
    vi.stubGlobal('fetch', handler)
    const explain = useAgentExplain(ref('http://backend'))
    const first = explain.explain('bazi', baziOutput())
    await explain.explain('bazi', baziOutput())
    expect(handler).toHaveBeenCalledTimes(1)
    pending.resolve(jsonResponse(explainBody()))
    await first
    expect(explain.status.value).toBe('success')
  })

  it('取消请求回到 idle，迟到响应不覆盖', async () => {
    const pending = deferred<Response>()
    vi.stubGlobal('fetch', vi.fn(() => pending.promise))
    const explain = useAgentExplain(ref('http://backend'))
    const running = explain.explain('bazi', baziOutput())
    explain.cancel()
    expect(explain.status.value).toBe('idle')
    pending.resolve(jsonResponse(explainBody()))
    await running
    expect(explain.status.value).toBe('idle')
    expect(explain.result.value).toBeNull()
  })

  it('切换结果（reset）后旧解释响应不落到新结果', async () => {
    const pending = deferred<Response>()
    vi.stubGlobal('fetch', vi.fn(() => pending.promise))
    const explain = useAgentExplain(ref('http://backend'))
    const running = explain.explain('bazi', baziOutput())
    explain.reset()
    pending.resolve(jsonResponse(explainBody()))
    await running
    expect(explain.status.value).toBe('idle')
    expect(explain.result.value).toBeNull()
  })

  it('后端返回的解释领域与请求不一致时拒绝展示', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(explainBody({ agent: 'ziwei' }))))
    const explain = useAgentExplain(ref('http://backend'))
    await explain.explain('bazi', baziOutput())
    expect(explain.status.value).toBe('error')
    expect(explain.error.value).toContain('不一致')
    expect(explain.result.value).toBeNull()
  })

  it('解释失败不修改传入的计算结果对象', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )
    const output = baziOutput()
    const explain = useAgentExplain(ref('http://backend'))
    await explain.explain('bazi', output)
    expect(output.request_id).toBe('agent-r1')
    expect(output.result).toMatchObject({ day_master: '辛' })
  })
})
