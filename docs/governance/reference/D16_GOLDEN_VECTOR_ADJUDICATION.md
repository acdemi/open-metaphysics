# D-16 Golden Vector Adjudication

> **This is a governance decision record — not an implementation plan.**

---

## §0 Governance Metadata

```text
document: D-16 Golden Vector Adjudication
project: ACIS
domain: Reference / Conformance
baseline: main @ de97fd7
source: D16_GOLDEN_VECTOR_CLARIFICATION.md
status: ADJUDICATED — DECISION RECORDED; IMPLEMENTATION NOT YET AUTHORIZED
decision_authority: CAO
decision_scope: D-16
```

**Decision basis**: `docs/governance/reference/D16_GOLDEN_VECTOR_CLARIFICATION.md`（事实核查与 A/B 分析），
已冻结规范（`docs/specification/CONFORMANCE_SPEC.md`、`docs/specification/IMPLEMENTATION_GUIDE.md`），
已冻结实现（`reference/conformance.py`、`reference/conformance_runner.py`、
`reference/knowledge_behavior.py`、`reference/consensus_behavior.py`），以及 CAO 直接给出的裁定文本。

**Recorded governance state**（CAO 原文）：

```text
D-16 DECISION REACHED
D-16 IMPLEMENTATION NOT YET AUTHORIZED

P2:
NOT STARTED
```

**Implementation authorization**（CAO 原文）：**NONE AT THIS STAGE.**
No code, specification, golden vector, generator, RuntimeAdapter, ACP-REF-002, or P2 artifact
may be modified as part of this decision input.

---

## §1 Decision Record

### D-16-1

```text
Decision:
ALLOW

CF-015 may recognize an executable behavior representation as an equivalent
representation of a Behavior Contract for coverage purposes, provided that this
interpretation is explicitly established by the D-16 governance decision.

This does NOT redefine the existing JSON "golden vector" schema, and does NOT claim
that an executable verifier is itself a traditional golden vector artifact.

The current P1-1 executable behavior representation is therefore eligible to satisfy
the representation requirement only after this governance decision is formally recorded.
```

- **Rationale**（仅据澄清文档 §4 与 CAO 裁定文本）：
  澄清文档 §4.1 已确认 CF-015 的「known set」与「missing coverage MUST fail」两句在 P1-1 中已满足（52/52 执行、
  无代表物即失败），唯一未闭合的是「represented by … golden vector」一句的**形态**要求；
  澄清文档 §4.1 Q4 判定「按字面口径不能宣称合规」。CAO 选择以**治理解释**而非改文字的方式闭合该形态争议，
  并同时以两条否定句限定其边界（不重定义 JSON schema、不主张 verifier 本身即 golden vector）。
- **Governance consequence**：CF-015 的代表物语义自**本裁定记录成立之时**起，包含
  「executable behavior representation」这一**经治理决定确立的等价形态**；该等价性**不是**对
  `IMPLEMENTATION_GUIDE.md` §5 所定义 JSON 结构的修改。此解释为 D-16 范围内的**唯一有效解释**。
- **Implementation consequence**：**无**（本阶段零实现授权）。P1-1 现有机制不作改动。

### D-16-2

```text
Decision:
N/A

Option B is not authorized because D-16-1 permits the executable behavior
representation path.
```

- **Rationale**：D-16-1 = ALLOW 已闭合形态争议，故 Option B（按字面补齐传统 golden vector）未被授权。
- **Governance consequence**：Option B 路径**未被授权**；澄清文档 §6 所列 CF-013 / CF-017 / CF-018 /
  adapter 协议等约束**不进入执行**。
- **Implementation consequence**：不得扩展 `generate_golden_vectors()`、不得新增/标注 golden vector、
  不得扩展 `RuntimeAdapter`、不得改动 `reference/conformance/golden/`。

### D-16-3

```text
Decision:
N/A

No B-1 or B-2 implementation is authorized.
```

