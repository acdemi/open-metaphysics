<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import { DOMAINS, GENDER_OPTIONS, TIMEZONE_OPTIONS } from '../config'
import type { AgentName } from '../api/types'
import type { AnalysisApi } from '../composables/useAnalysis'
import type { ConnectionApi } from '../composables/useConnection'
import type { FieldKey } from '../utils/validation'

const props = defineProps<{ analysis: AnalysisApi; connection: ConnectionApi }>()

const {
  form,
  errors,
  preview,
  loading,
  submit,
  resetDemo,
  errorForField,
} = props.analysis

const dateInput = ref<HTMLInputElement | null>(null)
const timeInput = ref<HTMLInputElement | null>(null)
const timezoneInput = ref<HTMLInputElement | null>(null)
const questionInput = ref<HTMLTextAreaElement | null>(null)
const seedInput = ref<HTMLInputElement | null>(null)
const latInput = ref<HTMLInputElement | null>(null)
const lonInput = ref<HTMLInputElement | null>(null)

const fieldElements: Partial<Record<FieldKey, () => HTMLElement | null>> = {
  date: () => dateInput.value,
  time: () => timeInput.value,
  timezone: () => timezoneInput.value,
  question: () => questionInput.value,
  seed: () => seedInput.value,
  lat: () => latInput.value,
  lon: () => lonInput.value,
}

const errorList = computed(() => errors.value)

const healthChecked = computed(() => props.connection.healthState.value === 'ok')
const registeredAgents = computed<readonly string[]>(() => props.connection.registeredAgents.value)

function domainAvailable(id: AgentName): boolean {
  if (!healthChecked.value) return true
  return registeredAgents.value.includes(id)
}

watch(registeredAgents, (agents) => {
  if (agents.length === 0) return
  const kept = form.domains.filter((domain) => agents.includes(domain))
  if (kept.length > 0) {
    form.domains = kept
    return
  }
  form.domains = agents.includes('bazi') ? ['bazi'] : []
})

watch(errorList, (list) => {
  const first = list[0]
  if (!first || !first.field) return
  const target = fieldElements[first.field]?.()
  if (target) void nextTick(() => target.focus())
})

function onSubmit(): void {
  void submit()
}

function onReset(): void {
  resetDemo()
}
</script>

