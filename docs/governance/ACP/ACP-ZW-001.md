# ACP-ZW-001 — 紫微定局表规范算法替换

> **Status**: **IMPLEMENTED**（2026-08-13, Phase 6.7.1.6）
> **Approve**: 人工批准（Phase 6.7.1.5 裁定 REVISED, 本 Sprint 执行）
> **Rule**: ZW-012（`ZIWEI_RULE_DECISION.md`）

## 1. 裁定依据（Phase 6.7.1.5）

- 当前硬编码表无统一生成规则（访问宫数 12/12/11/11/8）, 违反四项著名
  结构不变式（木三无寅卯 / 金四无酉戌 / 土五无辰巳 / 火六无未申）。
- 异常模式与生成错误特征一致（木三起寅=默认索引 / 金土火起丑=复制水二 /
  步长 ju-1=off-by-one）; 水二局存在 1 日错位。
- 修订规则为统一生成式, 全部不变式成立, 与经典《紫微星诀》速见表吻合。

## 2. 变更前后对比

| 项 | Before | After |
|----|--------|-------|
| 定义 | 硬编码 5×30 查表 `ZIWEI_POS`（162 行） | 生成式常量: `ZIWEI_JU_START` + `ZIWEI_JU_STEP` + `_ziwei_pos_table()`; `ZIWEI_POS` 接口不变（dict[ju][day]） |
| 规则 | 无统一规则 | `idx = (START[ju] + (day-1)//STEP[ju]) % 12`; START={2:丑(11),3:辰(2),4:亥(9),5:午(4),6:酉(7)}; STEP={2:2,3:3,4:3,5:3,6:3} |
| 访问宫数 | 12/12/11/11/8 | 12/10/10/10/10 |
| 不变式 | 4/4 违反 | 4/4 满足 |
| 水二局 | 初一独丑, 初二起两日一宫（1 日错位） | 初一初二丑, 初三初四寅（标准两日一宫） |
| 接口 | `ZIWEI_POS[ju][day]` | 同（保留） |
| Engine 版本 | 0.2.0 | 0.3.0 |

## 3. 测试结果

- `tests/test_ziwei.py`: 33/33 通过; `test_ziwei_pos_values_snapshot` 快照
  重生成（SHA-256 → `1cc796400c628e419e9942a2ddba236c77a95e4285fc1f94fcc9b4d057c44909`）。
- 全仓库: 578/578 通过; ruff check/format 通过。
- 其余测试自动一致（公式/镜像/偏移类测试读同一模块常量, 无需改）;
  `test_fate_palace_canonical`（水二局 day1 → 丑）在两种规则下相同。

## 4. 向量迁移影响声明

- Phase 6.7.2 Golden Vector: ZV-pos 组及所有全盘向量**按修订后表采样**。
- 此前未生成任何正式向量（Phase 6.7.1/6.7.1.5 均未生成）, 无迁移成本。
- 变更后全盘输出变化（星曜位置), 属于 ACP 批准的规范变更。

## 5. 修改文件

- `src/openmetaphysics/agents/ziwei.py`（定局表生成逻辑 + 版本 0.3.0）
- `tests/test_ziwei.py`（快照哈希更新）
