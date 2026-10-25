/* 前端配置：API 地址解析、预填示例、领域元数据。
 *
 * API 基础地址优先级（与迁移前一致）：
 *   1. URL 查询参数      ?api=http://127.0.0.1:8080
 *   2. localStorage      om.apiBase（设置面板保存）
 *   3. 常量默认值        DEFAULT_API_BASE
 * `?api=` 同时作为「恢复默认」的目标地址。
 */

import type { AgentName, Gender } from '../api/types'

export const DEFAULT_API_BASE = 'http://127.0.0.1:8000'
export const API_BASE_STORAGE_KEY = 'om.apiBase'
export const DEFAULT_TIMEOUT_MS = 90_000

export interface StorageLike {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
}

export function normalizeApiBase(value: string): string {
  return value.trim().replace(/\/+$/, '')
}

export function queryApiBase(search: string): string | null {
  const value = new URLSearchParams(search).get('api')
  return value ? normalizeApiBase(value) : null
}

/** 默认值（也是「恢复默认」的目标）：`?api=` 优先于编译期常量。 */
export function defaultApiBase(search: string, fallback: string = DEFAULT_API_BASE): string {
  return queryApiBase(search) ?? normalizeApiBase(fallback)
}

export function resolveApiBase(
  search: string,
  storage: StorageLike | null,
  fallback: string = DEFAULT_API_BASE,
): string {
  const fromQuery = queryApiBase(search)
  if (fromQuery) {
    persistApiBase(fromQuery, storage)
    return fromQuery
  }
  if (storage) {
    try {
      const stored = storage.getItem(API_BASE_STORAGE_KEY)
      if (stored) return normalizeApiBase(stored)
    } catch {
      /* localStorage 不可用（隐私模式等）时忽略 */
    }
  }
  return defaultApiBase(search, fallback)
}

export function persistApiBase(base: string, storage: StorageLike | null): string {
  const clean = normalizeApiBase(base)
  if (storage) {
    try {
      if (clean) storage.setItem(API_BASE_STORAGE_KEY, clean)
      else storage.removeItem(API_BASE_STORAGE_KEY)
    } catch {
      /* 忽略 */
    }
  }
  return clean || DEFAULT_API_BASE
}

export function resetApiBaseToDefault(
  search: string,
  storage: StorageLike | null,
  fallback: string = DEFAULT_API_BASE,
): string {
  if (storage) {
    try {
      storage.removeItem(API_BASE_STORAGE_KEY)
    } catch {
      /* 忽略 */
    }
  }
  return defaultApiBase(search, fallback)
}

/** 浏览器环境下的 storage 访问（可能抛错，因此集中在这里）。 */
export function browserStorage(): StorageLike | null {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

/* ---------------------------------------------------------------- 预填示例 */
export interface DemoDefaults {
  date: string
  time: string
  timezone: string
  gender: Gender
  question: string
  domains: AgentName[]
}

/** 来自仓库 README 的已验证调用示例（POST /agents/bazi/compute，1990-06-15T08:30:00+08:00）。 */
export const DEMO_DEFAULTS: DemoDefaults = {
  date: '1990-06-15',
  time: '08:30',
  timezone: 'Asia/Shanghai',
  gender: 'male',
  question: '今年的工作发展如何？',
  domains: ['bazi'],
}

/* ------------------------------------------------------------------ 领域 */
export interface DomainMeta {
  id: AgentName
  label: string
  latin: string
  description: string
  badge: string
  badgeClass: 'badge-ok' | 'badge-partial'
}

export const DOMAINS: readonly DomainMeta[] = [
  {
    id: 'bazi',
    label: '八字',
    latin: 'BAZI',
    description: '四柱 · 藏干 · 纳音 · 十神 · 大运',
    badge: '计算完整',
    badgeClass: 'badge-ok',
  },
  {
    id: 'ziwei',
    label: '紫微',
    latin: 'ZIWEI',
    description: '十二宫 · 主星 · 五行局',
    badge: '辅星为空',
    badgeClass: 'badge-partial',
  },
  {
    id: 'qimen',
    label: '奇门',
    latin: 'QIMEN',
    description: '九宫 · 八门 · 九星 · 八神 · 局数',
    badge: '解释为通用后备',
    badgeClass: 'badge-partial',
  },
  {
    id: 'liuyao',
    label: '六爻',
    latin: 'LIUYAO',
    description: '本卦 · 变卦 · 互卦 · 纳甲 · 六亲',
    badge: '自动起卦',
    badgeClass: 'badge-partial',
  },
]

export function domainLabel(agent: string): string {
  return DOMAINS.find((domain) => domain.id === agent)?.label ?? agent
}

/* -------------------------------------------------------- 时区 / 性别选项 */
export interface SelectOption {
  value: string
  label: string
}

export const TIMEZONE_OPTIONS: readonly SelectOption[] = [
  { value: 'Asia/Shanghai', label: '中国标准时间（UTC+8）' },
  { value: 'Asia/Hong_Kong', label: '香港时间（UTC+8）' },
  { value: 'Asia/Taipei', label: '台北时间（UTC+8）' },
  { value: 'Asia/Singapore', label: '新加坡时间（UTC+8）' },
  { value: 'Asia/Tokyo', label: '日本标准时间（UTC+9）' },
  { value: 'Asia/Seoul', label: '韩国标准时间（UTC+9）' },
  { value: 'UTC', label: 'UTC' },
  { value: 'Europe/London', label: '伦敦（UTC+0/+1）' },
  { value: 'Europe/Paris', label: '巴黎（UTC+1/+2）' },
  { value: 'America/New_York', label: '纽约（UTC-5/-4）' },
  { value: 'America/Los_Angeles', label: '洛杉矶（UTC-8/-7）' },
  { value: 'Australia/Sydney', label: '悉尼（UTC+10/+11）' },
]

export const GENDER_OPTIONS: readonly { value: Gender; label: string }[] = [
  { value: 'male', label: '男' },
  { value: 'female', label: '女' },
  { value: 'unknown', label: '未知' },
]
