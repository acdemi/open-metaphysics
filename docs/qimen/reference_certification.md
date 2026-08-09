# Qimen Reference Certification

> **认证日期**: 2026-08-09
> **执行人**: OpenMetaphysics 自主工作流（明早人工验收）
> **阶段**: Phase 5.7 — Reference Runtime Domain Alignment Sprint

---

## 认证内容

| 项 | 值 |
|----|-----|
| 契约版本 | **v1.0.0**（`docs/specification/QIMEN_BEHAVIOR_CONTRACT.md`, Frozen） |
| 规则集版本 | **v0.3.0** |
| 黄金向量数量与状态 | **24 / 24 通过**（逐字节一致, `reference/tests/test_golden_vectors.py`） |
| 独立测试用例数量 | **38**（reference/tests: 黄金 27 + 契约边界 8 + 等价 3） |
| 确定性等价 | **30/30 抽样逐字节一致**（`reference/tests/test_equivalence.py`, 固定种子 2024） |
| 契约符合性审计 | **14/14 QC Full**（`docs/qimen/reference_contract_audit.md`） |
| 偏差 | 无（`reference_alignment_proof.md` 偏差处理表为空） |

## 独立实现声明

> **"Reference implementation does not import Product Runtime."**
>
> 具体承诺（由测试强制）：
> - `reference/qimen/domain.py` 与 `reference/qimen/astronomy.py` 源码
>   不含任何 `from/import openmetaphysics` 语句
>   （`test_reference_source_independent_of_src`）
> - Reference 测试套件（除等价对照脚本外）不导入 `src/openmetaphysics` 任何模块
> - 天文/干支基础为 core 的规范移植（Meeus 同源），无运行时依赖

## Evidence 关联

| Evidence | 内容 |
|----------|------|
| E015 | Reference 实现 24/24 向量一致（5.9B） |
| E016 | 自包含实现 + 独立性源码检查 + 24/24 向量一致（5.7） |
| E017 | 30/30 强确定性等价（Product == Reference, 固定种子） |

## 认证声明

Reference Qimen Domain（`reference/qimen/`）作为独立于 Product Runtime 的
契约符合性实现，**通过** Frozen Contract v1.0.0 全部 14 条 QC 条款审计、
24/24 规范向量验收与 30 抽样确定性等价证明。未来任何算法修改必须同时
通过 Product + Reference 双重契约验证。

---
*本工件为文本认证记录，不构成额外报告文件。*
