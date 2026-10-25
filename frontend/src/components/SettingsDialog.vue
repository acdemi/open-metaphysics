<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import type { ConnectionApi } from '../composables/useConnection'

const props = defineProps<{ open: boolean; connection: ConnectionApi }>()
const emit = defineEmits<{ 'update:open': [value: boolean] }>()

const dialog = ref<HTMLDialogElement | null>(null)
const apiBaseInput = ref('')

const corsHint = computed(
  () => `OM_CORS_ORIGINS=${typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:5173'}`,
)

watch(
  () => props.open,
  (open) => {
    const element = dialog.value
    if (!element) return
    if (open) {
      apiBaseInput.value = props.connection.apiBase.value
      if (!element.open) element.showModal()
    } else if (element.open) {
      element.close()
    }
  },
)

function close(): void {
  emit('update:open', false)
}

function save(): void {
  props.connection.applyApiBase(apiBaseInput.value)
  close()
}

function restoreDefault(): void {
  apiBaseInput.value = props.connection.restoreDefaultApiBase()
}
</script>

<template>
  <dialog
    id="settings-dialog"
    ref="dialog"
    class="settings-dialog"
    aria-labelledby="settings-title"
    @close="close"
    @cancel="close"
  >
    <form method="dialog" id="settings-form" class="settings-form" @submit.prevent="save">
      <h2 id="settings-title">后端连接设置</h2>
      <div class="field">
        <label for="settings-api-base">API 基础地址</label>
        <input
          id="settings-api-base"
          v-model="apiBaseInput"
          type="url"
          placeholder="http://127.0.0.1:8000"
          spellcheck="false"
        />
        <p class="field-hint">
          默认读自 <code>src/config/index.ts</code>，也可用 <code>?api=</code> 查询参数覆盖；此处修改会保存到浏览器 localStorage。
        </p>
      </div>
      <div class="settings-note">
        <p><strong>跨域提示：</strong>若前端与服务端不在同一来源，启动后端时需允许该来源：</p>
        <pre>{{ corsHint }}</pre>
      </div>
      <div class="settings-actions">
        <button type="button" class="btn" id="btn-settings-default" @click="restoreDefault">恢复默认</button>
        <button type="submit" class="btn btn-primary" value="save">保存并重新检测</button>
      </div>
    </form>
  </dialog>
</template>