- **Rationale**：因 D-16-2 = N/A，B 的两个变体均无适用前提。
- **Governance consequence**：澄清文档 §6 的 B-1（生成器产出行为向量）与 B-2（向量加 `behavior_ids` 标注）
  **均为未授权路径**，不得以任何形式实施或"预备实施"。
- **Implementation consequence**：无。

### D-16-4

```text
Decision:
INDEPENDENT D-16 ACP

D-16 shall be handled through a dedicated D-16 ACP.

It may be scheduled in the same governance batch as ACP-REF-002, but it remains an
independently identifiable decision and must not be absorbed into ACP-REF-002's
unrelated scope-expansion or contract decisions.
```

- **Rationale**：澄清文档 §7.2 确认 D-16 **不属于** ACP-REF-002 的既有范围（后者处理
  `REFERENCE_RUNTIME_SPEC` §3.2 的范围边界与 `rule`/`pattern` 契约完备性；D-16 处理 `CONFORMANCE_SPEC`
  CF-015 的代表物形态语义，涉及 golden 向量与生成器），故需独立可识别的治理载体。
- **Governance consequence**：D-16 由**专属 D-16 ACP**承载；可与 ACP-REF-002 同批排期，但
  **不得被吸收**进 ACP-REF-002 的无关范围扩张或契约决定。`ACP-REF-002` 本身**未被本裁定修改**。
- **Implementation consequence**：无（本阶段零实现授权）；D-16 ACP 获批前不得实施 D-16 项下任何变更。

### D-16-5

```text
Decision:
ADD TO CONFORMANCE_SPEC §5

The fields:
- behavior_coverage
- unrepresented_behaviors

shall be formally described in the ConformanceResult field table.

An ACP is required before modifying the frozen specification.

Version impact is NOT PREJUDGED by this decision. The required specification version
increment, if any, shall be determined under the applicable specification versioning
rules during the ACP.
```

- **Rationale**：澄清文档 §3.5 记录了一项**同类、较小**的字面对齐问题 ——
  P1-1 新增的 `ConformanceResult.behavior_coverage` / `unrepresented_behaviors`
  （`reference/conformance.py:81-82`）**未见于** `CONFORMANCE_SPEC.md` §5 的
  `ConformanceResult` 字段表（L356-367）。CAO 裁定将其**正式补入**该表。
- **Governance consequence**：`docs/specification/CONFORMANCE_SPEC.md` §5 的字段表**需要变更**，
  且该变更**必须经 ACP** 后方可实施。版本影响**未被预先裁定**。
- **Implementation consequence**：**本阶段不得修改规范**；具体版本递增在 D-16 ACP 内按适用版本规则确定。

### 边界声明（覆盖全部五项）

```text
Implementation authorization: NONE AT THIS STAGE.
```

本裁定记录**不**授权任何代码、规范、golden vector、生成器、`RuntimeAdapter`、`ACP-REF-002`
或 P2 工件的修改。

---

## §2 D-16 Final Governance Interpretation

### 2.1 CF-015 representation semantics（唯一有效解释）

```text
CF-015 representation semantics:

An executable behavior representation is recognized as an EQUIVALENT representation
of a Behavior Contract for CF-015 coverage purposes, established ONLY by this D-16
governance decision.

It does NOT redefine the JSON "golden vector" schema
(IMPLEMENTATION_GUIDE.md §5 / CF-017 / CF-018), and it does NOT assert that an
executable verifier is itself a traditional golden vector artifact.

The P1-1 executable behavior representation becomes eligible to satisfy the
representation requirement upon formal recording of this decision (this document).
```

**唯一性**：自本记录成立起，CF-015 的代表物语义**只以本节为准**。
本文件**不同时保留** A/B 两个「当前有效」解释 —— Option B（D-16-2）与 B-1/B-2（D-16-3）
均为 **N/A / 未授权**，不构成并行有效路径。

### 2.2 Terminology discipline（术语纪律）

本裁定与后续 D-16 ACP 中，下列术语**不得互换使用**：

