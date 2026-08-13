# Ziwei Corpus Pilot Audit（Phase 7.0 Pilot 审计）

> **Sprint**: Phase 7.1.0 — Corpus Scope & Source Freeze
> **日期**: 2026-08-13
> **对象**: Phase 7.0 Pilot（20 nodes / 12 relations / 3 references）
> **原则**: **不修改 Pilot 数据**（保持历史完整性）; 处置为建议,
> 执行发生在 Phase 7.1.1+ 正式化时。

---

## 1. Nodes 审计（20/20）

| ID | 类型 | 符合 Scope | 来源可靠 | Provenance 完整 | Schema 匹配 | 处置 |
|----|------|-----------|----------|-----------------|-------------|------|
| kn:wuxing:mu | wuxing | ✅（第一阶段） | ✅ Tier 1 | ✅（全书/星曜总论） | ✅ | **保留, 第一波** |
| kn:wuxing:huo | wuxing | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:wuxing:tu | wuxing | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:wuxing:jin | wuxing | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:wuxing:shui | wuxing | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:main_star:ziwei | main_star | ✅（14 计划中 1） | ✅ | ✅ | ✅ | 保留, 第一波（待补 9 星） |
| kn:main_star:tianji | main_star | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:main_star:taiyang | main_star | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:main_star:tianfu | main_star | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:main_star:lianzhen | main_star | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:palace:minggong | palace | ✅（12 计划中 1） | ✅ | ✅ | ✅ | 保留, 第一波（待补 7 宫） |
| kn:palace:xiongdi | palace | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:palace:fuqi | palace | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:palace:zinv | palace | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:palace:caibo | palace | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:ten_god:zhengguan | ten_god | ✅（10 计划中 1, 跨系统） | ✅ Tier 1（渊海子平） | ✅ | ✅ | 保留, 第一波（跨系统归属见 GAP-04） |
| kn:ten_god:qisha | ten_god | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:ten_god:zhengyin | ten_god | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:ten_god:pianyin | ten_god | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| kn:ten_god:bijian | ten_god | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |

**Nodes 汇总**: 20/20 保留进入第一波; 0 待补充 provenance; 0 迁移; 0 Schema GAP。

## 2. Relations 审计（12/12）

| ID | 类型 | 符合 Scope | 来源可靠 | Provenance 完整 | Schema 匹配 | 处置 |
|----|------|-----------|----------|-----------------|-------------|------|
| rel:sheng:mu_huo | sheng | ✅（计划 5/5） | ✅ | ✅ | ✅ | 保留, 第一波 |
| rel:sheng:huo_tu | sheng | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| rel:sheng:tu_jin | sheng | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| rel:sheng:jin_shui | sheng | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| rel:sheng:shui_mu | sheng | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| rel:ke:mu_tu | ke | ✅（计划 5/5） | ✅ | ✅ | ✅ | 保留, 第一波 |
| rel:ke:tu_shui | ke | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| rel:ke:shui_huo | ke | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| rel:ke:huo_jin | ke | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| rel:ke:jin_mu | ke | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |
| rel:he:ziwei_tianfu | he | ✅（计划 5 中 1） | ✅（契约 BC-012 + 全书） | ✅ | ✅ | 保留, 第一波（待补 4 同度关系） |
| rel:he:lianzhen_tianfu | he | ✅ | ✅ | ✅ | ✅ | 保留, 第一波 |

**Relations 汇总**: 12/12 保留; 0 待补充; 0 迁移; 0 GAP。
> 注: `rel:he:*` 的 source 引用冻结契约条款（BC-012）为合法 provenance
> （规范优先原则, Admission Policy §3.2）。

## 3. References 审计（3/3）

| ID | 类型 | 符合 Scope | 来源可靠 | Provenance 完整 | Schema 匹配 | 处置 |
|----|------|-----------|----------|-----------------|-------------|------|
| ref:classic:ziwei_quanshu_ziwei | classic_text | ✅（计划 3 中 1） | ✅ Tier 1 | ✅ | ✅ | 保留, 第一波（待补 2 经典引用） |
| ref:school:zhongzhou_minggong | school_commentary | ✅（计划 2 中 1） | ⚠️ 中（Tier 2, 纸质本未授权数字版） | ✅（王亭之/中州派讲义） | ✅ | **保留, 待补充 provenance**（版次/页码登记, 见 GAP-02） |
| ref:oral:lianzhen_tianfu_tongdu | oral_tradition | ✅（计划 2 中 1） | ✅（口诀 + 契约恒等式验证） | ✅ | ✅ | 保留, 第一波 |

**References 汇总**: 2/3 完整保留; 1/3（school:zhongzhou）**待补充 provenance**
（版次信息缺失 → 7.1.3 补登或降级）。

## 4. 审计结论

- **20/20 + 12/12 + 2/3** 直接保留（第一波）; **1 reference** 待补充 provenance。
- Pilot 无 Schema GAP、无越界类型、无 Tier 4 来源。
- Pilot 数据**不修改**；以上处置在 7.1.1 正式化时执行（内容不动, 走查准入流程）。
