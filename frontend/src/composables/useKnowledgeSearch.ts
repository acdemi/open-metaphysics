/* 知识检索：独立检索冻结语料（POST /knowledge/search），不是解释/结论的证据链。
 *
 * 状态机：idle → loading → success | empty | error。连续检索会中止上一条请求，
 * 并用序号丢弃过期响应，避免旧结果覆盖新结果；组件卸载时由调用方 cancel()。
 */

import { ref, type Ref } from 'vue'

import { fetchKnowledgeCorpora, fetchKnowledgeSearch } from '../api/client'
import { asErrorMessage, isApiError } from '../api/errors'
import type { KnowledgeCorpusInfo, KnowledgeSearchChunk } from '../api/types'

export type KnowledgeSearchStatus = 'idle' | 'loading' | 'success' | 'empty' | 'error'

export interface KnowledgeSearchApi {
  query: Ref<string>
  k: Ref<number>
  includeEvidence: Ref<boolean>
  status: Ref<KnowledgeSearchStatus>
  chunks: Ref<KnowledgeSearchChunk[]>
  error: Ref<string | null>
  lastQuery: Ref<string>
  corpora: Ref<KnowledgeCorpusInfo[]>
  corporaLoading: Ref<boolean>
  corporaError: Ref<string | null>
  submit(): Promise<void>
  cancel(): void
  reset(): void
  loadCorpora(): Promise<void>
}

const MAX_K = 20

function errorText(error: unknown): string {
  if (!isApiError(error)) return asErrorMessage(error)
  if (error.kind === 'invalid_response') return '后端知识检索响应格式不符合契约，已阻止展示。'
  if (error.transport === 'network') return '无法连接后端：请确认服务已启动、API 地址正确。'
  if (error.transport === 'timeout') return '检索超时，请减少返回条数后重试。'
  if (error.kind === 'invalid_request') return '检索参数未通过后端校验（HTTP 422）。'
  return `${error.kind}：${error.message}`
}

export function useKnowledgeSearch(apiBase: Ref<string>): KnowledgeSearchApi {
  const query = ref('')
  const k = ref(5)
  const includeEvidence = ref(false)
  const status = ref<KnowledgeSearchStatus>('idle')
  const chunks = ref<KnowledgeSearchChunk[]>([])
  const error = ref<string | null>(null)
  const lastQuery = ref('')
  const corpora = ref<KnowledgeCorpusInfo[]>([])
  const corporaLoading = ref(false)
  const corporaError = ref<string | null>(null)

  let searchController: AbortController | null = null
  let searchSeq = 0
  let corporaSeq = 0

  async function submit(): Promise<void> {
    const normalized = query.value.trim()
    if (!normalized) {
      chunks.value = []
      status.value = 'error'
      error.value = '请输入查询关键词后再检索。'
      return
    }
    const limit = Math.trunc(k.value)
    if (!Number.isFinite(limit) || limit <= 0 || limit > MAX_K) {
      chunks.value = []
      status.value = 'error'
      error.value = `返回条数需为 1–${MAX_K} 的整数。`
      return
    }

    searchController?.abort()
    const controller = new AbortController()
    searchController = controller
    const seq = ++searchSeq
    status.value = 'loading'
    error.value = null
    try {
      const { data } = await fetchKnowledgeSearch(
        apiBase.value,
        { query: normalized, k: limit, includeEvidence: includeEvidence.value },
        { signal: controller.signal },
      )
      if (seq !== searchSeq) return
      lastQuery.value = data.query
      chunks.value = data.chunks
      status.value = data.chunks.length > 0 ? 'success' : 'empty'
    } catch (caught) {
      if (seq !== searchSeq) return
      if (isApiError(caught) && caught.kind === 'cancelled') return
      chunks.value = []
      status.value = 'error'
      error.value = errorText(caught)
    } finally {
      if (seq === searchSeq) searchController = null
    }
  }

  function cancel(): void {
    searchController?.abort()
    searchController = null
    // 让在途请求的响应失效（abort 是尽力而为，mock/浏览器时序可能仍 resolve）。
    searchSeq += 1
    if (status.value === 'loading') {
      status.value = 'idle'
      error.value = null
    }
  }

  function reset(): void {
    cancel()
    status.value = 'idle'
    chunks.value = []
    error.value = null
    lastQuery.value = ''
  }

  async function loadCorpora(): Promise<void> {
    const seq = ++corporaSeq
    corporaLoading.value = true
    corporaError.value = null
    try {
      const { data } = await fetchKnowledgeCorpora(apiBase.value)
      if (seq !== corporaSeq) return
      corpora.value = data.corpora
    } catch (caught) {
      if (seq !== corporaSeq) return
      corpora.value = []
      corporaError.value = errorText(caught)
    } finally {
      if (seq === corporaSeq) corporaLoading.value = false
    }
  }

  return {
    query,
    k,
    includeEvidence,
    status,
    chunks,
    error,
    lastQuery,
    corpora,
    corporaLoading,
    corporaError,
    submit,
    cancel,
    reset,
    loadCorpora,
  }
}
