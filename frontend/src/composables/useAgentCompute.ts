/* 领域独立计算：GET /agents + GET /agents/{name}/schema + POST /agents/{name}/compute。
 *
 * 与 Orchestration 分开：这里只调用一个领域 Agent，不产生跨域共识，也不虚构其他领域结果。
 * 状态机：idle → loading → success | error；切换领域/新请求会作废旧请求。
 */

import { computed, reactive, ref, type ComputedRef, type Ref } from 'vue'

import { computeAgent, fetchAgentList, fetchAgentSchema } from '../api/client'
import { asErrorMessage, isApiError, validationDetailMessages } from '../api/errors'
import { isDomainOutput } from '../api/parse'
import type { AgentInfo, AgentName, AgentSchemaResponse, AnyOutput } from '../api/types'
import { DOMAINS } from '../config'
import {
  buildAgentPayload,
  draftFromSchema,
  emptyDraft,
  type AgentDraft,
  type AgentFieldErrors,
} from '../utils/agentForm'
import { readInputSchemaFromResponse, type AgentInputSchema } from '../utils/agentSchema'
import { makeRequestId } from '../utils/validation'

export type AgentComputeStatus = 'idle' | 'loading' | 'success' | 'error'

export interface AgentComputeApi {
  agents: Ref<AgentInfo[]>
  agentsLoading: Ref<boolean>
  agentsError: Ref<string | null>
  domains: typeof DOMAINS
  selected: Ref<AgentName>
  schema: Ref<AgentSchemaResponse | null>
  inputSchema: ComputedRef<AgentInputSchema | null>
  schemaLoading: Ref<boolean>
  schemaError: Ref<string | null>
  draft: AgentDraft
  fieldErrors: Ref<AgentFieldErrors>
  status: Ref<AgentComputeStatus>
  result: Ref<AnyOutput | null>
  error: Ref<string | null>
  elapsedMs: Ref<number>
  init(): Promise<void>
  selectAgent(name: AgentName): void
  submit(): Promise<void>
  cancel(): void
  clearResult(): void
}

function errorText(error: unknown): string {
  if (!isApiError(error)) return asErrorMessage(error)
  if (error.kind === 'invalid_response') return '后端计算结果格式不符合契约，已阻止展示。'
  if (error.transport === 'network') return '无法连接后端：请确认服务已启动、API 地址正确。'
  if (error.transport === 'timeout') return '计算超时，请重试。'
  if (error.status === 422) {
    const details = validationDetailMessages(error.body)
    if (details.length > 0) return `参数未通过后端校验：${details.join('；')}`
    return `参数未通过后端校验：${error.message}`
  }
  if (error.kind === 'unknown_agent') return `后端没有该领域 Agent：${error.message}`
  if (error.kind === 'calculation_failed') return `后端计算失败：${error.message}`
  return `${error.kind}：${error.message}`
}

