# Knowledge Phase 7.2B-R3 — 三命通會卷三 其余神煞（9 类）生产报告

> **Sprint**: Phase 7.2B-R3 · **日期**: 2026-09-16 · **分支**: `work/knowledge/phase7.2b-r3`
> **基线**: main `e5f324f`（7.2B-R2: 93/37/32）· **来源**: 《三命通會》卷三 revid 2184219
> （sha256 `2de8fc1bf46eb4ecc5436b6cece6d4a06e56330565f3aa6e4cfaa581f5b0488e`，抓取前后两次实测一致）
> **前置**: `KNOWLEDGE_PHASE_7.2B_R2_EVIDENCE_REVIEW.md`（R2 证据门复核 PASS）

---

## 1. 结果

- **+9 神煞节点**：金舆 / 三奇 / 天德 / 月德 / 太极贵人 / 学堂 / 词馆 / 德秀 / 暗金的煞；`shen_sha` 18 → **27**。
- **语料 93/37/32 → 102/37/41**（nodes/relations/references），digest `86179bb945bf09235a0f1e8f476ea71459a9377949aa1e4837feb99b8fae952a`。
- **逐字核验 9/9 passage + 9/9 key_quote PASS**；passage 由 revision-pinned 抓取件**机器切取**（逐字由构造保证），零省略号。
- `validate` **PASSED**（KB-001~020）；pytest 全绿（新增 `tests/test_knowledge_corpus_r3.py` 7 条回归）。
- **未做**（确认未越界）：关系层（D-1 未裁）、四化（GAP-14 无对应 node_type）、卷一杂曜（D-7 scope 未批）、冻结契约/向量/Reference、卷二·卷三 紫微全书。

## 2. 证据与复现

### 2.1 本轮 9 类（全部来自卷三已核章节）

| # | 节点 | 中文 | 章节 | 原文关键句（连续、无省略号） |
|---|------|------|------|------------------------------|
| 1 | `kn:shen_sha:jin_yu` | 金舆 | 论金舆 | 故金舆常居禄前二辰 |
| 2 | `kn:shen_sha:san_qi` | 三奇 | 论三奇 | 奇为贵也；奇者，异也 |
| 3 | `kn:shen_sha:tian_de` | 天德 | 论天月德 | 天德者，谓周天有三百六十五度二十五分半 |
| 4 | `kn:shen_sha:yue_de` | 月德 | 论天月德 | 故壬甲丙癸谓之月德 |
| 5 | `kn:shen_sha:tai_ji_gui_ren` | 太极贵人 | 论太极贵 | 造化始终相保，乃曰太极贵也 |
| 6 | `kn:shen_sha:xue_tang` | 学堂 | 论学堂词馆 | 长生乃学堂之正位 |
| 7 | `kn:shen_sha:ci_guan` | 词馆 | 论学堂词馆 | 临官乃词馆正位 |
| 8 | `kn:shen_sha:de_xiu` | 德秀 | 论德秀 | 德者，阴阳解凶之神；秀者，天地清秀之气 |
| 9 | `kn:shen_sha:an_jin_de_sha` | 暗金的煞 | 论暗金的煞 | 五行中惟金能煞物，故总名曰暗金的煞也 |

### 2.2 复现

```bash
# 原文（revision-pinned）
curl -sL "https://zh.wikisource.org/w/index.php?title=%E4%B8%89%E5%91%BD%E9%80%9A%E6%9C%83/%E5%8D%B7%E4%B8%89&action=raw&oldid=2184219" -o j3.txt
sha256sum j3.txt        # 2de8fc1b…488e（65356 B）
# 生成 + 校验
python knowledge/pipeline.py       # 102/37/41, digest 86179bb9…
python knowledge/validate.py       # VALIDATION PASSED
pytest -q                          # 全绿（含本 R3 回归 7 条）
```

### 2.3 结构性证据不变量

本轮新增回归 `test_r3_key_quote_is_substring_of_passage`：**每条 R3 节点的 `原文关键句` 必须是其引用 passage 的子串**
（逐字），把「关键句与引用同源」从人工核对提升为机器不变量。9/9 满足。

## 3. 边界与零触碰

- 触及文件：`knowledge/corpus/ziwei/nodes/shen_sha.yaml`（仅追加）、
  `knowledge/corpus/ziwei/references/phase_7.2b_r3.yaml`（新增）、`knowledge/ziwei_corpus.json`（生成物）、
  `tests/test_knowledge_corpus_r3.py`（新增）+ 本报告 + GAP/归档指针。
- **既有 18 个 shen_sha 节点零改动**（纯追加；唯一非追加编辑是文件头注释计数 `18 个` → `27 个`）。
- **冻结工件零触碰**：`reference/`（含 `contracts/`、`knowledge.py`）、`docs/specification/`、
  Golden Vectors、ACP 目录均无 diff。
- **未新增来源**：沿用 7.3.1 已登记并 revision-pinned 的 Tier 1《三命通會》卷三；
  未引入 Tier 2+/未知来源，未以训练知识替代原文。
- **Schema 纪律**：节点字段严格落在冻结 `KnowledgeNode`（`extra="forbid"`）内，未新增字段/枚举。

## 4. GAP 与决策点

| 项 | 变化 |
|----|------|
| GAP-05（神煞/辅星来源） | 状态列追加：7.2B-R3 再产 9 类（卷三其余神煞），shen_sha 18 → 27；限定范围=卷三已核章节 |
| GAP-14（四化无 node_type） | **维持未解决**；本轮未生产四化（H3/E7：不擅自扩 schema） |
| **D-9（新）** | `shen_sha` 达 **27**，超出 `ZIWEI_CORPUS_COVERAGE_MATRIX.md` Phase-7.1.0 规划预期 **10-20**；类型本身在 Scope 内（优先级 2），但**数量已超规划带 → 请追认 scope**（或指示停止继续扩 shen_sha） |
| D-6 / D-7 | 四化 schema / 卷一杂曜（`auxiliary_star` 12-15 是否扩）——**均未动** |
| D-1 | 关系层生产仍待裁定（15 类 relation_type 表达力），本轮未动 |
| **D-10** | 本分支 `work/knowledge/phase7.2b-r3` 的合并 / 保留 / 关闭 |

## 5. 产出物清单

| 文件 | 状态 |
|------|------|
| `knowledge/corpus/ziwei/nodes/shen_sha.yaml` | 修改（+9 节点；头注释计数同步） |
| `knowledge/corpus/ziwei/references/phase_7.2b_r3.yaml` | 新增（9 条条目级引用） |
| `knowledge/ziwei_corpus.json` | 生成物（102/37/41） |
| `tests/test_knowledge_corpus_r3.py` | 新增（7 条回归） |
| `docs/governance/knowledge/KNOWLEDGE_PHASE_7.2B_R2_EVIDENCE_REVIEW.md` | 前置（本分支前一提交） |
| `docs/governance/knowledge/KNOWLEDGE_PHASE_7.2B_R3_REPORT.md` | 新增（本文件） |
| `docs/governance/knowledge/ZIWEI_CORPUS_GAPS.md` | GAP-05 状态行更新 |
<!-- 状态指针（CAPABILITY_STATUS.md）按 E3 于合并时刷新 -->
