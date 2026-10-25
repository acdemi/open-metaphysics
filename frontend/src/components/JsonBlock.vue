<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    value: unknown
    label?: string
    testid?: string
  }>(),
  { label: '查看原始 JSON', testid: undefined },
)

const text = computed<string>(() => {
  try {
    return JSON.stringify(props.value, null, 2)
  } catch {
    return String(props.value)
  }
})
</script>

<template>
  <details class="raw">
    <summary>{{ label }}</summary>
    <pre :data-testid="testid">{{ text }}</pre>
  </details>
</template>
