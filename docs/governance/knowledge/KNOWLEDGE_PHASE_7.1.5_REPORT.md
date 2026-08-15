# Knowledge Phase 7.1.5 — Evidence Supplement + Heavenly Stem Vocabulary Report

> **Sprint**: Phase 7.1.5（Gate A: GAP-10 证据审查 + Gate B: 天干词汇 + Gate C: 回归）
> **日期**: 2026-08-13
> **结果**: **+10 天干节点 + 9 刑害关系（恃势刑 3 + 六害 6）**; Corpus 63/32/10

---

## §0 前置审计（Task 0 — 7.1.4B 关系统计差异核查）

**结论: 无差异。7.1.4B 新增关系 = 5 条, 与报告一致。**

| # | relation ID | source → target | 依据 |
|---|-------------|-----------------|------|
| 1 | rel:xing:yin_si | kn:earthly_branch:yin → kn:earthly_branch:si | 渊海子平·论大运「寅刑巳」 |
| 2 | rel:xing:si_shen | kn:earthly_branch:si → kn:earthly_branch:shen | 同上「巳刑申」 |
| 3 | rel:xing:shen_yin | kn:earthly_branch:shen → kn:earthly_branch:yin | 同上「申刑寅」 |
| 4 | rel:xing:zi_mao | kn:earthly_branch:zi → kn:earthly_branch:mao | 渊海子平·论命细法「子卯相刑」 |
| 5 | rel:xing:mao_zi | kn:earthly_branch:mao → kn:earthly_branch:zi | 同上（互刑双向） |

**说明**: 「子卯相刑」为**互刑**（子刑卯 且 卯刑子）, 按古典双向语义编码为
2 条 directed 关系（报告 §3 已明确标注「子刑卯、卯刑子（2 条 directed, 互刑）」）;
故 3（寅巳申环）+ 2（子卯互刑）= **+5**, 18→23 正确。corpus JSON 逐条核对
（§上表, 5 条端点/来源全部一致）, **无需修正**。

---

## 1. Executive Summary

- **Gate A（GAP-10）**: 以《三命通会》卷二（wikisource 通行本, 新增 Tier 1
  来源）验证恃势之刑与六害——**原文逐字命中**, 生产 **9 条关系**
  （恃势刑丑戌未环 ×3 + 六害六配对 ×6）; GAP-10 → **CLOSED**。
- **Gate B（Heavenly Stem）**: 10 个天干节点生产（渊海子平 Tier 1）。
  枚举名核验: 冻结 KB-002 / reference/knowledge.py 为 **`heavenly_stem`**
  （非任务书示例的 `gans`）—— 以冻结规范为准。
- **Gate C**: 63/32/10 全量通过校验与确定性构建; 599/599; 零触碰。

## 2. Gate A — GAP-10 Evidence Review（三命通会/卷二）

### 核验记录（原文检索, wikisource 通行本）

| 候选 | 原文 | 结果 |
|------|------|------|
| 恃势之刑（丑戌未） | ✅「丑顺至戌，戌顺至未，极十数而为恃势之刑」+「丑恃旺水刑戌中之墓火；戌恃六甲之尊刑未六癸之卑；未有旺土，复恃势刑丑中之旺水」 | **生产 ×3**（丑→戌, 戌→未, 未→丑） |
| 六害（六配对） | ✅「子未相害…丑午相害…寅巳相害…卯辰相害…申亥相害…酉戌相害」（论六害章逐字全出） | **生产 ×6**（undirected 配对） |

> 佐证: 三命通会卷二 TOC 含「24论六害 / 25论三刑」; 无恩/无礼之刑亦同章
> （已由 7.1.4B 渊海子平验证 寅巳申/子卯, 双源互证）。

### 产出（9 条, 全部通过 9 项准入检查）

| ID | type | source → target | 章节 |
|----|------|-----------------|------|
| rel:xing:chou_xu | xing | 丑 → 戌 | 卷二·论三刑 |
| rel:xing:xu_wei | xing | 戌 → 未 | 卷二·论三刑 |
| rel:xing:wei_chou | xing | 未 → 丑 | 卷二·论三刑 |
| rel:hai:zi_wei / chou_wu / yin_si / mao_chen / shen_hai / you_xu | hai | 六配对 | 卷二·论六害 |

新增引用: ref:classic:sanming_shishi_xing / ref:classic:sanming_liuhai（追溯闭环）。
新来源登记: `sources/ziwei/source_03.yaml`（三命通会, Tier 1）。

## 3. Gate B — Heavenly Stem Vocabulary（10 节点）

| 干 | 五行 | 阴阳 | 干 | 五行 | 阴阳 |
|----|------|------|----|------|------|
| 甲 | 木 | 阳 | 己 | 土 | 阴 |
| 乙 | 木 | 阴 | 庚 | 金 | 阳 |
| 丙 | 火 | 阳 | 辛 | 金 | 阴 |
| 丁 | 火 | 阴 | 壬 | 水 | 阳 |
| 戊 | 土 | 阳 | 癸 | 水 | 阴 |

- ID: `kn:heavenly_stem:jia` ~ `gui`; node_type: **heavenly_stem**
  （KB-002 冻结枚举名; 非 gans）; attributes: stem_index 0..9 / element / yin_yang。
- 来源: 渊海子平·论天干地支暗藏总诀（wikisource 核验, 干诗诀/干支藏遁章节存在）。
- **不生产** 五合等天干关系（禁止越界）。

## 4. Gate C — 集成与回归

```
$ uv run python knowledge/pipeline.py
corpus written: .../knowledge/ziwei_corpus.json (63 nodes, 32 relations, 10 references)
sha256: f9be72a4...

$ uv run python knowledge/validate.py
VALIDATION PASSED: all corpus entries conform to KB-001~020
确定性: 双重运行 SHA-256 一致 ✅
pytest tests/test_knowledge_pipeline.py: 10/10 PASS（test_source_to_corpus_reproducible
  断言更新: sources 2 → >=2, 因新增 source_03）
pytest 全量: 599/599 PASS
ruff check / format --check: PASS
```

## 5. Corpus 最终统计

| 类别 | 数量 | 变化 |
|------|------|------|
| nodes | **63** | +10（heavenly_stem） |
| relations | **32** | +9（xing 3 + hai 6） |
| references | **10** | +2（三命通会 ×2） |
| sources | **3** | +1（三命通会, Tier 1） |

## 6. GAP 状态

| GAP | 状态 |
|-----|------|
| GAP-10 | **CLOSED**（三命通会原文验证, 9 条全产） |
| GAP-02 | REMAINS OPEN（未触碰） |
| GAP-09 | CLOSED（7.1.4A/B 已结） |
| GAP-01/03~08 | 未触碰（范围外） |

## 7. 零触碰验证

| 检查 | 结果 |
|------|------|
| 既有 53 节点 / 23 关系 / 8 引用 | ✅ 未修改 |
| src/ / docs/ziwei/ / KB 规范 / CAPABILITY_LIFECYCLE | ✅ 全空 |
| 新 node_type / relation_type / ref_type | ✅ 未新增 |
| LLM / RAG / 网络爬虫 | ✅ 未引入（来源核验为只读检索; 三命通会文本仅作证据核验, 未采集入库） |
| 测试变更 | ✅ 仅 source 计数断言 2→>=2（来源扩充所致, 非行为变更） |

## 8. 停止声明

**本 Sprint 停止。** 未进入 shen_sha / auxiliary_star / interpretation;
未进入天干关系扩展（五合等）; 未引入 LLM/RAG。
等待人工 Evidence Review 与授权。
