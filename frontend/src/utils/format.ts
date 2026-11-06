/* 展示层格式化：只做显示，不参与任何计算。 */

import type { TraceScalar } from '../api/types'

export function fmtPercent(value: number | null | undefined, digits = 1): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—'
  return `${(value * 100).toFixed(digits)}%`
}

export function fmtNum(value: number | null | undefined, digits = 2): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '—'
  return value.toFixed(digits)
}

export function elapsedLabel(milliseconds: number): string {
  return `${(milliseconds / 1000).toFixed(2)} s`
}

export function formatScalar(value: TraceScalar): string {
  if (typeof value === 'boolean') return value ? 'true' : 'false'
  return String(value)
}

export function scalarEntries(
  record: Record<string, TraceScalar> | undefined,
): { key: string; value: string }[] {
  if (!record) return []
  return Object.entries(record).map(([key, value]) => ({ key, value: formatScalar(value) }))
}

/** 按 1 起始的爻位/柱位取数组元素，越界返回 null（不虚构）。 */
export function atPosition<T>(list: readonly T[] | undefined, position: number): T | null {
  if (!list) return null
  const index = position - 1
  return index >= 0 && index < list.length ? (list[index] ?? null) : null
}

/* 六十四卦（King Wen 序）——名称表与 src/openmetaphysics/core/models.py::HEXAGRAMS 同序，
 * 仅用于把后端返回的卦序号显示成卦名，不参与任何计算。 */
const HEXAGRAM_NAMES = [
  '乾', '坤', '屯', '蒙', '需', '讼', '师', '比', '小畜', '履', '泰', '否',
  '同人', '大有', '谦', '豫', '随', '蛊', '临', '观', '噬嗑', '贲', '剥', '复',
  '无妄', '大畜', '颐', '大过', '坎', '离', '咸', '恒', '遯', '大壮', '晋', '明夷',
  '家人', '睽', '蹇', '解', '损', '益', '夬', '姤', '萃', '升', '困', '井',
  '革', '鼎', '震', '艮', '渐', '归妹', '丰', '旅', '巽', '兑', '涣', '节',
  '中孚', '小过', '既济', '未济',
] as const

export function hexagramName(num: number | null | undefined): string | null {
  if (typeof num !== 'number' || !Number.isInteger(num) || num < 1 || num > HEXAGRAM_NAMES.length) {
    return null
  }
  return HEXAGRAM_NAMES[num - 1] ?? null
}

/** 九宫（洛书方位）显示顺序：巽4 离9 坤2 / 震3 中5 兑7 / 艮8 坎1 乾6 */
export const QIMEN_PALACE_ORDER = [4, 9, 2, 3, 5, 7, 8, 1, 6] as const

/** 六爻起卦值：6 老阴 / 7 少阳 / 8 少阴 / 9 老阳 */
export const CAST_LABELS: Record<number, string> = {
  6: '老阴 ×',
  7: '少阳',
  8: '少阴',
  9: '老阳 ○',
}

/** 后端用 ASCII 枚举表达阴阳，这里只做显示层映射。 */
export const YIN_YANG_LABELS: Record<string, string> = {
  yang: '阳',
  yin: '阴',
}
