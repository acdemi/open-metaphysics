# Knowledge Phase 7.2B-R — shen_sha / auxiliary_star 证据驱动生产报告

> **Sprint**: Phase 7.2B-R（重跑） · **日期**: 2026-09-15 · **分支**: `work/knowledge/phase7.2b-rerun`（基线 main `bdc5c10`）
> **前置**: Phase 7.3.1（Tier 1 来源 revision-pinned 获取 + 逐字核验 36/36 断言 PASS）
> **结论**: 首批生产 **23 节点 + 12 引用**（auxiliary_star 12 / shen_sha 11）；语料 63/37/10 → **86/37/22**；测试 **599/599 通过**

---

## 1. 结果

- **做了什么**：依据 7.3.1 逐字证据生产
  `knowledge/corpus/ziwei/nodes/auxiliary_star.yaml`（12 节点：文昌/文曲/左辅/右弼/天魁/天钺/禄存/天马/擎羊/陀罗/火星/铃星）
  与 `nodes/shen_sha.yaml`（11 节点：羊刃/禄神/驿马/天乙贵人/劫煞/亡神/将星/华盖/咸池/孤辰/寡宿），
  并新增 `references/phase_7.2b.yaml`（12 条 `classic_text` 条目级引用，含 羊刃 的三命通會卷三/卷六/淵海子平**跨源对照**）。
- **没做什么**：**未生产任何关系**（37 条不变，理由见 §4 D-1）；未修改契约/Schema/Reference/Golden Vector/ACP；
  未改动既有 63 节点的任何语义。
- **关键数字**：

| 指标 | 之前 | 之后 |
|------|------|------|
| 节点 | 63 | **86**（+23） |
| 关系 | 37 | 37（未变） |
| 引用 | 10 | **22**（+12） |
| 语料 sha256 | 9c222617 → b1b8f90a | **9a213728238428fd02e11c58007e4891d4d0b287d21d48024d50cbbd65714156** |
| 测试 | 599 passed | **599 passed**（exit 0） |
| 证据核验 | — | **23/23 PASS**（逐节点原文关键句机器核验） |

## 2. 证据与复现

每个新节点的 `attributes.原文关键句` 均为**逐字原文**，并由机器核验脚本按
`source.url` 定位 7.3.1 的 revision-pinned 抓取件做去空白子串匹配：

~~~text
pass 23  fail 0  total 23      # 23/23 逐字命中（首轮 22/23，kn:shen_sha:jie_sha
                               #  因属性里写了省略号「……」而 FAIL → 改为原文连续句后 PASS）
~~~

复现：

~~~bash
python knowledge/pipeline.py     # corpus written: 86 nodes, 37 relations, 22 references
python knowledge/validate.py     # VALIDATION PASSED: all corpus entries conform to KB-001~020
pytest -q                        # 599 passed（exit 0）
# 证据核验（一次性临时脚本，不入仓）：读 7.3.1 抓取件 + source.url 映射 + 去空白子串匹配
~~~

来源 pin（与 7.3.1 dossier 一致）：紫微斗數全書/卷一 revid 7913704；三命通會 卷三 2184219 / 卷二 2292392 / 卷六 845352；
淵海子平 2593607。转录讹误在引用 passage 内**就地标注**（V-1 巳/己、V-3 已/巳、V-4 幸/辛），未静默改写。

## 3. 边界与零触碰

- 变更文件：`nodes/auxiliary_star.yaml`、`nodes/shen_sha.yaml`、`references/phase_7.2b.yaml`（新增）、
  `knowledge/ziwei_corpus.json`（pipeline 重生成）、状态文档（指针）。
- 未触碰：`reference/`、`src/`、`docs/specification/`、`reference/contracts/`、Golden Vectors、
  `docs/governance/ACP/`、既有 63 节点的 YAML。
- 跨系统处置：神煞属子平体系，`systems: [bazi]` 并在 Ziwei 语料中作共享概念保留（GAP-04 同类惯例）；
  紫微的 天马（`kn:auxiliary_star:tian_ma`）与子平的 驿马（`kn:shen_sha:yi_ma`）**不合并**，各自标注。
- 原文出处精确到问答条目/章节（如 `卷一·諸星問答論·問文昌星所主若何`、`卷三·论羊刃`），
  `interpretation` 以简体书写并保留原文「不可核实即不生产」的边界（未引入任何原文之外的起例/口诀）。

## 4. GAP 与决策点

| GAP | 变更 |
|-----|------|
| GAP-12（auxiliary_star 主源不可达） | 🟢 **CLOSED**（限定范围：卷一·諸星問答論 12 星已生产并逐字可回溯） |
| GAP-13（shen_sha 逐字核验未达成） | 🟢 **CLOSED**（限定范围：11 神煞已生产，逐字断言 PASS） |
| GAP-05（神煞/辅星无单一权威来源） | 🟢 **CLOSED（证据与生产侧）**——来源策略 + 逐字证据 + 首批生产均落地；流派差异以 `schools` 显式保留（羊刃 子平 阴干无刃说） |
| GAP-01（紫微斗數全集） | 🟡 未变（D-5） |

**决策点**：

- **D-1 关系层（本次刻意未做）**：神煞/辅星与干支/主星的关联需要 `relation_type` 语义匹配；
  冻结界面的 15 类（sheng/ke/chong/xing/he/hai/fuzhu/zhiyue/duiying/…）能否无损表达
  「羊刃=禄前一辰」「驿马=三合绝处」这类**定位关系**需人工裁定；若无损方案缺失则应记 GAP（不得强行套用）。
- **D-2 契约示例层 → 无需 ACP（本 Sprint 实测结论）**：冻结的 `reference/contracts/knowledge_contract.json` 中
  `golden_examples` 为 **query 级**示例（find_by_id 等），并非按 node_type 提供示例；
  `node_types` 已包含 `auxiliary_star` 与 `shen_sha`。故 7.2B §12「生产 auxiliary_star 需补契约示例层 → 走 ACP」
  的**前提不成立**，本次生产**未触发 ACP**（仅此结论，如需修改契约仍需 ACP）。
- **D-3** Tier 1 抓取快照是否入库；**D-4** 天乙贵人韵文体口诀缺位（引用 passage 已标注 L-3）；
  **D-5** GAP-01 是否推进；**D-6** 本分支合并（用户已预授权）。
- 未决的**流派归属**（如 咸池/桃花 的现代命理扩张解释）未纳入，保持 Tier 1 原文口径。

## 5. 产出物清单

| 文件 | 状态 |
|------|------|
| `knowledge/corpus/ziwei/nodes/auxiliary_star.yaml` | 新增（12 节点） |
| `knowledge/corpus/ziwei/nodes/shen_sha.yaml` | 新增（11 节点） |
| `knowledge/corpus/ziwei/references/phase_7.2b.yaml` | 新增（12 引用） |
| `knowledge/ziwei_corpus.json` | 重生成（86/37/22, sha 9a213728） |
| `docs/governance/CAPABILITY_STATUS.md` / `docs/PROJECT_STATUS.md` | 指针更新（按 E3） |
| `docs/governance/knowledge/ZIWEI_CORPUS_GAPS.md` | GAP-05/12/13 状态更新 |
| `context/归档.md` | 归档（≤15 行，按 E3） |

> 本 Sprint 按**精简后规则**执行：1 份报告（本节即全部）+ 1 个能力指针 + 轻量归档；
> 未产出成功标准清单/执行记录/多份同步状态文档。
