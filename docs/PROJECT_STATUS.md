# PROJECT_STATUS

> **最后更新**: 2026-08-09
> **项目阶段**: Reference Freeze Candidate
> **Qimen Domain**: **Frozen and Certified**（契约冻结 + Reference 认证 + 双实现验证）

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
| Phase 3 | 八字 | 部分完成 | 四柱引擎已实现，全部测试通过 |
| Phase 4 | 紫微斗数 | 部分完成 | 宫位 + 十四主星已完成 |
| Phase 5 | 奇门遁甲 | **完成（Certified）** | 时家转盘排盘核心 + 契约冻结 v1.0.0 (QIMEN_BEHAVIOR_CONTRACT.md) + 24 规范向量 + 适配层/ABI/Reference 域建模 + **Reference 认证（独立实现, 双实现验证）**；流派假设 D2/D14 已政策裁定 |
| Phase 6 | 共识智能体 | 未开始 | - |
| Phase 7 | 编排 + API | 部分完成 | FastAPI 骨架已建立 |
| Phase 8 | 推理 + RAG | 未开始 | - |
| Phase 9 | 运维 + 可扩展性 | 未开始 | - |

**Production Runtime 测试总计**: 457 个，全部通过（含 Qimen 系列：排盘 33 + 契约 8 + 回归 26 + 适配器 7 + 契约适配 7 + ABI 5 + Reference 文档 7）。

---

## 5. Golden Tests 状态

### 5.1 测试总计

| 类别 | 测试数 | 通过 | 失败 |
|------|--------|------|------|
| Reference Runtime | 304 | 304 | 0 |
| Conformance Suite | 57 (测试) / 135 (检查) | 57 / 135 | 0 |
| Production | 77 | 77 | 0 |
| **总计** | **457** | **457** | **0** |

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

**Qimen Golden Vectors（Frozen Verification Artifacts）**:

| 向量集 | 向量数 | 状态 |
|--------|--------|------|
| `docs/qimen/golden_vectors.json` | **24** | **Frozen**，normative fixtures，机器回归 24/24，迁移须 ACP |

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

**当前 Sprint**: Phase 6.0 — Domain Capability Framework Standardization
（生命周期标准 `CAPABILITY_LIFECYCLE.md` + 模板 `DOMAIN_CAPABILITY_TEMPLATE.md`
+ 领域审计 `CAPABILITY_STATUS.md`；治理文档标准化评审，无功能实现）

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

---

## 8. Next Sprint

**待定**。等待用户明确指示。

可能的方向：
- 其他领域（八字/紫微/六爻）契约化路径复用 Qimen 流程（标准: `docs/governance/CAPABILITY_LIFECYCLE.md`；状态: `docs/governance/CAPABILITY_STATUS.md`）
- Qimen 功能扩展（格局判断 / 用神，需新授权）
- Reference Runtime 最终冻结（Reference Freeze Candidate -> Frozen）

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
| Governance | `docs/governance/` | 领域能力标准（CAPABILITY_LIFECYCLE.md）+ 登记模板（DOMAIN_CAPABILITY_TEMPLATE.md）+ 状态登记（CAPABILITY_STATUS.md） |
| Qimen 认证工件 | `docs/qimen/reference_certification.md` | Qimen Reference 认证记录 |

---

## 10. Standard Environment（uv）

本项目使用 uv 管理可复现的 Python 环境。

| 项 | 值 |
|----|-----|
| Python | 3.11（`.python-version` 固定） |
| 包管理 | uv（`uv sync --all-extras`） |
| 锁文件 | `uv.lock` |
| 核心依赖 | pydantic / fastapi / uvicorn / langgraph / httpx / pyyaml / jinja2 / sxtwl |

> **sxtwl 说明**: 农历计算依赖 `sxtwl`。其最新版（2.0.7）仅提供 Python 3.11
> 的 Windows 预编译 wheel（3.12 / 3.13 需 MSVC 从源码编译）。因此项目固定
> Python 3.11，保证 `uv sync` 在 Windows 上一键成功，无需编译工具链。核心
> 计算（Reference Runtime）不依赖 sxtwl，可完全离线测试。

### 搭建步骤

```bash
uv sync --all-extras                         # 创建 .venv 并安装全部依赖
.venv/Scripts/python -m pytest -q            # 运行全量测试（381/381）
```
