# BaZi Golden Vector Report

> **Sprint**: Phase 6.3A/6.3B — Golden Vector Generation + Freeze Candidate Preparation
> **日期**: 2026-08-09
> **状态**: Candidate（Freeze Review 前; 状态不升级）
> **数据**: `docs/bazi/golden_vectors.json`（24 向量, engine 0.1.0）
> **测试**: `tests/test_bazi_golden_vectors.py`（7 例, 全部通过）

---

## 1. Coverage Summary

**24 向量已生成**（`docs/bazi/golden_vectors.json`）, 分组:

| 组 | 数量 | 覆盖 |
|----|------|------|
| B_basic_* | 6 | 春夏秋冬 + 日主木（甲/乙）+ 日主金（庚/辛） |
| B_term_* | 6 | 立春前/后（B1）、清明前/后、立冬前/后（B2 节过渡） |
| B_late_* | 3 | 22:59 / 23:00 / 23:30（B3 换日 + B4 子时窗） |
| B_dayun_* | 5 | 顺/逆/UNKNOWN（B5/B6）+ X.5 banker's rounding + 分数天 |
| B_tz_* | 4 | UTC+8 经典例、UTC+0 同时刻、12/31 vs 1/1 年界（B1） |
| **合计** | **24** | 规则覆盖 B1~B6 全 ✅ |

**边界用例全部覆盖**:
- 立春（2024-02-04 前后 ±3h, UTC 判定锁定）
- 清明/立冬 节过渡（月柱切换）
- 晚子时 23:00 换日（22:59 → 亥时当日, 23:00 → 子时次日）
- 大运舍入边界（距节 4.5 天 → days/3=1.5 → round=2; 4 天 → 1.333 → 1）
- 时区（同刻 UTC+8/UTC+0 → 日柱同、时柱异）
- 年界（2023-12-31 与 2024-01-01 均为癸卯年）

**元数据完整**: 24 个唯一 id、每向量 coverage 标注、risk_flagged（仅
B_dayun_003 = True）、`day_rollover_policy: "23:00 local time"`、
`true_solar_time: not used` 记录于 metadata。

---

## 2. Cross-Domain Divergence（显式复述）

| 分歧 | BaZi（本域） | Qimen（契约 v1.0.0） | 处理 |
|------|--------------|----------------------|------|
| 晚子时日柱 | **23:00 换日**（B3, 向量 B_late_002 锁定） | **不换日**（D14 裁定） | 各自独立冻结; 向量中已注明 policy |
| 真太阳时 | **钟表时**（不用, metadata 声明） | **使用**（D13, 有坐标时） | BaZi 时柱按时区钟表时; 未来启用须 ACP |

> 两域行为均为既定实现, 互不影响; 已在
> `BAZI_ALGORITHM_ASSUMPTIONS.md` §3 与向量 metadata 双处记录。

---

## 3. Risk Register

| Risk | Status | Mitigation |
|------|--------|------------|
| 晚子时流派分歧（子初/子正/子时换日） | **Deferred** | 已记录（B3 裁定 + 向量 B_late_001~003 + 跨域对照）; Freeze Review 裁定 |
| 大运算法变体（起运舍入/方向） | **Deferred** | 已记录; `round(x.5)` banker's rounding 显式锁定（B5 + B_dayun_004/005）; 其余变体待 Review |
| UNKNOWN 性别处理 | **Frozen candidate** | B6 已锁定（按男处理 + gender_assumed）; 向量 B_dayun_003 + 测试 test_gender_unknown_locked |
| 节气时刻误差 | **Infrastructure dependency** | Meeus 截断 ~0.01°（<1 分钟, `approx_1min`）; 立春向量 ±3h 远离临界; 持续监控 |
| 时区回退链 | **Implemented** | 已记录于假设文档（born_location → born_at.tzinfo → UTC）; 向量 B_tz_002 覆盖 UTC+0 路径 |

---

## 4. Freeze Candidate 状态（Phase 6.3B）

| 项 | 状态 |
|----|------|
| 24 Golden Vectors | ✅ Candidate（`status: candidate`, `rule_set: draft`） |
| 回归测试 | ✅ 7 例通过（count/determinism/serialization/boundary/coverage/match） |
| 冻结边界 | ✅ `docs/bazi/BAZI_FREEZE_BOUNDARY.md`（IN SCOPE vs DEFERRED） |
| 规则裁定 | ✅ Draft（B1~B6, `BAZI_RULE_DECISION.md`） |
| 算法假设 | ✅ `BAZI_ALGORITHM_ASSUMPTIONS.md` |
| 测试缺口 | ⚠️ `BAZI_TEST_COVERAGE_REVIEW.md` 列出 +14 例 —— **本 Sprint 未补**（计算域单元测试, 待 6.4） |
| 状态升级 | ❌ 不升级（保持 Implemented, 等 Freeze Review） |

---

## 5. 遗留事项（Phase 6.4 Freeze Review 前置）

1. 补计算域单元测试（+14 例, 见 `BAZI_TEST_COVERAGE_REVIEW.md` §4）
2. Freeze Review: 规则一致性（B1~B6 定义→实现→向量覆盖）+ 向量充分性 + 架构边界
3. Review 裁定晚子时 / 大运变体（Deferred 项）
4. 契约草案（对齐 Qimen QC-001~014 结构）
