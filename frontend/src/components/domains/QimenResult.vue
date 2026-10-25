<script setup lang="ts">
import { computed } from 'vue'

import type { QimenBoard, QimenCell } from '../../api/types'
import { QIMEN_PALACE_ORDER } from '../../utils/format'

const props = defineProps<{ board: QimenBoard }>()

interface CellRow {
  label: string
  value: string
}

interface PalaceCell {
  palace: number
  cell: QimenCell | null
  rows: CellRow[]
}

const byPalace = computed<Map<number, QimenCell>>(() => {
  const map = new Map<number, QimenCell>()
  for (const cell of props.board.cells) map.set(cell.palace, cell)
  return map
})

function rowsFor(cell: QimenCell): CellRow[] {
  const entries: [string, string | null][] = [
    ['天盘', cell.sky_plate],
    ['地盘', cell.earth_plate],
    ['八神', cell.eight_gods],
    ['九星', cell.nine_stars],
    ['八门', cell.eight_doors],
    ['三奇', cell.three_qi],
  ]
  const rows: CellRow[] = []
  for (const [label, value] of entries) {
    if (value !== null && value !== '') rows.push({ label, value })
  }
  return rows
}

const grid = computed<PalaceCell[]>(() =>
  QIMEN_PALACE_ORDER.map((palace) => {
    const cell = byPalace.value.get(palace) ?? null
    return { palace, cell, rows: cell ? rowsFor(cell) : [] }
  }),
)

const dunLabel = computed<string>(() => {
  if (props.board.dun_type === 'yang') return '阳遁'
  if (props.board.dun_type === 'yin') return '阴遁'
  return props.board.dun_type
})
</script>

<template>
  <div class="kv-grid">
    <div class="kv"><dt>节气</dt><dd>{{ board.solar_term ?? '—' }}</dd></div>
    <div class="kv"><dt>遁 / 局</dt><dd>{{ dunLabel }} · {{ board.ju }} 局</dd></div>
    <div class="kv"><dt>日</dt><dd>{{ board.day_of_month }}</dd></div>
    <div class="kv"><dt>三奇偏移</dt><dd>{{ board.triple_offset }}</dd></div>
  </div>

  <p class="card-note">
    九宫按洛书方位排布：巽4 · 离9 · 坤2 / 震3 · 中5 · 兑7 / 艮8 · 坎1 · 乾6；宫位数据本身来自后端逐宫返回。
  </p>

  <div v-if="board.cells.length > 0" class="qimen-grid">
    <div
      v-for="item in grid"
      :key="item.palace"
      class="qimen-cell"
      :class="{ 'is-central': item.cell?.is_central, 'is-void': item.cell?.is_void }"
    >
      <template v-if="item.cell">
        <div class="qimen-cell-head">
          <span class="qimen-cell-name">{{ item.cell.name }}</span>
          <span class="qimen-cell-idx">#{{ item.cell.palace }}</span>
        </div>
        <div v-for="row in item.rows" :key="row.label" class="qimen-row">
          <span class="k">{{ row.label }}</span><span class="v">{{ row.value }}</span>
        </div>
        <div class="palace-flags">
          <span v-if="item.cell.is_central" class="badge badge-neutral">中宫</span>
          <span v-if="item.cell.is_void" class="badge badge-warn">空亡</span>
        </div>
      </template>
      <template v-else>
        <div class="qimen-cell-head">
          <span class="qimen-cell-name">#{{ item.palace }}</span>
        </div>
        <div class="empty-inline">未返回</div>
      </template>
    </div>
  </div>
  <div v-else class="empty-inline">后端未返回盘面数据。</div>
</template>
