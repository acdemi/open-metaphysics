/* 后端连接状态：API 地址解析、/health 探测、设置面板的保存/恢复。 */

import { computed, ref, type ComputedRef, type Ref } from 'vue'

import { fetchHealth } from '../api/client'
import { asErrorMessage, isApiError } from '../api/errors'
import type { HealthResponse } from '../api/types'
import {
  browserStorage,
  persistApiBase,
  resetApiBaseToDefault,
  resolveApiBase,
  type StorageLike,
} from '../config'

export type HealthState = 'checking' | 'ok' | 'down'

export interface ConnectionApi {
  apiBase: Ref<string>
  health: Ref<HealthResponse | null>
  healthState: Ref<HealthState>
  healthError: Ref<string>
  healthSummary: ComputedRef<string>
  refresh(): Promise<void>
  applyApiBase(base: string): string
  restoreDefaultApiBase(): string
  registeredAgents: ComputedRef<string[]>
}

function currentSearch(): string {
  return typeof window === 'undefined' ? '' : window.location.search
}

export function useConnection(): ConnectionApi {
  const storage: StorageLike | null = browserStorage()
  const search = currentSearch()
  const apiBase = ref(resolveApiBase(search, storage))
  const health = ref<HealthResponse | null>(null)
  const healthState = ref<HealthState>('checking')
  const healthError = ref('')

  const healthSummary = computed<string>(() => {
    if (healthState.value === 'checking') return '正在检测后端…'
    if (healthState.value === 'down') return '后端不可用'
    const count = health.value?.agents.length ?? 0
    return `后端正常 · ${count} 个域`
  })

  const registeredAgents = computed<string[]>(() => health.value?.agents ?? [])

  async function refresh(): Promise<void> {
    healthState.value = 'checking'
    healthError.value = ''
    try {
      const { data } = await fetchHealth(apiBase.value)
      health.value = data
      healthState.value = 'ok'
    } catch (error) {
      health.value = null
      healthState.value = 'down'
      healthError.value = isApiError(error) ? `${error.kind}: ${error.message}` : asErrorMessage(error)
    }
  }

  function applyApiBase(base: string): string {
    apiBase.value = persistApiBase(base, storage)
    return apiBase.value
  }

  function restoreDefaultApiBase(): string {
    apiBase.value = resetApiBaseToDefault(search, storage)
    return apiBase.value
  }

  return {
    apiBase,
    health,
    healthState,
    healthError,
    healthSummary,
    refresh,
    applyApiBase,
    restoreDefaultApiBase,
    registeredAgents,
  }
}
