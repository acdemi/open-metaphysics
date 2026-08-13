# Ziwei Algorithm Assumptions

> **Sprint**: Phase 6.7.1 — Algorithm Stabilization（假设显式化）
> **日期**: 2026-08-13（Phase 6.7.1.5 更新: A-1/A-2/ZW-001/sxtwl 裁定完成）
> **性质**: 记录 `ZiweiEngine` v0.2.0 的每一个确定性假设。**不修改任何算法**;
> 仅显式化既有行为, 供规则裁定（`ZIWEI_RULE_DECISION.md`）与 Golden Vector
> 设计（`ZIWEI_GOLDEN_VECTOR_READINESS.md`）使用。
> **编号**: ZW-A1~ZW-A15, 与 Phase 7.0 规则清单 ZW-001~017 交叉引用。
> **禁止**: 加入当前实现不存在的能力（辅星/四化/大限/流年均不在此表, 由
> ZW-017 显式声明为"未实现"）。
> **Phase 6.7.1.5 裁定同步**: ZW-A10（定局表）与 ZW-A12（廉贞）→ REVISED
> （ACP Required, 未执行）; ZW-A4 补 sxtwl 锁版裁定; ZW-A15 输入校验分层。
> 完整记录: `ZIWEI_DECISION_RESOLUTION.md`。

---

## 假设总表

### ZW-A1 日期/时间输入（对应 ZW-001）

- **Assumption ID**: ZW-A1
- **Name**: 出生时刻必须为 tz-aware datetime
- **Actual Behavior**: `AgentInput.born_at` 校验器拒绝 naive datetime
  （`ValueError: born_at must be timezone-aware`）; 合法输入恒有 tzinfo。
- **Code Evidence**: `core/schemas.py:58-63`
- **Existing Test Evidence**: `test_compute_naive_datetime_422`（API 层, tests/test_api.py:45）;
  Ziwei 专属: 无直接断言（间接经所有用例 tz-aware 构造）
- **Boundary**: naive 输入 → 422（API）/ ValidationError（直调）
- **Risk**: 低 —— 信封级统一校验, 跨域一致
- **Freeze Candidate**: ✅（跨域共享信封行为, 契约化时引用而非重复定义）

### ZW-A2 时区解析链（对应 ZW-002）

- **Assumption ID**: ZW-A2
- **Name**: 本地时区回退链（无 UTC 兜底）
- **Actual Behavior**: `born_location.timezone`（ZoneInfo）→ 解析失败静默
  回退 → `born_at.tzinfo`。**无第三级 UTC 兜底**; 无警告、无 metadata 标记。
- **Code Evidence**: `agents/ziwei.py:268-276`
- **Existing Test Evidence**: 本 Sprint 前无; 已补
  `test_timezone_invalid_fallback` / `test_no_location_uses_born_tzinfo`
- **Boundary**: 无 born_location; 时区字符串非法; `born_location.timezone=None`
- **Risk**: 中 —— 与 BaZi BC-012（有 UTC 兜底）链定义差异（ZB-06）;
  因 born_at 强制 tz-aware, 行为等价, 契约化时须显式声明差异
- **Freeze Candidate**: ✅ 维持现状 + 差异声明

### ZW-A3 时辰划分（对应 ZW-003）

- **Assumption ID**: ZW-A3
- **Name**: 时辰 = 本地钟表时, 子时 23:00~00:59
- **Actual Behavior**: `hour_idx = ((local.hour+1)//2) % 12`（子=0..亥=11）;
  本地民用钟表时; **不使用真太阳时**（`core/solar_time.py` 仅供 Qimen）。
- **Code Evidence**: `agents/ziwei.py:279-281`, `:289-291`
- **Existing Test Evidence**: 间接（canonical 例 04:00 → 寅时）; 已补
  `test_hour_window_boundary_2259_vs_2300` / `test_timezone_changes_fate_palace`
- **Boundary**: 22:59（亥）vs 23:00（子）; 00:59（子）vs 01:00（丑）
- **Risk**: 中 —— 真太阳时流派差异（Qimen D13 使用）; 跨域登记 ZQ-01
- **Freeze Candidate**: ✅（与 BaZi 一致, 与 Qimen 有意差异）

### ZW-A4 农历转换（对应 ZW-004）

- **Assumption ID**: ZW-A4
- **Name**: 公历→农历经 sxtwl, 取本地民用日期; 闰月按月号同值安星
- **Actual Behavior**: `solar_to_lunar(local.year, local.month, local.day)`
  （sxtwl）; leap 月 → `calendar_note = "leap month {m} (闰月) using month
  number {m} for placement"` 且安星月号 = 平月号; 晚子时不换日。
