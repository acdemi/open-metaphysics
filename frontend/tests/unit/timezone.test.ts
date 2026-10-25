import { describe, expect, it } from 'vitest'

import { formatDateTime, formatOffset, isValidTimeZone, zonedToIso } from '../../src/utils/timezone'

describe('zonedToIso', () => {
  it('按历史夏令时换算 Asia/Shanghai（1990-06 为 UTC+9）', () => {
    const result = zonedToIso('1990-06-15', '08:30', 'Asia/Shanghai')
    expect(result.iso).toBe('1990-06-15T08:30:00+09:00')
    expect(result.offsetMinutes).toBe(540)
  })

  it('UTC 时区输出 +00:00', () => {
    expect(zonedToIso('2024-03-01', '06:00', 'UTC').iso).toBe('2024-03-01T06:00:00+00:00')
  })

  it('拒绝不存在的日期', () => {
    expect(() => zonedToIso('2024-02-30', '10:00', 'UTC')).toThrow(/不存在/)
  })

  it('拒绝无法识别的 IANA 时区', () => {
    expect(() => zonedToIso('2024-01-01', '10:00', 'Mars/Olympus')).toThrow(/时区/)
  })

  it('拒绝非法时间格式', () => {
    expect(() => zonedToIso('2024-01-01', '25:00', 'UTC')).toThrow(/超出/)
  })
})

describe('formatOffset', () => {
  it('格式化正负偏移', () => {
    expect(formatOffset(540)).toBe('UTC+09:00')
    expect(formatOffset(-300)).toBe('UTC-05:00')
    expect(formatOffset(0)).toBe('UTC+00:00')
  })
})

describe('formatDateTime', () => {
  it('归一化后端微秒时间戳后仍可解析', () => {
    const text = formatDateTime('1990-02-04T02:11:40.542161Z')
    expect(text).toContain('1990')
    expect(text).not.toContain('T02:11:40.542161')
  })

  it('空值显示占位符', () => {
    expect(formatDateTime(null)).toBe('—')
  })
})

describe('isValidTimeZone', () => {
  it('识别合法与非法时区', () => {
    expect(isValidTimeZone('Asia/Tokyo')).toBe(true)
    expect(isValidTimeZone('Not/AZone')).toBe(false)
    expect(isValidTimeZone('')).toBe(false)
  })
})
