# BaZi Test Coverage Review

> **日期**: 2026-08-09（Phase 6.2 Test Coverage Audit）
> **对象**: `tests/test_bazi.py`（11 例）+ `tests/test_determinism.py`（2 例 BaZi）
> **目的**: 分类现有覆盖、识别缺口、列出 Freeze 前必补测试。

---

## 1. 现有覆盖（Existing Coverage）

### 1.1 `tests/test_bazi.py`（11 例）

| 测试 | 覆盖规则 | 类别 |
|------|----------|------|
| `test_year_pillar_1985` | B1（年柱干支 + 索引） | ✅ 年柱基础 |
| `test_month_and_hour_branches` | B2（申月）+ B4（巳时） | ✅ 月/时支基础 |
| `test_day_pillar_sexagenary_parity` | B3（干支奇偶不变式） | ✅ 日柱不变式 |
| `test_lichun_boundary_switches_year` | B1（立春前/后 UTC 边界） | ✅ 年界边界 |
| `test_2300_day_rollover` | B3 + B4（23:00 换日 + 亥/子时） | ✅ 晚子时换日 |
| `test_hidden_stems_and_nayin_present` | 藏干/纳音 | ✅ 存在性（弱断言） |
| `test_ten_gods_against_day_master` | 十神（比肩） | ✅ 十神基础 |
| `test_dayun_count_and_progression` | B5（8 步, +10 岁） | ✅ 大运结构 |
| `test_gender_assumed_flag` | B6（UNKNOWN → assumed） | ✅ 性别回退 |
| `test_bazi_explainer_fallback` | 解释层（**契约化范围外**） | ⚠️ 非计算域 |
| `test_bazi_explainer_pattern_extraction` | 解释层（**契约化范围外**） | ⚠️ 非计算域 |

### 1.2 `tests/test_determinism.py`（BaZi 相关 2 例）

| 测试 | 覆盖 | 类别 |
|------|------|------|
| `test_bazi_replay_identical` | 同输入 ⇒ 同输出（computed_at 除外） | ✅ 确定性（对齐 QC-001） |
| `test_input_hash_stable` | input_hash 稳定 64 位 | ✅ 可审计 |

### 1.3 覆盖小结

| 规则 | 现有覆盖 | 强度 |
|------|----------|------|
| B1 年柱 | 3 例（基础 + 边界） | 中 |
| B2 月柱 | 1 例（仅月支） | **弱**（无月干/五虎遁断言） |
| B3 日柱 | 3 例（parity + 换日） | 中 |
| B4 时柱 | 2 例（巳/亥/子） | **弱**（无五鼠遁时干断言） |
| B5 大运 | 1 例（仅顺运结构） | **弱**（无方向/舍入断言） |
| B6 性别 | 1 例（UNKNOWN 标记） | 中（无 UNKNOWN 方向断言） |

---

## 2. 缺失覆盖（Missing Coverage）

| # | 缺口 | 涉及规则 | 风险 |
|---|------|----------|------|
| G1 | 月干五虎遁（不同年干 → 月干） | B2 | 月柱错误未被测试发现 |
| G2 | 时干五鼠遁（不同日干 → 时干） | B4 | 时柱错误未被测试发现 |
| G3 | 大运顺/逆方向（阳女逆 / 阴男逆 / 阴女顺） | B5 | 方向反转回归无法捕获 |
| G4 | 大运起运舍入（距节 X.5 天, banker's rounding） | B5 | 起运 ±1 岁回归 |
| G5 | 时区差（同刻不同时区 → 日/时柱不同） | B3/B4 | 本地时区逻辑回归 |
| G6 | 无坐标回退路径（无 born_location → 用 born_at.tzinfo） | B3/B4 | 回退路径未锁定 |
| G7 | 节过渡跨月（惊蛰/立秋 ±2h） | B2 | 节界错误 |
| G8 | 立春时区敏感边界（本地 23:xx 立春） | B1 | UTC 判定行为 |
| G9 | 子时 00:xx 五鼠遁时干 | B4 | 子时窗 |
| G10 | 闰月期间日期 | B2（N/A 锁定） | 太阳历无依赖证明 |
| G11 | dayun_count 定制（非 8） | B5 | 可配参数回归 |
| G12 | FEMALE 显式用例（现仅有 MALE/UNKNOWN） | B5/B6 | 女性路径未被直接测试 |

---

## 3. 现有测试中的范围外项（契约化时处理）

| 项 | 说明 |
|----|------|
| `test_bazi_explainer_fallback` / `_pattern_extraction` | 解释层测试（`BaziExplainer`）—— 不属确定性计算域；契约化**保留**（解释层自身回归），但**不纳入** BaZi 计算契约/向量范围 |

---

## 4. Required Additions Before Freeze（Freeze 前必补测试）

依据 `BAZI_GOLDEN_VECTOR_PLAN.md` 24 向量设计, 生成向量前需补充的
**计算域单元测试**（预计 +14 例, 全部为确定性断言）:

| 新增测试（建议命名） | 覆盖缺口 | 关联向量 |
|----------------------|----------|----------|
| `test_month_stem_wuhu_dun_years` | G1 | V-CB-5 |
| `test_hour_stem_wushu_dun_days` | G2 | V-TB-3 |
| `test_dayun_direction_four_combos` | G3 | V-DY-1~4 |
| `test_dayun_rounding_bankers` | G4 | V-DY-6 |
| `test_timezone_changes_pillars` | G5 | V-LC-1/3 |
| `test_no_location_fallback` | G6 | V-LC-2 |
| `test_solar_term_transition_month` | G7 | V-CB-4 |
| `test_lichun_local_midnight_window` | G8 | V-CB-3 |
| `test_zi_hour_stem_early_morning` | G9 | V-TB-3 |
| `test_leap_month_no_effect` | G10 | V-EC-1 |
| `test_dayun_count_custom` | G11 | V-EC-3 |
| `test_female_explicit_direction` | G12 | V-DY-2/3 |
| `test_start_at_feb29_fallback` | —（边界） | V-EC-4 |
| `test_parity_invariant_sweep` | —（不变式） | V-EC-2 |

**追加后预计**: 计算域测试 11 + 14 = **25 例**（另保留 2 例解释层测试,
不计入计算域）。

---

## 5. 结论

- 现有 11 例覆盖四柱/十神/藏干/纳音/大运**结构正确性**与 2 项边界
  （立春/23:00）+ 确定性双跑
- 主要缺口: 五虎遁月干 / 五鼠遁时干 / 大运方向与舍入 / 时区与回退路径
- Freeze 前需 **+14 例**计算域测试（上表）, 与 24 向量计划一一对应
