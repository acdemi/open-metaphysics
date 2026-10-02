# Knowledge Phase 7.1.3 Completion — yinyong(5) + shuyu(5) 关系补齐报告

> **Sprint**: 关系层补齐（Phase 7.1.3 规划项收口） · **日期**: 2026-09-16
> **分支**: `work/knowledge/phase7.2b-r3` · **基线**: 本分支 `225707d`（语料 102/37/41）
> **范围依据**: `ZIWEI_CORPUS_BUILD_PLAN.md` 7.1.3「yinyong(5) + shuyu(5) 随引用建立」
> 与 `ZIWEI_CORPUS_COVERAGE_MATRIX.md` §2（两类长期标「需新增 5」，实际生产 0）
> **性质**: **补齐既有规划**，非扩范围 —— 未新增 node_type / relation_type / 来源 / 节点

---

## 1. 结果

- **+10 关系**：`yinyong` 5（节点间引用）+ `shuyu` 5（星曜属五行）。
- 语料 **102/37/41 → 102/47/41**（nodes/relations/references），
  digest `bac1b1ef0db1bb95655e96decba57ceebdec11511a69f0ed63f998f2f3d14707`。
- **Coverage Matrix §2 关系矩阵至此无未闭合项**（sheng/ke/he/chong/xing/hai/yinyong/shuyu 全部 ✅）。
- 端到端验证：`validate` **PASSED**（KB-001~020，含端点存在性/唯一性）；pytest 全绿
  （新增 `tests/test_knowledge_corpus_relations.py` 6 条回归）。
- **零节点生产、零新来源、零 schema 变更、零冻结工件触碰。**

## 2. 证据与复现

### 2.1 shuyu（星曜属五行）—— 来源《紫微斗數全書》卷二（revid 1963110, sha256 `1e255c6a…`）

依据 **卷二·安身命例「北斗化吉凶并分属五行」** 星曜五行名录（逐字引文见每条 `evidence.description`）：

| 关系 | 方向 | 逐字引文 |
|------|------|----------|
| `rel:shuyu:ziwei_tu` | 紫微 → 土 | 紫微属土 |
| `rel:shuyu:tianji_mu` | 天机 → 木 | 天机属木 |
| `rel:shuyu:taiyang_huo` | 太阳 → 火 | 太阳属火 |
| `rel:shuyu:wuqu_jin` | 武曲 → 金 | 武曲属金 |
| `rel:shuyu:taiyin_shui` | 太阴 → 水 | 太阴属水 |

**选取规则（写入 `shuyu.yaml` 头注）**：只取**单一五行、且无第二来源冲突**的十四主星条目。
擎羊/陀罗/火星/铃星 在卷一与卷二之间**五行归属不一致**，按 Admission Policy §3
「多源并列、不静默合并」本轮**不生产**，登记为 **GAP-15**（决策点 D-11）。

### 2.2 yinyong（节点间引用）—— 来源《三命通會》卷三（revid 2184219, sha256 `2de8fc1b…`）

| 关系 | 方向 | 逐字引文 |
|------|------|----------|
| `rel:yinyong:zai_sha_jiang_xing` | 灾煞 → 将星 | 常居劫煞之前，冲破将星，谓之灾煞 |
| `rel:yinyong:jin_yu_lu_shen` | 金舆 → 禄神 | 故金舆常居禄前二辰 |
| `rel:yinyong:yang_ren_lu_shen` | 羊刃 → 禄神 | 故羊刃常居禄前一辰 |
| `rel:yinyong:xue_tang_yi_ma` | 学堂 → 驿马 | 学堂如更朝驿马，位极勋高压天下 |
| `rel:yinyong:san_qi_tian_yi_gui_ren` | 三奇 → 天乙贵人 | 带天乙贵者，勋业超群 |

方向语义：**引用方 → 被引用方**（directed）。

### 2.3 复现

