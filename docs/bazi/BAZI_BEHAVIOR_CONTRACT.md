# BaZi Behavior Contract

> **状态**: **Frozen** — Phase 6.5 Contract Freeze（正式冻结, v1.0.0）
> **contract_id**: `bazi:behavior:v1.0.0`
> **版本**: 1.0.0
> **system**: bazi
> **engine_version**: 0.1.0（`BaziEngine.version`）
> **rule_set_version**: 0.1.0
> **frozen_rules**: B1, B2, B3, B4, B5, B6
> **deferred_rules**: 无（格局/用神/强弱/神煞/流年属未来 Sprint, 不在本契约范围）
> **Golden Vectors**: `docs/bazi/golden_vectors.json`（24, normative regression fixtures）
> **Schema 引用**: `src/openmetaphysics/agents/bazi.py`（BaziInput / BaziChart / Pillar / DaYun）
> **相关文档**: `docs/bazi/BAZI_ALGORITHM_ASSUMPTIONS.md` /
> `docs/bazi/BAZI_RULE_DECISION.md` / `docs/bazi/BAZI_FREEZE_BOUNDARY.md` /
> `docs/governance/bazi/BAZI_FREEZE_REVIEW.md` / `docs/bazi/BAZI_CROSS_DOMAIN_BOUNDARIES.md`
> **历史**: Draft 版本保留于 `docs/bazi/BAZI_BEHAVIOR_CONTRACT_DRAFT.md`（不删除）

**契约性质**: 本契约将 BaZi 确定性排盘（四柱/十神/藏干/纳音/大运）行为固化为
规范性要求。任何变更（算法/规则/向量）须经 **ACP**, 并递增契约版本。
Golden Vector 为不可变规范回归装置, 迁移须 ACP。

---

## 1. Freeze Record（冻结记录）

| 项 | 值 |
|----|-----|
| **Frozen version** | **1.0.0** |
| **Freeze date** | **2026-08-09** |
| **Rules covered** | B1 年柱 / B2 月柱 / B3 日柱 / B4 时柱 / B5 大运 / B6 性别 UNKNOWN |
| **Golden Vector count** | **24**（candidate → normative fixtures） |
| **Policy decisions** | 晚子时 = 23:00 本地换日; 大运 = round(x.5) 银行家舍入; UNKNOWN 按男处理; 无效时区静默回退 born_at.tzinfo |
| **Reference requirement** | `reference/bazi/` 独立实现（不导入 production）须通过 24/24 等价 + BC 审计 |
| **Change procedure** | ACP → 契约版本递增 → Golden Vector 迁移 → Reference 同步更新 + 重新认证 |
| **Review evidence** | `docs/governance/bazi/BAZI_FREEZE_REVIEW.md`（PASS, B1~B6 四列全 ✅） |

---

## 2. Contract Metadata

| 项 | 值 |
|----|-----|
| contract_id | bazi:behavior:v1.0.0 |
| version | 1.0.0 |
| status | **Frozen** |
| system | bazi |
| engine_version | 0.1.0 |
| rule_set_version | 0.1.0 |
| frozen_rules | B1, B2, B3, B4, B5, B6 |
| policy_decisions | 晚子时 23:00 换日; 大运 banker's rounding; UNKNOWN 按男; 时区静默回退 |
| vector_store | docs/bazi/golden_vectors.json（24, normative fixtures） |
| schema_ref | BaziInput / BaziChart（agents/bazi.py） |
| test_refs | tests/test_bazi.py（11）; tests/test_bazi_units.py（14）; tests/test_bazi_golden_vectors.py（7） |

---

## 3. Contract Clauses

### BC-001 Deterministic Output

- **Definition**: 相同输入 ⇒ 字节级相同输出（`computed_at` 信封除外）。
- **Preconditions**: `BaziInput` 合法（born_at 必须 tz-aware; born_location 可选）。
- **Deterministic requirement**: 无随机、无系统时钟、无 I/O、无 LLM; 计算为输入纯函数。
- **Observable output**: 两次计算 `BaziChart.model_dump(mode="json")` 逐字节一致。
- **Related rules**: 引擎契约（DeterministicEngine）。
- **Golden vectors**: ALL（24）。
- **Test references**: `test_bazi_golden_vectors.py::test_determinism`; `test_determinism.py::test_bazi_replay_identical`。

### BC-002 Year Pillar（B1）

- **Definition**: 年柱以**立春**为界, 在 **UTC 时刻**比较 `born_at >= lichun_time(year)`; 年干支序号 = `(立春年 - 4) % 60`。
- **Preconditions**: 无。
- **Deterministic requirement**: 立春时刻由 Meeus 算法确定（approx_1min）。
- **Observable output**: `year_pillar.stem/branch` + `year_boundary`。
- **Related rules**: B1。
- **Golden vectors**: B_term_001（立春前→癸卯）, B_term_002（立春后→甲辰）, B_tz_003/004（12/31 与 1/1 均癸卯）。
- **Test references**: `test_lichun_boundary_switches_year`; `test_bazi_units.py::test_wuhu_dun_bing_xin_year_geng_yin_month`（立春前年界）。

