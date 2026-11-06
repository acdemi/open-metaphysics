<script setup lang="ts">
import { computed } from 'vue'

import type { AgentComputeApi } from '../composables/useAgentCompute'
import { GENDER_OPTIONS, TIMEZONE_OPTIONS } from '../config'
import { BORN_LOCATION_HINT, FIELD_LABELS } from '../utils/agentForm'
import { enumValues, fieldShape, hasField, isRequired, type FieldShape } from '../utils/agentSchema'

const props = defineProps<{ compute: AgentComputeApi }>()
const {
  draft,
  inputSchema,
  schemaLoading,
  schemaError,
  fieldErrors,
  status,
} = props.compute

/** 通用控件之外的字段由 schema 驱动；复杂字段（出生时刻/casts）用领域专用控件。 */
const EXCLUDED = new Set([
  'request_id',
  'born_at',
  'locale',
  'client_nonce',
  'gender',
  'question',
  'seed',
  'casts',
])

type TextDraftKey = 'dayunCount' | 'lunarMonth' | 'lunarDay'

const DRAFT_KEYS: Record<string, TextDraftKey> = {
  dayun_count: 'dayunCount',
  lunar_month: 'lunarMonth',
  lunar_day: 'lunarDay',
}

interface ExtraField {
  key: string
  draftKey: TextDraftKey
  shape: FieldShape
  required: boolean
  label: string
  testId: string
}

const extraFields = computed<ExtraField[]>(() => {
  const schema = inputSchema.value
  if (!schema) return []
  return Object.keys(schema.properties)
    .filter((key) => !EXCLUDED.has(key))
    .map((key) => {
      const shape = fieldShape(schema, key)
      if (!shape) return null
      const draftKey = DRAFT_KEYS[key]
      if (!draftKey) return null
      return {
        key,
        draftKey,
        shape,
        required: isRequired(schema, key),
        label: FIELD_LABELS[key] ?? shape.title ?? key,
        testId: `agent-${key.replaceAll('_', '-')}`,
      }
    })
    .filter((field): field is ExtraField => field !== null)
})

const genderOptions = computed(() => {
  const schema = inputSchema.value
  const values = schema ? enumValues(schema, 'gender') : []
  const allowed = values.length > 0 ? values : GENDER_OPTIONS.map((item) => item.value)
  return GENDER_OPTIONS.filter((item) => allowed.includes(item.value))
})

const castField = computed(() =>
  inputSchema.value && hasField(inputSchema.value, 'casts')
    ? fieldShape(inputSchema.value, 'casts')
    : null,
)
const bornLocationField = computed(() =>
  inputSchema.value && hasField(inputSchema.value, 'born_location')
    ? fieldShape(inputSchema.value, 'born_location')
    : null,
)
const seedField = computed(() =>
  inputSchema.value && hasField(inputSchema.value, 'seed')
    ? fieldShape(inputSchema.value, 'seed')
    : null,
)
const timezoneChoices = computed(() => {
  const values = TIMEZONE_OPTIONS.map((option) => option.value)
  return values.includes(draft.timezone)
    ? TIMEZONE_OPTIONS
    : [{ value: draft.timezone, label: draft.timezone }, ...TIMEZONE_OPTIONS]
})

function extraPlaceholder(field: ExtraField): string {
  if (field.key === 'lunar_month') return '留空则由公历换算'
  if (field.key === 'lunar_day') return '留空则由公历换算'
  const value = field.shape.defaultValue
  return value === null || value === undefined ? '' : `默认 ${String(value)}`
}

function extraTestId(field: ExtraField): string {
  return field.testId
}

function draftValue(key: TextDraftKey): string {
  return draft[key]
}

function setDraftValue(key: TextDraftKey, value: string): void {
  draft[key] = value
}

function submit(): void {
  void props.compute.submit()
}

function cancel(): void {
  props.compute.cancel()
}

function errorFor(key: string): string {
  return fieldErrors.value[key] ?? ''
}
</script>

