# PROJECT_STATUS

> **最后更新**: 2026-09-16
> **项目阶段**: Reference Freeze Candidate（Knowledge 语料 **Ziwei 已冻结 v1.0.0**）
> **Qimen Domain**: **Frozen and Certified**（契约冻结 + Reference 认证 + 双实现验证）
> **BaZi Domain**: **Integration Ready**（契约 v1.0.0 Frozen + Reference Certified + 集成就绪审查 7/7）
> **Ziwei Domain**: **Integration Ready**（契约 v1.0.0 Frozen + Reference Certified + 集成就绪审查 7/7）
> **Production Runtime（`src/`）**: **部分实现** —— Phase 0~5 完成/认证（Qimen Certified）；Phase 6/7/8 已实现（含待修缺陷）；Phase 9 **仅桩**。本节依据 **2026-09-16 只读代码审计**刷新，明细见 §4 与 `docs/PROJECT_REVIEW_2026-09-16.md`
> **Knowledge Layer**: Architecture **Frozen** / Pipeline **Validated** / Corpus **FROZEN-v1.0.0**（`ziwei_corpus:v1.0.0`, 2026-09-16, D-12=A 批准 —— Ziwei **102 节点 + 47 关系 + 41 引用**, digest `69d6e2a6…`；变更须走 Corpus 级审查）

---

## 1. Project Version

| 项目 | 版本 |
|------|------|
| OpenMetaphysics | Reference Freeze Candidate |
| Reference Runtime | 1.0.0 (Contract Version) |
| Behavior Version | 1.0.0 |
| Contract Version | 1.0.0 |
| Conformance Version | 1.0.0 |
| **Qimen Behavior Contract** | **1.0.0（Frozen + Certified）** |
| **Qimen Reference** | **Certified Independent Implementation** |
| **Qimen Golden Vectors** | **24（Frozen Verification Artifacts）** |
| **BaZi Behavior Contract** | **1.0.0（Frozen, Integration Ready）** |
| **BaZi Reference** | **Certified（24/24 等价）** |
| **BaZi Golden Vectors** | **24（normative fixtures）** |
| **Ziwei Behavior Contract** | **1.0.0（Frozen, Integration Ready）** |
| **Ziwei Reference** | **Certified（24/24 等价）** |
| **Ziwei Golden Vectors** | **24（normative fixtures）** |
| **Knowledge Behavior Contract** | **KB-001~020（Frozen）** |
| **Knowledge Corpus** | **FROZEN-v1.0.0（`ziwei_corpus:v1.0.0`, 2026-09-16）—— 102/47/41** |

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
| **Qimen Domain** | **Frozen + Certified** | 契约 v1.0.0 + Reference 认证 + 24 向量双实现验证 |
| **BaZi Domain** | **Integration Ready** | 契约 v1.0.0 Frozen + Reference Certified + Schema 登记 + 变更政策生效（Phase 6.6） |
| **Ziwei Domain** | **Integration Ready** | 契约 v1.0.0 Frozen + Reference Certified + Schema 登记 + 变更政策生效（Phase 6.7.5） |
| **Knowledge Domain** | **引用层（Corpus FROZEN-v1.0.0）** | Architecture Frozen（KB-001~020）+ Pipeline Validated + Corpus **FROZEN-v1.0.0**（`ziwei_corpus:v1.0.0`, 102 节点/47 关系/41 引用, digest `69d6e2a6…`, 2026-09-16; 变更须走 Corpus 级审查）+ Provenance AUDITED |
| **Knowledge/Schema** | **门控** | node_type/relation_type/ref_type 变更须 ACP/Schema Gate（参考 7.2A 流程） |
| Production Runtime | **部分实现** | Python 侧（`src/`）为唯一可用实现：Phase 0~5 完成/认证，Phase 6/7/8 已实现（含缺陷），Phase 9 仅桩；`crates/` 与 `services/` 仍是 bootstrap 占位。详见 §4 |

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

