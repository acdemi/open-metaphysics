# Phase 5.9B — Reference Qimen Domain 实现 交付报告（存档）

> **归档日期**: 2026-08-09
> **原始场景**: 自主 Sprint（按 QIMEN_FREEZE_REVIEW Future Roadmap 第 2 步）
> **状态**: 已交付 — **24/24 规范向量逐字节一致（E015）**

---

## 1. Executive Summary

依契约 v1.0.0 实现 Reference Qimen Domain：`reference/qimen/domain.py`
（规范性表格自包含 + 共享基础层依赖显式记录）。**首次运行即 24/24 向量
逐字节一致**；与 Product Runtime 双实现互证（30 固定种子抽样一致）。
**492 tests passing**（457 + 7 contracts 测试补齐 + 28 reference 验收）。

## 2. 实现（reference/qimen/domain.py）

| 模块 | 内容 |
|------|------|
| 规范性表格（自包含） | 宫名/九星/八门/八神/六仪三奇/六甲/宫支映射/遁序节气表 |
| 干支基础 | hour_branch / 五鼠遁 / 旬首 / 空亡支 / 支宫映射 |
| 遁与局 | 阴阳遁（D1）/ 日号三元（D2 Option A）/ 局数公式（D3） |
| 盘面构建 | 地盘（D4）/ 天盘+值符（D5/D6）/ 值使（D7）/ 星门神（D8-D10）/ 空亡（D11）/ 中宫寄坤二（D12） |
| 入口 | `compute(payload_dict) -> board_dict`（JSON 形态，晚子时不换日 D14） |

**共享基础层依赖**（显式记录于 docstring 与 README）：节气时刻/日干支/真太阳时
来自 `src/openmetaphysics/core/`（Phase 1 共享基础，C-04 自研核心 IP）；
奇门规范内容全部自包含，不依赖 src agents。

## 3. 验收（tests/test_reference_qimen.py，28 测试）

| 测试 | 验证 |
|------|------|
| test_reference_matches_all_24_vectors | **24/24 逐字节一致（核心验收）** |
| test_reference_vector_regression[24] | 逐向量回归（失败点名） |
| test_reference_deterministic | 同输入两次一致（QC-001） |
| test_reference_matches_product_runtime | 双实现互证（规范装置仲裁） |
| test_reference_deterministic_seeded_sample | 固定种子 30 抽样 reference == runtime |

## 4. Evidence Ledger（E015，模块 docstring 记录）

```
E015: reference/qimen 实现依契约 v1.0.0, 24/24 规范向量逐字节一致,
      与 Product Runtime 输出一致 (双实现互证 + 规范装置仲裁)。
```

## 5. 配套更新

- `reference/qimen/README.md` / `runtime_vs_reference.md`：建模层 → 实现层状态
- `tests/test_qimen_reference_docs.py`：纯度测试 → 实现层存在测试（5.7 约束为
  Sprint 范围；实现按契约对齐）
- `tests/test_qimen_contract_adapter.py`（**新增 7 测试，补齐 5.8**）：manifest
  schema 正/反例、input/output 校验、runtime alignment、24/24 golden 验证
- 修正 5.8 schema 历史笔误：frozen_rules minItems 14→13（契约实际 13 条冻结
  规则，D2 为政策裁定）；qc_ids 保持 14
- 文档刷新：`PROJECT_STATUS.md` / `ROADMAP.md` / `context/` 笔记（457→492 tests，
  Phase 5 完成，契约冻结）

## 6. Test Results

```
ruff check            ✅ All checks passed
ruff format --check   ✅ 94 files already formatted
pytest                ✅ 492 passed (457 + 7 + 28)
Reference 24/24       ✅ 逐字节一致
```

## 7. Governance Compliance

```
src agents/qimen.py        未修改 ✅   QIMEN_BEHAVIOR_CONTRACT.md  未修改 ✅
golden_vectors.json        未修改 ✅   无新增规则 ✅（实现严格依契约）
reference/qimen 落地       ✅（按评审路线图第 2 步）
```

## 8. Next Steps

- Qimen 功能扩展（格局判断 / 用神，需新授权）
- 其他命理域契约化复用 Qimen 流程
- 跨语言（Rust/Go）以 ABI snapshot 为类型参考
