# Capability Status

> 领域能力成熟度跟踪（Domain Maturity Tracking）— 唯一权威状态登记
> 状态模型与迁移规则: `docs/governance/CAPABILITY_LIFECYCLE.md`
> 登记模板: `docs/governance/DOMAIN_CAPABILITY_TEMPLATE.md`
> 更新: 2026-09-16（Phase 7.1.6 **Corpus Freeze v1.0.0** —— 语料 102/47/41, D-12=A 批准；
> 同日按只读代码审计刷新 Qimen 测试列与 **Liuyào Schema 条目** —— 见 `docs/PROJECT_REVIEW_2026-09-16.md`）
> 2026-10-03（**P2.1 BaZi Knowledge Integration** —— 新增 `bazi_corpus:0.1.0`
> 40/67/14 并接入既有 Pipeline / 校验器 / Retriever / Explain 链路；Ziwei 冻结语料
> 字节未变（digest `69d6e2a6…`）；不新增治理流程）
> 2026-10-03（**P2.2 Qimen Knowledge Integration** —— 新增 `qimen_corpus:0.1.0`
> 47/60/15 接入同一条 RAG→Explain 链路；Ziwei 与 BaZi 语料字节未变；
> 不新增治理流程、不修改冻结 Schema / Qimen 契约 / 计算逻辑）
> 2026-10-19（**P2.3 Liuyao Knowledge Integration** —— 新增 `liuyao_corpus:0.1.0`
> 43/54/23；首个 revision-pinned 逐章逐字核验的来源域《增刪卜易》；
> 接入同一条 RAG→Explain 链路；Ziwei / BaZi / Qimen 语料字节未变；
> 不修改冻结 Schema / 契约 / 计算逻辑）
> 2026-10-19（**P2.4 Liuyao Knowledge Enrichment II** —— `liuyao_corpus:0.2.0`
> 61/66/41；新增 18 个结构/法则 pattern 节点与 18 条逐字引用；
> 同域深化，Ziwei / BaZi / Qimen 语料字节未变；不修改冻结 Schema / 契约 / 计算逻辑）
> 2026-10-23（**Liuyao Contract Freeze** —— `ACP-LIUYAO-001` 批准 D1-D4；
> 契约 v1.0.0 **Frozen**（30 条）+ 25 Golden Vectors **Frozen** +
> Reference **Certified**；Freeze Review / Audit PASS。Liuyao 状态升级
> **Integration Ready（Certified Frozen Capability）**）
> 2026-10-24（**项目审计 + Sprint 0 真实性收口** —— 复核四域 Integration Ready /
> Certified 与生产运行时真实缺口；清理 12 条已合并分支、修正状态指针与 GAP 记录）
> 2026-10-24（**Sprint 1 / ACP-KNOWLEDGE-001** —— YAML 固定 LF，Ziwei 冻结语料
> digest `69d6e2a6…` → `93dba067…`（EOL 勘误，内容零变化）；Liuyao/BaZi/Qimen
> 全量 digest 由测试锚定；Linux/LF 与 Windows 均可复现；已合并 `a77c7f6`）
> 2026-10-24（**Sprint 2 / ACP-REF-002** —— Reference Runtime 范围追认与契约补全；
> Rule/Pattern 契约补齐至 5 层；CF-016~CF-019 落地；规范 v1.1.0；
> `REFERENCE_FREEZE_REVIEW.md` PASS，Reference Runtime 状态升级 **Frozen**）
> 2026-10-24（**Sprint 3 / 生产硬化** —— Qdrant ingestion（upsert + 自动建
> collection）+ `query_points` / legacy `search` 回退 + 失败回退 InMemory；
> provider HTTP 离线 mock 测试（Ollama / OpenAI 兼容）；当时全仓 1073 / 1071+2）
> 2026-10-24（**Sprint 4 / Liuyao Corpus Freeze v1.0.0** —— 41 条 revision-pinned
> 逐字引用；metadata candidate→frozen、0.2.0→1.0.0，内容零变化；digest `3a09a08e…`；
> BaZi 经评审推迟（待 H6 证据扩展））
> 2026-10-24（**Sprint 5 / Phase 9 核心收口** —— MCP stdio JSON-RPC transport
> （无外部 SDK）+ Postgres 会话/追踪持久化（SQLAlchemy，失败回退 InMemory）+
> Dockerfile / compose app profile；全仓 1089 / 1087+2）
> 2026-10-24（**BaZi Corpus Freeze v1.0.0（有界）** —— H6 9/14 逐字 +
> 5 convention-level；metadata candidate→frozen、0.1.0→1.0.0；digest `488ce510…`；
> Qimen 维持 candidate（revision pin 已登记））
> 2026-10-24（**Qimen Corpus Freeze v1.0.0（有界）** —— 10/15 revision-pinned 逐字 +
> 5 摘要；metadata candidate→frozen、0.1.0→1.0.0；digest `ffeb3319…`；
> 四域语料全部 frozen）

---

## 状态矩阵（Domain Status Matrix）

