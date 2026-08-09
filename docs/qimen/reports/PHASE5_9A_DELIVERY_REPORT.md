# Phase 5.9A — Runtime Type Boundary Definition 交付报告（存档）

> **归档日期**: 2026-08-09
> **原始场景**: Runtime Type Boundary Definition（ABI 参考）
> **状态**: 已交付

---

## 1. Executive Summary

建立 Qimen Runtime **显式数据类型边界**：`src/openmetaphysics/domain/qimen/`
新增 `types.py`（TypedDict + 结构 SPEC）、`structural.py`（运行时结构校验器）、
`abi.py`（ABI snapshot 自动生成 + 结构 inventory）；快照产物
`docs/qimen/qimen_abi_snapshot.json`。**457 tests passing**（452 + 5），
ruff 全绿，行为零变化。全部字段来自实测 inventory，零臆造。

## 2. 实现

### types.py — TypedDict + SPEC（同源）
| 类型 | 字段（实测来源） |
|------|------------------|
| `QimenInput` | request_id/born_at/born_location/gender/question/locale/seed/client_nonce（含 GeoPointDict 嵌套） |
| `QimenPalace` | palace/name/sky_plate/earth_plate/eight_gods/nine_stars/eight_doors/three_qi/is_void/is_central |
| `QimenOutput` | solar_term/ju/dun_type/day_of_month/triple_offset/cells（list[QimenPalace]） |

`TYPE_SPECS` 机器规格（type/required/properties/items/enum）与 TypedDict 同源。

### structural.py — 运行时结构校验器
- 不使用 `isinstance(TypedDict)`；逐 key 结构检查：类型（number 收 int/float、
  integer 排除 bool）、必填、嵌套 object/array、enum
- `validate_structure(instance, spec, path) -> list[str]`

### abi.py — ABI snapshot + inventory
- `build_abi_snapshot()`：从 types.py 自动生成，含 contract_version 1.0.0 +
  runtime_version 0.3.0 + 3 类型规格
- `build_structure_inventory(objects)`：从实际对象集合提取 `{path: [types]}`
- 快照文件 `docs/qimen/qimen_abi_snapshot.json`（已生成，新鲜度测试强制同步）

## 3. 测试（tests/test_qimen_abi.py，5/5）

inventory 一致性（观测路径 ⊆ SPEC / 类型兼容 / 必填齐全）/ runtime 输出一致
（24 向量零违规）/ golden 结构验证（input/board/每宫）/ 快照新鲜度 / 快照元数据。

## 4. 修正记录

- `abi.py` 仓库根路径深度错误（parents[3]→parents[4]，曾误写至 src/docs/ 已清理）
- `abi.py` 缺失 type_name 导入

## 5. Test Results

```
ruff check            ✅   ruff format --check   ✅
pytest                ✅ 457 passed (452 + 5 new)
ABI snapshot          ✅ 新鲜度 + 元数据通过
```

## 6. Constraints Compliance

```
qimen.py / 契约 / golden_vectors.json 未修改 ✅   无新增规则 ✅
类型定义来自实际输出 ✅（inventory 测试强制）   行为零变化 ✅
```
