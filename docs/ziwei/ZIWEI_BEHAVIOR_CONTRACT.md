# Ziwei Behavior Contract

> **状态**: **Frozen** — Phase 6.7.5 Contract Freeze（正式冻结, v1.0.0）
> **contract_id**: `ziwei:behavior:v1.0.0`
> **版本**: 1.0.0
> **冻结日期**: 2026-08-13
> **system**: ziwei
> **engine_version**: 0.3.0（`ZiweiEngine.version`）
> **rule_set_version**: 0.3.0
> **frozen_rules**: ZW-002~011, ZW-013, ZW-015, ZW-016, ZW-017（14 条 FROZEN）
> **implemented_rules**: ZW-001, ZW-012, ZW-014（3 条 IMPLEMENTED, ACP 修订后规范定义）
> **policy_decisions**: 晚子时不换日（A-3）; 时区两级链静默回退（A-4）;
> 闰月月号同值安星 + calendar_note（A-6）; 年干立春界随 BaZi（A-7）
> **Golden Vectors**: `docs/ziwei/golden_vectors.json`（24, **normative fixtures**）
> **Schema 引用**: `src/openmetaphysics/agents/ziwei.py`（ZiweiInput / ZiweiChart /
> Palace）+ `docs/SCHEMAS.md §3.2`
> **相关文档**: `ZIWEI_ALGORITHM_ASSUMPTIONS.md` / `ZIWEI_RULE_DECISION.md` /
> `ZIWEI_DECISION_RESOLUTION.md` / `ZIWEI_GOLDEN_VECTOR_READINESS.md` /
> `ZIWEI_GOLDEN_VECTOR_REPORT.md` / `ZIWEI_FREEZE_REVIEW.md` /
> `ZIWEI_REFERENCE_AUDIT.md` / `ZIWEI_REFERENCE_CERTIFICATION.md` /
> `ZIWEI_CROSS_DOMAIN_BOUNDARIES.md` / `ZIWEI_INTEGRATION_READINESS.md`
> **格式对齐**: `docs/specification/QIMEN_BEHAVIOR_CONTRACT.md`（QC-001~014 结构）/
> `docs/bazi/BAZI_BEHAVIOR_CONTRACT.md`（BC-001~014 编号）
> **历史**: Draft 版本保留于 `docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT_DRAFT.md`（不删除）

**契约性质**: 本契约将 Ziwei 确定性排盘行为（输入校验/时区/时辰/历法/年干/
五虎遁/命身宫/五行局/十二宫/紫微定局/天府镜像/双星系/阴阳标记/能力边界）
固化为规范性要求。任何变更（算法/规则/向量）须经 **ACP**, 并递增契约版本。
Golden Vector 为不可变规范回归装置, 迁移须 ACP。

---

## 1. Freeze Record（冻结记录）

| 项 | 值 |
|----|-----|
| **Frozen version** | **1.0.0** |
| **Freeze date** | **2026-08-13** |
| **Rules covered** | ZW-001 输入校验 / ZW-002 时区 / ZW-003 时辰 / ZW-004 农历 / ZW-005 年干 / ZW-006 五虎遁 / ZW-007 命宫 / ZW-008 身宫 / ZW-009 命宫天干 / ZW-010 五行局 / ZW-011 十二宫 / ZW-012 紫微定局 / ZW-013 天府镜像 / ZW-014 廉贞 / ZW-015 天府星系 / ZW-016 阴阳 / ZW-017 能力边界 |
| **Golden Vector count** | **24**（candidate → normative fixtures） |
| **Policy decisions** | 晚子时不换日（A-3）; 时区两级链无 UTC 兜底（A-4）; 闰月月号同值 + calendar_note（A-6）; 年干立春界随 BaZi（A-7） |
| **Reference requirement** | `reference/ziwei/` 独立实现（不导入 production）须通过 24/24 等价 + BC 审计 |
| **Change procedure** | ACP → 契约版本递增 → Golden Vector 迁移 → Reference 同步更新 + 重新认证 |
| **Review evidence** | `ZIWEI_FREEZE_REVIEW.md`（PASS）; `ZIWEI_REFERENCE_AUDIT.md`（14/14 PASS）; `ZIWEI_INTEGRATION_READINESS.md`（7/7 PASS） |

---

## 2. Contract Metadata