| Domain | Status | Contract | Golden Vectors | Reference | 测试 |
|--------|--------|----------|----------------|-----------|------|
| **Qimen** | **Integration Ready**（Certified Frozen Capability） | v1.0.0 Frozen | 24（Frozen） | Certified（双实现验证） | 93 + 28 |
| **BaZi** | **Integration Ready**（Certified Capability） | v1.0.0 Frozen | 24（normative） | Certified（24/24 等价） | 11 + 14 + 7 + 6 |
| **Ziwei** | **Integration Ready**（Certified Capability） | v1.0.0 **Frozen**（`ziwei:behavior:v1.0.0`, 2026-08-13） | 24（normative fixtures） | Certified（24/24 等价, `reference/ziwei/`） | 33 + 7 + 4 |
| **Liuyào** | **Integration Ready**（Certified Frozen Capability） | v1.0.0 Frozen（`liuyao:behavior:v1.0.0`, 2026-10-23, 30 条） | 25（Frozen） | Certified（独立实现；21/21 + 40/40） | 6 + 6 + 8 |
| **Reference Runtime** | **Frozen**（ACP-REF-002，2026-10-24） | 5 层契约 v1.0.0 | 5 层 / 19 向量 | Self-conformant（176/176 certified） | 373 |
| Consensus | N/A（非计算域；Evidence 引擎独立实现） | — | — | 等价认证（52 输入 + 3 向量） | 32 |
| Knowledge Layer | 引用层（不产生计算输出） | Architecture **FROZEN**（KB-001~020）; Pipeline **VALIDATED**（多域）; Corpus **FROZEN-v1.0.0**（`ziwei_corpus:v1.0.0`, 102 节点 / 47 关系 / 41 引用, digest `93dba067…`，2026-10-24 EOL 勘误（内容零变化），原 `69d6e2a6…`，2026-09-16 D-12=A 批准）+ **BaZi FROZEN v1.0.0（有界证据）**（`bazi_corpus:v1.0.0`, 40 节点 / 67 关系 / 14 引用, digest `488ce510…`, 2026-10-24：9/14 逐字 + 5 convention-level）+ **Qimen FROZEN v1.0.0（有界证据）**（`qimen_corpus:v1.0.0`, 47 节点 / 60 关系 / 15 引用, digest `ffeb3319…`, 2026-10-24：10/15 逐字 + 5 摘要）+ **Liuyao FROZEN v1.0.0**（`liuyao_corpus:v1.0.0`, 61 节点 / 66 关系 / 41 引用, digest `3a09a08e…`, 2026-10-24 Corpus Freeze —— P2 系列首个 revision-pin 逐章逐字核验域）; Provenance **AUDITED**（Qimen 为书级归属 + 章节锚点；Liuyao 为 revision pin + 逐字核验）。冻结程序与变更门槛见 `docs/governance/knowledge/KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md` | — | — | 全仓库回归（2026-10-24 全绿, 含 BaZi/Qimen/Liuyao 语料/检索/Explain E2E, 1087 passed + 2 skipped） |

