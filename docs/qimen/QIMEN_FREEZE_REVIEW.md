# Qimen Freeze Candidate Review

> **状态**: Phase 5.4 — Architecture Governance / Domain Review
> **日期**: 2026-08-09
> **范围**: Qimen Product Runtime（`src/openmetaphysics/agents/qimen.py`）
> **评审输入**: QIMEN_RULE_DECISION.md / QIMEN_ALGORITHM_ASSUMPTIONS.md /
> QIMEN_D2_IMPACT_ANALYSIS.md / golden_vectors.json / qimen.py / test_qimen.py
> **结论**: **PASS WITH CONDITIONS**（运行时冻结候选成立；契约化须先满足条件）
> **性质**: 评审文档。未创建 Behavior Contract，未修改任何算法。
> **Phase 5.6 更新**: 评审条件已全部关闭 —— D2/D14 政策裁定完成、3 个
> 缺口向量已补齐、契约已冻结
> （`docs/specification/QIMEN_BEHAVIOR_CONTRACT.md` v1.0.0 Frozen）。
> 评审结论升级为 **PASS（正式冻结）**。

---

## 1. Review Scope & Method

- **冻结规则一致性**：对 D1/D3-D13 逐条核对 规则定义 → 实现位置 → 测试覆盖 →
  Golden Vector 覆盖 → 风险；并做跨规则链条一致性核查。
- **Deferred 影响**：D2/D14 分别按"阻塞 / 非阻塞技术债"分类。
- **向量充分性**：21 向量按 局数/阴阳遁/节气/时辰/中宫/真太阳时 六维评估。
- **契约就绪度**：评估当前状态生成 Behavior Contract / Conformance Test /
  Reference Runtime 实现的能力与前置条件（不创建契约）。
- **架构边界**：git 工作区核实修改范围。

---

## 2. Frozen Rule Review（Task A）

### 2.1 逐条评审表

