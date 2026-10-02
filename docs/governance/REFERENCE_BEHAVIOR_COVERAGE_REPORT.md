# Reference 行为覆盖补齐报告（ACP-REF-001 选项 A 实施）

> **Sprint**: P1-1 · **日期**: 2026-09-16 · **分支**: `work/reference/p1-behavior-coverage`
> **授权**: 人工裁定「补齐实现（选项 A），授权一个 Sprint，接受期间 CI 红灯」
> **依据**: `docs/governance/ACP/ACP-REF-001_conformance_behavior_coverage.md`

---

## 1. 结果

| 指标 | 前 | 后 |
|------|----|----|
| Conformance 检查总数 | 135 | **170** |
| 行为覆盖检查条数 | 17（硬编码、恒真） | **52**（逐条真实执行） |
| `behavior_coverage` | 未暴露 | **1.0（52/52）** |
| `unrepresented_behaviors` | 未暴露 | **[]** |
| `certified` | True（强度被高估） | **True（强度已如实）** |
| 全仓测试 | 618 | **627**（+9，含 2 个负向对照） |

**关键结果**：因补齐了缺失验证器，实施后覆盖率即为 **52/52**，`certified` 始终为 True 且强度如实 ——
**未出现红灯**（授权的「接受红灯」未被用到）。`CONFORMANCE_SPEC` **零修改**（走 A 而非 B）。

## 2. 证据与复现

```bash
pytest -q                       # 627 collected, exit 0
ruff check src/ tests/ reference/   # All checks passed
python -c "from reference.conformance_runner import ConformanceRunner, ReferenceAdapter as A; \
  r=ConformanceRunner().run(A(),'reference','1.0.0'); \
  print(r.certified, r.passed, r.total, r.behavior_coverage, r.unrepresented_behaviors)"
# -> True 170 170 1.0 []
```

**机制非空转的证明**（`tests/test_reference_behavior_coverage.py`）：
- `test_missing_representation_fails_conformance`：注入缺失代表物 → `certified=False`、`behavior_coverage<1.0`、
  `CF-BEHAV-KB-001` 失败；
- `test_failing_representation_fails_conformance`：代表物返回 False → `certified=False`。

**契约 ID 集合**：`REQUIRED_BEHAVIOR_IDS` = 7 BC（CF-015 列举）+ KB-001~020 + CS-001~025 = **52**。

## 3. 边界与零触碰

| 改动 | 说明 |
|------|------|
| `reference/conformance_runner.py` | `REQUIRED_BEHAVIOR_IDS` + `_behavior_representation()` + 重写 `_check_behavior_coverage` + 派生检查措辞如实化 |
| `reference/conformance.py` | `ConformanceResult` 新增 `behavior_coverage` / `unrepresented_behaviors` |
| `reference/knowledge_behavior.py` | 新增 KB-001~011 验证器；`audit()` 由 5 键扩到 KB-001~020 全覆盖；**并更正原映射错误** |
| `reference/consensus_behavior.py` | 新增 13 条 CS 验证器；`audit()` 由 5 键扩到 CS-001~025 全覆盖 |
| `tests/test_reference_behavior_coverage.py` | 新增 9 条（含 2 负向对照） |

- **`docs/specification/` 零修改**（选项 A 无需改 CF-015）。
- 未触碰 `reference/contracts/*.json`、Golden Vectors、域算法（`reference/{qimen,bazi,ziwei}`）、`src/`。
- 域认证（Qimen 30/30、BaZi 24/24、Ziwei 24/24）不受影响（独立等价测试）。

> **一处诚实更正**：原 `knowledge_behavior.audit()` 把 KB-013~015 当作「节点列表排序」、
> 把确定性挂在 KB-019、`audit()` 只调用 5 项 —— 与 `KNOWLEDGE_BEHAVIOR_SPEC.md` 原文不符。
> 本次已按规范逐条对齐（KB-013/014/015 = `find_by_type`/`find_by_system`/`find_by_tag` 的排序；
> KB-016 = `find_relation`；KB-017 = `find_reference`；KB-019 = 重复关系拒绝；KB-020 = 确定性与 JSON 稳定）。

## 4. GAP 与决策点

| 项 | 状态 |
|----|------|
| **待确认（D-16）** | CF-015 原文用词为 "at least one **golden vector**"；本次代表物为**可执行行为验证器**（更强、执行真实断言）与对应层 golden 检查，**字面**不完全一致。若要求严格一致，须再出一小 ACP 明确代表物形态或补生成对应向量 |
| D-13 | 已由本 Sprint 关闭（认证口径与空转检查处置完成） |
| `ACP-REF-002` | 仍 **PROPOSED**（范围扩张追认 + rule/pattern 契约），拟与 Reference 最终冻结同批 |

## 5. 产出物清单

| 文件 | 状态 |
|------|------|
| `reference/conformance_runner.py` / `conformance.py` | 修改 |
| `reference/knowledge_behavior.py` / `consensus_behavior.py` | 修改（+24 验证器） |
| `tests/test_reference_behavior_coverage.py` | 新增（9 条） |
| `docs/governance/ACP/ACP-REF-001_conformance_behavior_coverage.md` | PROPOSED → **IMPLEMENTED** |
| `docs/governance/ACP/README.md` / `docs/PROJECT_STATUS.md` §5.4 / `docs/PROJECT_REVIEW_2026-09-16.md` §2.2·§4.2 | 状态刷新 |