Production Runtime（`src/`, `crates/`, `services/`）是正式实现。Python 侧（`src/`）
是当前唯一可用实现；`crates/om-calendar`（1 crate，占位）与 `services/gateway`
（1 module，占位）尚未启动。

> 本表依据 **2026-09-16 只读代码审计**（逐模块取证）刷新，替换此前停留在
> 2026-08-17 的判定；审计明细与缺陷登记见 `docs/PROJECT_REVIEW_2026-09-16.md`。

| Phase | 领域 | 状态 | 说明 |
|-------|------|------|------|
| Phase 0 | 脚手架 | 完成 | pyproject.toml（src 布局）、ruff+pytest、sxtwl==2.0.7 锁定 |
| Phase 1 | 基础 (schemas, models, calendar, engines, config) | 完成 | core 6 模块全部实现；JSON Schema **仅运行时导出**（`BaseAgent.schema()` + `GET /agents/{name}/schema` + MCP `agent_schema`），**无落盘工件** |
| Phase 2 | 六爻 | 部分完成 | **领域专属 Schema 已存在**（`liuyao.py`：`LiuyaoInput`/`YaoLine`/`LiuyaoChart`/`LiuyaoOutput`）+ 纳甲/六亲/六神/世应/用神/本变互卦/种子起卦；缺契约化（规则清单→向量→契约→`reference/liuyao/`→等价认证） |
| Phase 3 | 八字 | **完成（Integration Ready）** | 四柱引擎（五虎遁/五鼠遁/立春界/23:00 换日）+ 藏干/纳音/十神/大运；契约 v1.0.0 Frozen（BC-001~014）+ Reference 独立实现（24/24 等价）。可选：机器可读契约 MANIFEST |
| Phase 4 | 紫微斗数 | **完成（Integration Ready）** | 定局表 + 十四主星 + 农历；契约 v1.0.0 Frozen（BC-001~014, ZW-001~017）+ Reference 独立实现（24/24 等价）；规则 ACP 已实施（Engine v0.3.0）。**边界**：辅星/四化/大限等属 ZW-017 未实现边界（须 ACP）；`agents/ziwei/pattern_matcher.py` 为死代码且不可导入（见审计 §2.3） |
| Phase 5 | 奇门遁甲 | **完成（Certified）** | 时家转盘排盘核心 + 契约冻结 v1.0.0 (QIMEN_BEHAVIOR_CONTRACT.md, QC-001~014) + 24 规范向量 + 适配层/ABI/Reference 域建模 + **Reference 认证（独立实现, 双实现验证）**；流派假设 D2/D14 已政策裁定 |
| Phase 6 | 共识智能体 | 部分完成 | `agents/consensus.py` 已实现并接入编排（`/orchestrate`）；缺机器可读契约适配层、生产↔Reference 等价测试；`majority`/`all` 策略无表决语义 |
| Phase 7 | 编排 + API | 部分完成（≈达成） | LangGraph 五步（validate→route→fan_out→consensus→respond）齐全 + 6 端点 + 自动 OpenAPI；缺独立 `/consensus` 端点、知识端点、鉴权/CORS |
| Phase 8 | 推理 + RAG | 部分完成 | provider（Ollama / OpenAI 兼容 Qwen·DeepSeek）+ Explainer 确定性后备 + InMemory/Qdrant 检索器均已实现；**缺陷**：RAG 全仓无 `.add()` → 检索恒空；provider/RAG 零测试；`BaziExplainer`/`ZiweiExplainer` 未接线且坏死 |
| Phase 9 | 运维 + 可扩展性 | **仅桩** | `mcp/server.py` 49 行契约桩（无 transport，`pyproject.toml` 无 mcp 依赖）；`docker-compose.yml` 已定义 PG/Qdrant/Valkey/Ollama 但 `src/` 零消费者；会话/追踪持久化未实现；无冒烟测试 |

