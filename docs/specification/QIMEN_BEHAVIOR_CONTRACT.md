# Qimen Behavior Contract

> **状态**: **Frozen** — Phase 5.6 Contract Freeze Sprint
> **contract_id**: `qimen:behavior:v1.0.0`
> **版本**: 1.0.0
> **system**: qimen
> **engine_version**: 0.3.0（`QimenEngine.version`）
> **rule_set_version**: 0.3.0
> **frozen_rules**: D1, D3, D4, D5, D6, D7, D8, D9, D10, D11, D12, D13, D14
> **deferred_rules**: 无（D2 已裁定为规范近似，见 QC-004）
> **Golden Vectors**: `docs/qimen/golden_vectors.json`（24，normative regression fixtures）
> **Schema 引用**: `docs/SCHEMAS.md §3.3`（QimenInput / QimenBoard / QimenCell）
> **相关文档**: `QIMEN_RULE_DECISION.md` / `QIMEN_ALGORITHM_ASSUMPTIONS.md` /
> `QIMEN_FREEZE_REVIEW.md` / `QIMEN_FREEZE_GAP.md`

**契约性质**: 本契约将 Qimen 时家转盘排盘行为固化为规范性要求。任何变更
（算法/规则/向量）须经 **ACP**，并递增契约版本。Golden Vector 为不可变
规范回归装置，迁移须 ACP。

---

## 1. Contract Metadata

| 项 | 值 |
|----|-----|
| contract_id | qimen:behavior:v1.0.0 |
| version | 1.0.0 |
| status | **Frozen** |
| system | qimen |
| engine_version | 0.3.0 |
| rule_set_version | 0.3.0 |
| frozen_rules | D1, D3, D4, D5, D6, D7, D8, D9, D10, D11, D12, D13, D14 |
| policy_decisions | D2 = Option A（日号近似为规范行为）；D14 = 晚子时不换日柱 |
| vector_store | docs/qimen/golden_vectors.json（24, normative fixtures） |
| schema_ref | docs/SCHEMAS.md §3.3 |
| test_refs | tests/test_qimen.py（33）；tests/test_qimen_contract.py（契约校验） |

---

## 2. Contract Clauses

### QC-001 Deterministic Output

- **Definition**: 相同输入 ⇒ 字节级相同输出。
- **Preconditions**: 输入为合法 `QimenInput`（born_at 必须 tz-aware；
  born_location 可选）。
- **Deterministic requirement**: 无随机、无系统时钟、无 I/O、无 LLM；
  计算为输入纯函数。
- **Observable output**: 相同输入两次计算，`QimenBoard.model_dump(mode="json")`
  逐字节一致（信封 `computed_at` 除外）。
- **Related rules**: 引擎契约（DeterministicEngine）。
- **Golden vectors**: ALL（24）。
- **Test references**: `test_golden_vector_determinism`、
  `test_determinism_json_bytes`、`test_determinism_replay`。

### QC-002 Nine Palace Completeness

- **Definition**: 输出恒为 9 宫，宫位完整唯一。
- **Preconditions**: 无（任何合法输入）。
- **Deterministic requirement**: 宫位由输入唯一确定。
- **Observable output**: `len(cells) == 9`；`palace` 唯一覆盖 1..9；
  宫名 = 坎坤震巽中宫乾兑艮离（`PALACE_NAMES_9`）。
- **Related rules**: Schema §3.3。
- **Golden vectors**: ALL（24）。
- **Test references**: `test_nine_palace_completeness`、`test_has_all_9_palaces`、
  `test_symbol_uniqueness`、`_assert_board_state_valid`。

### QC-003 Dun Type

- **Definition**: 阳遁/阴遁由管辖节气决定（D1, Frozen）。
- **Preconditions**: 输入时刻在 24 节气历范围内（前一年+当年扫描）。
- **Deterministic requirement**: 管辖节气 = 24 节气中最后一个不晚于输入
  UTC 时刻者；唯一确定。
