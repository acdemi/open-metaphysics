<script setup lang="ts">
import { computed } from 'vue'

import type { BaziChart, BaziPillar, PillarPosition } from '../../api/types'
import { formatDateTime } from '../../utils/timezone'

const props = defineProps<{ chart: BaziChart }>()

const POSITIONS: readonly PillarPosition[] = ['year', 'month', 'day', 'hour']
const POSITION_LABELS: Record<PillarPosition, string> = {
  year: '年柱',
  month: '月柱',
  day: '日柱',
  hour: '时柱',
}

const pillars = computed<Record<PillarPosition, BaziPillar | null>>(() => {
  const map: Record<PillarPosition, BaziPillar | null> = { year: null, month: null, day: null, hour: null }
  for (const pillar of props.chart.pillars) map[pillar.position] = pillar
  return map
})

const tenGods = computed(() => Object.entries(props.chart.ten_gods_map))
</script>

<template>
  <div class="kv-grid">
    <div class="kv">
      <dt>日主</dt>
      <dd><strong>{{ chart.day_master }}</strong>（{{ chart.day_master_element }}）</dd>
    </div>
    <div class="kv">
      <dt>月令（节）</dt>
      <dd>{{ chart.month_boundary }}</dd>
    </div>
    <div class="kv">
      <dt>立春年界</dt>
      <dd>{{ formatDateTime(chart.year_boundary) }}</dd>
    </div>
    <div class="kv">
      <dt>性别处理</dt>
      <dd>{{ chart.gender_assumed ? '未提供性别，后端按 unknown 推定' : '已按提供的性别计算大运方向' }}</dd>
    </div>
  </div>

  <div class="pillars" role="table" aria-label="四柱">
    <div class="ph">四柱</div>
    <div v-for="position in POSITIONS" :key="`h-${position}`" class="ph">{{ POSITION_LABELS[position] }}</div>

    <div class="ph">天干</div>
    <div v-for="position in POSITIONS" :key="`s-${position}`" class="glyph">
      {{ pillars[position]?.stem ?? '—' }}
    </div>

    <div class="ph">地支</div>
    <div v-for="position in POSITIONS" :key="`b-${position}`" class="glyph-branch">
      {{ pillars[position]?.branch ?? '—' }}
    </div>

    <div class="ph">藏干</div>
    <div v-for="position in POSITIONS" :key="`h-${position}`" class="sub">
      {{ pillars[position]?.hidden_stems.join(' · ') || '—' }}
    </div>

    <div class="ph">纳音</div>
    <div v-for="position in POSITIONS" :key="`n-${position}`" class="sub">
      {{ pillars[position]?.nayin ?? '—' }}
    </div>

    <div class="ph">十神</div>
    <div v-for="position in POSITIONS" :key="`t-${position}`" class="ten-god">
      {{ pillars[position]?.ten_god ?? '—' }}
    </div>
  </div>

  <div v-if="tenGods.length">
    <p class="card-note" style="margin-bottom: 6px">十神对照（含藏干）：</p>
    <div class="chips">
      <span v-for="[stem, god] in tenGods" :key="stem" class="chip"><b>{{ stem }}</b>{{ god }}</span>
    </div>
  </div>

  <div>
    <p class="card-note" style="margin-bottom: 6px">大运（{{ chart.dayun.length }} 步）：</p>
    <div v-if="chart.dayun.length" class="table-wrap">
      <table class="data">
        <thead>
          <tr><th>大运</th><th>起止年龄</th><th>干支</th><th>起始时间</th></tr>
        </thead>
        <tbody>
          <tr v-for="step in chart.dayun" :key="step.index">
            <td class="num">{{ step.index }}</td>
            <td>{{ step.start_age }}–{{ step.end_age }} 岁</td>
            <td><strong>{{ step.stem }}{{ step.branch }}</strong></td>
            <td>{{ formatDateTime(step.start_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="empty-inline">后端未返回大运数据。</div>
  </div>
</template>
