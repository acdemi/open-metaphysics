/* 单域解释：POST /agents/{name}/explain。
 *
 * 解释不重新计算：请求体必须携带已计算的 AgentOutput。解释失败不影响计算结果，
 * 这里只管理解释自身的状态；切换计算结果/领域时由调用方 reset() 隔离旧响应。
 */

import { ref, type Ref } from 'vue'

import { explainAgent } from '../api/client'
import { asErrorMessage, isApiError, validationDetailMessages } from '../api/errors'
import type { AgentExplainResponse, AgentName, AnyOutput } from '../api/types'

export type AgentExplainStatus = 'idle' | 'loading' | 'success' | 'error'

export interface AgentExplainApi {
  status: Ref<AgentExplainStatus>
  result: Ref<AgentExplainResponse | null>
  error: Ref<string | null>
  elapsedMs: Ref<number>
  explain(name: AgentName, output: AnyOutput): Promise<void>
  cancel(): void
  reset(): void
}

function errorText(error: unknown): string {
  if (!isApiError(error)) return asErrorMessage(error)
  if (error.kind === 'invalid_response') return '后端解释响应格式不符合契约，已阻止展示。'
  if (error.transport === 'network') return '无法连接后端：请确认服务已启动、API 地址正确。'
  if (error.transport === 'timeout') return '解释超时，请重试。'
  if (error.status === 422) {
    const details = validationDetailMessages(error.body)
    if (details.length > 0) return `解释请求参数未通过后端校验：${details.join('；')}`
    return `解释请求参数未通过后端校验：${error.message}`
  }
  if (error.kind === 'unknown_agent') return `后端没有该领域 Agent：${error.message}`
  return `${error.kind}：${error.message}`
}

export function useAgentExplain(apiBase: Ref<string>): AgentExplainApi {
  const status = ref<AgentExplainStatus>('idle')
  const result = ref<AgentExplainResponse | null>(null)
  const error = ref<string | null>(null)
  const elapsedMs = ref(0)

  let controller: AbortController | null = null
  let seq = 0

  async function explain(name: AgentName, output: AnyOutput): Promise<void> {
    if (status.value === 'loading') return
    controller?.abort()
    const next = new AbortController()
    controller = next
    const run = ++seq
    status.value = 'loading'
    error.value = null
    try {
      const { data, elapsedMs: elapsed } = await explainAgent(apiBase.value, name, output, {
        signal: next.signal,
      })
      if (run !== seq) return
      if (data.agent !== name) {
        status.value = 'error'
        error.value = `后端返回的解释领域（${data.agent}）与当前领域（${name}）不一致，已阻止展示。`
        return
      }
      result.value = data
      elapsedMs.value = elapsed
      status.value = 'success'
    } catch (caught) {
      if (run !== seq) return
      if (isApiError(caught) && caught.kind === 'cancelled') return
      status.value = 'error'
      error.value = errorText(caught)
    } finally {
      if (run === seq) controller = null
    }
  }

  function cancel(): void {
    controller?.abort()
    controller = null
    seq += 1
    if (status.value === 'loading') {
      status.value = 'idle'
      error.value = null
    }
  }

  function reset(): void {
    controller?.abort()
    controller = null
    seq += 1
    status.value = 'idle'
    result.value = null
    error.value = null
    elapsedMs.value = 0
  }

  return { status, result, error, elapsedMs, explain, cancel, reset }
}