**Production Runtime 测试总计**: 导入 `openmetaphysics.*`（`src/`）的测试文件 **20 个 / 230 例**，全部通过；另 `tests/test_qimen_reference_docs.py` 7 例（只读 docs 工件）与 `reference/tests/` 中直接对拍 `src` 的 9 例。**全仓收集 618 例**（2026-09-16 实测）。此前「457」口径已废弃。

---

## 5. Golden Tests 状态

### 5.1 测试总计

| 类别 | 测试数 | 通过 | 失败 |
|------|--------|------|------|
| Reference Runtime 核心（`test_reference_{rules,patterns,evidence,knowledge,consensus,conformance}.py`） | 304 | 304 | 0 |
| Production Runtime（导入 `openmetaphysics.*` 的 20 文件 **230** 例 + `test_qimen_reference_docs.py` **7** 例） | 237 | 237 | 0 |
| Knowledge Pipeline / Corpus 回归（`test_knowledge_pipeline.py` + `_corpus_r2` / `_corpus_r3` / `_corpus_relations`） | 29 | 29 | 0 |
| Reference 独立套件（`reference/tests/`，5 文件） | 48 | 48 | 0 |
| **总计（收集）** | **618** | **618（权威全绿口径）** | **0（真实缺陷）** |

> 实测：`pytest --collect-only -q` 收集 **618** 个测试（2026-09-16；此前「599 / 2026-08-17」口径已废弃）。
> Conformance Suite（57 测试 / 135 检查）已含于上表第一行的 304 例内，非独立增量。
> **对账**：304 + 237 + 29 + 48 = 618。
> 注：本机 DSH 文件沙箱曾以 `WinError 5/EPERM` 拒绝 4 个「子进程管道捕获」测试
> （`test_knowledge_pipeline.py` ×3 + `test_ziwei_equivalence::test_reference_independent_of_production`）。
> **2026-09-16 复测未复现**：`reference/tests/` 独立套件 **48/48 通过**（含 `test_ziwei_equivalence.py` 4 passed）。
> `reference/tests/` 仍需随全量套件从仓库根运行。

### 5.2 测试文件明细

| 文件 | 测试数 | 状态 |
|------|--------|------|
| `tests/test_reference_rules.py` | 29 | 全部通过 |
| `tests/test_reference_patterns.py` | 31 | 全部通过 |
| `tests/test_reference_evidence.py` | 46 | 全部通过 |
| `tests/test_reference_knowledge.py` | 71 | 全部通过 |
| `tests/test_reference_consensus.py` | 70 | 全部通过 |
| `tests/test_reference_conformance.py` | 57 | 全部通过 |
| `tests/test_reference_qimen.py` | 28 | 全部通过（Qimen 参考域独立套件） |
| `tests/test_api.py` | 7 | 全部通过 |
| `tests/test_bazi.py` | 11 | 全部通过 |
| `tests/test_calendar.py` | 6 | 全部通过 |
| `tests/test_consensus.py` | 3 | 全部通过 |
| `tests/test_determinism.py` | 4 | 全部通过 |
| `tests/test_liuyao.py` | 6 | 全部通过 |
| `tests/test_models.py` | 7 | 全部通过 |
| `tests/test_orchestration.py` | 4 | 全部通过 |
| `tests/test_qimen.py` | 33 | 全部通过 |
| `tests/test_qimen_contract.py` | 8 | 全部通过 |
| `tests/test_qimen_regression.py` | 26 | 全部通过 (24/24 向量) |
| `tests/test_qimen_adapter.py` | 7 | 全部通过 |
| `tests/test_qimen_contract_adapter.py` | 7 | 全部通过 |
| `tests/test_qimen_abi.py` | 5 | 全部通过 |
| `tests/test_qimen_reference_docs.py` | 7 | 全部通过 |
| `tests/test_solar_time.py` | 7 | 全部通过 |
| `tests/test_ziwei.py` | 33 | 全部通过 |
| `tests/test_bazi_golden_vectors.py` | 7 | 全部通过 |
| `tests/test_bazi_units.py` | 14 | 全部通过 |
| `tests/test_ziwei_golden_vectors.py` | 7 | 全部通过 |
| `tests/test_knowledge_pipeline.py` | 10 | 全部通过 |
| `tests/test_knowledge_corpus_r2.py` | 6 | 全部通过 |
| `tests/test_knowledge_corpus_r3.py` | 7 | 全部通过 |
| `tests/test_knowledge_corpus_relations.py` | 6 | 全部通过 |
| `reference/tests/test_equivalence.py` | 3 | 全部通过 |
| `reference/tests/test_bazi_equivalence.py` | 6 | 全部通过 |
| `reference/tests/test_ziwei_equivalence.py` | 4 | 全部通过（2026-09-16 复测，此前「沙箱拒绝」未复现） |
| `reference/tests/test_contract_boundaries.py` | 8 | 全部通过 |
| `reference/tests/test_golden_vectors.py` | 27 | 全部通过 |
| **合计** | **618** | 权威口径 618/618 全绿（2026-09-16 实测收集） |

