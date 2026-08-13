# Ziwei Test Coverage Review

> **Sprint**: Phase 7.0 — 测试覆盖审计
> **日期**: 2026-08-09
> **对象**: `tests/test_ziwei.py`（12 例, 唯一 Ziwei 测试文件; `reference/tests/`
> 无 Ziwei 测试）
> **方法**: 逐例分类（单元/边界/集成/smoke）, 标注 Golden Vector 可用性;
> 数字均为真实计数, 无虚构。

---

## 1. 现有测试分类（12 例）

| # | 测试 | 类别 | 断言强度 | Golden Vector 可用性 |
|---|------|------|----------|----------------------|
| 1 | `test_fate_palace_canonical` | 边界/canonical（正月寅时→命宫子, 水二局） | **强**（数值断言） | ✅ 直接升级为向量 V-REF 候选 |
| 2 | `test_body_palace_position` | 边界/canonical（身宫辰） | 强 | ✅ 同上 |
| 3 | `test_all_12_palaces_have_correct_names` | 结构（集合断言） | 中（无位置映射断言） | ⚠️ 需补位置断言 |
| 4 | `test_all_palaces_have_stem_branch` | smoke（仅长度=1） | **弱**（只验证"不报错"） | ❌ |
| 5 | `test_14_major_stars_all_present` | 结构（集合断言） | 中（存在性, 无位置） | ⚠️ 需补位置断言 |
| 6 | `test_ziwei_tianfu_mirror_relationship` | 结构不变式 | 强 | ✅ |
| 7 | `test_lunar_conversion_2024_05_01` | 历法数值 | 强（sxtwl 输出锁定） | ✅（历法依赖锁定） |
| 8 | `test_lunar_conversion_2024_02_10` | 历法数值（春节边界） | 强 | ✅ |
| 9 | `test_lunar_conversion_leap_month_2023` | 历法数值（闰月） | 强 | ✅ |
| 10 | `test_replay_identical` | 确定性 | 强（逐字节） | ✅（QC-001 型） |
| 11 | `test_user_provided_lunar_used_directly` | smoke（仅 `is not None`） | **弱** | ❌ |
| 12 | `test_metadata_updated` | metadata | 强 | ✅（间接） |

**统计**:
- 单元测试: 12（全部在单文件）
- 边界测试: 2（#1 命宫 canonical, #2 身宫 canonical）
- 历法数值测试: 3（#7/8/9）
- 确定性测试: 1（#10）
- 集成测试: 0
- 纯 smoke（只验证不报错）: 2（#4, #11）

---

## 2. 规则覆盖矩阵

| 规则 | 有测试? | 测试强度 |
|------|---------|----------|
| ZW-001 输入定义 | ⚠️ smoke（#11） | 弱 |
| ZW-002 时区解析 | ❌ 无 | — |
| ZW-003 时辰 | 间接（#1 04:00→寅） | 中 |
| ZW-004 农历转换 | ✅ 3 例数值 | 强 |
| ZW-005 年干立春界 | ❌ 无专属（共享原语测试在 BaZi 域） | — |
| ZW-006 五虎遁 | 间接（#1） | 中 |
| ZW-007 命宫 | ✅ #1 | 强 |
| ZW-008 身宫 | ✅ #2 | 强 |
| ZW-009 命宫天干 | 间接（#1 丙子） | 中 |
| ZW-010 五行局 | ⚠️ 仅水二局（#1）; 木三/金四/土五/火六 **零覆盖** | 弱 |
| ZW-011 十二宫 | ✅ #3/#4 | 中-弱 |
| ZW-012 紫微定局 | ❌ 无直接位置断言（仅间接） | — |
| ZW-013 天府镜像 | ✅ #6 | 强 |
| ZW-014 紫微星系 | ⚠️ 存在性（#5） | 中 |
| ZW-015 天府星系 | ⚠️ 存在性（#5） | 中 |
| ZW-016 阴阳 | ❌ 无 | — |
| ZW-017 未实现边界 | ✅ metadata（#12） | 强 |

