<script setup lang="ts">
import { computed } from 'vue'

import type { LiuyaoChart, YaoLine } from '../../api/types'
import { atPosition, CAST_LABELS, hexagramName } from '../../utils/format'

const props = defineProps<{ chart: LiuyaoChart }>()

interface HexagramBox {
  key: string
  title: string
  num: number | null
  lines: readonly YaoLine[]
  showChanging: boolean
}

function sortedDesc(lines: readonly YaoLine[]): YaoLine[] {
  return [...lines].sort((left, right) => right.position - left.position)
}

const boxes = computed<HexagramBox[]>(() => [
  { key: 'original', title: '本卦', num: props.chart.original_hexagram, lines: props.chart.original, showChanging: true },
  { key: 'changed', title: '变卦', num: props.chart.changed_hexagram, lines: props.chart.changed, showChanging: false },
  { key: 'mutual', title: '互卦', num: props.chart.mutual_hexagram, lines: props.chart.mutual, showChanging: false },
])

const detailLines = computed<YaoLine[]>(() => sortedDesc(props.chart.original))

function markFor(line: YaoLine): string {
  if (!line.is_changing) return ''
  return line.cast_value === 9 ? '○' : '×'
}

function changeLabel(line: YaoLine): string {
  if (!line.is_changing) return ''
  return CAST_LABELS[line.cast_value] ?? '动'
}

function hexLabel(num: number | null): string {
  if (num === null) return '无（无动爻）'
  const name = hexagramName(num)
  return name ? `第 ${num} 卦 · ${name}` : `第 ${num} 卦`
}

const castNote = computed<string>(() =>
  props.chart.original.map((line) => `${line.position}:${line.cast_value}`).join(' · '),
)
</script>

<template>
  <div class="kv-grid">
    <div class="kv">
      <dt>本卦</dt>
      <dd><strong>{{ hexLabel(chart.original_hexagram) }}</strong></dd>
    </div>
    <div class="kv"><dt>变卦</dt><dd>{{ hexLabel(chart.changed_hexagram) }}</dd></div>
    <div class="kv"><dt>互卦</dt><dd>{{ hexLabel(chart.mutual_hexagram) }}</dd></div>
    <div class="kv"><dt>宫位</dt><dd>{{ chart.palace }}（{{ chart.palace_element }}）</dd></div>
    <div class="kv"><dt>用神</dt><dd>{{ chart.yong_shen ?? '未判定' }}</dd></div>
    <div class="kv"><dt>世 / 应</dt><dd>{{ chart.shi_position }} 爻 / {{ chart.ying_position }} 爻</dd></div>
  </div>

  <div class="hexagrams">
    <div v-for="box in boxes" :key="box.key" class="hexagram-box">
      <div class="hexagram-title"><span>{{ box.title }}</span></div>
      <div class="hexagram-name">
        {{ box.num === null ? '—' : hexagramName(box.num) ?? '—' }}
        <span class="num">{{ hexLabel(box.num) }}</span>
      </div>
      <div class="yao-lines">
        <div
          v-for="line in sortedDesc(box.lines)"
          :key="line.position"
          class="yao-line"
          :class="{ 'is-changing': box.showChanging && line.is_changing }"
          :title="`第 ${line.position} 爻`"
        >
          <span class="pos">{{ line.position }}</span>
          <span class="yao-bars">
            <template v-if="line.is_yin">
              <span class="yao-bar half"></span><span class="yao-gap"></span><span class="yao-bar half"></span>
            </template>
            <span v-else class="yao-bar"></span>
          </span>
          <span class="mark">{{ box.showChanging ? markFor(line) : '' }}</span>
        </div>
      </div>
    </div>
  </div>

  <div class="liuyao-detail scroll-x">
    <div class="liuyao-rows">
      <div class="hdr">爻位</div>
      <div class="hdr">阴阳 / 动</div>
      <div class="hdr">纳甲</div>
      <div class="hdr">六亲</div>
      <div class="hdr">六神</div>
      <div class="hdr">世应</div>
      <template v-if="detailLines.length > 0">
        <template v-for="line in detailLines" :key="line.position">
          <div>{{ line.position }}</div>
          <div>
            {{ line.is_yin ? '阴' : '阳' }}
            <span v-if="line.is_changing" class="badge badge-warn">{{ changeLabel(line) }}</span>
          </div>
          <div>{{ atPosition(chart.najia, line.position) ?? '—' }}</div>
          <div>{{ atPosition(chart.liu_qin, line.position) ?? '—' }}</div>
          <div>{{ atPosition(chart.liu_shen, line.position) ?? '—' }}</div>
          <div class="shi">
            <span v-if="line.position === chart.shi_position" class="badge badge-fact">世</span>
            <span v-if="line.position === chart.ying_position" class="badge badge-interpret">应</span>
          </div>
        </template>
      </template>
      <div v-else class="empty-inline" style="grid-column: 1 / -1">后端未返回爻数据。</div>
    </div>
  </div>

  <p class="card-note">
    起卦值：{{ castNote }}（6 老阴 / 7 少阳 / 8 少阴 / 9 老阳）。未显式提供 <code>seed</code> 时，起卦由后端按请求确定性派生的种子决定。
  </p>
</template>