> **只标记实际状态**: 本表仅反映已完成的工件与验证。未达到的阶段不得
> 标注为已完成。
> **Phase 6.1**: BaZi 迁移评估完成（`docs/governance/bazi/Bazi_CAPABILITY_ASSESSMENT.md`）,
> 状态维持 Implemented（无虚报）。模板领域无关性审查:
> `docs/governance/CAPABILITY_TEMPLATE_REVIEW.md`。
> **Phase 6.4**: BaZi **Freeze Review PASS**（`BAZI_FREEZE_REVIEW.md`, B1~B6 冻结,
> Deferred 项裁定, 24 向量充分）→ 契约草案
> （`docs/bazi/BAZI_BEHAVIOR_CONTRACT_DRAFT.md`, `bazi:behavior:0.1.0-draft`）→
> 状态升级 **Contract Candidate**（契约尚未正式冻结）。
> **Phase 6.5**: BaZi 契约正式冻结 **v1.0.0**（`BAZI_BEHAVIOR_CONTRACT.md`）+
> Reference 独立实现（`reference/bazi/`, 无 src 导入）+ 14/14 BC 审计 +
> **24/24 Production == Reference 等价** → 状态升级 **Reference Certified**。
> **Phase 6.6**: BaZi Schema 登记（SCHEMAS.md §3.1）+ 变更政策生效 +
> 集成边界审查 7/7（`BAZI_INTEGRATION_READINESS.md`）→ 状态升级
> **Integration Ready**（完整生命周期完成）。
> **Phase 7.0**: Ziwei 迁移评估完成（`docs/governance/ziwei/` 4 份工件）;
> 状态维持 **Implemented**（无虚报）; Framework 可零修改复用（结论:
> Reusable without modification）。
> **Phase 6.7.1**: Ziwei 算法稳定化完成（2026-08-13）—— 审计
> `ZIWEI_ALGORITHM_AUDIT.md` + 假设 `ZIWEI_ALGORITHM_ASSUMPTIONS.md` +
> 规则裁定 `ZIWEI_RULE_DECISION.md`（14 Freeze Candidate / 3 Deferred）+
> 跨域边界 `ZIWEI_CROSS_DOMAIN_BOUNDARIES.md` + 向量设计
> `ZIWEI_GOLDEN_VECTOR_READINESS.md` + 补测 +21（12→33, 全绿）。
> 状态维持 **Implemented**; 未创建契约/向量/Reference。
> **Phase 6.7.1.5**: 决策解决（2026-08-13）—— 四项裁定全部 **REVISED +
> ACP Required（未执行）**: A-1 定局表（统一生成规则）、A-2 廉贞 -8、
> ZW-001 输入校验、sxtwl 固定 `2.0.7`。完整记录
> `docs/governance/ziwei/ZIWEI_DECISION_RESOLUTION.md`; 状态维持
> **Implemented**; Phase 6.7.2 向量生成必须等待 ACP 执行。
> **Phase 6.7.1.6**: ACP 实施（2026-08-13）—— ACP-ZW-001（定局表生成式,
> 统一规则 起宫 丑/辰/亥/午/酉 + 步长 2/3/3/3/3）、ACP-ZW-002（廉贞 -8）、
> ACP-ZW-003（输入校验显式化）、ACP-ZW-004（sxtwl==2.0.7 pin）全部
> **IMPLEMENTED**（记录: `docs/governance/ACP/`）; Engine **v0.3.0**;
> 快照/校验测试迁移; 全仓库 578/578 全绿（2026-08-13 当时口径，现为 1089 collected / 1087 passed + 2 skipped）; Ziwei 规则集无 ACP 阻塞,
> Phase 6.7.2 向量生成可按修订规则集启动。状态维持 **Implemented**。
> **Phase 6.7.2**: Golden Vector 生成（2026-08-13）—— 24 个规范性向量
> `docs/ziwei/golden_vectors.json`（Engine v0.3.0 输出生成, status=candidate,
> 17/17 规则覆盖 + A-1/A-2 专项 PASS）+ 回归测试 7 例; 全仓库 585/585 全绿（2026-08-13 当时口径）。
> 状态维持 **Implemented**。
> **Phase 6.7.3**: Freeze Review & Gate（2026-08-13）—— 证据审查 6/6 PASS;
> 边界裁定 A-3/A-4/A-6/A-7 全部 **FROZEN**（显式声明）; 17 规则终态
> （3 IMPLEMENTED + 14 FROZEN）; Verdict **PASS** → 契约草案
> `docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT_DRAFT.md`（BC-001~014）。
> 状态维持 **Implemented**。
> **Phase 6.7.4**: Reference Certification（2026-08-13）—— `reference/ziwei/`
> 独立实现（tables/astronomy/domain, 无 src 导入, 显式复用 reference/bazi
> 共享原语）+ **24/24 Golden Vector 等价** + 4 例等价测试 + 14/14 BC 审计 +
> 认证记录 → 状态升级 **Reference Certified**。
> **Phase 6.7.5**: Integration Ready Closure（2026-08-13）—— 契约正式冻结
> **`ziwei:behavior:v1.0.0`**（BC-001~014, 2026-08-13）+ Freeze Integrity
> Check 8/8 + Schema 登记确认（SCHEMAS.md §3.2）+ 变更政策生效 +
> 集成边界审查 7/7（`ZIWEI_INTEGRATION_READINESS.md`）→ 状态升级
> **Integration Ready**（完整生命周期完成, 与 Qimen/BaZi 并列）。
> **Phase 7.0**: Knowledge Pipeline Validation（2026-08-13）—— `knowledge/`
> 试点语料（Ziwei 20 节点/12 关系/3 引用）+ 确定性 Pipeline + KB-001~020
> 校验 + 10 回归测试（报告:
> `docs/governance/knowledge/KNOWLEDGE_SPRINT_0_REPORT.md`）→
> Knowledge Layer 状态: Architecture **FROZEN**（未变）/ Pipeline
> **VALIDATED** / Corpus **PARTIAL**（仅指针更新, 不升级——引用层不产生
> 计算输出）。
> **Phase 7.1.1**: Ziwei Core Vocabulary（2026-08-13）—— 新增 21 节点
> （main_star +9 / palace +7 / ten_god +5, 均 Tier 1 来源, 武曲/贪狼含
> 中州派 SchoolView）+ Pilot 20 节点正式化 → **41/41 节点完成**,
> 校验/确定性通过（报告: `docs/governance/knowledge/KNOWLEDGE_PHASE_7.1.1_REPORT.md`）。
> Corpus: **PARTIAL**（Ziwei, 41 节点; 关系/引用待 7.1.2/7.1.3; 仍为引用层, 不升级）。
> **Phase 7.1.0**: Ziwei Corpus Scope & Source Freeze（2026-08-13）——
> 7 份治理工件（Scope / Source Registry / Admission Policy / Pilot Audit /
> Coverage Matrix / Build Plan / Gaps）→ Corpus 范围与来源策略**已冻结**
> （第一波: 41 节点 + 24 关系 + 8 引用; 构建序列 7.1.1~7.1.6）。
> Knowledge Layer 状态: Architecture **FROZEN** / Pipeline **VALIDATED** /
> Corpus **PARTIAL**（Scope 已冻结, 语料数量未变; 仍为引用层, 不升级）。
> **Phase 7.1.2~7.1.6**: Ziwei Relations & References 生产（2026-08-13）——
> 7.1.2 he/chong 关系（18 关系, xing/hai 缺口 GAP-09）; 7.1.3 引用与 provenance
> （+4 引用, GAP-02 REMAINS OPEN）; 7.1.4B 地支 12 节点 + xing 5（GAP-09 关闭）;
> 7.1.5 天干 10 节点 + 三命通会 xing 3 / hai 6（GAP-10 CLOSED）; 7.1.6 五合 5
> （he_wu_he）→ Corpus **63 节点 / 37 关系 / 10 引用**（sha256 9c222617）。
> **Phase 7.2A**: Schema Admission Gate（2026-08-17）—— `shen_sha` 与
> `auxiliary_star` 两类型经 KB-002 / `reference/knowledge.py::NodeType` /
> `knowledge_contract.json` 三处冻结权威交叉核对均裁定 **A（已存在, 无需 ACP）**;
> 零数据生产; **GAP-05 Schema 部分 RESOLVED**（剩余阻塞 = 来源选定 + 7.2B 生产授权）;
> 报告 `docs/governance/knowledge/KNOWLEDGE_PHASE_7.2A_REPORT.md`。
> Knowledge Layer 状态: Architecture **FROZEN** / Pipeline **VALIDATED** /
> Corpus **PARTIAL**（Ziwei 63/37/10; Schema 已进 7.2B 前; 仍为引用层, 不升级）。
> **Phase 7.2B**: shen_sha / auxiliary_star 证据驱动生产（2026-08-17）—— Tier 1 原文
> 不可达（三命通会/渊海子平 webfetch 失败 → GAP-13；紫微全书未入库 → GAP-12、
> 全集未获取 → GAP-01）→ **0 生产**; Corpus 维持 63/37/10（sha256 9c222617）。
> **Phase 7.3**: Source Acquisition & Evidence Availability（2026-08-25）—— 来源状态登记
> （SOURCE_STATUS.md, 四来源 FETCH_BLOCKED/NOT_ATTEMPTED / Source Discovery 🟡
> SOURCE_DISCOVERED）+ webfetch 4 次阻塞 → **0 生产**; 语料 sha 规范化 LF 口径
> b1b8f90a（内容不变 63/37/10）; Knowledge Layer 状态维持 **PARTIAL**（引用层, 不升级）。
> **Phase 7.3.1**: Tier 1 来源获取与逐字证据核验（2026-09-15）—— Phase 7.3 §9 的
> 四项下一步执行完毕: 紫微斗數全書（卷一/卷二/卷三, revid 7913704/1963110/2268626）、
> 三命通會（卷一~卷九, 卷三 revid 2184219）、淵海子平（revid 2593607）全部
> revision-pinned 获取 + sha256 登记; 逐字核验 **36/36 义理断言 PASS + 10/10 转录差异
> 核验 PASS**（`KNOWLEDGE_PHASE_7.3.1_EVIDENCE_DOSSIER.md`）; GAP-12/GAP-13 →
> **EVIDENCE_VERIFIED**（证据侧）; **Knowledge Production 0**（未获 7.2B 重跑授权）;
> 语料维持 63/37/10（corpus sha b4af74ab, 仅 `metadata.source_digests` 同步）。
> 报告: `docs/governance/knowledge/KNOWLEDGE_PHASE_7.3.1_REPORT.md`。
> Knowledge Layer 状态维持 **PARTIAL**（引用层, 不升级; 证据就绪 ≠ 生产授权）。
> **Phase 7.2B-R**: shen_sha / auxiliary_star 证据驱动生产（2026-09-15）—— 首批
> **23 节点（auxiliary_star 12 + shen_sha 11）+ 12 引用**; 语料 **86/37/22**
> （sha256 9a213728）; 逐节点原文关键句核验 23/23 PASS, 测试 599/599;
> GAP-05/12/13（限定范围）CLOSED; D-2 实测结论: 冻结契约 golden_examples 为 query 级
> 且 node_types 已含两类型 → **生产不触发 ACP**。报告:
> `docs/governance/knowledge/KNOWLEDGE_PHASE_7.2B_RERUN_REPORT.md`。
> **Phase 7.2B-R2**: 三命通會卷三其余神煞（2026-09-15）—— 追加 **7 节点**
> （空亡/元辰/灾煞/六厄/勾绞/天罗地网/十恶大败）+ **10 引用**; 语料 **93/37/32**
> （sha256 ce3b83b7）; key_quote 7/7 + passage 10/10 机器核验 PASS; 测试 **605/605**;
> 报告 `docs/governance/knowledge/KNOWLEDGE_PHASE_7.2B_R2_REPORT.md`。
> **P2.1 BaZi Knowledge Integration**（2026-10-03）—— 复用既有 Knowledge / RAG /
> Explain 架构（未新建第二套架构、未改 Retriever 算法、未引入 embedding/向量库）:
> 新增 **`bazi_corpus:0.1.0`（candidate）** = 40 节点（五行 6 / 十神 10 /
> 日主·月令 2 / 天干 11 / 地支 13）+ 67 关系（五行生克、天干五合、地支六合、
> 六冲、三合、三会、刑（含自刑）、六害、六破）+ 14 引用；`pipeline.py` /
> `validate.py` 多域化（Ziwei 输出逐字节不变, digest `69d6e2a6…`）;
> `rag/corpus.py` 多域加载 + `retriever` 默认索引两域; 新增 BaZi 语料/校验/
> 检索/Explain/HTTP E2E/确定性测试。**BaZi 未新增冻结契约、未修改计算逻辑**。
> 已知缺口（schema: 破无 `po` 类型 → 以 `duiying`+subtype 承载; 日主/月令无专用
> node_type; 章节级逐字核验范围有限）记录于 `knowledge/README.md` §7。
> 语料**未升级为 frozen**（需独立 Corpus 级审查）。
> **P2.2 Qimen Knowledge Integration**（2026-10-03）—— 复用同一 Knowledge / RAG /
> Explain 架构（未新建第二套知识系统、未改 Retriever 算法、未引入 embedding/向量库）:
> 新增 **`qimen_corpus:0.1.0`（candidate）** = 47 节点（九宫 10 / 八门 9 / 九星 10 /
> 八神 9 / 奇门结构与法则 9）+ 60 关系（属于（成员/体系归属）+ 对应（地盘宫↔星·
> 宫↔门配属、值符↔值符神、阳遁↔阴遁、旬首↔六仪、三奇↔六仪、空亡↔旬首、
> 三元↔阴阳遁））+ 15 引用；节点文本保持纯中文（避免拉丁词污染字符级稀有度权重）。
> `pipeline.py` / `validate.py` / `rag/corpus.py` 三处登记即完成接入；新增
> `QimenExplainer`（**仅**覆写检索查询构造，prompt 契约与离线 fallback 沿用通用
> 实现），修复「通用查询从不携带 阴遁/阳遁·节气·局数·值符·值使」的实测缺陷。
> 结果: 九宫/八门/九星/八神/阴遁/阳遁/值符/值使 八项必需术语 **top-1 命中**;
> `POST /agents/qimen/explain` HTTP E2E（含 provider timeout / knowledge 不可用）
> 全绿。**未修改 Qimen frozen contract、golden vectors、计算逻辑、KB Schema**;
> Ziwei 冻结语料 digest `69d6e2a6…` 与 BaZi 语料 digest `69b6edea…` 均未变（当时口径）。
> 已知缺口（GAP-QIMEN-01 八门无专用 node_type; GAP-QIMEN-02 结构/法则无专用
> node_type; GAP-QIMEN-03 八神流派命名差异; Qimen 无 revision-pin 逐字核验;
> 跨平台 YAML EOL 会影响 `source_digests`）记录于 `knowledge/README.md` §7。
> **`.gitattributes` 未修改**（建议规则会改变冻结 Ziwei digest，前提不成立）。
> **P2.3 Liuyao Knowledge Integration**（2026-10-19）—— 复用同一 Knowledge / RAG /
> Explain 架构（未新建第二套知识系统、未改 Retriever 算法、未引入 embedding/向量库）:
> 新增 **`liuyao_corpus:0.1.0`（candidate）** = 43 节点（六亲 6 / 六神 7 / 八宫 9 /
> 结构法则 13（本卦·变卦·动爻·世应·纳甲·月建·日辰·旬空·六冲卦·六合卦·三合局·三刑·仇神）/
> 五行 5 / 用神体系 3（用神·元神·忌神））+ 54 关系（属于 + 五行生克 + 结构对应 +
> 月建/日辰作用）+ 23 引用；节点文本保持纯中文。
> **P2 系列首个 revision-pinned 证据域**: 《增刪卜易》主页 revid 2572918 + 17 个子页
> revid / 原始字节 SHA-256 逐条登记（`sources/liuyao/source_liuyao_01.yaml`），
> 已核章节**逐字核验**（transcription 异文逐条登记，不静默改写）。
> `pipeline.py` / `validate.py` / `rag/corpus.py` 三处登记即完成接入；新增
> `LiuyaoExplainer`（**仅**覆写检索查询构造, prompt 契约与离线 fallback 沿用通用实现），
> 修复「通用查询的 6 个语义槽被六亲占满，卦名/六神/世应/纳甲永不进入查询」的实测缺陷。
> 结果: 18 项组合/单术语查询 top-1 命中 Liuyao 节点；`POST /agents/liuyao/explain`
> HTTP E2E（含 provider timeout / knowledge 不可用 / k 边界 / 可复现）全绿。
> **未修改任何冻结契约、golden vectors、计算逻辑、KB Schema**；Ziwei digest
> `69d6e2a6…`、BaZi `69b6edea…`、Qimen `40de5c45…` 均未变（当时口径）。
> 已知缺口（GAP-LIUYAO-01 六亲无专用 node_type; -02 结构/法则无专用 node_type;
> -03 元神无专用 node_type; -04 仇神无专用 node_type; -05 互卦无定义性原文故不生产）
> 记录于 `knowledge/README.md` §7。
> **P2.4 Liuyao Knowledge Enrichment II**（2026-10-19）—— 同一域、同一架构:
> `liuyao_corpus` 0.1.0 → **0.2.0** = 61 节点（+18 结构/法则: 暗动·动散·卦变生克墓绝·
> 反吟·伏吟·生旺墓绝·应期·游魂·归魂·月破·飞神·伏神·进神·退神·随鬼入墓·独发·独静·两现）
> / 66 关系（+12）/ 41 引用（+18）。证据新增 7 个子页 revision pin（/22 /23 /24 /25
> /26又1 /26又3 /26又4）+ 主页卷之二第 27–32 章逐字核验；每条 passage 以清洗后原文
> 子串复核（保留 𨿽/眞/塡/﹐/﹑/﹕ 等异体字）。
> 评估但**未采纳**查询扩展: 向 `LiuyaoExplainer` 增加 12 个结构术语会把
> `kn:palace:liuyao_kan` 挤出 top-10（实测），损害卦盘特异检索；本轮保持 explainer
> 不变，语料仅作为可检索引用层。
> 结果: 36 项查询 top-1 命中（P2.3 18 + P2.4 18）；全仓库 1023 passed + 2 skipped；
> `validate.py` PASS；corpus digest `52efbff5…`。Ziwei/BaZi/Qimen 字节未变。
> 缺口: GAP-LIUYAO-02 扩展至 31 节点；GAP-LIUYAO-06 星煞章未收录（schema 归属与
> 价值密度未定）。

