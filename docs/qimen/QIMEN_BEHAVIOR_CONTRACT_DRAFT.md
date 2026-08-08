# Qimen Behavior Contract Draft

> **状态**: **Superseded（已被正式契约取代）** — Phase 5.6
> 正式冻结契约: **`docs/specification/QIMEN_BEHAVIOR_CONTRACT.md` v1.0.0 (Frozen)**
> 本文档保留为历史草稿记录，不再作为行为依据。
>
> **原状态**: Draft（草稿，未冻结）— Phase 5.5
> **版本**: 0.1.0-draft
> **引擎版本**: 0.3.0（`QimenEngine.version`）
> **规则集版本**: 0.3.0
> **关联文档**:
> - 规则裁定: `QIMEN_RULE_DECISION.md`
> - 冻结评审: `QIMEN_FREEZE_REVIEW.md`
> - 算法假设: `QIMEN_ALGORITHM_ASSUMPTIONS.md`
> - Golden Vectors: `golden_vectors.json`（24 向量）
> - Schema: `docs/SCHEMAS.md §3.3`
>
> **性质声明**: 本文档将冻结规则、Golden Vectors 与 Schema 行为转换为契约候选
> 条款（QC-001~QC-014）。**不是最终 Behavior Contract**；正式化须经 ACP +
> D2 政策裁定 + 评审条件满足（见 `QIMEN_FREEZE_GAP.md`）。

---

## 1. Contract Metadata

| 项 | 值 |
|----|-----|
| contract_id | qimen:behavior:v0.1.0-draft |
| status | Draft |
| system | qimen |
| engine_version | 0.3.0 |
| rule_set_version | 0.3.0 |
| frozen_rules | D1, D3, D4, D5, D6, D7, D8, D9, D10, D11, D12, D13 |
| deferred_rules | D2（三元划分）, D14（晚子时换日） |
| vector_store | docs/qimen/golden_vectors.json（24） |
| schema_ref | docs/SCHEMAS.md §3.3（QimenInput / QimenBoard / QimenCell） |

---

## 2. Contract Clauses

### QC-001 Deterministic Output

- **定义**: 相同输入 ⇒ 字节级相同输出。
- **要求**:
  - 相同 `QimenInput`（含 request_id/born_at/born_location/gender）两次计算，
    `QimenBoard.model_dump(mode="json")` 逐字节一致（信封 `computed_at` 除外）。
  - 无随机、无系统时钟、无 I/O、无 LLM。
- **向量映射**: 全部 24 向量（`test_golden_vector_determinism` / `test_determinism_json_bytes`）。

### QC-002 Nine Palace Completeness

- **定义**: 输出恒为 9 宫。
- **要求**:
  - `len(cells) == 9`；`palace` 唯一覆盖 1..9（无遗漏、无重复）。
  - 宫名与 `PALACE_NAMES_9` 一致（坎坤震巽中宫乾兑艮离）。
- **向量映射**: 全部 24 向量（`test_nine_palace_completeness` / `test_symbol_uniqueness`）。

### QC-003 Dun Type

- **定义**: 阳遁/阴遁由管辖节气决定（D1, Frozen）。
- **要求**:
  - 管辖节气 = 24 节气中最后一个不晚于输入 UTC 时刻者（扫描前一年+当年）。
  - 管辖节气 ∈ {冬至…芒种} ⇒ `dun_type == "yang"`；∈ {夏至…大雪} ⇒ `"yin"`。
  - 冬至时刻本身归阳遁，夏至时刻本身归阴遁（含边界）。
- **向量映射**: G1/G2/G3、Y_ju1~Y_ju9、Z_yin2/Z_yin3/Z_yin5、
  B_summer_before/B_summer_after、B_lichun_before/B_lichun_after、
  B_zishi、B_truesolar、N_chunfen、N_qiufen、N_late_zishi。

### QC-004 Ju Calculation ⚠ Deferred Rule Dependency

