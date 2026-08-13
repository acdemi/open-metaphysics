# Ziwei Golden Vector Readiness

> **Sprint**: Phase 6.7.1 — Golden Vector 候选设计（**不生成最终向量**）
> **日期**: 2026-08-13
> **性质**: Phase 6.7.2（Golden Vector Generation）的输入设计。本 Sprint 只做
> 候选选择与覆盖矩阵; **不创建 normative `golden_vectors.json`**。
> **对齐**: BaZi 24 向量量级（`docs/bazi/BAZI_GOLDEN_VECTOR_PLAN.md` 模式）;
> Phase 7.0 建议（TEST_COVERAGE_REVIEW §4）: 五行局 ×5、定局边界 ×4、时区 ×3、
> 时辰窗 ×2、闰月 ×2、canonical ×2、历法 ×3、结构不变式 ×3 = 24。

---

## 1. 候选向量矩阵（24）

### V-ZW-REF 基准（4）

| # | ID | 输入 | 断言维度 | 依据 |
|---|----|------|----------|------|
| 1 | ZV-ref-001 | 1900-01-29 04:00+08:00, 显式农历 1/1 | 命宫=子(10), 身宫=辰(2), 水二局, 十四主星全盘位置, 十二宫干支/名称 | `test_fate_palace_canonical` 强化版（F-9 注释勘误后） |
| 2 | ZV-ref-002 | 1985-08-15 10:00+08:00 | 命宫/身宫/木三局/阴阳=阴（乙丑年）/ 全盘主星 | 新测试 `test_wuxing_ju_all_five_elements` 锚点之一 |
| 3 | ZV-ref-003 | 2024-02-05 04:00+08:00 | 火六局 + 全盘 | 5 局锚点 |
| 4 | ZV-ref-004 | 2024-06-06 04:00+08:00 | 木三局 + 全盘 | 5 局锚点 |

### V-ZW-JU 五行局全类型（5）

| # | ID | 输入（+08:00, 04:00） | 期望局 |
|---|----|-----------------------|--------|
| 5 | ZV-ju-001 | 2024-01-01 | 水2局 |
| 6 | ZV-ju-002 | 2024-06-06 | 木3局 |
| 7 | ZV-ju-003 | 2024-10-03 | 金4局 |
| 8 | ZV-ju-004 | 2024-08-04 | 土5局 |
| 9 | ZV-ju-005 | 2024-02-05 | 火6局 |

> 锚点日期为 sxtwl 真实转换结果（本 Sprint 实测, 见 ALGORITHM_AUDIT F-11）;
> 生成向量时须逐字段记录全盘 JSON, 而非仅局名。

### V-ZW-POS 定局表边界（4）

| # | ID | 维度 | 候选输入 |
|---|----|------|----------|
| 10 | ZV-pos-001 | 日边界 1/30 | 显式农历 day=1 与 day=30（同局对照） |
| 11 | ZV-pos-002 | 局间对照（水/木） | 同 day 不同局（选真实日期锚点构造） |
| 12 | ZV-pos-003 | 局间对照（金/土/火） | 同上 |
| 13 | ZV-pos-004 | 用户农历覆盖路径 | 显式 lunar_month/day → 紫微位置 = ZIWEI_POS[ju][day] |

> ⚠️ **A-1 裁定依赖（Phase 6.7.1.5 已解决）**: ZW-012 裁定 **REVISED** ——
> 本组向量按**修订后表**（统一生成规则）生成, 且必须在 ACP 执行完成后采样;
> ACP 前不生成任何全盘向量。

### V-ZW-TZ 时区（3）

| # | ID | 输入 | 断言 |
|---|----|------|------|
| 14 | ZV-tz-001 | 同一时刻 UTC+8 vs UTC+0 | 时辰/命宫不同（本地时语义锁定） |
| 15 | ZV-tz-002 | 无 born_location | 回退 born_at.tzinfo（与显式同 tz 结果一致） |
| 16 | ZV-tz-003 | 非法时区字符串 | 静默回退（D-ZW-2 行为） |

