# Ziwei Corpus Coverage Matrix（覆盖矩阵）

> **Sprint**: Phase 7.1.0 — Corpus Scope & Source Freeze
> **日期**: 2026-08-13
> **状态**: **FROZEN**（目标值）; Pilot 覆盖为现状
> **依据**: `ZIWEI_CORPUS_SCOPE.md`（第一阶段冻结范围）

---

## 1. 节点覆盖矩阵（node_type）

| node_type | 计划节点数（第一波） | 已覆盖（Phase 7.1.1 后） | 需新增 | 来源就绪 |
|-----------|---------------------|-----------------|--------|----------|
| wuxing | 5 | **5** ✅ | 0 | ✅ Tier 1 |
| main_star | 14 | **14** ✅（Pilot 5 + 7.1.1 新增 9: 武曲/天同/太阴/贪狼/巨门/天相/天梁/七杀/破军; 武曲/贪狼含中州派 SchoolView） | 0 | ✅ Tier 1 + Tier 2 |
| palace | 12 | **12** ✅（Pilot 5 + 7.1.1 新增 7: 疾厄/迁移/奴仆/官禄/田宅/福德/父母） | 0 | ✅ Tier 1 |
| ten_god | 10 | **10** ✅（Pilot 5 + 7.1.1 新增 5: 劫财/食神/伤官/正财/偏财） | 0 | ✅ Tier 1（渊海子平） |
| heavenly_stem | 10 | 0 | 10 | ✅ Tier 1（干支基础; 归 7.1.4） |
| earthly_branch | 12 | 0 | 12 | ✅ Tier 1（归 7.1.4） |
| auxiliary_star | 12-15 | 0 | 12-15 | ⚠️ 需来源确认（Tier 2+; GAP-05） |
| shen_sha | 10-20 | 0 | 10-20 | ⚠️ 需来源确认（GAP-05） |
| pattern | 20-50 | 0 | 20-50 | ⚠️ 高争议（SchoolView 多源; A-8） |
| 断事类 ×8（career 等） | 10-20/类 | 0 | — | 🔴 解释域依赖（范围外） |
| 用神类 ×4（yong_shen 等） | 10/类 | 0 | — | 🔴 跨域授权（范围外） |

> **第一波节点 41/41 已全部完成**（Phase 7.1.1, 2026-08-13）。

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

| 类别 | 计划（第一波） | 已覆盖（Phase 7.1.1 后） | 缺口 |
|------|---------------|-------------|------|
| nodes | 41（wuxing/main_star/palace/ten_god） | **41** ✅ | 0 |
| relations | 24（sheng/ke/he/chong/xing/hai） | 12 | 12（Phase 7.1.2） |
| references | 8（3/2/1/2） | 3 | 5（Phase 7.1.3） |

> 干支（22 节点）+ 其余关系/引用在 7.1.4 扩展与后续阶段按 Scope/GAP 推进。
