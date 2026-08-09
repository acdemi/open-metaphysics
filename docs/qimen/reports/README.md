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
| [PHASE5_7_DELIVERY_REPORT.md](PHASE5_7_DELIVERY_REPORT.md) | Phase 5.7 | Reference Qimen Domain 建模（纯文档层） | 2026-08-09 |
| [PHASE5_8_DELIVERY_REPORT.md](PHASE5_8_DELIVERY_REPORT.md) | Phase 5.8 | Contract Adapter 包（契约清单层，测试后补） | 2026-08-09 |
| [PHASE5_8A_DELIVERY_REPORT.md](PHASE5_8A_DELIVERY_REPORT.md) | Phase 5.8A | 契约 Schema 提取（机器可读定义层） | 2026-08-09 |
| [PHASE5_8B_DELIVERY_REPORT.md](PHASE5_8B_DELIVERY_REPORT.md) | Phase 5.8B | Runtime Adapter Interface（domain 层） | 2026-08-09 |
| [PHASE5_8C_DELIVERY_REPORT.md](PHASE5_8C_DELIVERY_REPORT.md) | Phase 5.8C | Golden Vector 机器回归（24/24 防护网 + E014） | 2026-08-09 |
| [PHASE5_9A_DELIVERY_REPORT.md](PHASE5_9A_DELIVERY_REPORT.md) | Phase 5.9A | Runtime 类型边界（TypedDict + ABI snapshot） | 2026-08-09 |
| [PHASE5_9B_DELIVERY_REPORT.md](PHASE5_9B_DELIVERY_REPORT.md) | Phase 5.9B | **Reference Qimen Domain 实现**（24/24 向量一致, E015）+ 5.8 测试补齐 + 文档刷新 | 2026-08-09 |
| [PHASE5_7_ALIGNMENT_DELIVERY_REPORT.md](PHASE5_7_ALIGNMENT_DELIVERY_REPORT.md) | Phase 5.7 对齐 | **Reference ↔ 契约最终对齐**（自包含化 + 14/14 QC 审计 + 30/30 等价 + 认证, E016/E017） | 2026-08-09 |

## 相关产物索引

| 产物 | 位置 |
|------|------|
| **正式冻结契约** | `docs/specification/QIMEN_BEHAVIOR_CONTRACT.md`（v1.0.0, Frozen） |
| 契约机器 Schema | `docs/specification/qimen_contract.schema.json`（+ x-contract 提取） |
| 算法假设明细 | `docs/qimen/QIMEN_ALGORITHM_ASSUMPTIONS.md` |
| 规则裁定记录 | `docs/qimen/QIMEN_RULE_DECISION.md` |
| D2 影响分析 | `docs/qimen/QIMEN_D2_IMPACT_ANALYSIS.md` |
| Freeze 评审 | `docs/qimen/QIMEN_FREEZE_REVIEW.md` |
| 冻结缺口（已关闭） | `docs/qimen/QIMEN_FREEZE_GAP.md` |
| Golden Vectors（24, normative fixtures） | `docs/qimen/golden_vectors.json` |
| ABI 快照 | `docs/qimen/qimen_abi_snapshot.json` |
| 契约清单适配层 | `src/openmetaphysics/contracts/` |
| Runtime Adapter | `src/openmetaphysics/domain/qimen/adapter.py` |
| 类型边界 + ABI | `src/openmetaphysics/domain/qimen/types.py` / `structural.py` / `abi.py` |
| Reference Qimen Domain | `reference/qimen/` |
| 测试 | `tests/test_qimen*.py`（regression / contract / adapter / abi / reference_docs） |