| 项 | 值 |
|----|-----|
| contract_id | ziwei:behavior:v1.0.0 |
| version | 1.0.0 |
| status | **Frozen** |
| system | ziwei |
| engine_version | 0.3.0 |
| rule_set_version | 0.3.0 |
| frozen_rules | ZW-002, ZW-003, ZW-004, ZW-005, ZW-006, ZW-007, ZW-008, ZW-009, ZW-010, ZW-011, ZW-013, ZW-015, ZW-016, ZW-017 |
| implemented_rules | ZW-001, ZW-012, ZW-014 |
| policy_decisions | 晚子时不换日（A-3）; 时区两级链无 UTC 兜底（A-4）; 闰月月号同值 + 记录（A-6）; 年干立春界（A-7） |
| vector_store | docs/ziwei/golden_vectors.json（24, normative fixtures） |
| schema_ref | ZiweiInput / ZiweiChart / Palace（agents/ziwei.py）+ SCHEMAS.md §3.2 |
| test_refs | tests/test_ziwei.py（33）+ test_ziwei_golden_vectors.py（7）+ reference/tests/test_ziwei_equivalence.py（4） |

---

## 3. Contract Clauses

### BC-001 Deterministic Output

- **Definition**: 相同输入 ⇒ 字节级相同输出（`computed_at` 信封除外）。
- **Preconditions**: `ZiweiInput` 合法（born_at 必须 tz-aware; 显式农历须同给同省）。
- **Deterministic requirement**: 无随机、无系统时钟、无 I/O、无 LLM; 计算为输入纯函数;
  `sxtwl==2.0.7` 精确锁定（历法原语, ACP-ZW-004）。
- **Observable output**: 两次计算 `ZiweiChart.model_dump(mode="json")` 逐字节一致。
- **Related rules**: 引擎契约（DeterministicEngine）。
- **Golden vectors**: ALL（24）。
- **Test references**: `test_determinism`（golden）; `test_replay_identical`。

### BC-002 Input Schema & Validation（ZW-001）

- **Definition**: 输入 = `ZiweiInput`（request_id / born_at(tz-aware) /
  born_location? / gender / question? / locale / seed? / client_nonce? /
  lunar_month? / lunar_day?）。**显式农历优先于公历转换**; 校验:
  `lunar_month ∈ [1,12]`, `lunar_day ∈ [1,30]`, **两字段同给同省**;
  越界/部分提供 → **ValueError**（API 层 422）, 不得以 KeyError 从查表泄漏。
- **Preconditions**: born_at 必须 tz-aware。
- **Deterministic requirement**: 校验器与 schema `extra="forbid"` 固定。
- **Observable output**: 合法输入输出不变; 非法输入 → ValueError/422。
- **Related rules**: ZW-001（IMPLEMENTED, ACP-ZW-003）。
- **Golden vectors**: ZV-pos-001~004（显式农历路径）, ZV-ref-001。
- **Test references**: `test_lunar_input_out_of_range_rejected`; `test_user_provided_lunar_used_directly`。

### BC-003 Timezone Resolution（ZW-002）

- **Definition**: 本地时区解析顺序: `born_location.timezone`（ZoneInfo）→
  `born_at.tzinfo`。**两级链, 无 UTC 兜底**; 非法时区 → **静默回退**
  `born_at.tzinfo`（无警告、无 metadata 标记）。
- **Preconditions**: born_at 必须 tz-aware（因此两级链与 BaZi 三级链行为等价,
  ZB-06 声明差异）。
- **Deterministic requirement**: 回退规则固定（D-ZW-2, A-4 裁定 FROZEN）。
- **Observable output**: 本地时区相关输出（时辰/命身宫/农历日）。
- **Related rules**: ZW-002, BC-004, BC-005。
- **Golden vectors**: ZV-tz-001（+08:00 无 location）, ZV-tz-002（UTC+0 同时刻,
  命宫不同）, ZV-tz-003（非法时区 == tz-001）。
- **Test references**: `test_timezone_changes_fate_palace`; `test_no_location_uses_born_tzinfo`; `test_timezone_invalid_fallback`。

### BC-004 Hour Branch（ZW-003）

- **Definition**: 时支 = `((local.hour + 1) // 2) % 12`（0=子 … 11=亥）;
  **子时 = 23:00~00:59**（钟表时）; **不使用真太阳时**（与 Qimen D13 差异,
  ZW-003 声明）。
