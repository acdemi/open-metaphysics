<script setup lang="ts">
import type { ConnectionApi } from '../composables/useConnection'

const props = defineProps<{ connection: ConnectionApi; mode: 'analysis' | 'agent' }>()
const emit = defineEmits<{
  openSettings: []
  openHistory: []
  switchMode: [mode: 'analysis' | 'agent']
}>()

function refresh(): void {
  void props.connection.refresh()
}
</script>

<template>
  <header class="site-header">
    <div class="brand">
      <span class="brand-mark" aria-hidden="true">☯</span>
      <div class="brand-text">
        <h1>开放形而上学 <span class="brand-latin">OpenMetaphysics</span></h1>
        <p class="brand-tagline">本地优先 · 确定性规则引擎 · 前端 MVP</p>
      </div>
    </div>

    <div class="header-actions">
      <div class="mode-switch" role="group" aria-label="业务入口">
        <button
          type="button"
          class="mode-btn"
          :class="{ 'is-active': mode === 'analysis' }"
          :aria-pressed="mode === 'analysis' ? 'true' : 'false'"
          data-testid="mode-analysis"
          @click="emit('switchMode', 'analysis')"
        >
          综合分析
        </button>
        <button
          type="button"
          class="mode-btn"
          :class="{ 'is-active': mode === 'agent' }"
          :aria-pressed="mode === 'agent' ? 'true' : 'false'"
          data-testid="mode-agent"
          @click="emit('switchMode', 'agent')"
        >
          独立计算
        </button>
      </div>
      <button
        type="button"
        class="btn btn-small"
        id="btn-history"
        data-testid="btn-history"
        aria-haspopup="dialog"
        title="查看后端持久化的历史会话并恢复结果"
        @click="emit('openHistory')"
      >
        历史会话
      </button>
      <button
        type="button"
        id="health-pill"
        class="health-pill"
        :data-state="connection.healthState.value"
        data-testid="health-status"
        :title="connection.healthError.value || '点击重新检测后端状态'"
        aria-live="polite"
        @click="refresh"
      >
        <span class="dot" aria-hidden="true"></span>
        <span id="health-text" data-testid="health-text">{{ connection.healthSummary.value }}</span>
      </button>
      <button
        type="button"
        class="icon-btn"
        id="btn-settings"
        aria-haspopup="dialog"
        title="设置后端地址"
        @click="emit('openSettings')"
      >
        <span aria-hidden="true">⚙</span><span class="sr-only">设置</span>
      </button>
    </div>
  </header>
</template>
