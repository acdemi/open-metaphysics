# PROJECT_STATUS

> **最后更新**: 2026-07-14
> **项目阶段**: Reference Freeze Candidate

---

## 1. Project Version

| 项目 | 版本 |
|------|------|
| OpenMetaphysics | Reference Freeze Candidate |
| Reference Runtime | 1.0.0 (Contract Version) |
| Behavior Version | 1.0.0 |
| Contract Version | 1.0.0 |
| Conformance Version | 1.0.0 |

---

## 2. Freeze Status

| 冻结项 | 状态 | 说明 |
|--------|------|------|
| Phase 6 Architecture Freeze | **Frozen** | `docs/design/phase6/` 10 份文档，不可修改 |
| Phase 6.5 Engineering Freeze | **Frozen** | `docs/engineering/01_rule_dsl.md` 等 |
| Phase 6.6 Technology Selection | **Frozen** | `docs/engineering/11~14` |
| Phase 6.8 Repository Bootstrap | **Frozen** | Monorepo 基础设施 |
| Reference Runtime | **Candidate** | 行为规范已完成，待最终冻结 |
| Behavior Contracts | **Frozen** | 100 条合约，不可修改（需 ACP） |
| Contract JSON | **Frozen** | 3 份 Contract，v1.0.0 |
| Conformance Rules | **Frozen** | CF-001~020，不可修改 |
| Golden Vectors | **Auto-generated** | 19 个向量，自动发现 |
| Production Runtime | **Draft** | 尚未开始 |

---

## 3. Reference Runtime Progress

Reference Runtime（`reference/`）是整个项目的行为规范。全部 Python、内存
实现、单线程、确定性。

| Sprint | 领域 | 状态 | 测试数 | 关键文件 |
|--------|------|------|--------|----------|
| Sprint 1 | Rule: DSL -> Parser -> RuleEngine -> RuleEvaluation | 完成 | 29 | `parser.py`, `engine.py`, `models.py` |
| Sprint 2 | Pattern: PatternMatcher -> PatternMatch | 完成 | 31 | `patterns.py`, `pattern_matcher.py` |
| Sprint 3 | Evidence: EvidenceBuilder -> Evidence | 完成 | 46 | `evidence.py`, `evidence_builder.py` |
| Sprint 3.5 | Normative Spec + Behavior Contracts | 完成 | - | `docs/specification/` |
| Sprint 4 | Knowledge: KnowledgeStore -> KnowledgeResult | 完成 | 71 | `knowledge.py`, `knowledge_query.py` |
| Sprint 5 | Consensus: ConsensusBuilder -> ConsensusReport | 完成 | 70 | `consensus.py`, `consensus_builder.py` |
| Sprint 5.5 | Conformance: ConformanceRunner -> ConformanceResult | 完成 | 57 | `conformance.py`, `conformance_runner.py` |

**Reference Runtime 测试总计**: 304 个，全部通过。

### Reference Runtime 模块清单

| 模块 | 文件 | 职责 |
|------|------|------|
| Rule DSL Parser | `reference/parser.py` | YAML/JSON -> Rule 对象 |
| Rule Engine | `reference/engine.py` | 条件评估、DNF 展开 |
| Pattern Matcher | `reference/pattern_matcher.py` | 单系统/跨系统模式匹配 |
| Evidence Builder | `reference/evidence_builder.py` | RuleEvaluation/PatternMatch -> Evidence |
| Knowledge Store | `reference/knowledge_query.py` | 内存知识查询 |
| Consensus Builder | `reference/consensus_builder.py` | Evidence -> ConsensusReport |
| Conformance Runner | `reference/conformance_runner.py` | Golden Vector 验证 |

### Contract 清单

| Contract | 文件 | 版本 | Golden Examples |
|----------|------|------|-----------------|
| Evidence | `reference/contracts/evidence_contract.json` | 1.0.0 | 5 |
| Knowledge | `reference/contracts/knowledge_contract.json` | 1.0.0 | 7 |
| Consensus | `reference/contracts/consensus_contract.json` | 1.0.0 | 6 |
---

## 4. Product Runtime Progress

Production Runtime（`src/`, `crates/`, `services/`）是正式实现。当前大部分
领域尚未开始正式实现。

| Phase | 领域 | 状态 | 说明 |
|-------|------|------|------|
| Phase 0 | 脚手架 | 完成 | pyproject.toml, src 布局 |
| Phase 1 | 基础 (schemas, models, calendar, engines) | 部分完成 | core 模块骨架已建立 |
| Phase 2 | 六爻 | 部分完成 | 卦表、纳甲、六亲已实现 |
| Phase 3 | 八字 | 部分完成 | 四柱引擎已实现，2 个测试失败（pre-existing） |
| Phase 4 | 紫微斗数 | 部分完成 | 宫位 + 十四主星已完成 |
| Phase 5 | 奇门遁甲 | 骨架 | Schema 完整，核心 placement 待完成 |
| Phase 6 | 共识智能体 | 未开始 | - |
| Phase 7 | 编排 + API | 部分完成 | FastAPI 骨架已建立 |
| Phase 8 | 推理 + RAG | 未开始 | - |
| Phase 9 | 运维 + 可扩展性 | 未开始 | - |

**Production Runtime 测试总计**: 77 个（75 通过，2 失败）。

> 注: `tests/test_bazi.py` 中 2 个失败为 pre-existing 问题，与 Reference
> Runtime 无关。

---

