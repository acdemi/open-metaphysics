<script setup lang="ts">
import { ref } from 'vue'

import type { AnyOutput, ExplainDetail, KnowledgeChunk } from '../../api/types'
import { domainLabel } from '../../config'

const props = defineProps<{
  outputs: readonly AnyOutput[]
  details: Record<string, ExplainDetail>
}>()

const expanded = ref<Set<string>>(new Set())

function narrativeChunks(agent: string): KnowledgeChunk[] {
  const chunks = props.details[agent]?.knowledge ?? []
  return chunks.filter((chunk) => typeof chunk.text === 'string' && chunk.text.trim().length > 0)
}

function itemKey(agent: string, index: number): string {
  return `${agent}-${index}`
}

function isExpanded(agent: string, index: number): boolean {
  return expanded.value.has(itemKey(agent, index))
}

function toggle(agent: string, index: number): void {
  const key = itemKey(agent, index)
  const next = new Set(expanded.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  expanded.value = next
}

function knowledgeCount(agent: string): number {
  return props.details[agent]?.knowledge.length ?? 0
}
</script>

<template>
  <article
    v-for="(output, index) in outputs"
    :key="`${output.agent}-${index}`"
    class="card"
    :data-testid="`evidence-card-${output.agent}`"
    :data-index="index"
  >
    <div class="card-head">
      <h3>{{ domainLabel(output.agent) }} 的知识证据 <span class="card-sub">{{ knowledgeCount(output.agent) }} 条</span></h3>
      <div class="source-strip"><span class="badge badge-evidence">检索证据</span></div>
    </div>
    <div class="card-body">
      <p v-if="narrativeChunks(output.agent).length > 0" class="card-note">
        <strong>如何阅读：</strong>以下片段由后端在冻结知识语料中检索后随解释返回，含来源书名 / 章节与节点 ID；它们用于给解释提供语境，<strong>不是</strong>对上方计算结论的证明。当前接口只返回 <code>id</code>、<code>source</code> 与片段原文。
      </p>
      <p v-else class="card-note">
        该域本次没有返回知识片段；页面不会用本地知识或模型记忆补齐。
      </p>

      <div v-if="narrativeChunks(output.agent).length > 0" class="evidence-list">
        <div
          v-for="(chunk, chunkIndex) in narrativeChunks(output.agent)"
          :key="chunk.id || chunkIndex"
          class="evidence-item"
        >
          <div class="evidence-head">
            <span class="evidence-source">{{ chunk.source || '（未提供来源）' }}</span>
            <span class="evidence-id">{{ chunk.id }}</span>
          </div>
          <div class="evidence-text" :class="{ clamped: !isExpanded(output.agent, chunkIndex) }">
            {{ chunk.text }}
          </div>
          <button
            type="button"
            class="btn btn-small evidence-toggle"
            :data-testid="`btn-evidence-toggle-${output.agent}-${chunkIndex}`"
            @click="toggle(output.agent, chunkIndex)"
          >
            {{ isExpanded(output.agent, chunkIndex) ? '收起' : '展开全文' }}
          </button>
        </div>
      </div>
      <div v-else class="empty-inline">本次解释链路未返回可展示的知识片段（或该域未配置检索器）。</div>
    </div>
  </article>
</template>