- **定义**: `ju = ((节气基本局 - 1) + 三元偏移) % 9 + 1`；基本局 = 节气在
  遁序列序号（D3, Frozen）。
- **⚠ 三元偏移依赖 D2（Deferred，非 Frozen）**:
  - 当前行为: 公历日号 1-10 → 0、11-20 → 3、21-30 → 6（日号近似）。
  - 契约地位: **候选条款**；正式冻结前须完成 D2 政策裁定（见 Freeze Gap 1）。
- **要求（候选）**: `ju ∈ [1,9]`；`triple_offset ∈ {0,3,6}`；
  `day_of_month` = 输入钟表日。
- **向量映射**: 全部 24 向量（ju 字段）；阳遁 1-9 局全覆盖。

### QC-005 Earth Plate

- **定义**: 地盘干（D4, Frozen）。
- **要求**:
  - 阳遁顺布、阴遁逆布六仪三奇（戊己庚辛壬癸丁丙乙）。
  - 阳遁 n 局甲子戊在 n 宫；阴遁 n 局甲子戊在 (10-n) 宫。
  - 9 宫各恰一个干，集合 = {戊己庚辛壬癸丁丙乙}。
- **向量映射**: 全部 24 向量（earth_plate）；`test_earth_placement_invariants`。

### QC-006 Heaven Plate

- **定义**: 天盘干（D5/D6, Frozen）。
- **要求**:
  - 值符星 = 旬首六仪所在地盘宫之九星；值符随时干：时干宫 = 值符落宫。
  - 天盘 = 地盘按 `(时干宫 - 旬首宫) mod 9` 顺转。
  - 值符宫天盘干 = 旬首所遁之仪。
  - 时干为甲（旬首时辰）时，时干宫 = 旬首宫。
- **向量映射**: G1/G2/G3、Y_ju1~Y_ju9、Z_yin2/Z_yin3/Z_yin5、B_*、N_*。
  零转盘: G2、B_zishi、Y_ju1。

### QC-007 Zhi Fu（值符）

- **定义**: 值符星与值符神（D5/D10/D12, Frozen）。
- **要求**:
  - 值符星 = `NINE_STARS[旬首宫]`（旬首在中宫 ⇒ 天禽为值符星）。
  - 值符神 = 八神之首，落值符宫；值符宫为中宫时寄坤二宫（D12）。
  - 八神顺时针顺布（阴阳遁同向，跳过中宫）。
- **向量映射**: G1/G2/G3、Z_yin2（值符落中宫寄坤）、Z_yin5、Y_ju5（天禽为
  值符星）、N_qiufen（天禽为值符星，旬首在中宫）。

### QC-008 Zhi Shi（值使）

- **定义**: 值使门（D7/D12, Frozen）。
- **要求**:
  - 值使门 = 旬首宫地盘八门（旬首在中宫 ⇒ 取坤二宫死门）。
  - 随时支: 从本宫起，阳遁顺行/阴遁逆行，
    步数 = `(时支序 - 旬首支序) mod 12`。
  - 落中宫 ⇒ 寄坤二宫。
- **向量映射**: G1（惊门@巽四）、G3（死门@离九）、Y_ju1（休门落中宫寄坤）、
  Z_yin5（景门落中宫寄坤）、N_*。

### QC-009 Nine Stars

- **定义**: 九星排布（D8, Frozen）。
- **要求**:
  - 天盘九星随值符顺转（洛书宫序）。
  - 天禽参与转盘（9 宫 ↔ 9 星一一对应，不寄宫）。
  - 星集合恒 = {天蓬天芮天冲天辅天禽天心天柱天任天英}。
- **向量映射**: 全部 24 向量（nine_stars）；`test_nine_stars_correct` /
  `test_symbol_uniqueness`。

### QC-010 Eight Doors

