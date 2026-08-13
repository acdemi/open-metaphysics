# Ziwei Integration Readiness

> **Sprint**: Phase 6.7.5 — Integration Readiness Closure（Governance Closure）
> **日期**: 2026-08-13
> **目的**: 审查 Ziwei 满足 Integration Ready 的全部条件, 形成治理闭环记录。
> **性质**: 审查文档。不新增能力、不修改冻结工件（src/ / reference/ziwei/ /
> golden_vectors.json 均未触碰）。

---

## 1. Integration Ready 条件审查（7/7）

| # | 条件 | 状态 | 证据 |
|---|------|------|------|
| 1 | **Contract Frozen** | ✅ | `docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT.md` **v1.0.0 Frozen**（`ziwei:behavior:v1.0.0`, 2026-08-13, BC-001~014, 无 DRAFT/Candidate/TODO/DEFERRED 残留） |
| 2 | **Reference Certified** | ✅ | `docs/governance/ziwei/ZIWEI_REFERENCE_CERTIFICATION.md`（24/24 等价 + 14/14 审计 + 独立性） |
| 3 | **Golden Vectors Frozen** | ✅ | `docs/ziwei/golden_vectors.json` **24 normative fixtures**（Engine v0.3.0 生成, candidate → normative, 不可变） |
| 4 | **Reference Equivalence PASS** | ✅ | `reference/tests/test_ziwei_equivalence.py` — **24/24 Reference == expected**, 全结构逐字段相等, 零偏差 |
| 5 | **Schema Registered** | ✅ | `docs/SCHEMAS.md` §3.2 登记（按冻结契约 BC-013 实际结构; 本 Sprint 完成契约登记头部 + 局名格式勘误） |
| 6 | **Change Policy Registered** | ✅ | 契约 §1 Freeze Record + §6 Change Procedure + CAPABILITY_STATUS.md Ziwei 节（与 CAPABILITY_LIFECYCLE.md §5 一致, 框架未修改） |
| 7 | **Domain Boundary Explicit** | ✅ | `docs/governance/ziwei/ZIWEI_CROSS_DOMAIN_BOUNDARIES.md` + 契约 §4 范围外 + §5 跨域声明（ZB-01/ZB-06/ZQ-02/D13 差异） |

**结论: 7/7 满足 → Ziwei 达到 Integration Ready 全部条件。**

---

## 2. Change Policy 正式引用

Ziwei 冻结工件的变更必须完整执行（与 `CAPABILITY_LIFECYCLE.md` §5 一致,
本 Sprint 未修改框架, 仅为正式引用）:

1. **ACP**（Architecture Change Proposal, 等待人工批准）
2. **Contract version increment**（v1.0.0 → 下一版本, 契约 §6）
3. **Golden Vector migration**（24 向量不可原地修改, 生成新向量集）
4. **Reference re-certification**（`reference/ziwei/` 同步更新 + 24/24 等价 + BC 审计重新通过）

引用位置: `ZIWEI_BEHAVIOR_CONTRACT.md` §1/§6 / `CAPABILITY_STATUS.md` Ziwei 节 /
本文件 §2。

---

## 3. Freeze Integrity Check（硬门, 8/8 PASS）

| # | 检查项 | 状态 | 证据 |
|---|--------|------|------|
| 1 | BC-001~014 全部存在且完整 | ✅ | 契约 §3（14 条款, 逐条含 Definition/Preconditions/Deterministic requirement/Observable output/Related rules/Golden vectors/Test references） |
| 2 | 每条 BC ≥1 Golden Vector 覆盖 | ✅ | 程序化核对: BC-001~013 规则映射零缺失（ZW-001~017 全部覆盖）; BC-014 = ALL(24) |
| 3 | 每条 BC 在 Reference 中有实现（注释标注） | ✅ | `reference/ziwei/*.py` 逐条款引用（BC-001~013 代码注释; BC-014 由向量+等价测试承载, 同 BaZi 处理） |
| 4 | 每条 BC 在 Reference Audit 列为 PASS | ✅ | `ZIWEI_REFERENCE_AUDIT.md` 14/14 PASS（逐条要求/行为/证据） |
| 5 | Contract 版本 = v1.0.0 | ✅ | 头部 + §1 Freeze Record + §2 Metadata（`ziwei:behavior:v1.0.0`） |
| 6 | 变更须 ACP 显式声明 | ✅ | 契约性质段 + §1 Change procedure + §6 Change Procedure |
| 7 | 解释层显式排除 | ✅ | 契约 §4（格局/四化/大限/流年/LLM/RAG/Consensus/真太阳时） |
| 8 | 跨域差异（ZB-01, ZB-06, ZQ-02）显式登记 | ✅ | 契约 §5 + `ZIWEI_CROSS_DOMAIN_BOUNDARIES.md`（ZB-01/ZB-06/ZQ-02/D13） |

**结论: 8/8 PASS → Contract → Vectors → Reference → Certification 闭环无矛盾。**

---

## 4. Schema 与登记勘误（本 Sprint 完成）

| # | 位置 | 勘误 | 说明 |
|---|------|------|------|
| S-1 | `docs/SCHEMAS.md` §3.2 头部 | "未注册契约 / Implemented / v0.2.0" → **契约登记 `ziwei:behavior:v1.0.0` Frozen / v0.3.0** | 状态登记更新（纯文档, 无行为变化） |
| S-2 | `docs/SCHEMAS.md` §3.2 `wuxing_ju` 注释 | "例如 水二局" → **"例如 水2局"（BC-009 规范格式 `{元素}{数}局`）** | 与契约格式一致（Phase 6.7.2 报告 E-2 的落地勘误） |

Schema 结构本身与 BC-013 一致（calendar_note 位于 ZiweiChart; `extra="forbid"`;
字段集逐一对齐）——**未修改任何 Schema 行为**。

---

## 5. 当前 Scope 显式声明（不含以下能力）

- 辅星/杂曜/四化/大限/流年（ZW-017 边界, 新增须 ACP）
- 格局分析（Pattern analysis, 解释域 A-8）
- 解释 / 叙述 / 推荐 / Narrative 生成
- LLM reasoning / RAG / Consensus 集成
- Knowledge Layer 语料建设

以上属未来授权 Sprint。Ziwei 域仅产生**确定性观测结果**
（命/身宫/五行局/十二宫/十四主星/阴阳标记）。

---

## 6. Known Limitations

| 项 | 说明 |
|----|------|
| 农历精度 | 依赖 sxtwl==2.0.7 输出（精确 pin, ACP-ZW-004; 历法数值向量 ZV-lun-001~005 锁定） |
| 真太阳时 | 不采用（跨域差异声明, 契约 §5） |
| 时区回退 | 静默两级链（无 UTC 兜底, A-4 FROZEN; ZV-tz-003 锁定） |
| 等价覆盖 | 24 向量（engine 0.3.0 / rule_set 0.3.0） |
| 文档勘误历史 | E-1（readiness ZV-ref-002 局名标注, FREEZE_REVIEW §3）; S-1/S-2（本 Sprint）—— 均不影响契约/向量/Reference 一致性 |
