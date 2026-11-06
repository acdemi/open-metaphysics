<script setup lang="ts">
import { ref, watch } from 'vue'

import type { SessionHistoryApi } from '../composables/useSessionHistory'
import type { StoredSession } from '../api/types'
import { formatDateTime } from '../utils/timezone'

const props = defineProps<{ open: boolean; history: SessionHistoryApi }>()
const emit = defineEmits<{
  'update:open': [value: boolean]
  restored: [session: StoredSession]
}>()

const dialog = ref<HTMLDialogElement | null>(null)

watch(
  () => props.open,
  (open) => {
    const element = dialog.value
    if (!element) return
    if (open) {
      if (!element.open) element.showModal()
    } else if (element.open) {
      element.close()
    }
  },
)

function close(): void {
  emit('update:open', false)
}

async function restore(requestId: string): Promise<void> {
  const session = await props.history.restore(requestId)
  if (session) emit('restored', session)
}
</script>

<template>
  <dialog
    id="session-history-dialog"
    ref="dialog"
    class="settings-dialog history-dialog"
    data-testid="session-history-dialog"
    aria-labelledby="history-title"
    @close="close"
    @cancel="close"
  >
    <div class="history-form">
      <div class="history-head">
        <div>
          <h2 id="history-title">会话历史</h2>
          <p class="card-note">
            来自后端 <code>GET /sessions</code>（持久化存储；默认进程内存，进程重启后清空）。选择一条可恢复其完整结果。
          </p>
        </div>
        <button
          type="button"
          class="btn btn-small"
          data-testid="btn-history-refresh"
          :disabled="history.loading.value"
          @click="history.refresh()"
        >
          刷新
        </button>
      </div>

      <p v-if="history.loading.value" class="history-state" data-testid="history-loading">
        正在读取会话列表…
      </p>
      <p v-else-if="history.error.value" class="history-state history-error" data-testid="history-error">
        {{ history.error.value }}
      </p>
      <p
        v-else-if="history.sessions.value.length === 0"
        class="history-state"
        data-testid="history-empty"
      >
        后端还没有持久化会话：先完成一次分析，再回来查看。
      </p>
      <ul v-else class="session-list" data-testid="session-list">
        <li
          v-for="item in history.sessions.value"
          :key="item.request_id"
          class="session-item"
          :data-session-id="item.request_id"
        >
          <div class="session-meta">
            <code class="session-id">{{ item.request_id }}</code>
            <span class="card-note">创建于 {{ formatDateTime(item.created_at) }}</span>
          </div>
          <button
            type="button"
            class="btn btn-small session-restore"
            :data-session-restore="item.request_id"
            :disabled="history.restoringId.value !== null"
            @click="restore(item.request_id)"
          >
            {{ history.restoringId.value === item.request_id ? '读取中…' : '恢复结果' }}
          </button>
        </li>
      </ul>

      <p
        v-if="history.restoreError.value"
        class="history-state history-error"
        data-testid="history-restore-error"
      >
        {{ history.restoreError.value }}
      </p>

      <div class="history-actions">
        <button type="button" class="btn" data-testid="btn-history-close" @click="close">关闭</button>
      </div>
    </div>
  </dialog>
</template>