- **Preconditions**: 本地时区按 BC-003 解析。
- **Deterministic requirement**: 钟表时, 无真太阳时修正。
- **Observable output**: 命身宫（依赖 hour_idx）、时辰窗切换（命宫差 1）。
- **Related rules**: ZW-003, BC-003, BC-008。
- **Golden vectors**: ZV-hour-001（22:59 亥）, ZV-hour-002（23:00 子）,
  ZV-lun-005（23:30 子）。
- **Test references**: `test_hour_window_boundary_2259_vs_2300`。

### BC-005 Lunar Conversion & Late Zi Hour（ZW-004）

- **Definition**: 公历→农历经 `sxtwl==2.0.7`（`core/calendar.py` 共享原语）,
  取**本地民用日期**; **晚子时（23:00 后）不换日**（农历日 = 民用日,
  A-3 裁定 FROZEN, 与 Qimen D14 一致 / 与 BaZi BC-004 差异 ZB-01）;
  **闰月按月号同值安星** + `calendar_note` 记录（A-6 裁定 FROZEN）。
- **Preconditions**: 本地时区按 BC-003。
- **Deterministic requirement**: sxtwl 版本精确锁定（ACP-ZW-004）;
  闰月"同值"策略固定（D-ZW-4）。
- **Observable output**: 命身宫（lunar_month/day）、紫微定局（lunar_day）、
  `calendar_note`（闰月时非空）。
- **Related rules**: ZW-004, BC-008, BC-011。
- **Golden vectors**: ZV-lun-001（2024-05-01→3/23）, ZV-lun-002（春节 1/1）,
  ZV-lun-003（闰二月 note）, ZV-lun-005（23:30 同日）, ZV-hour-001/002（同日）。
- **Test references**: `test_lunar_conversion_2024_05_01`; `test_lunar_conversion_2024_02_10`;
  `test_lunar_conversion_leap_month_2023`; `test_leap_month_placement_uses_month_number`。

### BC-006 Year Stem Lichun Boundary（ZW-005）

- **Definition**: 年干以**立春**（UTC 时刻）为界, 复用 BaZi 原语
  `bazi_year_index`（**引用而非重复实现**）; 年序 `(立春年-4)%60`。
- **Preconditions**: 无。
- **Deterministic requirement**: 立春时刻与 BaZi 共享确定（approx_1min）。
- **Observable output**: `yin_yang` 标记（阳年/阴年, 见 BC-013）。
- **Related rules**: ZW-005, BC-013。
- **Golden vectors**: ZV-lun-004（立春后 1h → 甲辰, yang）。
- **Test references**: `test_yin_yang_lichun_boundary`; `test_yin_yang_year_stem`。

### BC-007 WuHu Dun（ZW-006）

- **Definition**: 寅月干 = `(year_stem_idx * 2 + 2) % 10`（甲己起丙寅）;
  十二宫干 = `(yin_month_stem + palace_index) % 10`。
- **Preconditions**: 年干按 BC-006。
- **Deterministic requirement**: 五虎遁表固定。
- **Observable output**: 十二宫 `heavenly_stem`; 命宫天干（BC-009）。
- **Related rules**: ZW-006, BC-009, BC-010。
- **Golden vectors**: ZV-ref-001~004（全盘干支）。
- **Test references**: `test_palace_stems_follow_wuhu_dun`。

### BC-008 Ming/Shen Palace Position（ZW-007, ZW-008）

- **Definition**: `ming = ((lunar_month - 1) - hour_idx) % 12`（寅=0, 逆数生时）;
  `shen = ((lunar_month - 1) + hour_idx) % 12`（顺数生时）。
- **Preconditions**: 农历月按 BC-005, 时辰按 BC-004。
- **Deterministic requirement**: 公式固定（ZW-007/008 Freeze Candidate 确认 FROZEN）。
- **Observable output**: `fate_palace_index` / `body_palace_index`;
  对应宫位 `is_fate_palace` / `is_body_palace`。
- **Related rules**: ZW-007, ZW-008, BC-004, BC-005。
- **Golden vectors**: ZV-ref-001（命宫子/身宫辰）; 全部向量含命/身宫。
- **Test references**: `test_fate_palace_canonical`; `test_body_palace_position`;
  `test_ming_shen_formula_sweep`。