- **定义**: 八门排布（D9, Frozen）。
- **要求**:
  - 值使落宫后，其余门按洛书宫序顺布（跳过中宫）。
  - 中宫不开门（`eight_doors is None` 仅限中宫）。
  - 门集合恒 = 8 门（休死伤杜开惊生景）。
- **向量映射**: 全部 24 向量（eight_doors）。

### QC-011 Eight Gods

- **定义**: 八神排布（D10, Frozen）。
- **要求**:
  - 值符神随值符落宫顺时针顺布（阴阳遁同向，跳过中宫）。
  - 中宫无神；八神集合恒 = {值符螣蛇太阴六合白虎玄武九地九天}。
- **向量映射**: 全部 24 向量（eight_gods）；`test_frozen_rule_regression` F9。

### QC-012 Three Qi

- **定义**: 三奇落宫（继承 D6 天盘语义）。
- **要求**:
  - `three_qi` = 天盘干落宫：乙/丙/丁 各恰一宫（其余宫为 null）。
  - 三奇落宫互异。
- **向量映射**: 全部 24 向量（three_qi）；三奇相邻: Y_ju2（2,3,4）。

### QC-013 Void Palace

- **定义**: 空亡（D11, Frozen）。
- **要求**:
  - 时柱旬空二支（甲子旬→戌亥 … 甲寅旬→子丑）映射宫位:
    坎子/艮丑寅/震卯/巽辰巳/离午/坤未申/兑酉/乾戌亥。
  - 空亡宫 1~2 个（两支可同宫）。
- **向量映射**: 全部 24 向量（is_void）；单宫: G1/G2/Y_ju1/B_zishi；
  双宫: G3/Z_yin5/N_chunfen/N_qiufen。

### QC-014 Central Palace Handling

- **定义**: 中宫处理（D12, Frozen）。
- **要求**:
  - 仅 palace 5 `is_central=True`；中宫 `eight_doors=None`、`eight_gods=None`。
  - 值符落中宫 ⇒ 八神值符寄坤二宫。
  - 值使落中宫 ⇒ 寄坤二宫；旬首在中宫 ⇒ 值使门取坤二宫（死门）。
  - 天禽星不寄宫（参与转盘，见 QC-009）。
- **向量映射**: G3、Y_ju1、Z_yin2、Z_yin5、N_qiufen、Y_ju5。

---

## 3. Golden Vector Mapping（Task B）

| Contract ID | 关键向量 |
|-------------|----------|
| QC-001 | 全部 24 |
| QC-002 | 全部 24 |
| QC-003 | G1, G2, G3, Y_ju1, Y_ju7, B_summer_before, B_summer_after, B_lichun_before, B_lichun_after |
| QC-004 | 全部 24（ju）；阳遁 1-9: Y_ju1~Y_ju9；阴遁: Z_yin2/3/5, N_qiufen |
| QC-005 | 全部 24（earth_plate） |
| QC-006 | G1, G2, G3, Y_ju1, B_zishi（零转盘），N_chunfen, N_qiufen |
| QC-007 | G1, G2, G3, Z_yin2, Z_yin5, Y_ju5, N_qiufen |
| QC-008 | G1, G3, Y_ju1, Z_yin5 |
| QC-009 | 全部 24（nine_stars） |
| QC-010 | 全部 24（eight_doors） |
| QC-011 | 全部 24（eight_gods） |
| QC-012 | 全部 24（three_qi）；Y_ju2（相邻） |
| QC-013 | 全部 24（is_void）；G3, Z_yin5（双宫） |
| QC-014 | G3, Y_ju1, Z_yin2, Z_yin5, Y_ju5, N_qiufen |

---

## 4. Non-Goals（本契约不含）

- 格局判断 / 吉凶解释 / 用神 / 应期
- 暗干 / 飞盘 / 置闰法（D2 未裁定前不进入契约）
- RAG / Consensus / LLM 解释层
- Schema 变更（QimenBoard/QimenCell 字段冻结，不因本契约修改）