### BC-003 Month Pillar（B2）

- **Definition**: 月界 = **12 节**（立春/惊蛰/清明/立夏/芒种/小暑/立秋/白露/寒露/立冬/大雪/小寒）, **不使用中气**; 月支 = 节固定地支; 月干 = **五虎遁** `(年干×2+2+(月支-2)) % 10`; 边界 UTC 比较。
- **Preconditions**: 无。
- **Deterministic requirement**: 节时刻由 Meeus 确定。
- **Observable output**: `month_pillar.stem/branch` + `month_boundary`（节名）。
- **Related rules**: B2。
- **Golden vectors**: B_term_003~006（清明 卯→辰, 立冬 戌→亥）; B_basic_*。
- **Test references**: `test_bazi_units.py::test_wuhu_dun_jia_ji_year_bing_yin_month` / `_yi_geng_year_wu_yin_month` / `_bing_xin_year_geng_yin_month`。

### BC-004 Day Pillar（B3）

- **Definition**: 干支日序 = `(JDN + 49) % 60`; **23:00 本地时间换日**（`local.hour >= 23` → 次日干支）。
- **Preconditions**: 本地时区按 BC-012 解析。
- **Deterministic requirement**: 晚子时 23:00 换日为**官方政策**（与 Qimen D14 差异, 见 `BAZI_CROSS_DOMAIN_BOUNDARIES.md` D-01）。
- **Observable output**: `day_pillar.stem/branch`。
- **Related rules**: B3, BC-012。
- **Golden vectors**: B_late_001（22:59 当日亥时）, B_late_002（23:00 次日子时）, B_late_003（23:30 次日）; B_basic_*。
- **Test references**: `test_2300_day_rollover`; `test_bazi_golden_vectors.py::test_boundary_regression`。

### BC-005 Hour Pillar（B4）

- **Definition**: 时支 = `((local.hour+1)//2) % 12`（子时 = 23:00~00:59）; 时干 = **五鼠遁** `(日干×2 + 时支) % 10`; **钟表时**, 不使用真太阳时。
- **Preconditions**: 本地时区按 BC-012。
- **Deterministic requirement**: 真太阳时**不采用**（与 Qimen D13 差异, 见 D-02）; 时干基于**换日后的日柱**（晚子时 23:00 后按次日日干）。
- **Observable output**: `hour_pillar.stem/branch`。
- **Related rules**: B4, BC-012。
- **Golden vectors**: B_late_*（子时）; B_tz_002（UTC+0 同时刻时柱差异）。
- **Test references**: `test_bazi_units.py::test_wushu_dun_jia_ji_day_jia_zi_hour` / `_yi_geng_day_bing_zi_hour` / `_bing_xin_day_wu_zi_hour`; `test_timezone_valid_offset`。

### BC-006 Ten Gods Mapping

- **Definition**: 全部柱干 + 藏干 vs 日主的十神映射: 同阴阳 → 比肩/劫财; 相生 → 偏印/正印; 我生 → 食神/伤官; 相克 → 七杀/正官; 我克 → 偏财/正财（按五行生克 + 阴阳异同）。
- **Preconditions**: 无。
- **Deterministic requirement**: 五行生克表 + 阴阳判定固定。
- **Observable output**: `ten_gods_map`（键 = 出现的全部干支）。
- **Related rules**: 十神映射（`BAZI_FREEZE_BOUNDARY.md` §1）。
- **Golden vectors**: ALL（ten_gods 字段）。
- **Test references**: `test_ten_gods_against_day_master`; `test_bazi_golden_vectors.py::test_vectors_match_engine`。

### BC-007 Hidden Stems

- **Definition**: 各柱支的藏干列表按固定表（子=癸, 丑=己癸辛, 寅=甲丙戊, 卯=乙, 辰=戊乙癸, 巳=丙庚戊, 午=丁己, 未=己丁乙, 申=庚壬戊, 酉=辛, 戌=戊辛丁, 亥=壬甲）。
- **Preconditions**: 无。
- **Deterministic requirement**: 表固定。
- **Observable output**: `pillars[*].hidden_stems`。
- **Golden vectors**: ALL（hidden_stems 字段）。
- **Test references**: `test_hidden_stems_and_nayin_present`。

### BC-008 Na Yin

- **Definition**: 各柱干支纳音按固定表（60 组, 每 2 组同名, 按干支序索引）。
- **Preconditions**: 无。
- **Deterministic requirement**: 表固定。
- **Observable output**: `pillars[*].nayin`。
- **Golden vectors**: ALL（nayin 字段）。
- **Test references**: `test_hidden_stems_and_nayin_present`。

### BC-009 Da Yun Direction（B5）

- **Definition**: 方向 = (年干阳 ∧ 男) ∨ (年干阴 ∧ 女) → **顺排**, 其余 **逆排**; 每步干支 = 月柱干支 ±1 序（顺 +1, 逆 -1, mod 60）; 步进 +10 岁; 默认 **8 步**（可配 `dayun_count`）。
- **Preconditions**: gender 按 BC-011 解析。
- **Deterministic requirement**: 顺逆判定固定。
- **Observable output**: `dayun[*].stem/branch/start_age/end_age/start_at`。
- **Related rules**: B5, BC-010, BC-011。
- **Golden vectors**: B_dayun_001（阳男顺, dy0=7）; B_dayun_002（阳女逆, dy0=3）。
- **Test references**: `test_bazi_units.py::test_dayun_forward_yang_male_yin_female` / `test_dayun_reverse_yin_male_yang_female`。

