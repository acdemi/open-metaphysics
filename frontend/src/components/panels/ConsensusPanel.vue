<script setup lang="ts">
import { computed } from 'vue'

import type { AnyOutput, ConsensusOutput } from '../../api/types'
import { domainLabel } from '../../config'
import { CONSENSUS_EVIDENCE_BOUNDARY, describeConsensusState } from '../../utils/consensus'
import { fmtNum, fmtPercent } from '../../utils/format'
import JsonBlock from '../JsonBlock.vue'

const props = defineProps<{
  consensus: ConsensusOutput | null
  outputs: readonly AnyOutput[]
  runErrors: readonly string[]
}>()

const result = computed(() => props.consensus?.result ?? null)
const state = computed(() =>
  describeConsensusState(props.consensus, props.outputs, props.runErrors),
)

const contributions = computed(() => result.value?.contributions ?? [])
const conflicts = computed(() => result.value?.conflicts ?? [])
const trace = computed(() => props.consensus?.reasoning_trace ?? [])

const statusClass = computed(() => {
  switch (state.value.kind) {
    case 'generated':
      return 'badge-ok'
    case 'partial':
      return 'badge-partial'
    case 'unavailable':
    case 'none':
      return 'badge-warn'
  }
})

const matrixAgents = computed<string[]>(() => Object.keys(result.value?.agreement_matrix ?? {}))
const matrixRows = computed(() =>
  matrixAgents.value.map((rowAgent) => ({
    agent: rowAgent,
    cells: matrixAgents.value.map((colAgent) => {
      const value = result.value?.agreement_matrix[rowAgent]?.[colAgent]
      return { agent: colAgent, value: typeof value === 'number' ? value : null }
    }),
  })),
)

function level(value: number | null): 'high' | 'mid' | 'low' | '' {
  if (value === null) return ''
  if (value >= 0.7) return 'high'
  if (value >= 0.45) return 'mid'
  return 'low'
}

const gaugeWidth = computed<string>(() => {
  const overall = result.value?.overall_confidence
  if (typeof overall !== 'number') return '0'
  return String(Math.max(0, Math.min(100, overall * 100)))
})

const meta = computed(() => props.consensus?.metadata ?? {})
</script>

