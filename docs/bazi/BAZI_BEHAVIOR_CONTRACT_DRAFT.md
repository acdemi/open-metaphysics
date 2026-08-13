# BaZi Behavior Contract (Draft)

> **状态**: **DRAFT** —— 待正式评审委员会冻结（Freeze Review 已 PASS,
> 本文档为冻结前置产物）
> **contract_id**: `bazi:behavior:0.1.0-draft`
> **版本**: 0.1.0 (draft)
> **system**: bazi
> **engine_version**: 0.1.0（`BaziEngine.version`）
> **rule_set_version**: 0.1.0
> **frozen_rules**: B1, B2, B3, B4, B5, B6（已冻结, 见 `BAZI_FREEZE_REVIEW.md`）
> **deferred_rules**: 无（格局/用神/强弱属未来 Sprint, 不在本契约范围）
> **Golden Vectors**: `docs/bazi/golden_vectors.json`（24, candidate → 冻结后为
> normative fixtures）
> **Schema 引用**: `src/openmetaphysics/agents/bazi.py`（BaziInput / BaziChart /
> Pillar / DaYun）+ `docs/bazi/BAZI_FREEZE_BOUNDARY.md`
> **相关文档**: `BAZI_ALGORITHM_ASSUMPTIONS.md` / `BAZI_RULE_DECISION.md` /
> `BAZI_FREEZE_REVIEW.md` / `BAZI_CROSS_DOMAIN_BOUNDARIES.md`
> **格式对齐**: `docs/specification/QIMEN_BEHAVIOR_CONTRACT.md`（QC-001~014 结构）

**契约性质**: 本契约将 BaZi 时家排盘（四柱/十神/藏干/纳音/大运）行为固化为
规范性要求。任何变更（算法/规则/向量）须经 **ACP**, 并递增契约版本。
Golden Vector 为不可变规范回归装置, 迁移须 ACP。

---

## 1. Contract Metadata

| 项 | 值 |
|----|-----|
| contract_id | bazi:behavior:0.1.0-draft |
| version | 0.1.0 (draft) |
| status | **DRAFT**（待冻结） |
| system | bazi |
| engine_version | 0.1.0 |
| rule_set_version | 0.1.0 |
| frozen_rules | B1, B2, B3, B4, B5, B6 |
| policy_decisions | 晚子时 = 23:00 换日（C.1 裁定）；大运 = round(x.5) 银行家舍入（C.2 裁定） |
| vector_store | docs/bazi/golden_vectors.json（24, candidate） |
| schema_ref | BaziInput / BaziChart（agents/bazi.py） |
| test_refs | tests/test_bazi.py（11）+ test_bazi_units.py（14）+ test_bazi_golden_vectors.py（7） |

---

## 2. Contract Clauses

### BC-001 Deterministic Output

- **Definition**: 相同输入 ⇒ 字节级相同输出（`computed_at` 信封除外）。
- **Preconditions**: `BaziInput` 合法（born_at 必须 tz-aware; born_location 可选）。
- **Deterministic requirement**: 无随机、无系统时钟、无 I/O、无 LLM; 计算为输入纯函数。
- **Observable output**: 两次计算 `BaziChart.model_dump(mode="json")` 逐字节一致。
- **Related rules**: 引擎契约（DeterministicEngine）。
- **Golden vectors**: ALL（24）。
- **Test references**: `test_determinism`（golden）; `test_bazi_replay_identical`。

### BC-002 Year Pillar（B1）

- **Definition**: 年柱以**立春**为界, 在 **UTC 时刻**比较
  `born_at >= lichun_time(year)`; 年干支序号 = `(立春年 - 4) % 60`。
- **Preconditions**: 无。
- **Deterministic requirement**: 立春时刻由 Meeus 算法确定（approx_1min）。
- **Observable output**: `year_pillar.stem/branch` + `year_boundary`。
- **Related rules**: B1。
- **Golden vectors**: B_term_001, B_term_002, B_tz_003, B_tz_004。
- **Test references**: `test_lichun_boundary_switches_year`; 五虎遁立春前边界。

### BC-003 Month Pillar（B2）

