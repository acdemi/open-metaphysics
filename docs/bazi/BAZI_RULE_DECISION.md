# BaZi Rule Decision

> **状态**: **Draft** — 未冻结（Phase 6.2 规则裁定准备）
> **日期**: 2026-08-09
> **模式**: 对齐 Qimen `QIMEN_RULE_DECISION.md`（D1~D14 结构）
> **范围**: 仅确定性排盘（四柱/十神/藏干/纳音/大运）
> **规则集版本**: 0.1.0（`BaziEngine.version`）
> **裁定原则**: 本 Sprint **不改变算法** —— 裁定即"将当前行为声明为
> 契约候选规范"，与 Qimen D2（近似为规范）同性质。

---

## 1. 规则清单总览

| Rule | 主题 | 裁定 | 状态 |
|------|------|------|------|
| B1 | 年柱边界（立春, UTC 比较） | 维持现状（UTC 判定为规范） | Draft |
| B2 | 月柱（12 节 + 五虎遁, UTC 比较） | 维持现状 | Draft |
| B3 | 日柱（JDN+49, 23:00 换日） | 维持现状（含跨域分歧声明） | Draft |
| B4 | 时柱（子时 23:00~00:59 + 五鼠遁, 钟表时） | 维持现状（不使用真太阳时） | Draft |
| B5 | 大运（顺逆 + round(days/3) 起运） | 维持现状（banker's rounding 为规范） | Draft |
| B6 | 性别 UNKNOWN 回退 | 维持现状（按男处理 + gender_assumed） | Draft |

---

## 2. 规则裁定明细

### B1 年柱边界

- **Definition**: 年柱以立春为界。`born_at >= lichun_time(year)`（UTC 时刻）→ 年干序 = `(year-4)%60`；否则属上一年。
- **Current implementation**: `core/calendar.py::bazi_year_index`；测试 `test_lichun_boundary_switches_year`（UTC 输入, 2024-02-04 0:00/9:00 跨界）。
- **Decision**: 维持现状 —— UTC 时刻判定为**既定规范**。
- **Alternatives**: 本地时区判定（边界 ±数小时内结果不同）；农历正月初一年界（民俗派, 非子平）。
- **Replaceability**: 中 —— 改动需重写 `bazi_year_index` + 全量向量迁移；当前无修复必要。
- **Golden Vector impact**: 需要 **立春前/后 2 向量**（含时区敏感边界 1 向量）。

### B2 月柱 / 节气

- **Definition**: 月界 = 12 节（立春/惊蛰/清明/立夏/芒种/小暑/立秋/白露/寒露/立冬/大雪/小寒），`BAZI_MONTH_BOUNDARIES` 表（节名, 黄经, 月支索引）；月支 = 节定支；月干 = 五虎遁 `(年干×2+2+(月支-2))%10`；边界 UTC 比较。
- **Current implementation**: `core/calendar.py::month_boundary_before` + `agents/bazi.py` 月柱段；测试仅断言月支（1985-08-15 → 申月）。
- **Decision**: 维持现状 —— 12 节 + 五虎遁为**既定规范**。
- **Alternatives**: 中气分月（少数派）；节令按本地时区折算。
- **Replaceability**: 低 —— 主流子平一致。
- **Golden Vector impact**: 需**节气过渡 3 向量**（惊蛰/立秋/小寒跨节 ±2h）+ 五虎遁月干 3 向量（不同年干）。

### B3 日柱

- **Definition**: 干支日序 = `(JDN + 49) % 60`；**23:00 本地时间换日**（`local.hour >= 23` → 次日）。
- **Current implementation**: `core/calendar.py::sexagenary_day_index` + `agents/bazi.py` 日柱段（`eff = local + 1day if hour>=23`）；测试 `test_2300_day_rollover` + `test_day_pillar_sexagenary_parity`。
- **Decision**: 维持现状 —— 23:00 换日为**既定规范**（与 Qimen D14 跨域分歧, 各自独立声明）。
- **Alternatives**: 0:00 换日；子正换日；不换日（= Qimen D14）。
- **Replaceability**: 高（流派分歧敏感）—— 但当前测试已锁定，变更须 ACP + 全量迁移。
- **Golden Vector impact**: 需**晚子时 2 向量**（23:00 前/后, 跨域对照注释）+ 日柱序 1 向量。

