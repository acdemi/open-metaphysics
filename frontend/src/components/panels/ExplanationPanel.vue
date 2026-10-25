<script setup lang="ts">
import type { AnyOutput, ExplainDetail } from '../../api/types'
import { domainLabel } from '../../config'

const props = defineProps<{
  outputs: readonly AnyOutput[]
  details: Record<string, ExplainDetail>
}>()

function explanationOf(agent: string): string {
  return (props.details[agent]?.explanation ?? '').trim()
}

function providerLabel(agent: string): string {
  const provider = props.details[agent]?.provider ?? null
  return provider ? `provider: ${provider}` : '离线确定性后备'
}

function degradedOf(agent: string): boolean {
  return props.details[agent]?.degraded === true
}

function knowledgeCount(agent: string): number {
  return props.details[agent]?.knowledge.length ?? 0
}

function providerError(agent: string): { kind: string; type: string | null; provider: string | null; message: string | null } | null {
  const error = props.details[agent]?.error
  if (!error) return null
  return {
    kind: error.kind,
    type: error.type ?? null,
    provider: error.provider ?? null,
    message: error.message ?? null,
  }
}
</script>

<template>
  <article
    v-for="(output, index) in outputs"
    :key="`${output.agent}-${index}`"
    class="card"
    :data-testid="`explanation-card-${output.agent}`"
    :data-index="index"
  >
    <div class="card-head">
      <h3>{{ domainLabel(output.agent) }} 的解释 <span class="card-sub">{{ output.agent }}</span></h3>
      <div class="source-strip">
        <span class="badge badge-interpret">生成解释</span>
        <span class="badge badge-neutral">{{ providerLabel(output.agent) }}</span>
        <span v-if="degradedOf(output.agent)" class="badge badge-partial">已降级</span>
        <span v-else class="badge badge-ok">未降级</span>
        <span v-if="knowledgeCount(output.agent) > 0" class="badge badge-evidence">
          引用 {{ knowledgeCount(output.agent) }} 条知识
        </span>
      </div>
    </div>
    <div class="card-body">
      <div
        v-if="explanationOf(output.agent)"
        class="explain-body"
        :data-testid="`explanation-text-${output.agent}`"
      >
        {{ explanationOf(output.agent) }}
      </div>
      <div v-else class="empty-inline">后端本次未返回解释文本。</div>

      <p v-if="degradedOf(output.agent)" class="card-note">
        当前为<strong>降级模式</strong>：未配置 LLM provider（或 provider 调用失败），解释由确定性模板/结果摘要生成，不含任何模型推断。
      </p>
      <p v-else class="card-note">
        解释由已配置的 LLM provider 基于 FACTS + 检索知识生成；FACTS 仍以后端计算结果为准。
      </p>

      <div v-if="providerError(output.agent)" class="provider-error">
        <strong>解释服务错误（不影响计算结果）：</strong>
        kind=<code>{{ providerError(output.agent)?.kind }}</code>
        <template v-if="providerError(output.agent)?.type">
          · type=<code>{{ providerError(output.agent)?.type }}</code>
        </template>
        <template v-if="providerError(output.agent)?.provider">
          · provider=<code>{{ providerError(output.agent)?.provider }}</code>
        </template>
        <div>{{ providerError(output.agent)?.message }}</div>
      </div>

      <div class="explain-meta">
        <span>解释来源：<code>explanation_detail["{{ output.agent }}"]</code></span>
        <span>与「{{ domainLabel(output.agent) }}」的计算结果一一对应</span>
      </div>
    </div>
  </article>
</template>