- **Observable output**: 管辖节气 ∈ {冬至…芒种} ⇒ `dun_type == "yang"`；
  ∈ {夏至…大雪} ⇒ `"yin"`。冬至时刻本身归阳遁，夏至时刻本身归阴遁。
- **Related rules**: D1（QIMEN_RULE_DECISION.md）。
- **Golden vectors**: G1, G2, G3, Y_ju1, Y_ju7,
  B_summer_before, B_summer_after, B_lichun_before, B_lichun_after。
- **Test references**: `test_dun_type_boundary`、
  `test_winter_solstice_boundary_switch`、`test_summer_solstice_boundary_switch`。

### QC-004 Ju Calculation

- **Definition**: `ju = ((节气基本局 - 1) + 三元偏移) % 9 + 1`（D3, Frozen）。
  三元偏移采用 **D2 政策裁定 Option A**：日号近似为规范行为。
- **Preconditions**: 输入时刻在节气历范围内。
- **Deterministic requirement**: 基本局 = 管辖节气在遁序列序号
  （阳遁 冬至=1…芒种=12；阴遁 夏至=1…大雪=12）；三元偏移按公历日号:
  1-10 → 0、11-20 → 3、21-30 → 6。
- **Observable output**: `ju ∈ [1,9]`；`triple_offset ∈ {0,3,6}`；
  `day_of_month` = 输入钟表日。
- **Related rules**: D3（冻结）、D2（政策裁定 Option A，契约 v1.0.0 生效；
  迁移路径见 `QIMEN_D2_IMPACT_ANALYSIS.md`，若未来改判真拆补法须
  契约主版本递增 v1.0.0 → v2.0.0）。
- **Golden vectors**: ALL（24）—— 阳遁 1-9 局全覆盖（Y_ju1~Y_ju9），
  阴遁 {2,3,5,7}（Z_yin2/Z_yin3/Z_yin5/N_qiufen）。
- **Test references**: `test_ju_range`、`test_ju_1_to_9_coverage`、
  `test_triple_offset_correct`、`test_golden_vectors_full_board`。

### QC-005 Earth Plate

- **Definition**: 地盘干（D4, Frozen）。
- **Preconditions**: 局数确定（QC-004）。
- **Deterministic requirement**: 阳遁顺布、阴遁逆布六仪三奇
  （戊己庚辛壬癸丁丙乙）；阳遁 n 局甲子戊在 n 宫，阴遁 n 局甲子戊在 (10-n) 宫。
- **Observable output**: 每宫 `earth_plate` 恰一干；9 干集合 =
  {戊己庚辛壬癸丁丙乙}，互异。
- **Related rules**: D4。
- **Golden vectors**: ALL（24）。
- **Test references**: `test_earth_placement_invariants`、
  `test_ju_1_to_9_coverage`。

### QC-006 Heaven Plate

- **Definition**: 天盘干（D5/D6, Frozen）。
- **Preconditions**: 地盘与值符确定。
- **Deterministic requirement**: 值符星 = 旬首六仪所在地盘宫之九星；
  值符随时干：时干宫 = 值符落宫；天盘 = 地盘按
  `(时干宫 - 旬首宫) mod 9` 顺转；值符宫天盘干 = 旬首所遁之仪；
  时干为甲（旬首时辰）时，时干宫 = 旬首宫。
- **Observable output**: 每宫 `sky_plate` 恰一干，9 干互异；
  天盘干集合 = 地盘干集合。
- **Related rules**: D5, D6。
- **Golden vectors**: G1, G2, G3, Y_ju1, B_zishi, N_chunfen, N_qiufen
  （零转盘: G2, B_zishi, Y_ju1）。
- **Test references**: `test_hour_plan_consistency`、
  `test_golden_vector_yin_norotation_semantics`、`test_frozen_rule_regression`。

### QC-007 Zhi Fu（值符）

- **Definition**: 值符星与值符神（D5/D10/D12, Frozen）。
- **Preconditions**: 时干支、旬首确定。
- **Deterministic requirement**: 值符星 = `NINE_STARS[旬首宫]`
  （旬首在中宫 ⇒ 天禽为值符星）；值符神落值符宫（中宫 ⇒ 寄坤二宫）；
  八神顺时针顺布（阴阳遁同向，跳过中宫）。
