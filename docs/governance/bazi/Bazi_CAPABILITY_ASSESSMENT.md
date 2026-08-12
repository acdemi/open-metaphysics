# BaZi Domain Capability Assessment

> **Sprint**: Phase 6.1 — BaZi Domain Capability Migration Assessment
> **模式**: Governance Framework Validation（无功能实现）
> **日期**: 2026-08-09
> **目的**: 评估 BaZi 域当前成熟度，验证 Capability Lifecycle Framework
> 是否领域无关；产出 → Contract Candidate 的迁移要求。
> **依据**: `docs/governance/CAPABILITY_LIFECYCLE.md`（阶段/状态模型）

---

## 1. 审计范围与方法

| 层 | 检查位置 | 结果见 |
|----|----------|--------|
| 计算层 | `src/openmetaphysics/agents/bazi.py`（305 行, engine v0.1.0）+ `core/calendar.py` | §2.1 |
| 契约层 | `docs/`、`docs/specification/`、`reference/contracts/` | §2.2 |
| Reference 层 | `reference/`（含子目录） | §2.3 |
| 测试层 | `tests/test_bazi.py`（145 行, 11 例） | §2.4 |
| Schema | `src/openmetaphysics/agents/bazi.py`（BaziInput/Pillar/BaziChart/BaziOutput） | §2.1 |

---

## 2. Current State Audit

### 2.1 Calculation Layer

| 项 | 状态 | 证据 |
|----|------|------|
| 确定性计算存在 | ✅ | `BaziEngine(DeterministicEngine)` v0.1.0，`calculate()` 纯函数，无 LLM/随机/IO/时钟依赖 |
| 输入/输出 Schema 存在 | ✅ | `BaziInput(AgentInput)`（含 `dayun_count`, gender, born_at, born_location）；`BaziChart`/`Pillar`/`DaYun` 均 `extra="forbid"`；`BaziOutput` 信封 |
| Schema 文档化/导出 | ❌ | 无 JSON Schema 导出；未登记 `docs/SCHEMAS.md`（Qimen 有 §3.3 登记） |
| 边界用例文档化 | ⚠️ 部分 | 测试覆盖：立春年界（`test_lichun_boundary_switches_year`）、23:00 晚子时换日（`test_2300_day_rollover`）、性别未知回退（`test_gender_assumed_flag`）；但**无独立算法假设文档**（Qimen 有 QIMEN_ALGORITHM_ASSUMPTIONS.md） |
| 历法/时间规则显式 | ✅ | `core/calendar.py` 显式函数：`solar_term_time`（Meeus）、`lichun_time`、`sexagenary_day_index`（JDN+49）、`month_boundary_before`、`bazi_year_index`；engine 元数据声明 `solar_term_precision: "approx_1min"` |
| 主要规则 | — | 年柱=立春界；月柱=节界+五虎遁；日柱=干支日序（23:00 换日）；时柱=五鼠遁；十神/藏干/纳音/大运（性别+年干阴阳定顺逆, 3 天=1 年） |

**结论**: Stage 1（Calculation Runtime）**实质性满足**（确定性算法 + 领域 Schema + 测试）。
缺项：Schema 文档登记、算法假设文档。

### 2.2 Contract Layer

| 项 | 状态 | 说明 |
|----|------|------|
| Behavior Contract | ❌ | 无 `BAZI_BEHAVIOR_CONTRACT.md`（Qimen 有 v1.0.0） |
| 规则裁定文档 | ❌ | 无冻结规则清单 / 规则 ID（Qimen 有 QIMEN_RULE_DECISION.md, D1~D14） |
| Golden Vectors | ❌ | 无领域向量（`docs/qimen/golden_vectors.json` 仅为 Qimen；framework 向量 `reference/conformance/golden/*` 中的 `rule:bazi:*` 为 **DSL 示例规则 ID**，非 BaZi 域规范装置） |
| Freeze Review | ❌ | 无（Qimen 有 QIMEN_FREEZE_REVIEW.md PASS） |

**结论**: Stage 2（Behavior Contract）**未开始**。契约层零工件。

### 2.3 Reference Layer