- **Definition**: 月界 = **12 节**（立春/惊蛰/清明/立夏/芒种/小暑/立秋/白露/
  寒露/立冬/大雪/小寒）, **不使用中气**; 月支 = 节固定地支; 月干 = **五虎遁**
  `(年干×2+2+(月支-2)) % 10`; 边界 UTC 比较。
- **Preconditions**: 无。
- **Deterministic requirement**: 节时刻由 Meeus 确定。
- **Observable output**: `month_pillar.stem/branch` + `month_boundary`（节名）。
- **Related rules**: B2。
- **Golden vectors**: B_term_003~006; B_basic_*。
- **Test references**: 五虎遁 ×3（甲己→丙寅 / 乙庚→戊寅 / 丙辛→庚寅, 含立春前边界）。

### BC-004 Day Pillar（B3）

- **Definition**: 干支日序 = `(JDN + 49) % 60`; **23:00 本地时间换日**
  （`local.hour >= 23` → 次日干支）。
- **Preconditions**: 本地时区按 BC-012 解析。
- **Deterministic requirement**: 晚子时 23:00 换日为**官方政策**
  （与 Qimen D14 差异, 见 `BAZI_CROSS_DOMAIN_BOUNDARIES.md` D-01）。
- **Observable output**: `day_pillar.stem/branch`。
- **Related rules**: B3, BC-012。
- **Golden vectors**: B_late_001（22:59 当日）, B_late_002/003（23:00 次日）; B_basic_*。
- **Test references**: `test_2300_day_rollover`; golden `test_boundary_regression`。

### BC-005 Hour Pillar（B4）

- **Definition**: 时支 = `((local.hour+1)//2) % 12`（子时 = 23:00~00:59）;
  时干 = **五鼠遁** `(日干×2 + 时支) % 10`; **钟表时**, 不使用真太阳时。
- **Preconditions**: 本地时区按 BC-012。
- **Deterministic requirement**: 真太阳时**不采用**（与 Qimen D13 差异,
  见 D-02）。
- **Observable output**: `hour_pillar.stem/branch`。
- **Related rules**: B4, BC-012。
- **Golden vectors**: B_late_*, B_tz_002（UTC+0 同时刻时柱差异）。
- **Test references**: 五鼠遁 ×3（甲子/丙子/戊子）; 时区 ×2。

### BC-006 Ten Gods Mapping

- **Definition**: 全部柱干 + 藏干 vs 日主的十神映射
  （同阴阳 → 比肩/劫财; 相生 → 偏印/正印; 我生 → 食神/伤官;
  相克 → 七杀/正官; 我克 → 偏财/正财）。
- **Preconditions**: 无。
- **Deterministic requirement**: 五行关系表 + 阴阳判定固定。
- **Observable output**: `ten_gods_map`。
- **Related rules**: 十神映射（BAZI_FREEZE_BOUNDARY §1）。
- **Golden vectors**: ALL（ten_gods 字段）。
- **Test references**: `test_ten_gods_against_day_master`。

### BC-007 Hidden Stems

- **Definition**: 各柱支的藏干列表按固定表
  （`BRANCH_HIDDEN_STEMS`, 子=癸, 丑=己癸辛, …）。
- **Preconditions**: 无。
- **Observable output**: `pillars[*].hidden_stems`。
- **Golden vectors**: ALL（hidden_stems 字段）。
- **Test references**: `test_hidden_stems_and_nayin_present`。

### BC-008 Na Yin

- **Definition**: 各柱干支纳音按固定表（`NAYIN`, 60 组）。
- **Preconditions**: 无。
- **Observable output**: `pillars[*].nayin`。
- **Golden vectors**: ALL（nayin 字段）。
- **Test references**: `test_hidden_stems_and_nayin_present`。

### BC-009 Da Yun Direction（B5）

- **Definition**: 方向 = (年干阳 ∧ 男) ∨ (年干阴 ∧ 女) → **顺排**, 其余 **逆排**;
  每步 = 月柱干支 ±1 序, 步进 +10 岁, 默认 8 步（可配 `dayun_count`）。
