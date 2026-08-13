# Ziwei Corpus Build Plan（构建执行计划）

> **Sprint**: Phase 7.1.0 — Corpus Scope & Source Freeze
> **日期**: 2026-08-13
> **状态**: **FROZEN**（执行顺序约束: 不得跨阶段跳跃; 每子阶段可独立验证）
> **依据**: `ZIWEI_CORPUS_SCOPE.md` / `ZIWEI_CORPUS_COVERAGE_MATRIX.md` /
> `ZIWEI_CORPUS_ADMISSION_POLICY.md`

---

## 执行序列

```text
7.1.1 Core Vocabulary（41 节点）
   ↓
7.1.2 Relations（24 关系）
   ↓
7.1.3 References & Provenance 补充（8 引用 + 走查）
   ↓
7.1.4 Extended Nodes（干支 22 + shen_sha/aux 首批）
   ↓
7.1.5 Corpus Validation & Evidence Review
   ↓
7.1.6 Corpus Freeze（v1.0.0）
```

---

## Phase 7.1.1 — Core Vocabulary

| 项 | 值 |
|----|-----|
| 新增节点数 | 21（main_star +9, palace +7, ten_god +5）; 保留 Pilot 20 |
| 新增关系数 | 0 |
| 新增引用数 | 0 |
| 所需来源 | 紫微斗数全书（Tier 1）; 渊海子平（Tier 1） |
| 交付物 | corpus/nodes 全量 41; pipeline 运行; 校验 + 回归通过 |

**验证**: `python knowledge/pipeline.py` + `validate.py` + `pytest tests/test_knowledge_pipeline.py` 全绿。

## Phase 7.1.2 — Relations

| 项 | 值 |
|----|-----|
| 新增关系数 | 12（he +3, chong +3, xing +3, hai +3）; 保留 Pilot 12 |
| 所需来源 | 紫微斗数全书（地支冲刑害/同度恒等式）; 契约 BC-012 交叉引用 |
| 交付物 | corpus/relations 全量 24; 关系端点完整性校验 |

**验证**: 同上 + 端点存在性检查（validate.py 已含）。

## Phase 7.1.3 — References & Provenance

| 项 | 值 |
|----|-----|
| 新增引用数 | 5（classic +2, school +1, modern +1, oral +1）; 保留 Pilot 3 |
| 新增关系数 | yinyong(5) + shuyu(5) 随引用建立（可并入 7.1.2 或本阶段, 不跨 7.1.1 顺序） |
| 所需来源 | 紫微斗数全集（GAP-01）; 中州派讲义版次（GAP-02）; iztro（Tier 3, MIT） |
| 交付物 | references 全量 8; Pilot audit 处置落地（school:zhongzhou provenance 补登或降级） |

## Phase 7.1.4 — Extended Nodes

| 项 | 值 |
|----|-----|
| 新增节点数 | 干支 22（heavenly_stem 10 + earthly_branch 12）+ shen_sha/auxiliary_star 首批（来源确认后, 数量按 GAP-05 结论） |
| 所需来源 | Tier 1（干支）+ Tier 2/3（神煞/辅星, 待来源登记） |
| 交付物 | nodes 扩展; 干支关系（冲合刑害）交叉补充 |

## Phase 7.1.5 — Corpus Validation & Evidence Review

| 项 | 值 |
|----|-----|
| 内容 | 全量走查 Admission Policy 六项; 冲突 SchoolView 核对; GAP 复核; 确定性/序列化复核 |
| 交付物 | 校验报告（人工 Evidence Review 输入） |

## Phase 7.1.6 — Corpus Freeze（v1.0.0）

| 项 | 值 |
|----|-----|
| 内容 | Corpus 版本 v1.0.0（ziwei_corpus.json 正式冻结, 变更须走 Corpus 级审查流程） |
| 交付物 | Freeze 记录 + CAPABILITY_STATUS 指针更新（Corpus: PARTIAL → FROZEN-v1.0.0） |

---

## 约束

1. **顺序硬约束**: 7.1.1 → 7.1.2 → … 不得跳跃（如先 pattern 后 main_star 禁止）。
2. **独立可验证**: 每个子阶段结束 Pipeline 可运行、测试全绿、零触碰边界保持。
3. **不跨阶段生产**: 子阶段内只生产本阶段 Scope 内容。
4. **Pilot 数据不修改**: 7.1.1 正式化时仅流程走查, 内容不变。
