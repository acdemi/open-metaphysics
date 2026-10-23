# Liuyao Reference Runtime

自包含的六爻 Reference 实现，用于验证 Production Runtime 的行为等价性。

- **入口**: `compute(payload: dict) -> dict`
- **契约**: `docs/liuyao/LIUYAO_BEHAVIOR_CONTRACT.md`（v1.0.0 **Frozen**；30 clauses，ID 范围 LC-001~LC-052）
- **规则清单**: `docs/liuyao/LIUYAO_RULE_INVENTORY.md`（LY-01~LY-11，Frozen）
- **Golden Vectors**: `docs/liuyao/golden_vectors.json`（25，Frozen）
- **等价证明**: `reference/tests/test_liuyao_equivalence.py`

## 输入

```python
compute(
    {
        "born_at": "1985-08-15T10:00:00+08:00",  # tz-aware ISO-8601
        "casts": [7, 7, 8, 8, 7, 8],  # 6 值 ∈ {6,7,8,9}；可为 None
        "question": "财运如何",  # 可选
        "seed": 12345,  # casts 为 None 时必需
    }
)
```

`casts` 与 `seed` 均缺省时抛 `ValueError`：Reference 不接受不可复现的输入。
该自动 seed 路径明确不属于冻结契约（LC-D04）；冻结范围只覆盖显式
`casts` / `seed`。

## 独立性

`reference/liuyao/` **不得**导入 `openmetaphysics`（由
`reference/tests/test_liuyao_equivalence.py::test_reference_source_is_independent_of_src` 断言）。

`tables.py` 与 `astronomy.py` 由生产侧共享表**一次性导出**为静态字面量，
并由 `test_reference_tables_match_production_tables` 守卫一致性（漂移即失败）。
导出脚本保留在 `tools/gen_liuyao_reference_tables.py` 以留痕，
但**运行时不依赖** `tools/`。

## 文件

| 文件 | 内容 |
|------|------|
| `domain.py` | 六爻算法（LY-01~LY-11） |
| `tables.py` | 五行/八卦/64 卦/干支/八宫/纳甲/六神/用神表 |
| `astronomy.py` | Julian Day Number / 干支纪日 |
| `__init__.py` | 导出 `compute` / `VERSION` |