- **Preconditions**: gender 按 BC-011 解析。
- **Deterministic requirement**: 顺逆判定固定。
- **Observable output**: `dayun[*].stem/branch/start_age/end_age/start_at`。
- **Related rules**: B5, BC-010, BC-011。
- **Golden vectors**: B_dayun_001（阳男顺）, B_dayun_002（阳女逆）。
- **Test references**: 顺（阳男+阴女）/ 逆（阴男+阳女）。

### BC-010 Da Yun Start Age（B5）

- **Definition**: `start_age = max(0, round(距节边界天数 / 3))`,
  采用 **Python banker's rounding**（.5 取偶）—— 本项目的规范性算法。
- **Preconditions**: 距节天数 = 与最近节边界（顺=后一个, 逆=前一个）的
  秒差 / 86400。
- **Deterministic requirement**: `round(x.5)` 语义显式锁定。
- **Observable output**: `dayun[0].start_age`。
- **Related rules**: B5。
- **Golden vectors**: B_dayun_004（4.5 天 → 1.5 → 2）, B_dayun_005（4 天 → 1）。
- **Test references**: `test_dayun_bankers_rounding_x5`, `test_dayun_fractional_floor`。

### BC-011 Gender UNKNOWN（B6）

- **Definition**: `Gender.UNKNOWN`（含 schema 缺省）在大运方向判定中
  **按男处理**, 且输出 `gender_assumed=True`。
- **Preconditions**: 无。
- **Observable output**: `gender_assumed` + 与 male 一致的大运。
- **Related rules**: B6, BC-009。
- **Golden vectors**: B_dayun_003。
- **Test references**: UNKNOWN ×2（缺省/显式, 与 male 对照）。

### BC-012 Timezone Policy（B4 基础设施）

- **Definition**: 本地时区解析顺序: `born_location.timezone`（ZoneInfo）→
  `born_at.tzinfo` → UTC。**静默回退**（不产生警告）。日柱换日与时辰
  均按本地时间; 节气边界按 UTC（BC-002/003）。
- **Preconditions**: born_at 必须 tz-aware。
- **Observable output**: 本地时区相关输出（day/hour pillar, start_at）。
- **Related rules**: B4, BC-004, BC-005。
- **Golden vectors**: B_tz_001（UTC+8）, B_tz_002（UTC+0 同时刻）。
- **Test references**: `test_timezone_valid_offset`, `test_timezone_invalid_fallback`。

### BC-013 Schema Contract

- **Definition**: 输入 = `BaziInput`（request_id / born_at(tz-aware) /
  born_location? / gender / dayun_count=8）; 输出 = `BaziOutput` 信封 +
  `BaziChart`（pillars ×4, ten_gods_map, dayun, boundaries）; 全部
  `extra="forbid"`。
- **Preconditions**: 无。
- **Golden vectors**: ALL（input/expected 结构对照）。
- **Test references**: `test_vector_count`, `test_vectors_match_engine`。

### BC-014 Golden Vectors

- **Definition**: `docs/bazi/golden_vectors.json` 24 向量为规范回归装置
  （冻结后 normative fixtures, 当前 candidate）。
- **Preconditions**: 无。
- **Deterministic requirement**: 24/24 与引擎输出逐字节一致。
- **Golden vectors**: 自身。
- **Test references**: `test_bazi_golden_vectors.py`（7 例）。

---

## 3. 契约范围外（显式排除）

| 项 | 说明 |
|----|------|
| 格局分析 / 用神 / 强弱 / 神煞 / 流年 | 未来 Sprint（BAZI_FREEZE_BOUNDARY §2） |
| 解释层 / 叙述 / 建议 / LLM / RAG / Consensus | Domain Boundary（ARCHITECTURE.md §1） |

---

## 4. 冻结前置条件（Review Board 确认清单）

1. Freeze Review PASS（✅ 已完成, `BAZI_FREEZE_REVIEW.md`）
2. Deferred 项裁定（✅ 已完成, 晚子时 23:00 + banker's rounding）
3. 24 向量充分性（✅ 已确认, 无需增补）
4. 单元测试 14 例（✅ 已补齐, 全部通过）
5. 本草案评审通过 → 版本 0.1.0-draft → **1.0.0 Frozen**
