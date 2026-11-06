import { describe, expect, it } from 'vitest'

import { buildRequest, makeRequestId, type FormValues } from '../../src/utils/validation'

function form(overrides: Partial<FormValues> = {}): FormValues {
  return {
    domains: ['bazi'],
    date: '1990-06-15',
    time: '08:30',
    timezone: 'Asia/Shanghai',
    gender: 'male',
    question: '今年的工作发展如何？',
    seed: '',
    lat: '',
    lon: '',
    nonce: '',
    ...overrides,
  }
}

describe('buildRequest', () => {
  it('生成带时区的 born_at 与固定字段', () => {
    const built = buildRequest(form(), 'req-1')
    expect('payload' in built).toBe(true)
    if (!('payload' in built)) return
    expect(built.payload.payload.born_at).toBe('1990-06-15T08:30:00+09:00')
    expect(built.payload.payload.question).toBe('今年的工作发展如何？')
    expect(built.payload.agents).toEqual(['bazi'])
    expect(built.payload.explain).toBe(true)
    expect(built.payload.payload.born_location).toBeUndefined()
  })

  it('缺少日期与时间时给出字段级错误', () => {
    const built = buildRequest(form({ date: '', time: '' }), 'req-2')
    expect('payload' in built).toBe(false)
    if ('payload' in built) return
    expect(built.errors.map((error) => error.field)).toEqual(expect.arrayContaining(['date', 'time']))
  })

  it('未选择领域时报错', () => {
    const built = buildRequest(form({ domains: [] }), 'req-3')
    if ('payload' in built) throw new Error('不该生成请求体')
    expect(built.errors.some((error) => error.field === 'domains')).toBe(true)
  })

  it('经纬度必须成对出现', () => {
    const built = buildRequest(form({ lat: '39.9' }), 'req-4')
    if ('payload' in built) throw new Error('不该生成请求体')
    expect(built.errors.some((error) => error.field === 'lat')).toBe(true)
  })

  it('成对经纬度写入 born_location 并带时区', () => {
    const built = buildRequest(form({ lat: '39.9', lon: '116.4' }), 'req-5')
    if (!('payload' in built)) throw new Error('应生成请求体')
    expect(built.payload.payload.born_location).toEqual({
      latitude: 39.9,
      longitude: 116.4,
      timezone: 'Asia/Shanghai',
    })
  })

  it('seed 必须是整数', () => {
    const built = buildRequest(form({ seed: '1.5' }), 'req-6')
    if ('payload' in built) throw new Error('不该生成请求体')
    expect(built.errors.some((error) => error.field === 'seed')).toBe(true)
  })

  it('整数 seed 与 client_nonce 会进入 payload', () => {
    const built = buildRequest(form({ seed: '42', nonce: 'nonce-1' }), 'req-7')
    if (!('payload' in built)) throw new Error('应生成请求体')
    expect(built.payload.payload.seed).toBe(42)
    expect(built.payload.payload.client_nonce).toBe('nonce-1')
  })

  it('问题超过 500 字时报错', () => {
    const built = buildRequest(form({ question: 'a'.repeat(501) }), 'req-8')
    if ('payload' in built) throw new Error('不该生成请求体')
    expect(built.errors.some((error) => error.field === 'question')).toBe(true)
  })
})

describe('makeRequestId', () => {
  it('生成 ui- 前缀且唯一的请求 id', () => {
    const first = makeRequestId()
    const second = makeRequestId()
    expect(first.startsWith('ui-')).toBe(true)
    expect(first).not.toBe(second)
  })
})