**完全无测试的规则**: ZW-002（时区）、ZW-005（Ziwei 视角）、ZW-016（阴阳）。

---

## 3. 缺口清单（Freeze 前必补）

| # | 缺口 | 涉及规则 | 建议用例数 |
|---|------|----------|-----------|
| G1 | 五行局全类型（木三/金四/土五/火六 各至少 1 例 canonical） | ZW-010 | 4 |
| G2 | 紫微定局表位置断言（含 30 日边界、跨局抽样） | ZW-012 | 3~5 |
| G3 | 十四主星逐宫位置断言（紫微星系 6 + 天府星系 8, 固定盘全位置核对） | ZW-014/015 | 2（全位置） |
| G4 | 时区差（同一时刻不同时区 → 时辰/农历日不同） | ZW-002/003 | 2 |
| G5 | 无 born_location 回退 + 无效时区 | ZW-002 | 1~2 |
| G6 | 子时窗边（23:00/00:59） | ZW-003 | 1~2 |
| G7 | 显式农历与公历不一致的优先序断言（当前 smoke 弱） | ZW-001 | 1 |
| G8 | 闰月安星策略显式断言（calendar_note + 月号同值） | ZW-004 | 1 |
| G9 | 阴阳字段直接断言 | ZW-016 | 1 |
| G10 | 十二宫名称→位置映射断言（当前仅集合） | ZW-011 | 1 |
| G11 | 立春年界（Ziwei 输入视角, 年干切换） | ZW-005 | 1 |

**合计缺口: 约 17~21 例**。补完后计算域测试预计 29~33 例。

---

## 4. Golden Vector 候选评估

| 可升级为向量的现有测试 | 建议 |
|------------------------|------|
| #1/#2 canonical 例 | ✅ 直接作为基准向量（V-REF） |
| #7/8/9 历法数值 | ✅ 锁定 sxtwl 依赖行为 |
| #6 镜像不变式 | ✅ 结构不变式向量 |
| #10 replay | ✅ 确定性向量 |
| #3/#5 | ⚠️ 需升级为位置断言后使用 |

**向量覆盖维度建议**（对齐 BaZi 24 量级, Phase 7.1 落地）: 五行局 ×5、
定局边界 ×4、时区 ×3、时辰窗 ×2、闰月 ×2、canonical 基准 ×2、历法 ×3、
结构不变式 ×3 = 24。

---

## 5. Phase 6.7.1 补测结果（2026-08-13, 追加章节）

> 依据 §3 缺口清单 G1~G11 补测; **全部确定性, 锁定当前行为, 零 src 修改**。
> `tests/test_ziwei.py`: 12 → **33 例**（+21）。全仓库 578 例全绿。

### 5.1 新增测试清单（21 例）