<template>
  <section class="panel input-panel" aria-labelledby="input-title">
    <div class="panel-head">
      <h2 id="input-title">分析输入</h2>
      <p class="panel-sub">字段来自后端 <code>AgentInput</code> / <code>/orchestrate</code> 契约</p>
    </div>

    <form id="analysis-form" novalidate data-testid="form-analysis" @submit.prevent="onSubmit">
      <fieldset class="field-group">
        <legend>
          分析领域 <span class="hint">可多选；选择 2 个及以上域时，后端会额外返回「共识」</span>
        </legend>
        <div id="domain-grid" class="domain-grid">
          <label
            v-for="domain in DOMAINS"
            :key="domain.id"
            class="domain-card"
            :data-domain="domain.id"
            :title="domainAvailable(domain.id) ? '' : `后端未注册该域（${domain.id}）`"
          >
            <input
              v-model="form.domains"
              type="checkbox"
              name="domain"
              :value="domain.id"
              :data-testid="`domain-${domain.id}`"
              :disabled="!domainAvailable(domain.id)"
            />
            <span class="domain-body">
              <span class="domain-name">{{ domain.label }} <em>{{ domain.latin }}</em></span>
              <span class="domain-desc">{{ domain.description }}</span>
              <span class="domain-meta">
                <span class="badge" :class="domain.badgeClass">{{ domain.badge }}</span>
              </span>
            </span>
          </label>
        </div>
      </fieldset>

      <div class="field-row">
        <div class="field">
          <label for="input-date">出生日期 <span class="req">*</span></label>
          <input
            id="input-date"
            ref="dateInput"
            v-model="form.date"
            type="date"
            name="date"
            required
            min="1900-01-01"
            max="2099-12-31"
            data-testid="input-date"
            :aria-invalid="errorForField('date') ? 'true' : undefined"
          />
        </div>
        <div class="field">
          <label for="input-time">出生时间 <span class="req">*</span></label>
          <input
            id="input-time"
            ref="timeInput"
            v-model="form.time"
            type="time"
            name="time"
            required
            step="60"
            data-testid="input-time"
            :aria-invalid="errorForField('time') ? 'true' : undefined"
          />
        </div>
      </div>

      <div class="field">
        <label for="input-timezone">时区（出生地）</label>
        <input
          id="input-timezone"
          ref="timezoneInput"
          v-model="form.timezone"
          type="text"
          name="timezone"
          list="tz-options"
          spellcheck="false"
          autocomplete="off"
          data-testid="input-timezone"
          :aria-invalid="errorForField('timezone') ? 'true' : undefined"
        />
        <datalist id="tz-options">
          <option v-for="zone in TIMEZONE_OPTIONS" :key="zone.value" :value="zone.value">
            {{ zone.label }}
          </option>
        </datalist>
        <p class="field-hint">
          IANA 时区名，用于把出生时间转换成带时区的 ISO 时间；后端要求 <code>born_at</code> 必须带时区。
        </p>
      </div>

      <fieldset class="field-group">
        <legend>性别 <span class="hint">影响八字大运方向；未知时后端会标记 gender_assumed</span></legend>
        <div class="segmented" role="radiogroup" aria-label="性别">
          <label v-for="gender in GENDER_OPTIONS" :key="gender.value">
            <input
              v-model="form.gender"
              type="radio"
              name="gender"
              :value="gender.value"
              :data-testid="`gender-${gender.value}`"
            />
            <span>{{ gender.label }}</span>
          </label>
        </div>
      </fieldset>

      <div class="field">
        <label for="input-question">问题 / 分析主题 <span class="optional">（可选）</span></label>
        <textarea
          id="input-question"
          ref="questionInput"
          v-model="form.question"
          name="question"
          rows="3"
          maxlength="500"
          data-testid="input-question"
          placeholder="例如：今年的工作发展如何？"
          :aria-invalid="errorForField('question') ? 'true' : undefined"
        />
        <p class="field-hint">
          会写入 <code>payload.question</code>，并作为解释链路的检索语境；不影响确定性计算。
        </p>
      </div>

      <details class="advanced">
        <summary>高级参数（可选，均来自后端 schema）</summary>
        <div class="advanced-body">
          <div class="field-row">
            <div class="field">
              <label for="input-seed">起卦种子 <code>seed</code></label>
              <input
                id="input-seed"
                ref="seedInput"
                v-model="form.seed"
                type="number"
                name="seed"
                step="1"
                placeholder="留空则自动"
                data-testid="input-seed"
                :aria-invalid="errorForField('seed') ? 'true' : undefined"
              />
            </div>
            <div class="field">
              <label for="input-lon">经度 <code>longitude</code></label>
              <input
                id="input-lon"
                ref="lonInput"
                v-model="form.lon"
                type="number"
                name="lon"
                step="any"
                min="-180"
                max="180"
                placeholder="-180 ~ 180"
                :aria-invalid="errorForField('lon') ? 'true' : undefined"
              />
            </div>
          </div>
          <div class="field-row">
            <div class="field">
              <label for="input-lat">纬度 <code>latitude</code></label>
              <input
                id="input-lat"
                ref="latInput"
                v-model="form.lat"
                type="number"
                name="lat"
                step="any"
                min="-90"
                max="90"
                placeholder="-90 ~ 90"
                :aria-invalid="errorForField('lat') ? 'true' : undefined"
              />
            </div>
            <div class="field">
              <label for="input-nonce">幂等键 <code>client_nonce</code></label>
              <input
                id="input-nonce"
                v-model="form.nonce"
                type="text"
                name="nonce"
                maxlength="64"
                placeholder="可选"
                autocomplete="off"
              />
            </div>
          </div>
          <p class="field-hint">
            六爻在未提供 <code>casts</code> 时按 <code>seed</code> 确定性起卦；此页面通过 <code>/orchestrate</code> 调用，因此不提供域专属的 <code>casts</code> 字段（该字段仅 <code>/agents/{name}/compute</code> 支持）。
          </p>
        </div>
      </details>

      <div v-if="errorList.length" class="form-errors" id="form-errors" role="alert" data-testid="form-errors">
        <strong>请修正以下 {{ errorList.length }} 处输入：</strong>
        <ul>
          <li v-for="(error, index) in errorList" :key="index">{{ error.message }}</li>
        </ul>
      </div>

      <div class="form-actions">
        <button
          type="submit"
          class="btn btn-primary"
          id="btn-submit"
          data-testid="btn-submit"
          :data-loading="loading ? 'true' : 'false'"
          :disabled="loading"
        >
          <span class="btn-label">{{ loading ? '分析中…' : '开始分析' }}</span>
          <span class="spinner" aria-hidden="true"></span>
        </button>
        <button
          type="button"
          class="btn"
          id="btn-reset"
          data-testid="btn-reset"
          :disabled="loading"
          @click="onReset"
        >
          重置示例
        </button>
      </div>

      <details class="request-preview">
        <summary>本次将发送的请求体（不虚构字段）</summary>
        <pre id="request-preview" data-testid="request-preview">{{ preview }}</pre>
      </details>
    </form>
  </section>
</template>