| Rule | 规则定义 | 实现位置 (qimen.py) | 测试覆盖 | Golden 覆盖 | 风险 |
|------|----------|---------------------|----------|-------------|------|
| D1 阴阳遁 | 节气管辖（UTC 判定），冬至(含)→阳遁，夏至(含)→阴遁；管辖节气 = 24 节气中最后一个 ≤ 时刻 | `dun_type_and_base_ju` | `dun_type_boundary`、`winter_solstice_boundary_switch`、`summer_solstice_boundary_switch`、F1 | 21/21（dun_type）；冬至/夏至/立春 边界 6 向量 | **Low**（主流，双边界测试锁定） |
| D3 局数公式 | `ju = ((节气基本局-1)+三元偏移)%9+1`，基本局 = 节气在遁序序号 | `build_palaces` | `ju_range`、`ju_1_to_9_coverage`、F2 | 21/21（ju 1-9 全覆） | **Low**（纯算术，输入源 D2 依赖已声明） |
| D4 地盘 | 阳顺/阴逆布六仪三奇；阴遁 n 局甲子戊 (10-n) 宫 | `earth_placement` | `earth_placement_invariants`（18 组）、F3、`ju_1_to_9_coverage` | 21/21（earth_plate） | **Low**（经典规则无流派分歧） |
| D5 值符 | 值符星 = 旬首六仪宫地盘星；值符随时干（时干宫 = 值符落宫；时干为甲取旬首宫） | `build_palaces` | `zhifu_zhishi_on_boards`、G1/G3 语义、F4、`hour_plan_consistency` | 21/21（八神值符/星/天盘干） | **Low**（经典例核验） |
| D6 天盘 | 天盘 = 地盘按 `(时干宫-旬首宫)mod9` 顺转 | `build_palaces` | F5、`hour_plan_consistency`、`golden_vector_yin_norotation_semantics` | 21/21；零转盘 3 向量（G2/B_zishi/Y_ju1） | **Low**（转盘法几何唯一自洽解） |
| D7 值使 | 值使门 = 旬首宫门；随时支：本宫起阳顺/阴逆 `(时支-旬首支)mod12` 步；落中宫寄坤二 | `build_palaces` | F6、`zhifu_zhishi_on_boards`、G1/G3 语义 | 21/21（eight_doors）；值使落中宫 2 向量（Y_ju1/Z_yin5） | **Medium**（流派差异已注记；经典例+回归双锁） |
| D8 九星天禽 | 天禽参与转盘（9 宫 ↔ 9 星一一对应，不寄宫） | `build_palaces` | `nine_stars_correct`、`symbol_uniqueness`、F7 | 21/21；天禽为值符星（旬首在中宫）1 向量（Y_ju5） | **Low-Med**（Schema 约束下唯一可行；简化已注记） |
| D9 八门 | 值使落宫后其余门按洛书宫序顺布（跳过中宫） | `build_palaces` | F8、`nine_palace_completeness` | 21/21（eight_doors） | **Low** |
| D10 八神 | 值符神随值符落宫顺时针顺布（阴阳遁同向） | `build_palaces` | F9（逐位序断言）、`symbol_uniqueness` | 21/21（eight_gods） | **Medium**（阴遁逆布为少数派，变更需 ACP） |
| D11 空亡 | 时柱旬空二支 → 宫位（坎子/艮丑寅/震卯/巽辰巳/离午/坤未申/兑酉/乾戌亥） | `void_branch_indices` + `PALACE_BRANCHES` | `void_branch_invariants`（6 旬全检）、`void_palace_rule`、F10 | 21/21（is_void）；单宫/双宫空亡均覆盖 | **Low**（干支规则可独立验证） |
| D12 中宫寄坤二 | 值符/值使落中宫→寄坤二；旬首在中宫→取坤二门 | `build_palaces` | F11、G3 语义、`golden_vector_yin_zhonggong_jigong_semantics` | 4 中宫向量（G3/Y_ju1/Z_yin2/Z_yin5） | **Medium**（流派选择，主流；已显式裁定） |
| D13 真太阳时 | 有坐标 → 真太阳时定时辰；日期/日柱用钟表日 | `effective_hour` | F12（跨辰例）、`golden_vector_yin_norotation_semantics` | 21/21（均带 born_location）；跨辰 1 向量（B_truesolar） | **Low**（复用 core.solar_time，行为已验证） |

### 2.2 跨规则一致性核查（内部矛盾检查）

| 链条 | 一致性 | 验证 |
|------|--------|------|
| D4→D5→D6 | 地盘定旬首宫 → 值符星 → 天盘顺转 | 18 新向量生成期逐盘断言 `sky[时干宫]==旬首仪` 且 `offset==(时干宫-旬首宫)mod9` ✅ |
| D4→D7→D9 | 地盘定旬首宫门 → 值使落宫 → 八门旋转 | 逐盘断言 `doors[值使落宫]==值使门` ✅ |
| D5/D7→D12 | 值符/值使落中宫寄坤二 | Z_yin2（值符寄）、Y_ju1/Z_yin5（值使寄）、Z_yin5（双寄）✅ |
| D5→D8 | 旬首在中宫时值符星 = 天禽 | Y_ju5：甲子戊@中五宫，值符天禽随甲子时干落宫 ✅；Z_yin2 为值符星（天柱）落中宫型 |
| D1→D3 | 节气→基本局无重叠（阳 12 + 阴 12） | 位置序号映射互斥 ✅ |
| D13→D1 | 真太阳时（时辰）与 UTC 节气判定无交互 | 两条独立输入轴，无冲突 ✅ |

**结论：12 条冻结规则内部一致，无矛盾。** 全部规则均有实现、测试、向量三重要素对应。

---

## 3. Deferred Decision Review（Task B）

### D2 三元划分 — 分类：**B. Non-blocking technical debt**

