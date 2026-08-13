# Ziwei Rule Decision

> **Sprint**: Phase 6.7.1 — 规则裁定（Draft, **不代表冻结**）
> **日期**: 2026-08-13
> **模式**: 对齐 BaZi `BAZI_RULE_DECISION.md`（Phase 6.2 同型工件）与 Qimen
> `QIMEN_RULE_DECISION.md` 裁定模式。
> **编号**: 沿用 Phase 7.0 清单 `ZIWEI_RULE_INVENTORY.md` 的 ZW-001~017
> （内部清单编号, 冻结后转契约条款编号）。
> **裁定原则**: 本 Sprint **不改变算法** —— 裁定 = "将当前行为声明为契约
> 候选规范"。存在未决歧义的规则 → Deferred, 不强推冻结。
> **状态机**: Draft → Freeze Candidate → FROZEN（仅 Phase 6.7.3 Freeze Review
> 后可达 FROZEN）。

---

## 1. 规则清单总览

| Rule | 主题 | 裁定 | 状态 |
|------|------|------|------|
| ZW-001 | 输入规范（显式农历优先 + 校验缺口） | 维持现状（含 KeyError 行为锁定） | **Deferred**（校验策略未裁定） |
| ZW-002 | 时区解析链 | 维持现状 + 声明与 BaZi BC-012 差异 | Freeze Candidate |
| ZW-003 | 时辰（钟表时, 子时 23:00~00:59） | 维持现状 | Freeze Candidate |
| ZW-004 | 农历转换（sxtwl + 闰月月号同值） | 维持现状 + sxtwl 锁版为契约化前置 | Freeze Candidate |
| ZW-005 | 年干立春界（共享 BaZi 原语） | 维持现状（引用而非重复定义） | Freeze Candidate |
| ZW-006 | 五虎遁 | 维持现状 | Freeze Candidate |
| ZW-007 | 命宫公式 | 维持现状 | Freeze Candidate |
| ZW-008 | 身宫公式 | 维持现状 | Freeze Candidate |
| ZW-009 | 命宫天干 | 维持现状 | Freeze Candidate |
| ZW-010 | 五行局映射 | 维持现状（全 5 局测试已补） | Freeze Candidate |
| ZW-011 | 十二宫布局 | 维持现状（位置断言已补） | Freeze Candidate |
| ZW-012 | 紫微定局表 | **候选裁定: 维持现状**; 表与主流歌诀差异未决 | **Deferred**（A-1 待人工裁定） |
| ZW-013 | 天府镜像 | 维持现状 | Freeze Candidate |
| ZW-014 | 紫微星系（廉贞 -9） | **候选裁定: 维持现状**; 偏移差异未决 | **Deferred**（A-2 待人工裁定） |
| ZW-015 | 天府星系 | 维持现状 | Freeze Candidate |
| ZW-016 | 阴阳标记 | 维持现状（测试已补） | Freeze Candidate |
| ZW-017 | 未实现能力边界 | 维持现状（冻结"未实现"声明） | Freeze Candidate |

**汇总**: Freeze Candidate 14 条（其中 ZW-002/004 带注记）; Deferred 3 条
（ZW-001/012/014）; FROZEN 0 条。

---

## 2. 规则裁定明细

### ZW-001 输入规范

- **Definition**: `ZiweiInput(AgentInput)` + `lunar_month/lunar_day: int|None`;
  显式农历（两字段同时提供）优先于公历转换; 年干仍取公历立春界。
- **Current Implementation**: `agents/ziwei.py:236-238`, `:295-303`;
  无范围校验（`lunar_day=31` → `ZIWEI_POS[ju][day]` KeyError）。
- **Existing Evidence**: `test_user_provided_lunar_used_directly`（smoke, 已强化）;
  新增 `test_lunar_day_out_of_range_raises_keyerror`（锁定当前 KeyError 行为）;
  `test_user_lunar_override_flows_into_placement`。
- **Candidate Decision**: 维持现状 —— 显式农历优先 + 越界 KeyError 直抛
  （当前行为即候选规范）。
- **Open Question**: (a) KeyError 是否可接受（建议契约化时补显式校验, 属
  ACP 变更）; (b) 显式农历与公历日期不一致时无一致性告警, 是否接受。
- **Status**: **Deferred**（校验策略未裁定）