### 5.3 Golden Vectors

| 层 | 向量数 | 文件 |
|----|--------|------|
| Rule | 6 | `reference/conformance/golden/rule_vectors.json` |
| Pattern | 5 | `reference/conformance/golden/pattern_vectors.json` |
| Evidence | 1 | `reference/conformance/golden/evidence_vectors.json` |
| Knowledge | 4 | `reference/conformance/golden/knowledge_vectors.json` |
| Consensus | 3 | `reference/conformance/golden/consensus_vectors.json` |
| **总计** | **19** | 自动发现，禁止人工维护 |

**Qimen Golden Vectors（Frozen Verification Artifacts）**:

| 向量集 | 向量数 | 状态 |
|--------|--------|------|
| `docs/qimen/golden_vectors.json` | **24** | **Frozen**，normative fixtures，机器回归 24/24，迁移须 ACP |
| `docs/bazi/golden_vectors.json` | **24** | **normative fixtures**（Engine v0.1.0，机器回归通过） |
| `docs/ziwei/golden_vectors.json` | **24** | **normative fixtures**（Engine v0.3.0，机器回归通过） |

### 5.4 Conformance Suite 结果

| 指标 | 值 |
|------|-----|
| 总检查数 | 135 |
| 通过 | 135 |
| 失败 | 0 |
| 认证状态 | **Certified**（强度见下注） |

> ⚠️ **认证强度注（2026-09-16 只读审计发现）**：135 个检查中含大量无条件通过 ——
> `_check_behavior_coverage` 硬编码 17 个 ID（BC 7/7、KB 4/20、CS 6/25）且一律
> `passed=True`，**CF-015（`CONFORMANCE_SPEC.md`）要求的 KB-001~020 + CS-001~025
> 共 83 个 ID 未验证**；`_check_ordering` / `_check_hash` / `_check_null` /
> `_check_enum` 四类亦为无条件 `passed=True`。故文中**不应表述为「覆盖率 100%」**，
> `certified=True` 的强度低于此前口径。已有域认证（Qimen 30/30、BaZi 24/24、
> Ziwei 24/24）由独立等价测试支撑，不受影响。处置见
> `docs/PROJECT_REVIEW_2026-09-16.md` §2.2 与 §4.2 P1-1（须 ACP / 缺陷提案，不得静默改 `reference/`）。

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

**当前 Sprint**: Knowledge / Ziwei 语料 —— **已完成并冻结（Phase 7.1.6 Corpus Freeze）**
（`ziwei_corpus:v1.0.0`：**102 节点 + 47 关系 + 41 引用**, digest `69d6e2a6…`；
Phase 7.2B-R/R2/R3 生产辅星 12 + 神煞 27，Phase 7.1.3 补齐 `yinyong(5)`/`shuyu(5)` 关系；
`Coverage Matrix` §1/§2 无未闭合项，唯一引用缺口 GAP-02；回归 618/618。
详见 `docs/governance/knowledge/KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md`。）

**Qimen Domain 状态**: **Frozen and Certified**（Integration Ready）

