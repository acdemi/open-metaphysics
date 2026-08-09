# Phase 5.8 — Qimen Contract Adapter & Reference Runtime Alignment 交付报告（存档）

> **归档日期**: 2026-08-09
> **原始场景**: Contract Adapter（本 Sprint 被 5.8A 打断，测试补齐于后续自主工作）
> **状态**: 已交付（契约包 + 测试见本存档与 test_qimen_contract_adapter.py）

---

## 1. Executive Summary

建立契约与 Runtime 之间的**机器可验证适配层**：`src/openmetaphysics/contracts/` 包
（契约清单 MANIFEST + 轻量 JSON Schema 子集校验器 + QimenContractAdapter）。
零运行时变更；不新增任何规则。本 Sprint 交付契约包主体；其测试在后续自主
工作中补齐（见 §5）。

## 2. 交付物

| 文件 | 内容 |
|------|------|
| `src/openmetaphysics/contracts/__init__.py` | 包导出（MANIFEST / QimenContractAdapter / __version__） |
| `src/openmetaphysics/contracts/qimen_contract.schema.json` | 契约清单 JSON Schema（contract_id/version/status/engine/rule_set/frozen_rules/qc_ids/golden_vector_count，2020-12） |
| `src/openmetaphysics/contracts/qimen_contract.py` | MANIFEST（v1.0.0 机器清单）+ `_schema_errors`（const/enum/type/required/items/minItems/uniqueItems 子集）+ `QimenContractAdapter` |

## 3. QimenContractAdapter（5.8 版，契约清单层）

| 方法 | 行为 |
|------|------|
| load_schema / load_vectors | 读取 schema 与 24 向量 |
| validate_manifest | 清单须满足 schema（version/QC/frozen status） |
| validate_runtime_alignment | 适配层符号表 ↔ 运行时符号表一致 |
| validate_input | QC-001 前置：合法 QimenInput 且 born_at tz-aware |
| validate_output | QC-002~014 可观察不变量（9 宫/遁局/天地盘/星门神/三奇/空亡/中宫/键序） |
| validate_vector / validate_golden_vectors | 向量元数据 + expected_board 不变量 + 运行时复算比对 |

## 4. 已知漂移（非阻塞，warning 级）

golden_vectors.json 为冻结前产物，向量级 `deferred_rules` 仍为 ['D2','D14']
（契约 v1.0.0 已裁定两者为规范）。适配层以 warning 记录；向量元数据对齐
需后续授权 Sprint（本 Sprint 禁止修改 fixtures）。

## 5. 测试补齐（自主工作阶段）

`tests/test_qimen_contract_adapter.py`：schema 校验（manifest 正/反例）、
adapter 校验（input/output/runtime alignment）、24/24 golden vector 验证。

## 6. Governance Compliance

```
qimen.py / 契约 / golden_vectors.json 未修改 ✅   无新增规则 ✅
无 LLM / 外部 API ✅   轻量校验（类型/范围/结构，无排盘计算）✅
```
