<script setup lang="ts">
import { computed } from 'vue'

import { isDomainOutput } from '../api/parse'
import type { AnyOutput, DomainOutput } from '../api/types'
import { domainLabel } from '../config'
import { fmtPercent } from '../utils/format'
import JsonBlock from './JsonBlock.vue'
import BaziResult from './domains/BaziResult.vue'
import LiuyaoResult from './domains/LiuyaoResult.vue'
import QimenResult from './domains/QimenResult.vue'
import ZiweiResult from './domains/ZiweiResult.vue'

const props = defineProps<{ output: AnyOutput; index: number }>()

const domain = computed<DomainOutput | null>(() => (isDomainOutput(props.output) ? props.output : null))

const bazi = computed(() => (domain.value?.agent === 'bazi' ? domain.value.result : null))
const ziwei = computed(() => (domain.value?.agent === 'ziwei' ? domain.value.result : null))
const qimen = computed(() => (domain.value?.agent === 'qimen' ? domain.value.result : null))
const liuyao = computed(() => (domain.value?.agent === 'liuyao' ? domain.value.result : null))
const known = computed(() => bazi.value !== null || ziwei.value !== null || qimen.value !== null || liuyao.value !== null)

const testId = computed(() => `domain-card-${props.output.agent}`)
const rawTestId = computed(() => `raw-result-${props.output.agent}`)
const confidenceLabel = computed(() =>
  typeof props.output.confidence.value === 'number'
    ? `置信度 ${fmtPercent(props.output.confidence.value)}`
    : '',
)
</script>

<template>
  <article class="card" :data-testid="testId" :data-index="index">
    <div class="card-head">
      <h3>
        {{ domainLabel(output.agent) }}
        <span class="card-sub">{{ output.agent }} · {{ output.request_id }}</span>
      </h3>
      <div class="source-strip">
        <span class="badge badge-fact">确定性计算</span>
        <span class="badge badge-neutral">engine {{ output.engine_version }}</span>
        <span v-if="confidenceLabel" class="badge badge-neutral">{{ confidenceLabel }}</span>
      </div>
    </div>
    <div class="card-body">
      <BaziResult v-if="bazi" :chart="bazi" />
      <ZiweiResult v-else-if="ziwei" :chart="ziwei" />
      <QimenResult v-else-if="qimen" :board="qimen" />
      <LiuyaoResult v-else-if="liuyao" :chart="liuyao" />
      <template v-else>
        <div class="empty-inline">该域（{{ output.agent }}）暂无专用渲染器，原始结果见 JSON。</div>
      </template>

      <p class="card-note">此卡内容为后端确定性引擎的原始计算结果，未经前端加工。</p>
      <JsonBlock :value="output.result" :testid="rawTestId" />
      <span v-if="!known" class="sr-only">未知域回退渲染</span>
    </div>
  </article>
</template>
