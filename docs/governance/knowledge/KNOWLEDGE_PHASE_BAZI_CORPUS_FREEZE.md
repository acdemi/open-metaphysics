# BaZi Corpus Freeze v1.0.0（有界冻结记录·已批准）

> **日期**: 2026-10-24 · **分支**: `work/knowledge/h6-gap-closure`
> **批准**: 用户 2026-10-24 批准有界冻结（接受 5 条 convention-level 边界）
> **评审**: `BAZI_CORPUS_FREEZE_REVIEW.md` · **证据**: `KNOWLEDGE_H6_EVIDENCE_DOSSIER.md`

---

## 1. 冻结声明

| 项 | 值 |
|----|----|
| 冻结产物 | `knowledge/bazi_corpus.json` |
| 版本 | **`bazi_corpus:v1.0.0`（bounded evidence）** |
| digest (SHA-256) | `488ce51099c18546aa693d364954cf1adf25b5ddb29921469d1c57a9e195f4ea` |
| 计数 | **40 nodes / 67 relations / 14 references** |
| 规范输入 | `knowledge/corpus/bazi/**` |
| 来源登记 | `sources/bazi/source_bazi_01.yaml`（淵海子平 revid 2593607）、`source_bazi_02.yaml`（三命通會 卷二 revid 2292392） |
| 生成器 | `knowledge/pipeline.py`（确定性；LF 输出） |
| 生效 | 本记录提交后 |

## 2. 证据边界（冻结基线）

| 级别 | 数量 | 引用 |
|------|------|------|
| A. revision-pinned 逐字核验 | 9/14 | wuxing_shengke、ten_god、day_master、month_order、gan_he、sanhe、xing_wuen、xing_shishi、hai |
| B. convention-level（书级归属 + 引擎表一致性） | 5/14 | wangshuai、zhi_he、chong、sanhui、po |

B 级为通行子平表格约定，两层 Tier-1 来源无连续原文列表；由 `reference/bazi/tables.py`
与 31 项语料测试锁定。**冻结记录明确声明：B 级不宣称逐字。**

## 3. 变更流程

任何 node/relation/reference 的新增、修改、删除须走 corpus 级审查：
提案 → 证据（逐字或 convention-level 边界说明）→ pipeline/validate/双跑/回归 → 人工批准
→ 版本递增 + 本记录更新。

## 4. 验证回执（2026-10-24）

| 检查 | 结果 |
|------|------|
| pipeline 双跑 digest | 一致 **`488ce510…`** |
| `validate.py` | `VALIDATION PASSED` |
| 定向测试 | `tests/test_bazi_knowledge_corpus.py` **31 passed** |
| Qimen/Liuyao 影响 | 未触碰；Qimen 维持 candidate |
