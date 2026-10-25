<script setup lang="ts">
import { computed } from 'vue'

import type { LoadingStep } from '../composables/useAnalysis'
import { domainLabel } from '../config'
import type { AgentName } from '../api/types'

const props = defineProps<{
  elapsedMs: number
  steps: readonly LoadingStep[]
  apiBase: string
  domains: readonly AgentName[]
}>()

const emit = defineEmits<{ cancel: [] }>()

const elapsed = computed<string>(() => (props.elapsedMs / 1000).toFixed(1))
const target = computed<string>(() => {
  const names = props.domains.map((domain) => domainLabel(domain)).join(' · ')
  return `${names} → ${props.apiBase}/orchestrate`
})
</script>

<template>
  <div class="state-card loading-state" id="results-loading" data-testid="results-loading">
    <h3>正在请求后端分析…</h3>
    <ol class="loading-steps" id="loading-steps">
      <li
        v-for="step in steps"
        :key="step.key"
        :data-step="step.key"
        :data-state="step.state === 'idle' ? undefined : step.state"
      >
        {{ step.label }}
      </li>
    </ol>
    <p class="loading-meta">
      <span id="loading-elapsed">{{ elapsed }}</span> 秒 · <span id="loading-target">{{ target }}</span>
    </p>
    <button type="button" class="btn btn-small" id="btn-cancel" data-testid="btn-cancel" @click="emit('cancel')">
      取消请求
    </button>
  </div>
</template>
