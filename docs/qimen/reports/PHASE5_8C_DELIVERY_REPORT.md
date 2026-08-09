# Phase 5.8C — Golden Vector Machine Validation 交付报告（存档）

> **归档日期**: 2026-08-09
> **原始场景**: Golden Vector Machine Validation（回归防护网）
> **状态**: 已交付

---

## 1. Executive Summary

Golden Vectors 升级为**自动执行的回归防护网**：新建 `tests/test_qimen_regression.py`
（26 测试），每个 CI 周期自动验证 **24/24 向量**通过 + 契约覆盖测试。
**452 tests passing**（426 + 26），ruff 全绿，零运行时变更。E014 以代码注释
形式记入 Evidence Ledger。

## 2. 实现

### test_all_normative_vectors_pass — 全量回归 + 显式统计
- 24 向量 → QimenAgent 计算 → 与 expected_board 深度相等比较（str/int/bool/None，
  无浮点，无需容差）
- 显式输出：`[Qimen Regression] 24/24 vectors passed`（失败逐条 `[FAIL]`）
- 任何不匹配 → 断言失败（CI 阻断）

### test_normative_vector_regression[24 参数化]
逐向量参数化，失败时 pytest 显式点名向量 id。

### test_contract_coverage — 契约覆盖验证
读取 `qimen_contract.schema.json` x-contract 规则（14 条），每条 QC 的
observable_output 均由机器断言覆盖（QC_CHECKERS 注册表，QC-001~014 一一对应，
注册表缺漏即失败）：

| QC | 集合级机器断言 |
|----|----------------|
| QC-001 | 双次计算逐字节一致 |
| QC-002 | 9 宫唯一/宫名/键序稳定 |
| QC-003 | dun 枚举+双遁覆盖+冬至/夏至边界标签 |
| QC-004 | ju∈[1,9]/偏移/日号=输入日/阳遁 1-9 全覆 |
| QC-005/006 | 天地盘 9 干互异+天盘=地盘集合+值符宫天盘干=旬首仪（LIUJIA 映射） |
| QC-007/008 | 值符唯一且=落宫；值使门=落宫 |
| QC-009~011 | 星/门/神集合完整互异+中宫无门神 |
| QC-012/013/014 | 三奇恰{乙丙丁}；空亡 1-2 宫；中宫恰 palace 5 |

## 3. Evidence Ledger（E014，代码注释记录）

```
E014: 24/24 规范向量自动回归验证通过; Runtime engine 0.3.0 对
      QIMEN_BEHAVIOR_CONTRACT.md v1.0.0 (Frozen) 持续合规;
      本模块即自动执行证据 (每次 pytest 重放)。
```

## 4. Test Results

```
ruff check            ✅   ruff format --check   ✅
pytest                ✅ 452 passed (426 + 26 new)
[Qimen Regression] 24/24 vectors passed ✅
```

## 5. Constraints Compliance

```
qimen.py / 契约 / golden_vectors.json fixtures 未修改 ✅
无新增规则 ✅（校验器全部源自契约 observable_output）   无 Runtime 行为变更 ✅
```