### B4 时柱

- **Definition**: 时支 = `((local.hour+1)//2)%12`（子时 = 23:00~00:59）；时干 = 五鼠遁 `(日干×2+时支)%10`；钟表时（**不用真太阳时**）。
- **Current implementation**: `agents/bazi.py` 时柱段；测试仅断言 巳时/亥/子（`test_month_and_hour_branches`, `test_2300_day_rollover`）。
- **Decision**: 维持现状 —— 钟表时 + 五鼠遁为**既定规范**；真太阳时显式不采用（与 Qimen D13 分歧）。
- **Alternatives**: 真太阳时定时辰（Qimen 模式）；子初/子正两派。
- **Replaceability**: 中 —— 若未来启用真太阳时须 ACP。
- **Golden Vector impact**: 需**五鼠遁时干 3 向量**（不同日干×时辰）+ 时辰窗边 1 向量。

### B5 大运

- **Definition**: 顺逆 = 阳年男/阴年女顺，其余逆；起运 = `max(0, round(距节天数/3))`（Python banker's rounding, .5 取偶）；每步 +10 年；默认 8 步（`dayun_count`）；`start_at` = `local + n年`（2/29 → 2/28）。
- **Current implementation**: `agents/bazi.py::_dayun`；测试 `test_dayun_count_and_progression`（仅顺运男, 未断言方向/舍入）。
- **Decision**: 维持现状 —— banker's rounding 与 3 天=1 年为**既定规范**（显式声明, 对齐 Qimen D2 近似裁定模式）。
- **Alternatives**: 四舍五入（.5 进 1）；余数弃位；按精确分数年。
- **Replaceability**: 中 —— 舍入差异仅在边界（.5 天 ±1 岁）, 向量锁定即可。
- **Golden Vector impact**: 需**顺/逆各 2 向量 + UNKNOWN 1 向量 + 舍入边界 1 向量**（±1 岁敏感用例）。

### B6 性别 / UNKNOWN

- **Definition**: `Gender.UNKNOWN` 在大运方向判定按**非女**（男）处理；输出 `gender_assumed=True`。
- **Current implementation**: `agents/bazi.py`（`female = gender == FEMALE`；`gender_assumed=(payload.gender==UNKNOWN)`）；测试 `test_gender_assumed_flag`。
- **Decision**: 维持现状 —— UNKNOWN 按男处理 + 显式标记为**既定规范**。
- **Alternatives**: UNKNOWN 报错拒绝；UNKNOWN 默认顺运。
- **Replaceability**: 低 —— 回退行为无歧义。
- **Golden Vector impact**: 需 **UNKNOWN 1 向量**（与 MALE 输出对照, 断言 gender_assumed）。

---

## 3. 契约化前置条件

1. B1/B2 UTC 边界比较、B3 晚子时换日、B4 钟表时、B5 banker's rounding、
   B6 UNKNOWN 回退 —— 全部裁定"维持现状"（本 Sprint 完成, Draft）
2. Golden Vectors 草案设计（`docs/bazi/BAZI_GOLDEN_VECTOR_PLAN.md`）
3. 测试缺口补齐（`docs/bazi/BAZI_TEST_COVERAGE_REVIEW.md` §4）
4. Freeze Review → 契约草案（Phase 6.3）

> **冻结政策预告**: 本裁定为 Draft。任何规则变更须 ACP + 规则集版本递增
> + Golden Vector 迁移（对齐 `CAPABILITY_LIFECYCLE.md` §5）。