export function useAgentCompute(apiBase: Ref<string>): AgentComputeApi {
  const agents = ref<AgentInfo[]>([])
  const agentsLoading = ref(false)
  const agentsError = ref<string | null>(null)
  const selected = ref<AgentName>('bazi')
  const schema = ref<AgentSchemaResponse | null>(null)
  const schemaLoading = ref(false)
  const schemaError = ref<string | null>(null)
  const draft = reactive<AgentDraft>(emptyDraft())
  const fieldErrors = ref<AgentFieldErrors>({})
  const status = ref<AgentComputeStatus>('idle')
  const result = ref<AnyOutput | null>(null)
  const error = ref<string | null>(null)
  const elapsedMs = ref(0)

  const cache = new Map<AgentName, AgentSchemaResponse>()
  let computeController: AbortController | null = null
  let computeSeq = 0
  let schemaSeq = 0

  const inputSchema = computed<AgentInputSchema | null>(() => readInputSchemaFromResponse(schema.value))

  async function loadAgents(): Promise<void> {
    agentsLoading.value = true
    agentsError.value = null
    try {
      const { data } = await fetchAgentList(apiBase.value)
      agents.value = data.agents
    } catch (caught) {
      agents.value = []
      agentsError.value = errorText(caught)
    } finally {
      agentsLoading.value = false
    }
  }

  function resetForm(): void {
    Object.assign(draft, emptyDraft())
    fieldErrors.value = {}
    result.value = null
    error.value = null
    elapsedMs.value = 0
    status.value = 'idle'
  }

  function applySchema(next: AgentSchemaResponse | null): void {
    schema.value = next
    Object.assign(draft, draftFromSchema(readInputSchemaFromResponse(next)))
  }

  function selectAgent(name: AgentName): void {
    if (selected.value === name && schema.value !== null) return
    computeController?.abort()
    computeSeq += 1
    selected.value = name
    schema.value = null
    schemaError.value = null
    resetForm()

    const cached = cache.get(name)
    if (cached) {
      applySchema(cached)
      return
    }
    const seq = ++schemaSeq
    schemaLoading.value = true
    void (async () => {
      try {
        const { data } = await fetchAgentSchema(apiBase.value, name)
        if (seq !== schemaSeq || selected.value !== name) return
        cache.set(name, data)
        applySchema(data)
      } catch (caught) {
        if (seq !== schemaSeq || selected.value !== name) return
        schemaError.value = errorText(caught)
      } finally {
        if (seq === schemaSeq) schemaLoading.value = false
      }
    })()
  }

  async function init(): Promise<void> {
    await loadAgents()
    selectAgent(selected.value)
  }

  async function submit(): Promise<void> {
    if (status.value === 'loading') return
    const schemaNow = inputSchema.value
    if (schemaNow === null) {
      status.value = 'error'
      error.value = schemaError.value ?? '领域 Schema 尚未加载完成，暂时无法计算。'
      return
    }
    const requestId = makeRequestId()
    const { payload, errors } = buildAgentPayload(draft, requestId, schemaNow)
    if (Object.keys(errors).length > 0) {
      fieldErrors.value = errors
      return
    }
    fieldErrors.value = {}
    computeController?.abort()
    const controller = new AbortController()
    computeController = controller
    const seq = ++computeSeq
    const domain = selected.value
    status.value = 'loading'
    error.value = null
    try {
      const { data, elapsedMs: elapsed } = await computeAgent(apiBase.value, domain, payload, {
        signal: controller.signal,
      })
      if (seq !== computeSeq) return
      if (data.agent !== domain) {
        status.value = 'error'
        error.value = `后端返回的领域（${data.agent}）与当前选择（${domain}）不一致，已阻止展示。`
        return
      }
      if (!isDomainOutput(data)) {
        status.value = 'error'
        error.value = `后端结果不是已知领域（${data.agent}），已阻止展示。`
        return
      }
      result.value = data
      elapsedMs.value = elapsed
      status.value = 'success'
    } catch (caught) {
      if (seq !== computeSeq) return
      if (isApiError(caught) && caught.kind === 'cancelled') return
      status.value = 'error'
      error.value = errorText(caught)
      result.value = null
    } finally {
      if (seq === computeSeq) computeController = null
    }
  }

  function cancel(): void {
    computeController?.abort()
    computeController = null
    computeSeq += 1
    if (status.value === 'loading') status.value = 'idle'
  }

  function clearResult(): void {
    result.value = null
    error.value = null
    elapsedMs.value = 0
    status.value = 'idle'
  }

  return {
    agents,
    agentsLoading,
    agentsError,
    domains: DOMAINS,
    selected,
    schema,
    inputSchema,
    schemaLoading,
    schemaError,
    draft,
    fieldErrors,
    status,
    result,
    error,
    elapsedMs,
    init,
    selectAgent,
    submit,
    cancel,
    clearResult,
  }
}
