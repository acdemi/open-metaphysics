# Qimen Rule Decision

> **状态**: 已裁定 — Phase 5.2 Rule Decision & Contract Preparation
> **日期**: 2026-08-09
> **范围**: `src/openmetaphysics/agents/qimen.py` 时家奇门转盘法
> **前置**: `docs/qimen/QIMEN_ALGORITHM_ASSUMPTIONS.md`（D1-D14 假设清单）
> **性质**: 工程决策记录。本文档**不创建** Behavior Contract；Golden Vector
> 分类升级仅为文档层裁定，contract 化需另行 Sprint 授权。
> **Phase 5.6 更新**: D2 政策裁定 Option A（日号近似为规范行为）、D14 裁定
> （晚子时不换日柱）；正式契约已冻结 —
> `docs/specification/QIMEN_BEHAVIOR_CONTRACT.md` v1.0.0。

---

## 1. Decision Summary

| ID | 决策项 | 当前实现 | Decision | Status | Reason |
|----|--------|----------|----------|--------|--------|
| D1 | 阴阳遁切换 | 节气管辖（UTC 判定），冬至(含)→阳遁，夏至(含)→阴遁 | **保留** | **Freeze** | 通行规则；既有测试锁定；无流派分歧 |
| D2 | 三元划分 | 日号 1-10/11-20/21-30 → +0/+3/+6 | **保留（延迟冻结）** | **Deferred** | 日号近似非主流拆补法；替换将失效全部向量与既有测试；需 ACP 级裁定 |
| D3 | 局数公式 | `((节气基本局-1)+三元偏移)%9+1` | **保留** | **Freeze** | 公式稳定；偏移输入依赖 D2（见注 1） |
| D4 | 地盘 | 阳顺/阴逆布六仪三奇；阴遁甲子戊 (10-n) 宫 | **保留** | **Freeze** | 通行规则；经典例核验；无流派分歧 |
| D5 | 值符 | 值符星=旬首宫地盘星；值符随时干 | **保留** | **Freeze** | 通行转盘法；经典例核验（阳遁一局庚午时天蓬落震三） |
| D6 | 天盘 | 地盘按 `(时干宫-旬首宫)mod9` 顺转 | **保留** | **Freeze** | 转盘法几何唯一自洽解 |
| D7 | 值使 | 随时支：本宫起阳顺/阴逆 `(时支-旬首支)mod12` 步 | **保留** | **Freeze** | 通行转盘法；经典例核验（休门逐时顺行至戊辰寄坤二）；见注 2 |
| D8 | 九星天禽 | 天禽参与转盘（不寄宫） | **保留** | **Freeze** | Schema 约束：9 宫 ↔ 9 星一一对应；寄坤需改 Schema（禁止） |
| D9 | 八门 | 值使落宫后洛书序顺布（跳过中宫） | **保留** | **Freeze** | 通行转盘法 |
| D10 | 八神 | 值符神随值符落宫顺布（阴阳遁同向） | **保留** | **Freeze** | 通行转盘法；阴遁逆布为少数派（见注 3） |
| D11 | 空亡 | 时柱旬空二支 → 宫位 | **保留** | **Freeze** | 时家主流；干支规则可独立验证 |
| D12 | 中宫寄宫 | 寄**坤二**宫 | **保留（明确选择寄坤二）** | **Freeze** | 转盘法主流；G3 依赖；寄艮八为罕见派 |
| D13 | 真太阳时 | 有坐标时用真太阳时定时辰；日期/日柱用钟表日 | **保留** | **Freeze** | 复用既有 `core.solar_time`；行为已验证（跨辰例见测试） |
| D14 | 晚子时 | 23:00-24:00 不换日柱 | **保留（延迟冻结）** | **Deferred** | 两派并存；无向量覆盖；零成本保持开放 |