### ZW-002 时区解析链

- **Definition**: 本地时区 = `born_location.timezone`（ZoneInfo）→ 失败/缺失
  回退 `born_at.tzinfo`; **无 UTC 兜底**; 静默回退（无警告/标记）。
- **Current Implementation**: `agents/ziwei.py:268-276`
- **Existing Evidence**: 新增 `test_timezone_invalid_fallback` /
  `test_no_location_uses_born_tzinfo` / `test_timezone_changes_fate_palace`。
- **Candidate Decision**: 维持现状; 契约化时**显式声明**与 BaZi BC-012
  （有 UTC 兜底）的链定义差异（ZB-06, 行为等价因 born_at 强制 tz-aware）。
- **Open Question**: 是否在未来对齐 BaZi 补 UTC 兜底（须 ACP）; 静默回退是否
  需要 metadata 标记。
- **Status**: **Freeze Candidate**（带注记）

### ZW-003 时辰定义

- **Definition**: `hour_idx = ((local.hour+1)//2) % 12`; 子时 = 23:00~00:59;
  钟表时; 不使用真太阳时。
- **Current Implementation**: `agents/ziwei.py:279-281`
- **Existing Evidence**: canonical 例（04:00→寅时）; 新增
  `test_hour_window_boundary_2259_vs_2300`。
- **Candidate Decision**: 维持现状 —— 钟表时 + 该时辰窗为候选规范;
  真太阳时显式不采用（与 Qimen D13 有意差异）。
- **Open Question**: 无（晚子时换日属 ZW-004/跨域 ZB-01, 与时辰窗本身无关）。
- **Status**: **Freeze Candidate**

### ZW-004 农历转换

- **Definition**: 公历→农历经 sxtwl（`sxtwl>=1.6`）, 取**本地民用日期**;
  闰月按月号同值安星 + `calendar_note`; 晚子时不换日（农历日 = 民用日）。
- **Current Implementation**: `agents/ziwei.py:294-303`; `core/calendar.py:174-188`
- **Existing Evidence**: 历法数值 ×3; 新增 `test_leap_month_placement_uses_month_number`。
- **Candidate Decision**: 维持现状 —— 闰月"月号同值"为候选规范（流派变体
  见歧义 A-6）; 契约化时**必须**将 sxtwl 精确锁版 + 历法数值向量纳入规范
  回归（F-8）。
- **Open Question**: sxtwl 锁版策略（精确 pin vs 范围 + 向量回归）;
  闰月"同值安星"是否最终裁定。
- **Status**: **Freeze Candidate**（带注记: sxtwl 锁版为契约化前置）

### ZW-005 年干立春界

- **Definition**: 年干以立春为界（UTC 时刻比较）, 年序 `(立春年-4)%60`;
  复用 BaZi B1 原语（共享, 非重复实现）。
- **Current Implementation**: `agents/ziwei.py:316`; `core/calendar.py:144-154`
- **Existing Evidence**: 共享原语 BaZi 域边界测试; 新增 Ziwei 视角
  `test_yin_yang_lichun_boundary`（立春 ±1h yin→yang）。
- **Candidate Decision**: 维持现状; 契约化时**引用** BaZi BC-002 原语而非重复定义。
- **Open Question**: 传统紫微多按农历正月初一取年干（歧义 A-7）—— 是否
  显式声明"本项目紫微年干随 BaZi 立春界"。
- **Status**: **Freeze Candidate**

### ZW-006 五虎遁

- **Definition**: `yin_month_stem = (year_stem_idx*2+2) % 10`（甲己起丙寅）。
- **Current Implementation**: `agents/ziwei.py:318`
- **Existing Evidence**: canonical 例（命宫丙子）; 新增
  `test_palace_stems_follow_wuhu_dun`（12 宫全序）。
- **Candidate Decision**: 维持现状。
- **Open Question**: 无。
- **Status**: **Freeze Candidate**

### ZW-007 命宫

- **Definition**: `ming = ((lunar_month-1) - hour_idx) % 12`（寅=0, 逆数生时）。
- **Current Implementation**: `agents/ziwei.py:305-306`
- **Existing Evidence**: `test_fate_palace_canonical`; 新增
  `test_ming_shen_formula_sweep`（12×12 全组合）。
