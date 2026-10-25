<script setup lang="ts">
import type { ConnectionApi } from '../composables/useConnection'

const props = defineProps<{ connection: ConnectionApi }>()
const emit = defineEmits<{ openSettings: [] }>()

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