### BC-009 Ming Palace Stem & WuXing Ju（ZW-009, ZW-010）

- **Definition**: `ming_stem = (yin_month_stem + ming_index) % 10`;
  五行局 = 命宫干支**纳音末字** → `{元素}{数}局`（水2/木3/金4/土5/火6,
  输出格式为规范, 如 "水2局"）。
- **Preconditions**: 命宫按 BC-008, 干支按 BC-007。
- **Deterministic requirement**: 纳音表（60 组）固定; 局名格式
  `"{元素}{数}局"` 为规范（书写形式"水二局"等非契约值）。
- **Observable output**: `wuxing_ju`。
- **Related rules**: ZW-009, ZW-010, BC-008, BC-011。
- **Golden vectors**: ZV-ju-001~005（5 局全类型）; ZV-ref-001~004。
- **Test references**: `test_wuxing_ju_all_five_elements`; `test_wuxing_ju_nayin_invariant`。

### BC-010 Twelve Palace Layout（ZW-011）

- **Definition**: 宫 i（0..11, 寅=0 顺行）: 干 = `(yin_month_stem + i) % 10`,
  支 = 固定表 `PALACE_BRANCHES`（寅卯辰巳午未申酉戌亥子丑）, 名 =
  `PALACE_NAMES[(ming - i) % 12]`（命/兄弟/夫妻/子女/财帛/疾厄/迁移/奴仆/
  官禄/田宅/福德/父母）; 命/身宫标志按 BC-008。
- **Preconditions**: 无。
- **Deterministic requirement**: 名称/地支表固定。
- **Observable output**: `palaces[*]`（index/name/earthly_branch/heavenly_stem/
  is_fate_palace/is_body_palace）。
- **Related rules**: ZW-011, BC-007, BC-008。
- **Golden vectors**: ZV-ref-001~004。
- **Test references**: `test_all_12_palaces_have_correct_names`; `test_all_palaces_have_stem_branch`; `test_palace_names_positions_mapping`。

### BC-011 Ziwei Placement（ZW-012, A-1）

- **Definition**: 紫微位置 = **统一生成式**
  `idx = (START[ju] + (lunar_day - 1) // STEP[ju]) % 12`
  （寅=0）; START = {水2:丑(11), 木3:辰(2), 金4:亥(9), 土5:午(4), 火6:酉(7)},
  STEP = {水2:2, 其余:3}。**结构不变式**: 木三不落寅卯 / 金四不落酉戌 /
  土五不落辰巳 / 火六不落未申。
- **Preconditions**: 五行局按 BC-009, 农历日按 BC-005。
- **Deterministic requirement**: 生成式固定（ACP-ZW-001 实施; 原硬编码表废弃）。
- **Observable output**: 紫微所在宫位 `main_stars`。
- **Related rules**: ZW-012（IMPLEMENTED）, BC-012, BC-009, BC-005。
- **Golden vectors**: ZV-ju-001~005（5 局）; ZV-pos-001（day1）/002（day30）/
  003（局间）/004（覆盖路径）; ZV-inv-001（day23）。
- **Test references**: `test_ziwei_pos_values_snapshot`; `test_ziwei_pos_table_structure`;
  `test_user_lunar_override_flows_into_placement`。

### BC-012 Tianfu Mirror & Star Systems（ZW-013, ZW-014, ZW-015, A-2）

- **Definition**: 天府 = `(-紫微) % 12`（寅申轴对称, ZW-013）;
  **紫微星系**: 紫微0 / 天机-1 / 太阳-3 / 武曲-4 / 天同-5 / 廉贞**-8**（mod 12,
  ZW-014, ACP-ZW-002 实施）; **天府星系**: 天府0 / 太阴+1 / 贪狼+2 / 巨门+3 /
  天相+4 / 天梁+5 / 七杀+6 / 破军+10（ZW-015）。
  **恒等式**: "紫微在子午, 廉贞天府同度辰戌" 成立（A-2 专项验证）。
- **Preconditions**: 紫微位置按 BC-011。
- **Deterministic requirement**: 偏移表固定; 每宫 `main_stars` 顺序固定。
- **Observable output**: 十四主星全盘位置（每星恰一次, 共 14）。
- **Related rules**: ZW-013, ZW-014（IMPLEMENTED）, ZW-015, BC-011。
- **Golden vectors**: ZV-inv-001（紫微在子, 廉贞天府同度辰）; ZV-lun-004;
  ZV-ju-004 / ZV-hour-001/002 / ZV-lun-005（紫微在午, 同度戌）; 全部向量含
  14 星断言。