| 项 | 值 |
|----|-----|
| 契约版本 | **v1.0.0**（`docs/specification/QIMEN_BEHAVIOR_CONTRACT.md`, Frozen） |
| Reference 认证 | **Certified Independent Implementation**（`docs/qimen/reference_certification.md`, 2026-08-09） |
| Golden Vectors | **24 / 24 通过**（Frozen Verification Artifacts, 机器回归） |
| 双实现验证 | Product Runtime + Reference Runtime 双实现逐字节一致（30/30 等价, E017） |
| 测试 | 全仓库 green（含 reference/tests 独立套件） |

**已交付（历史 Sprint）**:
- Phase 5.7（对齐 Sprint）: Reference 自包含实现（astronomy.py 移植, 无 src 导入）+ 独立测试套件 38 例 + 审计/等价证明/认证工件（14/14 QC Full, 30/30 等价, E016/E017）
- Phase 5: 时家奇门转盘排盘核心（engine 0.3.0）
- Phase 5.1~5.4: 算法审查 / 规则裁定（12 Freeze）/ 向量扩充（24）/ Freeze Review（PASS）
- Phase 5.5~5.6: 契约草稿 → **契约正式冻结 v1.0.0**（D2/D14 政策裁定 + 向量提升 normative）
- Phase 5.7: Reference Qimen Domain 建模（reference/qimen/ 纯文档层）
- Phase 5.8/5.8A/5.8B/5.8C: 契约适配层（contracts 包）/ 契约 Schema 提取 / Runtime Adapter / Golden Vector 机器回归（E014）
- Phase 5.9A: Runtime 类型边界（TypedDict + ABI snapshot）
- 全量测试 530+ 通过（含 reference/tests 独立套件）
- Phase 6.5/6.6（BaZi）: 契约 **v1.0.0 Frozen**（BC-001~014）+ Reference 独立实现 +
  **24/24 等价认证** + Schema 登记 + 集成就绪审查 7/7 → **Integration Ready**
  （`docs/bazi/`，2026-08-13 历史重写后经分支合并）
- Phase 6.7.1（Ziwei）: 规则清单 **ZW-001~017**（14 Freeze Candidate + 3 REVISED）+
  测试 12 → 33 + 11 审计发现 + 4 项 ACP 决策（定局表公式化 / 廉贞 -8 / 输入校验 / sxtwl 锁版）
- Phase 6.7.1.5/6.7.1.6（Ziwei）: 4 项 ACP **IMPLEMENTED**（定局生成式 / 廉贞 -8 /
  输入校验显式化 / sxtwl==2.0.7 pin; Engine **v0.3.0**）
- Phase 6.7.2~6.7.5（Ziwei）: Golden Vector 生成（24）→ Freeze Review（PASS）→
  Reference Certified（24/24 等价）→ **Integration Ready**（契约 `ziwei:behavior:v1.0.0` Frozen）
- Phase 7.0（Knowledge）: Corpus Pipeline 验证（Ziwei 试点 20/12/3）+ 确定性 Pipeline +
  KB-001~020 校验
- Phase 7.1.0~7.1.6（Knowledge）: Corpus 全量建设 —— Scope/Source 冻结 → 核心词汇 41 →
  关系/引用/天干/地支/五合扩展 → **63 节点 + 37 关系 + 10 引用**（sha256 9c222617）
- Phase 7.2A（Knowledge）: Schema Admission Gate —— shen_sha / auxiliary_star 均裁定
  **A（已存在，无需 ACP）**；GAP-05 Schema 部分 RESOLVED；零数据生产
- Phase 7.2B（Knowledge, 2026-08-17）: shen_sha / auxiliary_star **证据驱动生产
  —— 0 产出**（三命通会/渊海子平 webfetch 失败 → GAP-13; 紫微全书原文未入库 +
  全集未获取 → GAP-12）; Corpus 维持 63/37/10
