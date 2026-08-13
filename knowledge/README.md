# Knowledge 语料库（Knowledge Corpus）

> **阶段**: Phase 7.0 — Pipeline Validation（试点）
> **状态**: **Pipeline Validated, Corpus Partial**（Ziwei 试点）
> **规范基准**: `docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md`（KB-001~020, Frozen）+
> `docs/design/phase6/01_knowledge_layer_architecture.md`（Frozen）+
> 规范性模型 `reference/knowledge.py`
> **边界**: Knowledge 为**只读引用层**，不参与任何计算、不产生结论、
> 不修改 Evidence / Confidence（KB 契约架构边界）。

---

## 1. 范围

- **试点领域**: 仅 Ziwei（含少量跨系统 ten_god 概念节点，来源《渊海子平》）
- **试点规模**: 20 节点 + 12 关系 + 3 引用（验证 Pipeline 用，非全量语料）
- **来源**: 2 个（`sources/ziwei/source_01.yaml` 紫微斗数全书;
  `source_02.yaml` 渊海子平）—— 原始数据引用，**不包含**古籍全文

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
| nodes | 20 | wuxing(5) / main_star(5) / palace(5) / ten_god(5) |
| relations | 12 | sheng(5) / ke(5) / he(2) |
| references | 3 | classic_text / school_commentary / oral_tradition |

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
- ❌ 不铺开全领域（Phase 7.1 全量建设待授权）
