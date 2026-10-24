# Qimen Corpus Freeze Review（奇门语料冻结审查）

> **Status**: **PASS（有界）/ FROZEN**（2026-10-24 人工批准并实施）
> **Date**: 2026-10-24 · **Branch**: `work/knowledge/qimen-verbatim`
> **方案**: `qimen_corpus:0.1.0 (candidate)` → **`qimen_corpus:1.0.0 (frozen, bounded evidence)`**
> **冻结 digest**: `ffeb3319fcd8e8b01b1834c8b174587814cf2d4f5abd911fcaa06118f72d2032`
> **冻结记录**: `KNOWLEDGE_PHASE_QIMEN_CORPUS_FREEZE.md`
> **输入**: `KNOWLEDGE_H6_EVIDENCE_DOSSIER.md`、`source_qimen_01/02.yaml`

---

## 1. 冻结证据边界

| 级别 | 数量 | 引用 |
|------|------|------|
| **A. revision-pinned 逐字核验** | **10 / 15** | jiugong、bamen、bamen_suozhu、jiuxing_suozhu、bashen、bashen_leishen、yangdun、yindun、yanbo_yinyang、liuyi |
| **B. 书级/章节级摘要** | 5 / 15 | jiuxing、zhifu、zhishi、sanqi、xunshou_kongwang |

B 级说明（不虚构）：
- 未在抓取件中找到连续原文（或仅 TOC 出现），保留摘要并显式标注；
- 与 engine 表（PALACE/NINE_STARS/SANQI/LIUYI 等）一致性由语料测试锁定；
- 冻结记录声明 B 级**不宣称逐字**。

## 2. 验证回执（2026-10-24）

| 检查 | 结果 |
|------|------|
| H6 抓取 | 統宗 oldid 1378608（141759 B，sha256 `b4d0271d…`）；煙波 revid 1336835（5935 B，`702f6311…`）；零 retry |
| pipeline 双跑 digest | 一致 **`76e4a4d0…`**（候选基线） |
| `validate.py` | `VALIDATION PASSED` |
| 定向测试 | `tests/test_qimen_knowledge_corpus.py` **31 passed** |
| 内容 | 47 nodes / 60 relations / 15 references；A 级 10 条逐字 |

## 3. 冻结变更与实施记录（2026-10-24）

| 步骤 | 状态 |
|------|------|
| 用户批准有界冻结 | DONE |
| `pipeline.py` `DOMAINS["qimen"]` → `frozen` / `1.0.0` | DONE |
| 重生成 `qimen_corpus.json`（metadata 变化；内容零变化） | DONE（digest `ffeb3319…`） |
| `KNOWLEDGE_PHASE_QIMEN_CORPUS_FREEZE.md` 冻结记录 | DONE |
| 测试 `QIMEN_DIGEST` / status / version 断言更新 | DONE |
| 状态指针（knowledge/README、CAPABILITY_STATUS、PROJECT_STATUS、项目进展梳理） | DONE |
| 门槛复跑（pipeline 双跑 / validate / 定向 + 全量 pytest / ruff） | DONE |
| H7 合并 | DONE（`09fecd4`，2026-10-24） |

**批准语（已使用）**：`批准 Qimen 有界冻结 v1.0.0（接受 5 条摘要边界）。`
