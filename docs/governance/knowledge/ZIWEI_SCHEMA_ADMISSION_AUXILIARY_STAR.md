# Ziwei Schema Admission Gate — auxiliary_star（门 A 独立裁定记录）

> **Sprint**: Phase 7.2A — Shen Sha / Auxiliary Star Schema Admission Gate
> **日期**: 2026-08-17
> **状态**: **A — 已存在**（冻结 Schema 已注册; 可直接进入生产授权评估）
> **性质**: 不修改任何冻结规范, 不生产任何数据。
> **裁定独立**: 本文件仅裁定 `auxiliary_star`; `shen_sha` 见独立文件
> `ZIWEI_SCHEMA_ADMISSION_SHEN_SHA.md`（两类型分开判断, 互不默认）。

---

## 1. 三处冻结权威交叉核对

| 核对点 | 位置 | 预期 | 实际 |
|--------|------|------|------|
| node_type 枚举 | KB-002（`docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md` §KB-002, L95） | 是否包含 `auxiliary_star` | ✅ **包含**（20 类型清单第 7 位: `...main_star, auxiliary_star, shen_sha, pattern, ...`） |
| NodeType 枚举 | `reference/knowledge.py` L40 | 是否包含 `AUXILIARY_STAR` | ✅ **包含**（`AUXILIARY_STAR = "auxiliary_star"`） |
| contract 引用 | `reference/contracts/knowledge_contract.json` L990 | 是否包含 `auxiliary_star` | ✅ **包含**（`node_types` 数组第 7 位） |

> 注: 契约中**尚无** `auxiliary_star` 示例节点（区别于 shen_sha 的
> `kn:shen_sha:yang_ren`）。即 Schema 已注册, 但契约示例层缺位 —— 该空缺
> 不阻塞 Schema Admission（KB-002 注册即允许生产）, 属于 7.2B 生产时的示例补充项。

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
| canonical node_type | `auxiliary_star` |
| NodeType 枚举成员 | `NodeType.AUXILIARY_STAR` |
| canonical ID 格式 | `kn:auxiliary_star:<name_en>`（符合 KB-001 `^kn:[a-z_]+:[a-z_0-9]+$`） |
| 已存在契约示例 | 无（示例层空缺, 7.2B 补充） |
| 业务理由 | 辅星语义节点（左辅右弼等; ZW-017 计算未实现, 仅引用/知识收录; Scope §2 优先级 2） |
| 来源要求 | 需来源确认（Tier 2+）; 南派/北派星曜表差异 → 需 SchoolView（见 GAP-05） |

## 4. 语义边界（Scope Note, 不修改冻结规范）

- 与 `main_star` 边界: main_star 为十四主星（紫微星系/天府星系）;
  auxiliary_star 为**辅佐星曜**（左辅、右弼、文昌、文曲、天魁、天钺、禄存、擎羊、
  陀罗、火星、铃星、天马等, 各派收录口径不一）。两者在星曜表中为**并列**语义槽位,
  node_type 互斥。
- 与 `shen_sha` 边界: 传统上部分辅星与神煞概念有交叉（流派差异）; 本项目以
  node_type 划分: auxiliary_star = 星曜表中固定辅佐位; shen_sha = 干支/星曜
  派生的神煞语义标签。具体星曜归入哪类, 由 7.2B 来源裁定（SchoolView 分歧保留）。
- 与 `palace` / `heavenly_stem` / `earthly_branch` 边界: 宫位与干支为位置/符号
  基底; auxiliary_star 为星曜语义, 不相交。

## 5. 非目标（显式）

- ❌ 不包含 auxiliary_star 节点生产（Phase 7.2B, 待授权）
- ❌ 不包含来源选定 / SchoolView 多源裁定（GAP-05 关联, 待 7.2B 前置）
- ❌ 不扩展 node_type / relation_type / ref_type
- ❌ 不修改 KB-001~020 / Corpus / src/ / docs/ziwei/

## 6. 后续路径（等待人工 Evidence Review 与授权）

1. 认可本裁定（A 类）后: GAP-05 关联的 **Schema 阻塞项移除**（实际冻结 Schema
   已注册 `auxiliary_star`）。
2. Phase 7.2B 生产前置条件: **生产授权** + **来源确认（Tier 2+ 多源 SchoolView）**
   + **契约示例层补充**（7.2B 生产首节点时一并写入）。
