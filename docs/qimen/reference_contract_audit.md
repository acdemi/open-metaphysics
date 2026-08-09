# Reference Qimen — 契约符合性审计

> **审计对象**: `reference/qimen/domain.py` + `reference/qimen/astronomy.py`
> **契约**: `docs/specification/QIMEN_BEHAVIOR_CONTRACT.md` v1.0.0 (Frozen)
> **审计日期**: 2026-08-09（Phase 5.7 Alignment Sprint）
> **独立性**: Reference 实现不导入 `src/openmetaphysics` 任何模块
> （由 `reference/tests/test_golden_vectors.py::test_reference_source_independent_of_src` 强制）

## 审计方法

逐契约条目（QC-001~014）对照 Reference 实现源码、契约条款与独立测试套件
（`reference/tests/`）。状态定义：

- **Full**：契约要求有明确对应模块/逻辑，且有独立测试覆盖
- **Equivalent**：实现结构不同，但输出完全满足契约（经向量/抽样验证）
- **Partial**：部分满足，需修正
- **Missing**：不存在对应实现

## 符合性矩阵

| QC | 状态 | 契约要求 | Reference 实现位置 | 独立测试用例 | 说明 |
|----|------|----------|---------------------|--------------|------|
| QC-001 Deterministic Output | **Full** | 相同输入 ⇒ 字节级相同输出；无 I/O/时钟/随机 | `domain.compute()`（纯函数） | `test_golden_vectors.py::test_reference_deterministic` | 信封元数据（computed_at/input_hash）属 Product AgentOutput 层；契约可观察输出 = board JSON，reference 以同构形态输出 |
| QC-002 Nine Palace Completeness | **Full** | 恒 9 宫；palace 1..9 唯一；宫名固定 | `build_board()` cells 构造 | `test_contract_boundaries.py::test_nine_palace_invariants_sample`；24 向量 | - |
| QC-003 Dun Type | **Full** | 节气管辖（UTC），冬至/夏至含边界 | `dun_type_and_base_ju()` + `astronomy.solar_term_time` | `test_contract_boundaries.py::test_winter/summer_solstice_boundary_switch`、`test_dun_type_base_ju_known_dates` | 节气时刻为 core 的规范移植（Meeus 同源），经 24 向量 + 30 抽样验证等价 |
| QC-004 Ju Calculation | **Full** | `((基本局-1)+三元偏移)%9+1`；日号近似（D2 Option A） | `ju_from_day_of_month()` + `build_board()` | 24 向量（阳遁 1-9 局全覆）；`test_lichun_term_switch_ju_recompute` | - |
| QC-005 Earth Plate | **Full** | 阳顺/阴逆布六仪三奇；阴遁甲子戊 (10-n) 宫 | `earth_placement()` | 24 向量（earth_plate 字段） | - |
| QC-006 Heaven Plate | **Full** | 天盘顺转；值符宫天盘干=旬首仪 | `build_board()`（offset 顺转） | 24 向量（sky_plate 字段） | - |
| QC-007 Zhi Fu | **Full** | 值符星=旬首宫星；随时干；八神顺布；中宫寄坤二 | `build_board()`（gods/zhifu） | 24 向量（值符唯一且=落宫） | - |
| QC-008 Zhi Shi | **Full** | 值使随时支 mod12；落中宫寄坤二 | `build_board()`（doors） | 24 向量（Y_ju1/Z_yin5 中宫寄宫向量） | - |
| QC-009 Nine Stars | **Full** | 天盘九星顺转；天禽参与转盘 | `NINE_STARS` + `build_board()` | 24 向量（nine_stars 字段） | - |
| QC-010 Eight Doors | **Full** | 值使后洛书序顺布；中宫不开门 | `build_board()`（doors） | 24 向量；`test_nine_palace_invariants_sample` | - |
| QC-011 Eight Gods | **Full** | 值符神顺布；中宫无神 | `build_board()`（gods） | 24 向量；`test_nine_palace_invariants_sample` | - |
| QC-012 Three Qi | **Full** | 天盘干乙丙丁各一宫 | `build_board()`（three_qi） | 24 向量；`test_nine_palace_invariants_sample` | - |
| QC-013 Void Palace | **Full** | 时柱旬空二支→宫位 | `void_branch_indices()` + `branch_to_palace()` | 24 向量（is_void 字段） | - |
| QC-014 Central Palace Handling | **Full** | 仅 palace 5 is_central；值符/值使落中宫寄坤二 | `build_board()`（is_central/寄宫） | 24 向量；`test_nine_palace_invariants_sample` | - |

## 结果

- **Full: 14/14；Partial: 0；Missing: 0；Equivalent: 0**
- 全部契约条目在 Reference 实现中有明确对应逻辑与独立测试覆盖
- 唯一实现结构差异（Equivalent 性质）说明：节气时刻/真太阳时由
  `astronomy.py` 提供——为 core 共享基础（Meeus 同源算法）的规范移植，
  输出一致性由 24 规范向量验收 + 30 抽样等价证明（
  `reference/tests/test_equivalence.py`）双重强制

## 偏差记录

| 偏差 | 类型 | 处理 |
|------|------|------|
| 无 | - | - |

审计结论：**Reference 实现完全符合 Frozen Contract v1.0.0，无 Missing/Partial，
无偏差闭环项。**
