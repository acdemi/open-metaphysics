# Phase 5.1 — Qimen Algorithm Stabilization Review 交付报告（存档）

> **归档日期**: 2026-08-09
> **原始场景**: Algorithm Review + Documentation
> **状态**: 已交付（后续演进见 Phase 5.2/5.3/5.4 存档）

---

## 1. Review Summary

对 `qimen.py` 全量复核 + 330 盘批量扫描（全年各月、冬至/夏至边界 ±1h、午夜时辰），**零异常**：

- ✅ 未发现新 bug；Phase 5 的 11 项假设均显式存在于模块 docstring
- ✅ 值符/值使规则经经典例独立核验（阳遁一局庚午时值符天蓬落震三；休门甲子坎一→乙丑坤二→…→戊辰中五寄坤二）
- ✅ 阴遁地盘公式修复（Phase 5）经 18 组纯函数不变量锁定
- ⚠ 识别最高替换风险项：**三元划分**（D2，日号近似，非真拆补法）

## 2. 新增文档

**`docs/qimen/QIMEN_ALGORITHM_ASSUMPTIONS.md`** — 14 项决策逐项记录：当前规则 / 选择理由 / 替代流派 / 可替换性 / Golden 影响。含 Phase 5 修复记录表、Golden Vector 分类、不变量清单、剩余风险。

## 3. Algorithm Decisions Table（14 项，详见文档 §2）

| # | 决策 | 可替换性 | 最高风险 |
|---|------|---------|---------|
| D1 | 阴阳遁（节气管辖，UTC 判定） | 低 | - |
| D2 | **三元（日号 1-10/11-20/21-30）** | **高** | ⚠ 真拆补法会失效全部向量 |
| D3 | 局数 `((base-1)+off)%9+1` | 中 | 固定局表替代时全变 |
| D4 | 地盘顺/逆布 | 低 | - |
| D5 | 值符随时干（旬首星） | 低~中 | - |
| D6 | 天盘顺转 | 低 | - |
| D7 | **值使步数 mod 12** | 中 | ⚠ 流派差异 |
| D8 | 九星（天禽不寄坤） | 中 | 简化 |
| D9 | 八门顺布 | 低~中 | - |
| D10 | 八神顺布 | 中 | 阴遁逆布派 |
| D11 | 空亡（时柱旬空→宫位） | 低 | - |
| D12 | 中宫寄坤二 | 中 | 寄宫方向 |
| D13 | 真太阳时定时辰 | 低 | - |
| D14 | 晚子时不换日 | 低 | - |

## 4. Golden Vectors 分类（详见文档 §5）

| 向量 | 分类 |
|------|------|
| G1 阳遁转盘 (2024-02-15) | **candidate normative** |
| G2 阴遁零转 (2024-08-15) | **candidate normative** |
| G3 中宫寄宫 (2024-08-14) | **candidate normative（依赖 D12 流派选择，冻结前须裁定寄宫）** |
| 节气边界对 ×2（冬至/夏至 ±1h） | candidate normative |

全部向量兼作确定性回归向量（逐字节断言）。**未转换为 Behavior Contracts**（遵任务要求）。

## 5. 新增不变量测试（+3，共 27 个 qimen 测试）

- `test_invariant_sweep_full_year` — 56 盘跨年扫描：九宫完整性、符号唯一、无非法宫状态、空亡 1~2 宫、三奇唯一
- `test_hour_plan_consistency` — HourPlan 与盘面自洽（旬首宫/值符宫/甲时干宫/天盘干=旬首仪）
- `test_symbol_uniqueness` — 每类符号恰好出现一次

## 6. Remaining Risks

| 风险 | 等级 |
|------|------|
| D2 三元为日号近似，与主流拆补法结果可能不同 | **高** |
| D7 值使步数 / D10 八神方向流派差异 | 中 |
| D8/D12 天禽与寄宫为简化/流派选择 | 中 |
| Golden 未覆盖 1~4 局、晚子时、真太阳时跨辰边界 | 低 |

## 7. Recommendation for Phase 5.2

1. **裁定流派**：优先决议 D2（拆补法真元 vs 保持日号近似）与 D12（寄宫方向）；如采纳真拆补法需 ACP 迁移全部向量
2. **扩充 Golden 覆盖**：1~4 局、晚子时（D14）、真太阳时跨辰边界输入
3. **Contract 冻结准备**：规则集裁定后，将 candidate normative 向量升级为 Behavior Contract（需另行 Sprint 授权）

## Governance Compliance

```
reference/ 未修改 ✅   docs/specification/ 未修改 ✅
Behavior Contracts 未创建/未修改 ✅   proto/ 未修改 ✅
其他 Agent 未修改 ✅   RuntimeAdapter 未实现 ✅
无解释规则/吉凶判断/RAG ✅   无新依赖 ✅
```
