# Ziwei Schema Admission Gate — shen_sha（门 A 独立裁定记录）

> **Sprint**: Phase 7.2A — Shen Sha / Auxiliary Star Schema Admission Gate
> **日期**: 2026-08-17
> **状态**: **A — 已存在**（冻结 Schema 已注册; 可直接进入生产授权评估）
> **性质**: 不修改任何冻结规范, 不生产任何数据。
> **裁定独立**: 本文件仅裁定 `shen_sha`; `auxiliary_star` 见独立文件
> `ZIWEI_SCHEMA_ADMISSION_AUXILIARY_STAR.md`（两类型分开判断, 互不默认）。

---

## 1. 三处冻结权威交叉核对

| 核对点 | 位置 | 预期 | 实际 |
|--------|------|------|------|
| node_type 枚举 | KB-002（`docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md` §KB-002, L96） | 是否包含 `shen_sha` | ✅ **包含**（20 类型清单第 8 位: `...main_star, auxiliary_star, shen_sha, pattern, ...`） |
| NodeType 枚举 | `reference/knowledge.py` L41 | 是否包含 `SHEN_SHA` | ✅ **包含**（`SHEN_SHA = "shen_sha"`） |
| contract 引用 | `reference/contracts/knowledge_contract.json` L991 + L392-396 | 是否包含 `shen_sha` | ✅ **包含**（`node_types` 数组第 8 位; 且含契约示例节点 `kn:shen_sha:yang_ren` / `node_type: "shen_sha"`） |

> 佐证（非裁定依据, 仅记录）: `reference/examples/knowledge/nodes.yaml` L145-158
> 含 `kn:shen_sha:yang_ren` 示例（羊刃, systems: [bazi, ziwei]）。

## 2. 裁定

| 检查 | 结果 |
|------|------|
| 裁定分类 | **A — 已存在** |
| 是否需要 Schema Change / ACP | ❌ **不需要**（KB-002 已注册, 无缺口） |
| 是否修改任何冻结规范 | ❌ 不修改 |
| 是否生产节点 | ❌ 不生产（本 Sprint 为 Schema 审查） |

## 3. Canonical 记录（供 7.2B 生产引用）

| 项 | 值 |
|----|-----|
| canonical node_type | `shen_sha` |
| NodeType 枚举成员 | `NodeType.SHEN_SHA` |
| canonical ID 格式 | `kn:shen_sha:<name_en>`（符合 KB-001 `^kn:[a-z_]+:[a-z_0-9]+$`） |
| 已存在契约示例 | `kn:shen_sha:yang_ren`（羊刃, 三命通会, credibility 0.85） |
| 业务理由 | 神煞语义节点（ZW-017 计算未实现, 仅引用/知识收录; Scope §2 优先级 2） |
| 来源要求 | 需来源确认（Tier 2+）; 流派分歧大 → 需多源 SchoolView（见 GAP-05） |

## 4. 语义边界（Scope Note, 不修改冻结规范）

- 与 `main_star` / `auxiliary_star` 边界: shen_sha 是**神煞**语义类别
  （羊刃、禄神、桃花、天乙贵人等传统神煞体系）; main_star 是十四主星,
  auxiliary_star 是辅星（左辅右弼等）。三者在 Ziwei 星曜表中为**并列**语义槽位,
  node_type 互斥, 不重叠。
- 与 `earthly_branch` / `heavenly_stem` 边界: 干支为历法/基础符号体系;
  shen_sha 常由干支组合推导（如羊刃 = 帝旺位), 但属于**派生语义**节点, 非符号本体。
- 与 `pattern` 边界: pattern（格局）是星曜/宫位组合的解释性归类; shen_sha 是
  单星/干支的语义标签。若将来某神煞被纳入格局判断, 属解释域（ZW-017 边界外）。

## 5. 非目标（显式）

- ❌ 不包含 shen_sha 节点生产（Phase 7.2B, 待授权）
- ❌ 不包含来源选定 / SchoolView 多源裁定（GAP-05 关联, 待 7.2B 前置）
- ❌ 不扩展 node_type / relation_type / ref_type
- ❌ 不修改 KB-001~020 / Corpus / src/ / docs/ziwei/

## 6. 后续路径（等待人工 Evidence Review 与授权）

1. 认可本裁定（A 类）后: GAP-05 关联的 **Schema 阻塞项移除**（原本按任务书
   示例延后; 实际冻结 Schema 已注册 `shen_sha`）。
2. Phase 7.2B 生产前置条件: **生产授权** + **来源确认（Tier 2+ 多源 SchoolView）**。
