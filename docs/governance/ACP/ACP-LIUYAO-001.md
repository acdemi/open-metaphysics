# ACP-LIUYAO-001 — 六爻行为契约冻结与 Reference 认证

> **Status**: **IMPLEMENTED**（2026-10-23 人工批准并实施）
> **Date**: 2026-10-23
> **Domain**: Liuyao（六爻）
> **Proposer**: OpenMetaphysics engineering
> **Approved by**: 用户（2026-10-23，D1-D4）
> **Approval required**: 是（H3：Behavior Contract / Golden Vectors / Reference behavior）
> **Related**: `ACP-REF-001`、`ACP-REF-002`（流程先例）；BaZi / Ziwei / Qimen 冻结先例

---

## 1. 背景

六爻 Phase B 契约化在批准时停留在 candidate：

- `docs/liuyao/LIUYAO_RULE_INVENTORY.md`（LY-01~LY-11）
- `docs/liuyao/LIUYAO_BEHAVIOR_CONTRACT.md`（v1.0.0 candidate，30 条）
- `docs/liuyao/golden_vectors.json`（candidate）
- `reference/liuyao/`（自包含，v0.1.0）
- `reference/tests/test_liuyao_equivalence.py`（等价证明）

现状问题：

1. 契约、向量、Reference 已可用，但未走 ACP，不能标记 Frozen。
2. `CAPABILITY_STATUS.md` 矩阵写 `Implemented / 无 / 无 / 无`，详细节却写
   `Integration Ready`，状态自相矛盾。
3. 自动 seed 路径受 `PYTHONHASHSEED` 影响，不能作为冻结行为。
4. Reference 对 tz-naive `born_at` 静默按 UTC 处理，与生产拒绝行为不一致。
5. 契约未写明互卦 `cast_value` 语义；向量/文档仍写 24 条。

本 ACP 已批准：**将六爻 candidate 契约/向量/Reference 正式冻结并认证**，
同时批准为消除上述矛盾所做的冻结前修正。

---

## 2. 拟冻结工件

| 工件 | 版本/数量 | 拟议状态 |
|------|-----------|----------|
| `docs/liuyao/LIUYAO_BEHAVIOR_CONTRACT.md` | `liuyao:behavior:v1.0.0` / 30 clauses | **FROZEN** |
| `docs/liuyao/golden_vectors.json` | 25（normal 10 / edge 6 / boundary 5 / invalid 4） | **FROZEN** |
| `docs/liuyao/LIUYAO_RULE_INVENTORY.md` | LY-01~LY-11 | **FROZEN**（随契约） |
| `reference/liuyao/` | v0.1.0 | **CERTIFIED** |
| `reference/tests/test_liuyao_equivalence.py` | 8 tests | **CERTIFIED EVIDENCE** |
| `docs/liuyao/LIUYAO_FREEZE_REVIEW.md` | PASS | 冻结记录 |
| `docs/liuyao/LIUYAO_REFERENCE_AUDIT.md` | PASS | 审计记录 |
| `docs/liuyao/LIUYAO_REFERENCE_CERTIFICATION.md` | CERTIFIED | 认证记录 |
| `docs/liuyao/LIUYAO_INTEGRATION_READINESS.md` | READY | 就绪评估 |

**不冻结**：`src/openmetaphysics/agents/liuyao.py`（生产实现保持不变）、
`docs/specification/`、`reference/contracts/`、其他域工件。

---

## 3. 冻结前修正（已实施，待追认）

### 3.1 LC-003：Reference 拒绝 tz-naive

- 生产 `AgentInput` 已拒绝 tz-naive；Reference 原先静默补 UTC。
- 修正：`reference/liuyao/domain.py` 改为抛
  `ValueError("born_at must be timezone-aware")`。
- 证据：新增 `LY_inv_004` + 等价测试拒绝断言。
- 影响：仅 candidate Reference；不改变生产行为。

### 3.2 LC-004 / LC-D04：自动 seed 明确为冻结外

- 生产在无 `casts`/`seed` 时自动 seed；`derive_seed` 使用 `hash()`，跨进程
  不可复现。
- 契约明确：冻结只覆盖显式 `casts`/`seed`；自动 seed 不在契约内。
- Reference 继续拒绝无 `casts`/`seed`；等价测试显式锁定该边界。
- **不修改**共享 `core/engines.py`（H2）。

### 3.3 LC-015：互卦 `cast_value` 澄清

- 生产与 Reference 均保留源 cast（6/9），仅 `is_changing=false`。
- 契约补写该语义；无代码变更。

### 3.4 向量与文档计数

- 新增 `LY_inv_004`（tz-naive 拒绝），向量 24 → 25，invalid 3 → 4。
- 契约头部已从“candidate fixtures”改为“normative fixtures（Frozen）”。
- 同步 `LIUYAO_RULE_INVENTORY.md`、`reference/liuyao/README.md`。

