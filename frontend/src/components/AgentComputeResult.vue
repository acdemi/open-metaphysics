<script setup lang="ts">
import { computed, onUnmounted, watch } from 'vue'

import type { AgentName, AnyOutput } from '../api/types'
import { domainLabel } from '../config'
import { useAgentExplain } from '../composables/useAgentExplain'
import { isAgentName } from '../utils/agentForm'
import { elapsedLabel } from '../utils/format'
import DomainCard from './DomainCard.vue'

const props = defineProps<{ result: AnyOutput; elapsedMs: number; apiBase: string }>()

const explain = useAgentExplain(computed(() => props.apiBase))
const { status, result: explanation, error, elapsedMs: explainElapsed } = explain

const domain = computed(() => domainLabel(props.result.agent))
const agent = computed<AgentName | null>(() =>
  isAgentName(props.result.agent) ? props.result.agent : null,
)
const knowledge = computed(() => explanation.value?.knowledge ?? [])
const providerLabel = computed(() => explanation.value?.provider ?? '离线确定性后备')
const degraded = computed(() => explanation.value?.degraded === true)
const providerError = computed(() => explanation.value?.error ?? null)
const buttonLabel = computed(() => {
  if (status.value === 'loading') return '解释中…'
  return explanation.value ? '重新解释' : '请求解释'
})

watch(
  () => props.result.request_id,
  () => explain.reset(),
)
onUnmounted(() => explain.cancel())

function requestExplain(): void {
  if (!agent.value) return
  void explain.explain(agent.value, props.result)
}

function cancelExplain(): void {
  explain.cancel()
}
</script>

<template>
  <section class="agent-result" data-testid="agent-result">
    <div class="card">
      <div class="card-head">
        <h3>独立计算结果 · {{ domain }}</h3>
        <div class="source-strip">
          <span class="badge badge-fact">单域独立计算</span>
          <span class="badge badge-neutral" data-testid="agent-result-domain">
            {{ result.agent }}
          </span>
          <span class="badge badge-neutral">engine {{ result.engine_version }}</span>
          <span class="badge badge-neutral">耗时 {{ elapsedLabel(elapsedMs) }}</span>
        </div>
      </div>
      <div class="card-body">
        <p class="card-note" data-testid="agent-isolation-note">
          本次只调用 <code>{{ result.agent }}</code> 领域的单个 Agent（request_id：{{
            result.request_id
          }}）；<b>不产生跨域共识</b>，也不包含其他领域结果。该结果与「综合分析」是两种独立业务入口，
          未经过 Orchestration。
        </p>
      </div>
    </div>

    <DomainCard :output="result" :index="0" />

    <article class="card agent-explain" data-testid="agent-explain">
      <div class="card-head">
        <h3>解释 <span class="card-sub">{{ result.agent }}</span></h3>
        <div class="source-strip">
          <span class="badge badge-interpret">Agent Explain</span>
          <span class="badge badge-neutral">POST /agents/{{ result.agent }}/explain</span>
        </div>
      </div>
      <div class="card-body">
        <p class="card-note">
          解释由后端基于<b>本次计算结果</b>生成（接口不重新计算）；知识引用是解释器<b>实际绑定</b>的条目。
          单域 explain 只返回 <code>id</code> 与 <code>source</code>，因此只展示这两项，不补造原文、标签或页码。
        </p>

        <div class="agent-explain-actions">
          <button
            type="button"
            class="btn btn-primary btn-small"
            data-testid="btn-agent-explain"
            :disabled="status === 'loading' || !agent"
            @click="requestExplain"
          >
            {{ buttonLabel }}
          </button>
          <button
            v-if="status === 'loading'"
            type="button"
            class="btn btn-small"
            data-testid="btn-agent-explain-cancel"
            @click="cancelExplain"
          >
            取消
          </button>
          <span v-if="explanation" class="hint">解释耗时 {{ elapsedLabel(explainElapsed) }}</span>
        </div>

        <div v-if="status === 'loading'" class="empty-inline" data-testid="agent-explain-loading">
          正在请求解释…
        </div>
        <div
          v-if="status === 'error'"
          class="history-state history-error"
          data-testid="agent-explain-error"
        >
          {{ error }}
        </div>

        <template v-if="explanation">
          <div
            v-if="explanation.explanation.trim()"
            class="explain-body"
            data-testid="agent-explain-text"
          >
            {{ explanation.explanation }}
          </div>
          <div v-else class="empty-inline" data-testid="agent-explain-empty">
            后端本次未返回解释文本。
          </div>

          <div class="source-strip" data-testid="agent-explain-meta">
            <span class="badge badge-neutral" data-testid="agent-explain-provider">
              {{ providerLabel }}
            </span>
            <span v-if="degraded" class="badge badge-partial" data-testid="agent-explain-degraded">
              已降级
            </span>
            <span v-else class="badge badge-ok">未降级</span>
            <span v-if="knowledge.length > 0" class="badge badge-evidence">
              引用 {{ knowledge.length }} 条知识
            </span>
          </div>

          <div
            v-if="providerError"
            class="provider-error"
            data-testid="agent-explain-provider-error"
          >
            <strong>解释服务错误（不影响计算结果）：</strong>
            kind=<code>{{ providerError.kind }}</code>
            <template v-if="providerError.type"> · type=<code>{{ providerError.type }}</code></template>
            <template v-if="providerError.provider">
              · provider=<code>{{ providerError.provider }}</code>
            </template>
            <div>{{ providerError.message }}</div>
          </div>

          <section class="agent-knowledge" data-testid="agent-knowledge-refs">
            <h4>解释引用的知识（后端实际绑定）</h4>
            <p v-if="knowledge.length === 0" class="empty-inline" data-testid="agent-knowledge-empty">
              本次解释没有返回知识引用。
            </p>
            <ul v-else class="agent-knowledge-list">
              <li
                v-for="(ref, index) in knowledge"
                :key="`${ref.id}-${index}`"
                class="agent-knowledge-item"
                data-testid="agent-knowledge-ref"
              >
                <code class="agent-knowledge-id" data-testid="agent-knowledge-id">{{ ref.id }}</code>
                <span
                  v-if="ref.source.trim()"
                  class="agent-knowledge-source"
                  data-testid="agent-knowledge-source"
                >
                  来源：{{ ref.source }}
                </span>
                <span
                  v-else
                  class="agent-knowledge-source is-missing"
                  data-testid="agent-knowledge-source"
                >
                  来源缺失（后端未提供）
                </span>
                <p v-if="ref.text" class="agent-knowledge-text">{{ ref.text }}</p>
              </li>
            </ul>
            <p class="card-note" data-testid="agent-knowledge-boundary">
              这些引用来自本次解释链，<b>不是</b>「综合分析 → 知识检索」里用户主动发起的独立检索结果；
              即使 id 相同，也不能据此推断某次独立检索参与了本次解释。
            </p>
          </section>
        </template>
      </div>
    </article>
  </section>
</template>
