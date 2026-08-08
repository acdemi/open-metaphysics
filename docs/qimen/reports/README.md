# Qimen 交付报告存档（Phase 5 系列）

> **说明**: Phase 5 奇门遁甲各 Sprint 的交付报告存档。
> 报告内容与交付时保持一致，仅作归档记录。

| 报告 | 阶段 | 内容 | 日期 |
|------|------|------|------|
| [PHASE5_DELIVERY_REPORT.md](PHASE5_DELIVERY_REPORT.md) | Phase 5 | 时家奇门排盘核心实现（转盘法） | 2026-08-09 |
| [PHASE5_1_DELIVERY_REPORT.md](PHASE5_1_DELIVERY_REPORT.md) | Phase 5.1 | 算法稳定化审查（14 项假设文档化） | 2026-08-09 |
| [PHASE5_2_DELIVERY_REPORT.md](PHASE5_2_DELIVERY_REPORT.md) | Phase 5.2 | 规则裁定（12 Freeze / 2 Deferred） | 2026-08-09 |
| [PHASE5_3_DELIVERY_REPORT.md](PHASE5_3_DELIVERY_REPORT.md) | Phase 5.3 | Golden Vector 扩充（3→21）+ D2 影响分析 | 2026-08-09 |
| [PHASE5_4_DELIVERY_REPORT.md](PHASE5_4_DELIVERY_REPORT.md) | Phase 5.4 | Freeze Candidate Review（PASS WITH CONDITIONS） | 2026-08-09 |
| [PHASE5_5_DELIVERY_REPORT.md](PHASE5_5_DELIVERY_REPORT.md) | Phase 5.5 | 契约准备（草稿 QC-001~014 + 缺口向量 21→24） | 2026-08-09 |
| [PHASE5_6_DELIVERY_REPORT.md](PHASE5_6_DELIVERY_REPORT.md) | Phase 5.6 | **契约正式冻结 v1.0.0**（D2/D14 裁定 + 向量提升） | 2026-08-09 |

## 相关产物索引

| 产物 | 位置 |
|------|------|
| **正式冻结契约** | `docs/specification/QIMEN_BEHAVIOR_CONTRACT.md`（v1.0.0, Frozen） |
| 算法假设明细 | `docs/qimen/QIMEN_ALGORITHM_ASSUMPTIONS.md` |
| 规则裁定记录 | `docs/qimen/QIMEN_RULE_DECISION.md` |
| D2 影响分析 | `docs/qimen/QIMEN_D2_IMPACT_ANALYSIS.md` |
| Freeze 评审 | `docs/qimen/QIMEN_FREEZE_REVIEW.md` |
| 冻结缺口（已关闭） | `docs/qimen/QIMEN_FREEZE_GAP.md` |
| Golden Vectors（24, normative fixtures） | `docs/qimen/golden_vectors.json` |
| 契约校验测试 | `tests/test_qimen_contract.py` |
| 排盘测试 | `tests/test_qimen.py`（33 测试） |
