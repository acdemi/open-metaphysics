# Ziwei Rule Inventory

> **Sprint**: Phase 7.0 — 规则盘点（内部清单, **不代表冻结**）
> **日期**: 2026-08-09
> **方法**: 从 `src/openmetaphysics/agents/ziwei.py` 实际提取（非模板套用;
> 不使用 Qimen QC / BaZi B 编号）
> **说明**: Freeze Candidate 列 = 是否具备进入契约化的规范候选条件（需
> Phase 7.1+ 裁定确认, 本阶段不冻结）

---

## 规则清单

### ZW-001 输入定义

- **Rule Name**: Ziwei 输入信封
- **Current Behavior**: `ZiweiInput(AgentInput)` + `lunar_month/lunar_day: int|None`（1..12 / 1..30; None → 公历自动转农历）
- **Source Code Evidence**: `agents/ziwei.py:236-238`
- **Existing Test Evidence**: `test_user_provided_lunar_used_directly`（smoke, 弱）
- **Deterministic?**: ✅
- **Boundary Cases**: 显式农历与公历不一致（未测试）; lunar_day > 30（未校验, 定局表 KeyError 风险 —— 已暴露为开放问题）
- **Freeze Candidate?**: ✅ 需补输入校验裁定
- **Open Decision**: 显式农历优先序 + 越界值校验策略

### ZW-002 时区解析

- **Rule Name**: 本地时区回退链
- **Current Behavior**: `born_location.timezone`（ZoneInfo）→ `born_at.tzinfo`; **无 UTC 兜底**（与 BaZi BC-012 差异, 因 born_at 强制 tz-aware, 行为等价但链定义不同）
- **Source Code Evidence**: `agents/ziwei.py:268-276`
- **Existing Test Evidence**: 无（Asia/Shanghai 单一时区）
- **Deterministic?**: ✅
- **Boundary Cases**: 无效时区（未测试）; 无 born_location（未测试）
- **Freeze Candidate?**: ⚠️ 需测试锁定
- **Open Decision**: 是否对齐 BaZi 静默回退语义

### ZW-003 时辰定义

- **Rule Name**: 时辰支（钟表时）
- **Current Behavior**: `((local.hour+1)//2) % 12`; 子时 = 23:00~00:59; **不使用真太阳时**
- **Source Code Evidence**: `agents/ziwei.py:279-281`
- **Existing Test Evidence**: 间接（test_fate_palace_canonical 04:00 → 寅时）
- **Deterministic?**: ✅
- **Boundary Cases**: 23:00/00:59 子时窗边（未测试）
- **Freeze Candidate?**: ✅
- **Open Decision**: 真太阳时（与 BaZi 一致不采用; Qimen 采用 —— 跨域差异, 见 PRECHECK）

### ZW-004 农历转换

- **Rule Name**: 公历→农历（sxtwl）
- **Current Behavior**: `solar_to_lunar(local.year, local.month, local.day)` —— **本地民用日期**转换; 闰月 → `calendar_note` 记录 + **按月号同值安星**
- **Source Code Evidence**: `agents/ziwei.py:294-303`; `core/calendar.py:174-188`
- **Existing Test Evidence**: `test_lunar_conversion_2024_05_01` / `_2024_02_10` / `_leap_month_2023`（3 例数值断言）
- **Deterministic?**: ✅（依赖 sxtwl 版本固定输出）
- **Boundary Cases**: 闰月安星策略（月号同值, 未显式裁定）; 23:00 后本地日期与民用日（无换日逻辑）
- **Freeze Candidate?**: ⚠️ 需 sxtwl 版本绑定裁定
- **Open Decision**: 闰月流派策略; sxtwl 依赖版本锁定（**编译库, compute() 内唯一外部依赖**）

### ZW-005 年干（立春界）

