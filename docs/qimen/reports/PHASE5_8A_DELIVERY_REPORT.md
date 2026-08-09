# Phase 5.8A — Contract Schema Extraction 交付报告（存档）

> **归档日期**: 2026-08-09
> **原始场景**: Contract Schema Extraction
> **状态**: 已交付

---

## 1. Executive Summary

完成契约机器可读定义层：`docs/specification/qimen_contract.schema.json`
（JSON Schema Draft 2020-12），内含契约结构词汇表 + `x-contract` 提取产物
注解（contract_version + 14 条 QC 规则的 id/name/status/observable_inputs/
observable_outputs，全部逐条取自 markdown，零臆造）。`tests/test_qimen_contract.py`
新增 4 测试（原有 4 测试保留）。**419 tests passing**，无 API/运行时变更。

## 2. 提取要素

| 要素 | 值 |
|------|-----|
| contract_version | `"1.0.0"`（SemVer，const 约束） |
| rules | 14 条（QC-001~QC-014，id enum 唯一约束） |
| rules[].status | 全部 `"frozen"`；枚举 `["frozen","draft","deprecated"]` |
| rules[].observable_inputs | 逐条取自各条款 Preconditions |
| rules[].observable_outputs | 逐条取自各条款 Observable output |

## 3. 产出文件

| 文件 | 性质 |
|------|------|
| `docs/specification/qimen_contract.schema.json` | **新增** — $schema/title/description/properties/required 齐备；id pattern `^QC-\d{3}$`；status enum；`x-contract` 提取注解 |
| `tests/test_qimen_contract.py` | +4 测试（原有 4 个保留） |
| `src/openmetaphysics/contracts/qimen_contract.py` | 清理 5.8 遗留 lint |

## 4. 新增测试（tests/test_qimen_contract.py，8/8 通过）

| 测试 | 验证 |
|------|------|
| test_contract_schema_is_valid | schema 合法 + status enum + `x-contract` 实例通过自校验（自包含子集校验器） |
| test_contract_identifiers_unique | id 枚举 14 个唯一，三方一致 |
| test_contract_version_format | SemVer + 与 markdown 元数据一致 |
| test_contract_matches_markdown_snapshot | rule 数量 = markdown 条目数 = 14；name 逐字一致 |

## 5. Test Results

```
ruff check            ✅   ruff format --check   ✅
pytest                ✅ 419 passed (415 + 4 new)
```

## 6. Constraints Compliance

```
qimen.py / QIMEN_BEHAVIOR_CONTRACT.md / golden_vectors.json 未修改 ✅
无新增规则 ✅（提取基于文档，快照测试强制）   无 API/运行时变更 ✅
```