- **Candidate Decision**: 维持现状。
- **Open Question**: 无。
- **Status**: **Freeze Candidate**

### ZW-008 身宫

- **Definition**: `shen = ((lunar_month-1) + hour_idx) % 12`（顺数生时）。
- **Current Implementation**: `agents/ziwei.py:307`
- **Existing Evidence**: `test_body_palace_position`; sweep（同 ZW-007）。
- **Candidate Decision**: 维持现状。
- **Open Question**: 无。
- **Status**: **Freeze Candidate**

### ZW-009 命宫天干

- **Definition**: `ming_stem = (yin_month_stem + ming_index) % 10`。
- **Current Implementation**: `agents/ziwei.py:322-324`
- **Existing Evidence**: canonical 例（丙子 → 涧下水）; 五虎遁全序断言
  （ZW-006 新测试同源）。
- **Candidate Decision**: 维持现状。
- **Open Question**: 无。
- **Status**: **Freeze Candidate**

### ZW-010 五行局

- **Definition**: 命宫干支纳音末字 → `JU_NUMBER{水2,木3,金4,土5,火6}` →
  `"{元素}{数}局"`。
- **Current Implementation**: `agents/ziwei.py:43`, `:325-328`
- **Existing Evidence**: 水二局 canonical; 新增 `test_wuxing_ju_all_five_elements`
  （5 真实日期锚点, 见 ALGORITHM_AUDIT F-11）+ `test_wuxing_ju_nayin_invariant`。
- **Candidate Decision**: 维持现状（主流定局, 无流派歧义）。
- **Open Question**: 无。
- **Status**: **Freeze Candidate**

### ZW-011 十二宫布局

- **Definition**: 宫 i: 干 `=(yin_month_stem+i)%10`, 支 `=PALACE_BRANCHES[i]`,
  名 `=PALACE_NAMES[(ming-i)%12]`, 命/身宫标志。
- **Current Implementation**: `agents/ziwei.py:336-348`
- **Existing Evidence**: 名称集合/干支存在性; 新增
  `test_palace_names_positions_mapping`。
- **Candidate Decision**: 维持现状。
- **Open Question**: 无。
- **Status**: **Freeze Candidate**

### ZW-012 紫微定局表 ⚠️

- **Definition**: `zw = ZIWEI_POS[ju][lunar_day]`（硬编码 5×30 查表）。
- **Current Implementation**: `agents/ziwei.py:49-210`, `:351`。
- **Existing Evidence**: 新增 `test_ziwei_pos_table_structure` +
  `test_ziwei_pos_full_sweep`（150 组合逐格锁定当前表值）。
- **Candidate Decision**: **候选裁定 = 维持现状**（当前表即候选规范）;
  但表与主流《紫微星诀》存在系统性差异（F-3/歧义 A-1: 仅水二局一致,
  木三/金四/土五/火六的起宫与步长均不同）, 属**必须人工确认的流派裁定**。
- **Open Question**: (a) 当前表是有意变体（哪一流派）还是缺陷;
  (b) 若裁定修正 → ACP + 表替换 + 全部相关向量迁移; (c) 若裁定维持 →
  显式写入契约并声明与主流差异。
- **Status**: **Deferred**（待人工裁定; 当前行为已被测试逐格锁定,
  无论裁定方向, 证据均可用）

### ZW-013 天府镜像

- **Definition**: `tf = (-zw) % 12`（寅申轴对称）。
- **Current Implementation**: `agents/ziwei.py:352`
- **Existing Evidence**: `test_ziwei_tianfu_mirror_relationship`; sweep
  （150 组合镜像断言）。
- **Candidate Decision**: 维持现状。
- **Open Question**: 无（锚点 zw 受 ZW-012 裁定影响, 公式本身无歧义）。
- **Status**: **Freeze Candidate**

### ZW-014 紫微星系（廉贞 -9）⚠️

- **Definition**: 紫微0 / 天机-1 / 太阳-3 / 武曲-4 / 天同-5 / 廉贞-9（mod 12）。
- **Current Implementation**: `agents/ziwei.py:214-221`, `:360-362`
- **Existing Evidence**: 新增 `test_ziwei_xingxi_offsets`（六星位置断言）。
- **Candidate Decision**: **候选裁定 = 维持现状**; 但廉贞 -9 与主流 -8
  相差一宫（F-4/歧义 A-2）, 属必须人工确认的流派裁定。