- Phase 7.3（Knowledge, 2026-08-25）: Source Acquisition & Evidence Availability
  —— 来源状态登记（SOURCE_STATUS.md, 四来源 FETCH_BLOCKED/NOT_ATTEMPTED）+
  webfetch 阻塞 → **0 生产**; 语料 sha 规范化 LF 口径 b1b8f90a（内容不变 63/37/10）
- Phase 7.3.1（Knowledge, 2026-09-15）: **Tier 1 来源获取与逐字证据核验** ——
  紫微斗數全書（卷一/二/三）、三命通會（卷一~九）、淵海子平 全部 **revision-pinned**
  获取 + sha256 登记; 逐字核验 **36/36 义理断言 + 10/10 转录差异核验 PASS**
  → **GAP-12/GAP-13 证据侧阻塞解除**（EVIDENCE_VERIFIED）; **0 生产**（未获重跑授权）;
  语料维持 63/37/10（corpus sha b4af74ab, 仅 source_digests 同步）
- Phase 7.2B-R（Knowledge, 2026-09-15）: **shen_sha / auxiliary_star 首批生产** ——
  23 节点（auxiliary_star 12 + shen_sha 11）+ 12 条 classic_text 条目级引用
  （含羊刃三源对照）; 语料 **86/37/22**（sha256 9a213728）; 逐节点原文关键句核验
  **23/23 PASS**; 测试 599/599; GAP-05/12/13（限定范围）CLOSED
- Phase 7.2B-R2（Knowledge, 2026-09-15）: **三命通會卷三其余神煞** —— 追加
  7 节点（空亡/元辰/灾煞/六厄/勾绞/天罗地网/十恶大败）+ 10 条条目级引用;
  语料 **93/37/32**（sha256 ce3b83b7）; key_quote 7/7 + passage 10/10 核验 PASS;
  测试 **605/605**（新增 6 条回归测试）
- Phase 7.2B-R3（Knowledge, 2026-09-16）: **三命通會卷三其余神煞** —— 追加 9 节点
  （金舆/三奇/天德/月德/太极贵/学堂/词馆/德秀/暗金煞）+ 9 条条目级引用;
  语料 **102/37/41**（sha256 9a… → digest `69d6e2a6…`）
- Phase 7.1.3 补齐（Knowledge, 2026-09-16）: 关系层 `yinyong(5)` + `shuyu(5)`
  → 语料 **102/47/41**; 引文逐字 10/10 + 端点 10/10 PASS
- **Phase 7.1.6 Corpus Freeze（Knowledge, 2026-09-16, D-12=A 批准）**:
  `ziwei_corpus:v1.0.0` 正式冻结（102 节点 + 47 关系 + 41 引用, digest `69d6e2a6…`）;
  Coverage Matrix §1/§2 无未闭合项，唯一引用缺口 GAP-02; 此后变更须走 **Corpus 级审查**;
  回归 **618/618**。详见 `docs/governance/knowledge/KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md`

---

## 8. Next Sprint

**下一步（待用户明确授权）**：

- ~~关系层生产（Knowledge）: 神煞/辅星 ↔ 干支/主星 的关联~~ → **§2 规划内的
  `yinyong(5)` / `shuyu(5)` 已完成（2026-09-16）**；其余 ×7（fuzhu/zhiyue/duiying/
  yingxiang/zengqiang/xueroo/zhixiang）仍属后续阶段（解释域/断事），未规划生产
- ~~Corpus 扩展: 三命通會卷三其余神煞~~ → **已完成（Phase 7.2B-R2/R3）**
- ~~Corpus 冻结~~ → **已完成（Phase 7.1.6 Corpus Freeze v1.0.0, D-12=A）**；
  此后任何语料变更须走 **Corpus 级审查**（见冻结记录 §2）
- **开放项（不阻塞冻结, 待裁定）**: GAP-02（school_commentary 唯一引用缺口）/
  D-11（GAP-15 星曜五行多源冲突口径）/ D-6（四化 schema, 须 ACP）/ D-7（auxiliary_star
  是否扩至卷一杂曜, 须 scope 批准）/ D-3 抓取快照入库 / D-5 GAP-01 版本核验
