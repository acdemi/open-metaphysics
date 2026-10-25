/* 分析工作流：表单状态 → 校验 → POST /orchestrate → 结果 / 错误 / 取消。 */

import { computed, reactive, ref, type ComputedRef, type Ref } from 'vue'

import { postOrchestrate, probeReachable } from '../api/client'
import {
  asErrorMessage,
  backendErrorBody,
  isApiError,
  validationDetailMessages,
} from '../api/errors'
import type { OrchestrationRequest, OrchestrationResponse } from '../api/types'
import { DEMO_DEFAULTS } from '../config'
import { buildRequest, makeRequestId, type FieldError, type FieldKey, type FormValues } from '../utils/validation'

export type ViewState = 'empty' | 'loading' | 'error' | 'results'

export type TabName = 'calculation' | 'evidence' | 'explanation' | 'consensus' | 'execution'

export const RESULT_TABS: readonly { id: TabName; label: string }[] = [
  { id: 'calculation', label: '计算结果' },
  { id: 'evidence', label: '知识证据' },
  { id: 'explanation', label: '解释' },
  { id: 'consensus', label: '综合共识' },
  { id: 'execution', label: '执行详情' },
]

export interface LoadingStep {
  key: 'submit' | 'compute' | 'render'
  label: string
  state: 'idle' | 'active' | 'done'
}

export interface AnalysisErrorView {
  title: string
  message: string
  hints: string[]
  raw: string | null
}

export interface AnalysisApi {
  form: FormValues
  errors: Ref<FieldError[]>
  preview: Ref<string>
  view: Ref<ViewState>
  result: Ref<OrchestrationResponse | null>
  loading: Ref<boolean>
  elapsedMs: Ref<number>
  steps: Ref<LoadingStep[]>
  error: Ref<AnalysisErrorView | null>
  activeTab: Ref<TabName>
  lastPayload: Ref<OrchestrationRequest | null>
  activeDomainLabels: ComputedRef<string>
  submit(): Promise<void>
  rerun(): Promise<void>
  cancel(): void
  resetDemo(): void
  clearErrors(): void
  setTab(tab: TabName): void
  fieldError(field: FieldKey): string | null
  errorForField(field: FieldKey): boolean
}

function demoForm(): FormValues {
  return {
    domains: [...DEMO_DEFAULTS.domains],
    date: DEMO_DEFAULTS.date,
    time: DEMO_DEFAULTS.time,
    timezone: DEMO_DEFAULTS.timezone,
    gender: DEMO_DEFAULTS.gender,
    question: DEMO_DEFAULTS.question,
    seed: '',
    lat: '',
    lon: '',
    nonce: '',
  }
}

function initialSteps(): LoadingStep[] {
  return [
    { key: 'submit', label: '提交请求', state: 'idle' },
    { key: 'compute', label: '后端确定性计算与知识检索', state: 'idle' },
    { key: 'render', label: '渲染结果', state: 'idle' },
  ]
}

