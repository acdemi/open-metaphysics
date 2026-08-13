# Reference BaZi Domain

> **状态**: Phase 6.5 Reference Implementation（依契约 v1.0.0; 独立性声明: 不导入 src）
> **契约**: [BAZI_BEHAVIOR_CONTRACT.md](../../docs/bazi/BAZI_BEHAVIOR_CONTRACT.md) v1.0.0 (Frozen)
> **规范向量**: [golden_vectors.json](../../docs/bazi/golden_vectors.json)（24, normative fixtures）
> **产品运行时**: `src/openmetaphysics/agents/bazi.py`（engine v0.1.0）
> **验收**: `reference/tests/test_bazi_equivalence.py`（24/24 Production == Reference, 逐字节）

---

## 1. Reference Domain 边界

`reference/bazi/` 是八字领域的 **Reference 契约实现**:

- ✅ 依冻结契约 BC-001~014 独立实现（四柱/十神/藏干/纳音/大运/gender/timezone）
- ✅ **独立性声明**: 本目录源码不含任何 `from/import openmetaphysics` 语句
  （由测试强制）; 天文/干支基础为**规范移植**（Meeus 同源, 无运行时依赖）
- ❌ 不定义新行为 —— 行为权威唯一来源是契约 v1.0.0
- ❌ 不包含格局/用神/解释层（Domain Boundary, `BAZI_FREEZE_BOUNDARY.md`）

### 层级关系

```
docs/bazi/BAZI_BEHAVIOR_CONTRACT.md  ← 行为权威（Frozen v1.0.0）
docs/bazi/golden_vectors.json        ← 规范回归装置（24, normative fixtures）
src/openmetaphysics/agents/bazi.py   ← 产品运行时（契约绑定）
reference/bazi/                      ← 本层：契约实现（验收 = 24/24 等价）
```

## 2. 目录结构

```
reference/bazi/
├── README.md         # 本文件：边界 + 独立性声明
├── __init__.py       # compute() 入口
├── tables.py         # 规范表（干支/藏干/纳音/五行/节气黄经, BC-006~008）
├── astronomy.py      # 历法原语（Meeus 截断, BC-002/003/010）
└── domain.py         # 契约实现（BC-001~014）
```

## 3. 实现约束

1. **不修改** `src/openmetaphysics/agents/bazi.py`
2. **不修改** `docs/bazi/BAZI_BEHAVIOR_CONTRACT.md`
3. **不修改** `docs/bazi/golden_vectors.json`
4. 实现变更后必须通过 `reference/tests/test_bazi_equivalence.py`（24/24 等价）
   + `tests/test_bazi_golden_vectors.py`（24/24 向量回归）

违反以上任何一条即视为越界, 需 ACP。

## 4. 输入 / 输出

```python
from reference.bazi import compute

chart = compute(
    {
        "born_at": datetime(2024, 3, 15, 10, 0, tzinfo=timezone(timedelta(hours=8))),
        "gender": "male",
        "born_location": {"timezone": "Asia/Shanghai"},
    }
)
# chart == production BaziChart.model_dump(mode="json")   (结构逐字段一致)
```

## 5. 参考文档

| 文档 | 用途 |
|------|------|
| [BAZI_ALGORITHM_ASSUMPTIONS.md](../../docs/bazi/BAZI_ALGORITHM_ASSUMPTIONS.md) | B1~B6 假设 |
| [BAZI_FREEZE_REVIEW.md](../../docs/governance/bazi/BAZI_FREEZE_REVIEW.md) | 冻结评审（PASS） |
| [BAZI_REFERENCE_AUDIT.md](../../docs/bazi/BAZI_REFERENCE_AUDIT.md) | BC 逐条审计 |
| [BAZI_REFERENCE_CERTIFICATION.md](../../docs/bazi/BAZI_REFERENCE_CERTIFICATION.md) | 认证记录 |
| [BAZI_CROSS_DOMAIN_BOUNDARIES.md](../../docs/bazi/BAZI_CROSS_DOMAIN_BOUNDARIES.md) | 跨域边界 |