- **Ziwei 计算域**: Integration Ready 为生命周期终点；辅星/四化/大限等属 ZW-017
  冻结边界，扩展须 **ACP + 用户授权**
- 其它 Knowledge Corpus 扩展（pattern / 断事类 / 用神类等，随授权）
- 其它领域契约化路径复用 Qimen/BaZi 流程（标准: `docs/governance/CAPABILITY_LIFECYCLE.md`；
  状态: `docs/governance/CAPABILITY_STATUS.md`）
- Qimen/BaZi/Ziwei 功能扩展（格局判断 / 用神，需新授权）
- Reference Runtime 最终冻结（Reference Freeze Candidate -> Frozen）
- 本文档 + docs/governance/CAPABILITY_STATUS.md + knowledge/README.md 等随各 Sprint 持续刷新

### 8.1 Production Runtime 收口（2026-09-16 只读代码审计新增）

**P0 —— 立即（无需新授权）**
- **状态指针刷新**：`PROJECT_STATUS.md` §1/§2/§4/§5/§7/§9/§10/§11 + `CAPABILITY_STATUS.md`
  + `ROADMAP.md` + `项目进展梳理.md`（^ 本次已执行）
- **死代码清理**：`src/openmetaphysics/agents/ziwei/pattern_matcher.py`（108 行；零导入、
  目录缺 `__init__.py` 导致不可导入、且落在紫微契约 §4 显式排除的「格局识别」范围内）
- **仓库清理**：根目录 `phase_7.2b_r2_status.txt` 一次性状态戳
- **分支清账**：8 条未合并本地分支逐一给结论

**P1 —— 可信度与治理债务（建议优先于新功能）**
- **D-13 Conformance 空转处置**（见 §5.4 注；须 ACP 或缺陷提案，不得静默改 `reference/`）
- **D-14 Reference Runtime 范围扩张 ACP 补正**（KnowledgeStore / Consensus 未走 ACP）
- **契约补全**：`rule_contract.json` / `pattern_contract.json` + 生成器 + diff 测试
- **坏死/空转修复**：`ZiweiExplainer` 字段契约修复或删除；RAG 接线（灌入 `KnowledgeChunk`）；
  为 `inference/providers.py` / `rag/retriever.py` 补测试

**P2 —— 主线候选（1~2 周，择一，需授权）**
- **A（推荐）六爻域契约化**：Schema 定稿 → 规则清单 → 向量 → Freeze Review → 契约 v1.0.0
  → `reference/liuyao/` 独立实现 → 24/24 等价 → 治理注册（10+ 文件，零算法创新）
- **B Reference Runtime 最终冻结**（依赖 P1 的 ACP 补正与契约补全）
- **C Production Runtime Phase 9 收口**：MCP transport 接线 + 依赖声明；compose 补应用服务；
  会话/追踪持久化；RAG 接线

**本轮新增 GAP 登记（建议）**: GAP-16 Conformance 行为覆盖空转（17/100）·
GAP-17 Reference Runtime 范围扩张未走 ACP · GAP-18 `ZiweiExplainer` 坏死未接线 ·
GAP-19 RAG 检索恒空

---

## 9. 关键文档索引

| 文档 | 位置 | 用途 |
|------|------|------|
| AGENTS.md | 根目录 | 长期规则（硬规则 H1~H8 + 效率规则 E1~E7；2026-09-15 精简版） |
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
| Governance | `docs/governance/` | 领域能力标准（CAPABILITY_LIFECYCLE.md）+ 登记模板（DOMAIN_CAPABILITY_TEMPLATE.md）+ 状态登记（CAPABILITY_STATUS.md） |
| Qimen 认证工件 | `docs/qimen/reference_certification.md` | Qimen Reference 认证记录 |
| Ziwei 认证工件 | `docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT.md` / `reference/ziwei/` | Ziwei 契约 / Reference 认证 |
| Knowledge 治理 | `docs/governance/knowledge/` | Scope / Source / Admission / Build Plan / Coverage / Gaps / 各 Phase 报告 |
| Knowledge 语料 | `knowledge/` | 数据源（sources）、语料（corpus）、Pipeline（pipeline.py / validate.py）、输出（ziwei_corpus.json） |

