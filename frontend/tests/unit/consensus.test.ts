import { describe, expect, it } from 'vitest'

import { ApiError } from '../../src/api/errors'
import { parseOrchestrationResponse } from '../../src/api/parse'
import type { AnyOutput, ConsensusOutput } from '../../src/api/types'
import {
  CONSENSUS_EVIDENCE_BOUNDARY,
  describeConsensusState,
} from '../../src/utils/consensus'

function baziOutput(): AnyOutput {
  return {
    request_id: 'cons-1',
    agent: 'bazi',
    engine_version: '0.1.0',
    input_hash: 'hash-bazi',
    computed_at: '2026-01-01T00:00:00Z',
    confidence: { value: 0.95, method: 'rule_coverage', factors: {} },
    reasoning_trace: [
      { step: 1, rule_ref: 'bazi.year_pillar', description: 'sexagenary year', inputs: {}, outputs: {} },
    ],
    metadata: {},
    result: {
      day_master: '辛',
      day_master_element: '金',
      pillars: [],
      dayun: [],
      ten_gods_map: {},
      year_boundary: '1990-02-04T02:11:40Z',
      month_boundary: '芒种',
      gender_assumed: false,
    },
  }
}

function ziweiOutput(): AnyOutput {
  return {
    request_id: 'cons-1',
    agent: 'ziwei',
    engine_version: '0.3.0',
    input_hash: 'hash-ziwei',
    computed_at: '2026-01-01T00:00:00Z',
    confidence: { value: 0.95, method: 'rule_coverage', factors: {} },
    reasoning_trace: [],
    metadata: {},
    result: {
      fate_palace_index: 0,
      body_palace_index: 0,
      yin_yang: '阳',
      wuxing_ju: '水二局',
      palaces: [],
      calendar_note: null,
    },
  }
}

function consensus(overrides: Record<string, unknown> = {}): ConsensusOutput {
  return {
    request_id: 'cons-1',
    agent: 'consensus',
    engine_version: '0.1.0',
    computed_at: '2026-01-01T00:00:00Z',
    confidence: 0.8313,
    reasoning_trace: [
      {
        step: 1,
        rule_ref: 'consensus.elements',
        description: 'extract 五行 signal per modality',
        inputs: {},
        outputs: { bazi: '金', ziwei: '土' },
      },
    ],
    metadata: { strategy: 'weighted', agent_count: 2 },
    result: {
      overall_confidence: 0.8313,
      contributions: [
        { agent: 'bazi', confidence: 0.95, weight: 0.95, element: '金', summary: 'bazi 结果摘要' },
        { agent: 'ziwei', confidence: 0.95, weight: 0.95, element: '土', summary: 'ziwei 结果摘要' },
      ],
      agreement_matrix: {
        bazi: { bazi: 1, ziwei: 0.4 },
        ziwei: { bazi: 0.4, ziwei: 1 },
      },
      conflicts: [
        { agents: ['bazi', 'ziwei'], field: 'element', values: ['金', '土'], severity: 'medium' },
      ],
      synthesis: 'Cross-modal consensus over: bazi(金), ziwei(土). 1 element conflict(s) detected.',
      recommendation: '偏保守参考',
    },
    ...overrides,
  } as ConsensusOutput
}

function orchestration(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    request_id: 'cons-1',
    outputs: [baziOutput(), ziweiOutput()],
    consensus: consensus(),
    explanation: {},
    explanation_detail: {},
    errors: [],
    ...overrides,
  }
}

