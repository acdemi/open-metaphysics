# Knowledge Phase 7.2B — shen_sha / auxiliary_star Evidence-Driven Production Report

> **Sprint**: Phase 7.2B — 受控语料扩展 Sprint（证据驱动，不预设数量）
> **日期**: 2026-08-17
> **分支**: `work/knowledge/phase7.2b-shensha-auxstar-production`（基于 7.2A 分支累积）
> **结果**: **0 节点 / 0 关系 / 0 引用生产** —— Tier 1 原文不可达，按"不可核实→不生产、不虚构"原则拒绝；Corpus 维持 63/37/10

---

## 1. Executive Summary

Phase 7.2B 在 7.2A Schema 放行后进入受控生产。按硬约束"Tier 1 优先 / 不可核实→不生
产 / 不虚构 / 不以网络常见度为据"，对 shen_sha 与 auxiliary_star **独立**逐候选核验：

- **shen_sha → 0 生产**：Tier 1 来源（《三命通会》source_sanming_01 /《渊海子平》
  source_bazi_01）已登记且 7.1.5 曾成功核验卷二，但本会话内对 wikisource 的 webfetch
  2 次失败（timeout / transport error），神煞章节 verbatim 原文未能获取；拒绝以训练
  知识替代原文 → GAP-13。
- **auxiliary_star → 0 生产**：Tier 1 主源《紫微斗数全书》source_01.yaml 明记
  「原文不在仓库内，url=null」；《紫微斗数全集》GAP-01 待获取 → 原文根本不可达 →
  GAP-12。

**这是证据驱动原则下的合规结果**：prompt 明确"首要目标：高置信度、可追溯……而非
尽可能多"与"不可核实→不生产，记录为 GAP，不虚构"。零生产 + GAP 登记 + 人工决策点
是 prompt 工作流（"完成所有任务后 STOP，等待人工 Evidence Review 与授权"）的预期形态。

## 2. Task 0 — 来源确认 / Evidence Policy

### 来源策略（已定义，GAP-05 来源部分 CLOSED）

| 来源等级 | 使用策略 | 说明 |
|----------|----------|------|
| Tier 1（经典原文） | 可直接生产 | 全书/全集/三命通会/渊海子平等，需 verbatim 原文片段 + 出处 |
| Tier 2+（流派注释/现代整理） | 多源交叉验证后生产 | ≥2 独立来源 + 标记 SchoolView |
| 不可核实 | 不生产 | 记 GAP，不虚构 |

### SchoolView 策略

- 同概念不同来源不同定义 → `schools` 列表（`SchoolView{school, interpretation, source, weight}`）显式保留差异；
- 不静默合并，不选"主流"为默认；冻结规范已有定义 → 以冻结规范为准，来源作 provenance 补充。

### 实际来源可达性核验（7.2B 会话）

| source_id | title | 登记状态 | 原文可达性（7.2B） |
|-----------|-------|----------|--------------------|
| source_ziwei_01 | 紫微斗数全书 | 已登记 | ❌ 原文未入库（source_01.yaml: url=null，原文不在仓库内） |
| source_ziwei_02 | 紫微斗数全集 | GAP-01 待获取 | ❌ 扫描本质量参差，未获取 |
| source_bazi_01 | 渊海子平 | 已登记（wikisource） | ❌ webfetch 失败（本会话） |
| source_sanming_01 | 三命通会 | 已登记（wikisource，7.1.5 曾成功） | ❌ webfetch 2 次失败（timeout / transport error） |

> 结论：四项 Tier 1 来源在 7.2B 会话内**无一可逐字核验**。非来源不存在，而是原文未入库
> + 本会话 webfetch 不可达。7.1.5 成功核验三命通会卷二证明来源本身有效，阻塞在"原文
> 入库 / webfetch 可用"。

## 3. shen_sha 节点清单（逐候选，Task 1）

**裁定：0 生产**。候选起点（禄存/擎羊/陀罗/火星/铃星/天魁/天钺/文昌/文曲/左辅/右弼/
羊刃/驿马/亡神/劫煞/天乙贵人/禄神/华盖…）仅作检索起点，**不预设数量**。

| 候选 | 检索来源 | 原文核验 | 结果 |
|------|----------|----------|------|
| 全部候选 | 三命通会 / 渊海子平（wikisource） | ❌ webfetch 2 次失败，未获 verbatim 原文 | **不生产** |

