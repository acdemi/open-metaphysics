import { afterEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

import { ApiError } from '../../src/api/errors'
import {
  parseAgentComputeResponse,
  parseAgentListResponse,
  parseAgentSchemaResponse,
} from '../../src/api/parse'
import { useAgentCompute } from '../../src/composables/useAgentCompute'
import {
  buildAgentPayload,
  castsError,
  draftFromSchema,
  emptyDraft,
  validateDraft,
} from '../../src/utils/agentForm'
import { describeField, enumValues, fieldShape, readInputSchemaFromResponse } from '../../src/utils/agentSchema'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function schemaFixture(domain: 'bazi' | 'liuyao' = 'bazi'): Record<string, unknown> {
  const properties: Record<string, unknown> = {
    request_id: { title: 'Request Id', type: 'string' },
    born_at: { title: 'Born At', type: 'string' },
    gender: { $ref: '#/$defs/Gender', default: 'unknown' },
    question: { anyOf: [{ type: 'string' }, { type: 'null' }], default: null, title: 'Question' },
    locale: { default: 'zh-CN', title: 'Locale', type: 'string' },
    seed: {
      anyOf: [{ type: 'integer' }, { type: 'null' }],
      default: null,
      title: 'Seed',
    },
    born_location: {
      anyOf: [{ $ref: '#/$defs/GeoPoint' }, { type: 'null' }],
      default: null,
      title: 'Born Location',
    },
  }
  if (domain === 'bazi') {
    properties.dayun_count = { default: 8, title: 'Dayun Count', type: 'integer' }
  } else {
    properties.casts = {
      anyOf: [{ items: { type: 'integer' }, type: 'array' }, { type: 'null' }],
      default: null,
      title: 'Casts',
    }
  }
  return {
    name: domain,
    engine_version: '0.1.0',
    input_schema: {
      $defs: {
        Gender: { enum: ['male', 'female', 'unknown'], title: 'Gender', type: 'string' },
        GeoPoint: {
          properties: {
            latitude: { title: 'Latitude', type: 'number' },
            longitude: { title: 'Longitude', type: 'number' },
            elevation_m: { anyOf: [{ type: 'number' }, { type: 'null' }], default: null },
            timezone: { anyOf: [{ type: 'string' }, { type: 'null' }], default: null },
          },
          required: ['latitude', 'longitude'],
          title: 'GeoPoint',
          type: 'object',
        },
      },
      properties,
      required: ['request_id', 'born_at'],
      title: `${domain}Input`,
      type: 'object',
    },
    output_schema: { type: 'object' },
  }
}

function baziOutput(): Record<string, unknown> {
  return {
    request_id: 'agent-r1',
    agent: 'bazi',
    engine_version: '0.1.0',
    input_hash: 'abc',
    computed_at: '2026-01-01T00:00:00Z',
    confidence: { value: 0.95, method: 'rule_coverage', factors: {} },
    reasoning_trace: [
      { step: 1, rule_ref: 'bazi.year_pillar', description: 'sexagenary year', inputs: {}, outputs: {} },
    ],
    metadata: { deterministic: true },
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

function stubAgentRoutes(options: {
  compute?: (url: string, init?: RequestInit) => Response | Promise<Response>
  schema?: (name: string) => Record<string, unknown>
} = {}) {
  const handler = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.endsWith('/agents')) {
      return jsonResponse({
        agents: [
          { name: 'bazi', engine_version: '0.1.0' },
          { name: 'liuyao', engine_version: '0.1.0' },
          { name: 'qimen', engine_version: '0.3.0' },
          { name: 'ziwei', engine_version: '0.3.0' },
        ],
      })
    }
    if (url.includes('/schema')) {
      const match = /\/agents\/([^/]+)\/schema/.exec(url)
      const name = match?.[1] ?? 'bazi'
      return jsonResponse(options.schema?.(name) ?? schemaFixture(name === 'liuyao' ? 'liuyao' : 'bazi'))
    }
    if (options.compute) return options.compute(url, init)
    return jsonResponse(baziOutput())
  })
  vi.stubGlobal('fetch', handler)
  return handler
}

