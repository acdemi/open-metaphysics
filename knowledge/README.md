# Knowledge 语料库（Knowledge Corpus）

> **阶段**: Phase 7.1.6 全量建设（Phase 7.2A Schema Gate 已通过）
> **状态**: **Pipeline Validated, Corpus Partial**（Ziwei 试点 → 扩展建设中）
> **规范基准**: `docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md`（KB-001~020, Frozen）+
> `docs/design/phase6/01_knowledge_layer_architecture.md`（Frozen）+
> 规范性模型 `reference/knowledge.py`
> **边界**: Knowledge 为**只读引用层**，不参与任何计算、不产生结论、
> 不修改 Evidence / Confidence（KB 契约架构边界）。

---

## 1. 范围

- **试点领域**: 仅 Ziwei（含少量跨系统 ten_god 概念节点，来源《渊海子平》）
- **试点到全量演进**: Phase 7.0 试点（20 节点/12 关系/3 引用，验证 Pipeline）→
  Phase 7.1.1~7.1.6 全量建设（核心词汇 → 天干/地支/关系/引用扩展）→
  当前 **63 节点 + 37 关系 + 10 引用**（`ziwei_corpus.json` 实测, sha256 9c222617）。
  治理进展见 `docs/governance/knowledge/`（Scope/Source/Admission/Build Plan/
  Coverage Matrix/Gaps 及各 Phase 报告）。Phase 7.2A Schema 门已通过
  （shen_sha / auxiliary_star 均裁定 **A 已存在**, 待 7.2B 生产授权）。
- **来源**: 3 个 Tier 1 来源（`sources/ziwei/source_01.yaml` 紫微斗数全书;
  `source_02.yaml` 渊海子平; `source_03.yaml` 三命通会）—— 原始数据引用，
  **不包含**古籍全文

## 2. 目录结构

```text
knowledge/
├── README.md                  # 本文件
├── sources/ziwei/             # 来源元数据（引用，非数据）
├── corpus/ziwei/
│   ├── nodes/                 # KnowledgeNode（wuxing/main_star/palace/ten_god）
│   ├── relations/             # KnowledgeRelation（sheng/ke/he）
│   └── references/            # KnowledgeReference（classic/school/oral）
├── pipeline.py                # 确定性合并 + 校验 + checksum
├── validate.py                # Schema 校验（KB-001~020）
└── ziwei_corpus.json          # Pipeline 输出（确定性 JSON, 勿手改）
```

## 3. 统计

| 类别 | 数量 | 类型覆盖 |
|------|------|----------|
| nodes | 63 | wuxing(5) / main_star(14) / palace(12) / ten_god(10) / heavenly_stem(10) / earthly_branch(12) |
| relations | 37 | sheng / ke / he / xing / hai / chong（含五合/三合/六害等） |
| references | 10 | classic_text / school_commentary / oral_tradition |

> 数量以 `ziwei_corpus.json` 为准（63/37/10, sha256 9c222617）；详细节点/关系/
> 引用分项见 `docs/governance/knowledge/ZIWEI_CORPUS_COVERAGE_MATRIX.md` 与
> 各 Phase 报告（7.1.1 核心词汇 / 7.1.2 关系 / 7.1.3 引用 / 7.1.4B 地支+刑 /
> 7.1.5 天干+三命刑害 / 7.1.6 五合）。**注意**：node_type 具体枚举以冻结
> KB-002 & `reference/knowledge.py::NodeType` 为准（本表为语义概览）。

## 4. 运行

```bash
uv run python knowledge/pipeline.py    # 生成 ziwei_corpus.json + sha256
uv run python knowledge/validate.py    # 校验（PASS/FAIL 报告）
uv run pytest tests/test_knowledge_pipeline.py -q
```

Pipeline 确定性要求（硬性）：无时钟/随机/网络；`sort_keys=True`；
来源 digest（SHA-256）嵌入 corpus metadata 用于版本追踪。

## 5. 添加新来源 / 节点

1. `sources/ziwei/source_XX.yaml` 登记来源元数据（title/author/school/url）
2. `corpus/ziwei/nodes/*.yaml`（或 relations/references）追加条目
   （顶层 `nodes:`/`relations:`/`references:` 列表；字段按 reference/knowledge.py）
3. 重跑 `pipeline.py` + `validate.py` + 回归测试
4. 保持 `provenance`（source.text）非空；id 唯一；relation 端点必须存在

## 6. 边界

- ❌ 语料不参与 Ziwei/Qimen/BaZi 计算（只读引用层）
- ❌ 不引入 LLM/RAG/Interpretation 到 Pipeline
- ❌ 不铺开全领域（当前仅 Ziwei；BaZi 等语料待相应 Knowledge Sprint 授权）
- ❌ 不修改冻结规范（KB-001~020）；Schema 变更须 ACP/门控（如 7.2A 式 Schema Gate）
- ❌ 不生产无 Tier 1 来源的节点/关系（Gate C 证据规则；见 Coverage Matrix / Gaps）
