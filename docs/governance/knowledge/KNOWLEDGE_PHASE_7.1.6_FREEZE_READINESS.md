# Knowledge Phase 7.1.6 — Corpus Freeze Readiness（冻结就绪审计，待人工批准）

> **Sprint**: Phase 7.1.6 Corpus Freeze（Build Plan 收口步骤） · **日期**: 2026-09-16
> **分支**: `work/knowledge/phase7.2b-r3` @ `e833d4c` · **基线**: main `e5f324f`
> **性质**: **就绪审计 + 冻结候选（CANDIDATE）** —— 本文件**不宣告冻结**。
> `CAPABILITY_STATUS.md` 的 Corpus 状态仍为 `PARTIAL`，改为 `FROZEN-v1.0.0` 须人工批准。

---

## 1. 结论

```text
FREEZE-READY（技术上全部就绪，零阻塞）
待人工批准两项: ① D-9 shen_sha 超规划带追认  ② 冻结本身
```

Phase 7.1.6 是 `ZIWEI_CORPUS_BUILD_PLAN.md` 执行序列的最后一步
（7.1.1 → … → 7.1.5 → **7.1.6 Corpus Freeze（v1.0.0）**），也是 Ziwei 范围内
**唯一仍未执行的规划项**。Ziwei 计算域本身无遗留（`ZIWEI_FREEZE_REVIEW.md`：
「未遗留 DEFERRED 项」；唯一「未实现」为 ZW-017 冻结边界，变更须 ACP）。

## 2. 冻结候选（Freeze Candidate）

### 2.1 对象

| 项 | 值 |
|----|----|
| 规范产物 | `knowledge/ziwei_corpus.json`（生成物，唯一对外语料） |
| 规范输入 | `knowledge/corpus/ziwei/{nodes,relations,references}/*.yaml` |
| digest（就绪审计时） | `bac1b1ef0db1bb95655e96decba57ceebdec11511a69f0ed63f998f2f3d14707` → 冻结时因 metadata 规范化变为 `69d6e2a6…` → **2026-10-24 经 `ACP-KNOWLEDGE-001` EOL 勘误为 `93dba067…`**（节点/关系/引用内容零变化; 见 `KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md` §1.1/§3） |
| 计数 | **102 nodes / 47 relations / 41 references** |
| 版本建议 | `ziwei_corpus:v1.0.0` |

### 2.2 覆盖闭合度

| 类别 | 分布 |
|------|------|
| node_type | wuxing 5 / main_star 14 / palace 12 / ten_god 10 / heavenly_stem 10 / earthly_branch 12 / auxiliary_star 12 / shen_sha 27 |
| relation_type | sheng 5 / ke 5 / he 10 / chong 3 / xing 8 / hai 6 / **shuyu 5** / **yinyong 5** |
| ref_type | classic_text 37 / school_commentary 1⚠️ / modern_interpretation 1 / oral_tradition 2 |

`ZIWEI_CORPUS_COVERAGE_MATRIX.md` §1 节点矩阵与 §2 关系矩阵**均无未闭合项**；
§3 引用矩阵仅剩 `school_commentary` 1 条（GAP-02，无可核实来源）。

### 2.3 来源可回溯性

全部证据来自**已登记且 revision-pinned** 的 Tier 1 来源；本分支逐字核验覆盖：
《紫微斗數全書》卷一 revid 7913704 / 卷二 revid 1963110 / 卷三 revid 2268626（sha256 已实测登记）、
《三命通會》卷二 revid 2292392 / 卷三 revid 2184219（sha256 `2de8fc1b…` 逐字节复现）。

## 3. 就绪核验（全部实测）

| 检查 | 命令/方式 | 结果 |
|------|-----------|------|
| 计数与 digest | `python knowledge/pipeline.py` | 102/47/41，`bac1b1ef…` |
| 确定性（KB-020） | pipeline 双跑 | 两次 digest 一致 ✅ |
| 文件字节 = 登记值 | `Get-FileHash ziwei_corpus.json` | `bac1b1ef…` ✅（DEF-02 修复后一致） |
| KB 规范 | `python knowledge/validate.py` | `VALIDATION PASSED`（KB-001~020 + 端点/唯一性） |
| 回归测试 | `pytest -q`（junit XML） | **618 / 618**，failures=0 errors=0 |
| 冻结工件漂移 | `git diff main...HEAD -- reference docs/specification docs/design docs/engineering` | **空** ✅ |
| 工作树 | `git status` | 干净 ✅ |

本分支累计变更 = 14 文件（全部位于 `knowledge/`、`tests/`、`docs/governance/knowledge/`、`context/`），
无跨域写入、无冻结工件触碰、无 ACP 触发。

## 4. 冻结时须一并载入的登记项（不得静默丢弃）

| 项 | 状态 | 说明 |
|----|------|------|
| GAP-02 | OPEN | `school_commentary` 尚缺 1 条（中州派无可核实来源；现有 1 条标 `not_authoritative`） |
| GAP-14 | OPEN | 四化无对应 `node_type`（schema gap，不擅自扩） |
| GAP-15 | OPEN | 星曜五行多源冲突（擎羊/陀罗/火星/铃星：卷一 vs 卷二） |
| GAP-01 | SOURCE_DISCOVERED | 《紫微斗數全集》未获取（第二权威缺位） |
| GAP-03/04/06/07/08 | 记录 | Schema 表达缺口 / 跨系统归属 / pattern / 断事类 / 用神类（范围外） |
| **D-9** | **待追认** | `shen_sha` 27 **超出** Phase-7.1.0 规划带 10-20 |
| D-11 | 待裁 | GAP-15 处置口径（多源并列 vs 不生产） |
| D-6 / D-7 | 待裁 | 四化 schema / `auxiliary_star` 是否扩至卷一杂曜 |

## 5. 建议与所需批准

**建议顺序**：先追认 **D-9**（否则会把一个未追认的超带状态冻进 v1.0.0），再执行冻结。

冻结一旦批准，将执行（**批准前不做**）：

1. `CAPABILITY_STATUS.md`：Knowledge Corpus `PARTIAL` → **`FROZEN-v1.0.0`**（1~3 行，E3 单一指针）；
2. 新增 Freeze 记录（digest + 计数 + 冻结范围 + 变更流程引用）；
3. 声明变更流程：此后任何 `nodes/relations/references` 变更须走 **Corpus 级审查**（对齐
   `RUNTIME_CONTRACT.md` 的合并门精神），而非普通 Sprint 追加。

**需人工裁定（D-12）**：

- **A（推荐）**：追认 D-9 → 冻结 `ziwei_corpus:v1.0.0`（open gaps 随冻结载入 §4）。
- **B**：不追认 D-9，但接受「超带」为既成事实并冻结（冻结记录显式标注超带）。
- **C**：暂不冻结，继续维持 `PARTIAL`。

## 6. 产出物

| 文件 | 状态 |
|------|------|
| `docs/governance/knowledge/KNOWLEDGE_PHASE_7.1.6_FREEZE_READINESS.md` | 新增（本文件，CANDIDATE） |
<!-- 冻结记录 / CAPABILITY_STATUS 指针：仅在 D-12 批准后产出 -->