| # | 新增测试 | 覆盖缺口 | 覆盖规则 |
|---|----------|----------|----------|
| 13 | `test_ziwei_pos_table_structure` | G2 | ZW-012（150 组合存在性 + 值域） |
| 14 | `test_ziwei_pos_values_snapshot` | G2 | ZW-012（SHA-256 快照逐格锁定现行表, 不判断流派正误） |
| 15 | `test_ziwei_tianfu_mirror_multiple_ju` | — | ZW-013（5 局真实盘镜像） |
| 16 | `test_ziwei_xingxi_offsets` | G3 | ZW-014（六星位置断言, 含廉贞 -9 锁定） |
| 17 | `test_tianfu_xingxi_offsets` | G3 | ZW-015（八星位置断言） |
| 18 | `test_palace_stems_follow_wuhu_dun` | — | ZW-006/011（12 宫天干全序） |
| 19 | `test_palace_names_positions_mapping` | G10 | ZW-011（宫名→位置映射） |
| 20 | `test_ming_shen_formula_sweep` | — | ZW-007/008（12 月 × 12 时辰全组合 144 例） |
| 21 | `test_wuxing_ju_all_five_elements` | G1 | ZW-010（真实日期锚点 ×5: 水2/木3/金4/土5/火6） |
| 22 | `test_wuxing_ju_nayin_invariant` | G1 | ZW-010（命宫纳音末字 → 局数不变式） |
| 23 | `test_yin_yang_year_stem` | G9 | ZW-016（甲子年 yang / 乙丑年 yin） |
| 24 | `test_yin_yang_lichun_boundary` | G11 | ZW-005（立春 ±1h 年干切换, Ziwei 视角） |
| 25 | `test_hour_window_boundary_2259_vs_2300` | G6 | ZW-003（22:59 亥 vs 23:00 子: 命宫 6→5, 水二→木三局） |
| 26 | `test_timezone_changes_fate_palace` | G4 | ZW-002/003（同一时刻 UTC+8 vs UTC+0） |
| 27 | `test_no_location_uses_born_tzinfo` | G5 | ZW-002（无坐标回退链） |
| 28 | `test_timezone_invalid_fallback` | G5 | ZW-002（非法时区静默回退） |
| 29 | `test_leap_month_placement_uses_month_number` | G8 | ZW-004（闰二月: calendar_note + 月号同值安星） |
| 30 | `test_user_lunar_override_flows_into_placement` | G7 | ZW-001（显式农历流入定局表） |
| 31 | `test_lunar_day_out_of_range_raises_keyerror` | G7 | ZW-001（越界 KeyError 行为锁定） |
| 32 | `test_aux_stars_always_empty` | — | ZW-017（未实现边界锁定） |
| 33 | `test_output_serialization_roundtrip` | — | 序列化稳定（JSON-safe + ZiweiChart round-trip） |

### 5.2 补测后规则覆盖矩阵（更新）

| 规则 | 补测前 | 补测后 | 强度 |
|------|--------|--------|------|
| ZW-001 输入定义 | ⚠️ smoke | 显式农历流入 + KeyError 锁定（#30/#31） | 中-强（校验策略仍 Deferred） |
| ZW-002 时区解析 | ❌ 无 | #26/#27/#28 | 强 |
| ZW-003 时辰 | 间接 | #25（窗边数值） | 强 |
| ZW-004 农历转换 | ✅ 3 例 | + #29（闰月安星策略） | 强 |
| ZW-005 年干立春界 | ❌ 无专属 | #24（立春 ±1h） | 强 |
| ZW-006 五虎遁 | 间接 | #18（12 宫全序） | 强 |
| ZW-007 命宫 | ✅ | + #20 sweep（144 组合） | 强 |
| ZW-008 身宫 | ✅ | + #20 sweep | 强 |
| ZW-009 命宫天干 | 间接 | #18 同源 | 强 |
| ZW-010 五行局 | ⚠️ 仅水二 | #21（全 5 局）+ #22（不变式） | 强 |
| ZW-011 十二宫 | 中-弱 | #19（位置映射） | 强 |
| ZW-012 紫微定局 | ❌ 无直接断言 | #13/#14（150 组合结构 + SHA-256 快照） | 强（流派裁定仍待人工） |
| ZW-013 天府镜像 | ✅ | + #15（5 局） | 强 |
| ZW-014 紫微星系 | ⚠️ 存在性 | #16（位置断言） | 强（廉贞 -9 待裁定） |
| ZW-015 天府星系 | ⚠️ 存在性 | #17（位置断言） | 强 |
| ZW-016 阴阳 | ❌ 无 | #23 | 强 |
| ZW-017 未实现边界 | ✅ | + #32 | 强 |

### 5.3 补测后剩余缺口（Freeze 前无需再补）

- 序列化跨语言一致性: 无 Rust/Go 实现, 本阶段 N/A（Reference 阶段处理）。
- 定局表/廉贞流派裁定（A-1/A-2）: **不是测试缺口**, 是人工裁定项
  （`ZIWEI_RULE_DECISION.md` §4）。
- 全部 G1~G11 缺口已闭合; 原估计 17~21 例, 实际落地 21 例, 与估计一致。
