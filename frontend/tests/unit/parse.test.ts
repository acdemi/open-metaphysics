import { describe, expect, it } from 'vitest'

import { ApiError } from '../../src/api/errors'
import { parseOrchestrationResponse } from '../../src/api/parse'

function baziOutput(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    request_id: 'req-1',
    agent: 'bazi',
    engine_version: '0.1.0',
    input_hash: 'abc',
    computed_at: '2026-01-01T00:00:00Z',
    confidence: { value: 0.95, method: 'rule_coverage', factors: { steps: 6 } },
    reasoning_trace: [
      { step: 1, rule_ref: 'bazi.year_pillar', description: 'sexagenary year', inputs: {}, outputs: { stem: '庚' } },
    ],
    metadata: { deterministic: true },
    result: {
      day_master: '辛',
      day_master_element: '金',
      pillars: [
        {
          position: 'year',
          stem: '庚',
          branch: '午',
          stem_index: 6,
          branch_index: 6,
          hidden_stems: ['丁', '己'],
          nayin: '路旁土',
          ten_god: '劫财',
        },
      ],
      dayun: [],
      ten_gods_map: { 庚: '劫财' },
      year_boundary: '1990-02-04T02:11:40.542161Z',
      month_boundary: '芒种',
      gender_assumed: false,
    },
    ...overrides,
  }
}

function orchestration(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    request_id: 'req-1',
    outputs: [baziOutput()],
    consensus: null,
    explanation: {},
    explanation_detail: {
      bazi: {
        explanation: '日主辛',
        provider: null,
        degraded: true,
        knowledge: [],
        evidence: {},
        error: null,
      },
    },
    errors: [],
    ...overrides,
  }
}

function consensus(): Record<string, unknown> {
  return {
    request_id: 'req-1',
    agent: 'consensus',
    engine_version: '0.1.0',
    computed_at: '2026-01-01T00:00:00Z',
    // 后端 ConsensusOutput.confidence 是 float（不是 ConfidenceScore 对象）
    confidence: 0.8313,
    reasoning_trace: [
      { step: 1, rule_ref: 'consensus.elements', description: 'extract', inputs: {}, outputs: { bazi: '金' } },
    ],
    metadata: { strategy: 'weighted', agent_count: 2 },
    result: {
      overall_confidence: 0.83,
      contributions: [{ agent: 'bazi', confidence: 0.95, weight: 0.95, element: '金', summary: '日主 辛' }],
      agreement_matrix: { bazi: { bazi: 1 } },
      conflicts: [],
      synthesis: 'Cross-modal consensus',
      recommendation: 'review_conflicts',
    },
  }
}

describe('parseOrchestrationResponse', () => {
  it('解析合法响应中的域输出与解释详情', () => {
    const parsed = parseOrchestrationResponse(orchestration())
    expect(parsed.outputs).toHaveLength(1)
    const output = parsed.outputs[0]
    expect(output?.agent).toBe('bazi')
    expect(output?.result).toMatchObject({ day_master: '辛', day_master_element: '金' })
    expect(parsed.explanation_detail.bazi?.degraded).toBe(true)
    expect(parsed.consensus).toBeNull()
  })

  it('接受 float 形式的 consensus.confidence（后端非 AgentOutput 子类）', () => {
    const parsed = parseOrchestrationResponse(orchestration({ consensus: consensus() }))
    expect(parsed.consensus?.confidence).toBeCloseTo(0.8313)
    expect(parsed.consensus?.result.contributions[0]?.element).toBe('金')
  })

  it('字段缺失时抛出 invalid_response，而不是静默降级', () => {
    const broken = orchestration({
      outputs: [baziOutput({ confidence: undefined })],
    })
    let caught: unknown = null
    try {
      parseOrchestrationResponse(broken)
    } catch (error) {
      caught = error
    }
    expect(caught).toBeInstanceOf(ApiError)
    if (caught instanceof ApiError) {
      expect(caught.kind).toBe('invalid_response')
      expect(caught.message).toContain('confidence')
    }
  })

  it('未知域保留为通用输出，不伪造专用结果', () => {
    const parsed = parseOrchestrationResponse(
      orchestration({
        outputs: [baziOutput({ agent: 'future-domain', result: { anything: 1 } })],
      }),
    )
    expect(parsed.outputs[0]?.agent).toBe('future-domain')
    expect(parsed.outputs[0]?.result).toEqual({ anything: 1 })
  })

  it('知识片段保留可选原文', () => {
    const parsed = parseOrchestrationResponse(
      orchestration({
        explanation_detail: {
          bazi: {
            explanation: 'x',
            provider: null,
            degraded: true,
            knowledge: [
              { id: 'kn:a', source: '渊海子平', text: '原文片段' },
              { id: 'kn:b', source: '三命通会' },
            ],
            evidence: {},
            error: null,
          },
        },
      }),
    )
    expect(parsed.explanation_detail.bazi?.knowledge[0]?.text).toBe('原文片段')
    expect(parsed.explanation_detail.bazi?.knowledge[1]?.text).toBeUndefined()
  })
})