| 术语 | 精确定义 | 不得表述为 |
|------|----------|-----------|
| **golden vector** | `reference/conformance/golden/{layer}_vectors.json` 中的 JSON 对象，结构依 `IMPLEMENTATION_GUIDE.md` §5；由 `generate_golden_vectors()` 生成（CF-013）、自动发现（CF-017）、`expected_output` 为 adapter 产出的精确 canonical JSON（CF-018） | ✗ 不得把可执行验证器称为 golden vector |
| **executable behavior representation** | P1-1 中 `_behavior_representation()`（`conformance_runner.py:544`）解析出的 bool-returning 可执行断言 | ✗ 不得混写为 "golden vector 已存在" |
| **behavior verifier** | `knowledge_behavior.py` / `consensus_behavior.py` 中的 `verify_*` 静态方法 | ✗ 不得等同于 golden vector 工件 |
| **behavior coverage** | `ConformanceResult.behavior_coverage`（已执行代表物数 / 52） | ✗ 不得引申为「向量覆盖率」 |
| **supported_behaviors** | `ConformanceManifest` 字段，由 `certify()` 从 `BEHAVIOR_COVERAGE` 且 `passed` 的 check `name` 汇集 | ✗ **不得**当作 CF-015 的 golden-vector representation（CAO 未如此裁定） |

**特别禁令**（遵从 Task 3）：

1. **禁止**将「行为验证器通过」自动写成「golden vector 已存在」——
   除非这正是 D-16-1 明确裁定的语义。D-16-1 的措辞是 *equivalent representation*，
   **且明确声明不主张 verifier 本身即 golden vector**，故该写法不被允许。
2. **禁止**将 `supported_behaviors` manifest 当作 CF-015 的 golden-vector representation。

---

## §3 Frozen Surface Impact

> **「CHANGE REQUIRED」不等于「本任务现在执行修改」。** 本节仅记录治理边界。

| 冻结面 | 状态 | 依据 / 说明 |
|--------|------|-------------|
| `docs/specification/CONFORMANCE_SPEC.md` §5（`ConformanceResult` 字段表） | **CHANGE REQUIRED** | D-16-5：两字段 **shall be formally described**；须先经 ACP。**本阶段不执行** |
| `docs/specification/CONFORMANCE_SPEC.md` CF-015 文字表述 | **UNCHANGED**（本裁定未要求改文字） | D-16-1 以治理解释确立等价形态，并明确「does NOT redefine the existing JSON golden vector schema」。是否需要文字层面的同步，属 D-16 ACP 内的规范编辑事项，**本裁定未预先确定** |
| `docs/specification/IMPLEMENTATION_GUIDE.md` §5（Golden Vector Format） | **UNCHANGED** | D-16-1 明确不重定义 JSON golden vector schema；D-16-2/D-16-3 = N/A，无新向量形态 |
| `reference/conformance.py`（`GoldenVector` / `RuntimeAdapter` / `ConformanceResult`） | **UNCHANGED** | 无授权变更；两字段**已存在**于实现（`:81-82`），D-16-5 只涉及规范描述 |
| `reference/conformance_runner.py`（`REQUIRED_BEHAVIOR_IDS` / `_behavior_representation` / `_check_behavior_coverage` / `certify`） | **UNCHANGED** | 无授权变更 |
| `reference/knowledge_behavior.py` / `reference/consensus_behavior.py`（行为验证器） | **UNCHANGED** | 无授权变更 |
| `reference/conformance/golden/*.json`（19 条向量） | **UNCHANGED** | D-16-2/D-16-3 = N/A；不新增、不标注、不重生成 |
| `docs/governance/ACP/ACP-REF-002_scope_expansion_and_contracts.md` | **NOT IN SCOPE** / **UNCHANGED** | D-16-4：D-16 须独立可识别，不得被吸收；本裁定未修改该文件 |
| `docs/specification/REFERENCE_RUNTIME_SPEC.md` §3.1/§3.2/§6.1/§10 | **NOT IN SCOPE** | 属 ACP-REF-002 范围，与 D-16 无关 |
| `docs/governance/CAPABILITY_STATUS.md` | **NOT IN SCOPE** | 本裁定未触及 |

