<script setup lang="ts">
import { computed } from 'vue'

import type { ConsensusOutput } from '../../api/types'
import { domainLabel } from '../../config'
import { fmtNum, fmtPercent } from '../../utils/format'
import JsonBlock from '../JsonBlock.vue'

const props = defineProps<{ consensus: ConsensusOutput | null }>()

const result = computed(() => props.consensus?.result ?? null)

const contributions = computed(() => result.value?.contributions ?? [])
const conflicts = computed(() => result.value?.conflicts ?? [])

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
  <div v-if="!consensus" class="empty-inline">
    本次运行没有返回共识：/orchestrate 仅在至少两个域都成功产出结果时生成共识。
  </div>

  <article v-else class="card" data-testid="consensus-card">
    <div class="card-head">
      <h3>
        综合共识
        <span class="card-sub">{{ consensus.engine_version }} · {{ consensus.request_id }}</span>
      </h3>
      <div class="source-strip">
        <span class="badge badge-fact">后端 Consensus 引擎</span>
        <span v-if="result?.recommendation" class="badge badge-interpret">建议：{{ result.recommendation }}</span>
      </div>
    </div>
    <div class="card-body">
      <div class="consensus-hero">
        <div class="confidence-gauge">
          <div class="confidence-value">{{ fmtPercent(result?.overall_confidence ?? null) }}</div>
          <div class="confidence-label">综合置信度 overall_confidence</div>
          <div class="meter"><span :style="{ width: `${gaugeWidth}%` }"></span></div>
          <div class="confidence-label" style="margin-top: 8px">
            策略 {{ meta.strategy ?? '—' }} · {{ meta.agent_count ?? '—' }} 个域
          </div>
        </div>
        <div>
          <p class="card-note" style="margin-bottom: 6px"><strong>合成结论（后端 synthesis 字段原文）：</strong></p>
          <div class="synthesis-text">{{ result?.synthesis ?? '—' }}</div>
        </div>
      </div>

      <div>
        <p class="card-note" style="margin-bottom: 6px">各域贡献：</p>
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

      <div>
        <p class="card-note" style="margin-bottom: 6px">冲突：</p>
        <div style="display: flex; flex-direction: column; gap: 6px">
          <div v-for="(conflict, index) in conflicts" :key="index" class="conflict-item">
            <span class="badge badge-warn">{{ conflict.severity }}</span>
            <span>
              字段 <code>{{ conflict.field }}</code>：
              {{ conflict.agents.map((agent) => domainLabel(agent)).join(' / ') }}
              给出不同值
              <strong v-for="(value, valueIndex) in conflict.values" :key="valueIndex">{{ value }}</strong>
            </span>
          </div>
          <div v-if="conflicts.length === 0" class="empty-inline">后端未检测到跨域冲突。</div>
        </div>
      </div>

      <div>
        <p class="card-note" style="margin-bottom: 6px">一致性矩阵：</p>
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
      </div>

      <p class="card-note">
        共识由后端 <code>ConsensusAgent</code> 基于各域已算出的置信度与五行标签合成；前端不做任何加权或再计算。
      </p>
      <JsonBlock :value="consensus" testid="raw-consensus" />
    </div>
  </article>
</template>
