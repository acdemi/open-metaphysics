# ACP-REF-001 — Conformance 行为覆盖与派生检查处置

> **Status**: **IMPLEMENTED**（2026-09-16 · 选项 A · 人工授权单个 Sprint）· 实施分支 `work/reference/p1-behavior-coverage`
> **修正记录**: 初版（同日）称「83/100 ID 未验证、4 类检查无条件通过」——**经二轮复核该表述不准确**，
> 本版为修正后的准确口径（见 §1.4「初版勘误」）。
> **范围**: `reference/conformance_runner.py`（Reference 行为实现，冻结）+ `reference/knowledge_behavior.py` + `reference/consensus_behavior.py` + `reference/conformance.py`
> **规范未改**: 走**选项 A（补齐实现以符合 CF-015）**，故 `docs/specification/CONFORMANCE_SPEC.md` **零修改**（无需版本递增）。

## 0. 实施结果（2026-09-16）

| 指标 | 实施前 | 实施后 |
|------|--------|--------|
| Conformance 检查总数 | 135 | **170** |
| 行为覆盖检查条数 | 17（硬编码、恒真） | **52**（逐条真实执行） |
| `behavior_coverage` | 未暴露 | **1.0（52/52）** |
| `unrepresented_behaviors` | 未暴露 | **[]** |
| `certified` | True（强度被高估） | **True（已如实验证）** |
| 测试 | 618 | **627**（新增 9 条锁定机制，含 2 个负向对照） |

**落地内容**

- **A-1 机制**：新增 `REQUIRED_BEHAVIOR_IDS`（CF-015 的 52 个 ID）与 `_behavior_representation()`；
  `_check_behavior_coverage` 改为**逐 ID 执行代表物**，无代表物 → **FAIL**；派生四项检查的措辞改为
  「derived from the golden match (not independently re-verified)」。
- **A-2 KB**：`knowledge_behavior.py` 新增 **KB-001~011**（模型校验：ID 格式/枚举/边界/`extra=forbid`）
  共 11 个验证器（均含「合法载荷必被接受」的正向对照，防止空转），并把 `audit()` 由 5 键扩到
  **KB-001~020 全覆盖**；同时**更正**原 `audit()` 的映射错误（原把 KB-013~015 当作「列表排序」、
  把确定性挂在 KB-019 —— 与规范原文不符，现按规范逐条对齐）。
- **A-3 CS**：`consensus_behavior.py` 新增 **CS-002/003/004/005/006/007/008/009/010/018/019/022/024**
  共 13 个验证器（驱动真实 `ConsensusBuilder` 断言可观测后果），`audit()` 由 5 键扩到 **CS-001~025 全覆盖**。
- **A-4 追溯**：每个 ID 的 `message` 记录代表物来源（`KnowledgeBehavior.audit()` /
  `ConsensusBehavior.audit()` / 对应层 golden 检查 / 实时缺字段探针）。
- **A-5 口径**：`ConformanceResult` 新增 `behavior_coverage` 与 `unrepresented_behaviors`；
  `certified` 保持 `failed == 0` 语义 —— 覆盖不足会**真实失败**（已由负向对照测试锁定）。

**未采用红旗过渡**：因 A-2/A-3 已把缺失验证器补齐，实施后覆盖率即为 **52/52**，
`certified` 始终为 True 且**其强度已如实**，无需任何过渡方案，main 亦未出现红灯。

**关于 CF-015 措辞的说明（须确认）**：CF-015 原文为「每个行为合约 **MUST** 由至少一条
**golden vector** 代表」。本次落地的代表物为**可执行行为验证器**（KB/CS）与**对应层 golden 检查**（BC），
而非为每个 ID 新建一条 golden vector。这是**同一意图的更强实现**（执行真实断言而非快照比对），
但**字面上**与 CF-015 的 "golden vector" 用词不同。若要求严格字面一致，可再出一次小 ACP
把代表物形态写清或补生成对应向量 —— 请裁定。

---

## 1. 问题（实测证据）

### 1.1 CF-015 的规范要求（原文）