注 1（D3）：局数公式冻结；其"三元偏移"输入源依赖 D2。若 D2 未来被替换
（真拆补法），D3 公式随偏移语义复审，但公式本身（基本局+偏移）预期不变。
注 2（D7）：值使落宫 = 本宫起顺/逆行 `(时支-旬首支) mod 12` 步，落中宫寄坤二。
已由经典例（阳遁一局甲子旬休门逐时顺行）与回归用例（2024-01-01 辰时戊辰时
休门落坤二）双重锁定。
注 3（D10）：冻结为"阴阳遁同向顺布"。若未来裁定阴遁逆布，G2/G3 的
`eight_gods` 全部改变，须走 ACP。

---

## 2. Frozen Rules

以下 12 项规则进入冻结（冻结 = 变更须 ACP 级裁定 + Golden Vector 迁移）：

| # | 冻结规则 | 关键约束 |
|----|----------|----------|
| F1 (D1) | 阴阳遁：节气管辖、UTC 判定、冬至/夏至含边界 | 测试 `test_dun_type_boundary` + 两个节气边界测试 |
| F2 (D3) | 局数公式 `((base-1)+offset)%9+1` | 偏移输入依赖 D2 |
| F3 (D4) | 地盘顺/逆布；阴遁甲子戊 (10-n) 宫 | 纯函数 `earth_placement` 不变量 |
| F4 (D5) | 值符随时干；值符星=旬首宫地盘星 | G1/G2/G3 值符断言 |
| F5 (D6) | 天盘顺转 `(时干宫-旬首宫)mod9` | G1/G3 天盘断言 |
| F6 (D7) | 值使随时支 mod12；落中宫寄坤二 | G1/G3 + 回归用例（戊辰时休门落坤二） |
| F7 (D8) | 天禽参与转盘（9 宫 ↔ 9 星） | 符号唯一性不变量；G1 天禽@兑七 |
| F8 (D9) | 八门洛书序顺布（跳过中宫） | 门唯一性不变量 |
| F9 (D10) | 八神顺布（阴阳遁同向） | G2/G3 八神断言 |
| F10 (D11) | 空亡：时柱旬空 → 宫位映射 | 干支规则独立验证；G1/G2/G3 空亡断言 |
| F11 (D12) | 中宫寄坤二（值符/值使/旬首取门） | G3 + 回归用例 |
| F12 (D13) | 真太阳时定时辰；钟表日定日期/日柱 | 回归用例（11:20 → 巳时） |

冻结规则的可观察行为由 `tests/test_qimen.py::test_frozen_rule_regression`
逐条断言；修改任一冻结规则必须同步更新该测试与 Golden Vectors。

---

## 3. Deferred Rules

| ID | 规则 | 当前行为（保留） | 开放问题 | 解锁条件 |
|----|------|------------------|----------|----------|
| D2 | 三元划分（日号近似） | 1-10/11-20/21-30 → 0/3/6 | 是否迁移真拆补法（符头+超神接气）或置闰法 | 用户/Reference Runtime 裁定；ACP 批准向量迁移 |
| D14 | 晚子时 | 不换日柱 | 换日派 vs 不换日派 | 用户裁定或新增覆盖向量 |

Deferred 不表示行为未定义：当前行为即为工程基线，仅**冻结状态**延迟。

---

## 4. Migration Impact

若未来修改 Deferred 规则（或经 ACP 修改 Frozen 规则）：

| 变更 | Golden Vector 影响 | Behavior Contract 影响 | RuntimeAdapter 影响 |
|------|--------------------|------------------------|---------------------|
| D2 → 真拆补法 | **G1-G3 全部失效**（ju/triple_offset/day_of_month）；`test_triple_offset_correct`、`test_ju_1_to_9_coverage`、节气边界测试局数全变 | 未来奇门 Behavior Contract 的三元条款须先行冻结（本 Sprint 未创建） | 无直接 RuntimeAdapter 影响；Proto/Adapter 仅透传 QimenBoard |
| D2 → 置闰法 | 同上（+ 置闰期输入需新向量） | 同上 | 同上 |
| D14 → 换日柱 | 仅 23:00-24:00 输入；现有向量不受影响；需新增晚子时向量 | 同上 | 同上 |
| D10 → 阴遁逆布 | G2/G3 `eight_gods` 全变 | 同上 | 同上 |
| 任何 Frozen 规则变更 | 受影响的盘面字段全变，需逐向量复核 | 同上 | 同上 |