**本任务实际改动**：仅新增本文件（见 §9 审计）。

---

## §4 ACP Boundary

依据 **D-16-4 = INDEPENDENT D-16 ACP**：

```text
D-16 ACP must be approved before implementation.
```

**治理关系**

- **独立载体**：D-16 由**专属 D-16 ACP**处理；**不并入** ACP-REF-002 的范围扩张与契约决定。
- **可同批排期**：D-16 ACP 可与 ACP-REF-002 排入**同一治理批次**，但二者**分别可识别**。
- **不可混入**（D-16-4 原文要求）：

```text
D-16 remains an independently identifiable decision item
and must not be absorbed into unrelated scope-expansion decisions.
```

**范围划分（依 D-16-1 / D-16-4 / D-16-5 记录，非新增裁定）**

| 事项 | 归属 | 说明 |
|------|------|------|
| 固化 CF-015 的 executable behavior representation 等价解释 | **D-16 ACP** | D-16-1 的治理解释需在专属 ACP 中作为规范载体落地（具体编辑形态属该 ACP 内决定） |
| `CONFORMANCE_SPEC.md` §5 补入 `behavior_coverage` / `unrepresented_behaviors` 描述 | **D-16 ACP** | D-16-5 明确 *An ACP is required before modifying the frozen specification* |
| §5 变更所引发的版本递增判定 | **D-16 ACP** | D-16-5：*Version impact is NOT PREJUDGED*，按适用版本规则在 ACP 内确定 |
| `REFERENCE_RUNTIME_SPEC.md` §3.1/§3.2/§6.1/§10 的范围扩张追认 | **ACP-REF-002** | 与 D-16 无关，**不得混入** D-16 ACP |
| `rule_contract.json` / `pattern_contract.json` 补全 | **ACP-REF-002** | 同上 |
| `CAPABILITY_STATUS.md` 增加 Reference Runtime 登记行 | **ACP-REF-002** | 同上 |
| Reference Runtime 最终冻结条件 | **ACP-REF-002**（其 §5） | 其中「认证口径定稿」条件与 D-16 相关，但 D-16 结论须以**独立可识别**方式引用，不得被范围扩张议题覆盖 |

**未在本裁定中确定的事项**：D-16 ACP 中 CF-015 文字是否需要同步修订（见 §3）。

---

## §5 P1-1 Disposition

D-16-1 = **ALLOW**，故：

```text
P1-1 implementation remains unchanged.
```

- **P1-1 的 52/52 行为覆盖执行结果予以保留，且不被重新定义。**
  已记录事实（`main @ de97fd7`）：Conformance **170/170**、`REQUIRED_BEHAVIOR_IDS` = **52**、
  `behavior_coverage` = **1.0**、`unrepresented_behaviors` = **[]**、`certified` = **True**、
  全仓测试 **627/627**、`ruff` clean。
- **机制术语的正确读法**：P1-1 的代表物是 `executable behavior representation`（§2.2 术语表），
  **不是** golden vector 工件；其合格性来源是**本裁定记录**（D-16-1 的 "only after this governance
  decision is formally recorded"），而非对 JSON 向量 schema 的重新定义。
- **未授权项**：本裁定**不授权**改动 P1-1 任何代码；`ConformanceResult` 两字段的**规范描述**
  属 D-16-5（须 ACP，见 §7）。
- **历史实验/验证结果不作修改**：本记录不重跑、不重述、不弱化 P1-1 的既有验证回执。

---

## §6 P2 Gate

```text
P2 MUST NOT START until D-16 governance closure
and all required authorization gates are satisfied.
```

具体状态（依 D-16-4 与 ACP-REF-002 现状）：

```text
P2 remains blocked pending ACP approval and implementation/evidence closure.
P2 remains blocked by remaining Reference governance gates.
```

- **理由 1（D-16 侧）**：D-16-1 ~ D-16-5 已**裁定**，但 **D-16 IMPLEMENTATION NOT YET AUTHORIZED**；
  D-16-4 要求专属 D-16 ACP，且该 ACP 的规范变更（D-16-5）尚未获批 → **D-16 governance closure 未完成**。
