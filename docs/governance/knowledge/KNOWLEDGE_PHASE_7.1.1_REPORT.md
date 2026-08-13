# Knowledge Phase 7.1.1 — Ziwei Core Vocabulary Production Report

> **Sprint**: Phase 7.1.1 — Core Vocabulary（受控语料生产）
> **日期**: 2026-08-13
> **依据**: Phase 7.1.0 冻结工件（Scope / Source Registry / Admission Policy /
> Build Plan / Gaps）
> **结果**: **41/41 第一波节点完成**（20 Pilot 正式化 + 21 新增）

---

## 1. Executive Summary

按 Build Plan 序列 7.1.1（Core Vocabulary）执行：新增 21 个节点
（main_star +9 / palace +7 / ten_god +5，全部 Tier 1 来源），
Pilot 20 节点正式化（内容零修改）。`knowledge/ziwei_corpus.json`
现含 **41 节点 / 12 关系 / 3 引用**，全部通过 KB-001~020 校验，
双重构建逐字节一致。全量测试 599/599 无回归。

---

## 2. 新增节点清单（21 个）

| # | ID | 类型 | 来源（Tier） | 备注 |
|---|----|------|--------------|------|
| 1 | kn:main_star:wuqu | main_star | 紫微斗数全书（T1）+ 中州派（T2 SchoolView） | offset -4, 属金 |
| 2 | kn:main_star:tiantong | main_star | 紫微斗数全书（T1） | offset -5, 属水 |
| 3 | kn:main_star:taiyin | main_star | 紫微斗数全书（T1） | offset +1, 属水 |
| 4 | kn:main_star:tanlang | main_star | 紫微斗数全书（T1）+ 中州派（T2 SchoolView） | offset +2, 属木 |
| 5 | kn:main_star:jumen | main_star | 紫微斗数全书（T1） | offset +3, 属水 |
| 6 | kn:main_star:tianxiang | main_star | 紫微斗数全书（T1） | offset +4, 属水 |
| 7 | kn:main_star:tianliang | main_star | 紫微斗数全书（T1） | offset +5, 属土 |
| 8 | kn:main_star:qisha | main_star | 紫微斗数全书（T1） | offset +6, 属金 |
| 9 | kn:main_star:pojun | main_star | 紫微斗数全书（T1） | offset +10, 属水 |
| 10 | kn:palace:ji_e | palace | 紫微斗数全书（T1） | 疾厄宫 |
| 11 | kn:palace:qianyi | palace | 紫微斗数全书（T1） | 迁移宫 |
| 12 | kn:palace:nupu | palace | 紫微斗数全书（T1） | 奴仆宫 |
| 13 | kn:palace:guanlu | palace | 紫微斗数全书（T1） | 官禄宫 |
| 14 | kn:palace:tianzhai | palace | 紫微斗数全书（T1） | 田宅宫 |
| 15 | kn:palace:fude | palace | 紫微斗数全书（T1） | 福德宫 |
| 16 | kn:palace:fumu | palace | 紫微斗数全书（T1） | 父母宫 |
| 17 | kn:ten_god:jiecai | ten_god | 渊海子平（T1） | 劫财 |
| 18 | kn:ten_god:shishen | ten_god | 渊海子平（T1） | 食神 |
| 19 | kn:ten_god:shangguan | ten_god | 渊海子平（T1） | 伤官 |
| 20 | kn:ten_god:zhengcai | ten_god | 渊海子平（T1） | 正财 |
| 21 | kn:ten_god:piancai | ten_god | 渊海子平（T1） | 偏财 |

> 主星偏移与元素为经典知识（星曜总论）；与 Ziwei Contract BC-012 偏移表
> 一致（知识层为引用，不参与计算）。武曲/贪狼按 Scope 要求含中州派
> SchoolView（Admission Policy 冲突处理示范）。

## 3. Pilot 正式化状态（20 个）

- **19/20**: provenance 完整（source.text + chapter + author），直接保留。
- **1 处缺口**: `ref:school:zhongzhou_minggong`（中州派讲义）——
  版本/出版社信息**不可核实**（无授权数字版），**未虚构补充**；
  维持 GAP-02 记录（Phase 7.1.3 处理：补登版次或降级）。
- Pilot 条目内容**零修改**（仅新条目追加至同一 YAML 文件）。

## 4. 最终节点统计

| 类别 | 计划 | 完成 | 状态 |
|------|------|------|------|
| wuxing | 5 | 5 | ✅ |
| main_star | 14 | 14 | ✅ |
| palace | 12 | 12 | ✅ |
| ten_god | 10 | 10 | ✅ |
| **合计** | **41** | **41** | **41/41 完整** |

## 5. Pipeline 运行结果

```
$ uv run python knowledge/pipeline.py
corpus written: .../knowledge/ziwei_corpus.json (41 nodes, 12 relations, 3 references)
sha256: 77ea406b...

$ uv run python knowledge/validate.py
VALIDATION PASSED: all corpus entries conform to KB-001~020

确定性: 双重运行 SHA-256 一致 ✅（KB-020）
```

## 6. 回归测试结果

| 套件 | 结果 |
|------|------|
| `tests/test_knowledge_pipeline.py` | 10/10 PASS |
| 全量 pytest | **599/599 PASS**（无回归） |
| ruff check / format --check | 通过 |

## 7. 遇到的 GAP（记录，不解决）

| GAP | 说明 | 处理 |
|-----|------|------|
| GAP-02 | 中州派讲义版本/页码不可核实（ref:school:zhongzhou_minggong provenance 缺口） | 维持记录; Phase 7.1.3 补登或降级 |
| （无新增 GAP） | 21 个新增节点均满足六项准入条件, 无强造数据 | — |

## 8. 零触碰验证

| 检查 | 结果 |
|------|------|
| `git diff -- src/` | ✅ 空 |
| `git diff -- docs/ziwei/` | ✅ 空 |
| `git diff -- docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md` | ✅ 空 |
| `git diff -- docs/governance/CAPABILITY_LIFECYCLE.md` | ✅ 空 |
| 新 node_type / relation_type / ref_type | ✅ 未新增 |
| LLM / RAG / 网络依赖 | ✅ 未引入 |
| Ziwei Contract / Golden Vectors / Reference / Production | ✅ 未修改 |

## 9. Phase 7.1.2（Relations Production）入口条件声明

1. **41/41 节点完成** ✅（本 Sprint）
2. Coverage Matrix 已更新 ✅
3. Pipeline/校验/确定性/回归全部通过 ✅
4. 7.1.2 范围（Build Plan）: 新增 12 关系（he +3 / chong +3 / xing +3 / hai +3）
   → 关系总数 24; 端点完整性依赖本 Sprint 41 节点 ✅ 已就绪
5. 待人工 Evidence Review + 授权

---

**本 Sprint 停止。** 不进入 Phase 7.1.2; 不扩展 shen_sha/pattern;
不引入 LLM/RAG; 不修改任何冻结规范。