- **是否存在隐藏不一致**：存在一种系统性近似特征（非引擎缺陷）：日号 1-10/11-20/21-30
  的三元窗口与节气时刻不对齐 —— 月中开始的节气（如大寒 1/20）在其当月永远没有
  "上元"日号窗口。该行为**显式记录**于 QIMEN_ALGORITHM_ASSUMPTIONS.md（D2）与
  QIMEN_D2_IMPACT_ANALYSIS.md §1，向量与测试按同一规则一致编码 —— 属
  "已文档化的近似"，非"隐藏不一致"。
- **是否阻止 Reference Candidate**：**不阻止**运行时冻结候选 —— 行为稳定、
  可复现、可回归（21 向量 + 33 测试锁定）。但**阻止 ju/三元字段升级为
  normative**（向量整体维持 candidate normative），故契约 Sprint 必须显式声明
  "日号近似为既定规范"或先裁定真拆补法。
- **现在替换是否可行**：技术上可行（实现 ~60 行），但需 ACP + 21 向量全量迁移 +
  6+ 测试更新（影响量化见 D2 分析文档）。当前阶段无收益优先，**维持 Deferred**。
- **结论**：非阻塞技术债。不构成 Freeze 阻塞项。

### D14 晚子时 — 分类：**B. Non-blocking technical debt**

- **当前行为**：23:00-24:00 时支 = 子（当日），不换日柱。
- **缺失覆盖**：21 向量中 0 个位于 23-24 点；相关代码路径仅由
  `test_invariant_sweep_full_year`（含 23:00 输入）与随机 100 盘覆盖。
- **冻结影响**：若现在冻结"不换日"，是零向量支持的学派裁定；若冻结"换日"，
  同样无依据。两派并存且行为确定 —— 维持 Deferred 成本为零。
- **结论**：非阻塞。建议在契约 Sprint 内新增 1 个晚子时向量后再裁定。

---

## 4. Golden Vector Adequacy（Task C）

### 4.1 覆盖矩阵

| 维度 | 覆盖 | 状态 |
|------|------|------|
| 局数 | 阳遁 1-9 **全覆**；阴遁 {2,3,5,7}（4 局，≥3 要求） | **PASS** |
| 阴阳遁 | 阳 12 向量 / 阴 9 向量，双遁零转盘/转盘均有 | **PASS** |
| 节气 | 12/24 节气（冬至 小寒 大寒 立春 雨水 惊蛰 清明 芒种 夏至 小暑 立秋 大雪）；阳遁序列 8/12、阴遁序列 4/12；节气切换对（立春/夏至）+ 阴阳遁切换对（冬至/夏至） | **PASS（有缺口）** |
| 时辰 | 时支覆盖 子丑寅卯辰巳午（小时 0/1/3/6/8/10/11/12）；无 未申酉戌亥、无 23-24 点 | **PASS（D14 相关缺口）** |
| 中宫 | 值符落中宫 ×3（G3/Z_yin2/Z_yin5）、值使落中宫 ×2（Y_ju1/Z_yin5）、旬首在中宫取门（Z_yin2） | **PASS** |
| 真太阳时 | 21/21 均带坐标（真太阳路径全覆盖）；跨辰显式向量 ×1（B_truesolar） | **PASS（无坐标回退路径仅测试覆盖）** |

### 4.2 判定：**达到 Candidate Freeze 最低覆盖**

- 局数空间（阳 1-9 + 阴 4 局）、双遁方向、阴阳切换边界、中宫寄宫、真太阳时
  跨辰 —— 全部达到。
- 未覆盖节气（12 个）走完全相同的代码路径（节气→序号→基本局 + 三元偏移 +
  边界判定），风险可忽略；契约 Sprint 建议补 2 向量（春分/秋分 各一）消除
  语义盲区。
- 晚子时缺口与 D14 Deferred 一致，属有意为之。

---