- **Code Evidence**: `agents/ziwei.py:294-303`; `core/calendar.py:174-188`
- **Existing Test Evidence**: 历法数值 ×3（`test_lunar_conversion_*`）; 已补
  `test_leap_month_placement_uses_month_number`
- **Boundary**: 闰月（2023-03-22 → 闰二月）; 春节前后（2024-02-10）;
  sxtwl 版本升级行为漂移
- **Risk**: 高 —— `sxtwl>=1.6` 非精确锁版, compute() 内唯一外部依赖（F-8）;
  闰月策略为项目选择（流派存在"闰月作下月/上月"变体, 见歧义 A-6）
- **Freeze Candidate**: ✅ 维持现状（月号同值）; sxtwl 锁版策略列入契约化前置
- **sxtwl 锁版裁定（Phase 6.7.1.5, D-ZW-9）**: **固定版本 `sxtwl==2.0.7`**
  （环境实测安装版本; 当前声明 `>=1.6` 已跨 1.x→2.x 大版本）。pin 动作随
  ACP 执行（本 Sprint 不修改 pyproject.toml）。验证: 3 例历法数值测试
  （`test_lunar_conversion_*`, 已锁 2.0.7 输出）+ Phase 6.7.2 历法向量
  （ZV-lun-001~003）+ replay。升级须 ACP + 向量迁移。
  详见 `ZIWEI_DECISION_RESOLUTION.md` §5。

### ZW-A5 年干立春界（对应 ZW-005）

- **Assumption ID**: ZW-A5
- **Name**: 年干以立春为界（UTC 时刻比较）, 复用 BaZi 原语
- **Actual Behavior**: `bazi_year_index(born)` → 年序 `(立春年-4)%60`;
  立春前属上年。Ziwei 年干取自**公历立春**, 非农历正月初一。
- **Code Evidence**: `agents/ziwei.py:316`; `core/calendar.py:144-154`
- **Existing Test Evidence**: 共享原语在 BaZi 域有边界测试; Ziwei 视角已补
  `test_yin_yang_lichun_boundary`
- **Boundary**: 立春 ±1h（2024-02-04 立春前后 yin→yang）
- **Risk**: 中 —— 传统紫微多按农历正月初一取年干, 存在流派变体（歧义 A-7）
- **Freeze Candidate**: ✅（跨域共享原语, 契约化时引用 BaZi BC-002）

### ZW-A6 五虎遁（对应 ZW-006）

- **Assumption ID**: ZW-A6
- **Name**: 宫垣天干起法（甲己起丙寅）
- **Actual Behavior**: `yin_month_stem = (year_stem_idx*2+2) % 10`
- **Code Evidence**: `agents/ziwei.py:318`
- **Existing Test Evidence**: 间接（canonical 例 命宫丙子）; 已补
  `test_palace_stems_follow_wuhu_dun`（12 宫全序断言）
- **Boundary**: 10 年干全覆盖由公式保证; 边界 = 立春年切换（ZW-A5）
- **Risk**: 低 —— 主流一致
- **Freeze Candidate**: ✅

### ZW-A7 命宫（对应 ZW-007）

- **Assumption ID**: ZW-A7
- **Name**: 命宫定位公式
- **Actual Behavior**: `ming = ((lunar_month-1) - hour_idx) % 12`
  （PALACE_BRANCHES 空间, 寅=0; 逆数生时）
- **Code Evidence**: `agents/ziwei.py:305-306`
- **Existing Test Evidence**: `test_fate_palace_canonical`; 已补
  `test_ming_shen_formula_sweep`（12 月 × 12 时辰全组合）
- **Boundary**: 月/时全组合; 亥时与子时跨日窗（ZW-A3）
- **Risk**: 低 —— canonical 公式, 主流一致
- **Freeze Candidate**: ✅

### ZW-A8 身宫（对应 ZW-008）

- **Assumption ID**: ZW-A8
- **Name**: 身宫定位公式
- **Actual Behavior**: `shen = ((lunar_month-1) + hour_idx) % 12`（顺数生时）
- **Code Evidence**: `agents/ziwei.py:307`
- **Existing Test Evidence**: `test_body_palace_position`; 已补 sweep（同 ZW-A7）
- **Boundary**: 同 ZW-A7
- **Risk**: 低 —— canonical 公式
- **Freeze Candidate**: ✅

### ZW-A9 五行局（对应 ZW-010）

- **Assumption ID**: ZW-A9
- **Name**: 五行局 = 命宫干支纳音末字映射
- **Actual Behavior**: `nayin_for(ming_stem, ming_branch)[-1]` → 元素 →
  `JU_NUMBER{水2,木3,金4,土5,火6}` → `"{元素}{数}局"`
