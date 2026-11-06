import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

import { ApiError } from '../../src/api/errors'
import { parseKnowledgeCorporaResponse, parseKnowledgeSearchResponse } from '../../src/api/parse'
import { useKnowledgeSearch } from '../../src/composables/useKnowledgeSearch'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function chunk(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    id: 'kn:earthly_branch:yin',
    text: '寅 地支第三位，属木，主东北。',
    source: '渊海子平 · 论天干地支暗藏总诀',
    tags: ['earthly_branch', 'ziwei'],
    ...overrides,
  }
}

function searchBody(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    query: '紫微',
    include_evidence: false,
    chunks: [chunk()],
    ...overrides,
  }
}

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

describe('parseKnowledgeSearchResponse', () => {
  it('解析检索结果：来源/标签/片段', () => {
    const parsed = parseKnowledgeSearchResponse(searchBody())
    expect(parsed.query).toBe('紫微')
    expect(parsed.chunks).toHaveLength(1)
    expect(parsed.chunks[0]?.source).toContain('渊海子平')
    expect(parsed.chunks[0]?.tags).toEqual(['earthly_branch', 'ziwei'])
  })

  it('缺少可选 source/tags 时使用安全默认值', () => {
    const parsed = parseKnowledgeSearchResponse(
      searchBody({ chunks: [{ id: 'kn:x', text: '片段' }] }),
    )
    expect(parsed.chunks[0]?.source).toBe('')
    expect(parsed.chunks[0]?.tags).toBeUndefined()
  })

  it('非法结构抛 invalid_response', () => {
    expect(() => parseKnowledgeSearchResponse(searchBody({ chunks: 'nope' }))).toThrowError(
      ApiError,
    )
    expect(() =>
      parseKnowledgeSearchResponse(searchBody({ chunks: [chunk({ id: 1 })] })),
    ).toThrowError(ApiError)
    expect(() =>
      parseKnowledgeSearchResponse(searchBody({ chunks: [chunk({ source: 7 })] })),
    ).toThrowError(ApiError)
  })
})

describe('parseKnowledgeCorporaResponse', () => {
  it('解析语料库状态与计数', () => {
    const parsed = parseKnowledgeCorporaResponse({
      corpora: [
        { corpus_id: 'ziwei_corpus', status: 'frozen', version: '1.0.0', counts: { nodes: 102 } },
      ],
    })
    expect(parsed.corpora[0]?.status).toBe('frozen')
    expect(parsed.corpora[0]?.counts?.nodes).toBe(102)
  })

  it('计数非数字或 corpora 非数组时抛 invalid_response', () => {
    expect(() =>
      parseKnowledgeCorporaResponse({ corpora: [{ corpus_id: 'x', counts: { nodes: 'many' } }] }),
    ).toThrowError(ApiError)
    expect(() => parseKnowledgeCorporaResponse({ corpora: {} })).toThrowError(ApiError)
  })
})

describe('useKnowledgeSearch', () => {
  it('空查询不发起请求，只给出校验错误', async () => {
    const fetchMock = vi.fn(async () => jsonResponse(searchBody()))
    vi.stubGlobal('fetch', fetchMock)
    const search = useKnowledgeSearch(ref('http://backend'))
    search.query.value = '   '
    await search.submit()
    expect(search.status.value).toBe('error')
    expect(search.error.value).toContain('请输入查询关键词')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('非法条数不发起请求', async () => {
    const fetchMock = vi.fn(async () => jsonResponse(searchBody()))
    vi.stubGlobal('fetch', fetchMock)
    const search = useKnowledgeSearch(ref('http://backend'))
    search.query.value = '紫微'
    search.k.value = 0
    await search.submit()
    expect(search.status.value).toBe('error')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('loading → success，并回填后端 query', async () => {
    const pending = deferred<Response>()
    vi.stubGlobal('fetch', vi.fn(() => pending.promise))
    const search = useKnowledgeSearch(ref('http://backend'))
    search.query.value = '紫微'
    search.includeEvidence.value = true
    const running = search.submit()
    expect(search.status.value).toBe('loading')
    pending.resolve(jsonResponse(searchBody({ include_evidence: true })))
    await running
    expect(search.status.value).toBe('success')
    expect(search.chunks.value).toHaveLength(1)
    expect(search.lastQuery.value).toBe('紫微')
    expect(search.error.value).toBeNull()
  })

  it('空结果进入 empty 状态', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(searchBody({ chunks: [] }))))
    const search = useKnowledgeSearch(ref('http://backend'))
    search.query.value = '不存在的关键词zzz'
    await search.submit()
    expect(search.status.value).toBe('empty')
  })

  it('HTTP 错误进入 error 状态且不静默', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({ detail: 'boom', error: { kind: 'internal_error', message: 'boom' } }, 500),
      ),
    )
    const search = useKnowledgeSearch(ref('http://backend'))
    search.query.value = '紫微'
    await search.submit()
    expect(search.status.value).toBe('error')
    expect(search.error.value).toContain('internal_error')
    expect(search.chunks.value).toEqual([])
  })

  it('连续检索：中止旧请求，旧响应不覆盖新结果', async () => {
    const first = deferred<Response>()
    const second = deferred<Response>()
    const signals: AbortSignal[] = []
    let index = 0
    vi.stubGlobal(
      'fetch',
      vi.fn((_url: string, init?: RequestInit) => {
        if (init?.signal) signals.push(init.signal as AbortSignal)
        index += 1
        return index === 1 ? first.promise : second.promise
      }),
    )
    const search = useKnowledgeSearch(ref('http://backend'))
    search.query.value = '旧查询'
    const firstRun = search.submit()
    search.query.value = '新查询'
    const secondRun = search.submit()
    expect(signals[0]?.aborted).toBe(true)

    second.resolve(jsonResponse(searchBody({ query: '新查询', chunks: [chunk({ id: 'kn:new' })] })))
    await secondRun
    first.resolve(jsonResponse(searchBody({ query: '旧查询', chunks: [chunk({ id: 'kn:old' })] })))
    await firstRun

    expect(search.lastQuery.value).toBe('新查询')
    expect(search.chunks.value.map((item) => item.id)).toEqual(['kn:new'])
    expect(search.status.value).toBe('success')
  })

  it('cancel 中止请求并回到 idle', async () => {
    const pending = deferred<Response>()
    const signals: AbortSignal[] = []
    vi.stubGlobal(
      'fetch',
      vi.fn((_url: string, init?: RequestInit) => {
        if (init?.signal) signals.push(init.signal as AbortSignal)
        return pending.promise
      }),
    )
    const search = useKnowledgeSearch(ref('http://backend'))
    search.query.value = '紫微'
    const running = search.submit()
    search.cancel()
    expect(signals[0]?.aborted).toBe(true)
    expect(search.status.value).toBe('idle')
    pending.resolve(jsonResponse(searchBody()))
    await running
    expect(search.status.value).toBe('idle')
  })

  it('语料库加载成功与失败都有明确状态', async () => {
    const ok = useKnowledgeSearch(ref('http://backend'))
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({
          corpora: [{ corpus_id: 'ziwei_corpus', status: 'frozen', version: '1.0.0', counts: { nodes: 102 } }],
        }),
      ),
    )
    await ok.loadCorpora()
    expect(ok.corpora.value).toHaveLength(1)
    expect(ok.corporaError.value).toBeNull()

    const bad = useKnowledgeSearch(ref('http://backend'))
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse({ nope: true })))
    await bad.loadCorpora()
    expect(bad.corpora.value).toEqual([])
    expect(bad.corporaError.value).toContain('格式不符合契约')
  })
})
