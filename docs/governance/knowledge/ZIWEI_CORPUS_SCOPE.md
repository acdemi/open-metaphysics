# Ziwei Knowledge Corpus Scope（语料范围冻结）

> **Sprint**: Phase 7.1.0 — Corpus Scope & Source Freeze
> **日期**: 2026-08-13
> **状态**: **FROZEN**（本文件为 Phase 7.1.1+ 语料建设的范围依据）
> **规范基准**: `KNOWLEDGE_BEHAVIOR_SPEC.md` KB-002（20 种 node_type, 冻结）/
> KB-007（15 种 relation_type）/ KB-011（4 种 ref_type）
> **原则**: 不得为凑数纳入 node_type；每个 type 须有业务理由与来源要求；
> 争议须标记分歧来源。发现 Schema 表达缺口 → 记 GAP（不修改规范）。

---

## 1. 决策规则

1. **业务理由优先**：每个 node_type 的纳入必须能映射到 Ziwei 冻结契约
   （BC-001~014）或领域基础概念（五行/干支/生克）。
2. **来源先行**：无 Tier 1~3 可靠来源的类型不得进入正式 Corpus（Admission Policy）。
3. **争议显式化**：流派分歧 → `SchoolView` 保留差异；无共识 → 降优先级或延后。
4. **不碰计算**：本 Corpus 只读引用；与 Ziwei 计算无关（ZW-017 边界保持）。
5. **枚举冻结**：不新增 node_type / relation_type / ref_type；缺口记 GAP。

---

## 2. node_type 覆盖计划（20 种逐项登记）

| node_type | 第一阶段 | 优先级 | 预期数量级 | 来源要求 | 业务理由（映射契约） | 争议标记 |
|-----------|---------|--------|-----------|----------|----------------------|----------|
| wuxing | ✅ | 1 | 5 | 经典（Tier 1） | 五行局 BC-009、生克关系基底 | 无 |
| ten_god | ✅ | 1 | 10 | 经典（Tier 1, 渊海子平） | 子平共享概念（跨系统试点已含 5） | 无（属 bazi 体系, 收录为共享概念, 见 GAP-04） |
| heavenly_stem | ✅ | 1 | 10 | 经典（Tier 1） | 天干表（BC-007 五虎遁/干支基础） | 无 |
| earthly_branch | ✅ | 1 | 12 | 经典（Tier 1） | 地支表（BC-010 宫位地支/时辰 BC-004） | 无 |
| palace | ✅ | 1 | 12 | 经典（Tier 1） | 十二宫（BC-010, 命/身宫 BC-008） | 无 |
| main_star | ✅ | 1 | 14 | 经典（Tier 1） | 十四主星（BC-011/012 定局与星系） | 无 |
| auxiliary_star | 🟡 | 2 | 12-15 | 需来源确认（Tier 2+） | 左辅右弼等（ZW-017 计算未实现, 语义节点可收录） | 有: 流派星曜表差异（南派/北派） |
| shen_sha | 🟡 | 2 | 10-20 | 需来源确认 | 神煞语义（计算未实现, 仅引用层） | 有: 神煞体系流派分歧大 |
| pattern | 🟡 | 3 | 20-50 | 高争议（需 SchoolView 多源） | 格局（A-8: Ziwei 格局属解释域; 收录仅作知识） | 高: 格局定义无统一权威 |
| career | 🔴 | 4 | 10-20 | 解释域依赖 | 断事语义（依赖未实现能力, ZW-017 边界外） | 高: 断事规则流派差异 |
| personality | 🔴 | 4 | 10-20 | 解释域依赖 | 同上 | 高 |
| marriage | 🔴 | 4 | 5-10 | 解释域依赖 | 同上 | 高 |
| health | 🔴 | 4 | 5-10 | 解释域依赖 | 同上 | 高 |
| wealth | 🔴 | 4 | 5-10 | 解释域依赖 | 同上 | 高 |
| annual_fortune | 🔴 | 4 | 10-20 | 解释域依赖 | 流年语义（未实现） | 高 |
| major_luck | 🔴 | 4 | 10-20 | 解释域依赖 | 大限语义（未实现） | 高 |
| yong_shen | 🔴 | 5 | 10 | 跨域（子平体系） | 用神体系（属 BaZi 语料授权范围） | 有: 用神取法流派分歧 |
| xi_shen | 🔴 | 5 | 10 | 跨域 | 同上 | 有 |
| ji_shen | 🔴 | 5 | 10 | 跨域 | 同上 | 有 |
| tiao_hou | 🔴 | 5 | 10 | 跨域 | 调候（子平体系） | 有 |

> 优先级: 1 = 第一阶段（7.1.1~7.1.3）; 2 = 第二阶段（7.1.4）;
> 3 = 第三阶段（7.1.4 扩展）; 4 = 后续阶段（依赖解释域授权）; 5 = 跨域授权。

---

## 3. 第一阶段冻结范围（本文件核心）

**Phase 7.1.1~7.1.3 仅覆盖**:

| 类别 | 数量 | 说明 |
|------|------|------|
| nodes | 41 | wuxing(5) + main_star(14) + palace(12) + ten_god(10) |
| relations | 24 | sheng(5) + ke(5) + he(5) + chong(3) + xing(3) + hai(3) |
| references | 8 | classic_text(3) + school_commentary(2) + modern_interpretation(1) + oral_tradition(2) |

> heavenly_stem/earthly_branch 节点归入 7.1.4 扩展（与干支关系同批, 避免单批过大）。

**范围外（本阶段明确不生产）**: auxiliary_star / shen_sha / pattern /
断事类（career 等 8 种）/ 用神类（yong_shen 等 4 种）—— 见 §2 优先级与 GAP。

---

## 4. Scope 变更机制

- 本 Scope 为**治理冻结**文件；变更须经人工批准（对齐 Admission Policy 与
  ACP 精神, 但本文件非契约, 不触发 ACP）。
- 每个子阶段（7.1.1~7.1.6）交付时按本 Scope 校验；越界即回退。
