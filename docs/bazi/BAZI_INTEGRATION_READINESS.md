# BaZi Integration Readiness

> **Sprint**: Phase 6.6 — Integration Readiness Closure（Governance Closure）
> **日期**: 2026-08-09
> **目的**: 审查 BaZi 满足 Integration Ready 的全部条件, 形成治理闭环记录。
> **性质**: 审查文档。不新增能力、不修改冻结工件。

---

## 1. Integration Ready 条件审查

| # | 条件 | 状态 | 证据 |
|---|------|------|------|
| 1 | **Contract Frozen** | ✅ | `docs/bazi/BAZI_BEHAVIOR_CONTRACT.md` **v1.0.0 Frozen**（`bazi:behavior:v1.0.0`, 2026-08-09, BC-001~014） |
| 2 | **Reference Certified** | ✅ | `docs/bazi/BAZI_REFERENCE_CERTIFICATION.md`（14/14 BC 审计 + 独立性审计） |
| 3 | **Golden Vectors Frozen** | ✅ | `docs/bazi/golden_vectors.json` **24 normative fixtures**（`status` 字段语义由冻结契约 BC-014 确立, 不可变） |
| 4 | **Reference Equivalence PASS** | ✅ | `reference/tests/test_bazi_equivalence.py` — **24/24 Production == Reference**, 全结构逐字段相等, 零偏差 |
| 5 | **Schema Registered** | ✅ | `docs/SCHEMAS.md` §3.1 登记（Phase 6.6 Task A, 按冻结契约 BC-013 实际结构） |
| 6 | **Change Policy Registered** | ✅ | 契约 §5 Change Procedure + CAPABILITY_STATUS.md BaZi 变更政策（与 CAPABILITY_LIFECYCLE.md §5 一致, 框架未修改） |
| 7 | **Domain Boundary Explicit** | ✅ | `docs/bazi/BAZI_FREEZE_BOUNDARY.md` + 契约 §4 范围外声明 + ARCHITECTURE.md §1 |

**结论: 7/7 满足 → BaZi 达到 Integration Ready 全部条件。**

---

## 2. Change Policy 正式引用（Task B）

BaZi 冻结工件的变更必须完整执行（与 `CAPABILITY_LIFECYCLE.md` §5 一致,
本 Sprint 未修改框架, 仅为正式引用）:

1. **ACP**（Architecture Change Proposal, 等待人工批准）
2. **Contract version increment**（v1.0.0 → 下一版本, 契约 §5）
3. **Golden Vector migration**（24 向量不可原地修改, 生成新向量集）
4. **Reference re-certification**（`reference/bazi/` 同步更新 + 24/24 等价 + BC 审计重新通过）

引用位置: `BAZI_BEHAVIOR_CONTRACT.md` §5 / `CAPABILITY_STATUS.md` BaZi 节 /
本文件 §2。

---

## 3. 跨域边界登记（与 Qimen 对照, 有意差异）

| # | 维度 | BaZi（已冻结） | Qimen（已冻结） |
|---|------|----------------|-----------------|
| D-01 | 晚子时（23:00-24:00） | **23:00 换日**（BC-004） | **不换日**（D14） |
| D-02 | 真太阳时 | **不使用**（钟表时, BC-005） | **使用**（D13, 有坐标时） |
| D-03 | 节气边界比较 | UTC 时刻 | UTC 判定（机制一致） |
| D-04 | 时区回退 | 静默回退 born_at.tzinfo → UTC（BC-012） | —（域输入无此路径） |

> 依据: `docs/bazi/BAZI_CROSS_DOMAIN_BOUNDARIES.md`（冻结登记表）。

---

## 4. 当前 Scope 显式声明（不含以下能力）

- 格局分析（Pattern analysis）
- 用神（Useful God）
- 流年解释（Annual fortune interpretation）
- 大运解释 / 吉凶（Fortune judgement）
- 推荐（Recommendation）
- Narrative 生成
- LLM reasoning
- RAG
- Consensus 集成

以上属未来授权 Sprint（`BAZI_FREEZE_BOUNDARY.md` §2 / 契约 §4）。
BaZi 域仅产生**确定性观测结果**（四柱/十神/藏干/纳音/大运）。

---

## 5. Known Limitations

| 项 | 说明 |
|----|------|
| 节气精度 | Meeus 截断 ~0.01°（<1 分钟）; 立春向量 ±3h 规避临界歧义 |
| 真太阳时 | 不采用（跨域有意差异 D-02） |
| 时区回退 | 静默（无警告, BC-012 测试锁定） |
| 等价覆盖 | 24 向量（engine 0.1.0 / rule_set 0.1.0） |
