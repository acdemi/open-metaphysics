# Consensus Capability Clarification（事实报告）

> **性质**: **事实报告 + 结构裁定记录**。2026-10-24 已裁定 **S-1 = 并列**：
> 保留 Cross-Modal `ConsensusAgent`，并行新增 Evidence 生产引擎（不替换、不重命名）。
> **日期**: 2026-09-16 · **阶段**: Phase C4 · **基线**: `main`
> **2026-10-24 更新**: A1 等价实现（`498189a`）已 cherry-pick 到
> `work/consensus/evidence-engine`，补 RuntimeAdapter/包导出接线后已合并（`b0ce66f`）。

## 0. 结论（一句话）

Production 的 `ConsensusAgent` 与 Reference 的 `ConsensusBuilder` 是**两个不同的 capability**，
解决不同问题、输入输出均不同；orchestration 使用的是前者，Reference 契约描述的是后者。
**不应强行合并**，只需命名与文档澄清。

---

## 1. 六个问题的事实回答

| # | 问题 | 事实 | 证据 |
|---|------|------|------|
| 1 | 是否解决同一个问题 | **否**。前者回答「多个模态的结论是否一致/冲突」；后者回答「同一结论由哪些 Evidence 支持、按什么策略裁决」 | 见 §2 输入/输出对比 |
| 2 | 输入是否应该相同 | **否，且不可能相同**。前者是 `list[AgentOutput]`（已完成计算的信封）；后者是 `list[Evidence]`（上游证据层产物） | `agents/consensus.py:20-24` vs `reference/consensus.py:97-110` |
| 3 | 输出是否应该相同 | **否**。字段集不相交 | 见 §3 |
| 4 | orchestration 当前用的是哪一个 | **`ConsensusAgent`（跨模态）** —— 没有任何生产代码引用 `reference.consensus*` | `orchestration/graph.py:14,81`；全库 import 扫描见 §4 |
| 5 | Reference contract 是否描述另一个独立 capability | **是**。`reference/contracts/consensus_contract.json` v1.0.0 + `CONSENSUS_BEHAVIOR_SPEC.md`（CS-001~025, Frozen）+ conformance `CONSENSUS` 层（3 条 golden vector）全部描述 Evidence 聚合 | §5 |
| 6 | 是否应拆成 `CrossModalConsensus` / `EvidenceConsensus` | **是**（命名澄清，不做结构改动） | §6 |

---

## 2. 输入 / 问题域对比

| | Legacy `ConsensusAgent` | Reference `ConsensusBuilder` |
|---|---|---|
| 输入类型 | `list[AgentOutput]`（`agent_outputs`，min_length=1） | `list[Evidence]` + `ConsensusConfig` |
| 抽取信号 | 每模态的**五行**（`_element_of`，按 agent 名分支） | 每条 Evidence 的 `(domain, conclusion, confidence, system)` |
| 问题 | 跨模态是否一致？何处相克？总体可信度？ | 同一结论的置信度如何聚合？同域多个结论如何裁决？ |
| 策略 | `weighted` / `majority` / `all`（权重语义） | `retain_all` / `highest_confidence` / `majority`（裁决语义） |
| 冲突判据 | 五行 `ke` / `being_ke` 关系对，`severity` 恒 `medium` | 同域多结论，按策略判定存活/丢弃 |

**结论**：输入不同 → 问题不同 → 两者不是同一 capability 的两种实现。

## 3. 输出对比（字段集不相交）

| Legacy `ConsensusReport` | Reference `ConsensusReport` |
|---|---|
| `overall_confidence` | `report_id` |
| `contributions: [AgentContribution]` | `overall_confidence` |
| `agreement_matrix: {agent: {agent: float}}` | `domains: [Domain]` |
| `conflicts: [Conflict{agents, field, values, severity}]` | `conclusions: [ConsensusConclusion]` |
| `synthesis: str` | `conflicts: [ConsensusConclusion]` |
| `recommendation: str \| None` | `evidence_ids: [str]` |
| — | `metadata` / `version` |

