# Knowledge Phase 7.1.6 — Heavenly Stem Five-Combinations Report

> **Sprint**: Phase 7.1.6 — 天干五合（he, 证据驱动）
> **日期**: 2026-08-13
> **结果**: **+5 关系（五合 5/5 全部原文验证）**; Corpus 63/37/10

---

## 1. Executive Summary

天干五合候选 5 条在《三命通会》卷二·论十干化气（Tier 1）**全部逐字验证**
（渊海子平佐证 甲己/戊癸）——按证据驱动原则 **5/5 全产**（无证据不足项,
无需 GAP-11）。关系类型复用 `he`（KB-007 既有枚举）, 化气五行记于
conditions（relation_subtype=wu_he / result_element）, 未新增枚举。

## 2. Task 0 — Schema 预检查

| 检查 | 结果 |
|------|------|
| `he` 是否合法 relation_type | ✅ KB-007 冻结枚举含 `he`（已用于星曜同宫/五合复用） |
| 天干节点实际 ID | ✅ `kn:heavenly_stem:jia` ~ `gui`（10 个全存在, corpus JSON 核对） |
| NodeType 枚举含 HEAVENLY_STEM | ✅ `reference/knowledge.py` NodeType.HEAVENLY_STEM（KB-002 冻结） |
| 阻塞 | ❌ 无（预检查 PASS, 无需 STOP） |

## 3. Task 2 — 证据检索（每候选逐项）

| 候选 | 三命通会/卷二·论十干化气 | 渊海子平佐证 | 验证 |
|------|--------------------------|--------------|------|
| 甲己合（化土） | ✅「故甲己合而化土，其气上升而云施」 | ✅「谓之甲己化土」 | **通过** |
| 乙庚合（化金） | ✅「乙庚化金，非已酉丑月不化」 | （主页面未收录该章） | **通过** |
| 丙辛合（化水） | ✅「丙辛化水。非申子辰月不化」 | 同上 | **通过** |
| 丁壬合（化木） | ✅「丁壬化木，非亥卯未月不化」 | 同上 | **通过** |
| 戊癸合（化火） | ✅「戊癸化火，非丙午戌月不化」 | ✅「戊癸化火巳午」 | **通过** |

> 佐证: 三命通会卷二 TOC 含「19论十干化气」; 原文同时记载「妒合」等化气
> 条件细节（非本关系范围, 记于 evidence 引文）。

## 4. Task 3 — 生产关系（5 条）

| ID | 端点 | 化气五行 | 来源 | 准入 |
|----|------|----------|------|------|
| rel:he:jia_ji | jia ↔ ji | 土 | 三命通会·卷二·论十干化气 | ✅ 6/6 |
| rel:he:yi_geng | yi ↔ geng | 金 | 同上 | ✅ 6/6 |
| rel:he:bing_xin | bing ↔ xin | 水 | 同上 | ✅ 6/6 |
| rel:he:ding_ren | ding ↔ ren | 木 | 同上 | ✅ 6/6 |
| rel:he:wu_gui | wu ↔ gui | 火 | 同上（渊海子平佐证） | ✅ 6/6 |

- direction: undirected; weight: 1.0; evidence 含原文引文; conditions 记
  relation_subtype=wu_he + result_element。
- 端点全部 ∈ 63 节点（validate.py 端点存在性 PASS）。

## 5. 未生产关系

无（5/5 证据充分）。六合/三合/冲/刑/害 **未生产**（越界禁止）;
天干 合 之外的其他关系（如 天干相冲 甲庚冲等）不在本 Sprint 范围。

## 6. 最终统计与验证

| 项 | 值 |
|----|-----|
| nodes | **63**（不变） |
| relations | **37**（sheng 5 / ke 5 / he 10 / chong 3 / xing 8 / hai 6） |
| references | **10**（不变） |
| sha256 | 9c222617…（双重运行一致） |
| 校验 | VALIDATION PASSED（KB-001~020） |
| 测试 | 10/10 pipeline + **599/599** 全量 |
| ruff | check / format --check PASS |

## 7. GAP 更新

| GAP | 状态 |
|-----|------|
| （新增）GAP-11 | **无需创建** —— 五合 5/5 证据充分, 无证据不足候选 |
| GAP-02 | REMAINS OPEN（未触碰） |
| 其余 | 未触碰 |

## 8. 零触碰验证

| 检查 | 结果 |
|------|------|
| 既有 63 节点 / 32 关系 / 10 引用 | ✅ 未修改 |
| src/ / docs/ziwei/ / KB 规范 / CAPABILITY_LIFECYCLE | ✅ 全空 |
| 新 node_type / relation_type | ✅ 未新增 |
| LLM / RAG / 网络爬虫 | ✅ 未引入（原文核验只读检索） |
| 六合/三合/冲/刑/害 等其他关系 | ✅ 未生产 |

## 9. Phase 7.2A 入口条件声明

1. Corpus: 63 节点 / 37 关系 / 10 引用, 证据闭合（干支体系完整:
   天干 10 + 地支 12 + 五合/三刑/六害/六冲对宫等已覆盖）✅
2. GAP-02（school）为唯一 REMAINS OPEN 项（不影响生产）✅
3. 7.2A 候选范围（待授权）: shen_sha / auxiliary_star Schema Gate
   （照 7.1.4A 模式: 先核实冻结枚举是否已含, 再决定 ACP 或生产）;
   interpretation 层仍待 Knowledge 就绪后另行授权。

---

**本 Sprint 停止。** 未进入 7.2A; 未进入 interpretation; 未引入 LLM/RAG;
未修改任何冻结规范。等待人工 Evidence Review 与授权。
