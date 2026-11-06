/* 会话历史：GET /sessions 列表 + GET /sessions/{id} 读取。
 *
 * 两个端点在 OpenAPI 中还没有响应模型（后端直接返回 store 的原始 dict），
 * 因此响应在 client 层经 `parse.ts` 逐字段校验；这里只管理对话框状态与错误文案。
 */

import { ref, type Ref } from 'vue'

import { fetchSessionList, fetchStoredSession } from '../api/client'
import { asErrorMessage, isApiError } from '../api/errors'
import type { SessionSummary, StoredSession } from '../api/types'

export interface SessionHistoryApi {
  loading: Ref<boolean>
  error: Ref<string | null>
  sessions: Ref<SessionSummary[]>
  /** 当前分页参数（P2.2：GET /sessions?limit=50&offset=0）。 */
  total: Ref<number>
  pageSize: number
  restoringId: Ref<string | null>
  restoreError: Ref<string | null>
  refresh(): Promise<void>
  restore(requestId: string): Promise<StoredSession | null>
}

function errorText(error: unknown): string {
  if (!isApiError(error)) return asErrorMessage(error)
  if (error.kind === 'invalid_response') return '后端会话响应格式不符合契约，已阻止展示。'
  if (error.transport === 'network') return '无法连接后端：请确认服务已启动、API 地址正确。'
  if (error.transport === 'timeout') return '读取会话超时，请重试。'
  if (error.kind === 'not_found') return '该会话已不存在（可能已被清理）。'
  return `${error.kind}：${error.message}`
}

export function useSessionHistory(apiBase: Ref<string>): SessionHistoryApi {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const sessions = ref<SessionSummary[]>([])
  const total = ref(0)
  const restoringId = ref<string | null>(null)
  const restoreError = ref<string | null>(null)
  const pageSize = 50

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const { data } = await fetchSessionList(apiBase.value, pageSize, 0)
      sessions.value = data.sessions
      total.value = data.total ?? data.sessions.length
    } catch (caught) {
      sessions.value = []
      total.value = 0
      error.value = errorText(caught)
    } finally {
      loading.value = false
    }
  }

  async function refresh(): Promise<void> {
    await load()
  }

  async function restore(requestId: string): Promise<StoredSession | null> {
    restoringId.value = requestId
    restoreError.value = null
    try {
      const { data } = await fetchStoredSession(apiBase.value, requestId)
      return data
    } catch (caught) {
      restoreError.value = errorText(caught)
      return null
    } finally {
      restoringId.value = null
    }
  }

  return {
    loading,
    error,
    sessions,
    total,
    pageSize,
    restoringId,
    restoreError,
    refresh,
    restore,
  }
}
