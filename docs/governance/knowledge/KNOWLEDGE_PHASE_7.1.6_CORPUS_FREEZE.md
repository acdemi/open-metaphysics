# Knowledge Phase 7.1.6 — Ziwei Corpus Freeze v1.0.0（冻结记录·已批准）

> **日期**: 2026-09-16 · **分支**: `work/knowledge/phase7.2b-r3`
> **批准**: 决策点 **D-12 = A**（人工裁定：追认 D-9 + 冻结 `ziwei_corpus:v1.0.0`）
> **依据**: `ZIWEI_CORPUS_BUILD_PLAN.md` §7.1.6 · **就绪审计**: `KNOWLEDGE_PHASE_7.1.6_FREEZE_READINESS.md`

---

## 1. 冻结声明

| 项 | 值 |
|----|----|
| 冻结产物 | `knowledge/ziwei_corpus.json` |
| 版本 | **`ziwei_corpus:v1.0.0`** |
| digest (SHA-256) | `69d6e2a6b2f82d58292bfd11847aa7d26e2cd75eabda8cdbbbb67d4f6cc5f73d` |
| 计数 | **102 nodes / 47 relations / 41 references** |
| 规范输入 | `knowledge/corpus/ziwei/{nodes,relations,references}/*.yaml`（与产物同源、同提交） |
| 生成器 | `knowledge/pipeline.py`（确定性；LF 输出，DEF-02 已修复） |
| 生效 | 本记录提交后 |

**内容覆盖（冻结基线）**

| 类别 | 分布 |
|------|------|
| node_type | wuxing 5 / main_star 14 / palace 12 / ten_god 10 / heavenly_stem 10 / earthly_branch 12 / auxiliary_star 12 / shen_sha 27 |
| relation_type | sheng 5 / ke 5 / he 10 / chong 3 / xing 8 / hai 6 / shuyu 5 / yinyong 5 |
| ref_type | classic_text 37 / school_commentary 1⚠️ / modern_interpretation 1 / oral_tradition 2 |

## 2. 冻结范围与变更流程

**冻结对象**：上述产物 + 其规范输入 YAML + 来源登记（`sources/ziwei/*.yaml` 的 revision pin）。

**变更流程**（自本记录起生效）：任何 node / relation / reference 的**新增、修改、删除**，
须走 **Corpus 级审查**（对齐 `docs/specification/RUNTIME_CONTRACT.md` 的合并门精神）：

```text
提案（范围 + 来源）
   ↓ 证据逐字核验（revision-pinned 原文子串匹配回执）
   ↓ pipeline / validate / 确定性双跑 / 回归测试
   ↓ 人工批准
   ↓ 版本递增 + Freeze 记录更新
```

**版本递增建议**：兼容追加 → `v1.0.x`；闭合既有开放项 → `v1.1.0`；
结构性变更（node_type / relation_type / ref_type 参与）→ `v2.0.0`（并须先过 Schema Gate/ACP）。
实际定级由人工在批准时决定。

## 3. 冻结时的元数据规范化（同提交）

语料自我标识由 Phase 7.0 试点值升级为冻结值：

| 字段 | 变更前 | 变更后 |
|------|--------|--------|
| `corpus_id` | `ziwei_pilot_v1` | **`ziwei_corpus`** |
| `status` | `pilot` | **`frozen`** |
| `version` | （无） | **`1.0.0`** |

> 因此冻结 digest 由就绪审计时的候选值 `bac1b1ef…` 变为
> `69d6e2a6…`；**节点 / 关系 / 引用内容零变化**（仅 metadata 自我标识）。

## 4. D-9 追认（人工裁定）

`shen_sha` 27 节点**超出** `ZIWEI_CORPUS_COVERAGE_MATRIX.md` 的 Phase-7.1.0 规划带 `10-20`，
经 **D-12 = A** 裁定**追认**为既成范围。记录理由：

- 27 条全部来自 **revision-pinned Tier 1** 原文（《三命通會》卷三 revid 2184219 等），逐字核验 PASS；
- 规划带为**数量级估计**，非硬上限；不得为凑数纳入 —— 本次全部为证据驱动，未凑数；
- `auxiliary_star` 维持 12（在规划带 12-15 内），未扩。

## 5. 随冻结载入的开放项（不得静默丢弃）

| 项 | 状态 | 含义 |
|----|------|------|
| GAP-02 | OPEN | `school_commentary` 尚缺 1 条（中州派无可核实来源；现有 1 条为 `not_authoritative`）—— **唯一引用缺口** |
| GAP-14 | OPEN | 四化无对应 `node_type`（schema gap，不擅自扩；须 ACP） |
| GAP-15 | OPEN | 星曜五行多源冲突（擎羊/陀罗/火星/铃星：卷一 vs 卷二） |
| GAP-01 | SOURCE_DISCOVERED | 《紫微斗數全集》未获取（第二权威缺位） |
| GAP-03/04/06/07/08 | 记录 | Schema 表达缺口 / 跨系统归属 / pattern / 断事类 / 用神类（范围外） |
| D-11 | 待裁 | GAP-15 处置口径（多源并列 vs 不生产） |
| D-6 / D-7 | 待裁 | 四化 schema / `auxiliary_star` 是否扩至卷一杂曜 |

> 以上开放项**不阻塞冻结**：冻结记录的是「已核实内容 + 已知边界」的确定状态，
> 而非「无缺口」。

## 6. 验证回执

| 检查 | 结果 |
|------|------|
| pipeline 双跑 digest | 一致（`69d6e2a6…`） |
| 文件字节哈希 == 登记 digest | ✅ |
| `validate.py` | `VALIDATION PASSED`（KB-001~020 + 端点/唯一性） |
| 回归测试 | **618 / 618**（failures=0 errors=0） |
| 冻结工件漂移（`reference/` `docs/specification/` `docs/design/` `docs/engineering/`） | 空 ✅ |

## 7. 产出物

| 文件 | 状态 |
|------|------|
| `docs/governance/knowledge/KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md` | 新增（本记录） |
| `knowledge/pipeline.py` | metadata 冻结标识（§3） |
| `knowledge/ziwei_corpus.json` | 冻结产物 v1.0.0 |
| `docs/governance/CAPABILITY_STATUS.md` | Corpus `PARTIAL` → `FROZEN-v1.0.0` |
| `knowledge/README.md` | 计数/状态刷新 |
| `docs/governance/knowledge/ZIWEI_CORPUS_BUILD_PLAN.md` | 7.1.6 执行记录 |
| `docs/governance/knowledge/ZIWEI_CORPUS_GAPS.md` | D-9 追认注记 |