<template>
  <form class="agent-form" data-testid="agent-compute-form" @submit.prevent="submit">
    <p v-if="schemaLoading" class="card-note" data-testid="agent-schema-loading">
      正在读取领域输入 Schema…
    </p>
    <p v-else-if="schemaError" class="history-state history-error" data-testid="agent-schema-error">
      {{ schemaError }}
    </p>
    <p v-else-if="inputSchema" class="card-note" data-testid="agent-schema-status">
      输入字段由 <code>GET /agents/{{ compute.selected.value }}/schema</code> 驱动；
      required：{{ inputSchema.required.join('、') || '无' }}。
    </p>

    <fieldset class="fieldset">
      <legend>出生信息</legend>
      <div class="agent-form-grid">
        <div class="field">
          <label :for="'agent-date'">{{ FIELD_LABELS.date }}</label>
          <input
            id="agent-date"
            v-model="draft.date"
            data-testid="agent-date"
            type="date"
            autocomplete="off"
          />
          <p v-if="errorFor('date')" class="field-error" data-testid="agent-field-error-date">
            {{ errorFor('date') }}
          </p>
        </div>
        <div class="field">
          <label :for="'agent-time'">{{ FIELD_LABELS.time }}</label>
          <input
            id="agent-time"
            v-model="draft.time"
            data-testid="agent-time"
            type="time"
            autocomplete="off"
          />
          <p v-if="errorFor('time')" class="field-error" data-testid="agent-field-error-time">
            {{ errorFor('time') }}
          </p>
        </div>
        <div class="field">
          <label :for="'agent-timezone'">{{ FIELD_LABELS.timezone }}</label>
          <select id="agent-timezone" v-model="draft.timezone" data-testid="agent-timezone">
            <option v-for="option in timezoneChoices" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <p
            v-if="errorFor('timezone')"
            class="field-error"
            data-testid="agent-field-error-timezone"
          >
            {{ errorFor('timezone') }}
          </p>
        </div>
      </div>

      <div v-if="bornLocationField" class="agent-form-grid">
        <div class="field">
          <label for="agent-latitude">{{ FIELD_LABELS.latitude }}</label>
          <input
            id="agent-latitude"
            v-model="draft.latitude"
            data-testid="agent-latitude"
            type="number"
            step="any"
            placeholder="例如 31.2304"
            autocomplete="off"
          />
          <p v-if="errorFor('latitude')" class="field-error" data-testid="agent-field-error-latitude">
            {{ errorFor('latitude') }}
          </p>
        </div>
        <div class="field">
          <label for="agent-longitude">{{ FIELD_LABELS.longitude }}</label>
          <input
            id="agent-longitude"
            v-model="draft.longitude"
            data-testid="agent-longitude"
            type="number"
            step="any"
            placeholder="例如 121.4737"
            autocomplete="off"
          />
          <p
            v-if="errorFor('longitude')"
            class="field-error"
            data-testid="agent-field-error-longitude"
          >
            {{ errorFor('longitude') }}
          </p>
        </div>
        <p class="hint field-wide" data-testid="born-location-hint">
          {{ BORN_LOCATION_HINT }}
        </p>
      </div>

      <div class="agent-form-grid">
        <div class="field">
          <label for="agent-gender">{{ FIELD_LABELS.gender }}</label>
          <select id="agent-gender" v-model="draft.gender" data-testid="agent-gender">
            <option v-for="option in genderOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <p v-if="errorFor('gender')" class="field-error" data-testid="agent-field-error-gender">
            {{ errorFor('gender') }}
          </p>
        </div>
        <div class="field field-wide">
          <label for="agent-question">{{ FIELD_LABELS.question }}</label>
          <input
            id="agent-question"
            v-model="draft.question"
            data-testid="agent-question"
            type="text"
            placeholder="可选，例如：今年的工作发展如何？"
            autocomplete="off"
          />
        </div>
        <div v-if="seedField" class="field">
          <label for="agent-seed">{{ FIELD_LABELS.seed }}</label>
          <input
            id="agent-seed"
            v-model="draft.seed"
            data-testid="agent-seed"
            type="number"
            inputmode="numeric"
            placeholder="留空则不发送"
            autocomplete="off"
          />
          <p v-if="errorFor('seed')" class="field-error" data-testid="agent-field-error-seed">
            {{ errorFor('seed') }}
          </p>
        </div>
      </div>
    </fieldset>

    <fieldset v-if="extraFields.length > 0 || castField" class="fieldset">
      <legend>领域参数</legend>
      <div class="agent-form-grid">
        <div v-for="field in extraFields" :key="field.key" class="field">
          <label :for="field.testId">
            {{ field.label }}
            <span v-if="field.required" class="required-mark">*</span>
          </label>
          <input
            :id="field.testId"
            :data-testid="extraTestId(field)"
            :value="draftValue(field.draftKey)"
            :type="field.shape.type === 'integer' || field.shape.type === 'number' ? 'number' : 'text'"
            :step="field.shape.type === 'integer' ? '1' : undefined"
            :placeholder="extraPlaceholder(field)"
            autocomplete="off"
            @input="setDraftValue(field.draftKey, ($event.target as HTMLInputElement).value)"
          />
          <p v-if="field.shape.description" class="hint">{{ field.shape.description }}</p>
          <p
            v-if="errorFor(field.key)"
            class="field-error"
            :data-testid="`agent-field-error-${field.key}`"
          >
            {{ errorFor(field.key) }}
          </p>
        </div>

        <div v-if="castField" class="field field-wide">
          <label for="agent-casts">
            {{ FIELD_LABELS.casts }}
          </label>
          <input
            id="agent-casts"
            v-model="draft.casts"
            data-testid="agent-casts"
            type="text"
            placeholder="留空则按 seed 起卦；或填 6 个值，如 7,8,9,6,7,8（自下而上）"
            autocomplete="off"
          />
          <p class="hint">6 个值，每个只能是 6 / 7 / 8 / 9；顺序为自下而上。</p>
          <p v-if="errorFor('casts')" class="field-error" data-testid="agent-field-error-casts">
            {{ errorFor('casts') }}
          </p>
        </div>
      </div>
    </fieldset>

    <div class="agent-form-actions">
      <button
        type="submit"
        class="btn btn-primary"
        data-testid="btn-agent-compute"
        :disabled="status === 'loading' || schemaLoading"
      >
        {{ status === 'loading' ? '计算中…' : '开始计算' }}
      </button>
      <button
        v-if="status === 'loading'"
        type="button"
        class="btn btn-small"
        data-testid="btn-agent-cancel"
        @click="cancel"
      >
        取消
      </button>
      <span class="hint">
        只调用
        {{ compute.selected.value }} 单个 Agent；不发起编排、不产生共识。
      </span>
    </div>
  </form>
</template>
