# Ziwei Source Registry（来源登记与分级）

> **Sprint**: Phase 7.1.0 — Corpus Scope & Source Freeze
> **日期**: 2026-08-13
> **状态**: **FROZEN**
> **规则**: Tier 4 来源不得作为正式语料的唯一依据；版权/可获取性问题明确标记。
> 来源引用以 `sources/ziwei/source_XX.yaml` 为正式登记物（本表为治理视图）。

---

## Tier 1 — 经典原文（classic_text）

| source_id | title | attribution | source_type | school_view | acquisition_status | provenance | reliability_note |
|-----------|-------|-------------|-------------|-------------|--------------------|------------|------------------|
| source_ziwei_01 | 紫微斗数全书 | 题「陈抟（希夷）」传；罗洪先辑（明） | classic_text | 南派三合（星曜体系主干） | 已登记（原文未入库, 章节引用） | 通行古籍本（public domain 范围） | 高: 星曜/宫位/五行生克权威出处; 星曜赋性部分流派注记多, 以原文为据 |
| source_ziwei_02 | 紫微斗数全集 | 明清刻本（作者归属存疑） | classic_text | 南派三合 | 待获取（扫描本质量参差） | 待确认版本 | 中: 与全书互补; 部分章节错漏, 需校对（见 GAP-01） |
| source_bazi_01 | 渊海子平 | 徐升（宋）；杨淙增校 | classic_text | 子平 | 已登记（mymmscs/books txt 镜像） | https://github.com/mymmscs/books | 高: 十神/生克权威出处（跨系统共享概念） |

## Tier 2 — 流派注释 / 整理（school_commentary）

| source_id | title | attribution | source_type | school_view | acquisition_status | provenance | reliability_note |
|-----------|-------|-------------|-------------|-------------|--------------------|------------|------------------|
| source_ziwei_03 | 中州派紫微斗数讲义 | 王亭之（陆斌兆系） | school_commentary | 中州派 | 待确认（纸质本, 无授权数字版） | 出版社/版次待登记 | 中: 体系化教学文本; 与南派差异须 SchoolView 保留（见 GAP-02） |
| source_ziwei_04 | 现代整理本（待定, 如佛光山版） | 待确认 | school_commentary | — | 待获取 | 待登记 | 待审查后定级 |

## Tier 3 — 现代研究 / 摘要（modern_interpretation）

| source_id | title | attribution | source_type | school_view | acquisition_status | provenance | reliability_note |
|-----------|-------|-------------|-------------|-------------|--------------------|------------|------------------|
| source_ziwei_05 | iztro（紫微斗数开源引擎文档/规则摘要） | SylarLong | modern_interpretation | 南派为主 | 已调研（GitHub, MIT） | https://github.com/SylarLong/iztro (4.1k★, MIT) | 中: 结构化规则摘要便于交叉验证; 属现代整理, 不得作为经典语义的唯一依据 |
| source_ziwei_06 | 学术论文（候选, 待检索） | 待确认 | modern_interpretation | — | 待获取 | 待登记 | 待审查 |

## Tier 4 — 不可确认来源

| 描述 | 处置 |
|------|------|
| 各类网络转载/公众号摘录（无版本、无归属） | **待审查**, 不得进入正式 Corpus（Admission Policy 禁止） |
| 二手转述且无法回溯原文者 | 同上 |

---

## 关键约束

1. **Tier 4 禁用**: 不作为任何条目唯一依据；仅可作交叉参考线索。
2. **版权**: 古籍原文（Tier 1, public domain）引用允许；现代文本（Tier 2/3）
   仅引段落级摘要 + provenance，不复制全文。
3. **登记闭环**: 每个新增来源必须先入本表（或 sources/*.yaml）再入 Corpus；
   入库顺序: 登记 → 审查 → 引用。