- **理由 2（Reference 侧）**：`ACP-REF-002` 仍为 **PROPOSED**（未批准），其项下的范围扩张追认、
  `rule`/`pattern` 契约补全、Reference 登记行与最终冻结条件均未闭合。

**明确禁止**：**不得**因为 D-16 已裁定而自动启动六爻 Contractification（P2）。
本裁定**不构成** P2 的启动授权。

---

## §7 D-16-5 — ConformanceResult Fields

对象字段：

```text
behavior_coverage
unrepresented_behaviors
```

**现状（事实）**：二者已于 P1-1 存在于冻结实现
（`reference/conformance.py:81-82`；赋值处 `reference/conformance_runner.py:681-682`），
但**未见于** `docs/specification/CONFORMANCE_SPEC.md` §5 的 `ConformanceResult` 字段表（L356-367）。

**依 CAO 的 D-16-5 裁定逐项记录**（不扩大影响范围）：

| # | 问题 | 记录 |
|---|------|------|
| 1 | 是否属于规范定义字段 | **应成为规范定义字段** —— D-16-5：*shall be formally described in the ConformanceResult field table*。当前仅为**实现事实**，规范描述待补 |
| 2 | 是否需要补入 `CONFORMANCE_SPEC.md` §5 | **是**（shall be formally described） |
| 3 | 是否触发版本递增 | **未预先裁定（NOT PREJUDGED）** —— 按适用规范版本规则**在 ACP 内**确定 |
| 4 | 是否需要 ACP | **是** —— *An ACP is required before modifying the frozen specification* |
| 5 | 是否允许作为当前实现事实保留但暂不进入规范 | **本裁定未授权任何当前修改**；D-16-5 的方向是**经 ACP 补入规范**。因此「长期停留于实现而不进入规范」**不是** D-16-5 所确立的状态（该裁定用词为 *shall*）。本阶段既不修改规范，也不修改实现 |

**不得扩大**：D-16-5 仅涉及上述**两个字段**的描述与 ACP 前置；
**不**涉及字段语义变更、**不**涉及新增字段、**不**涉及 `ConformanceManifest` 的改动。

---

## §8 Next Authorized Action

依据 D-16-4（INDEPENDENT D-16 ACP）与 D-16-5（改规范须先经 ACP），且本阶段实现授权为 **NONE**：

```text
NEXT AUTHORIZED ACTION:
Prepare the dedicated D-16 ACP for approval —
formalize the CF-015 executable-behavior-representation interpretation
and add behavior_coverage / unrepresented_behaviors to CONFORMANCE_SPEC §5 —
with no implementation until that ACP is approved.
```

**该动作的边界**：

- 该 ACP **仅限于 D-16 范围**（不得混入 ACP-REF-002 的范围扩张与契约决定）。
- 在 D-16 ACP 获批前：**不得**修改 `CONFORMANCE_SPEC.md`、**不得**修改 `IMPLEMENTATION_GUIDE.md`、
  **不得**修改 `reference/`、**不得**生成 golden vector、**不得**启动 P2。
- 起草 ACP **本身**亦未在本裁定中被授权为「立即执行」；
  本裁定记录的是**唯一后续路径**，实际起草需由后续指令启动。

> 本节**不提供备选路径**（无 "A or B"、无 "recommended/alternative"）；D-16 范围内的唯一有效解释见 §2.1。

---

## §9 Runtime Object Status（recorded state）

```text
D-16:
    ADJUDICATED (decision recorded; implementation not yet authorized)

P1-1:
    UNCHANGED (implementation preserved as-is; results not redefined)

D-16-1: ALLOW    D-16-2: N/A    D-16-3: N/A    D-16-4: INDEPENDENT D-16 ACP
D-16-5: ADD TO CONFORMANCE_SPEC §5 (ACP required; version impact not prejudged)

P2:
    NOT STARTED (blocked)
```

---

*本文件为治理裁定记录。它不构成实现授权，也不改变任何冻结工件、代码、golden vector 或 P2 工件。*
