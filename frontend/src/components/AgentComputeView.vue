<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'

import { useAgentCompute } from '../composables/useAgentCompute'
import { DOMAINS } from '../config'
import AgentComputeForm from './AgentComputeForm.vue'
import AgentComputeResult from './AgentComputeResult.vue'

const props = defineProps<{ apiBase: string }>()

const compute = useAgentCompute(computed(() => props.apiBase))
const { selected, status, result, error, elapsedMs, agentsLoading, agentsError } = compute

const activeEngineVersion = computed(
  () => compute.agents.value.find((agent) => agent.name === selected.value)?.engine_version ?? '',
)

onMounted(() => {
  void compute.init()
})

onUnmounted(() => {
  compute.cancel()
})
</script>

<template>
  <main class="layout agent-layout" id="agent-compute" data-testid="agent-compute">
    <aside class="panel agent-panel">
      <div class="panel-head">
        <h2>领域独立计算</h2>
        <span class="badge badge-fact">POST /agents/{name}/compute</span>
      </div>
      <p class="panel-note">
        选择一个领域 Agent 直接计算，不经过编排：<b>不产生跨域共识</b>，也不调用其他领域。
        输入字段来自后端各领域的 JSON Schema。
      </p>
      <p v-if="agentsLoading" class="card-note" data-testid="agent-agents-loading">
        正在读取已注册 Agent…
      </p>
      <p v-else-if="agentsError" class="card-note history-error" data-testid="agent-agents-error">
        {{ agentsError }}（仍可按内置领域元数据选择）
      </p>

      <div class="agent-domain-grid" data-testid="agent-domain-list">
        <button
          v-for="domain in DOMAINS"
          :key="domain.id"
          type="button"
          class="agent-domain"
          :class="{ 'is-active': selected === domain.id }"
          :aria-pressed="selected === domain.id ? 'true' : 'false'"
          :data-testid="`agent-domain-${domain.id}`"
          @click="compute.selectAgent(domain.id)"
        >
          <span class="agent-domain-label">{{ domain.label }}</span>
          <span class="agent-domain-latin">{{ domain.latin }}</span>
          <span class="agent-domain-desc">{{ domain.description }}</span>
          <span v-if="activeEngineVersion && selected === domain.id" class="agent-domain-engine">
            engine {{ activeEngineVersion }}
          </span>
        </button>
      </div>

      <AgentComputeForm :compute="compute" />
    </aside>

    <section class="results agent-results" aria-live="polite">
      <div v-if="status === 'idle'" class="empty-inline" data-testid="agent-idle">
        选择领域、填写参数后点击「开始计算」。独立计算只返回所选领域的单个 Agent 结果。
      </div>
      <div v-else-if="status === 'loading'" class="empty-inline" data-testid="agent-loading">
        正在调用 {{ selected }} Agent 执行确定性计算…
      </div>
      <div
        v-else-if="status === 'error'"
        class="history-state history-error"
        data-testid="agent-error"
      >
        {{ error }}
      </div>
      <AgentComputeResult
        v-else-if="status === 'success' && result"
        :result="result"
        :elapsed-ms="elapsedMs"
        :api-base="apiBase"
      />
      <div v-else class="empty-inline" data-testid="agent-empty">
        后端未返回该领域的计算结果。
      </div>
    </section>
  </main>
</template>
