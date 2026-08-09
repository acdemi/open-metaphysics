# Phase 5.7 — Reference Qimen Domain Modeling 交付报告（存档）

> **归档日期**: 2026-08-09
> **原始场景**: Reference Qimen Domain Modeling（建模层，纯文档）
> **状态**: 已交付（后续实现见 Phase 5.9B 存档）

---

## 1. Executive Summary

建立 `reference/qimen/` 领域建模层（**纯文档，无代码**）：README（Domain 边界）、runtime_vs_reference（对照）、concepts/ 7 份概念文档（含强制流派差异记录 schools.md）。新增 7 个文档测试（结构/纯度/链接检查/外部引用/边界关键词/流派记录/契约向量引用）。415 tests passing。**零运行时变更**。

## 2. 目录结构（`reference/qimen/`）

```
reference/qimen/
├── README.md                   # Domain 边界 + 层级关系 + 强制约束
├── runtime_vs_reference.md     # 角色定位 / 行为一致性约定 / 概念→QC→实现 对照表 / 差异处理流程
└── concepts/
    ├── board.md                # 盘面模型（九宫/字段/规范不变量/序列化键序）
    ├── dundun_ju.md            # 遁与局（阴阳遁/三元 Option A/局数公式）
    ├── plates.md               # 天地盘（地盘顺逆布/天盘顺转公式/依赖链）
    ├── zhifu_zhishi.md         # 值符值使（时干支基础/规则表/经典例锚点）
    ├── stars_doors_gods.md     # 九星/八门/八神（固定表+转盘+不变量）
    ├── void_central.md         # 空亡（旬空映射表）/中宫（寄宫规则）
    └── schools.md              # ★ 流派差异记录（S1-S8 强制项）
```

## 3. 关键设计

- **边界**：行为权威唯一 = 契约 v1.0.0；规范装置 = 24 向量；本层 Phase 5.7 禁止 `*.py`（实现 Sprint 按契约对齐）
- **流派差异**：8 项（S1 三元/S2 转盘法/S3 值使/S4 八神方向/S5 天禽/S6 寄宫/S7 晚子时/S8 空亡基准），每项含规范选择+替代流派+记录位置+影响分级+变更纪律
- **链接检查修复**：初版相对路径错误（`../../specification` → `../../docs/specification`），链接检查测试捕获 9 文件 11 处断链并修复

## 4. 文档测试（`tests/test_qimen_reference_docs.py`，7 项）

结构存在性 / 建模层纯度（无 .py/.yaml/.json）/ 链接可解析 / 外部引用存在 / 边界关键词 / 流派 S1-S8 记录 / 契约与向量引用。

## 5. Test Results

```
ruff check            ✅ All checks passed
ruff format --check   ✅ 79 files already formatted
pytest                ✅ 415 passed (408 + 7 new)
```

## 6. Governance Compliance

```
qimen.py 未修改 ✅   QIMEN_BEHAVIOR_CONTRACT.md 未修改 ✅   golden_vectors.json 未修改 ✅
无新增 runtime behavior ✅（建模层纯文档）   流派差异显式记录 ✅（schools.md S1-S8）
```

**完成。停止，等待 Evidence Review。**
