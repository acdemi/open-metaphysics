# ACP-REF-001 — Conformance 行为覆盖与"空转检查"处置

> **Status**: **PROPOSED**（2026-09-16 · 待人工批准 · 未实施任何代码变更）
> **触发**: 2026-09-16 全项目审计 §2.2（`docs/PROJECT_REVIEW_2026-09-16.md`）
> **范围**: `reference/conformance_runner.py`（Reference 行为实现，冻结）+ `docs/specification/CONFORMANCE_SPEC.md` CF-015（冻结规范）
> **纪律**: 依 H3 —— 冻结工件变更须 ACP + 人工批准；**本提案不包含任何 `reference/` 修改**

---

## 1. 问题（实测证据）

`ConformanceRunner().run(ReferenceAdapter(), 'reference', '1.0.0')` 报 **135/135 checks passed、coverage 1.0、certified=True**，
且 CI（`.github/workflows/test.yml` L18-20）以此作为契约层合并门。但 135 个检查中含**大量无条件通过**：

| 检查 | 位置 | 现状 |
|------|------|------|
| `_check_behavior_coverage` | `reference/conformance_runner.py` L527-556 | 硬编码 **17 个**行为 ID（BC 7/7、KB 4/20、CS 6/25），对每个 ID 一律 `add_check(passed=True, message="Behavior contract covered by golden vectors")` —— **不做任何验证** |
| `_check_ordering` | 同文件 L454 | 无条件 `passed=True` |
| `_check_hash` | 同文件 L466 | 无条件 `passed=True` |
| `_check_null` | 同文件 L478 | 无条件 `passed=True` |
| `_check_enum` | 同文件 L490 | 无条件 `passed=True` |

而 **CF-015**（`CONFORMANCE_SPEC.md` L265-278）要求覆盖 **KB-001~020 + CS-001~025**。
现状覆盖 BC 7/7、KB 4/20、CS 6/25 → **83 个已冻结行为合约 ID 从未被验证**，却计入"通过"。

**后果**：`certified=True` / `coverage=1.0` 的**强度被高估**；任何据此做出的"Reference Runtime 已验证"表述都不成立。
（需区分：Qimen/BaZi/Ziwei 的**域级**认证另有独立等价测试支撑 —— 30/30 + 24/24 + 24/24 —— 不受本 ACP 影响；
本次影响的是 **Reference Runtime 整体认证**这一层表述。）

## 2. 为何须 ACP 而非直接修

1. `reference/conformance_runner.py` 属 H3 列的冻结工件（Reference 行为实现）；`CAPABILITY_LIFECYCLE.md` §5.2
   明确「达到 Contract Frozen 后，任何规则/算法变更须 ACP，**bug fix 亦须 ACP**」。
2. 本问题存在**两条互斥的正当出路**（改实现 vs 改规范），选择权属人工 —— 属 H3「发现设计不足 → 停止并出 ACP」。

## 3. 选项

### 选项 A（推荐）—— 补齐实现以符合 CF-015

- `_check_behavior_coverage`：由 17 个 ID 扩至 **100 个**（BC 35 + KB 20 + CS 25 + CF 20 的适用集，按 CF-015 口径）；
  每个 ID 须绑定**可执行断言**；无法机器验证者显式标注 `NOT_MACHINE_CHECKABLE` 并**计入未覆盖**，**不得默认 passed**。
- 4 类空转检查：**或**实现真实检查，**或**从 `ConformanceResult` 中删除 —— 不保留恒真 check。
- **判定口径必须同步改写**：`certified` 不得在覆盖不足时为 True。建议引入：
  - `certified = (已实现层全绿) ∧ (未覆盖 ID 数 == 0)`；或
  - 保留 `certified` 但**新增 `coverage_ratio` 并把 `certified` 语义收窄为「已声明范围」**，二者择一须在本 ACP 中定稿。
- 预期影响：**`certified` 可能由 `True` 变为 `False`** —— 这是修正而非回归；须同步修订所有"已验证/已认证"表述。
- 附带工作量：KB/CS 各层需要**新增 golden 向量**（现仅 Evidence 1 / Knowledge 4 / Consensus 3 条），
  否则大量 ID 无法绑定断言 → 需评估是否分批（先覆盖已实现层，其余登记为待补）。

### 选项 B —— 经 ACP 修订 CF-015（降低规范要求）

- 明确 CF-015 的覆盖范围为「**已实现并且已具备向量的层**」，并为 83 个未覆盖 ID 出具**显式豁免清单与理由**。
- `CONFORMANCE_SPEC.md` 属冻结规范 → 须版本递增（`CONFORMANCE_SPEC` 当前 1.0.0）。
- 影响：`certified` 语义收窄为「已声明覆盖范围内全绿」；须在规范与状态文档中同步写明**排除项**。

## 4. 影响面

| 对象 | 影响 |
|------|------|
| `reference/conformance_runner.py` | 冻结（Reference 行为实现）→ 须 ACP |
| `docs/specification/CONFORMANCE_SPEC.md` CF-015 | 冻结规范 → 选项 B 须版本递增 |
| `.github/workflows/test.yml` L18-20 | CI 契约门 —— 判定口径变化会影响红灯语义（选项 A 下 CI 可能开始失败，这正是期望行为） |
| 域认证（Qimen/BaZi/Ziwei） | **不受影响**（独立等价测试支撑） |
| `docs/PROJECT_STATUS.md` §5.4 等表述 | 须同步（已在 2026-09-16 P0-2 加注警示） |
| `reference/contracts/*.json` | 无直接影响；但与 ACP-REF-003（rule/pattern 契约缺失）相关 |

## 5. 建议

**选项 A + 分两步落地**：

1. **第一步（最小可信）**：把 17 → 100 个 ID 的覆盖清单补齐；未绑定断言的 ID 一律标记为**未覆盖**并从
   `passed` 统计中剔除；同时删除/实现 4 类空转检查。此步之后 `certified` 的数值可能下降 —— 这是**恢复可信度**，不是功能回归。
2. **第二步（补向量）**：为 KB/CS 未覆盖层补 golden 向量，分批把 `coverage_ratio` 回升，每批走一次本 ACP 的
   扩展评审（或按本 ACP 授权的一次性预算执行）。

## 6. 待批准事项

- [ ] 选项 A 还是 B？
- [ ] 若选 A：`certified` 的最终判定口径（`certified` 含覆盖率，或拆 `certified` + `coverage_ratio`）？
- [ ] 若选 A：是否授权**一次性**补齐 100 个 ID 的绑定 + 删除空转检查（含 `reference/` 行为实现修改）？
- [ ] 若选 B：接受 `CONFORMANCE_SPEC` 版本递增与豁免清单？

> 批准后执行；在此之前**不修改** `reference/` 与 `docs/specification/` 的任何文件。