**迁移通用流程**：ACP 批准 → 修改实现 + 更新 `QIMEN_ALGORITHM_ASSUMPTIONS.md`
与本文档 → 重新生成/人工核验 Golden Vectors → 版本号递增（`QimenEngine.version`
按既有策略 0.3.0 → 0.4.0）→ 全量测试。

---

## 5. Future Extension Boundary

以下内容**不属于**本 Sprint，且当前阶段**明确不实现**（保持未冻结）：

- 格局判断（八门/八神/星门组合吉凶）
- 吉凶解释 / 用神 / 应期
- 暗干 / 鸣法 / 飞盘扩展
- RAG / Knowledge 接入
- Consensus integration
- Reference Runtime 奇门模块 / RuntimeAdapter / Proto 对齐

这些方向属于未来独立 Sprint；本 Sprint 冻结的规则作为它们的输入约束。

---

## 6. Golden Vector 分类（Deliverable 2）

分类规则：`regression` = 仅捕捉非确定性/回归；`candidate normative` =
期望输出经人工独立核验，可作为未来契约基准。**规则冻结不自动产生
Behavior Contract** —— 本文档仅升级文档层分类。

| 向量 | 输入 | 分类 | 冻结依赖 | 说明 |
|------|------|------|----------|------|
| G1 `golden_yang_zhuanpan` | 2024-02-15 12:00 北京 | **candidate normative** | F1-F12（除 D2 偏移字段） | 阳遁转盘主路径；值符/值使经典例核验 |
| G2 `golden_yin_norotation` | 2024-08-15 12:00 北京 | **candidate normative** | F1-F12（除 D2 偏移字段） | 阴遁 + 甲日时干 + 零转盘边界 |
| G3 `golden_yin_zhonggong_jigong` | 2024-08-14 00:30 北京 | **candidate normative** | F1-F12（含 F11 中宫寄坤二） | 值符落中宫寄坤二；D12 已裁定故依赖成立 |

**说明**：三个向量的 `ju`/`triple_offset`/`day_of_month` 字段依赖 D2
（Deferred），故向量整体维持 candidate normative，未升级为 full normative；
冻结规则对应的盘面部分（地盘/天盘/值符/值使/八门/八神/空亡/寄宫）已获裁定。

**Phase 5.3 更新**：Golden Vector 集合已扩展至 **21 个**（新增 18 个，覆盖
阳遁 1-9 局、阴遁 4 局、节气边界、子时、真太阳时跨辰、值符/值使落中宫寄宫、
三奇集中），规范化存储于 **`docs/qimen/golden_vectors.json`**（每向量含
input / expected_board / engine_version / rule_set_version / frozen_rules /
deferred_rules / assumptions_reference）。D2 影响分析见
`docs/qimen/QIMEN_D2_IMPACT_ANALYSIS.md`。

---

## 7. 关联文档

| 文档 | 关系 |
|------|------|
| `docs/qimen/QIMEN_ALGORITHM_ASSUMPTIONS.md` | 假设明细（D1-D14 逐项规则/理由/替代） |
| `docs/qimen/QIMEN_RULE_DECISION.md` | 本文档（裁定结果） |
| `tests/test_qimen.py` | 冻结规则回归 + Golden 校验 + 不变量 |
| `docs/SCHEMAS.md §3.3` | QimenBoard/QimenCell Schema（未修改） |