---

## 10. Standard Environment（uv）

本项目使用 uv 管理可复现的 Python 环境。

| 项 | 值 |
|----|-----|
| Python | 3.11（`.python-version` 固定） |
| 包管理 | uv（`uv sync --all-extras`） |
| 锁文件 | `uv.lock` |
| 核心依赖 | pydantic / fastapi / uvicorn / langgraph / httpx / pyyaml / jinja2 / sxtwl（==2.0.7 精确锁定） |

> **sxtwl 说明**: 农历计算依赖 `sxtwl`。其最新版（2.0.7）仅提供 Python 3.11
> 的 Windows 预编译 wheel（3.12 / 3.13 需 MSVC 从源码编译）。因此项目固定
> Python 3.11，保证 `uv sync` 在 Windows 上一键成功，无需编译工具链。核心
> 计算（Reference Runtime）不依赖 sxtwl，可完全离线测试。

### 搭建步骤

```bash
uv sync --all-extras                         # 创建 .venv 并安装全部依赖
uv run pytest -q                             # 运行全量测试（618/618，2026-09-16）
```

---

## 11. 开发流程约定

> ⚠️ **本节 2026-08-12 原文已被 `AGENTS.md`（2026-09-15 精简版）取代**，
> 原「每轮对话 MUST 归档 + MAY 禁止直接改 main」的仪式性要求已删除。
> **现行规则以 `AGENTS.md` §1 硬规则 H1~H8 与 §2 效率规则 E1~E7 为准**：
>
> - **E1 决策分级**：文档 / 测试 / 内部重构 / GAP 登记 / **状态指针刷新** / 清理已合并分支
>   属自主执行（无需请示）；冻结工件或规范变更（H3 走 ACP）、跨域写、合并到 main、
>   付费或真实外部主体实验、对外发布必须请示。
> - **E3 状态指针单一权威**：能力/语料唯一指针为 `docs/governance/CAPABILITY_STATUS.md`（合并时更新）；
>   本文件只在**阶段边界**更新；`context/归档.md` 仅在合并或 Sprint 完成时追加（≤15 行）。
> - **E4 轻量变更可直推 main**：归档记录、状态指针刷新、错别字/GAP 编号修正、已合并分支清理、
>   纯格式/注释修正可跳过分支；其余（代码、数据、契约、报告、实验工件）走
>   `work/<领域>/<主题>` 分支。
> - **H7 合并门槛**：仅测试全绿 + 确定性可复现的分支可合并；合并需用户授权。

### 历史约定（2026-08-12，已归档不再生效）

每次对话 MUST 遵守：输出归档 + 分支工作流 + 用户把控合并。

- 每轮对话结束前，将本轮产出追加归档至 `context/归档.md`（追加式，不覆盖历史）。
- 所有代码/文档输出在独立分支 `work/<领域>/<主题>` 上进行，禁止直接改 main。
- 是否合并、是否进入下一步，由用户决定。

### 工具链编码约定（Windows UTF-8 修复）

系统活动代码页为 936 (GBK)，工具子进程输出曾被误读为乱码。已修复：

- opencode shell 改为 UTF-8 wrapper（`~/.config/opencode/opencode.json` 的 `shell` 指向
  `C:\Users\lkl\AppData\Local\Programs\opencode-utf8\pwsh.exe`，注入 `chcp 65001` +
  UTF-8 编码引导后转发真实 pwsh）。
- 本仓库 `.git/config` 已设置 `core.quotepath false`（git 中文文件名正常显示）。

> 备注：`HKCU\Console\CodePage` 注册表方案与 pwsh profile 方案对工具子进程均无效
> （opencode 强制 `-NoProfile` 且管道化 spawn），详见 `context/归档.md` 首条记录。