---

## Qimen

**Status**:

Integration Ready — **Certified Frozen Capability**（完整生命周期 Stage 0→4）

**Contract**:

v1.0.0（`docs/specification/QIMEN_BEHAVIOR_CONTRACT.md`, `contract_id: qimen:behavior:v1.0.0`）

**Reference**:

Certified（`docs/qimen/reference_certification.md`, 2026-08-09）
Independent Implementation, 双实现验证（Product == Reference, 30/30 等价）

**Verification**:

24 Golden Vectors（`docs/qimen/golden_vectors.json`, Frozen Verification Artifacts, 机器回归 24/24）

**Change Policy**:

ACP Required（ACP + 契约版本递增 + Golden Vector 迁移 + Reference 重新认证）

**冻结工件（Frozen Artifacts）**:

- Qimen Behavior Contract v1.0.0
- Golden Vector 数据集（24 向量）
- Reference Certification Report

**Constraints / Forbidden**:

- 禁止修改 `src/openmetaphysics/domain/qimen/` 算法代码
- 禁止修改 `reference/qimen/` 算法文件
- 禁止修改测试（除文档校验类测试）
- 禁止修改 Behavior Contract
- 禁止修改 Golden Vector 数据
- 禁止添加解释规则（Interpretation）
- 禁止添加新依赖

