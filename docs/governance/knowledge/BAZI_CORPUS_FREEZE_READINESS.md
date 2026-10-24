# BaZi Corpus Freeze Readiness（八字语料冻结就绪评估）

> **Status**: **NOT READY（逐字级冻结）— 建议先行证据扩展，或由人工选择有界冻结**
> **Date**: 2026-10-24
> **Domain**: Knowledge / BaZi
> **当前**: `bazi_corpus:0.1.0 (candidate)`，40 nodes / 67 relations / 14 references
> **依据**: `KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md` §2（需逐字核验回执）

---

## 1. 来源与证据现状

| 项 | 值 |
|----|-----|
| 来源 1 | `source_bazi_01`《渊海子平》revid **2593607**（2025-08-24，173237 B，sha256 a4447be5…） |
| 来源 2 | `source_sanming_01`《三命通会》卷二 revid **2292392**；卷三 2184219 / 卷六 845352 等（`source_bazi_02.yaml`） |
| acquisition | acquired（revision-pinned 抓取件在仓库外） |
| evidence_status | **`source_level_attributed`**（书级/卷级归属；P2.1 新增条目未逐字核验） |
| verified_scope | 仅 4 个已核章节：三命通会 卷二·论十干化气 / 论三刑 / 论六害；渊海子平 论大运 |

## 2. 引用级证据分类（14 条）

| reference | 来源/章节 | 证据级别 |
|-----------|-----------|----------|
| `ref:classic:bazi_gan_he` | 三命通会 卷二·论十干化气 | **逐字核验**（Phase 7.1.6；同一证据见 Ziwei `he_wu_he.yaml`） |
| `ref:classic:bazi_xing_wuen` | 渊海子平 论大运 | **逐字核验**（同一原文见 Ziwei `xing.yaml`） |
| `ref:classic:bazi_xing_shishi` | 三命通会 卷二·论三刑 | **逐字核验** |
| `ref:classic:bazi_hai` | 三命通会 卷二·论六害 | **逐字核验** |
| `bazi_wuxing_shengke` / `bazi_wangshuai` / `bazi_ten_god` / `bazi_day_master` / `bazi_month_order` / `bazi_zhi_he` / `bazi_chong` / `bazi_sanhe` / `bazi_sanhui` / `bazi_po` | 渊海子平（部分有章节） | **摘要式归属**（非引文；`classics.yaml` 头注明示“其余为书级来源归属，不书写未核验原文”） |

**结论**：10/14 引用为摘要式说明，无法提供“revision-pinned 原文子串匹配回执”，
不满足 7.1.6 冻结流程的逐字核验要求。

## 3. 覆盖与结构

| 检查 | 结果 |
|------|------|
| node 级引用覆盖 | 4 / 40 |
| relation 级引用覆盖 | 10 / 67 |
| target 完整性 | 无悬空 target |
| 节点/关系 `source.text` | 全部非空（KB-003） |
| 结构与关系计数 | relation 子类型计数与章节断言由 31 tests 覆盖 |
| 冻结门槛回执 | pipeline 双跑 `bazi_corpus.json` digest 稳定 **`69b6edea…`**；`validate.py` PASS；`tests/test_bazi_knowledge_corpus.py` **31 passed** |

**已登记缺口（`knowledge/README.md` §7）**：破（相破）无 relation_type（以 `duiying` +
`relation_subtype=po` 承载）；日主/月令无专用 node_type；章节级逐字核验范围有限。

## 4. 选项

| 选项 | 内容 | 评价 |
|------|------|------|
| **A（推荐）** | **推迟冻结**：在 H6 授权窗口内获取 revision-pinned 原文，对 10 条摘要引用做逐字核验（并按需扩展 node/relation 引用覆盖），随后按 7.1.6 流程冻结 | 满足 H5 与 7.1.6 流程；需外网授权 |
| B | **有界冻结**：以 `source_level_attributed` 冻结 `bazi_corpus:v1.0.0`，在冻结记录中显式声明“摘要式归属、无逐字回执”、列明 4 条已核章节与全部 GAP | 可立即收口，但降低证据等级；须人工明确接受 |
| C | 维持 candidate | 不计入冻结域；继续以候选状态使用 |

## 5. 建议

选 **A**：BaZi 内容（十神/干支/合冲刑害）本身已由引擎与测试锁定，缺的是**来源逐字回执**；
完成 10 条核验即可达到与 Liuyao 同级证据，不建议为提前收口而降低 H5 标准。

若选 B，需在批准语中明确：`批准 BaZi 有界冻结 v1.0.0（接受 source_level_attributed）`。