describe('consensus 响应解析', () => {
  it('解析正常 ConsensusOutput（contributions/agreement/conflicts/synthesis）', () => {
    const parsed = parseOrchestrationResponse(orchestration())
    expect(parsed.consensus).not.toBeNull()
    expect(parsed.consensus?.result.contributions).toHaveLength(2)
    expect(parsed.consensus?.result.conflicts[0]?.severity).toBe('medium')
    expect(parsed.consensus?.metadata.strategy).toBe('weighted')
    expect(parsed.consensus?.result.synthesis).toContain('Cross-modal consensus')
  })

  it('consensus 为 null 时保留 null，不伪造共识', () => {
    const parsed = parseOrchestrationResponse(
      orchestration({ outputs: [baziOutput()], consensus: null, errors: ['ziwei: RuntimeError: boom'] }),
    )
    expect(parsed.consensus).toBeNull()
    expect(parsed.errors).toEqual(['ziwei: RuntimeError: boom'])
  })

  it('Consensus 缺失必需字段时抛 invalid_response', () => {
    const broken = orchestration({
      consensus: { ...consensus(), result: { overall_confidence: 0.5, contributions: [] } },
    })
    expect(() => parseOrchestrationResponse(broken)).toThrowError(ApiError)
  })

  it('agreement_matrix 值非数字时抛 invalid_response', () => {
    const broken = consensus()
    const result = broken.result as unknown as Record<string, unknown>
    result.agreement_matrix = { bazi: { bazi: 'high' } }
    expect(() => parseOrchestrationResponse(orchestration({ consensus: broken }))).toThrowError(
      ApiError,
    )
  })
})

describe('describeConsensusState', () => {
  it('有共识且无冲突：状态为已生成，参与领域来自 contributions', () => {
    const outputs = [baziOutput(), ziweiOutput()]
    const item = consensus()
    item.result.conflicts = []
    const state = describeConsensusState(item, outputs, [])
    expect(state.kind).toBe('generated')
    expect(state.label).toContain('已生成')
    expect(state.contributionAgents).toEqual(['bazi', 'ziwei'])
    expect(state.successfulAgents).toEqual(['bazi', 'ziwei'])
  })

  it('有共识且 conflicts 非空：状态为部分共识（不计算支持率）', () => {
    const outputs = [baziOutput(), ziweiOutput()]
    const state = describeConsensusState(consensus(), outputs, [])
    expect(state.kind).toBe('partial')
    expect(state.conflictCount).toBe(1)
    expect(state.label).toContain('部分共识')
  })

  it('没有任何成功领域：无共识，失败项来自后端 errors 原文', () => {
    const state = describeConsensusState(null, [], ['bazi: RuntimeError: boom', 'ziwei: TimeoutError: x'])
    expect(state.kind).toBe('none')
    expect(state.label).toContain('无共识')
    expect(state.failedEntries).toHaveLength(2)
    expect(state.contributionAgents).toEqual([])
  })

  it('仅 1 个成功领域（部分失败）：无共识，原因说明后端 <2 规则', () => {
    const state = describeConsensusState(null, [baziOutput()], ['ziwei: RuntimeError: boom'])
    expect(state.kind).toBe('none')
    expect(state.reason).toContain('至少 2 个')
    expect(state.successfulAgents).toEqual(['bazi'])
    expect(state.failedEntries).toEqual(['ziwei: RuntimeError: boom'])
  })

  it('≥2 个领域成功但 consensus 为空：状态为不可用（不自行生成）', () => {
    const state = describeConsensusState(null, [baziOutput(), ziweiOutput()], [])
    expect(state.kind).toBe('unavailable')
    expect(state.label).toContain('不可用')
  })

  it('新分析结果（默认初始态）不会残留旧共识状态', () => {
    const before = describeConsensusState(consensus(), [baziOutput(), ziweiOutput()], [])
    expect(before.kind).not.toBe('none')
    const after = describeConsensusState(null, [], [])
    expect(after.kind).toBe('none')
    expect(after.contributionAgents).toEqual([])
    expect(after.conflictCount).toBe(0)
  })

  it('证据边界文案明确区分解释引用/知识检索，且声明 Consensus 无证据字段', () => {
    expect(CONSENSUS_EVIDENCE_BOUNDARY).toContain('不含 evidence')
    expect(CONSENSUS_EVIDENCE_BOUNDARY).toContain('知识证据')
    expect(CONSENSUS_EVIDENCE_BOUNDARY).toContain('知识检索')
  })
})
