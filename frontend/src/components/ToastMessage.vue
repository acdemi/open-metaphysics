<script setup lang="ts">
import type { ToastApi } from '../composables/useToast'

defineProps<{ toast: ToastApi }>()
</script>

<template>
  <div class="toast" role="status" :data-show="toast.visible.value ? 'true' : 'false'">
    {{ toast.message.value }}
  </div>
</template>