## 5. Golden Tests 状态

### 5.1 测试总计

| 类别 | 测试数 | 通过 | 失败 |
|------|--------|------|------|
| Reference Runtime | 304 | 304 | 0 |
| Conformance Suite | 57 (测试) / 135 (检查) | 57 / 135 | 0 |
| Pre-existing (Production) | 77 | 75 | 2 |
| **总计** | **381** | **379** | **2** |

### 5.2 测试文件明细

| 文件 | 测试数 | 状态 |
|------|--------|------|
| `tests/test_reference_rules.py` | 29 | 全部通过 |
| `tests/test_reference_patterns.py` | 31 | 全部通过 |
| `tests/test_reference_evidence.py` | 46 | 全部通过 |
| `tests/test_reference_knowledge.py` | 71 | 全部通过 |
| `tests/test_reference_consensus.py` | 70 | 全部通过 |
| `tests/test_reference_conformance.py` | 57 | 全部通过 |
| `tests/test_api.py` | 7 | 全部通过 |
| `tests/test_bazi.py` | 11 | 9 通过, 2 失败 |
| `tests/test_calendar.py` | 6 | 全部通过 |
| `tests/test_consensus.py` | 3 | 全部通过 |
| `tests/test_determinism.py` | 4 | 全部通过 |
| `tests/test_liuyao.py` | 6 | 全部通过 |
| `tests/test_models.py` | 7 | 全部通过 |
| `tests/test_orchestration.py` | 4 | 全部通过 |
| `tests/test_qimen.py` | 10 | 全部通过 |
| `tests/test_solar_time.py` | 7 | 全部通过 |
| `tests/test_ziwei.py` | 12 | 全部通过 |

### 5.3 Golden Vectors

| 层 | 向量数 | 文件 |
|----|--------|------|
| Rule | 6 | `reference/conformance/golden/rule_vectors.json` |
| Pattern | 5 | `reference/conformance/golden/pattern_vectors.json` |
| Evidence | 1 | `reference/conformance/golden/evidence_vectors.json` |
| Knowledge | 4 | `reference/conformance/golden/knowledge_vectors.json` |
| Consensus | 3 | `reference/conformance/golden/consensus_vectors.json` |
| **总计** | **19** | 自动发现，禁止人工维护 |

### 5.4 Conformance Suite 结果

| 指标 | 值 |
|------|-----|
| 总检查数 | 135 |
| 通过 | 135 |
| 失败 | 0 |
| 覆盖率 | 100% |
| 认证状态 | **Certified** |

---

## 6. Behavior Contract 状态

| 文档 | 合约数 | ID 范围 | 状态 |
|------|--------|---------|------|
| `BEHAVIOR_SPEC.md` | 35 | BC-RE/DNF/PM/EV/JSON/DET/EDGE | Frozen |
| `KNOWLEDGE_BEHAVIOR_SPEC.md` | 20 | KB-001 ~ KB-020 | Frozen |
| `CONSENSUS_BEHAVIOR_SPEC.md` | 25 | CS-001 ~ CS-025 | Frozen |
| `CONFORMANCE_SPEC.md` | 20 | CF-001 ~ CF-020 | Frozen |
| **总计** | **100** | | **全部 Frozen** |

所有 Behavior Contract 不可修改。任何修改需要 Architecture Change
Proposal (ACP)。

---

## 7. Current Sprint

**当前 Sprint**: Documentation Refresh（Architecture Governance）

**目标**: 同步现有文档与当前实现状态。

**交付物**:
- 更新 `docs/ARCHITECTURE.md`（Reference Freeze Candidate + Governance）
- 更新 `docs/SCHEMAS.md`（跨语言契约 + Reference/Production 关系）
- 更新 `docs/INTERFACES.md`（Reference Runtime 接口位置）
- 更新 `docs/ROADMAP.md`（双时间线）
- 新建 `docs/PROJECT_STATUS.md`（本文件）
- 补充 `docs/specification/IMPLEMENTATION_GUIDE.md`（Sprint 5.5 遗留）

---

## 8. Next Sprint

**待定**。等待用户明确指示。

可能的方向：
- Reference Runtime 最终冻结（Reference Freeze Candidate -> Frozen）
- Production Runtime Sprint 1（Rust/Go 正式实现启动）
- 其他领域扩展

---

## 9. 关键文档索引

| 文档 | 位置 | 用途 |
|------|------|------|
| AGENTS.md | 根目录 | 长期规则（Sprint Discipline 等） |
| ARCHITECTURE.md | `docs/` | 架构设计 + Governance |
| SCHEMAS.md | `docs/` | Schema 设计 + 跨语言契约 |
| INTERFACES.md | `docs/` | 接口设计 + Reference 位置 |
| ROADMAP.md | `docs/` | 双时间线路线图 |
| PROJECT_STATUS.md | `docs/` | 本文件，项目状态总览 |
| Phase 6 设计文档 | `docs/design/phase6/` | 架构冻结（不可修改） |
| Engineering 文档 | `docs/engineering/` | 工程冻结 + 技术选型 |
| Specification 文档 | `docs/specification/` | 行为规范 + Contract 治理 |
| Reference Runtime | `reference/` | 行为规范实现 |
| Contracts | `reference/contracts/` | 自动生成的 Architecture Contract |
| Golden Vectors | `reference/conformance/golden/` | 自动生成的 Conformance 向量 |
| Golden Tests | `tests/test_reference_*.py` | Reference Runtime 验证 |