## 5. Contract Readiness（Task D）

### 5.1 生成能力评估（不创建契约）

| 目标产物 | 当前就绪度 | 缺失前置条件 |
|----------|------------|--------------|
| **Behavior Contract** | 高 —— 12 条冻结规则可直译为契约条款；21 向量可作契约 fixtures | (1) 契约 Schema/格式裁定（可参照 `reference/contracts/*.json` 模式）；(2) D2 近似在契约文本中的显式声明；(3) ACP 批准 |
| **Conformance Tests** | 高 —— `golden_vectors.json` 结构化可直接被 conformance runner（`reference/conformance_runner.py` 模式）消费 | 决定向量→conformance fixture 的映射格式（含 input 规范化） |
| **Reference Runtime 实现** | 中 —— 逻辑纯 Python、无 sxtwl 依赖（仅 `solar_term_time`/`sexagenary_day_index` 纯函数 + 静态表），可移植 | 契约冻结先行；Reference qimen 域 Sprint 计划（ACP） |

### 5.2 契约化前置条件清单

1. D2：契约文本显式声明"日号近似三元为既定规范"（或先裁定真拆补法）
2. D14：新增晚子时向量 1 个后裁定
3. 补 2 个中段节气向量（春分/秋分）
4. 契约格式裁定 + ACP
5. 引擎版本若在契约化中变更 → 0.3.0 → 0.4.0 并全量迁移

---

## 6. Architecture Boundary Review（Task E）

```
git status 核实:
  M src/openmetaphysics/agents/qimen.py   (Phase 5 遗留, 本 Sprint 零改动)
  M tests/test_qimen.py                   (测试层)
  ?? docs/qimen/                          (评审产物)
  reference/   未修改 ✅   contracts/  未修改 ✅
  specification/ 未修改 ✅   proto/      未修改 ✅
  其他 Agent   未修改 ✅
```

- RuntimeAdapter：**不需要** —— 当前无跨语言实现（Rust/Go 未启动），Qimen 仅
  Python 运行时；Adapter 属未来多语言 Sprint 的产物。
- 本 Sprint 约束全满足：未改算法、未改冻结规则、未解 D2、未建契约、
  未加解释层/RAG/Consensus。

---

## 7. Freeze Decision

# **PASS WITH CONDITIONS**

| 项 | 判定 |
|----|------|
| 冻结规则内部一致性 | ✅ 12/12 一致，无矛盾（§2.2） |
| Golden Vector 充分性 | ✅ 达到候选冻结最低覆盖（§4） |
| Deferred 阻塞性 | ✅ D2/D14 均为非阻塞技术债（§3） |
| 运行时稳定性 | ✅ 404 tests / 21 向量 / 100 随机盘 / 确定性 JSON |
| 架构边界 | ✅ 无越界（§6） |

**Conditions（进入正式契约化的前置）**：
1. 契约 Sprint 中显式声明 D2 日号近似的规范地位（或裁定真拆补法）
2. 契约 Sprint 中补 2 个中段节气向量 + 1 个晚子时向量
3. 所有未来规则变更仍须 ACP + 版本递增 + 向量迁移（既有流程）

---

## 8. Future Roadmap

| 步骤 | 内容 | 前置 |
|------|------|------|
| **1. Qimen Behavior Contract Sprint**（推荐下一步） | 12 冻结规则 → 契约条款；21 向量 → 规范 fixtures；补 春分/秋分/晚子时 3 向量；D2 近似规范声明 | 本评审 PASS；ACP |
| **2. Reference Runtime Qimen Domain Sprint** | 依契约在 `reference/` 实现奇门域（Rule/Pattern 层已有基础） | 契约冻结 |
| **3. 功能扩展 Sprint** | 格局判断 / 用神 / 应期（新授权） | 任选 |
| **4. Consensus integration** | Qimen 盘面 → Evidence/Consensus | 契约冻结后 |
