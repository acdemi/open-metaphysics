# BaZi Corpus Freeze Review（八字语料冻结审查）

> **Status**: **PASS（有界）/ FROZEN**（2026-10-24 人工批准并实施）
> **Date**: 2026-10-24 · **Branch**: `work/knowledge/h6-gap-closure`
> **方案**: `bazi_corpus:0.1.0 (candidate)` → **`bazi_corpus:1.0.0 (frozen, bounded evidence)`**
> **冻结 digest**: `488ce51099c18546aa693d364954cf1adf25b5ddb29921469d1c57a9e195f4ea`
> **冻结记录**: `KNOWLEDGE_PHASE_BAZI_CORPUS_FREEZE.md`
> **输入**: `KNOWLEDGE_H6_EVIDENCE_DOSSIER.md`、`BAZI_CORPUS_FREEZE_READINESS.md`

---

## 1. 冻结证据边界

| 级别 | 数量 | 引用 |
|------|------|------|
| **A. revision-pinned 逐字核验** | **9 / 14** | wuxing_shengke、ten_god、day_master、month_order、gan_he、sanhe、xing_wuen、xing_shishi、hai |
| **B. convention-level（书级归属 + 引擎表一致性）** | 5 / 14 | wangshuai、zhi_he、chong、sanhui、po |

B 级说明（不虚构）：
- 两源已核范围内**无连续原文列表**（六合/六冲/三会/相破/旺相休囚死）；
- 均为通行子平**表格约定**，在来源中散见（如卷二「丑…见未则冲」「子…与午相冲」等）；
- 由 `reference/bazi/tables.py` 与 31 项语料测试锁定，`validate.py` 通过；
- 冻结记录将显式声明该层级，**不宣称逐字**。

## 2. 验证回执（2026-10-24）

| 检查 | 结果 |
|------|------|
| H6 抓取 | 淵海子平 / 三命通會卷二 sha256 与 pin 一致；零 retry |
| pipeline 双跑 digest | 一致 **`165047e0…`**（candidate 基线） |
| `validate.py` | `VALIDATION PASSED` |
| 定向测试 | `tests/test_bazi_knowledge_corpus.py` **31 passed** |
| 内容 | 40 nodes / 67 relations / 14 references；relation 子类型计数与章节断言通过 |

## 3. 冻结变更与实施记录（2026-10-24）

| 步骤 | 状态 |
|------|------|
| 用户批准有界冻结 | DONE |
| `pipeline.py` `DOMAINS["bazi"]` → `frozen` / `1.0.0` | DONE |
| 重生成 `bazi_corpus.json`（metadata 变化；内容零变化） | DONE（digest `488ce510…`） |
| `KNOWLEDGE_PHASE_BAZI_CORPUS_FREEZE.md` 冻结记录 | DONE |
| 测试 `BAZI_DIGEST` / status / version 断言更新 | DONE |
| 状态指针（knowledge/README、CAPABILITY_STATUS、PROJECT_STATUS、项目进展梳理） | DONE |
| 门槛复跑（pipeline 双跑 / validate / 定向 + 全量 pytest / ruff） | DONE |
| H7 合并 | 待授权 |

**批准语（已使用）**：`批准 BaZi 有界冻结 v1.0.0（接受 5 条 convention-level 边界）。`
