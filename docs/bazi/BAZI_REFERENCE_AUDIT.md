# BaZi Reference Audit

> **Sprint**: Phase 6.5 Task C — Reference Contract Audit
> **日期**: 2026-08-09
> **对象**: `reference/bazi/`（domain.py / astronomy.py / tables.py）对
> `docs/bazi/BAZI_BEHAVIOR_CONTRACT.md` v1.0.0 的逐条符合性审计
> **方法**: 逐条 BC-001~014 → 参考行为 → 证据（向量/测试）→ 判定
> **结论**: **PASS** —— 14/14 条款符合（与 Qimen 14/14 QC Full 对齐）

---

## 1. 审计表

### BC-001 Deterministic Output

- **Contract requirement**: 相同输入 ⇒ 字节级相同输出; 无随机/时钟/IO/LLM。
- **Reference behavior**: `compute()` 纯函数; 无随机源; 唯一非纯依赖为
  `zoneinfo.ZoneInfo`（确定性映射表）与 Meeus 数学。
- **Evidence**: `test_equivalence_all_24_vectors`（24/24）; `test_determinism`（golden, 双跑一致）。
- **Verdict**: ✅ PASS

### BC-002 Year Pillar（B1）

- **Contract requirement**: 立春 UTC 时刻比较; 年序 `(立春年-4)%60`。
- **Reference behavior**: `astronomy.bazi_year_index`（与契约条款逐字一致）。
- **Evidence**: 向量 B_term_001（立春前癸卯）/B_term_002（立春后甲辰）/B_tz_003/004; 等价 24/24。
- **Verdict**: ✅ PASS

### BC-003 Month Pillar（B2）

- **Contract requirement**: 12 节月界（非中气）; 月支=节定支; 五虎遁月干; UTC 比较。
- **Reference behavior**: `astronomy.month_boundary_before` + 五虎遁公式。
- **Evidence**: 向量 B_term_003~006（清明卯→辰/立冬戌→亥）; 单元测试五虎遁 ×3。
- **Verdict**: ✅ PASS

### BC-004 Day Pillar（B3）

- **Contract requirement**: `(JDN+49)%60`; **23:00 本地换日**。
- **Reference behavior**: `sexagenary_day_index` + `local.hour >= 23 → +1 day`。
- **Evidence**: 向量 B_late_001/002/003; `test_boundary_regression`。
- **Verdict**: ✅ PASS

### BC-005 Hour Pillar（B4）

- **Contract requirement**: 时支 `((h+1)//2)%12`; 五鼠遁时干; 钟表时; 时干基于换日后日干。
- **Reference behavior**: 与条款一致（`day_idx%10` 用于换日后日干）。
- **Evidence**: 向量 B_late_*（亥→子时）; 单元测试五鼠遁 ×3。
- **Verdict**: ✅ PASS

### BC-006 Ten Gods Mapping

- **Contract requirement**: 五行生克 + 阴阳异同 → 十神; 覆盖柱干 + 藏干。
- **Reference behavior**: `_ten_god` + ten_gods_map 构建（与条款一致）。
- **Evidence**: 向量 ALL（ten_gods 字段, 24/24 等价比对）。
- **Verdict**: ✅ PASS

### BC-007 Hidden Stems

- **Contract requirement**: 固定藏干表（12 支）。
- **Reference behavior**: `tables.BRANCH_HIDDEN_STEMS`（与契约表一致）。
- **Evidence**: 向量 ALL（hidden_stems 字段）; 单元测试存在性断言。
- **Verdict**: ✅ PASS

### BC-008 Na Yin

- **Contract requirement**: 60 组纳音表, 按干支序索引。
- **Reference behavior**: `tables.NAYIN` + `nayin_for`。
- **Evidence**: 向量 ALL（nayin 字段）。
- **Verdict**: ✅ PASS

### BC-009 Da Yun Direction（B5）

- **Contract requirement**: 阳男/阴女顺, 其余逆; ±1 序步进; +10 岁; 默认 8 步。
- **Reference behavior**: `forward` 判定 + `dir_step ±1` + 8 步循环。
- **Evidence**: 向量 B_dayun_001/002; 单元测试顺/逆 ×2。
- **Verdict**: ✅ PASS

### BC-010 Da Yun Start Age（B5）

- **Contract requirement**: `max(0, round(days/3))` 银行家舍入; 距节秒差/86400。
- **Reference behavior**: 与条款一致（Python round = banker's）。
- **Evidence**: 向量 B_dayun_004（4.5 天 → 2）/B_dayun_005（4 天 → 1）。
- **Verdict**: ✅ PASS

### BC-011 Gender UNKNOWN（B6）

- **Contract requirement**: UNKNOWN 按男处理 + `gender_assumed=True`。
- **Reference behavior**: `gender not in (male, female)` → assumed; female 判定仅 `== "female"`。
- **Evidence**: 向量 B_dayun_003（assume=True, 与 male 大运一致）。
- **Verdict**: ✅ PASS

### BC-012 Timezone Policy

- **Contract requirement**: born_location.timezone → born_at.tzinfo → UTC; 静默回退; 节气按 UTC; 换日/时辰按本地。
- **Reference behavior**: `_local_tz` 回退链 + UTC 边界比较（与条款一致）。
- **Evidence**: 向量 B_tz_001/002; 单元测试有效/无效时区。
- **Verdict**: ✅ PASS

### BC-013 Schema Contract

- **Contract requirement**: 输入 BaziInput / 输出 BaziChart 全字段（含 stem_index/branch_index/start_at/boundaries）。
- **Reference behavior**: `compute()` 输出与生产 `model_dump(mode="json")` **结构逐字段一致**（含 pydantic 时间序列化格式 Z/+HH:MM）。
- **Evidence**: `test_equivalence_field_completeness` / `test_equivalence_pillar_fields` / `test_equivalence_dayun_fields`。
- **Verdict**: ✅ PASS

### BC-014 Golden Vectors

- **Contract requirement**: 24 向量为规范装置; 24/24 与引擎逐字节一致。
- **Reference behavior**: 等价测试全部通过。
- **Evidence**: `test_equivalence_all_24_vectors`（24/24 零偏差）; golden 回归 7 例。
- **Verdict**: ✅ PASS

---

## 2. 独立性审计

| 项 | 结果 |
|----|------|
| `reference/bazi/` 源码无 `from/import openmetaphysics` | ✅（`test_reference_source_independent_of_src` 强制） |
| 无 production 依赖 / 无借道 production helper | ✅（仅 stdlib + 本包） |
| 规范移植声明 | ✅ 天文/干支表为契约冻结数据的独立移植（Meeus 同源） |

---

## 3. 审计结论

**PASS** —— 14/14 条款符合（BC-001~014）; 独立性审计通过;
未发现 Reference 与 Contract 不一致, 无需修改契约。
