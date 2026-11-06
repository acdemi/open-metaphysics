<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { useKnowledgeSearch } from '../../composables/useKnowledgeSearch'

const props = defineProps<{ apiBase: string; question: string }>()

const knowledge = useKnowledgeSearch(computed(() => props.apiBase))
const {
  query,
  k,
  includeEvidence,
  status,
  chunks,
  error,
  lastQuery,
  corpora,
  corporaLoading,
  corporaError,
} = knowledge

const expanded = ref<Set<number>>(new Set())

onMounted(() => {
  if (!query.value.trim() && props.question.trim()) query.value = props.question
  void knowledge.loadCorpora()
})

onUnmounted(() => {
  knowledge.cancel()
})

function toggle(index: number): void {
  const next = new Set(expanded.value)
  if (next.has(index)) next.delete(index)
  else next.add(index)
  expanded.value = next
}

function runSearch(): void {
  expanded.value = new Set()
  void knowledge.submit()
}
</script>

<template>
  <article class="card knowledge-card" data-testid="knowledge-search">
    <div class="card-head">
      <h3>知识检索</h3>
      <div class="source-strip">
        <span class="badge badge-evidence">检索参考</span>
        <span class="badge badge-neutral">POST /knowledge/search</span>
      </div>
    </div>
    <div class="card-body">
      <p class="card-note knowledge-disclaimer" data-testid="knowledge-disclaimer">
        以下为<b>独立知识检索</b>结果（冻结语料），仅作阅读参考：<b>不是本次命理结论或解释的证据链</b>；
        解释实际引用的知识请看「知识证据」标签页。检索排序/相关度不代表知识正确性，也不等于命理结论置信度。
      </p>

      <div class="knowledge-corpora" data-testid="knowledge-corpora">
        <span v-if="corporaLoading" class="card-note">读取语料状态…</span>
        <span v-else-if="corporaError" class="card-note knowledge-inline-error">{{ corporaError }}</span>
        <template v-else>
          <span
            v-for="corpus in corpora"
            :key="corpus.corpus_id"
            class="chip"
            :data-corpus-id="corpus.corpus_id"
          >
            <b>{{ corpus.corpus_id }}</b>{{ corpus.status ?? '未知' }} · v{{ corpus.version ?? '—' }}
            · 节点 {{ corpus.counts?.nodes ?? 0 }}
          </span>
        </template>
      </div>

      <form class="knowledge-form" @submit.prevent="runSearch">
        <label class="sr-only" for="knowledge-query">检索关键词</label>
        <input
          id="knowledge-query"
          v-model="query"
          data-testid="knowledge-query"
          type="search"
          placeholder="输入关键词，如：紫微 / 日主 / 纳甲"
          autocomplete="off"
        />
        <label class="knowledge-inline-check">
          <input
            v-model="includeEvidence"
            data-testid="knowledge-include-evidence"
            type="checkbox"
          />
          包含关系/引用证据
        </label>
        <label class="knowledge-inline-check">
          条数
          <select v-model.number="k" data-testid="knowledge-k" aria-label="返回条数">
            <option :value="3">3</option>
            <option :value="5">5</option>
            <option :value="10">10</option>
          </select>
        </label>
        <button
          type="submit"
          class="btn btn-primary btn-small"
          data-testid="btn-knowledge-search"
          :disabled="status === 'loading'"
        >
          检索
        </button>
        <button
          v-if="status === 'loading'"
          type="button"
          class="btn btn-small"
          data-testid="btn-knowledge-cancel"
          @click="knowledge.cancel()"
        >
          取消
        </button>
      </form>

      <div v-if="status === 'idle'" class="empty-inline" data-testid="knowledge-idle">
        尚未检索：输入关键词后点击「检索」。
      </div>
      <div v-else-if="status === 'loading'" class="knowledge-loading" data-testid="knowledge-loading">
        正在检索冻结语料…
      </div>
      <div v-else-if="status === 'error'" class="history-state history-error" data-testid="knowledge-error">
        {{ error }}
      </div>
      <div v-else-if="status === 'empty'" class="empty-inline" data-testid="knowledge-empty">
        没有匹配的知识片段：可换关键词、减少条数，或勾选「包含关系/引用证据」后重试。
      </div>
      <template v-else>
        <p class="card-note" data-testid="knowledge-summary">
          查询「{{ lastQuery }}」返回 {{ chunks.length }} 条参考（k={{ k }}，include_evidence={{
            includeEvidence ? 'true' : 'false'
          }}）。后端未返回相关度分数，故不展示分数。
        </p>
        <ul class="knowledge-results" data-testid="knowledge-results">
          <li
            v-for="(chunk, index) in chunks"
            :key="chunk.id"
            class="knowledge-result"
            :data-knowledge-id="chunk.id"
          >
            <div class="knowledge-result-head">
              <code class="knowledge-result-id" data-testid="knowledge-id">{{ chunk.id }}</code>
              <button
                type="button"
                class="btn btn-small knowledge-toggle"
                :data-testid="`knowledge-toggle-${index}`"
                :aria-expanded="expanded.has(index) ? 'true' : 'false'"
                @click="toggle(index)"
              >
                {{ expanded.has(index) ? '收起' : '展开' }}
              </button>
            </div>
            <p
              class="knowledge-text"
              :class="{ clamped: !expanded.has(index) }"
              :data-testid="`knowledge-text-${index}`"
            >
              {{ chunk.text }}
            </p>
            <div class="knowledge-result-meta">
              <span
                v-if="chunk.source.trim()"
                class="knowledge-source"
                :data-testid="`knowledge-source-${index}`"
              >
                来源：{{ chunk.source }}
              </span>
              <span
                v-else
                class="knowledge-source is-missing"
                :data-testid="`knowledge-source-${index}`"
              >
                来源缺失（后端未提供）
              </span>
              <span v-for="tag in chunk.tags ?? []" :key="tag" class="chip">{{ tag }}</span>
            </div>
          </li>
        </ul>
      </template>
    </div>
  </article>
</template>
