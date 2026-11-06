/* Consensus 展示状态：只根据 /orchestrate 实际返回的 consensus/outputs/errors 归纳。
 *
 * 后端不提供 consensus.status / participating_agents / evidence 字段：
 * - 状态标签是界面归纳，不是后端字段；
 * - 参与领域以 result.contributions 为准；
 * - 不根据“领域成功”推断其支持共识，也不计算权重/支持率。
 */

import type { AnyOutput, ConsensusOutput } from '../api/types'

export type ConsensusStateKind = 'generated' | 'partial' | 'none' | 'unavailable'

export interface ConsensusStateView {
  kind: ConsensusStateKind
  label: string
  reason: string
  successfulAgents: string[]
  contributionAgents: string[]
  failedEntries: string[]
  conflictCount: number
}

export function describeConsensusState(
  consensus: ConsensusOutput | null,
  outputs: readonly AnyOutput[],
  runErrors: readonly string[],
): ConsensusStateView {
  const successfulAgents = outputs.map((output) => output.agent)
  const failedEntries = [...runErrors]

  if (consensus) {
    const contributions = consensus.result.contributions ?? []
    const conflicts = consensus.result.conflicts ?? []
    const contributionAgents = contributions.map((item) => item.agent)
    if (conflicts.length > 0) {
      return {
        kind: 'partial',
        label: `部分共识（后端 conflicts 非空：${conflicts.length} 项）`,
        reason:
          '后端返回了非空 consensus，但报告里存在跨域冲突（conflicts 非空）。' +
          '界面只展示后端给出的冲突与一致性矩阵，不据此计算“支持率”。',
        successfulAgents,
        contributionAgents,
        failedEntries,
        conflictCount: conflicts.length,
      }
    }
    return {
      kind: 'generated',
      label: '共识已生成（后端返回非空 consensus）',
      reason:
        '后端返回了非空 consensus 且 conflicts 为空。参与领域与结论均来自后端 contributions/synthesis 原文。',
      successfulAgents,
      contributionAgents,
      failedEntries,
      conflictCount: 0,
    }
  }

  if (successfulAgents.length === 0) {
    return {
      kind: 'none',
      label: '无共识：没有可用的领域结果',
      reason:
        '本次没有任何成功的领域结果；后端仅在至少 2 个域成功产出结果时才生成共识，因此 consensus 为 null。',
      successfulAgents,
      contributionAgents: [],
      failedEntries,
      conflictCount: 0,
    }
  }
  if (successfulAgents.length === 1) {
    const failedNote =
      failedEntries.length > 0 ? `；失败项：${failedEntries.join('；')}` : '；本次未报告领域失败'
    return {
      kind: 'none',
      label: '无共识：成功领域不足 2 个',
      reason:
        `后端规则：至少 2 个域成功产出结果才生成共识。本次成功领域：${successfulAgents.join('、')}` +
        `${failedNote}。后端因此返回 consensus=null，这不是前端把结果包装成失败。`,
      successfulAgents,
      contributionAgents: [],
      failedEntries,
      conflictCount: 0,
    }
  }
  return {
    kind: 'unavailable',
    label: '共识不可用：≥2 个领域成功但未返回 consensus',
    reason:
      '响应中有至少 2 个成功的领域结果，但 consensus 为空；按接口契约这属于异常情况，' +
      '界面不会自行生成或补造共识。',
    successfulAgents,
    contributionAgents: [],
    failedEntries,
    conflictCount: 0,
  }
}

/** 后端 Consensus 响应里没有 evidence/source 字段；用于 UI 明确标注数据不可用。 */
export const CONSENSUS_EVIDENCE_BOUNDARY =
  '后端 consensus 对象不含 evidence / source / 文档 ID / 页码字段，因此本区域不展示（也无法展示）共识证据来源。' +
  '解释引用的知识见「知识证据」，用户主动发起的独立检索见「知识检索」，三者语义不同，' +
  '不能用解释引用或检索结果补齐 Consensus 证据。'