> **Rule**: Conformance **MUST** cover all Behavior Contracts.
> - The `BEHAVIOR_COVERAGE` check verifies a known set of behavior contract IDs
>   (BC-RE-001, BC-DNF-001, BC-PM-001, BC-EV-001, BC-JSON-001, BC-DET-001, BC-EDGE-001,
>   KB-001 through KB-020, CS-001 through CS-025).
> - **Each behavior contract MUST be represented by at least one golden vector.**
> - **Missing coverage MUST fail conformance.**

→ 所需集合 = 7（BC）+ 20（KB）+ 25（CS）= **52 个 ID**。

### 1.2 现状实现

`_check_behavior_coverage`（`reference/conformance_runner.py` L527-556）**硬编码 17 个 ID**
（BC 7 + KB{001,012,018,020} + CS{001,004,005,006,020,025}），对每个 ID 一律
`add_check(passed=True, message="Behavior contract covered by golden vectors")` ——
**不校验该 ID 是否真被任何向量代表**。

因此：`certified=True` / `coverage=1.0` 是在**未作覆盖验证**的情况下得出的，
且 **52 − 17 = 35 个合约 ID 完全未被纳入该检查**。

### 1.3 缺口是实质性的，不只是"未映射"（二轮复核新增）

| 证据 | 结论 |
|------|------|
| `reference/knowledge_behavior.py` 的 `verify_*` 仅覆盖 KB-012 / KB-013~015 / KB-016 / KB-017 / KB-018 / KB-019 / KB-020；其 `audit()` 只调用 5 项 | **KB-001 ~ KB-011（11 条）没有任何验证器** |
| `reference/consensus_behavior.py` 的 `verify_*` 覆盖 CS-001 / CS-008~009 / CS-011 / CS-012 / CS-013~015 / CS-016 / CS-017 / CS-020 / CS-021 / CS-023 / CS-025；`audit()` 只调用 5 项 | 约 **10 条 CS 无验证器** |
| 全仓测试中出现的 KB ID 仅 **11 个**（KB-001/007/012~020） | KB-002~006、008~011 亦无测试引用 |
| 全仓测试中出现的 **CS ID = 0 个** | CS 行为被"间接执行"，但**无 ID 级可追溯性** |
| `tests/test_reference_conformance.py::test_behavior_coverage_checks_present` **只断言 `BEHAVIOR_COVERAGE` 类别存在** | CF-015 自己的测试**也是空断言** |

**结论**：CF-015 的满足不能靠"补映射"，而需要**为约 35 个合约补写 ID 级验证**
（读 45 条规范条款 → 写断言 → 接入 `audit()` → 形成可追溯代表物）。这是 **Sprint 级工作量**，
非一次编辑可达。

### 1.4 初版勘误（诚实更正）

| 初版表述 | 实情 |
|----------|------|
| 「83/100 个 ID 未验证」 | 错误：CF-015 的所需集合是 **52**（非 100），现状声明 17 → **35 个未纳入**（100 是全部合约数，含未被 CF-015 列举的部分） |
| 「`_check_ordering` / `_check_hash` / `_check_null` / `_check_enum` 四类为无条件通过」 | **不准确**：它们在 `_check_vector` L380-385 中**仅在 golden 匹配通过后**才添加（`if passed:`）。准确表述是：这四项是**基于 golden 匹配的派生断言**，并未对 ordering/hash/null/enum 作独立验证（`_check_deterministic` 是唯一真正独立复跑的检查） |
| 「CF-015 未满足 → 83 个 ID 未验证」 | 修正为：**52 个所需 ID 中 35 个未被该检查纳入**，且其中约 **21 个根本不存在任何验证器** |

> 勘误不影响核心结论（`certified` 的强度被高估），但**影响工作量估算与实施路径**。

## 2. 为何须 ACP 而非直接修

1. `reference/conformance_runner.py` 与 `reference/knowledge_behavior.py` / `consensus_behavior.py`
   均属 H3 列的冻结工件（Reference 行为实现）；
2. 存在**两条正当出路**（补齐实现 vs 修订 CF-015），选择权属人工（H3：发现设计不足 → 停止并出 ACP）。

## 3. 选项

### 选项 A —— 补齐实现以符合 CF-015（真实覆盖）