- **Code Evidence**: `agents/ziwei.py:43`, `:321-328`; `core/models.py:163-228`
- **Existing Test Evidence**: 仅水二局（canonical 例）; 已补
  `test_wuxing_ju_all_five_elements`（真实日期锚点 ×5）+ `test_wuxing_ju_nayin_invariant`
- **Boundary**: 全部 5 元素（水/木/金/土/火）; 命宫干支纳音取值域 = 60 甲子
- **Risk**: 低 —— 主流定局（JU_NUMBER 与主流一致）
- **Freeze Candidate**: ✅

### ZW-A10 紫微定局表（对应 ZW-012）

- **Assumption ID**: ZW-A10
- **Name**: 紫微定位 = 定局表（5 局 × 30 日）
- **Actual Behavior**: `zw = ZIWEI_POS[ju][lunar_day]`; 当前实现为硬编码表,
  与经典《紫微星诀》结构不一致（F-3, 歧义 A-1）。
- **Code Evidence**: `agents/ziwei.py:49-210`, `:351`
- **Existing Test Evidence**: 间接（初一水二局 → 丑）; 已补
  `test_ziwei_pos_table_structure`（150 组合结构）+ `test_ziwei_pos_values_snapshot`
  （SHA-256 快照, 150 组合逐格锁定当前表值）
- **Boundary**: 日 1/30 边界; 各局起始宫; `lunar_day` 越界 KeyError（ZW-001）
- **Risk**: **高** —— 当前表违反"木三无寅卯 / 金四无酉戌 / 土五无辰巳 /
  火六无未申"四项著名结构不变式, 且无统一生成规则
- **Freeze Candidate**: ❌ **REVISED（Phase 6.7.1.5 裁定, ACP Required 未执行）**
  —— 修订为统一生成规则 `idx = (START + (day-1)//STEP) % 12`:
  START={水二:丑(11), 木三:辰(2), 金四:亥(9), 土五:午(4), 火六:酉(7)},
  STEP={水二:2, 木三/金四/土五/火六:3}。修订后全表与证据见
  `ZIWEI_DECISION_RESOLUTION.md` §2

### ZW-A11 天府镜像（对应 ZW-013）

- **Assumption ID**: ZW-A11
- **Name**: 天府定位 = 寅申轴镜像
- **Actual Behavior**: `tf = (-zw) % 12`
- **Code Evidence**: `agents/ziwei.py:352`
- **Existing Test Evidence**: `test_ziwei_tianfu_mirror_relationship`; 已补
  sweep（同 ZW-A10, 150 组合镜像断言）
- **Boundary**: 紫微在寅（镜像自同宫）; 紫微在申（镜像对称）
- **Risk**: 低 —— 主流一致（天府必与紫微寅申轴对称）
- **Freeze Candidate**: ✅（公式锁定; 注意其输入 zw 受 ZW-A10 裁定影响）

### ZW-A12 紫微星系偏移（对应 ZW-014）

- **Assumption ID**: ZW-A12
- **Name**: 六星安星（逆行, 偏移减）
- **Actual Behavior**: 紫微0 / 天机-1 / 太阳-3 / 武曲-4 / 天同-5 / 廉贞**-8**
  （Phase 6.7.1.5 修订后规范; 当前实现仍为 -9, 待 ACP）。
- **Code Evidence**: `agents/ziwei.py:214-221`, `:360-362`（当前 -9）
- **Existing Test Evidence**: 存在性; 已补 `test_ziwei_xingxi_offsets`
  （位置断言, 公式类 —— 读同一模块表, ACP 后自动一致）
- **Boundary**: mod 12 环绕（紫微在寅/亥等边缘宫）
- **Risk**: **高** —— 当前 -9 破坏"紫微在子午, 廉贞天府同度辰戌"著名恒等式
- **Freeze Candidate**: ❌ **REVISED（Phase 6.7.1.5 裁定, ACP Required 未执行）**
  —— 廉贞 = 紫微 **-8**（本项目规范定义为 -8, 而非历史原因）;
  依据: 歌诀隔位结构 + 廉贞天府同宫恒等式。详见
  `ZIWEI_DECISION_RESOLUTION.md` §3

### ZW-A13 天府星系偏移（对应 ZW-015）

- **Assumption ID**: ZW-A13
- **Name**: 八星安星（顺行, 偏移加）
- **Actual Behavior**: 天府0 / 太阴+1 / 贪狼+2 / 巨门+3 / 天相+4 / 天梁+5 /
  七杀+6 / 破军+10。与主流完全一致（含破军 +10 空三格）。