<template>
  <article class="card" data-testid="consensus-card">
    <div class="card-head">
      <h3>
        综合共识
        <span class="card-sub">{{ consensus?.engine_version ?? '后端未生成 consensus' }}</span>
      </h3>
      <div class="source-strip">
        <span class="badge" :class="statusClass" data-testid="consensus-status-label">
          {{ state.label }}
        </span>
        <span v-if="result?.recommendation" class="badge badge-interpret">
          建议：{{ result.recommendation }}
        </span>
      </div>
    </div>

    <div class="card-body">
      <p class="card-note" data-testid="consensus-status-reason">
        {{ state.reason }}
        <br />
        后端响应没有 <code>status</code> 字段：上面的状态是界面根据实际 consensus / conflicts / outputs /
        errors 归纳，不计算权重、置信度或支持率，也不把空结果包装成成功。
      </p>

      <div class="consensus-participants" data-testid="consensus-participants">
        <span class="card-note">成功领域（后端 outputs）：</span>
        <span
          v-for="agent in state.successfulAgents"
          :key="`ok-${agent}`"
          class="chip"
          data-testid="consensus-successful-agent"
        >
          {{ domainLabel(agent) }}（{{ agent }}）
        </span>
        <span v-if="state.successfulAgents.length === 0" class="card-note">无</span>
        <span v-if="state.contributionAgents.length > 0" class="card-note">
          参与共识的领域（后端 result.contributions）：
        </span>
        <span
          v-for="agent in state.contributionAgents"
          :key="`part-${agent}`"
          class="chip"
          :data-testid="`consensus-participant-${agent}`"
        >
          {{ domainLabel(agent) }}（{{ agent }}）
        </span>
      </div>

      <div v-if="state.failedEntries.length > 0" class="provider-error" data-testid="consensus-errors">
        <strong>运行错误（后端 <code>errors</code> 原文；不据此推断失败域支持共识）：</strong>
        <ul class="error-hints">
          <li v-for="(entry, index) in state.failedEntries" :key="index">{{ entry }}</li>
        </ul>
      </div>

      <template v-if="consensus && result">
        <div class="consensus-hero">
          <div class="confidence-gauge">
            <div class="confidence-value">{{ fmtPercent(result.overall_confidence ?? null) }}</div>
            <div class="confidence-label">综合置信度 overall_confidence</div>
            <div class="meter"><span :style="{ width: `${gaugeWidth}%` }"></span></div>
            <div class="confidence-label" style="margin-top: 8px">
              策略 {{ meta.strategy ?? '—' }} · {{ meta.agent_count ?? '—' }} 个域
            </div>
          </div>
          <div>
            <p class="card-note" style="margin-bottom: 6px">
              <strong>共识结论（后端 synthesis 字段原文）：</strong>
            </p>
            <div class="synthesis-text">{{ result.synthesis ?? '—' }}</div>
          </div>
        </div>

        <div>
          <p class="card-note" style="margin-bottom: 6px">
            各域贡献（后端 result.contributions，未在前端重新加权）：
          </p>
          <div class="table-wrap">
            <table class="data">
              <thead>
                <tr><th>域</th><th>置信度</th><th>权重</th><th>五行</th><th>摘要</th></tr>
              </thead>
              <tbody>
                <tr v-for="item in contributions" :key="item.agent">
                  <td>{{ domainLabel(item.agent) }}</td>
                  <td class="num">{{ fmtPercent(item.confidence) }}</td>
                  <td class="num">{{ fmtNum(item.weight, 2) }}</td>
                  <td>{{ item.element ?? '—' }}</td>
                  <td>{{ item.summary }}</td>
                </tr>
                <tr v-if="contributions.length === 0"><td colspan="5">无</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <section class="consensus-uncertainty" data-testid="consensus-uncertainty">
          <p class="card-note" style="margin-bottom: 6px">
            分歧与不确定性（冲突 conflicts / 一致性矩阵 agreement_matrix / overall_confidence 原值）：
          </p>
          <div style="display: flex; flex-direction: column; gap: 6px">
            <div v-for="(conflict, index) in conflicts" :key="index" class="conflict-item">
              <span class="badge badge-warn">{{ conflict.severity }}</span>
              <span>
                字段 <code>{{ conflict.field }}</code>：
                {{ conflict.agents.map((agent) => domainLabel(agent)).join(' / ') }}
                给出不同值
                <strong v-for="(value, valueIndex) in conflict.values" :key="valueIndex">{{
                  value
                }}</strong>
              </span>
            </div>
            <div v-if="conflicts.length === 0" class="empty-inline">
              后端未检测到跨域冲突（conflicts 为空）。
            </div>
          </div>

          <p class="card-note" style="margin: 10px 0 6px">
            一致性矩阵（后端 agreement_matrix 原值）：
          </p>
          <div class="table-wrap">
            <table class="matrix">
              <thead>
                <tr>
                  <th>—</th>
                  <th v-for="agent in matrixAgents" :key="agent">{{ domainLabel(agent) }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in matrixRows" :key="row.agent">
                  <th>{{ domainLabel(row.agent) }}</th>
                  <td v-for="cell in row.cells" :key="cell.agent" :data-level="level(cell.value)">
                    {{ cell.value === null ? '—' : cell.value.toFixed(2) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="consensus-evidence" data-testid="consensus-evidence-unavailable">
          <p class="card-note" style="margin-bottom: 6px"><strong>证据与来源：</strong></p>
          <div class="empty-inline">{{ CONSENSUS_EVIDENCE_BOUNDARY }}</div>

          <p class="card-note" style="margin: 10px 0 6px">
            共识审计轨迹（后端 reasoning_trace；这是计算步骤，不是证据来源）：
          </p>
          <ol class="consensus-trace" data-testid="consensus-trace">
            <li
              v-for="step in trace"
              :key="step.step"
              class="consensus-trace-step"
              data-testid="consensus-trace-step"
            >
              <code>{{ step.rule_ref }}</code> — {{ step.description }}
            </li>
            <li v-if="trace.length === 0" class="card-note">后端未返回 reasoning_trace。</li>
          </ol>
        </section>

        <p class="card-note">
          共识由后端 <code>ConsensusAgent</code> 基于各域已算出的置信度与五行标签合成；前端不做任何加权或再计算，
          也不把解释引用或知识检索结果当作 Consensus 证据。
        </p>
        <JsonBlock :value="consensus" testid="raw-consensus" />
      </template>

      <template v-else>
        <div class="empty-inline" data-testid="consensus-none">
          后端未返回共识对象；界面不构造占位结论，也不展示贡献、冲突或证据。
        </div>
        <p class="card-note">
          若需要跨域共识，请确保至少两个领域成功产出结果后重新分析；单域结果不会生成共识。
        </p>
      </template>
    </div>
  </article>
</template>