export function useAnalysis(apiBase: Ref<string>): AnalysisApi {
  const form = reactive<FormValues>(demoForm())
  const errors = ref<FieldError[]>([])
  const view = ref<ViewState>('empty')
  const result = ref<OrchestrationResponse | null>(null)
  const loading = ref(false)
  const elapsedMs = ref(0)
  const steps = ref<LoadingStep[]>(initialSteps())
  const errorView = ref<AnalysisErrorView | null>(null)
  const activeTab = ref<TabName>('calculation')
  const lastPayload = ref<OrchestrationRequest | null>(null)

  let abortController: AbortController | null = null
  let timer: ReturnType<typeof setInterval> | null = null
  let computeStepTimer: ReturnType<typeof setTimeout> | null = null

  const preview = computed<string>(() => {
    const built = buildRequest(form, 'ui-<提交时生成>')
    if ('payload' in built) {
      return JSON.stringify(built.payload, null, 2)
    }
    return [
      '// 请求体尚未可生成：',
      ...built.errors.map((item) => `// ${item.message}`),
    ].join('\n')
  })

  const activeDomainLabels = computed<string>(() => {
    const outputs = result.value?.outputs ?? []
    return outputs.map((output) => output.agent).join(' · ')
  })

  function clearErrors(): void {
    errors.value = []
  }

  function fieldError(field: FieldKey): string | null {
    return errors.value.find((item) => item.field === field)?.message ?? null
  }

  function errorForField(field: FieldKey): boolean {
    return errors.value.some((item) => item.field === field)
  }

  function setTab(tab: TabName): void {
    activeTab.value = tab
  }

  function resetDemo(): void {
    Object.assign(form, demoForm())
    clearErrors()
    view.value = 'empty'
    result.value = null
    errorView.value = null
    lastPayload.value = null
    elapsedMs.value = 0
    steps.value = initialSteps()
    activeTab.value = 'calculation'
  }

  function startLoadingUi(): void {
    steps.value = initialSteps()
    const submitStep = steps.value.find((step) => step.key === 'submit')
    if (submitStep) submitStep.state = 'active'
    elapsedMs.value = 0
    const startedAt = performance.now()
    if (timer !== null) clearInterval(timer)
    timer = setInterval(() => {
      elapsedMs.value = Math.round(performance.now() - startedAt)
    }, 100)
    if (computeStepTimer !== null) clearTimeout(computeStepTimer)
    computeStepTimer = setTimeout(() => {
      if (!loading.value) return
      const submit = steps.value.find((step) => step.key === 'submit')
      const compute = steps.value.find((step) => step.key === 'compute')
      if (submit) submit.state = 'done'
      if (compute) compute.state = 'active'
    }, 150)
  }

  function finishSteps(): void {
    for (const step of steps.value) step.state = 'done'
  }

  function stopLoadingUi(): void {
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
    if (computeStepTimer !== null) {
      clearTimeout(computeStepTimer)
      computeStepTimer = null
    }
  }

  async function toErrorView(error: unknown): Promise<AnalysisErrorView> {
    if (!isApiError(error) || error.transport === 'network') {
      const reachable = await probeReachable(apiBase.value)
      if (reachable) {
        return {
          title: '浏览器拦截了跨域响应（CORS）',
          message:
            '后端端口可达，但浏览器未能读取响应，通常是后端未允许当前页面来源。请按下面的方式重启后端后重试。',
          hints: [
            `当前页面来源：${window.location.origin}`,
            "启动后端时加入：OM_CORS_ORIGINS=http://127.0.0.1:5173（PowerShell：$env:OM_CORS_ORIGINS='http://127.0.0.1:5173'）",
            '也可以把前端与后端放在同一来源，或在右上角 ⚙ 设置中改用可访问的 API 地址。',
          ],
          raw: asErrorMessage(error),
        }
      }
      return {
        title: '无法连接后端',
        message: `请求 ${apiBase.value}/orchestrate 失败，浏览器没有收到任何响应。`,
        hints: [
          '确认后端已启动：uv run openmetaphysics（默认监听 127.0.0.1:8000）',
          `确认当前 API 地址正确：${apiBase.value}（可在 ⚙ 设置中修改）`,
          '确认没有防火墙/代理拦截本地端口。',
        ],
        raw: asErrorMessage(error),
      }
    }

    if (error.transport === 'timeout') {
      return {
        title: '请求超时',
        message: error.message,
        hints: [
          '多域联合分析（尤其包含解释与知识检索）可能较慢；可减少领域后重试。',
          '确认后端进程仍在运行，且没有被调试器/代理挂起。',
        ],
        raw: error.body ? JSON.stringify(error.body, null, 2) : error.message,
      }
    }

    if (error.transport === 'http') {
      const backend = backendErrorBody(error.body)
      const fields = backend?.fields ?? []
      const details = validationDetailMessages(error.body)
      const hints: string[] = []
      if (fields.length > 0) {
        hints.push(`后端指出的字段：${fields.map((location) => location.join('.')).join('、')}`)
      }
      if (details.length > 0) hints.push(`校验详情：${details.join('；')}`)

      const titles: Record<string, string> = {
        invalid_request: '请求参数未通过后端校验（422）',
        unknown_agent: '未知的分析领域（404）',
        calculation_failed: '后端确定性计算失败（500）',
        internal_error: '后端内部错误（500）',
        not_found: '资源不存在（404）',
        invalid_response: '后端响应格式不符合契约',
      }
      if (hints.length === 0) {
        hints.push(`后端返回：${JSON.stringify(error.body ?? {}).slice(0, 400)}`)
      }
      return {
        title: titles[error.kind] ?? `请求失败（HTTP ${error.status}）`,
        message: error.message || `后端返回 HTTP ${error.status}`,
        hints,
        raw: error.body ? JSON.stringify(error.body, null, 2) : error.message,
      }
    }

    return {
      title: '请求失败',
      message: asErrorMessage(error),
      hints: ['可重试；如果持续失败，请查看后端日志。'],
      raw: asErrorMessage(error),
    }
  }

  async function run(payload: OrchestrationRequest): Promise<void> {
    lastPayload.value = payload
    loading.value = true
    view.value = 'loading'
    errorView.value = null
    abortController = new AbortController()
    startLoadingUi()
    const startedAt = performance.now()
    try {
      const { data, elapsedMs: measured } = await postOrchestrate(apiBase.value, payload, {
        signal: abortController.signal,
      })
      result.value = data
      elapsedMs.value = measured || Math.round(performance.now() - startedAt)
      finishSteps()
      if (!data.consensus) {
        const consensusTab = RESULT_TABS.find((tab) => tab.id === 'consensus')
        if (consensusTab && activeTab.value === 'consensus') activeTab.value = 'calculation'
      }
      view.value = 'results'
    } catch (error) {
      if (isApiError(error) && error.kind === 'cancelled') {
        errorView.value = {
          title: '已取消请求',
          message: '本次分析已取消，后端可能仍完成了计算；可重新提交。',
          hints: [],
          raw: null,
        }
      } else {
        errorView.value = await toErrorView(error)
      }
      view.value = 'error'
    } finally {
      loading.value = false
      abortController = null
      stopLoadingUi()
    }
  }

  async function submit(): Promise<void> {
    if (loading.value) return
    const built = buildRequest(form, makeRequestId())
    errors.value = built.errors
    if (!('payload' in built)) return
    await run(built.payload)
  }

  async function rerun(): Promise<void> {
    if (loading.value) return
    const built = buildRequest(form, makeRequestId())
    errors.value = built.errors
    if (!('payload' in built)) {
      view.value = result.value ? 'results' : 'empty'
      return
    }
    await run(built.payload)
  }

  function cancel(): void {
    abortController?.abort()
  }

  return {
    form,
    errors,
    preview,
    view,
    result,
    loading,
    elapsedMs,
    steps,
    error: errorView,
    activeTab,
    lastPayload,
    activeDomainLabels,
    submit,
    rerun,
    cancel,
    resetDemo,
    clearErrors,
    setTab,
    fieldError,
    errorForField,
  }
}
