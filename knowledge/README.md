# Knowledge 语料库（Knowledge Corpus）

> **阶段**: Phase 7.1.6 —— **Ziwei Corpus Freeze v1.0.0**（2026-09-16, D-12=A 批准）
> + **P2.1 BaZi Knowledge Integration**（2026-10-03, BaZi Corpus candidate 0.1.0）
> **状态**: **Pipeline Validated**；Ziwei Corpus **FROZEN（`ziwei_corpus:v1.0.0`）**；
> BaZi Corpus **CANDIDATE（`bazi_corpus:0.1.0`）**
> **规范基准**: `docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md`（KB-001~020, Frozen）+
> `docs/design/phase6/01_knowledge_layer_architecture.md`（Frozen）+
> 规范性模型 `reference/knowledge.py`
> **边界**: Knowledge 为**只读引用层**，不参与任何计算、不产生结论、
> 不修改 Evidence / Confidence（KB 契约架构边界）。

---

## 1. 范围

- **语料域**: Ziwei（冻结 v1.0.0）+ BaZi（P2.1 候选 0.1.0）。
- **Ziwei 演进**: Phase 7.0 试点（20 节点/12 关系/3 引用，验证 Pipeline）→
  Phase 7.1.1~7.1.6 全量建设（核心词汇 → 天干/地支/关系/引用扩展）→
  Phase 7.2A Schema 门 → 7.2B-R/·R2/·R3 证据驱动生产（辅星/神煞）→
  **Phase 7.1.6 关系层补齐（yinyong/shuyu）+ Corpus Freeze v1.0.0**。
  当前 **102 节点 + 47 关系 + 41 引用**（`ziwei_corpus.json` 实测, digest `69d6e2a6…`）。
  治理进展见 `docs/governance/knowledge/`（Scope/Source/Admission/Build Plan/
  Coverage Matrix/Gaps/各 Phase 报告/**7.1.6 FREEZE**）。
- **BaZi 演进（P2.1, 2026-10-03）**: 首批**最小而有实际价值**的结构化语料 ——
  五行基础（5+旺衰 1）/ 十神全量（10）/ 日主与月令（2）/ 十天干（10）/ 十二地支（12）
  = **40 节点**；关系（五行生克 / 天干五合 / 地支六合 / 六冲 / 三合 / 三会 /
  刑（含自刑）/ 六害 / 六破）= **67 关系**；条目级引用 **14**（`bazi_corpus.json`）。
  目标链路（已由测试锁定）:
  `BaZi calculation → deterministic result → BaZi knowledge retrieval →
  explanation context → /agents/bazi/explain → HTTP response`。
  证据级别与剩余缺口见本文件 §7 与 P2.1 交付报告（章节级逐字核验范围有限，
  未核验原文一律不引用）。
- **变更流程（Ziwei 冻结后）**: 任何 node/relation/reference 变更须走 **Corpus 级审查**
  （提案 → 逐字证据核验 → validate/确定性/回归 → 人工批准 → 版本递增）。
  见 `docs/governance/knowledge/KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md`。
  BaZi 语料为 candidate，同样遵守 `ZIWEI_CORPUS_ADMISSION_POLICY.md` 的准入原则
  （Schema 有效 / 语义有效 / provenance 非空 / 来源已登记 / 确定性序列化 / 冲突显式）。
- **来源**: Tier 1 来源（`sources/ziwei/` 紫微斗数全书; `渊海子平`; `三命通会`；
  `sources/bazi/` 复用同一已 revision-pinned 获取的 `渊海子平` + `三命通会`）——
  原始数据引用，**不包含**古籍全文

## 2. 目录结构

```text
knowledge/
├── README.md                  # 本文件
├── sources/<domain>/          # 来源元数据（引用，非数据）
├── corpus/<domain>/
│   ├── nodes/                 # KnowledgeNode
│   ├── relations/             # KnowledgeRelation
│   └── references/            # KnowledgeReference
│   # <domain> ∈ {ziwei, bazi}
├── pipeline.py                # 确定性合并 + 校验 + checksum（多域）
├── validate.py                # Schema 校验（KB-001~020，多域 + 跨域 ID 唯一性）
├── ziwei_corpus.json          # Pipeline 输出（确定性 JSON, 勿手改）
└── bazi_corpus.json           # Pipeline 输出（确定性 JSON, 勿手改）
```

## 3. 统计

| 语料 | 状态 | nodes | relations | references |
|------|------|-------|-----------|------------|
| `ziwei_corpus` | frozen 1.0.0 (digest `69d6e2a6…`) | 102 | 47 | 41 |
| `bazi_corpus` | candidate 0.1.0 | 40 | 67 | 14 |

Ziwei 类型覆盖: nodes wuxing(5)/main_star(14)/palace(12)/ten_god(10)/
heavenly_stem(10)/earthly_branch(12)/auxiliary_star(12)/shen_sha(27);
relations sheng(5)/ke(5)/he(10)/chong(3)/xing(8)/hai(6)/shuyu(5)/yinyong(5)。

BaZi 类型覆盖: nodes wuxing(6: 木火土金水 + 旺衰)/ten_god(10)/
heavenly_stem(11: 十干 + 日主)/earthly_branch(13: 十二支 + 月令);
relations 五行生克(10, sheng/ke)、天干五合(5, he)、地支六合(6, he)、
六冲(6, chong)、三合(8, he)、三会(8, he)、刑(12, xing, 含自刑 4)、
六害(6, hai)、六破(6, duiying + `relation_subtype=po`, 见 §7 GAP)。

> 数量以 JSON 产物为准；node_type / relation_type / ref_type 具体枚举以
> 冻结 KB-002 / KB-007 / KB-011 & `reference/knowledge.py` 为准（上表为语义概览）。
> BaZi 节点 slug 带 `bazi_` 域前缀，ID 形式仍为 KB-001 的 `kn:<type>:<slug>`，
> 以与 Ziwei 冻结语料在**同一检索库**中保持 ID 唯一（`validate.py` 跨域校验）。

## 4. 运行

```bash
uv run python knowledge/pipeline.py            # 生成全部域 corpus + sha256
uv run python knowledge/pipeline.py bazi       # 仅生成 BaZi corpus
uv run python knowledge/validate.py            # 多域校验（PASS/FAIL 报告）
uv run pytest tests/test_knowledge_pipeline.py tests/test_bazi_knowledge_corpus.py -q
```

Pipeline 确定性要求（硬性）：无时钟/随机/网络；`sort_keys=True`；
来源 digest（SHA-256）嵌入 corpus metadata 用于版本追踪。

## 5. 添加新来源 / 节点

1. `sources/<domain>/source_XX.yaml` 登记来源元数据（title/author/school/url）
2. `corpus/<domain>/nodes|relations|references/*.yaml` 追加条目
   （顶层 `nodes:`/`relations:`/`references:` 列表；字段按 reference/knowledge.py）
3. 重跑 `pipeline.py` + `validate.py` + 回归测试
4. 保持 `provenance`（source.text）非空；id 唯一（含跨域）；relation 端点必须存在
5. 新增语料域: 在 `pipeline.py::DOMAINS`、`validate.py::DOMAINS` 与
   `src/openmetaphysics/rag/corpus.py::DOMAIN_CORPUS_FILES` 登记（复用同一
   Pipeline / 校验器 / Retriever，不新建第二套架构）

## 6. 边界

- ❌ 语料不参与 Ziwei/BaZi/Qimen/Liuyao 计算（只读引用层）
- ❌ 不引入 LLM/RAG 重写/embedding/向量库/外部检索服务到 Pipeline
- ❌ 不修改冻结规范（KB-001~020）；Schema 变更须 ACP/门控
- ❌ 不生产无 Tier 1 来源的节点/关系（Gate C 证据规则）
- ❌ 不修改已冻结的 Ziwei 语料（P2.1 未改动 `ziwei_corpus.json` 一个字节）

## 7. 已知语料缺口（P2.1 记录）

| 缺口 | 说明 | 处置 |
|------|------|------|
| 破（相破）无 relation_type | 冻结 KB-007 的 15 类中没有 `po` | 以中性 `duiying` 承载 + `relation_subtype=po` + evidence 保留规范名；未修改冻结契约，记为待裁定 |
| 日主/月令 无专用 node_type | 冻结 KB-002 的 20 类无「命局结构位概念」 | 分别以 `heavenly_stem` / `earthly_branch` 收录（日主即日干、月令即月支），记为 schema 缺口 |
| 章节级逐字核验范围有限 | 仅 三命通会 卷二·论十干化气/论三刑/论六害 与 渊海子平 论大运/论命细法 为已核验章节 | 其余条目为书级来源归属，不引用未核验原文；待后续 Evidence Review |
| 默认 k=3 检索排序 | 确定性字符重叠评分偏好覆盖面广的神煞长文（Phase C 已记录） | BaZi 专项查询命中 BaZi 语料 top-1/3；自动派生查询下 BaZi 语料于 k≥9 进入（测试已锁定实测值） |
| 未覆盖范畴 | 格局/用神/大运/流年/神煞等 BaZi 细目、藏干独立节点 | 后续 Knowledge Sprint（本轮不做完整体命理百科） |
