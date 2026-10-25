<script setup lang="ts">
import { computed } from 'vue'

import { domainLabel } from '../config'
import { copyText } from '../utils/clipboard'
import { elapsedLabel } from '../utils/format'
import { formatDateTime } from '../utils/timezone'
import { RESULT_TABS, type AnalysisApi, type TabName } from '../composables/useAnalysis'
import type { ConnectionApi } from '../composables/useConnection'
import type { ToastApi } from '../composables/useToast'
import CalculationPanel from './panels/CalculationPanel.vue'
import ConsensusPanel from './panels/ConsensusPanel.vue'
import EvidencePanel from './panels/EvidencePanel.vue'
import ExecutionPanel from './panels/ExecutionPanel.vue'
import ExplanationPanel from './panels/ExplanationPanel.vue'

const props = defineProps<{
  analysis: AnalysisApi
  connection: ConnectionApi
  toast: ToastApi
}>()

const result = computed(() => props.analysis.result.value)
const outputs = computed(() => result.value?.outputs ?? [])
const consensus = computed(() => result.value?.consensus ?? null)
const details = computed(() => result.value?.explanation_detail ?? {})
const runErrors = computed(() => result.value?.errors ?? [])
const requestId = computed(() => result.value?.request_id ?? '')
const domainNames = computed(() => outputs.value.map((output) => domainLabel(output.agent)).join(' · '))
const computedAt = computed(() => {
  const stamps = outputs.value.map((output) => output.computed_at).filter((stamp) => stamp.length > 0)
  return [...stamps].sort().at(-1) ?? null
})
const knowledgeCount = computed(() =>
  Object.values(details.value).reduce((total, detail) => total + detail.knowledge.length, 0),
)
const statusLabel = computed(() => (runErrors.value.length > 0 ? '部分完成' : '分析完成'))
const statusClass = computed(() => (runErrors.value.length > 0 ? 'badge-warn' : 'badge-ok'))

const activeTab = computed<TabName>(() => props.analysis.activeTab.value)
const tabCounts = computed<Record<TabName, string>>(() => ({
  calculation: outputs.value.length > 0 ? String(outputs.value.length) : '',
  evidence: knowledgeCount.value > 0 ? String(knowledgeCount.value) : '',
  explanation: outputs.value.length > 0 ? String(outputs.value.length) : '',
  consensus: '',
  execution: '',
}))

function tabVisible(tab: TabName): boolean {
  return tab !== 'consensus' || consensus.value !== null
}

function selectTab(tab: TabName): void {
  if (!tabVisible(tab)) return
  props.analysis.setTab(tab)
}

function onTabKeydown(event: KeyboardEvent): void {
  const keys = ['ArrowLeft', 'ArrowRight', 'Home', 'End']
  if (!keys.includes(event.key)) return
  const current = event.currentTarget
  if (!(current instanceof HTMLElement)) return
  const nav = current.closest('.tabs')
  const buttons = nav
    ? [...nav.querySelectorAll<HTMLButtonElement>('button[data-tab]:not([hidden])')]
    : []
  if (buttons.length === 0) return
  const currentIndex = buttons.findIndex((button) => button.dataset.tab === activeTab.value)
  let next = currentIndex
  if (event.key === 'ArrowRight') next = (currentIndex + 1) % buttons.length
  if (event.key === 'ArrowLeft') next = (currentIndex - 1 + buttons.length) % buttons.length
  if (event.key === 'Home') next = 0
  if (event.key === 'End') next = buttons.length - 1
  const target = buttons[next]
  if (!target) return
  event.preventDefault()
  const tab = target.dataset.tab
  if (tab === 'calculation' || tab === 'evidence' || tab === 'explanation' || tab === 'consensus' || tab === 'execution') {
    selectTab(tab)
  }
  target.focus()
}

async function copyRequestId(): Promise<void> {
  const ok = await copyText(requestId.value)
  props.toast.show(ok ? '已复制请求 ID' : '复制失败，请手动选择')
}