| 阶段 | 内容 | 量级 |
|------|------|------|
| **A-1（机制，先行且独立可交付）** | runner 中定义 `REQUIRED_BEHAVIOR_IDS`(52) 与**声明的代表物注册表**；`_check_behavior_coverage` 逐 ID 校验代表物**真实存在且通过**；无代表物 → **FAIL**（符合 CF-015 原文）；派生四项检查改名并如实标注 "derived from golden match" | 小（1 文件） |
| **A-2（补 KB 验证）** | 依据 `KNOWLEDGE_BEHAVIOR_SPEC.md` KB-001~KB-011 补写验证器并接入 `audit()` | 中（11 条 + 测试） |
| **A-3（补 CS 验证）** | 依据 `CONSENSUS_BEHAVIOR_SPEC.md` 补写缺失 CS 验证器并接入 `audit()` | 中（约 10 条 + 测试） |
| **A-4（向量化与追溯）** | 为 52 个 ID 建立"ID ↔ 代表物（向量/验证器）"的**机器可校验**登记，必要时为 KB/CS 生成对应 golden vector | 中 |
| **A-5（口径定稿）** | 定稿 `certified` 语义：建议 `certified = (failed == 0)`，另暴露 `behavior_coverage = 已代表/52`；**覆盖不足时 `certified` 必须为 False** | 小 |

**关键后果**：A-1 一旦落地并合并，`ConformanceRunner` 将**如实报告 `certified=False`**，
CI（`.github/workflows/test.yml` L18-20 断言 `r.certified`）随之变红 —— **这是修正而非回归**，
但在 A-2~A-4 完成前会持续红灯。故 **A-1 的合并时机必须与 A-2~A-4 的计划一并决定**。

### 选项 B —— 经 ACP 修订 CF-015（降低规范要求）

- 将覆盖要求收窄为「**已具备代表物的层**」，并为 35 个 ID 出具**显式豁免清单与理由**；
- `CONFORMANCE_SPEC.md`（冻结，当前 1.0.0）须**版本递增**；`certified` 语义收窄为「已声明范围」；
- 代价：CF-015 从此不再保证"全部行为合约被覆盖"，**规范强度下降**。

## 4. 影响面

| 对象 | 影响 |
|------|------|
| `reference/conformance_runner.py` | 冻结（须 ACP） |
| `reference/knowledge_behavior.py` / `consensus_behavior.py` | 冻结（须 ACP） |
| `docs/specification/CONFORMANCE_SPEC.md` CF-015 | 冻结规范（选项 B 须版本递增） |
| `.github/workflows/test.yml` L18-20 | 选项 A-1 合并后**将变红**，直至 A-2~A-4 完成 |
| 域认证（Qimen/BaZi/Ziwei） | **不受影响**（另有独立等价测试：30/30、24/24、24/24） |
| `docs/PROJECT_STATUS.md` §5.4 | 已有警示，须按本版勘误同步措辞 |

## 5. 建议

1. **接受 A-1/A-5 的语义**（`certified` 必须如实）：否则整个"认证"体系的可信度无法恢复 —— 这是本项目最重要的一项修正。
2. **A-1 不单独合并**：与 A-2~A-4 组成一个 Sprint（"Reference 行为覆盖补齐"），在**同一批次**内把覆盖补到 52/52 后再合并，避免 main 长时间红灯。
3. 若希望尽快落地可信机制、又暂不接受红灯：可选 **过渡方案** —— A-1 落地但 `certified` 保持现语义，
   **新增 `behavior_coverage` 与 `unrepresented_behaviors` 字段如实暴露**，同时把 CF-015 的门槛经
   **独立 ACP（选项 B 的限定版）**明确为"分阶段达标"。此过渡方案**必须书面**，不得默许。

## 6. 待批准事项

- [ ] 走 **A（补齐实现）** 还是 **B（修订 CF-015）** 还是 **过渡方案**？
- [ ] 若 A：是否授权一个 Sprint 完成 A-1~A-5（含约 21 条新验证器 + 52 个 ID 的机器登记）？
- [ ] 若 A：`certified` 在新口径下允许为 `False` 并接受 CI 红灯，还是采用过渡字段？
- [ ] 若 B：接受 `CONFORMANCE_SPEC` 版本递增与 35 条豁免清单？

> **批准前不修改** `reference/` 与 `docs/specification/` 任何文件。本版仅更正档案。