**拒绝理由**（对应 7 条红线 #1/#5）：
- 红线 #1：不以"网上常见"纳入 → 神煞定义若来自训练知识/网络常见度，一律拒绝。
- 红线 #5：不设"至少 N 个"KPI → 证据为 0 则生产 0。
- 不虚构：无 verbatim 原文片段（含出处）即不填 `interpretation` / `source.passage`。

> 注：`reference/examples/knowledge/nodes.yaml` 含 golden 示例 `kn:shen_sha:yang_ren`
> （source: 三命通会·羊刃）。该示例属 Reference Runtime golden 产物，**不可作为绕过
> 独立核验的捷径**直接提升至生产 Corpus（亦不应复制 reference/ 至 knowledge/corpus/）。

## 4. auxiliary_star 节点清单（逐候选，Task 2）

**裁定：0 生产**。候选起点（文昌/文曲/左辅/右弼/天魁/天钺/禄存/擎羊/陀罗/火星/铃星）
仅作检索起点。**与 shen_sha 分开判断、不互推**（红线 #4）。

| 候选 | 检索来源 | 原文核验 | 结果 |
|------|----------|----------|------|
| 全部候选 | 紫微斗数全书（主源）/ 紫微斗数全集 | ❌ 全书原文未入库（url=null）/ 全集 GAP-01 待获取 | **不生产** |

**拒绝理由**：辅星语义的权威定义在《紫微斗数全书》；该源 source_01.yaml 明记原文不在
仓库内、无 url。无原文则无法逐字核验，按"不可核实→不生产"拒绝（红线 #1/#5）。

## 5. shen_sha ↔ auxiliary_star 关系清单（Task 3）

**0 生产**。两类型均 0 节点，无关系可建。且 prompt 红线 #3"不因已有干支关系自动推导
神煞关系"独立成立。

## 6. 与已有节点的关系清单（Task 3）

**0 生产**。无新增节点，无 Tier 1 支撑的 shen_sha/auxiliary_star ↔ main_star/palace/
heavenly_stem/earthly_branch 关系。"传统上常见"非证据（红线 + Task 3 禁止）。

## 7. 新增引用清单

**0 新增**。无新增节点/关系，无新增 reference。Corpus 维持 10 引用。

## 8. 最终统计

| 项 | 7.1.6 基线 | 7.2B 变更 | 7.2B 最终 |
|----|-----------|-----------|-----------|
| nodes | 63 | 0 | **63** |
| relations | 37 | 0 | **37** |
| references | 10 | 0 | **10** |
| sha256 | 9c222617… | — | **9c222617…**（不变） |

## 9. Pipeline 运行结果（Task 5）

```
python knowledge/pipeline.py
  corpus written: knowledge/ziwei_corpus.json (63 nodes, 37 relations, 10 references)
  sha256: 9c2226175d2e026889d81473dbe2c49cc02bb96f31bfb831d65413c9fefa8312

python knowledge/validate.py
  VALIDATION PASSED: all corpus entries conform to KB-001~020
```

- 双重运行 SHA-256 一致（与 7.1.6 完全相同）→ 确定性保持。
- `ziwei_corpus.json` 由 pipeline 重写，但内容字节一致 → git diff 为空（见 §10）。

## 10. 回归测试结果（Task 6） + 零触碰验证

```
pytest -rN  →  599 passed, 1 warning in 104.70s   (599/599 PASS，无回归)
```

### 零触碰验证

| 检查 | 结果 |
|------|------|
| `git diff -- knowledge/corpus/` | ✅ 空 |
| `git diff -- knowledge/ziwei_corpus.json` | ✅ 空（sha256 不变） |
| `git diff -- src/` | ✅ 空 |
| `git diff -- docs/ziwei/` | ✅ 空 |
| `git diff -- docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md` | ✅ 空 |
| `git diff -- docs/governance/CAPABILITY_LIFECYCLE.md` | ✅ 空 |
| `git diff -- docs/specification/` / `docs/governance/ACP/` / `reference/` | ✅ 空 |
| 新增 node_type / relation_type / ref_type | ✅ 未新增 |
| LLM / RAG / 网络运行时依赖 | ✅ 未引入（pipeline 离线确定性; webfetch 仅作只读核验尝试且失败） |
| 已有 63/37/10 数据 | ✅ 未修改 |

> **Ruff 基线**：`ruff check` 2 处（test_crawl4ai.py E401/I001）+ `format --check` 7 文件
> 为 main 基线既有（7.2A 已复验），与本 Sprint 零相关；本 Sprint 未触碰任何 Python 文件。