```bash
# revision-pinned 原文（sha256 与登记值比对）
curl -sL "https://zh.wikisource.org/w/index.php?title=%E7%B4%AB%E5%BE%AE%E6%96%97%E6%95%B8%E5%85%A8%E6%9B%B8/%E5%8D%B7%E4%BA%8C&action=raw&oldid=1963110" -o zw2.txt
curl -sL "https://zh.wikisource.org/w/index.php?title=%E4%B8%89%E5%91%BD%E9%80%9A%E6%9C%83/%E5%8D%B7%E4%B8%89&action=raw&oldid=2184219" -o sm3.txt
sha256sum zw2.txt sm3.txt   # 1e255c6a… / 2de8fc1b…
python knowledge/pipeline.py     # 102/47/41, digest bac1b1ef…
python knowledge/validate.py     # VALIDATION PASSED
pytest -q                        # 全绿（含本批 6 条回归）
```

**逐字回执**：10/10 关系的「…」引文在对应 pinned 原文中命中（去空白后子串匹配），
端点 10/10 存在于语料节点集。

## 3. 边界与零触碰

- 触及文件：`knowledge/corpus/ziwei/relations/shuyu.yaml`（新增）、
  `knowledge/corpus/ziwei/relations/yinyong.yaml`（新增）、`knowledge/ziwei_corpus.json`（生成物）、
  `tests/test_knowledge_corpus_relations.py`（新增）、本报告、Coverage Matrix §2/§4 状态刷新、GAPS（GAP-15）。
- **未新增任何节点**；既有 102 节点零改动。
- **未新增来源**：shuyu 用已登记 `source_ziwei_01`（卷二 pin 原已在 `source_01.yaml` 登记）；
  yinyong 用 7.3.1 已 pin 的《三命通會》卷三。
- **冻结工件零触碰**：`reference/`（含 `contracts/`、`knowledge.py`）、`docs/specification/`、
  Golden Vectors、ACP 目录均无 diff；`relation_type` 取自冻结 KB-007 既有枚举，**未扩枚举**。
- 未合并 main、未推送。

## 4. GAP 与决策点

| 项 | 变化 |
|----|------|
| **GAP-15（新）** | 星曜五行多源冲突（擎羊/陀罗/火星/铃星: 卷一 vs 卷二 归属不一致）→ 该批 `shuyu` **不生产**，登记 OPEN |
| Coverage Matrix §2 | `yinyong` 0→**5 ✅**、`shuyu` 0→**5 ✅**，需新增 5→0；§2 关系矩阵**无未闭合项** |
| GAP-02（school_commentary 1） | 维持 OPEN（无可核实来源；**唯一剩余引用缺口**） |
| **D-11（新）** | GAP-15 处置口径：按流派分层并列生产，或维持不生产 |
| D-9 / D-7 / D-6 / D-1 / D-10 | 均**未动**（shen_sha 超带追认 / auxiliary_star 扩范围 / 四化 schema / 关系层表达力 / 分支合并） |

## 5. 产出物清单

| 文件 | 状态 |
|------|------|
| `knowledge/corpus/ziwei/relations/shuyu.yaml` | 新增（5 条） |
| `knowledge/corpus/ziwei/relations/yinyong.yaml` | 新增（5 条） |
| `knowledge/ziwei_corpus.json` | 生成物（102/47/41） |
| `tests/test_knowledge_corpus_relations.py` | 新增（6 条回归） |
| `docs/governance/knowledge/ZIWEI_CORPUS_COVERAGE_MATRIX.md` | §2/§4 覆盖状态刷新 |
| `docs/governance/knowledge/ZIWEI_CORPUS_GAPS.md` | 新增 GAP-15 |
| `docs/governance/knowledge/KNOWLEDGE_PHASE_7.1.3_COMPLETION_REPORT.md` | 新增（本文件） |
<!-- CAPABILITY_STATUS.md 按 E3 于合并时刷新 -->
