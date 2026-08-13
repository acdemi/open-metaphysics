# Ziwei Corpus Coverage Matrix（覆盖矩阵）

> **Sprint**: Phase 7.1.0 — Corpus Scope & Source Freeze
> **日期**: 2026-08-13
> **状态**: **FROZEN**（目标值）; Pilot 覆盖为现状
> **依据**: `ZIWEI_CORPUS_SCOPE.md`（第一阶段冻结范围）

---

## 1. 节点覆盖矩阵（node_type）

| node_type | 计划节点数（第一波） | 已覆盖（Pilot） | 需新增 | 来源就绪 |
|-----------|---------------------|-----------------|--------|----------|
| wuxing | 5 | 5 | 0 | ✅ Tier 1 |
| main_star | 14 | 5 | 9 | ✅ Tier 1（全书星曜总论; 待逐星核对赋性） |
| palace | 12 | 5 | 7 | ✅ Tier 1（全书十二宫释义） |
| ten_god | 10 | 5 | 5 | ✅ Tier 1（渊海子平论十神） |
| heavenly_stem | 10 | 0 | 10 | ✅ Tier 1（干支基础; 归 7.1.4） |
| earthly_branch | 12 | 0 | 12 | ✅ Tier 1（归 7.1.4） |
| auxiliary_star | 12-15 | 0 | 12-15 | ⚠️ 需来源确认（Tier 2+; GAP-05） |
| shen_sha | 10-20 | 0 | 10-20 | ⚠️ 需来源确认（GAP-05） |
| pattern | 20-50 | 0 | 20-50 | ⚠️ 高争议（SchoolView 多源; A-8） |
| 断事类 ×8（career 等） | 10-20/类 | 0 | — | 🔴 解释域依赖（范围外） |
| 用神类 ×4（yong_shen 等） | 10/类 | 0 | — | 🔴 跨域授权（范围外） |

## 2. 关系覆盖矩阵（relation_type）

| relation_type | 计划关系数（第一波） | 已覆盖 | 需新增 | 来源就绪 |
|---------------|---------------------|--------|--------|----------|
| sheng | 5 | 5 | 0 | ✅ |
| ke | 5 | 5 | 0 | ✅ |
| he | 5 | 2 | 3 | ⚠️ 需确认（星曜同度恒等式, 契约 BC-012 + 全书） |
| chong | 3 | 0 | 3 | ⚠️ 需确认（地支六冲, 归 7.1.2） |
| xing | 3 | 0 | 3 | ⚠️ 需确认（地支三刑） |
| hai | 3 | 0 | 3 | ⚠️ 需确认（地支六害） |
| yinyong | 5 | 0 | 5 | ✅（引用关系, 随 references 建立） |
| shuyu | 5 | 0 | 5 | ✅（星曜属五行/宫位归属） |
| 其余 ×7（fuzhu/zhiyue/duiying/yingxiang/zengqiang/xueroo/zhixiang） | — | 0 | — | 🔴 后续阶段（解释域/断事） |

## 3. 引用覆盖矩阵（ref_type）

| ref_type | 计划引用数（第一波） | 已覆盖 | 需新增 | 来源就绪 |
|----------|---------------------|--------|--------|----------|
| classic_text | 3 | 1 | 2 | ⚠️ 需获取（紫微斗数全集 Tier 1; GAP-01） |
| school_commentary | 2 | 1 | 1 | ⚠️ 需确认（中州派版次; GAP-02） |
| modern_interpretation | 1 | 0 | 1 | ⚠️ 需获取（iztro MIT 已调研） |
| oral_tradition | 2 | 1 | 1 | ✅（口诀类, 契约恒等式验证） |

---

## 4. 汇总

| 类别 | 计划（第一波） | Pilot 已覆盖 | 缺口 |
|------|---------------|-------------|------|
| nodes | 41（wuxing/main_star/palace/ten_god） | 20 | 21 |
| relations | 24（sheng/ke/he/chong/xing/hai） | 12 | 12 |
| references | 8（3/2/1/2） | 3 | 5 |

> 干支（22 节点）+ 其余关系/引用在 7.1.4 扩展与后续阶段按 Scope/GAP 推进。