### BC-010 Da Yun Start Age（B5）

- **Definition**: `start_age = max(0, round(距节边界天数 / 3))`, 采用 **Python banker's rounding**（.5 取偶）—— 本项目规范性算法; 距节天数 = 与最近节边界（顺 = 后一个, 逆 = 前一个）的秒差 / 86400。
- **Preconditions**: 无。
- **Deterministic requirement**: `round(x.5)` 语义显式锁定（例: 4.5 天 → 1.5 → 2; 4 天 → 1.333 → 1）。
- **Observable output**: `dayun[0].start_age`。
- **Related rules**: B5。
- **Golden vectors**: B_dayun_004（距清明 4.5 天 → start_age 2）, B_dayun_005（4 天 → 1）。
- **Test references**: `test_bazi_units.py::test_dayun_bankers_rounding_x5` / `test_dayun_fractional_floor`。

### BC-011 Gender UNKNOWN（B6）

- **Definition**: `Gender.UNKNOWN`（含 schema 缺省值）在大运方向判定中**按男处理**, 且输出 `gender_assumed=True`。
- **Preconditions**: 无。
- **Deterministic requirement**: 回退路径固定。
- **Observable output**: `gender_assumed` + 与 male 一致的大运。
- **Related rules**: B6, BC-009。
- **Golden vectors**: B_dayun_003（UNKNOWN, dy0=7 与 male 一致, assume=True）。
- **Test references**: `test_bazi_units.py::test_unknown_gender_default_fallback_male` / `test_unknown_gender_explicit_flag`; `test_bazi_golden_vectors.py::test_gender_unknown_locked`。

### BC-012 Timezone Policy（B4 基础设施）

- **Definition**: 本地时区解析顺序: `born_location.timezone`（ZoneInfo）→ `born_at.tzinfo` → UTC; **静默回退**（不产生警告）; 日柱换日（BC-004）与时辰（BC-005）按本地时间; 节气边界按 UTC（BC-002/003）。
- **Preconditions**: born_at 必须 tz-aware。
- **Deterministic requirement**: 回退链固定。
- **Observable output**: 本地时区相关输出（day/hour pillar, dayun start_at）。
- **Related rules**: B4, BC-004, BC-005。
- **Golden vectors**: B_tz_001（UTC+8 经典例）, B_tz_002（UTC+0 同时刻, 日柱同/时柱异）。
- **Test references**: `test_bazi_units.py::test_timezone_valid_offset` / `test_timezone_invalid_fallback`（静默回退 born_at.tzinfo）。

### BC-013 Schema Contract

- **Definition**: 输入 = `BaziInput`（request_id / born_at(tz-aware) / born_location? / gender(缺省 UNKNOWN) / dayun_count=8）; 输出 = `BaziOutput` 信封 + `BaziChart`（pillars ×4: position/stem/branch/stem_index/branch_index/hidden_stems/nayin/ten_god; ten_gods_map; dayun: index/start_age/end_age/stem/branch/stem_index/branch_index/start_at; year_boundary; month_boundary; day_master; day_master_element; gender_assumed）; 全部模型 `extra="forbid"`。
- **Preconditions**: 无。
- **Golden vectors**: ALL（input/expected 结构对照）。
- **Test references**: `test_bazi_golden_vectors.py::test_vectors_match_engine`（逐字段精确比对）。

### BC-014 Golden Vectors

- **Definition**: `docs/bazi/golden_vectors.json` 24 向量为规范回归装置（normative fixtures）。
- **Preconditions**: 无。
- **Deterministic requirement**: 24/24 与引擎输出逐字节一致。
- **Golden vectors**: 自身。
- **Test references**: `tests/test_bazi_golden_vectors.py`（7 例）; `reference/tests/test_bazi_equivalence.py`（Production == Reference, 24/24）。

---

## 4. 契约范围外（显式排除）

| 项 | 说明 |
|----|------|
| 格局分析 / 用神 / 强弱 / 神煞 / 流年 | 未来 Sprint（`BAZI_FREEZE_BOUNDARY.md` §2） |
| 解释层 / 叙述 / 建议 / 吉凶 / LLM / RAG / Consensus | Domain Boundary（`ARCHITECTURE.md` §1） |

---

## 5. Change Procedure（变更流程）

冻结后任何变更（算法/规则/向量/schema）必须完整执行:

1. **ACP**（Architecture Change Proposal, 等待人工批准）
2. **契约版本递增**（v1.0.0 → 下一版本）
3. **Golden Vector 迁移**（不可原地修改, 生成新向量集）
4. **Reference Runtime 同步更新 + 重新认证**（`reference/bazi/` 双实现验证）

违反即视为越界; 契约文本冻结后不得直接修改。