**范围之外（不属于冻结能力）**:

Interpretation / Recommendation / Narrative Generation / Belief Scoring /
LLM Reasoning / RAG Knowledge / Consensus Decision。Qimen 域只产生
确定性观测结果。

---

## BaZi（八字）

**Status**:

**Integration Ready** — Certified Capability（Phase 6.6, 2026-08-09）
—— 完整生命周期 Stage 0→4 完成: 契约 v1.0.0 Frozen + Reference Certified +
Schema 登记 + 变更政策生效 + 集成边界审查 PASS（
`docs/bazi/BAZI_INTEGRATION_READINESS.md`, 7/7）。
> 评估依据: `docs/governance/bazi/Bazi_CAPABILITY_ASSESSMENT.md`（Phase 6.1）
> Phase 6.2 稳定化工件（Draft, 未冻结）: `docs/bazi/BAZI_ALGORITHM_ASSUMPTIONS.md` /
> `docs/bazi/BAZI_RULE_DECISION.md` / `docs/bazi/BAZI_GOLDEN_VECTOR_PLAN.md` /
> `docs/bazi/BAZI_TEST_COVERAGE_REVIEW.md`
> Phase 6.3 证据（Candidate）: **24 向量**（`docs/bazi/golden_vectors.json`,
> engine 0.1.0, status=candidate）+ `BAZI_FREEZE_BOUNDARY.md` +
> `tests/test_bazi_golden_vectors.py`（7 例）+ `BAZI_GOLDEN_VECTOR_REPORT.md`
> Phase 6.4 冻结: `BAZI_FREEZE_REVIEW.md`（B1~B6 FROZEN, Deferred 裁定,
> 向量充分）+ `BAZI_CROSS_DOMAIN_BOUNDARIES.md` +
> `BAZI_BEHAVIOR_CONTRACT_DRAFT.md`（DRAFT）+ `tests/test_bazi_units.py`（14 例）
> Phase 6.5 认证: `BAZI_BEHAVIOR_CONTRACT.md`（**v1.0.0 Frozen**）+
> `reference/bazi/` 独立实现 + `BAZI_REFERENCE_AUDIT.md`（14/14 PASS）+
> `reference/tests/test_bazi_equivalence.py`（**24/24 等价**）+
> `BAZI_REFERENCE_CERTIFICATION.md`
> Phase 6.6 闭环: SCHEMAS.md §3.1 登记 + `BAZI_INTEGRATION_READINESS.md`（7/7）

