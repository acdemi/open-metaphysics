/* IANA 时区换算与时间展示。
 *
 * 后端要求 born_at 必须带时区偏移；浏览器里用户输入的是「当地钟表时间」，
 * 因此这里按所选 IANA 时区（含历史夏令时）换算成带偏移的 ISO 8601。
 */

export interface ZonedIso {
  iso: string
  offsetMinutes: number
}

const DATE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/
const TIME_PATTERN = /^(\d{2}):(\d{2})$/

export function isValidTimeZone(zone: string): boolean {
  if (!zone.trim()) return false
  try {
    new Intl.DateTimeFormat('en-US', { timeZone: zone })
    return true
  } catch {
    return false
  }
}

function pad(value: number): string {
  return String(value).padStart(2, '0')
}

/** 给定真实时刻，返回该 IANA 时区当时相对 UTC 的偏移（分钟，东为正）。 */
function offsetMinutesAt(instant: Date, zone: string): number {
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: zone,
    hourCycle: 'h23',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
  const parts: Record<string, string> = {}
  for (const part of formatter.formatToParts(instant)) {
    if (part.type !== 'literal') parts[part.type] = part.value
  }
  const year = Number(parts.year)
  const month = Number(parts.month)
  const day = Number(parts.day)
  const hour = Number(parts.hour)
  const minute = Number(parts.minute)
  const second = Number(parts.second)
  if ([year, month, day, hour, minute, second].some((value) => !Number.isFinite(value))) {
    throw new Error(`无法解析时区偏移：${zone}`)
  }
  const asUtc = Date.UTC(year, month - 1, day, hour, minute, second)
  return Math.round((asUtc - instant.getTime()) / 60_000)
}

export function formatOffset(offsetMinutes: number): string {
  const sign = offsetMinutes >= 0 ? '+' : '-'
  const abs = Math.abs(offsetMinutes)
  return `UTC${sign}${pad(Math.floor(abs / 60))}:${pad(abs % 60)}`
}

/** 把「当地日期 + 当地时间 + IANA 时区」转换为带偏移的 ISO 8601 字符串。 */
export function zonedToIso(dateStr: string, timeStr: string, zone: string): ZonedIso {
  const dateMatch = DATE_PATTERN.exec(dateStr.trim())
  const timeMatch = TIME_PATTERN.exec(timeStr.trim())
  if (!dateMatch) throw new Error('出生日期格式应为 YYYY-MM-DD')
  if (!timeMatch) throw new Error('出生时间格式应为 HH:mm')
  if (!isValidTimeZone(zone)) throw new Error(`无效的 IANA 时区：${zone}`)

  const year = Number(dateMatch[1])
  const month = Number(dateMatch[2])
  const day = Number(dateMatch[3])
  const hour = Number(timeMatch[1])
  const minute = Number(timeMatch[2])
  if (hour > 23 || minute > 59) throw new Error('出生时间超出 00:00–23:59 范围')

  const naiveUtc = Date.UTC(year, month - 1, day, hour, minute, 0)
  const check = new Date(naiveUtc)
  if (
    check.getUTCFullYear() !== year ||
    check.getUTCMonth() !== month - 1 ||
    check.getUTCDate() !== day
  ) {
    throw new Error('出生日期不存在（例如 2 月 30 日）')
  }

  let offset = offsetMinutesAt(new Date(naiveUtc), zone)
  let timestamp = naiveUtc - offset * 60_000
  // 夏令时边界修正：用换算后的真实时刻再确认一次偏移
  const corrected = offsetMinutesAt(new Date(timestamp), zone)
  if (corrected !== offset) {
    offset = corrected
    timestamp = naiveUtc - offset * 60_000
  }

  const local = new Date(timestamp + offset * 60_000)
  const iso =
    `${local.getUTCFullYear()}-${pad(local.getUTCMonth() + 1)}-${pad(local.getUTCDate())}` +
    `T${pad(local.getUTCHours())}:${pad(local.getUTCMinutes())}:00` +
    `${offset >= 0 ? '+' : '-'}${pad(Math.floor(Math.abs(offset) / 60))}:${pad(Math.abs(offset) % 60)}`
  return { iso, offsetMinutes: offset }
}

/** 后端 datetime 可能带微秒（JS Date 只认 3 位小数秒），这里先归一化。 */
function normalizeFractionalSeconds(iso: string): string {
  return iso.replace(/(\.\d{3})\d+/, '$1')
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const date = new Date(normalizeFractionalSeconds(iso))
  if (Number.isNaN(date.getTime())) return String(iso)
  try {
    const base = new Intl.DateTimeFormat('zh-CN', {
      dateStyle: 'medium',
      timeStyle: 'medium',
    }).format(date)
    const zone = timeZoneLabel(date)
    return zone ? `${base} ${zone}` : base
  } catch {
    return date.toISOString()
  }
}

function timeZoneLabel(date: Date): string {
  try {
    const parts = new Intl.DateTimeFormat('en-US', { timeZoneName: 'short' }).formatToParts(date)
    return parts.find((part) => part.type === 'timeZoneName')?.value ?? ''
  } catch {
    return ''
  }
}