- **Test references**: `test_ziwei_tianfu_mirror_relationship`; `test_ziwei_tianfu_mirror_multiple_ju`;
  `test_ziwei_xingxi_offsets`; `test_tianfu_xingxi_offsets`; `test_14_major_stars_all_present`。

### BC-013 Yin/Yang Mark & Capability Boundary（ZW-016, ZW-017）

- **Definition**: `yin_yang = "yang" if 年干阳 else "yin"`（固定阴阳表, ZW-016）;
  **未实现能力边界**（ZW-017）: 辅星/杂曜/四化/大限/流年**未实现**,
  `auxiliary_stars` 恒空, `gender` 继承但 Engine 从不读取,
  metadata `star_placement="14_major_stars"`。任何新增能力须 ACP。
- **Preconditions**: 年干按 BC-006。
- **Deterministic requirement**: 边界声明固定（gender/yin_yang 未来用途
  四化/大限, 属后续授权 Sprint）。
- **Observable output**: `yin_yang`; `auxiliary_stars`（恒空）; metadata。
- **Related rules**: ZW-016, ZW-017, BC-006。
- **Golden vectors**: ZV-ref-002（yin）, ZV-lun-004（yang）, ZV-ref-001~003（aux 空）。
- **Test references**: `test_yin_yang_year_stem`; `test_aux_stars_always_empty`; `test_metadata_updated`。

### BC-014 Golden Vectors

- **Definition**: `docs/ziwei/golden_vectors.json` 24 向量为**规范回归装置**
  （normative fixtures, 冻结后不可变; 迁移须 ACP）。
- **Preconditions**: 无。
- **Deterministic requirement**: 24/24 与 Engine v0.3.0 输出逐字节一致
  （确定性 + 重放 + 序列化三重锁定; Reference 24/24 等价）。
- **Golden vectors**: 自身。
- **Test references**: `tests/test_ziwei_golden_vectors.py`（7 例）;
  `reference/tests/test_ziwei_equivalence.py`（4 例）。

---

## 4. 契约范围外（显式排除）

| 项 | 说明 |
|----|------|
| 辅星/杂曜/四化/大限/流年 | 未实现（ZW-017 边界, 新增须 ACP） |
| 格局识别（pattern_matcher） | 解释域（A-8 记录: 链路断裂, 属解释域 Sprint） |
| 解释层 / 叙述 / 建议 / LLM / RAG / Consensus | Domain Boundary（ARCHITECTURE.md §1） |
| 真太阳时 | 不采用（BC-004 声明; 与 Qimen D13 差异） |

---

## 5. 跨域边界声明（引用 ZIWEI_CROSS_DOMAIN_BOUNDARIES.md）

| 边界 | Ziwei（本契约） | 对照域 | 说明 |
|------|-----------------|--------|------|
| ZB-01 晚子时 | **不换日**（BC-005, A-3 FROZEN） | BaZi 23:00 换日（BC-004） | 真实差异, 已登记 |
| ZB-06 时区回退 | 两级链无 UTC 兜底（BC-003, A-4 FROZEN） | BaZi 三级链含 UTC（BC-012） | 链定义差异, born_at 强制 tz-aware 下行为等价 |
| ZQ-02 晚子时日柱 | 不换日 | Qimen D14 不换日 | 巧合一致 |
| （无编号）时辰 | 钟表时, 不用真太阳时（BC-004） | Qimen 用真太阳时（D13） | 真实差异, 已登记 |

---

## 6. Change Procedure（变更流程）

冻结后任何变更（算法/规则/向量/schema）必须完整执行:

1. **ACP**（Architecture Change Proposal, 等待人工批准）
2. **Contract version increment**（v1.0.0 → 下一版本）
3. **Golden Vector migration**（24 向量不可原地修改, 生成新向量集）
4. **Reference re-certification**（`reference/ziwei/` 同步更新 + 24/24 等价 +
   BC 审计重新通过）

引用位置: 本契约 §1 Freeze Record / §6 / `CAPABILITY_STATUS.md` Ziwei 节 /
`ZIWEI_INTEGRATION_READINESS.md` §2（变更政策正式引用）。
