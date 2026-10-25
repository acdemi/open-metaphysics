<script setup lang="ts">
import type { AnyOutput } from '../../api/types'
import DomainCard from '../DomainCard.vue'

defineProps<{ outputs: readonly AnyOutput[]; runErrors: readonly string[] }>()
</script>

<template>
  <article v-if="runErrors.length" class="card">
    <div class="card-head">
      <h3>运行时有部分域失败</h3>
      <div class="source-strip"><span class="badge badge-warn">errors</span></div>
    </div>
    <div class="card-body">
      <ul class="error-hints">
        <li v-for="(message, index) in runErrors" :key="index">{{ message }}</li>
      </ul>
    </div>
  </article>

  <DomainCard
    v-for="(output, index) in outputs"
    :key="`${output.agent}-${index}`"
    :output="output"
    :index="index"
  />

  <div v-if="outputs.length === 0" class="empty-inline">后端未返回任何域的计算结果。</div>
</template>