- **Open Question**: 同 ZW-012（维持或 ACP 修正; 修正影响全部紫微在盘位置）。
- **Status**: **Deferred**（待人工裁定）

### ZW-015 天府星系

- **Definition**: 天府0 / 太阴+1 / 贪狼+2 / 巨门+3 / 天相+4 / 天梁+5 /
  七杀+6 / 破军+10（mod 12）。与主流完全一致。
- **Current Implementation**: `agents/ziwei.py:224-233`, `:365-367`
- **Existing Evidence**: 新增 `test_tianfu_xingxi_offsets`（八星位置断言）。
- **Candidate Decision**: 维持现状。
- **Open Question**: 无（锚点 tf 受 ZW-012 裁定影响）。
- **Status**: **Freeze Candidate**

### ZW-016 阴阳标记

- **Definition**: `yin_yang = "yang" if 年干阳 else "yin"`（`STEM_YIN_YANG` 表）。
- **Current Implementation**: `agents/ziwei.py:319`
- **Existing Evidence**: 新增 `test_yin_yang_year_stem`（甲子年 yang / 乙丑年 yin）。
- **Candidate Decision**: 维持现状。
- **Open Question**: 无（字段当前无下游消费, 属 ZW-017 边界的接口预留）。
- **Status**: **Freeze Candidate**

### ZW-017 未实现能力边界

- **Definition**: 辅星/杂曜/四化/大限/流年**未实现**; `auxiliary_stars` 恒空;
  `gender` 继承但 engine 从不读取; metadata `star_placement="14_major_stars"`。
- **Current Implementation**: `agents/ziwei.py:386-411`; engine 全文无
  `payload.gender` 引用（已核实）。
- **Existing Evidence**: `test_metadata_updated`; 新增 `test_aux_stars_always_empty`。
- **Candidate Decision**: 维持现状 —— 契约化时以"未实现边界"条款冻结
  （任何新增能力须 ACP）。
- **Open Question**: gender/yin_yang 未来用途（四化/大限, 后续授权）。
- **Status**: **Freeze Candidate**

---

## 3. 规则稳定化结果（Step 9 汇总）

| 类别 | 规则 | 数量 |
|------|------|------|
| **Freeze Candidate** | ZW-002*, ZW-003, ZW-004*, ZW-005, ZW-006, ZW-007, ZW-008, ZW-009, ZW-010, ZW-011, ZW-013, ZW-015, ZW-016, ZW-017 | 14（*带注记） |
| **Deferred** | ZW-001（校验策略）, ZW-012（定局表流派）, ZW-014（廉贞偏移） | 3 |
| **FROZEN** | — | 0 |

> 冻结时机: Phase 6.7.3 Freeze Review（需人工裁定 A-1/A-2/ZW-001 后）。
> Deferred 规则当前行为**已被测试锁定**, 裁定结果不影响证据完整性。

---

## 4. 领域内部歧义登记（Step 6）

### A-1 紫微定局表与主流《紫微星诀》系统性差异（ZW-012）

- **当前实现**: 硬编码 `ZIWEI_POS` 表: 水二局起丑两日一宫; 木三局起寅
  两日一宫; 金四局起丑三日一宫; 土五局起丑三日一宫; 火六局起丑四日一宫。
- **潜在变体**: 主流歌诀: 水二起丑、木三起辰、金四起亥、土五起午、火六
  起酉, 步长 = 局数（每 N 日行一宫）。
- **裁决要求**: 本项目必须决定"当前表是否成为规范"（不预设外部正误）。
- **影响面**: 4/5 局的紫微定位 → 天府镜像 → 十四主星全盘位置。
- **证据**: 150 组合逐格锁定测试已就位（`test_ziwei_pos_full_sweep`）。

### A-2 廉贞偏移 -9 vs 主流 -8（ZW-014）

- **当前实现**: 廉贞 = 紫微 -9（mod 12）。
- **潜在变体**: 主流: 廉贞 = 紫微 -8（例: 紫微在子 → 主流廉贞在辰与天府
  同宫; 当前实现廉贞在卯）。
- **裁决要求**: 同 A-1, 显式裁定。
- **影响面**: 廉贞所在宫位（六星中唯一差异）。