- **Rule Name**: 年柱干支（复用 BaZi B1 原语）
- **Current Behavior**: `bazi_year_index(born)` —— 立春 UTC 时刻比较, 年序 `(立春年-4)%60`
- **Source Code Evidence**: `agents/ziwei.py:316`
- **Existing Test Evidence**: 间接（无立春边界 Ziwei 专属测试）
- **Deterministic?**: ✅
- **Boundary Cases**: 立春前后（未测试, 与原语共享 BaZi 测试覆盖）
- **Freeze Candidate?**: ✅（跨域共享原语, 契约化时引用而非重复定义）
- **Open Decision**: 是否声明"引用 BaZi BC-002 原语"

### ZW-006 五虎遁

- **Rule Name**: 宫垣天干起法
- **Current Behavior**: `yin_month_stem = (year_stem_idx*2+2) % 10`（甲己起丙寅）
- **Source Code Evidence**: `agents/ziwei.py:318`
- **Existing Test Evidence**: 间接（test_fate_palace_canonical 甲年 → 命宫丙子）
- **Deterministic?**: ✅
- **Freeze Candidate?**: ✅
- **Open Decision**: 无

### ZW-007 命宫

- **Rule Name**: 命宫定位
- **Current Behavior**: `ming = ((lunar_month-1) - hour_idx) % 12`（PALACE_BRANCHES 空间, 寅=0）
- **Source Code Evidence**: `agents/ziwei.py:306`
- **Existing Test Evidence**: `test_fate_palace_canonical`（正月寅时 → 命宫子 ✅ 断言）
- **Deterministic?**: ✅
- **Boundary Cases**: 12 月/亥时 等全月时组合（未测试）
- **Freeze Candidate?**: ✅
- **Open Decision**: 无（canonical 公式）

### ZW-008 身宫

- **Rule Name**: 身宫定位
- **Current Behavior**: `shen = ((lunar_month-1) + hour_idx) % 12`
- **Source Code Evidence**: `agents/ziwei.py:307`
- **Existing Test Evidence**: `test_body_palace_position`（正月寅时 → 身宫辰 ✅）
- **Deterministic?**: ✅
- **Freeze Candidate?**: ✅
- **Open Decision**: 无

### ZW-009 命宫天干

- **Rule Name**: 命宫干支
- **Current Behavior**: `ming_stem = (yin_month_stem + ming_index) % 10`; 支 = PALACE_BRANCHES[ming_index]
- **Source Code Evidence**: `agents/ziwei.py:322-324`
- **Existing Test Evidence**: 间接（test_fate_palace_canonical 断言 丙子 → 涧下水）
- **Deterministic?**: ✅
- **Freeze Candidate?**: ✅
- **Open Decision**: 无

### ZW-010 五行局

- **Rule Name**: 五行局定法
- **Current Behavior**: 命宫干支纳音末字 → 元素 → `JU_NUMBER{水2,木3,金4,土5,火6}` → `"{元素}{数}局"`
- **Source Code Evidence**: `agents/ziwei.py:325-328`; `JU_NUMBER` 表
- **Existing Test Evidence**: `test_fate_palace_canonical`（水二局 ✅）
- **Deterministic?**: ✅
- **Boundary Cases**: 仅覆盖水二局; 其余 4 局（木三/金四/土五/火六）**零测试**
- **Freeze Candidate?**: ⚠️ 需全 5 局测试
- **Open Decision**: 无（主流定局）

### ZW-011 十二宫布局

- **Rule Name**: 宫位干支/名称/标志
- **Current Behavior**: 宫 i: 干=`(yin_month_stem+i)%10`, 支=PALACE_BRANCHES[i], 名=`PALACE_NAMES[(ming-i)%12]`, 命/身宫标志
- **Source Code Evidence**: `agents/ziwei.py:336-348`
- **Existing Test Evidence**: `test_all_12_palaces_have_correct_names` / `test_all_palaces_have_stem_branch`（后者仅长度 smoke）
- **Deterministic?**: ✅
- **Freeze Candidate?**: ✅（需补宫名位置断言, 现仅集合断言）
- **Open Decision**: 无

### ZW-012 紫微定局

