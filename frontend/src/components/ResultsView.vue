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
import KnowledgeSearchPanel from './panels/KnowledgeSearchPanel.vue'

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
const restored = computed(() => props.analysis.restoredFrom.value)
const domainNames = computed(() => outputs.value.map((output) => domainLabel(output.agent)).join(' · '))
/** 历史会话只保存结果；执行详情里的「请求 agents」以实际输出为准，避免与表单错位。 */
const executionDomains = computed<readonly string[]>(() =>
  restored.value ? outputs.value.map((output) => output.agent) : props.analysis.form.domains,
)
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
  knowledge: '',
  explanation: outputs.value.length > 0 ? String(outputs.value.length) : '',
  consensus: '',
  execution: '',
}))

function tabVisible(tab: TabName): boolean {
  // 单域成功时后端按规则不生成共识，保持不显示；
  // 有运行错误（部分失败）或 ≥2 个成功域时显示，用于解释 consensus 为空的原因。
  return (
    tab !== 'consensus' ||
    consensus.value !== null ||
    runErrors.value.length > 0 ||
    outputs.value.length >= 2
  )
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
  if (
    tab === 'calculation' ||
    tab === 'evidence' ||
    tab === 'knowledge' ||
    tab === 'explanation' ||
    tab === 'consensus' ||
    tab === 'execution'
  ) {
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
          <dd>{{ restored ? '—（历史会话）' : elapsedLabel(analysis.elapsedMs.value) }}</dd>
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

    <div v-if="restored" id="restored-banner" data-testid="restored-banner" class="history-banner">
      <span class="badge badge-neutral">历史会话</span>
      <span>
        已从 <code>GET /sessions/{{ restored.request_id }}</code> 恢复（创建于
        {{ formatDateTime(restored.created_at) }}）；运行耗时等仅属于新请求的字段不适用。
      </span>
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
        id="panel-knowledge"
        data-testid="panel-knowledge"
        aria-labelledby="tab-knowledge"
        :hidden="activeTab !== 'knowledge'"
      >
        <KnowledgeSearchPanel
          :api-base="connection.apiBase.value"
          :question="analysis.form.question"
        />
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
        <ConsensusPanel :consensus="consensus" :outputs="outputs" :run-errors="runErrors" />
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
          :last-payload="restored ? analysis.restoredRequest.value : analysis.lastPayload.value"
          :api-base="connection.apiBase.value"
          :elapsed-ms="analysis.elapsedMs.value"
          :domains="executionDomains"
          :restored="restored !== null"
          :toast="toast"
        />
      </div>
    </div>
  </div>
</template>
