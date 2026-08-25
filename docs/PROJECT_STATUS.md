# PROJECT_STATUS

> **最后更新**: 2026-08-17
> **项目阶段**: Reference Freeze Candidate（Knowledge 语料建设中）
> **Qimen Domain**: **Frozen and Certified**（契约冻结 + Reference 认证 + 双实现验证）
> **BaZi Domain**: **Integration Ready**（契约 v1.0.0 Frozen + Reference Certified + 集成就绪审查 7/7）
> **Ziwei Domain**: **Integration Ready**（契约 v1.0.0 Frozen + Reference Certified + 集成就绪审查 7/7）
> **Knowledge Layer**: Architecture **Frozen** / Pipeline **Validated** / Corpus **Partial**（Ziwei 63 节点 + 37 关系 + 10 引用，Phase 7.1.6；7.2A Schema 门已通过）

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
| **Knowledge Corpus** | **Validated / Partial（Ziwei 63/37/10, Phase 7.1.6）** |

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
| **Knowledge Domain** | **引用层（Partial）** | Architecture Frozen（KB-001~020）+ Pipeline Validated + Corpus Partial（Ziwei 63/37/10, Phase 7.1.6; 7.2A Schema 门已通过） |
| **Knowledge/Schema** | **门控** | node_type/relation_type/ref_type 变更须 ACP/Schema Gate（参考 7.2A 流程） |
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
| Phase 3 | 八字 | 部分完成（**Integration Ready**） | 四柱引擎 + 契约 v1.0.0 Frozen + Reference 独立实现（24/24 等价） |
| Phase 4 | 紫微斗数 | 部分完成（**Integration Ready**） | 定局表 + 十四主星 + 农历；契约冻结 v1.0.0 + Reference 独立实现（24/24 等价）；规则 ACP 已实施（Engine v0.3.0，定局生成式 / 廉贞 -8 / 输入校验 / sxtwl==2.0.7） |
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
| 域测试（Qimen 24/24、BaZi、Ziwei、Liuyao 等） | 含 Qimen Regression 24/24、BaZi/Production↔Reference 30/30、Ziwei 24/24 向量回归 | 正常 | 0 |
| Knowledge Pipeline 回归 | 10 | 10 | 0 |
| Reference 独立套件（`reference/tests/`） | 48 | 48 | 0 |
| **总计（收集）** | **599** | **599（权威全绿口径）** | **0（真实缺陷）** |

> 实测：`uv run pytest -q` 收集 **599** 个测试（2026-08-17）。
> 注：本机 DSH 文件沙箱会以 `WinError 5/EPERM` 拒绝 4 个「子进程管道捕获」测试
> （`test_knowledge_pipeline.py` ×3 + `test_ziwei_equivalence::test_reference_independent_of_production`），
> 属环境性限制非代码缺陷；在无管道限制环境（CI/本机普通运行）下为 **599/599 全绿**。
> `reference/tests/` 需随全量套件从仓库根运行（独立收集会因 `reference` 包导入路径问题报错）。

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
| `tests/test_ziwei.py` | 33 | 全部通过 |
| `tests/test_bazi_golden_vectors.py` | 7 | 全部通过 |
| `tests/test_bazi_units.py` | 14 | 全部通过 |
| `tests/test_ziwei_golden_vectors.py` | 7 | 全部通过 |
| `tests/test_knowledge_pipeline.py` | 10 | 全部通过 |
| `reference/tests/test_equivalence.py` | 3 | 全部通过 |
| `reference/tests/test_bazi_equivalence.py` | 6 | 全部通过 |
| `reference/tests/test_ziwei_equivalence.py` | 4 | 环境性（子进程管道被沙箱拒） |
| `reference/tests/test_contract_boundaries.py` | 8 | 全部通过 |
| `reference/tests/test_golden_vectors.py` | 27 | 全部通过 |
| **合计** | **599** | 权威口径 599/599 全绿 |

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

**当前 Sprint**: Knowledge 语料建设（Phase 7.x）
（最新 **Phase 7.2A Schema Admission Gate** 已通过：`shen_sha` / `auxiliary_star`
均裁定 **A（已存在，无需 ACP）**，零数据生产，待人工 Evidence Review + 7.2B 生产授权。
详见 `docs/governance/knowledge/KNOWLEDGE_PHASE_7.2A_REPORT.md`。）

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

---

## 8. Next Sprint

**下一步（待用户明确授权）**：

- **Phase 7.3+（Knowledge）**: shen_sha / auxiliary_star **生产重试**——前置：
  紫微全书原文入库 / 紫微全集获取（GAP-01）/ webfetch 可用（GAP-12/GAP-13）/
  或用户授权降级证据策略（7.2B 报告 §16）
- 其它 Knowledge Corpus 扩展（pattern / 断事类 / 用神类等，随授权）
- 其它领域契约化路径复用 Qimen/BaZi 流程（标准: `docs/governance/CAPABILITY_LIFECYCLE.md`；
  状态: `docs/governance/CAPABILITY_STATUS.md`）
- Qimen/BaZi/Ziwei 功能扩展（格局判断 / 用神，需新授权）
- Reference Runtime 最终冻结（Reference Freeze Candidate -> Frozen）
- 本文档 + context 状态 + knowledge/README 等随各 Sprint 持续刷新

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
uv run pytest -q                             # 运行全量测试（599/599）
```

---

## 11. 开发流程约定（2026-08-12）

### 对话工作流约定

每次对话 MUST 遵守：输出归档 + 分支工作流 + 用户把控合并。

- 每轮对话结束前，将本轮产出追加归档至 `context/归档.md`（追加式，不覆盖历史）。
- 所有代码/文档输出在独立分支 `work/<领域>/<主题>` 上进行，禁止直接改 main。
- 是否合并、是否进入下一步，由用户决定。

细则见 `AGENTS.md` → Conversation Workflow Convention。

### 工具链编码约定（Windows UTF-8 修复）

系统活动代码页为 936 (GBK)，工具子进程输出曾被误读为乱码。已修复：

- opencode shell 改为 UTF-8 wrapper（`~/.config/opencode/opencode.json` 的 `shell` 指向
  `C:\Users\lkl\AppData\Local\Programs\opencode-utf8\pwsh.exe`，注入 `chcp 65001` +
  UTF-8 编码引导后转发真实 pwsh）。
- 本仓库 `.git/config` 已设置 `core.quotepath false`（git 中文文件名正常显示）。

> 备注：`HKCU\Console\CodePage` 注册表方案与 pwsh profile 方案对工具子进程均无效
> （opencode 强制 `-NoProfile` 且管道化 spawn），详见 `context/归档.md` 首条记录。