| 项 | 状态 | 说明 |
|----|------|------|
| 独立实现 | ❌ | `reference/bazi/` **不存在**（`reference/qimen/` 为唯一域实现） |
| 交叉验证 | ❌ | 无 Product ↔ Reference 对照 |
| 确定性比较 | ❌ | 无等价测试套件 |

**结论**: Stage 3（Reference Certification）**未开始**。Reference 层零工件。

### 2.4 Tests

- `tests/test_bazi.py`: **11 例全部通过**（四柱、立春界、晚子时、藏干纳音、十神、大运、gender_assumed、explainer fallback/pattern）
- 注意: 2 例为 `BaziExplainer` 测试（解释层，非计算域范围，迁移时不影响）
- 无向量回归（对比 Qimen: 24 向量机器回归 + reference/tests 38 例）

---

## 3. Lifecycle Mapping（Task B）

| Stage | Requirement | Status | Missing Artifact |
|-------|-------------|--------|------------------|
| Stage 0 Exploration | domain scope / 非正式规则记录 | ⚠️ 部分 | 无规则/算法假设文档（规则仅存在于代码与测试注释） |
| Stage 1 Calculation Runtime | deterministic engine + schema + tests | ✅ **满足** | JSON Schema 导出 + SCHEMAS.md 登记（次要） |
| Stage 2 Behavior Contract | frozen rules + versioned contract + golden vectors | ❌ 未开始 | 规则裁定文档（冻结规则清单）→ 契约草案 → Golden Vectors（≥ 覆盖 立春界/晚子时/节气/性别/大运方向）→ Freeze Review |
| Stage 3 Reference Certification | independent implementation + contract verification + equivalence | ❌ 未开始 | `reference/bazi/` 独立实现 + 契约审计 + 等价测试 |
| Stage 4 Certified Capability | governance registration + integration ready | ❌ 未开始 | CAPABILITY_STATUS.md 注册 + 变更政策 |

**当前状态（Status Model）**: **Implemented** —— 正确，不可升级。
依据: Stage 1 满足但 Stage 2 工件为零，Contract Candidate 需要契约草案 + Freeze Review，均不存在。

---

## 4. Missing Artifacts（→ Contract Candidate 迁移要求）

按迁移顺序（对齐 `CAPABILITY_LIFECYCLE.md` §5）:

1. **BaZi 算法假设文档**（Stage 0 补完）: 明确记录 立春年界、23:00 换日、
   approx_1min 节气精度、大运起运（3 天=1 年取整）、性别 UNKNOWN 回退
   —— 与 Qimen D2 同性质（近似显式声明为规范候选）。
2. **规则裁定文档**（Stage 2 前置）: 将 engine 规则枚举为冻结规则清单
   （如 B1: 年柱立春界 / B2: 月柱节界+五虎遁 / B3: 日柱 23:00 换日 /
   B4: 时柱五鼠遁 / B5: 十神推导 / B6: 大运顺逆+起运），逐条核对
   定义→实现→测试覆盖。
3. **Golden Vectors 草案**（24 量级参考 Qimen）: 覆盖维度建议
   立春边界 / 晚子时 / 节气月界 / 性别×大运方向 / 闰月 / 时区 / 无坐标回退。
4. **契约草案 + Freeze Review**（Qimen 流程: QIMEN_BEHAVIOR_CONTRACT.md 模板）。
5. **Schema 登记**: SCHEMAS.md 新增 §（BaziInput/BaziChart + JSON Schema 导出）。

> 注意: 契约化**不包含**解释层/格局/用神/流年判断 —— 那些属未来授权 Sprint，
> 与确定性排盘能力分离（Domain Boundary, ARCHITECTURE.md §1）。

---

## 5. 结论

- BaZi 计算层成熟（Stage 1 实质满足），契约/Reference 层为零 → **状态: Implemented**
- 迁移至 Contract Candidate 的**唯一前置**是 规则裁定 + 向量草案 + 契约草案 + Freeze Review（全部为治理/文档工件，不要求算法改动）
- 框架验证结论见 `docs/governance/CAPABILITY_TEMPLATE_REVIEW.md`
