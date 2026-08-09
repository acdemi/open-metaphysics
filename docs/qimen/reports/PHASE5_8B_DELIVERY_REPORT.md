# Phase 5.8B — Runtime Adapter Interface 交付报告（存档）

> **归档日期**: 2026-08-09
> **原始场景**: Runtime Adapter Interface（domain 层）
> **状态**: 已交付

---

## 1. Executive Summary

创建 `src/openmetaphysics/domain/qimen/adapter.py`（新 domain 层，与 agents
解耦）：`QimenContractAdapter` 显式验证层 —— 输入合规（raw dict:
year/month/day/hour）、输出结构合规（QimenBoard JSON）、Golden Vector 回归
验证（委托现有 runtime，不修改）、契约状态查询。纯类型/范围/结构校验，
**零排盘计算、零 LLM**。7/7 新测试通过，**426 tests passing**（419 + 7）。

## 2. 实现（`src/openmetaphysics/domain/qimen/adapter.py`）

| 成员 | 行为 |
|------|------|
| `contract_version = "1.0.0"` | 硬编码（契约 v1.0.0） |
| `validate_input(raw_input) -> bool` | year/month/day/hour 存在 + 严格 int（排除 bool）+ 范围（1900-2100/1-12/1-31/0-23）+ 真实日期校验 |
| `validate_output(raw_output) -> bool` | board 6 键 + cells×9 + cell 10 键；类型/范围（ju 1-9、偏移、dun 枚举、布尔、宫位唯一） |
| `verify_golden_vector(vector) -> bool` | 构造输入 → 委托 QimenAgent 计算 → 与 expected_board 逐字节比对；异常/不一致 → False |
| `get_contract_status() -> dict` | contract_id/version、status Frozen、engine_version、rule_set_version、已核验数 |

**与 5.8 contracts 包分工**：domain adapter = 运行时输入/输出/回归；
contracts 包 = 契约清单/schema。

## 3. 测试（`tests/test_qimen_adapter.py`，7/7）

版本声明 / 缺字段拒绝 / 越界拒绝（含 2/30、非闰 2/29、bool）/ 24 向量输入
接受 + 整点向量行为不变（输出 == expected_board）/ verify_golden_vector
（含篡改拒绝）/ 输出结构接受 / 输出结构拒绝。

**设计说明**：raw 输入为小时粒度（无 minute）—— 5 个分钟≠0 向量仅做结构
校验，19 个整点向量做全盘比对（行为不变断言）。

## 4. 修正记录

- 相对导入深度错误（`..`→`...`，domain.qimen 层级）
- 测试 helper 时区缺失 → 补 Asia/Shanghai

## 5. Test Results

```
ruff check            ✅   ruff format --check   ✅
pytest                ✅ 426 passed (419 + 7 new)
```

## 6. Constraints Compliance

```
qimen.py / 契约 / golden_vectors.json 未修改 ✅   无 LLM / 外部 API ✅
轻量校验层（仅类型/范围/结构）✅
```
