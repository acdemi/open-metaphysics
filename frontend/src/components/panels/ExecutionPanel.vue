<script setup lang="ts">
import { ref } from 'vue'

import { fetchSession, fetchTraces } from '../../api/client'
import { isApiError } from '../../api/errors'
import type { OrchestrationRequest, OrchestrationResponse, ReasoningStep } from '../../api/types'
import type { AgentName } from '../../api/types'
import { domainLabel } from '../../config'
import type { ToastApi } from '../../composables/useToast'
import { elapsedLabel, formatScalar, scalarEntries } from '../../utils/format'
import { formatDateTime } from '../../utils/timezone'
import JsonBlock from '../JsonBlock.vue'

const props = defineProps<{
  result: OrchestrationResponse
  lastPayload: OrchestrationRequest | null
  apiBase: string
  elapsedMs: number
  domains: readonly AgentName[]
  toast: ToastApi
}>()

const outputVisible = ref(false)
const outputText = ref('')
const loadingKey = ref<'session' | 'traces' | null>(null)

function stepChips(step: ReasoningStep): { key: string; value: string }[] {
  const chips: { key: string; value: string }[] = []
  for (const [key, value] of Object.entries(step.inputs)) {
    chips.push({ key: `in:${key}`, value: formatScalar(value) })
  }
  for (const [key, value] of Object.entries(step.outputs)) {
    chips.push({ key: `out:${key}`, value: formatScalar(value) })
  }
  return chips
}

async function load(kind: 'session' | 'traces'): Promise<void> {
  const requestId = props.result.request_id
  loadingKey.value = kind
  outputVisible.value = true
  outputText.value = '读取中…'
  try {
    const response =
      kind === 'session'
        ? await fetchSession(props.apiBase, requestId)
        : await fetchTraces(props.apiBase, requestId)
    outputText.value = JSON.stringify(response.data, null, 2)
    props.toast.show(kind === 'session' ? '已读取会话' : '已读取追踪')
  } catch (error) {
    const message = isApiError(error) ? `${error.kind}: ${error.message}` : String(error)
    outputText.value = `读取失败（${message}）`
    props.toast.show('读取失败')
  } finally {
    loadingKey.value = null
  }
}
</script>

<template>
  <article class="card" data-testid="execution-overview">
    <div class="card-head">
      <h3>请求级执行信息</h3>
      <div class="source-strip"><span class="badge badge-neutral">/orchestrate</span></div>
    </div>
    <div class="card-body">
      <div class="kv-grid">
        <div class="kv"><dt>request_id</dt><dd class="mono">{{ result.request_id }}</dd></div>
        <div class="kv"><dt>agents（请求）</dt><dd>{{ domains.join(', ') || '—' }}</dd></div>
        <div class="kv"><dt>explain</dt><dd>true</dd></div>
        <div class="kv"><dt>strategy</dt><dd>weighted</dd></div>
        <div class="kv"><dt>HTTP 耗时</dt><dd>{{ elapsedLabel(elapsedMs) }}</dd></div>
        <div class="kv"><dt>会话 / 追踪</dt><dd>可按下按钮从后端读取</dd></div>
      </div>

      <div class="state-actions" style="margin-top: 0">
        <button
          type="button"
          class="btn btn-small"
          data-action="load-session"
          data-testid="btn-load-session"
          :disabled="loadingKey === 'session'"
          @click="load('session')"
        >
          读取会话 GET /sessions/{id}
        </button>
        <button
          type="button"
          class="btn btn-small"
          data-action="load-traces"
          data-testid="btn-load-traces"
          :disabled="loadingKey === 'traces'"
          @click="load('traces')"
        >
          读取追踪 GET /traces/{id}
        </button>
      </div>
      <pre v-show="outputVisible" id="session-trace-output" data-testid="session-trace-output">{{ outputText }}</pre>

      <div>
        <p class="card-note" style="margin-bottom: 6px">per-agent 错误（errors[]）：</p>
        <ul v-if="result.errors.length > 0" class="error-hints">
          <li v-for="(message, index) in result.errors" :key="index">{{ message }}</li>
        </ul>
        <div v-else class="empty-inline">本次运行没有 per-agent 错误。</div>
      </div>

      <div v-if="lastPayload">
        <p class="card-note" style="margin-bottom: 6px">本次请求体（与发送内容一致，仅 request_id 由提交时生成）：</p>
        <JsonBlock :value="lastPayload" testid="raw-request" />
      </div>
    </div>
  </article>

  <article
    v-for="(output, index) in result.outputs"
    :key="`${output.agent}-${index}`"
    class="card"
    :data-testid="`execution-card-${output.agent}`"
  >
    <div class="card-head">
      <h3>{{ domainLabel(output.agent) }} 执行信封</h3>
      <div class="source-strip"><span class="badge badge-neutral">AgentOutput</span></div>
    </div>
    <div class="card-body">
      <div class="kv-grid">
        <div class="kv"><dt>request_id</dt><dd class="mono">{{ output.request_id }}</dd></div>
        <div class="kv"><dt>agent</dt><dd>{{ output.agent }}</dd></div>
        <div class="kv"><dt>engine_version</dt><dd>{{ output.engine_version }}</dd></div>
        <div class="kv"><dt>computed_at</dt><dd>{{ formatDateTime(output.computed_at) }}</dd></div>
        <div class="kv">
          <dt>confidence</dt>
          <dd>{{ (output.confidence.value * 100).toFixed(1) }}% · {{ output.confidence.method }}</dd>
        </div>
        <div class="kv"><dt>input_hash</dt><dd class="mono">{{ output.input_hash }}</dd></div>
      </div>

      <div v-if="scalarEntries(output.metadata).length" class="chips">
        <span v-for="entry in scalarEntries(output.metadata)" :key="entry.key" class="chip">
          <b>{{ entry.key }}</b>{{ entry.value }}
        </span>
      </div>

      <div>
        <p class="card-note" style="margin-bottom: 6px">
          推理追踪（reasoning_trace，共 {{ output.reasoning_trace.length }} 步）：
        </p>
        <ul v-if="output.reasoning_trace.length > 0" class="trace-list">
          <li v-for="step in output.reasoning_trace" :key="step.step" class="trace-item">
            <span class="trace-step">{{ step.step }}</span>
            <div>
              <div class="trace-head">
                <span class="trace-ref">{{ step.rule_ref }}</span>
                <span class="trace-desc">{{ step.description }}</span>
              </div>
              <div v-if="stepChips(step).length" class="chips">
                <span v-for="chip in stepChips(step)" :key="chip.key" class="chip">
                  <b>{{ chip.key }}</b>{{ chip.value }}
                </span>
              </div>
            </div>
          </li>
        </ul>
        <div v-else class="empty-inline">该域未返回 reasoning_trace。</div>
      </div>

      <JsonBlock :value="output" :testid="`raw-output-${output.agent}`" />
    </div>
  </article>
</template>