仅 `overall_confidence` 与 `conflicts` 名称重合，**元素类型亦不同**
（`Conflict` ⟷ `ConsensusConclusion`）。

## 4. 依赖事实（谁用哪个）

| 消费者 | 使用的实现 |
|---|---|
| `orchestration/graph.py`（`_consensus` 节点） | `agents.consensus.ConsensusAgent` |
| `tests/test_consensus.py` | `agents.consensus.ConsensusAgent` |
| `tests/test_consensus_engine.py`（A1 并列实现，2026-10-24） | `openmetaphysics.consensus.ConsensusEngine`（Evidence 版） |
| `reference/*`、`reference/tests/*`、conformance | `reference.consensus` + `consensus_builder` |

**关键事实**：**没有任何生产代码**引用 `reference.consensus*`（独立实现原则）。
自 2026-10-24 起，Reference Evidence 契约已有**独立生产实现**（`openmetaphysics.consensus`，
52 输入逐字节等价）与契约适配器；Cross-Modal 与 Evidence 两个 capability **并列共存**，
互不影响。

## 5. Reference 契约归属

`reference/contracts/consensus_contract.json`：
- `contract_name: "consensus"`、`generated_by: reference.consensus_builder.export_consensus_contract`
- `models`: `ConsensusInput{evidence, config}` / `ConsensusConfig` / `ConsensusConclusion` / `ConsensusReport`
- `strategies`: `retain_all` / `highest_confidence` / `majority`

配套治理：`docs/specification/CONSENSUS_BEHAVIOR_SPEC.md`（CS-001~CS-025，**Frozen**）、
conformance **CONSENSUS 层**（`reference/conformance/golden/consensus_vectors.json`，3 条向量）。

→ 该契约描述的是 **Evidence 聚合 capability**，与 `ConsensusAgent` 无关。

## 6. 最小澄清（本次已实施 / 建议）

**已实施（纯命名与文档，零行为改动）**：
1. `src/openmetaphysics/agents/consensus.py` 模块 docstring：明确标为 **Cross-Modal Consensus**，
   并声明它**不是** Reference Evidence-consensus 契约的实现。
2. `docs/governance/CAPABILITY_STATUS.md` 的 Consensus 章节：拆为两个具名 capability。

**2026-10-24 结构裁定（S-1 = 并列）后已实施**：
- 保留 `agents.consensus.ConsensusAgent`（Cross-Modal）与 orchestration/API 不变。
- 新增 `openmetaphysics.consensus`（Evidence 引擎）与
  `contracts.consensus_contract.ConsensusContractAdapter`（含 `build_consensus`
  RuntimeAdapter 方法），并经 `openmetaphysics.contracts` 包导出。
- 未重命名既有类/模块/导入路径；不删除任何一侧。

## 7. 后续状态

| 项 | 内容 | 状态 |
|----|------|------|
| S-1 | 结构裁定：就地扩展 / 替换 / 保留并列 | **已裁定 = 并列**（2026-10-24 人工裁定） |
| S-2 | 并列命名 `CrossModalConsensus` / `EvidenceConsensus` | 未执行（避免破坏性重命名；以包/文档区分） |
| S-3 | `CAPABILITY_STATUS` 按 capability 登记 | DONE（两个具名 capability） |

> 2026-10-24 实施：`498189a` cherry-pick 为 `work/consensus/evidence-engine`；
> 补 `build_consensus` + `ConsensusConclusion` runtime alignment + 包导出；
> 等价 52 输入、冻结向量 3/3 复放一致；已合并 `b0ce66f`（2026-10-24）。

## 8. 判定

```text
C4 判定: 两个不同的 capability（不同问题 / 不同输入 / 不同输出）
处置 A (2026-09-16): 不合并；仅命名与文档澄清
处置 B (2026-10-24): S-1 = 并列；Evidence 生产引擎 + 契约适配器落地
                     （独立实现；52 输入逐字节等价；冻结向量 3/3）
是否 STOP: 否
```