- **Code Evidence**: `agents/ziwei.py:224-233`, `:365-367`
- **Existing Test Evidence**: 存在性; 已补 `test_tianfu_xingxi_offsets`（位置断言）
- **Boundary**: mod 12 环绕
- **Risk**: 低 —— 主流一致（其锚点 tf 受 ZW-A10 裁定影响）
- **Freeze Candidate**: ✅

### ZW-A14 宫位布局（对应 ZW-011 / ZW-009）

- **Assumption ID**: ZW-A14
- **Name**: 十二宫干支/名称/标志
- **Actual Behavior**: 宫 i: 干 `=(yin_month_stem+i)%10`, 支 `=PALACE_BRANCHES[i]`
  （寅起顺行）, 名 `=PALACE_NAMES[(ming-i)%12]`（逆时针排宫: 命宫→父母→福德→…→兄弟）,
  命/身宫标志。
- **Code Evidence**: `agents/ziwei.py:28-42`, `:336-348`
- **Existing Test Evidence**: 名称集合/干支存在性; 已补
  `test_palace_names_positions_mapping` + `test_palace_stems_follow_wuhu_dun`
- **Boundary**: 命宫在任一宫时名称滚动; 干支 mod 10 环绕
- **Risk**: 低 —— 主流一致
- **Freeze Candidate**: ✅

### ZW-A15 隐式默认与未实现边界（对应 ZW-001/ZW-016/ZW-017）

- **Assumption ID**: ZW-A15
- **Name**: 隐式默认值集合 + 未实现能力清单
- **Actual Behavior**:
  1. 显式农历（lunar_month+lunar_day 同时提供）优先于公历转换; 年干仍取公历立春界;
  2. `lunar_day` 越界无校验 → `ZIWEI_POS` KeyError;
  3. `gender` 继承但 engine 从不读取; `yin_yang` 计算但无下游消费;
  4. `auxiliary_stars` 恒空列表; 四化/大限/流年未实现;
  5. 置信度固定 0.95（基类默认）; trace 恒 4 步。
- **Code Evidence**: `agents/ziwei.py:236-238`, `:287-383`;
  `core/engines.py:141-145`（置信度）
- **Existing Test Evidence**: `test_user_provided_lunar_used_directly`（smoke, 已强化）;
  `test_metadata_updated`; 已补 `test_lunar_day_out_of_range_raises_keyerror` /
  `test_aux_stars_always_empty` / `test_yin_yang_year_stem`
- **Boundary**: lunar_day 0/31; 农历与公历不一致的输入组合
- **Risk**: 中 —— 校验缺失（KeyError）为已暴露行为; 已裁定"KeyError 属工程
  意外, 待修复"
- **Freeze Candidate**: ⚠️ 部分 —— 未实现边界（ZW-017）✅; 输入校验策略
  （ZW-001）**REVISED**（Phase 6.7.1.5 裁定: Contract 要求显式校验
  month∈[1,12]/day∈[1,30]/两字段同给同省; 当前实现待修复, ACP Required,
  修复仅影响非法输入路径。详见 `ZIWEI_DECISION_RESOLUTION.md` §4）

---

## 汇总

| 假设 | 主题 | Freeze Candidate |
|------|------|------------------|
| ZW-A1 | tz-aware 输入 | ✅ |
| ZW-A2 | 时区回退链（无 UTC 兜底） | ✅ + 差异声明 |
| ZW-A3 | 钟表时辰 | ✅ |
| ZW-A4 | sxtwl 农历 + 闰月月号同值 | ✅ + 锁版裁定（固定 2.0.7, ACP pin） |
| ZW-A5 | 立春年界（共享原语） | ✅ |
| ZW-A6 | 五虎遁 | ✅ |
| ZW-A7 | 命宫公式 | ✅ |
| ZW-A8 | 身宫公式 | ✅ |
| ZW-A9 | 五行局映射 | ✅ |
| ZW-A10 | 紫微定局表 | ❌ **REVISED**（统一生成规则, ACP） |
| ZW-A11 | 天府镜像 | ✅ |
| ZW-A12 | 紫微星系（廉贞） | ❌ **REVISED**（-8, ACP） |
| ZW-A13 | 天府星系 | ✅ |
| ZW-A14 | 宫位布局 | ✅ |
| ZW-A15 | 默认/未实现边界 | ⚠️ 部分 **REVISED**（输入校验, ACP） |

> 完整裁定与开放问题见 `ZIWEI_RULE_DECISION.md`（Phase 6.7.1, Draft, 未冻结）
> 与 `ZIWEI_DECISION_RESOLUTION.md`（Phase 6.7.1.5 四项裁定）。