## 11. GAP 更新（Task 7）

| GAP | 变更 | 状态 |
|-----|------|------|
| GAP-05 | 7.2B：来源策略已定义（Tier 1/Tier 2+/不可核实三档）+ 生产授权已获；实际生产因源文本不可达 → 0 | 待源文本可达 |
| GAP-12（新增） | auxiliary_star Tier 1 主源《紫微斗数全书》原文未入库 + 《全集》GAP-01 待获取 → 0 生产 | 待源文本可达 |
| GAP-13（新增） | shen_sha Tier 1 原文逐字核验未达成（三命通会/渊海子平 webfetch 2 次失败）→ 0 生产 | 待原文核验 |
| GAP-01 / GAP-02 | 未触碰 | 待解决 / REMAINS OPEN |
| 其余 | 未触碰 | 记录 |

## 12. Task 4 — 契约示例层（不执行）

`reference/contracts/knowledge_contract.json` 属**冻结 Reference Contract**。7.2B 硬约束
明列"❌ 不修改 Contract / Golden Vectors / Reference"，AGENTS.md 亦规定 Contract 修改须
走 ACP。且 auxiliary_star 0 生产 → 无示例可补。**Task 4 不执行**（N/A）；若将来生产
auxiliary_star 需补契约示例层，应走 ACP，非直接修改。

## 13. Task 8 — Capability Status

`docs/governance/CAPABILITY_STATUS.md` Knowledge Layer 条目 Corpus 指针：数量维持
63/37/10（未变），Phase 标注更新为 7.2B（source-access blocked, 0 produced）。

## 14. Phase 7.3 入口条件声明

| 条件 | 状态 |
|------|------|
| Schema（shen_sha / auxiliary_star） | ✅ A（7.2A 已放行） |
| 来源策略 | ✅ 已定义（7.2B Task 0） |
| 生产授权 | ✅ 已获（用户下发 7.2B） |
| **Tier 1 原文可达性** | ❌ **阻塞**（GAP-12 / GAP-13） |
| 实际生产 | ❌ 0 节点 / 0 关系 |

**7.3 / 7.2B 重跑前置**（待人工决策，任一即可）：
1. 《紫微斗数全书》原文入库（解决 auxiliary_star 主源 + shen_sha 佐证）；或
2. 《紫微斗数全集》获取（GAP-01 闭环，多源交叉）；或
3. webfetch 可用后重试三命通会/渊海子平神煞章节逐字核验（解决 shen_sha）；或
4. 用户授权降级证据策略（如允许章节级引用 + interpretation，弃 verbatim 要求）——
   此为策略变更，需显式批准并评估对"高置信度、可追溯"目标的折损。

## 15. 成功标准对照

- [x] 来源策略已定义（GAP-05 来源部分 CLOSED）
- [x] shen_sha 首批节点已生产（**数量由证据决定 = 0**，证据不足记 GAP-13）
- [x] auxiliary_star 首批节点已生产（**数量由证据决定 = 0**，源不可达记 GAP-12）
- [x] 相关关系已生产（数量由证据决定 = 0）
- [x] 示例层：N/A（冻结 Contract 不修改 + 0 生产）
- [x] 全量测试通过（599/599）
- [x] 报告已交付

## 16. 产出物清单

| 文件 | 说明 | 状态 |
|------|------|------|
| `docs/governance/knowledge/KNOWLEDGE_PHASE_7.2B_REPORT.md` | 本 Sprint 报告 | 待合并 |
| `docs/governance/knowledge/ZIWEI_CORPUS_GAPS.md` | GAP-05 更新 + GAP-12/13 新增 | 待合并 |
| `docs/governance/CAPABILITY_STATUS.md` | Corpus 指针 Phase 标注更新（数量不变） | 待合并 |
| `context/归档.md` | 追加 7.2B 记录 | 待合并 |
| 节点 / 关系 / 引用 / Contract / Schema / src / Golden Vectors | **未修改** | N/A |

---

**本 Sprint 停止。** 0 节点 / 0 关系 / 0 引用生产（证据驱动：Tier 1 原文不可达，不虚构）；
Corpus 维持 63/37/10；599/599 全绿；零触碰验证通过。未进入 Phase 7.3；未进入 pattern /
interpretation；未引入 LLM / RAG / 网络运行时依赖；未修改任何冻结规范。等待人工 Evidence
Review 与授权（7.3 入口条件见 §14）。
