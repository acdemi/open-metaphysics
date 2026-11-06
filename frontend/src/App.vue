<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import AnalysisForm from './components/AnalysisForm.vue'
import AgentComputeView from './components/AgentComputeView.vue'
import AppHeader from './components/AppHeader.vue'
import EmptyState from './components/EmptyState.vue'
import ErrorState from './components/ErrorState.vue'
import LoadingState from './components/LoadingState.vue'
import ResultsView from './components/ResultsView.vue'
import SessionHistoryDialog from './components/SessionHistoryDialog.vue'
import SettingsDialog from './components/SettingsDialog.vue'
import ToastMessage from './components/ToastMessage.vue'
import type { StoredSession } from './api/types'
import { useAnalysis } from './composables/useAnalysis'
import { useConnection } from './composables/useConnection'
import { useSessionHistory } from './composables/useSessionHistory'
import { useToast } from './composables/useToast'

const connection = useConnection()
const analysis = useAnalysis(connection.apiBase)
const history = useSessionHistory(connection.apiBase)
const toast = useToast()
const settingsOpen = ref(false)
const historyOpen = ref(false)
const mode = ref<'analysis' | 'agent'>('analysis')

onMounted(async () => {
  await connection.refresh()
  document.body.dataset.appReady = 'true'
})

watch(connection.apiBase, () => {
  settingsOpen.value = false
  historyOpen.value = false
  void connection.refresh()
})

function openHistory(): void {
  historyOpen.value = true
  history.restoreError.value = null
  void history.refresh()
}

function onHistoryRestored(session: StoredSession): void {
  const outcome = analysis.restoreSession(session)
  if (outcome.ok) {
    historyOpen.value = false
    toast.show('已恢复历史会话')
  } else {
    // 会话信封合法但结果无法还原（例如非 /orchestrate 会话）：留在对话框展示原因。
    history.restoreError.value = outcome.message
  }
}

function retry(): void {
  if (analysis.lastPayload.value) void analysis.rerun()
  else analysis.resetDemo()
}
</script>

<template>
  <a class="skip-link" :href="mode === 'analysis' ? '#main' : '#agent-compute'">跳到主要内容</a>

  <AppHeader
    :connection="connection"
    :mode="mode"
    @open-settings="settingsOpen = true"
    @open-history="openHistory"
    @switch-mode="mode = $event"
  />

  <main v-if="mode === 'analysis'" id="main" class="layout">
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

  <AgentComputeView
    v-else
    :key="connection.apiBase.value"
    :api-base="connection.apiBase.value"
  />

  <footer class="site-footer">
    <div v-if="mode === 'analysis'">
      <strong>OpenMetaphysics</strong> 前端 MVP · 计算来自 <code>/orchestrate</code> 真实响应，
      解释默认为离线确定性后备（<code>OM_ENABLE_EXPLAINER</code> 未启用时不调用 LLM）。
    </div>
    <div v-else>
      <strong>OpenMetaphysics</strong> 独立计算 · 结果来自 <code>POST /agents/{name}/compute</code>
      真实响应；单域计算不产生跨域共识。
    </div>
    <div id="footer-api" class="footer-api">后端地址：{{ connection.apiBase.value }}</div>
  </footer>

  <SessionHistoryDialog v-model:open="historyOpen" :history="history" @restored="onHistoryRestored" />
  <SettingsDialog v-model:open="settingsOpen" :connection="connection" />
  <ToastMessage :toast="toast" />
</template>
