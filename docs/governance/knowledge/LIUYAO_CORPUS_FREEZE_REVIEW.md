# Liuyao Corpus Freeze Review（六爻语料冻结审查）

> **Status**: **PASS / FROZEN**（2026-10-24 人工批准“只冻结 Liuyao”；已实施）
> **Date**: 2026-10-24
> **Domain**: Knowledge / Liuyao
> **方案**: `liuyao_corpus:0.2.0 (candidate)` → **`liuyao_corpus:1.0.0 (frozen)`**
> **冻结 digest**: `3a09a08eccd72a24363b64fa28fee4d01f80a4bfae8d4a366ae75360e2c8a53b`
> **冻结记录**: `KNOWLEDGE_PHASE_LIUYAO_CORPUS_FREEZE.md`
> **依据**: `KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md` §2 变更流程
> **输入**: `knowledge/liuyao_corpus.json`、`knowledge/corpus/liuyao/**`、
> `knowledge/sources/liuyao/source_liuyao_01.yaml`

---

## 1. 范围与来源

| 项 | 值 |
|----|-----|
| 语料 | `knowledge/liuyao_corpus.json`（61 nodes / 66 relations / 41 references） |
| 来源 | `source_liuyao_01`《增刪卜易》 |
| revision pin | 主页 revid **2572918**（2025-06-25，326152 B，sha1 ffbbd9d6…，`main_sha256 897f963b…`）+ 24 个子页 revid/SHA-256 逐页登记（`source_liuyao_01.yaml` §子页修订登记） |
| evidence_status | **`revision_pinned_verbatim_verified`**（逐章逐字核验） |
| 已核章节 | 卦象圖/八宮圖/渾天甲子/六親歌/世應/動變/用神/用神元神忌神仇神/元神忌神衰旺/五行相生·相克/月將/日辰/六神/六合/六沖/三刑/暗動/動散/卦變生克墓絕/反伏/旬空/生旺墓絕/應期總注/歸魂遊魂 + 主页卷之二第二十七~三十二章 |
| 转录异文 | 8 条逐条登记（辰在內→艮、天地觀→风地观、元武/滕蛇/靑龍、𨿽、原劍按语、反伏/伏呤、進退章标题）；语料按 engine 用名收录，引文保留原字 |

## 2. 证据审计（离线可核对项）

| 检查 | 结果 | 证据 |
|------|------|------|
| 引用条目数 | 41（classic_text 全部） | `knowledge/liuyao_corpus.json` |
| passage 策略 | 原文精确子串（仅去除维基标记/空白；`……` 连接不连续段落；异体字保留） | `corpus/liuyao/references/classics.yaml` 头注 |
| 章节登记 | 全部 source.chapter 命中 `source_liuyao_01.yaml` 已核章节 | 41/41 |
| target 完整性 | 无悬空 target（node/relation 均存在） | `validate.py` reference 目标存在性 |
| 节点来源 | 全部节点 `source.text` 非空（KB-003） | `validate.py` |
| 异文处理 | 不静默改写；引文保留原文、语料用 engine 名 | `source_liuyao_01.yaml` §转录异文登记 |

## 3. 覆盖与边界

| 项 | 值 |
|----|-----|
| node 级引用覆盖 | 38 / 61 |
| relation 级引用覆盖 | 1 / 66 |
| 未引用条目 | 仍具 node/relation 级 `source.text`/`evidence` 归属；`validate.py` 通过 |

**GAP（随冻结载入，不阻塞）**：

| GAP | 状态 | 说明 |
|-----|------|------|
| GAP-LIUYAO-01~04 | OPEN | 六亲/结构法则/元神/仇神无专用 node_type（以 ten_god/pattern/xi_shen 承载；schema 变更须 ACP） |
| GAP-LIUYAO-05 | 不生产 | 互卦无定义性原文（H5：不可核实不生产） |
| GAP-LIUYAO-06 | 延后 | 星煞章未收录（schema 归属/价值密度未定） |

**独立证据评审**：本次离线审计确认引用结构与逐字策略一致；原始抓取件在仓库外
（revision pin + SHA-256 已登记），如需第三方复核可在授权窗口内重放抓取。

## 4. 冻结门槛回执（2026-10-24）

| 检查 | 结果 |
|------|------|
| pipeline 双跑 | `liuyao_corpus.json` digest 稳定 **`52efbff5…`**（候选期基线） |
| `validate.py` | `VALIDATION PASSED`（KB-001~020） |
| 定向测试 | `tests/test_liuyao_knowledge_corpus.py` **79 passed** |
| 当前 metadata | `status: candidate`、`version: 0.2.0` |

## 5. 冻结变更与实施记录（2026-10-24）

| 步骤 | 状态 |
|------|------|
| `pipeline.py` `DOMAINS["liuyao"]` → `frozen` / `1.0.0` | DONE |
| 重生成 `liuyao_corpus.json`（metadata 变化；内容逐对象零变化） | DONE（digest `3a09a08e…`） |
| 测试常量与 status/version 断言更新 | DONE |
| `KNOWLEDGE_PHASE_LIUYAO_CORPUS_FREEZE.md` 冻结记录 | DONE |
| 状态指针（knowledge/README、CAPABILITY_STATUS、PROJECT_STATUS、项目进展梳理） | DONE |
| 门槛复跑（pipeline 双跑 / validate / 定向 + 全量 pytest / ruff） | DONE |
| H7 合并 | 待授权 |

**用户裁定**：只冻结 Liuyao；BaZi 推迟（`BAZI_CORPUS_FREEZE_READINESS.md` 选 A）。
