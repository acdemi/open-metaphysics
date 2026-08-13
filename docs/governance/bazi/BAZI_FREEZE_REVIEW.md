# BaZi Freeze Review

> **Sprint**: Phase 6.4 — Freeze Review & Rule Finalization
> **日期**: 2026-08-09
> **结论**: **PASS** —— B1~B6 全部 FROZEN（正式冻结, 裁定记录见 §2/§3）
> **三工件对照**: 定义 `docs/bazi/BAZI_ALGORITHM_ASSUMPTIONS.md` /
> 实现 `src/openmetaphysics/agents/bazi.py` + `core/calendar.py` / 证据
> `docs/bazi/golden_vectors.json`（24）+ `tests/test_bazi_units.py`（14 新增）

> **实现位置更正**: 任务书引用 `src/openmetaphysics/domain/bazi/core.py` 不存在
> （src 下仅 `domain/qimen/`）。BaZi 实现实际位于
> `src/openmetaphysics/agents/bazi.py`（引擎）+ `src/openmetaphysics/core/
> calendar.py`（历法）。按约束不修改 src，评审针对实际路径进行。

---

## 1. Freeze Review Table（Task B）

| Rule | Definition Aligns? | Implementation Aligns? | Vectors Cover? | Unit Tests Cover? | Verdict |
|------|--------------------|------------------------|----------------|-------------------|---------|
| **B1** 年柱（立春 UTC 边界） | ✅ | ✅ `bazi_year_index` | ✅ B_term_001/002, B_tz_003/004 | ✅ 五虎遁边界断言 + `test_lichun_boundary_switches_year` | **FROZEN** |
| **B2** 月柱（12 节 + 五虎遁） | ✅ | ✅ `month_boundary_before` + 五虎遁公式 | ✅ B_term_003~006, B_basic_* | ✅ 五虎遁 ×3（甲己→丙寅 / 乙庚→戊寅 / 丙辛→庚寅 + 立春前边界） | **FROZEN** |
| **B3** 日柱（JDN+49, 23:00 换日） | ✅ | ✅ `sexagenary_day_index` + 23:00 rollover | ✅ B_late_001~003 | ✅ `test_2300_day_rollover` + golden boundary 回归 | **FROZEN** |
| **B4** 时柱（五鼠遁, 钟表时, 时区回退） | ✅ | ✅ `((h+1)//2)%12` + 五鼠遁 + `_local_tz` | ✅ B_late_*, B_tz_002 | ✅ 五鼠遁 ×3（甲子/丙子/戊子）+ 时区 ×2（有效/无效回退） | **FROZEN** |
| **B5** 大运（顺逆 + round(days/3)） | ✅ | ✅ `_dayun`（banker's rounding, 8 步） | ✅ B_dayun_001~005 | ✅ 顺/逆 ×2 + X.5→2 + 1.333→1 | **FROZEN** |
| **B6** 性别 UNKNOWN 回退 | ✅ | ✅ 按男处理 + `gender_assumed` | ✅ B_dayun_003 | ✅ 缺省/显式 UNKNOWN ×2 | **FROZEN** |

**判定规则**: 全部四列 ✅ 才可 FROZEN —— 6/6 满足。

---

## 2. Deferred Items Resolution Record（Task C）

### C.1 晚子时（Late Zi Hour）政策 —— **RESOLVED: FROZEN**

| 项 | 值 |
|----|-----|
| 官方行为 | **23:00 本地时间换日柱**（子时 = 23:00~00:59） |
| 依据 | 现有实现 + `test_2300_day_rollover` + 向量 B_late_001~003（22:59 当日/23:00 次日） |
| 替代方案 | 子正换日 / 0:00 换日 / 不换日（=Qimen D14）—— **均不采纳**, 变更须 ACP |
| 跨域声明 | 与 Qimen D14（不换日）为**既定有意分歧**, 见 `BAZI_CROSS_DOMAIN_BOUNDARIES.md` |
| 裁定 | **23:00 = 本项目的官方 BaZi 行为**, 写入冻结记录与契约草案（BC-004） |

### C.2 大运算法规范 —— **RESOLVED: FROZEN**

| 项 | 值 |
|----|-----|
| 官方算法 | `start_age = max(0, round(days/3))`（Python **banker's rounding**, .5 取偶）; 方向 = 阳年男/阴年女顺、其余逆; 步进 +10 岁, 默认 8 步（可配 dayun_count） |
| 依据 | 向量 B_dayun_001~005（含 X.5→2 显式锁定）+ 单元测试 ×4 |
| 替代方案 | ceiling/floor 起运、四舍五入（.5 进 1）—— **均不采纳**, 变更须 ACP |
| 裁定 | **round(x.5) 银行家舍入 = 本项目规范性算法**, 写入契约草案（BC-010） |

---

## 3. Risk Register 更新（Task C 收尾）

| Risk | Phase 6.3 Status | Phase 6.4 Status |
|------|------------------|------------------|
| 晚子时流派分歧 | Deferred | **Resolved / Frozen**（C.1 裁定） |
| 大运算法变体 | Deferred | **Resolved / Frozen**（C.2 裁定） |
| UNKNOWN 性别处理 | Frozen candidate | **Frozen**（B6 + 2 单元测试） |
| 节气时刻误差 | Infrastructure dependency | 维持（Meeus ~0.01°, 监控） |
| 时区回退链 | Implemented | **Frozen**（B4 行为锁定; 注: 回退为静默, 不产生警告 —— 任务书"warning capture"预期与实现不符, 已按实际行为测试并记录） |

---

## 4. 24 Vector Sufficiency Review（Task D）

| 冻结规则 | 边界覆盖向量 | 判定 |
|----------|--------------|------|
| B1 立春 | B_term_001/002（±3h）+ B_tz_003/004（12/31 vs 1/1） | ✅ |
| B2 节过渡 | B_term_003~006（清明/立冬 卯↔辰、戌↔亥）+ 五虎遁月干（B_basic_*） | ✅ |
| B3 23:00 换日 | B_late_001~003（22:59/23:00/23:30） | ✅ |
| B4 时区/钟表时 | B_tz_001/002（UTC+8 vs UTC+0 同时刻）+ B_late_* 子时 | ✅ |
| B5 大运 | B_dayun_001~005（顺/逆/UNKNOWN/X.5/分数） | ✅ |
| B6 UNKNOWN | B_dayun_003 | ✅ |

**新单元测试暴露的边界**: 无效时区回退路径（静默 → born_at.tzinfo）—— 由
`test_timezone_invalid_fallback` 锁定; 该路径**不新增向量**（单元测试已
确定性覆盖, 向量充分性不受影响）。

**Verdict**: **24 vectors 对 Contract Candidate 充分, 无需增补**。
（对比 Qimen: 24 向量同量级; 全部冻结规则边界均已覆盖。）

---

## 5. 评审结论

**PASS** —— B1~B6 六条规则正式 FROZEN; 两个 Deferred 项正式裁定;
24 向量验证充分。进入 **Task F 决策门**: 契约草案创建 + 状态升级
Contract Candidate（详见 `docs/bazi/BAZI_BEHAVIOR_CONTRACT_DRAFT.md`）。
