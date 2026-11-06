import { describe, expect, it } from 'vitest'

import { parseAgentSchemaResponse } from '../src/api/parse'
import {
  BORN_LOCATION_HINT,
  buildAgentPayload,
  emptyDraft,
  validateDraft,
} from '../src/utils/agentForm'
import { readInputSchemaFromResponse } from '../src/utils/agentSchema'

/**
 * P2.1 / P2.5: born_location (GeoPoint) wiring in the single-domain compute form.
 *
 * `born_at` keeps its H5 semantics (offset derived from the selected IANA
 * timezone); `born_location.timezone` stays an IANA name for true-solar-time
 * correction on the backend.
 */
function schemaFor(withBornLocation = true): Record<string, unknown> {
  const properties: Record<string, unknown> = {
    request_id: { title: 'Request Id', type: 'string' },
    born_at: { title: 'Born At', type: 'string' },
    gender: {
      $ref: '#/$defs/Gender',
      default: 'unknown',
    },
  }
  if (withBornLocation) {
    properties.born_location = {
      anyOf: [{ $ref: '#/$defs/GeoPoint' }, { type: 'null' }],
      default: null,
      title: 'Born Location',
    }
  }
  return {
    name: 'bazi',
    engine_version: '0.1.0',
    input_schema: {
      $defs: {
        Gender: { enum: ['male', 'female', 'unknown'], title: 'Gender', type: 'string' },
        GeoPoint: {
          properties: {
            latitude: { title: 'Latitude', type: 'number' },
            longitude: { title: 'Longitude', type: 'number' },
            timezone: { anyOf: [{ type: 'string' }, { type: 'null' }], default: null },
          },
          required: ['latitude', 'longitude'],
          title: 'GeoPoint',
          type: 'object',
        },
      },
      properties,
      required: ['request_id', 'born_at'],
      title: 'BaziInput',
      type: 'object',
    },
    output_schema: { type: 'object' },
  }
}

function readSchema(withBornLocation = true) {
  return readInputSchemaFromResponse(parseAgentSchemaResponse(schemaFor(withBornLocation)))
}

describe('born_location payload', () => {
  it('经纬度成对时注入 GeoPoint，且不改变 born_at 生成逻辑', () => {
    const schema = readSchema()
    const draft = emptyDraft()
    draft.latitude = '31.2304'
    draft.longitude = '121.4737'
    const { payload, errors } = buildAgentPayload(draft, 'loc-1', schema)
    expect(errors).toEqual({})
    expect(payload.born_location).toEqual({
      latitude: 31.2304,
      longitude: 121.4737,
      timezone: 'Asia/Shanghai',
    })
    // 1990 年上海夏令时 UTC+9（H5 既有换算）
    expect(payload.born_at).toBe('1990-06-15T08:30:00+09:00')
  })

  it('经纬度留空时 payload 不含 born_location', () => {
    const { payload, errors } = buildAgentPayload(emptyDraft(), 'loc-2', readSchema())
    expect(errors).toEqual({})
    expect(payload).not.toHaveProperty('born_location')
  })

  it('schema 未声明 born_location 时不注入 payload', () => {
    const draft = emptyDraft()
    draft.latitude = '31.2304'
    draft.longitude = '121.4737'
    const { payload, errors } = buildAgentPayload(draft, 'loc-3', readSchema(false))
    expect(errors).toEqual({})
    expect(payload).not.toHaveProperty('born_location')
  })
})

describe('born_location 校验', () => {
  it('纬度过界（>90 / <-90）与经度过界（>180 / <-180）被拒绝', () => {
    const schema = readSchema()
    const draft = emptyDraft()
    draft.latitude = '90.1'
    draft.longitude = '121'
    expect(validateDraft(schema, draft).latitude).toContain('-90 到 90')

    draft.latitude = '-90'
    draft.longitude = '180.1'
    expect(validateDraft(schema, draft).longitude).toContain('-180 到 180')

    draft.longitude = '180'
    expect(validateDraft(schema, draft)).toEqual({})

    draft.latitude = 'abc'
    expect(validateDraft(schema, draft).latitude).toContain('-90 到 90')
  })

  it('只填一半时要求经纬度成对，且不构造 payload', () => {
    const schema = readSchema()
    const draft = emptyDraft()
    draft.latitude = '31.2304'
    const missingLongitude = validateDraft(schema, draft)
    expect(missingLongitude.latitude).toContain('同时填写')
    expect(missingLongitude.longitude).toContain('同时填写')
    expect(buildAgentPayload(draft, 'loc-4', schema).payload).toEqual({})

    draft.latitude = ''
    draft.longitude = '121.4737'
    const missingLatitude = validateDraft(schema, draft)
    expect(missingLatitude.latitude).toContain('同时填写')
    expect(missingLatitude.longitude).toContain('同时填写')
  })
})

describe('born_at / timezone 语义（H5）', () => {
  it('born_at 偏移跟随 IANA 时区，born_location.timezone 保持 IANA 名称', () => {
    const draft = emptyDraft()
    draft.date = '1990-01-15'
    draft.time = '08:30'
    draft.timezone = 'America/New_York'
    draft.latitude = '40.7128'
    draft.longitude = '-74.0060'
    const { payload } = buildAgentPayload(draft, 'loc-5', readSchema())
    expect(payload.born_at).toBe('1990-01-15T08:30:00-05:00')
    expect((payload.born_location as { timezone: string }).timezone).toBe('America/New_York')
  })

  it('表单提示明确 IANA 时区与真太阳时语义', () => {
    expect(BORN_LOCATION_HINT).toContain('IANA 时区')
    expect(BORN_LOCATION_HINT).toContain('真太阳时')
    expect(BORN_LOCATION_HINT).toContain('同时填写或同时留空')
  })
})