- **Observable output**: `eight_gods` 中"值符"所在宫 = 值符落宫
  （寄宫后）；值符星所在宫天盘干 = 旬首仪。
- **Related rules**: D5, D10, D12。
- **Golden vectors**: G1, G2, G3, Z_yin2, Z_yin5, Y_ju5, N_qiufen。
- **Test references**: `test_zhifu_zhishi_on_boards`、
  `test_golden_vector_yin_zhonggong_jigong_semantics`。

### QC-008 Zhi Shi（值使）

- **Definition**: 值使门（D7/D12, Frozen）。
- **Preconditions**: 旬首、时支确定。
- **Deterministic requirement**: 值使门 = 旬首宫地盘八门（旬首在中宫 ⇒
  取坤二宫死门）；随时支：从本宫起，阳遁顺行/阴遁逆行，
  步数 = `(时支序 - 旬首支序) mod 12`；落中宫 ⇒ 寄坤二宫。
- **Observable output**: 值使门所在宫 = 值使落宫。
- **Related rules**: D7, D12。
- **Golden vectors**: G1, G3, Y_ju1, Z_yin5。
- **Test references**: `test_zhifu_zhishi_on_boards`、
  `test_frozen_rule_regression`。

### QC-009 Nine Stars

- **Definition**: 九星排布（D8, Frozen）。
- **Preconditions**: 无。
- **Deterministic requirement**: 天盘九星随值符顺转（洛书宫序）；
  天禽参与转盘（9 宫 ↔ 9 星一一对应，不寄宫）。
- **Observable output**: 每宫 `nine_stars` 非空；星集合恒 =
  {天蓬天芮天冲天辅天禽天心天柱天任天英}，互异。
- **Related rules**: D8。
- **Golden vectors**: ALL（24）。
- **Test references**: `test_nine_stars_correct`、`test_symbol_uniqueness`。

### QC-010 Eight Doors

- **Definition**: 八门排布（D9, Frozen）。
- **Preconditions**: 值使落宫确定。
- **Deterministic requirement**: 值使落宫后其余门按洛书宫序顺布
  （跳过中宫）；中宫不开门。
- **Observable output**: 中宫 `eight_doors is None`；非中宫全部非空；
  门集合恒 = {休死伤杜开惊生景}，互异。
- **Related rules**: D9。
- **Golden vectors**: ALL（24）。
- **Test references**: `test_nine_palace_completeness`、
  `test_symbol_uniqueness`。

### QC-011 Eight Gods

- **Definition**: 八神排布（D10, Frozen）。
- **Preconditions**: 值符落宫确定。
- **Deterministic requirement**: 值符神随值符落宫顺时针顺布
  （阴阳遁同向，跳过中宫）；中宫无神。
- **Observable output**: 中宫 `eight_gods is None`；非中宫全部非空；
  神集合恒 = {值符螣蛇太阴六合白虎玄武九地九天}，互异。
- **Related rules**: D10。
- **Golden vectors**: ALL（24）。
- **Test references**: `test_frozen_rule_regression`（F9 顺布序断言）、
  `test_symbol_uniqueness`。

### QC-012 Three Qi

- **Definition**: 三奇落宫（天盘语义，继承 D6）。
- **Preconditions**: 天盘确定。
- **Deterministic requirement**: `three_qi` = 天盘干中乙/丙/丁所在宫，
  各恰一宫；其余宫为 null；三奇落宫互异。
- **Observable output**: 恰 3 宫 `three_qi` 非空，集合 = {乙丙丁}。
- **Related rules**: D6。
- **Golden vectors**: ALL（24）。
- **Test references**: `test_sanqi_detection`、`test_symbol_uniqueness`。

### QC-013 Void Palace

- **Definition**: 空亡（D11, Frozen）。
- **Preconditions**: 时干支确定。
- **Deterministic requirement**: 时柱旬空二支
  （甲子旬→戌亥 … 甲寅旬→子丑）映射宫位:
  坎子/艮丑寅/震卯/巽辰巳/离午/坤未申/兑酉/乾戌亥。