- **Rule Name**: 紫微星定位（查表）
- **Current Behavior**: `zw = ZIWEI_POS[ju][lunar_day]`（2~6 局 × 1~30 日 canonical 表）
- **Source Code Evidence**: `agents/ziwei.py:49-210`（全表）+ `:351`
- **Existing Test Evidence**: 间接（test_fate_palace_canonical 初一水二局 → 丑; 无直接位置断言）
- **Deterministic?**: ✅
- **Boundary Cases**: 30 日边界 / 各局序（未直接断言）
- **Freeze Candidate?**: ✅（canonical 表, 需向量锁定全表行为）
- **Open Decision**: 表来源校对（推荐 全 150 组合 = 5 局 × 30 日 逐格向量覆盖或抽样 24）

### ZW-013 天府镜像

- **Rule Name**: 天府定位（寅申轴对称）
- **Current Behavior**: `tf = (-zw) % 12`
- **Source Code Evidence**: `agents/ziwei.py:352`
- **Existing Test Evidence**: `test_ziwei_tianfu_mirror_relationship`（结构断言 ✅）
- **Deterministic?**: ✅
- **Freeze Candidate?**: ✅
- **Open Decision**: 无

### ZW-014 紫微星系（逆行）

- **Rule Name**: 六星安星
- **Current Behavior**: 紫微0/天机-1/太阳-3/武曲-4/天同-5/廉贞-9（偏移减, mod 12）
- **Source Code Evidence**: `agents/ziwei.py:214-221`, `:360-362`
- **Existing Test Evidence**: `test_14_major_stars_all_present`（仅存在性, **无位置断言**）
- **Deterministic?**: ✅
- **Freeze Candidate?**: ⚠️ 需位置断言向量
- **Open Decision**: 无（canonical 偏移）

### ZW-015 天府星系（顺行）

- **Rule Name**: 八星安星
- **Current Behavior**: 天府0/太阴+1/贪狼+2/巨门+3/天相+4/天梁+5/七杀+6/破军+10（偏移加, mod 12）
- **Source Code Evidence**: `agents/ziwei.py:224-233`, `:365-367`
- **Existing Test Evidence**: 同 ZW-014（存在性）
- **Deterministic?**: ✅
- **Freeze Candidate?**: ⚠️ 需位置断言向量
- **Open Decision**: 无

### ZW-016 阴阳

- **Rule Name**: 年干阴阳标记
- **Current Behavior**: `yin_yang` 字段 = 年干阴阳（"yang"/"yin"）
- **Source Code Evidence**: `agents/ziwei.py:319`
- **Existing Test Evidence**: 无直接断言
- **Deterministic?**: ✅
- **Freeze Candidate?**: ✅（低风险）
- **Open Decision**: 无

### ZW-017 未实现能力（显式边界）

- **Rule Name**: 辅星/杂曜/四化/大限/流年 + gender 未使用
- **Current Behavior**: `auxiliary_stars` 恒空列表; **gender 输入继承但 engine 从未读取**; metadata `star_placement="14_major_stars"`
- **Source Code Evidence**: `agents/ziwei.py:396-403`; engine 全文无 `payload.gender`
- **Existing Test Evidence**: `test_metadata_updated`
- **Deterministic?**: ✅（恒定空输出）
- **Freeze Candidate?**: ✅ 冻结"未实现"状态为契约边界声明
- **Open Decision**: gender 未来用途（四化/大限方向, 后续授权）; 辅星/四化加入需 ACP

---

## 汇总

| 类别 | 数量 |
|------|------|
| 已实现且确定性 | 17 条（ZW-001~017） |
| Freeze Candidate 直接合格 | 11 条（ZW-003/005/006/007/008/009/011/012/013/016/017） |
| Freeze Candidate 需补测试/裁定 | 6 条（ZW-001 输入校验、ZW-002 时区、ZW-004 sxtwl/闰月、ZW-010 全 5 局、ZW-014/015 位置断言） |
| 开放裁定点 | 6 项（显式农历优先序与校验、时区回退语义、闰月策略、sxtwl 版本绑定、真太阳时跨域、gender 未使用声明） |