**Calculation Layer**:

- 算法: `src/openmetaphysics/agents/bazi.py`（BaziEngine v0.1.0: 四柱, 十神/藏干/纳音/大运）
- 确定性: 是（无 LLM 参与；determinism 测试覆盖）
- Schema: 领域专属 `BaziInput`/`BaziChart`/`Pillar`/`DaYun`（`extra="forbid"`,
  位于 `agents/bazi.py`）；**未登记 SCHEMAS.md / 未导出 JSON Schema**
- 测试: `tests/test_bazi.py`（11）+ `tests/test_bazi_units.py`（14, Phase 6.4 补齐）

**Contract Layer**:

- 契约: **Frozen v1.0.0** `docs/bazi/BAZI_BEHAVIOR_CONTRACT.md`
  （`bazi:behavior:v1.0.0`; Draft 历史保留于 BAZI_BEHAVIOR_CONTRACT_DRAFT.md）
- 冻结规则: **B1~B6 FROZEN**（`BAZI_FREEZE_REVIEW.md` PASS）
- Golden Vectors: 24（**normative fixtures**, 机器回归 7 例通过）
- 政策裁定: 晚子时 23:00 换日; 大运 round(x.5) 银行家舍入

**Reference Layer**:

- 独立实现: `reference/bazi/`（tables/astronomy/domain, **无 src 导入**, 测试强制）
- 认证: **Certified** `docs/bazi/BAZI_REFERENCE_CERTIFICATION.md`
  （14/14 BC 审计 + 24/24 Production == Reference 精确等价）
- 变更政策: 任何变更须 ACP + 契约版本递增 + 向量迁移 + Reference 重新认证

**下一步（Reference Certified 退出条件 → Integration Ready）**:

- ~~Stage 4 治理注册完成~~ ✅（本表登记 + `BAZI_INTEGRATION_READINESS.md` 7/7, Phase 6.6）
- ~~变更政策生效~~ ✅（契约 §5 + 本表, 与 CAPABILITY_LIFECYCLE.md §5 一致）
- ~~SCHEMAS.md 登记~~ ✅（§3.1, 按冻结契约 BC-013 实际结构）
- 可选: JSON Schema 导出（`Model.model_json_schema()`, 未实现, 不影响状态）

---

## Ziwei（紫微斗数）

**Status**:

**Integration Ready** — Certified Capability（Phase 6.7.5, 2026-08-13）
—— 完整生命周期 Stage 0→4 完成: 契约 v1.0.0 Frozen + Reference Certified +
Schema 登记 + 变更政策生效 + 集成边界审查 PASS（
`docs/governance/ziwei/ZIWEI_INTEGRATION_READINESS.md`, 7/7 + Freeze Integrity 8/8）。
> Phase 7.0 评估（2026-08-09）: `docs/governance/ziwei/ZIWEI_CAPABILITY_ASSESSMENT.md`
> + `ZIWEI_RULE_INVENTORY.md`（ZW-001~017）+ `ZIWEI_TEST_COVERAGE_REVIEW.md`
> + `ZIWEI_CROSS_DOMAIN_PRECHECK.md`（ZB-01~09 / ZQ-01~04 差异登记）

**Calculation Layer**:

- 算法: `src/openmetaphysics/agents/ziwei.py`（ZiweiEngine **v0.3.0**:
  命宫/身宫, 五行局, 十四主星定局, 农历转换; 辅星/四化/大限未实现;
  Phase 6.7.1.6: 定局表统一生成规则 + 廉贞 -8 + 输入校验）
