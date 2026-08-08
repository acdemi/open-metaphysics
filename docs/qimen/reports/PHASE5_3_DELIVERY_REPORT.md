# Phase 5.3 — Qimen Golden Vector Expansion 交付报告（存档）

> **归档日期**: 2026-08-09
> **原始场景**: Validation & Stabilization
> **状态**: 已交付（后续演进见 Phase 5.4 存档）

---

## 1. Executive Summary

Golden Vector 集合从 3 个扩展至 **21 个**（新增 18 个），规范化存储于 `docs/qimen/golden_vectors.json`（79KB，每向量含 Task B 全部 7 项元数据）。新增 4 个测试 + 100 盘随机抽样验证。**核心算法零修改**，404 tests passing。生成过程中发现 3 处我自身手算错误（引擎均正确）：壬午时属甲戌旬非甲申旬、2024-07-07 为壬申日、立春 2024 为 2/4 08:21 UTC —— 已修正测试侧期望值，未触碰引擎。

## 2. Golden Vector 新增列表（18 个）

| 组 | 向量 | 输入 |
|----|------|------|
| 阳遁 1-9 局 | Y_ju1(值使寄宫) / Y_ju2(三奇集中2,3,4) / Y_ju3 / Y_ju4 / Y_ju5 / Y_ju6 / Y_ju7(冬至) / Y_ju8 / Y_ju9 | 2024-01-01 08:00 / 01-07 / 06-06 / 02-05 / 03-01 / 03-06 / 2023-12-23 / 04-05 / 01-21 12:00 |
| 阴遁 4 局 | Z_yin2(值符落中宫) / Z_yin5(值符+值使双中宫) / Z_yin3(大雪) / B_summer_after(夏至后) | 07-10 10:00 / 07-18 / 12-08 / 06-21 06:00 |
| 节气边界 | B_summer_before(夏至前,阳9) / B_lichun_before(大寒,3局) / B_lichun_after(立春,4局) | 06-21 03:30 / 02-04 12:00 / 02-05 01:00 |
| 时辰 | B_zishi(甲子时零转盘) / B_truesolar(真太阳时11:20→巳时) | 03-16 00:30 / 02-15 11:20 |

## 3. 覆盖矩阵

| 项目 | 覆盖 |
|------|------|
| 局数 | 阳遁 **1-9 全覆**；阴遁 {2,3,5,7} ≥3 ✓ |
| 阴阳遁 | 阳 12 向量 / 阴 9 向量 |
| 节气边界 | 冬至附近、夏至前后切换（阳9→阴7）、立春切换（3局→4局） |
| 子时 | B_zishi + G3 共 2 例 |
| 真太阳时 | B_truesolar 跨辰（钟表午→真太阳巳），另 17 向量均走真太阳路径 |
| 中宫 | 值符落中宫×3（G3/Z_yin2/Z_yin5）、值使落中宫寄宫×2（Y_ju1/Z_yin5）、三奇集中×1、空亡宫 1~2 宫全类型 |

## 4. D2 Impact Analysis 摘要（`QIMEN_D2_IMPACT_ANALYSIS.md`）

- 传导链：三元偏移→局数→地盘→天盘/值符/值使→八门八神三奇（**全部 21 向量受影响**）；时干支/旬首/空亡/中宫逻辑不受影响
- 需迁移测试 ≥6：`test_triple_offset_correct`、`test_ju_1_to_9_coverage`、`test_golden_vectors_full_board`、元数据版本、F2 断言、边界局数
- 替换成本：实现中 / 向量迁移高 / 需 ACP + 版本 0.3.0→0.4.0 + 新增符头/超神接气用例
- 结论：维持 Deferred

## 5. Modified Files

| 文件 | 性质 |
|------|------|
| `docs/qimen/golden_vectors.json` | **新增** — 21 向量规范化数据（含每向量元数据+plan 摘要） |
| `docs/qimen/QIMEN_D2_IMPACT_ANALYSIS.md` | **新增** — D2 影响分析 |
| `docs/qimen/QIMEN_RULE_DECISION.md` | 追加 Phase 5.3 交叉引用 |
| `tests/test_qimen.py` | 向量改由 JSON 加载（删 3 内联 dict）；+4 测试 |
| `src/openmetaphysics/agents/qimen.py` | **零修改** |

## 6. Test Results

```
ruff check            ✅ All checks passed
ruff format --check   ✅ 68 files already formatted
pytest                ✅ 404 passed (400 + 4 new; 19.4s)
Golden Vector 全通过   ✅ 21/21 (含元数据/确定性/序列化)
随机抽样              ✅ 100 盘无异常 (固定种子可复现)
```

新增测试：`test_golden_vector_count`（≥11、阳1-9、阴≥3、覆盖标签）、`test_golden_vector_determinism`（21×2 次 JSON 一致）、`test_board_serialization_stability`（键序固定+字节一致+数据文件键结构=Schema）、`test_random_year_sample_100_boards`（2023-2025 固定种子 100 盘状态不变量）。

## 7. Remaining Risks

| 风险 | 等级 |
|------|------|
| D2 日号三元与主流拆补法系统性差异（分析文档已量化） | 高（Deferred） |
| 新向量中 15 个仅经引擎+条件断言，未逐一人工核算全盘（关键链已核验：值符宫天盘干=旬首仪、值使/中宫/三奇条件） | 低~中 |
| 向量数据文件为文档层产物，非 Behavior Contract（升级需另行授权） | 低 |
| 晚子时（D14）仍无向量覆盖 | 低 |

## 8. Recommended Next Sprint

- **Behavior Contract 化 Sprint**：以 21 向量 + 12 冻结规则为输入，生成 Qimen Behavior Contract 草案（需新授权，本 Sprint 明确禁止）
- 或 **Reference Runtime 奇门域 Sprint**：以本数据文件为对齐基线
- 功能 Sprint（另授权）：格局判断 / 用神 / Consensus integration

## Governance Compliance

```
qimen 核心计算逻辑 未修改 ✅   Frozen Rules 未修改 ✅   D2 未修改 ✅
reference/ 未修改 ✅   Behavior Contracts 未创建 ✅   Schema 未修改 ✅
其他 Agent 未修改 ✅   无 LLM / 无新依赖 ✅   RuntimeAdapter 未实现 ✅
```