### 3.5 EOL 规范化（证据稳定性）

- `.gitattributes` 新增 Liuyao 作用域：`docs/liuyao/**`、`reference/liuyao/**`、
  `reference/tests/test_liuyao_equivalence.py`、`tests/test_liuyao*.py`、
  `tools/gen_liuyao_golden_vectors.py` 固定 `text eol=lf`。
- 原因：Windows `core.autocrlf=true` 会使同一工件在不同 worktree 产生不同
  SHA-256；冻结证据必须可复算。
- 影响：仅 EOL；无行为变化。Frozen digests 见
  `LIUYAO_REFERENCE_CERTIFICATION.md` §5。

---

## 4. 证据

| 证据 | 结果 |
|------|------|
| 定向 pytest（liuyao + golden + equivalence） | **20 passed**（6 + 6 + 8） |
| 生产 ↔ Reference 合法向量 | **21/21 byte-identical** |
| 生成输入 | **40/40 byte-identical**（`SEED=20260916`） |
| 显式 seed | 4/4（0/1/12345/2^31-1） |
| 23:00 换日边界 | 5/5 |
| 拒绝路径 | 4/4（长度/值域/时区） |
| Reference 表一致性 | 6 类表 + 2 个历法函数 PASS |
| Reference 源码独立 | 3 文件无 `openmetaphysics` 导入 |
| 全量 pytest | **1024 passed + 2 skipped**（1026 collected，2026-10-23） |
| ruff check | `src reference tests tools` 全部通过 |
| knowledge validate | `VALIDATION PASSED` |

---

## 5. 变更影响

### 5.1 行为

- **生产计算行为零变化**：未修改 `src/openmetaphysics/agents/liuyao.py`。
- Reference 仅收紧 tz-naive 输入（向生产对齐）；显式输入行为不变。
- 自动 seed 仍按现有生产行为运行，但明确不属于冻结契约。

### 5.2 兼容性

- 已使用显式 `casts`/`seed` 的客户端：无影响。
- 依赖自动 seed 的客户端：仍可运行；但其结果不承诺跨进程可复现，且不在
  冻结契约内。
- 其他域：零触碰。

### 5.3 风险

| Risk | 等级 | 缓解 |
|------|------|------|
| 自动 seed 被误认为冻结行为 | Medium | 契约 + 测试 + 状态文档三处声明 |
| 向量由生产生成（自证风险） | Medium | 独立 Reference + 40 生成输入 |
| Reference 修正引入回归 | Low | 定向 + 全量回归；只改拒绝路径 |
| 状态文档提前写 Frozen | Medium | 批准前统一写 Contract Candidate |

---

## 6. 批准记录

用户于 **2026-10-23** 以「批准」批准以下四项：

1. **D1**：冻结 `liuyao:behavior:v1.0.0`（30 条款）。
2. **D2**：冻结 25 条 Golden Vectors，并将 metadata 改为 `frozen`。
3. **D3**：认证 `reference/liuyao/` v0.1.0；接受 LC-D04 自动 seed 为冻结外，
   LC-042 信封为 Agent 层验证。
4. **D4**：将 `CAPABILITY_STATUS.md` 中 Liuyao 从 **Contract Candidate** 升级为
   **Integration Ready（Certified Frozen Capability）**，并同步 ROADMAP /
   PROJECT_STATUS / README / SCHEMAS。

批准原文：

```text
批准
```

---

## 7. 实施记录

| 步骤 | 状态 |
|------|------|
| D1 契约 v1.0.0 标记 Frozen | DONE |
| D2 25 Golden Vectors metadata → frozen + SHA-256 | DONE |
| D3 Reference 认证生效（20 targeted / 1024 + 2 full） | DONE |
| D4 CAPABILITY_STATUS 等状态指针 → Integration Ready | DONE |
| ACP README 登记 → IMPLEMENTED | DONE |
| 全量 pytest / ruff / validate | DONE |
| 合并（H7） | DONE（`7a6d7bb`，2026-10-23；归档 `930ae70`；EOL `a27bb4a`） |

冻结工件摘要见 `LIUYAO_REFERENCE_CERTIFICATION.md` §5；合并前不得推送 origin。

---

## 8. 回滚预案

若后续撤销本 ACP：

- 将 `LIUYAO_BEHAVIOR_CONTRACT.md`、`golden_vectors.json`、Reference 与测试
  恢复到 Phase B candidate 状态（`9b88064` / `cdeb64e` 基线）。
- 删除本 ACP 的四份审查文档，或标记 `WITHDRAWN`。
- Liuyao 状态恢复 `Contract Candidate`；生产行为不受影响。