### A-3 晚子时无换日（跨域 ZB-01, 域内同样未裁定）

- **当前实现**: 农历日 = 本地民用日期（sxtwl）; 23:00 后不换日。
- **潜在变体**: 子初换日（23:00, BaZi B3 模式）; 子正换日（0:00）。
- **裁决要求**: 契约化时转为显式裁定（当前为"无该逻辑"的隐性行为）。

### A-4 时区回退链无 UTC 兜底（ZB-06）

- **当前实现**: `location.tz → born_at.tzinfo`, 静默。
- **潜在变体**: BaZi BC-012 三级链（+UTC）; 回退时告警/标记。
- **裁决要求**: 声明差异（本 Sprint 已裁定: 维持现状 + 声明）。

### A-5 sxtwl 版本绑定（F-8）

- **当前实现**: `sxtwl>=1.6` 范围依赖; 3 例历法数值测试锁定当前输出。
- **潜在变体**: 精确 pin; 版本升级须向量回归 + ACP。
- **裁决要求**: 契约化前确定锁版策略。

### A-6 闰月安星策略

- **当前实现**: 闰月月号与平月同值安星 + calendar_note。
- **潜在变体**: 闰月作下月; 闰月作上月; 闰月专用盘。
- **裁决要求**: 维持"同值"为候选规范（ZW-004 已裁定方向）。

### A-7 年干取立春 vs 农历正月初一

- **当前实现**: 立春界（复用 BaZi 原语, ZW-005）。
- **潜在变体**: 传统紫微多按农历正月初一取年干/年支。
- **裁决要求**: 契约化时显式声明"随 BaZi 立春界"（本项目选择）。

### A-8 格局识别链路断裂（解释域, F-1/F-2）

- **当前实现**: `match_patterns` 死代码（模块遮蔽）; `ZiweiChart` 无
  `patterns` 字段; `ZiweiExplainer` 引用不存在字段且未接线。
- **潜在变体**: 修复接线（engine 输出 patterns / 或解释层独立计算）——
  属解释域, 不在计算域契约范围内。
- **裁决要求**: 后续解释域 Sprint 决策; 本 Sprint 仅记录。

---

## 5. 候选裁定记录（供 Phase 6.7.3 Freeze Review 引用）

| 裁定 | 内容 | 状态 |
|------|------|------|
| D-ZW-1 | 显式农历优先于公历; 年干仍取公历立春界（两条时间语义并存为规范） | 候选（待确认） |
| D-ZW-2 | 时区回退链维持现状（无 UTC 兜底）, 与 BaZi BC-012 差异显式声明 | 候选 |
| D-ZW-3 | 钟表时 + 子时 23:00~00:59, 不使用真太阳时 | 候选 |
| D-ZW-4 | 闰月月号同值安星 + calendar_note; sxtwl 锁版为契约化前置 | 候选 |
| D-ZW-5 | 年干立春界（引用 BaZi BC-002 原语） | 候选 |
| D-ZW-6 | 定局表/廉贞偏移维持现状或 ACP 修正 —— **待人工裁定（A-1/A-2）** | 待裁定 |
| D-ZW-7 | 未实现能力（辅星/四化/大限/流年/gender）冻结为边界声明 | 候选 |

---

## 6. Evidence Ledger 观察记录（Step 12）

> 项目无独立 Evidence Ledger 工件（Qimen E014 以代码注释形式记录）;
> 本 Sprint 观察记录在此登记, Phase 6.7.2 生成 Golden Vector 时引用。

| 日期 | Observation | Hypothesis | 状态 |
|------|-------------|------------|------|
| 2026-08-13 | Ziwei Algorithm Stabilization completed: 17 规则登记, 14 Freeze Candidate / 3 Deferred, +21 确定性测试（12→33, 全绿）, 11 项发现（F-1~F-11） | Ziwei can follow the same Capability Lifecycle as Qimen and BaZi | 记录（Hypothesis ≠ 证明） |
| 2026-08-13 | 定局表 4/5 局与主流歌诀差异（A-1）+ 廉贞偏移（A-2）为冻结前必须人工裁定的仅有两个计算域歧义 | 裁定"维持现状"或"ACP 修正"均可用既有 150 组合证据回归 | 待裁定 |
