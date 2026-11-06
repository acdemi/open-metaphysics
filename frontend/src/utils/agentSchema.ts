/* 受限的 JSON Schema 读取：只覆盖四个领域输入实际使用的标量 / 枚举 / 可空结构。
 *
 * 不实现通用 JSON Schema 表单引擎（超出本轮范围）：这里负责把后端
 * `/agents/{name}/schema` 的 `input_schema` 归一成表单可用的字段描述，
 * 复杂字段（出生时刻、六爻 casts、紫微农历）由领域专用控件处理。
 */

import type { AgentSchemaResponse } from '../api/types'

export interface JsonSchemaNode {
  type?: string
  enum?: unknown[]
  default?: unknown
  title?: string
  description?: string
  format?: string
  minimum?: number
  maximum?: number
  anyOf?: JsonSchemaNode[]
  oneOf?: JsonSchemaNode[]
  $ref?: string
  items?: JsonSchemaNode
  properties?: Record<string, JsonSchemaNode>
  required?: string[]
  $defs?: Record<string, JsonSchemaNode>
}

export interface AgentInputSchema {
  properties: Record<string, JsonSchemaNode>
  required: string[]
  $defs: Record<string, JsonSchemaNode>
}

export interface FieldShape {
  type: 'string' | 'integer' | 'number' | 'boolean' | 'array' | 'object' | 'unknown'
  nullable: boolean
  enumValues: string[]
  defaultValue: unknown
  title: string
  description: string
  minimum: number | null
  maximum: number | null
}

const SCALAR_TYPES = new Set(['string', 'integer', 'number', 'boolean', 'array', 'object'])

function asNodeMap(value: unknown): Record<string, JsonSchemaNode> {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return {}
  return value as Record<string, JsonSchemaNode>
}

/** 结构校验 + 归一；调用方已经过 `parseAgentSchemaResponse` 的运行时校验。 */
export function readInputSchema(value: unknown): AgentInputSchema | null {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) return null
  const record = value as Record<string, unknown>
  const properties = asNodeMap(record.properties)
  const defs = asNodeMap(record.$defs)
  const required = Array.isArray(record.required)
    ? record.required.filter((item): item is string => typeof item === 'string')
    : []
  return { properties, required, $defs: defs }
}

export function readInputSchemaFromResponse(
  response: AgentSchemaResponse | null,
): AgentInputSchema | null {
  if (!response) return null
  return readInputSchema(response.input_schema)
}

/** 解析本地 `$ref`（`#/$defs/Gender` 等）；无法解析时原样返回。 */
export function resolveRef(schema: AgentInputSchema, node: JsonSchemaNode): JsonSchemaNode {
  if (!node.$ref) return node
  const match = /^#\/\$defs\/([^/]+)$/.exec(node.$ref)
  if (!match) return node
  const target = schema.$defs[match[1] ?? '']
  return target ?? node
}

export function fieldNode(
  schema: AgentInputSchema,
  field: string,
): JsonSchemaNode | null {
  const node = schema.properties[field]
  return node ? resolveRef(schema, node) : null
}

export function hasField(schema: AgentInputSchema | null, field: string): boolean {
  return schema !== null && field in schema.properties
}

export function isRequired(schema: AgentInputSchema, field: string): boolean {
  return schema.required.includes(field)
}

/** 枚举值：支持直接 `enum` 或 `$ref` 到 `$defs` 里的枚举。 */
export function enumValues(schema: AgentInputSchema, field: string): string[] {
  const node = fieldNode(schema, field)
  if (!node || !Array.isArray(node.enum)) return []
  return node.enum.filter((item): item is string => typeof item === 'string')
}

/** 描述单个字段：合并 `anyOf` 中的可空分支，得到主类型 + nullable。 */
export function describeField(node: JsonSchemaNode): FieldShape {
  let type: FieldShape['type'] = 'unknown'
  let nullable = false
  let enumValues: string[] = []
  let defaultValue: unknown = null
  let title = node.title ?? ''
  let description = node.description ?? ''
  let minimum: number | null = null
  let maximum: number | null = null
  const candidates = node.anyOf ?? node.oneOf ?? [node]
  for (const candidate of candidates) {
    if (candidate.type === 'null') {
      nullable = true
      continue
    }
    if (candidate.type && SCALAR_TYPES.has(candidate.type)) type = candidate.type as FieldShape['type']
    if (Array.isArray(candidate.enum)) {
      enumValues = candidate.enum.filter((item): item is string => typeof item === 'string')
    }
    if (candidate.title) title = candidate.title
    if (candidate.description) description = candidate.description
    if (typeof candidate.minimum === 'number') minimum = candidate.minimum
    if (typeof candidate.maximum === 'number') maximum = candidate.maximum
    if (candidate.default !== undefined) defaultValue = candidate.default
  }
  if (node.enum) {
    enumValues = node.enum.filter((item): item is string => typeof item === 'string')
  }
  if (node.default !== undefined) defaultValue = node.default
  if (node.title) title = node.title
  if (node.description) description = node.description
  return { type, nullable, enumValues, defaultValue, title, description, minimum, maximum }
}

export function fieldShape(schema: AgentInputSchema, field: string): FieldShape | null {
  const node = fieldNode(schema, field)
  return node ? describeField(node) : null
}

export function defaultFieldValue(schema: AgentInputSchema, field: string): unknown {
  const node = fieldNode(schema, field)
  return node?.default ?? null
}
