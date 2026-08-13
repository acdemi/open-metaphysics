# BaZi Reference Certification

> **认证日期**: 2026-08-09
> **执行**: Phase 6.5 — Contract Freeze & Reference Certification Sprint
> **状态**: **Certified**（Reference Certified, 契约 v1.0.0 Frozen）

---

## 认证内容

| 项 | 值 |
|----|-----|
| **Contract version** | **v1.0.0**（`docs/bazi/BAZI_BEHAVIOR_CONTRACT.md`, Frozen, 2026-08-09） |
| **Reference implementation** | `reference/bazi/`（tables.py / astronomy.py / domain.py, 独立实现, 无 src 导入） |
| **Golden Vector count** | **24 / 24**（`docs/bazi/golden_vectors.json`, normative fixtures） |
| **Equivalence result** | **24/24 Production == Reference**, 全结构逐字段相等（`reference/tests/test_bazi_equivalence.py`, 6 例） |
| **Test result** | 全仓库 **557 passed**（含 Qimen 24/24 向量回归 + 30/30 等价 + BaZi 24/24 回归 + 14 单元 + 11 基础 + 6 等价） |
| **Audit result** | **14/14 BC PASS**（`docs/bazi/BAZI_REFERENCE_AUDIT.md`）; 独立性审计通过（无 openmetaphysics 导入） |
| **Certification date** | 2026-08-09 |

## 认证前置（全部满足）

1. ✅ Contract Frozen（Task A: BC-001~014 四列证据全 ✅ → `bazi:behavior:v1.0.0`）
2. ✅ Reference Audit PASS（Task C: 14/14）
3. ✅ 24/24 Equivalence PASS（Task D: 零偏差, 无 fuzzy / 无字段忽略）
4. ✅ 全量测试 PASS（557, ruff check/format 通过）
5. ✅ Qimen 工件零改动（24/24 向量回归 + 30/30 等价持续通过）

## Known Limitations

| 项 | 说明 |
|----|------|
| 真太阳时不采用 | 钟表时（BC-005, 与 Qimen D13 有意分歧, 见 BAZI_CROSS_DOMAIN_BOUNDARIES.md D-02） |
| 节气精度 | Meeus 截断 ~0.01°（<1 分钟）; 立春 ±3h 向量规避临界歧义 |
| 时区回退静默 | 无效时区静默回退 born_at.tzinfo, 不产生警告（BC-012, 已测试锁定） |
| 契约范围 | 仅确定性排盘; 格局/用神/强弱/流年/解释层显式排除（BAZI_FREEZE_BOUNDARY.md） |
| 等价覆盖 | 24 向量（engine 0.1.0, 规则集 0.1.0）; 未来规则变更须 ACP + 重新认证 |

## 认证声明

Reference BaZi Domain（`reference/bazi/`）作为独立于 Product Runtime 的
契约符合性实现, **通过** Frozen Contract v1.0.0 全部 14 条 BC 条款审计、
24/24 规范向量验收与 24/24 Production == Reference 精确等价证明。
未来任何算法修改必须同时通过 Product + Reference 双重契约验证。

---

*本工件为文本认证记录。*
