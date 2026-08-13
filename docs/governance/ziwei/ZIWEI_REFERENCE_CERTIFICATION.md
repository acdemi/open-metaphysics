# Ziwei Reference Certification

> **认证对象**: `reference/ziwei/`（独立实现）
> **认证基准**: `docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT_DRAFT.md`（BC-001~014）+
> `docs/ziwei/golden_vectors.json`（24, Engine v0.3.0）
> **认证日期**: 2026-08-13
> **认证结论**: **Reference Certified**（24/24 Golden Vector 等价 + 14/14 BC 审计 PASS）

---

## 1. Executive Summary

`reference/ziwei/` 为 Ziwei 行为的规范性 Reference 实现：**零 src 依赖**、
共享历法/干支原语显式复用 `reference/bazi/*`、全部规范表显式定义于
`reference/ziwei/tables.py`。24 个 Golden Vectors（Engine v0.3.0 生成）
在 Reference 下全部逐字节复现（`expected.chart` 完全相等），
14 条契约条款（BC-001~014）逐条审计 PASS。Ziwei 达到
**Reference Certified** 状态（Stage 3; Integration Ready 待 Phase 6.7.5）。

---

## 2. Reference 实现概述

| 模块 | 行数 | 职责 |
|------|------|------|
| `reference/ziwei/__init__.py` | 7 | 包导出（compute / ZiweiReferenceInput） |
| `reference/ziwei/tables.py` | 102 | BC-009/010/011/012 规范表（十二宫/五行局/定局 START-STEP/双星系偏移）; 共享干支纳音自 reference/bazi 引用 |
| `reference/ziwei/astronomy.py` | 23 | BC-005 农历转换（sxtwl==2.0.7, 独立封装） |
| `reference/ziwei/domain.py` | 144 | BC-001~014 参考引擎（输入校验/时区/时辰/命身宫/五行局/十二宫/定局/安星/阴阳） |
| `reference/ziwei/README.md` | 21 | 模块说明 + 复用引用登记 |
| `reference/tests/test_ziwei_equivalence.py` | 67 | 4 例等价/独立性/确定性/序列化测试 |

**合计**: 实现 276 行 + 测试 67 行。

**依赖**: 仅 `pydantic`（输入模型）与 `sxtwl==2.0.7`（BC-005 pin）;
无 `src/openmetaphysics` 导入。

---

## 3. 24/24 Golden Vector 等价测试结果

`reference/tests/test_ziwei_equivalence.py::test_24_golden_vectors_equivalent`:

```
遍历 24 向量: ref_compute(v["input"]) == v["expected"]["chart"]  → 24/24 相等
（fate/body palace, yin_yang, wuxing_ju, 12 palaces 全字段, calendar_note;
  逐字段精确相等, 无模糊匹配、无字段省略）
```

覆盖组: 基准盘 ×4 / 五行局 ×5 / 定局边界 ×4 / 时区 ×3 / 时辰窗 ×2 /
历法 ×5 / 不变式 ×1 —— 全部通过。

---

## 4. Reference Audit 结果（14/14 PASS）

| 组 | 条款 | 结论 |
|----|------|------|
| 基础 | BC-001 确定性 | PASS |
| 输入 | BC-002 Schema + 校验 | PASS |
| 历法链 | BC-003 时区 / BC-004 时辰 / BC-005 农历 / BC-006 年干 | PASS ×4 |
| 排盘 | BC-007 五虎遁 / BC-008 命身宫 / BC-009 五行局 / BC-010 十二宫 | PASS ×4 |
| 星曜 | BC-011 紫微定局 / BC-012 天府镜像 + 双星系 | PASS ×2 |
| 边界 | BC-013 阴阳 + 能力边界 / BC-014 Golden Vectors | PASS ×2 |

详见 `ZIWEI_REFERENCE_AUDIT.md`（逐条要求/行为/证据）。

---

## 5. 独立性验证

1. **源码级**: `reference/ziwei/**/*.py` 扫描零匹配 `openmetaphysics` 导入。
2. **运行时级**: 干净子进程 `python -c "import reference.ziwei; assert
   'openmetaphysics' not in sys.modules"` 通过（`test_reference_independent_of_production`）。
3. **共享原语显式登记**（契约允许, README.md 已列）:
   - `reference/bazi/astronomy.py::bazi_year_index` → BC-006
   - `reference/bazi/tables.py::HEAVENLY_STEMS/STEM_YIN_YANG/NAYIN/nayin_for` → BC-007/009
   - `sxtwl==2.0.7` → BC-005
4. **无行为泄漏**: Reference 无 Production 内部函数/数据结构引用;
   输出字段集与 BC-013 一致, 无额外默认值/回退（审计 §3~5）。

---

## 6. 认证结论

| 项 | 值 |
|----|-----|
| **状态** | **Reference Certified**（Stage 3, 2026-08-13） |
| Golden Vector 等价 | **24/24**（逐字节） |
| BC 审计 | **14/14 PASS** |
| 独立性 | 无 src 导入（源码扫描 + 运行时验证） |
| 全量测试 | **589/589 全绿** |
| 下一步 | Phase 6.7.5: 契约 v1.0.0 冻结 + Schema 登记 + 变更政策 → **Integration Ready**（等待人工授权） |

> 与 Qimen/BaZi 认证对齐: Reference 为行为规范层, 任何契约/规则/向量变更
> 须 ACP + 重新认证。
