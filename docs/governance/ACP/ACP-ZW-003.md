# ACP-ZW-003 — 输入校验显式化（KeyError → ValueError）

> **Status**: **IMPLEMENTED**（2026-08-13, Phase 6.7.1.6）
> **Approve**: 人工批准（Phase 6.7.1.5 裁定 REVISED, 本 Sprint 执行）
> **Rule**: ZW-001（`ZIWEI_RULE_DECISION.md`）

## 1. 裁定依据（Phase 6.7.1.5 分层裁定）

- **Contract requirement（领域规范层）**:
  1. lunar_month ∈ [1,12], lunar_day ∈ [1,30]（显式提供时）;
  2. 两字段必须同时提供或同时省略（部分提供 → 校验拒绝）;
  3. born_at 必须 tz-aware（既有信封契约, 未变）;
  4. 显式农历与公历不一致: 合法（重放特性）, 不做一致性校验;
  5. 越界 → 明确校验错误, 不以 KeyError 从查表底层意外泄漏。
- **Implementation behavior（Before）**: 无校验; day 越界 → `ZIWEI_POS`
  KeyError（工程意外）; month 越界 → 公式静默回绕; 部分提供 → 静默走公历。
- 校验实现与契约定义分离（ValueError 为 Python Schema 层实现, 不作为
  跨语言规范; 契约条款另行定义要求）。

## 2. 变更前后对比

| 输入 | Before | After |
|------|--------|-------|
| lunar_day=31 / 0 | KeyError（直抛, API 500） | `ValueError`（pydantic ValidationError, API 422） |
| lunar_month=13 / 0 | 静默回绕, 输出错误盘 | `ValueError`（422） |
| 仅 lunar_month | 静默走公历转换 | `ValueError`（422） |
| 仅 lunar_day | 同上 | `ValueError`（422） |
| 合法组合（同给 / 同省） | 正常 | 正常（无行为变化） |

实现位置: `ZiweiInput` 模型校验器（`agents/ziwei.py`, `@model_validator`）。

## 3. 测试结果

- 迁移: `test_lunar_day_out_of_range_raises_keyerror` →
  `test_lunar_input_out_of_range_rejected`（ValueError 语义 + 6 类非法输入 +
  合法组合接受）。
- `tests/test_ziwei.py`: 33/33; 全仓库 578/578; ruff 通过。

## 4. 向量迁移影响声明

- 合法输入输出零变化, 向量生成不受影响。
- 契约化时输入条款按本 ACP 的要求撰写（校验拒绝语义, 不含错误类型
  实现细节）。

## 5. 修改文件

- `src/openmetaphysics/agents/ziwei.py`（`ZiweiInput._validate_lunar_fields`）
- `tests/test_ziwei.py`（KeyError 测试迁移）
