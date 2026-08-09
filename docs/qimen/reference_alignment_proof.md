# Reference ↔ Product 对齐证明（强确定性等价）

> **契约**: QIMEN_BEHAVIOR_CONTRACT.md v1.0.0 (Frozen)
> **证明日期**: 2026-08-09（Phase 5.7 Alignment Sprint, Task B）
> **验证脚本**: `reference/tests/test_equivalence.py`（固定种子, 可复现）

## 声明

**强确定性等价成立**：对固定种子 2024 生成的 30 个合法 QimenInput，
Product Runtime 与 Reference Runtime 输出的完整 board JSON（canonical form）
**逐字节一致**。

## 方法

- **输入生成约束**（`_generate_inputs`，固定种子 `random.Random(2024)`）：
  - 年份 ∈ {2023, 2024, 2025}（覆盖阳遁/阴遁全域与闰年）
  - 日期：年内随机（0..364 天）+ 随机小时（0..23）
  - 坐标：北京（39.9°N, 116.4°E, Asia/Shanghai）—— 合法 QimenInput，
    能生成完整 QimenBoard（真太阳时路径）
- **对照**：
  1. Product Runtime：`openmetaphysics.agents.qimen.QimenAgent.compute()`
     （只读，未修改）
  2. Reference Runtime：`reference.qimen.domain.compute()`
- **比较**：`json.dumps(board, sort_keys=True, ensure_ascii=False)` 逐字节一致

## 结果

```
[Equivalence] 30/30 inputs byte-identical
```

| 项 | 值 |
|----|-----|
| 抽样数 | 30 |
| 逐字节一致 | 30/30（100%） |
| 引擎版本（Product） | 0.3.0 |
| 规则集版本 | 0.3.0 |
| 契约版本 | 1.0.0 |
| 元数据一致性 | ju / dun_type / triple_offset / solar_term 抽样 3 组全一致 |

## 偏差处理表（Task D）

| # | 偏差 | 类型 | 处理 | 状态 |
|---|------|------|------|------|
| D-1 | 无 | - | - | 无偏差，无需闭环 |

## 佐证

- 24/24 规范向量在 Reference 实现逐字节一致（`reference/tests/test_golden_vectors.py`）
- 30 固定种子抽样 Product == Reference（本文件）
- 两实现分别独立满足 Frozen Contract（`reference_contract_audit.md` 14/14 Full）

**结论：Reference 与 Product 在契约 v1.0.0 约束下强确定性等价；未来任何
算法修改须同时通过 Product + Reference 双重契约验证。**