function rerun(): void {
  void props.analysis.rerun()
}
</script>

<template>
  <div id="results" data-testid="results">
    <div class="summary-bar" id="results-summary" data-testid="results-summary">
      <div class="summary-status" id="summary-status">
        <span class="badge" :class="statusClass">{{ statusLabel }}</span>
        <h2>{{ domainNames }} 分析结果</h2>
        <button type="button" class="btn btn-small" data-action="rerun" style="margin-left: auto" @click="rerun">
          再次分析
        </button>
      </div>
      <dl class="summary-meta" id="summary-meta">
        <div>
          <dt>请求 ID</dt>
          <dd>
            {{ requestId }}
            <button type="button" class="copy-inline" data-action="copy-request-id" @click="copyRequestId">
              复制
            </button>
          </dd>
        </div>
        <div>
          <dt>耗时</dt>
          <dd>{{ elapsedLabel(analysis.elapsedMs.value) }}</dd>
        </div>
        <div>
          <dt>计算完成时间</dt>
          <dd>{{ formatDateTime(computedAt) }}</dd>
        </div>
        <div>
          <dt>共识</dt>
          <dd>{{ consensus ? '已返回' : '未返回（需 ≥2 个域成功）' }}</dd>
        </div>
        <div>
          <dt>后端</dt>
          <dd>{{ connection.apiBase.value }}</dd>
        </div>
      </dl>
    </div>

    <nav class="tabs" id="tabs" role="tablist" aria-label="结果分区">
      <button
        v-for="tab in RESULT_TABS"
        :key="tab.id"
        type="button"
        class="tab"
        role="tab"
        :id="`tab-${tab.id}`"
        :data-tab="tab.id"
        :data-testid="`tab-${tab.id}`"
        :aria-controls="`panel-${tab.id}`"
        :aria-selected="activeTab === tab.id ? 'true' : 'false'"
        :tabindex="activeTab === tab.id ? 0 : -1"
        :hidden="!tabVisible(tab.id)"
        @click="selectTab(tab.id)"
        @keydown="onTabKeydown"
      >
        {{ tab.label }}
        <span class="tab-count" :data-count="tab.id">{{ tabCounts[tab.id] }}</span>
      </button>
    </nav>

    <div class="tab-panels">
      <div
        class="tab-panel"
        role="tabpanel"
        id="panel-calculation"
        data-testid="panel-calculation"
        aria-labelledby="tab-calculation"
        :hidden="activeTab !== 'calculation'"
      >
        <CalculationPanel :outputs="outputs" :run-errors="runErrors" />
      </div>
      <div
        class="tab-panel"
        role="tabpanel"
        id="panel-evidence"
        data-testid="panel-evidence"
        aria-labelledby="tab-evidence"
        :hidden="activeTab !== 'evidence'"
      >
        <EvidencePanel :outputs="outputs" :details="details" />
      </div>
      <div
        class="tab-panel"
        role="tabpanel"
        id="panel-explanation"
        data-testid="panel-explanation"
        aria-labelledby="tab-explanation"
        :hidden="activeTab !== 'explanation'"
      >
        <ExplanationPanel :outputs="outputs" :details="details" />
      </div>
      <div
        class="tab-panel"
        role="tabpanel"
        id="panel-consensus"
        data-testid="panel-consensus"
        aria-labelledby="tab-consensus"
        :hidden="activeTab !== 'consensus'"
      >
        <ConsensusPanel :consensus="consensus" />
      </div>
      <div
        class="tab-panel"
        role="tabpanel"
        id="panel-execution"
        data-testid="panel-execution"
        aria-labelledby="tab-execution"
        :hidden="activeTab !== 'execution'"
      >
        <ExecutionPanel
          v-if="result"
          :result="result"
          :last-payload="analysis.lastPayload.value"
          :api-base="connection.apiBase.value"
          :elapsed-ms="analysis.elapsedMs.value"
          :domains="analysis.form.domains"
          :toast="toast"
        />
      </div>
    </div>
  </div>
</template>