async function waitForSchema(compute: ReturnType<typeof useAgentCompute>): Promise<void> {
  await vi.waitFor(() => {
    if (compute.schema.value === null) throw new Error('schema not loaded')
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('agent API parsing', () => {
  it('解析 Agent 列表', () => {
    const parsed = parseAgentListResponse({
      agents: [
        { name: 'bazi', engine_version: '0.1.0' },
        { name: 'ziwei', engine_version: '0.3.0' },
      ],
    })
    expect(parsed.agents.map((item) => item.name)).toEqual(['bazi', 'ziwei'])
  })

  it('解析 Schema 信封并暴露 input_schema', () => {
    const parsed = parseAgentSchemaResponse(schemaFixture('bazi'))
    expect(parsed.name).toBe('bazi')
    const schema = readInputSchemaFromResponse(parsed)
    expect(schema?.required).toEqual(['request_id', 'born_at'])
    expect(enumValues(schema!, 'gender')).toEqual(['male', 'female', 'unknown'])
  })

  it('Schema 缺少 properties 时抛 invalid_response', () => {
    expect(() =>
      parseAgentSchemaResponse({ name: 'bazi', engine_version: '0.1.0', input_schema: {}, output_schema: {} }),
    ).toThrowError(ApiError)
  })

  it('解析单域 Compute 响应（与 Orchestration outputs[] 同一信封）', () => {
    const parsed = parseAgentComputeResponse(baziOutput())
    expect(parsed.agent).toBe('bazi')
    expect(parsed.result).toBeTruthy()
  })

  it('Compute 响应缺少必需信封字段时抛 invalid_response', () => {
    expect(() => parseAgentComputeResponse({ request_id: 'x', agent: 'bazi' })).toThrowError(ApiError)
  })
})

describe('schema 字段描述', () => {
  it('合并 anyOf 可空分支并解析枚举 $ref', () => {
    const schema = readInputSchemaFromResponse(parseAgentSchemaResponse(schemaFixture('bazi')))
    const seed = schema ? describeField(schema.properties.seed ?? {}) : null
    expect(seed?.type).toBe('integer')
    expect(seed?.nullable).toBe(true)
    expect(seed?.defaultValue).toBeNull()

    const gender = schema ? fieldShape(schema, 'gender') : null
    expect(gender?.enumValues).toEqual(['male', 'female', 'unknown'])
  })
})

describe('agent 表单校验与 payload', () => {
  it('默认草稿使用后端 schema 的默认值', () => {
    const schema = readInputSchemaFromResponse(parseAgentSchemaResponse(schemaFixture('bazi')))
    const draft = draftFromSchema(schema)
    expect(draft.gender).toBe('unknown')
    expect(draft.dayunCount).toBe('8')
  })

  it('出生时刻非法时报错', () => {
    const draft = emptyDraft()
    draft.date = '1990-02-30'
    const errors = validateDraft(null, draft)
    expect(errors.date).toContain('不存在')
  })

  it('六爻 casts 必须是 6 个 6/7/8/9', () => {
    expect(castsError('7,8,9,6,7,8')).toBeNull()
    expect(castsError('7,8,9')).toContain('6 个')
    expect(castsError('7,8,9,6,7,0')).toContain('6、7、8 或 9')
  })

  it('紫微农历字段必须成对且范围合法', () => {
    const draft = emptyDraft()
    draft.lunarMonth = '5'
    expect(validateDraft(null, draft).lunar_month).toContain('同时填写')
    draft.lunarDay = '40'
    expect(validateDraft(null, draft).lunar_day).toContain('1–30')
  })

  it('构造 payload：只含 schema 声明字段并带默认值', () => {
    const schema = readInputSchemaFromResponse(parseAgentSchemaResponse(schemaFixture('bazi')))
    const draft = emptyDraft()
    draft.question = '今年如何'
    draft.seed = '42'
    const { payload, errors } = buildAgentPayload(draft, 'agent-r1', schema)
    expect(errors).toEqual({})
    expect(payload.request_id).toBe('agent-r1')
    // 1990 年 Asia/Shanghai 处于夏令时（UTC+9），与仓库既有换算一致
    expect(payload.born_at).toBe('1990-06-15T08:30:00+09:00')
    expect(payload.gender).toBe('unknown')
    expect(payload.question).toBe('今年如何')
    expect(payload.seed).toBe(42)
    expect(payload.dayun_count).toBe(8)
    expect(payload).not.toHaveProperty('locale')
    expect(payload).not.toHaveProperty('born_location')
  })

  it('六爻 payload 仅在填写时发送 casts', () => {
    const schema = readInputSchemaFromResponse(parseAgentSchemaResponse(schemaFixture('liuyao')))
    const empty = buildAgentPayload(emptyDraft(), 'r1', schema)
    expect(empty.payload).not.toHaveProperty('casts')
    const draft = emptyDraft()
    draft.casts = '7,8,9,6,7,8'
    const filled = buildAgentPayload(draft, 'r1', schema)
    expect(filled.payload.casts).toEqual([7, 8, 9, 6, 7, 8])
  })
})

describe('useAgentCompute', () => {
  it('init 加载 Agent 列表与 bazi schema，并按默认值初始化表单', async () => {
    stubAgentRoutes()
    const compute = useAgentCompute(ref('http://backend'))
    await compute.init()
    await waitForSchema(compute)
    expect(compute.agents.value).toHaveLength(4)
    expect(compute.selected.value).toBe('bazi')
    expect(compute.draft.dayunCount).toBe('8')
    expect(compute.status.value).toBe('idle')
  })

  it('提交成功：loading → success，结果属于所选领域', async () => {
    stubAgentRoutes()
    const compute = useAgentCompute(ref('http://backend'))
    await compute.init()
    await waitForSchema(compute)
    await compute.submit()
    expect(compute.status.value).toBe('success')
    expect(compute.result.value?.agent).toBe('bazi')
    expect(compute.elapsedMs.value).toBeGreaterThanOrEqual(0)
  })

  it('后端 422 错误展示字段级信息且保留输入', async () => {
    stubAgentRoutes({
      compute: async () =>
        jsonResponse(
          {
            detail: [{ loc: ['body', 'casts'], msg: 'each cast value must be 6,7,8 or 9' }],
            error: { kind: 'invalid_request', message: 'request validation failed' },
          },
          422,
        ),
    })
    const compute = useAgentCompute(ref('http://backend'))
    compute.draft.casts = ''
    await compute.init()
    await waitForSchema(compute)
    compute.draft.date = '1990-06-15'
    await compute.submit()
    expect(compute.status.value).toBe('error')
    expect(compute.error.value).toContain('参数未通过后端校验')
    expect(compute.error.value).toContain('casts')
    expect(compute.draft.date).toBe('1990-06-15')
  })

  it('重复提交只发出一次 compute 请求', async () => {
    let release!: (response: Response) => void
    const pending = new Promise<Response>((resolve) => {
      release = resolve
    })
    const handler = stubAgentRoutes({ compute: () => pending })
    const compute = useAgentCompute(ref('http://backend'))
    await compute.init()
    await waitForSchema(compute)
    const first = compute.submit()
    await compute.submit()
    const computeCalls = handler.mock.calls.filter(([url]) => String(url).includes('/compute')).length
    expect(computeCalls).toBe(1)
    release(jsonResponse(baziOutput()))
    await first
    expect(compute.status.value).toBe('success')
  })

  it('cancel 中止在途计算并回到 idle', async () => {
    let release!: (response: Response) => void
    const pending = new Promise<Response>((resolve) => {
      release = resolve
    })
    stubAgentRoutes({ compute: () => pending })
    const compute = useAgentCompute(ref('http://backend'))
    await compute.init()
    await waitForSchema(compute)
    const running = compute.submit()
    compute.cancel()
    expect(compute.status.value).toBe('idle')
    release(jsonResponse(baziOutput()))
    await running
    expect(compute.status.value).toBe('idle')
  })

  it('切换领域后旧计算响应不覆盖新领域', async () => {
    let release!: (response: Response) => void
    const pending = new Promise<Response>((resolve) => {
      release = resolve
    })
    stubAgentRoutes({ compute: () => pending })
    const compute = useAgentCompute(ref('http://backend'))
    await compute.init()
    await waitForSchema(compute)
    const running = compute.submit()
    compute.selectAgent('liuyao')
    await waitForSchema(compute)
    release(jsonResponse(baziOutput()))
    await running
    expect(compute.selected.value).toBe('liuyao')
    expect(compute.result.value).toBeNull()
    expect(compute.status.value).toBe('idle')
  })

  it('后端返回的领域与选择不一致时拒绝展示', async () => {
    stubAgentRoutes({
      compute: async () =>
        jsonResponse({
          ...baziOutput(),
          agent: 'ziwei',
          result: {
            fate_palace_index: 0,
            body_palace_index: 0,
            yin_yang: '阳',
            wuxing_ju: '水二局',
            palaces: [],
            calendar_note: null,
          },
        }),
    })
    const compute = useAgentCompute(ref('http://backend'))
    await compute.init()
    await waitForSchema(compute)
    await compute.submit()
    expect(compute.status.value).toBe('error')
    expect(compute.error.value).toContain('不一致')
    expect(compute.result.value).toBeNull()
  })
})