- 确定性: 是（无 LLM; replay 测试锁定）
- Schema: **领域专属** `ZiweiInput`（lunar_month/lunar_day 显式重放）/
  `ZiweiChart`/`Palace`（`extra="forbid"`）; SCHEMAS.md §3.2 已登记
  （Phase 6.7.1 完成勘误: calendar_note 位于 ZiweiChart; 未导出 JSON Schema）
- 测试: `tests/test_ziwei.py`（**33 例** = 12 基线 + 21 Phase 6.7.1 补测:
  定局表 150 组合快照 / 全 5 局 / 星曜位置 / 时区链 / 时辰窗 / 闰月 /
  立春界 / 序列化; 覆盖矩阵见 `ZIWEI_TEST_COVERAGE_REVIEW.md` §5）

**Contract Layer**:

- **契约**: **v1.0.0 Frozen**（`docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT.md`,
  `contract_id: ziwei:behavior:v1.0.0`, 2026-08-13, BC-001~014）
- **Golden Vectors**: `docs/ziwei/golden_vectors.json`（**24**, normative
  fixtures, Engine v0.3.0 生成, 机器回归 24/24）
- **变更政策**: ACP Required（ACP + 契约版本递增 + Golden Vector 迁移 +
  Reference 重新认证; 契约 §1/§6 + 本表 Ziwei 节 + INTEGRATION_READINESS §2）
- 规则裁定工件: `ZIWEI_ALGORITHM_ASSUMPTIONS.md`（ZW-A1~A15）/
  `ZIWEI_RULE_DECISION.md`（ZW-001~017: **3 IMPLEMENTED + 14 FROZEN**）/
  `ZIWEI_DECISION_RESOLUTION.md` + `docs/governance/ACP/ACP-ZW-001~004.md` /
  `ZIWEI_CROSS_DOMAIN_BOUNDARIES.md`（ZB-01~09 / ZQ-01~04）/
  `ZIWEI_GOLDEN_VECTOR_READINESS.md`

**Reference Layer**:

- `reference/ziwei/`（tables / astronomy / domain, **独立实现, 无 src 导入**;
  共享原语显式复用 `reference/bazi/*`——立春界/干支/纳音）
- `reference/tests/test_ziwei_equivalence.py`（4 例: 24/24 等价 / 独立性 /
  确定性 / 序列化）
- 审计: `docs/governance/ziwei/ZIWEI_REFERENCE_AUDIT.md`（**14/14 PASS**）;
  认证: `ZIWEI_REFERENCE_CERTIFICATION.md`

**冻结工件（Frozen Artifacts）**:

- Ziwei Behavior Contract v1.0.0（`docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT.md`）
- Golden Vector 数据集（24 向量, `docs/ziwei/golden_vectors.json`）
- Reference 独立实现 + 认证记录（`reference/ziwei/` +
  `ZIWEI_REFERENCE_CERTIFICATION.md`）
- 集成边界审查（`ZIWEI_INTEGRATION_READINESS.md`, 7/7）

**约束（Constraints / Forbidden）**:

- 禁止修改 `src/openmetaphysics/agents/ziwei.py` 算法代码
- 禁止修改 `reference/ziwei/` 算法文件
- 禁止修改 Behavior Contract / Golden Vector 数据
- 禁止添加解释规则 / 新依赖（须 ACP）

**范围之外（不属于冻结能力）**:

辅星/杂曜/四化/大限/流年 / 格局分析 / 解释层 / 叙述 / 建议 / LLM / RAG /
Consensus（契约 §4 显式排除; 任何新增能力须 ACP）

**下一步**:

- 无（Integration Ready = 完整生命周期终点, 对齐 Qimen/BaZi）。
- 未来能力扩展（功能 Sprint）与契约化升级须经 ACP + 用户授权。

---

## Liuyào（六爻）

**Status**:

**Integration Ready — Certified Frozen Capability**（2026-10-23，`ACP-LIUYAO-001`
D1-D4 批准；完整生命周期 Stage 0→4）

**Calculation Layer**:

- 算法: `src/openmetaphysics/agents/liuyao.py`（361 行；起卦/纳甲/六亲/六神/世应/用神/本变互卦）
- 确定性: 是（显式 `casts` 或显式 `seed` → `deterministic_rng(derive_seed(payload))`；
  **注意**：自动 seed 受 `PYTHONHASHSEED` 影响，跨进程不可复现 —— 见 `LC-D04`，
  且该路径**不属于冻结契约**）
- Schema: 领域专属模型 `LiuyaoInput` / `YaoLine` / `LiuyaoChart` / `LiuyaoOutput`
  （`agents/liuyao.py` L28 / L43 / L51 / L69），经 `AgentRegistry.schema()` 暴露为 JSON Schema；
  已在 `docs/SCHEMAS.md §3.4` 登记。
- 测试: `tests/test_liuyao.py`（6 例）+ `tests/test_liuyao_golden_vectors.py`（6 例）
  + `reference/tests/test_liuyao_equivalence.py`（8 例）

**Contract Layer**:

- 规则清单: `docs/liuyao/LIUYAO_RULE_INVENTORY.md`（LY-01~LY-11 + 输入校验 + 5 项已知边界）
- 行为契约: `docs/liuyao/LIUYAO_BEHAVIOR_CONTRACT.md`（**Frozen** v1.0.0；
  `liuyao:behavior:v1.0.0`；30 条，ID 范围 LC-001~LC-052）
- Golden Vectors: `docs/liuyao/golden_vectors.json`（**25 Frozen**：normal 10 / edge 6 / boundary 5 / invalid 4）
- Freeze Review: `docs/liuyao/LIUYAO_FREEZE_REVIEW.md`（**PASS**）
- Reference Audit: `docs/liuyao/LIUYAO_REFERENCE_AUDIT.md`（**PASS**）

