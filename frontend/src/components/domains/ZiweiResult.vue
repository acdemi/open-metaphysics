<script setup lang="ts">
import { computed } from 'vue'

import type { ZiweiChart, ZiweiPalace } from '../../api/types'
import { YIN_YANG_LABELS } from '../../utils/format'

const props = defineProps<{ chart: ZiweiChart }>()

const palaces = computed<ZiweiPalace[]>(() =>
  [...props.chart.palaces].sort((left, right) => left.index - right.index),
)

function palaceName(index: number): string {
  const palace = palaces.value.find((item) => item.index === index)
  return palace?.name ?? `#${index}`
}

const yinYangLabel = computed(() => YIN_YANG_LABELS[props.chart.yin_yang] ?? props.chart.yin_yang)
</script>

<template>
  <div class="kv-grid">
    <div class="kv"><dt>五行局</dt><dd>{{ chart.wuxing_ju }}</dd></div>
    <div class="kv"><dt>阴阳</dt><dd>{{ yinYangLabel }}</dd></div>
    <div class="kv">
      <dt>命宫</dt>
      <dd>{{ palaceName(chart.fate_palace_index) }}（索引 {{ chart.fate_palace_index }}）</dd>
    </div>
    <div class="kv">
      <dt>身宫</dt>
      <dd>{{ palaceName(chart.body_palace_index) }}（索引 {{ chart.body_palace_index }}）</dd>
    </div>
  </div>

  <p class="card-note">
    十二宫按后端返回的 index 0–11 顺序展示（非传统宫位排布还原）。辅星字段由后端返回；当前该接口未填充辅星时为「无主星」占位。
  </p>

  <div v-if="palaces.length" class="palace-grid">
    <div
      v-for="palace in palaces"
      :key="palace.index"
      class="palace"
      :class="{ 'is-fate': palace.is_fate_palace, 'is-body': palace.is_body_palace }"
    >
      <div class="palace-head">
        <span class="palace-name">{{ palace.name }}</span>
        <span class="palace-pos">#{{ palace.index }} {{ palace.earthly_branch }}{{ palace.heavenly_stem }}</span>
      </div>
      <div class="star-list">
        <template v-if="palace.main_stars.length > 0 || palace.auxiliary_stars.length > 0">
          <span v-for="star in palace.main_stars" :key="`m-${star}`" class="star">{{ star }}</span>
          <span v-for="star in palace.auxiliary_stars" :key="`a-${star}`" class="star aux">{{ star }}</span>
        </template>
        <span v-else class="star aux">无主星</span>
      </div>
      <div class="palace-flags">
        <span v-if="palace.is_fate_palace" class="badge badge-fact">命宫</span>
        <span v-if="palace.is_body_palace" class="badge badge-interpret">身宫</span>
      </div>
    </div>
  </div>
  <div v-else class="empty-inline">后端未返回宫位数据。</div>

  <p v-if="chart.calendar_note" class="card-note">日历备注：{{ chart.calendar_note }}</p>
</template>
