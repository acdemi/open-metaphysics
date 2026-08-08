# Runtime ↔ Reference 对照

> **契约**: [QIMEN_BEHAVIOR_CONTRACT.md](../../docs/specification/QIMEN_BEHAVIOR_CONTRACT.md) v1.0.0 (Frozen)
> **日期**: Phase 5.7

---

## 1. 角色定位

| 层 | 位置 | 角色 | 状态 |
|----|------|------|------|
| 行为契约 | `docs/specification/QIMEN_BEHAVIOR_CONTRACT.md` | 行为唯一权威（QC-001~014） | **Frozen v1.0.0** |
| 规范向量 | `docs/qimen/golden_vectors.json` | 规范回归装置（24, immutable） | **normative fixtures** |
| Product Runtime | `src/openmetaphysics/agents/qimen.py` | 正式实现（engine v0.3.0） | 契约绑定 |
| Reference Qimen Domain | `reference/qimen/`（本层） | 领域建模；未来 Reference 实现锚点 | **建模中（无代码）** |
| Reference Runtime（既有域） | `reference/*.py` | Rule/Pattern/Evidence/Knowledge/Consensus | 完成（不属本域） |

## 2. 行为一致性约定

- **Reference 优先级原则**（AGENTS.md §7）：Reference 优先于 Production。
  但**奇门域尚无 Reference 实现** —— 当前行为基准 = 冻结契约 v1.0.0 +
  规范向量，Product Runtime 已与其对齐（408 tests，含 24/24 向量校验）。
- 未来 Reference Qimen 实现 Sprint 的验收标准：实现输出与
  `golden_vectors.json`（24 向量）**逐字节一致**，并满足契约全部 QC 条款。
- 若未来 Reference 与 Runtime 产生分歧：**契约 v1.0.0 为最终裁判**；
  实现差异按 ACP 处理，不得静默修改契约（约束 2）。

## 3. 对照表：概念 → 契约条款 → 运行时实现

| 领域概念 | 契约条款 | 运行时实现位置 | 规范化选择 |
|----------|----------|----------------|------------|
| 确定性 | QC-001 | `QimenEngine.calculate` | 纯函数，无 I/O/时钟/随机 |
| 九宫完整性 | QC-002 | `build_palaces` | 恒 9 宫，palace 1..9 唯一 |
| 阴阳遁 | QC-003 | `dun_type_and_base_ju` | 节气管辖（UTC），冬至/夏至含边界 |
| 局数 | QC-004 | `build_palaces` | 日号三元近似（D2 Option A，规范） |
| 地盘 | QC-005 | `earth_placement` | 阳顺阴逆布六仪三奇 |
| 天盘 | QC-006 | `build_palaces` | `(时干宫-旬首宫)mod9` 顺转 |
| 值符 | QC-007 | `build_palaces` | 随时干；旬首宫星；寄坤二 |
| 值使 | QC-008 | `build_palaces` | 随时支 mod12；落中宫寄坤二 |
| 九星 | QC-009 | `NINE_STARS` + 转盘 | 天禽参与转盘（不寄宫） |
| 八门 | QC-010 | `EIGHT_DOORS` + 转盘 | 洛书序顺布，跳过中宫 |
| 八神 | QC-011 | `EIGHT_GODS` + 转盘 | 值符神起布，顺布，跳过中宫 |
| 三奇 | QC-012 | `SANQI` | 天盘干 乙丙丁 各一宫 |
| 空亡 | QC-013 | `void_branch_indices` + `PALACE_BRANCHES` | 时柱旬空 → 宫位 |
| 中宫 | QC-014 | `build_palaces` | 值符/值使寄坤二；天禽不寄 |

## 4. 本层（reference/qimen）当前边界

- ✅ 领域概念文档（[concepts/](concepts/)）—— 建模语言与结构
- ✅ 流派差异记录（[concepts/schools.md](concepts/schools.md)）
- ❌ 无实现代码（`*.py` 禁止，待契约化 Sprint）
- ❌ 不定义新行为 / 新概念 —— 一切以契约为准

## 5. 差异处理流程

发现文档/实现与契约冲突时：

1. **报告**（禁止静默修改契约或实现）
2. 分类：文档错误（修正文档）/ 实现 bug（修实现 + 回归）/
   契约缺陷（ACP + 版本流程，见契约 §6）
3. 记录于本对照表或 `concepts/schools.md`