**Reference Layer**:

- `reference/liuyao/`（**自包含**，不导入 `openmetaphysics`）：`domain.py` + `tables.py` + `astronomy.py` + `README.md`
- 认证: `docs/liuyao/LIUYAO_REFERENCE_CERTIFICATION.md`（**CERTIFIED**，2026-10-23）
- 等价证明: `reference/tests/test_liuyao_equivalence.py`
  —— 21/21 合法向量 + **40/40** 生成输入**逐字节一致**；4 条拒绝路径、
  4 个显式 seed、5 个换日边界；Reference 表与生产表**一致性守卫**、
  Reference 源码独立性断言

**下一步**:

- ~~领域专属 Schema 定义~~ → **已完成**（`docs/SCHEMAS.md §3.4`）
- ~~规则清单 + Golden Vectors → Reference 独立实现 → 等价认证~~ → **已完成**（Phase B，2026-09-16）
- ~~ACP 批准 + 冻结 metadata + 认证生效 + 状态升级~~ → **已完成**（2026-10-23）。
- 合并收口：已获 H7 授权，合并 `7a6d7bb`、归档 `930ae70`、EOL 固定 `a27bb4a`（2026-10-23）。未推送 origin。
- 文档：`ROADMAP` / `PROJECT_STATUS` / `README` / `SCHEMAS` / `reference/liuyao/README.md`
  / 规则清单已同步为 Integration Ready（见 `docs/liuyao/LIUYAO_INTEGRATION_READINESS.md` §5）。

**已知代码缺陷（2026-09-16 审计，非计算域契约影响；Phase B 未改动算法）**:

- `LiuyaoEngine._changed_yao` 中 `flipped` 重复赋值（`agents/liuyao.py` L258-260，首处为死赋值）
- `_select_yong_shen` 经 `LiuyaoEngine._yong_shen = staticmethod(...)` 猴子补丁挂载（L336）

---

## Reference Runtime（行为规范层）

**Status**: **Frozen**（2026-10-24，`ACP-REF-002` 批准并实施；`REFERENCE_FREEZE_REVIEW.md` PASS）

**范围**: 核心模块家族（models / parser / engine / patterns / pattern_matcher /
evidence_builder / knowledge_query / consensus_builder / conformance_runner）+
4 域 Reference（qimen / bazi / ziwei / liuyao）+ 5 层契约 + 5 层 Golden Vectors。

**冻结判据（ACP-REF-002 §5）**:

| # | 判据 | 状态 |
|---|------|------|
| 1 | ACP-REF-002 追认与规范修订 | DONE（`REFERENCE_RUNTIME_SPEC` v1.1.0） |
| 2 | ACP-REF-001 认证口径定稿（D-16） | DONE（`CONFORMANCE_SPEC` v1.1.0：executed representation） |
| 3 | 契约层 5 份齐平 | DONE（rule/pattern/evidence/knowledge/consensus，各 v1.0.0 + diff 测试） |
| 4 | CAPABILITY_STATUS 登记行 + 退出判据 | DONE（本节） |
| 5 | Reference 级冻结审查工件 | DONE（`docs/governance/REFERENCE_FREEZE_REVIEW.md`） |
| 6 | 门槛验证 | DONE（Reference 373 测试；全仓 1028+2；Conformance 176/176 certified；5 层 golden 重生成逐字节一致） |

**已知边界（不阻塞冻结）**: derived ordering/hash/null/enum 检查仍标注
“derived from golden match”（D-13 遗留）；CF-015 显式要求 52 个行为 ID
（非全部 80）；其他语言实现未纳入本冻结面。

---

## Consensus（共识 — 非计算域）

**Status**: N/A（不适用领域生命周期）

自 Phase C4 起，共识明确为**两个不同 capability**，不做合并
（事实报告与判定：`docs/CONSENSUS_CAPABILITY_CLARIFICATION.md`）：

| Capability | 实现 | 输入 | 输出 | 治理 |
|---|---|---|---|---|
| **Cross-Modal Consensus**（`CrossModalConsensus`，现名 `ConsensusAgent`） | `src/openmetaphysics/agents/consensus.py` | `list[AgentOutput]` | 一致矩阵 / 冲突 / 综合（`contributions`+`agreement_matrix`+`synthesis`） | 无契约；由 `tests/test_consensus.py` 覆盖 |
| **Evidence Consensus** | `reference/consensus_builder.py` + **生产** `src/openmetaphysics/consensus/`（2026-10-24 并列落地） | `list[Evidence]` + `ConsensusConfig` | `ConsensusReport{conclusions, conflicts, evidence_ids}` | `CONSENSUS_BEHAVIOR_SPEC.md`（CS-001~025，**Frozen**）+ `reference/contracts/consensus_contract.json` v1.0.0 + `ConsensusContractAdapter`（含 `build_consensus`）+ conformance CONSENSUS 层（3 向量） |

- orchestration（`orchestration/graph.py::_consensus`）使用的是 **Cross-Modal Consensus**（API 不变）。
- Evidence Consensus 自 2026-10-24 起有**独立生产实现**：52 输入与 Reference 逐字节等价、
  冻结向量 3/3 复放一致；`ConsensusContractAdapter` 经 `openmetaphysics.contracts` 导出。
- 两个 capability **并列共存**（S-1 = 并列，2026-10-24 裁定），互不影响。

---

## 生命周期参考

领域能力按三层生命周期固化：Domain Calculation Layer → Behavior Contract
Layer → Reference Verification Layer（状态模型见 `CAPABILITY_LIFECYCLE.md`，
架构定位见 `docs/ARCHITECTURE.md` §1）。
