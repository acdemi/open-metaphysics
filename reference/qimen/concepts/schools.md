# 概念：流派差异记录（Schools）

> **强制项**: 本域所有流派差异必须显式记录于此。
> **规范选择**: 以 [QIMEN_BEHAVIOR_CONTRACT.md](../../../docs/specification/QIMEN_BEHAVIOR_CONTRACT.md)
> v1.0.0 (Frozen) 为准；替代流派仅供记录与未来 ACP 参考，**不实现**。

| # | 主题 | 规范选择（契约 v1.0.0） | 替代流派 | 记录位置 |
|---|------|--------------------------|----------|----------|
| S1 | 三元划分 | **日号近似**（1-10/11-20/21-30 → +0/+3/+6），D2 Option A | 拆补法（符头+超神接气）、置闰法、茅山法 | [dundun_ju.md](dundun_ju.md)、QC-004、QIMEN_D2_IMPACT_ANALYSIS.md |
| S2 | 排盘法 | **转盘法**（天盘/八门/八神顺布） | 飞盘法（星门神飞布，跳中宫） | [plates.md](plates.md)、[stars_doors_gods.md](stars_doors_gods.md) |
| S3 | 值使排法 | **随时支**：本宫起阳顺/阴逆，步数 `(时支-旬首支)mod12` | 值使随时干；按宫位定序数法 | [zhifu_zhishi.md](zhifu_zhishi.md)、QC-008 |
| S4 | 八神方向 | **顺布**（阴阳遁同向） | 阴遁八神逆布（少数派） | [stars_doors_gods.md](stars_doors_gods.md)、QC-011 |
| S5 | 天禽处理 | **参与转盘**（9 宫 ↔ 9 星一一对应） | 天禽永远寄坤二宫与天芮同宫 | [stars_doors_gods.md](stars_doors_gods.md)、QC-009 |
| S6 | 中宫寄宫方向 | **寄坤二宫** | 寄艮八宫（罕见） | [void_central.md](void_central.md)、QC-014 |
| S7 | 晚子时 | **不换日柱**（23:00-24:00 时支=子，当日） | 晚子时换次日日柱 | [zhifu_zhishi.md](zhifu_zhishi.md)、QC-004 语义 |
| S8 | 空亡基准 | **时柱旬空** | 日柱旬空、年柱旬空 | [void_central.md](void_central.md)、QC-013 |

## 差异影响分级

| 级 | 主题 | 替换影响 |
|----|------|----------|
| 高 | S1 三元 | 全部盘面（局数→地盘→天盘→值符值使→星门神三奇）；契约主版本递增 v2.0.0 |
| 中 | S3 值使、S4 八神、S6 寄宫方向 | 对应盘面层（门/神/中宫向量） |
| 低 | S2 转盘/飞盘、S5 天禽、S7 晚子时、S8 空亡基准 | 对应盘面层或边界输入 |

## 变更纪律

任何流派改判：**ACP → 契约版本流程（契约 §6）→ 向量迁移 → 全量回归**。
禁止在本层静默实现替代流派。