### V-ZW-HOUR 时辰窗（2）

| # | ID | 输入 | 断言 |
|---|----|------|------|
| 17 | ZV-hour-001 | 22:59 vs 23:00（同日同地） | 亥/子切换 → 命宫差 1 宫 |
| 18 | ZV-hour-002 | 00:59 vs 01:00 | 子/丑切换 |

### V-ZW-LUNAR 历法（5）

| # | ID | 输入 | 断言 |
|---|----|------|------|
| 19 | ZV-lun-001 | 2024-05-01 → 农历 3/23 | sxtwl 数值锁定 |
| 20 | ZV-lun-002 | 2024-02-10 → 正月初一（春节） | 边界锁定 |
| 21 | ZV-lun-003 | 2023-03-22 → 闰二月（leap） | calendar_note + 月号同值安星 |
| 22 | ZV-lun-004 | 立春 ±1h（2024-02-04） | yin_yang 切换（年干边界, 共享原语） |
| 23 | ZV-lun-005 | 晚子时 23:30（同日对照） | 不换日行为锁定（A-3 裁定后转规范） |

### V-ZW-INV 结构不变式（1 组, 抽样 3）

| # | ID | 断言 |
|---|----|------|
| 24 | ZV-inv-* | (a) 十四主星总位置一致性（zw+offset 公式, mod 12）; (b) 天府镜像; (c) replay 逐字节 |

---

## 2. 与测试的映射（Phase 6.7.2 生成前全部就位）

| 向量组 | 对应已存在/新增测试 | 状态 |
|--------|---------------------|------|
| V-ZW-REF | `test_fate_palace_canonical` + 新全盘断言 | ✅ 就位 |
| V-ZW-JU | `test_wuxing_ju_all_five_elements` | ✅ 就位 |
| V-ZW-POS | `test_ziwei_pos_values_snapshot`（150 组合 SHA-256） | ✅ 就位（ACP 后重生成快照） |
| V-ZW-TZ | `test_timezone_*` ×3 | ✅ 就位 |
| V-ZW-HOUR | `test_hour_window_boundary_2259_vs_2300` | ✅ 就位 |
| V-ZW-LUNAR | `test_lunar_conversion_*` + `test_leap_month_*` + `test_yin_yang_lichun_boundary` | ✅ 就位 |
| V-ZW-INV | replay / mirror / offsets 测试 | ✅ 就位 |

---

## 3. 生成前置条件（Phase 6.7.2 入口）

> **Phase 6.7.1.5 裁定同步（2026-08-13）**: 前置条件 1 已裁定（REVISED）——
> ZV-pos 组**按修订后表**生成（统一生成规则 + 廉贞 -8）; 但 ACP 未执行,
> **向量生成必须等待 ACP 完成**（见 `ZIWEI_DECISION_RESOLUTION.md` §6）。

1. ~~人工裁定 A-1/A-2~~ ✅ **已裁定（REVISED）**; ⛔ **ACP 执行**（表替换 +
   廉贞 -8 + ZW-001 校验 + sxtwl pin）必须在向量生成前完成。
2. sxtwl 锁版（D-ZW-9: 固定 `sxtwl==2.0.7`）—— 已裁定, pin 随 ACP 执行;
   向量含历法数值, pin 是向量稳定的前提。
3. 向量格式对齐 BaZi: engine 版本 + status=candidate + 逐字段全盘 JSON。
4. 机器回归测试文件 `tests/test_ziwei_golden_vectors.py`（对齐 BaZi 7 例模式）。

## 4. 本 Sprint 明确不做

- ❌ 不生成 `docs/ziwei/golden_vectors.json`
- ❌ 不生成 `reference/ziwei/`
- ❌ 不冻结任何向量
