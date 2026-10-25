<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import AnalysisForm from './components/AnalysisForm.vue'
import AppHeader from './components/AppHeader.vue'
import EmptyState from './components/EmptyState.vue'
import ErrorState from './components/ErrorState.vue'
import LoadingState from './components/LoadingState.vue'
import ResultsView from './components/ResultsView.vue'
import SettingsDialog from './components/SettingsDialog.vue'
import ToastMessage from './components/ToastMessage.vue'
import { useAnalysis } from './composables/useAnalysis'
import { useConnection } from './composables/useConnection'
import { useToast } from './composables/useToast'

const connection = useConnection()
const analysis = useAnalysis(connection.apiBase)
const toast = useToast()
const settingsOpen = ref(false)

onMounted(async () => {
  await connection.refresh()
  document.body.dataset.appReady = 'true'
})

watch(connection.apiBase, () => {
  settingsOpen.value = false
  void connection.refresh()
})

function retry(): void {
  if (analysis.lastPayload.value) void analysis.rerun()
  else analysis.resetDemo()
}
</script>

<template>
  <a class="skip-link" href="#main">跳到主要内容</a>

  <AppHeader :connection="connection" @open-settings="settingsOpen = true" />

  <main id="main" class="layout">
    <AnalysisForm :analysis="analysis" :connection="connection" />

    <section class="results-panel" aria-labelledby="results-title">
      <h2 id="results-title" class="sr-only">分析结果</h2>

      <EmptyState v-if="analysis.view.value === 'empty'" />
      <LoadingState
        v-else-if="analysis.view.value === 'loading'"
        :elapsed-ms="analysis.elapsedMs.value"
        :steps="analysis.steps.value"
        :api-base="connection.apiBase.value"
        :domains="analysis.form.domains"
        @cancel="analysis.cancel()"
      />
      <ErrorState
        v-else-if="analysis.view.value === 'error' && analysis.error.value"
        :error="analysis.error.value"
        @retry="retry"
        @open-settings="settingsOpen = true"
      />
      <ResultsView
        v-else-if="analysis.view.value === 'results' && analysis.result.value"
        :analysis="analysis"
        :connection="connection"
        :toast="toast"
      />
    </section>
  </main>

  <footer class="site-footer">
    <div>
      <strong>OpenMetaphysics</strong> 前端 MVP · 计算来自 <code>/orchestrate</code> 真实响应，
      解释默认为离线确定性后备（<code>OM_ENABLE_EXPLAINER</code> 未启用时不调用 LLM）。
    </div>
    <div id="footer-api" class="footer-api">后端地址：{{ connection.apiBase.value }}</div>
  </footer>

  <SettingsDialog v-model:open="settingsOpen" :connection="connection" />
  <ToastMessage :toast="toast" />
</template>
