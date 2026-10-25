<script setup lang="ts">
import type { AnalysisErrorView } from '../composables/useAnalysis'

defineProps<{ error: AnalysisErrorView }>()
const emit = defineEmits<{ retry: []; openSettings: [] }>()
</script>

<template>
  <div class="state-card error-state" id="results-error" data-testid="results-error">
    <h3 id="error-title">{{ error.title }}</h3>
    <p id="error-message">{{ error.message }}</p>
    <ul v-if="error.hints.length" class="error-hints" id="error-hints">
      <li v-for="(hint, index) in error.hints" :key="index">{{ hint }}</li>
    </ul>
    <div v-if="error.raw" class="error-detail" id="error-detail">
      <details>
        <summary>原始错误信息</summary>
        <pre id="error-raw">{{ error.raw }}</pre>
      </details>
    </div>
    <div class="state-actions">
      <button type="button" class="btn btn-primary" id="btn-error-retry" @click="emit('retry')">重试</button>
      <button type="button" class="btn" id="btn-error-settings" @click="emit('openSettings')">
        检查后端地址
      </button>
    </div>
  </div>
</template>