- **Observable output**: `is_void` 宫 1~2 个（两支可同宫），其余 false。
- **Related rules**: D11。
- **Golden vectors**: ALL（24）。
- **Test references**: `test_void_branch_invariants`、
  `test_void_palace_rule`、`test_frozen_rule_regression`。

### QC-014 Central Palace Handling

- **Definition**: 中宫处理（D12, Frozen）。
- **Preconditions**: 无。
- **Deterministic requirement**: 仅 palace 5 `is_central=True`；中宫无
  八门八神；值符落中宫 ⇒ 八神值符寄坤二宫；值使落中宫 ⇒ 寄坤二宫；
  旬首在中宫 ⇒ 值使门取坤二宫（死门）；天禽星不寄宫。
- **Observable output**: `is_central` 恰一宫（palace 5）；寄宫行为见
  QC-007/QC-008。
- **Related rules**: D12。
- **Golden vectors**: G3, Y_ju1, Z_yin2, Z_yin5, Y_ju5, N_qiufen。
- **Test references**: `test_golden_vector_yin_zhonggong_jigong_semantics`、
  `test_nine_palace_completeness`、`test_frozen_rule_regression`。

---

## 3. Golden Vector Mapping（规范性）

约定：`ALL` = 全部 24 向量。映射仅用于校验，规范性真值以
`docs/qimen/golden_vectors.json` 为准。

| Contract ID | Golden Vectors |
|-------------|----------------|
| QC-001 | ALL |
| QC-002 | ALL |
| QC-003 | G1, G2, G3, Y_ju1_zhishi_zhonggong, Y_ju7_winter_solstice, B_summer_before, B_summer_after, B_lichun_before, B_lichun_after |
| QC-004 | ALL |
| QC-005 | ALL |
| QC-006 | G1, G2, G3, Y_ju1_zhishi_zhonggong, B_zishi, N_chunfen, N_qiufen |
| QC-007 | G1, G2, G3, Z_yin2_zhifu_zhonggong, Z_yin5_dual_zhonggong, Y_ju5, N_qiufen |
| QC-008 | G1, G3, Y_ju1_zhishi_zhonggong, Z_yin5_dual_zhonggong |
| QC-009 | ALL |
| QC-010 | ALL |
| QC-011 | ALL |
| QC-012 | ALL |
| QC-013 | ALL |
| QC-014 | G3, Y_ju1_zhishi_zhonggong, Z_yin2_zhifu_zhonggong, Z_yin5_dual_zhonggong, Y_ju5, N_qiufen |

---

## 4. Policy Decisions（本契约生效基础）

| 决策 | 内容 | 记录 |
|------|------|------|
| D2 | **Option A**: 日号三元近似（1-10/11-20/21-30 → 0/3/6）定为规范行为，契约 v1.0.0 生效；改判真拆补法须 ACP + 主版本递增（v2.0.0） | `QIMEN_FREEZE_GAP.md` Gap 1（Closed） |
| D14 | **晚子时（23:00-24:00）不换日柱**定为规范行为；向量 N_late_zishi 锁定 | `QIMEN_FREEZE_GAP.md` Gap 2（Closed） |

---

## 5. Non-Goals（本契约不含）

- 格局判断 / 吉凶解释 / 用神 / 应期
- 暗干 / 飞盘 / 置闰法 / 真拆补法（D2 改判路径见 QC-004）
- RAG / Consensus / LLM 解释层
- Schema 变更（QimenBoard/QimenCell 冻结于 `docs/SCHEMAS.md §3.3`）

---

## 6. Version Policy

| 变更类型 | 版本动作 |
|----------|----------|
| 契约条款修正（澄清措辞，行为不变） | 1.0.x |
| 冻结行为变更（算法/规则替换，如 D2 改判） | 主版本递增 1.0.0 → 2.0.0 |
| 向量新增（行为不变） | 次版本 1.1.0 |
| 向量修改/删除 | 主版本递增（迁移须 ACP） |
