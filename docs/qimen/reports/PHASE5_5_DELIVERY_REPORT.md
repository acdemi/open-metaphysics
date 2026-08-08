# Phase 5.5 — Qimen Behavior Contract Preparation 交付报告（存档）

> **归档日期**: 2026-08-09
> **原始场景**: Specification Preparation
> **状态**: 已交付（正式冻结见 Phase 5.6 存档）

---

## 1. Executive Summary

契约准备完成：新建契约草稿 `QIMEN_BEHAVIOR_CONTRACT_DRAFT.md`（QC-001~QC-014 共 14 条款，**Draft 未冻结**）、冻结缺口记录 `QIMEN_FREEZE_GAP.md`、新增 3 个缺口向量（春分/秋分/晚子时）→ 向量集 21→**24**（原 21 逐字节未变）。核心算法零修改，404 tests passing。

## 2. Contract Draft Structure

`docs/qimen/QIMEN_BEHAVIOR_CONTRACT_DRAFT.md`：
- **Contract Metadata**：version 0.1.0-draft / status Draft / engine_version 0.3.0 / rule_set 0.3.0 / frozen D1,D3-D13 / deferred D2,D14 / 关联文档
- **14 条款** + Golden Vector 映射表 + Non-Goals 声明

## 3. Contract IDs

| ID | 条款 | 规则源 | ID | 条款 | 规则源 |
|----|------|--------|----|------|--------|
| QC-001 | Deterministic Output | 引擎契约 | QC-008 | Zhi Shi | D7/D12 |
| QC-002 | Nine Palace Completeness | Schema | QC-009 | Nine Stars | D8 |
| QC-003 | Dun Type | D1 | QC-010 | Eight Doors | D9 |
| QC-004 | Ju Calculation | D3 + **⚠D2 Deferred dep** | QC-011 | Eight Gods | D10 |
| QC-005 | Earth Plate | D4 | QC-012 | Three Qi | 天盘语义 |
| QC-006 | Heaven Plate | D5/D6 | QC-013 | Void Palace | D11 |
| QC-007 | Zhi Fu | D5/D10/D12 | QC-014 | Central Palace | D12 |

QC-004 显式标注 **"Deferred rule dependency"（非 Frozen）**。

## 4. Golden Vector Mapping（节选）

- QC-003: G1/G2/G3、Y_ju1、Y_ju7、B_summer_before/after、B_lichun_before/after
- QC-007: G1/G2/G3、Z_yin2、Z_yin5、Y_ju5、N_qiufen（天禽为值符星）
- QC-008: G1、G3、Y_ju1、Z_yin5（含值使落中宫寄坤）
- QC-014: G3、Y_ju1、Z_yin2、Z_yin5、Y_ju5、N_qiufen
- 全表见草稿 §3（14 条款 × 向量，完整映射）

## 5. Freeze Gap Summary（`QIMEN_FREEZE_GAP.md`）

| Gap | 内容 | 状态 |
|-----|------|------|
| 1 | **D2 政策裁定**（批准日号近似为规范 or 真拆补法）— 影响全部 24 向量 | **Blocking**（QC-004 冻结前提） |
| 2 | D14 晚子时行为裁定（不换日）— 向量已补齐 | Non-blocking |
| 3 | 覆盖缺口（春分/秋分/晚子时向量） | ✅ **已关闭** |
| 4 | ACP 批准契约文本 + 按需版本流程 | **Blocking**（流程性） |

## 6. Added Vectors（+3，原 21 未动）

| 向量 | 输入 | 要点 |
|------|------|------|
| N_chunfen | 2024-03-20 12:00 北京 | 春分，阳遁 1 局（癸未日戊午时甲寅旬） |
| N_qiufen | 2024-09-23 12:00 北京 | 秋分，阴遁 4 局（庚寅日壬午时甲戌旬，旬首在中宫→值符星天禽） |
| N_late_zishi | 2024-05-15 23:30 北京 | 晚子时（23:30→子时），日号 15 不换日（D14 行为记录） |

均经 plan↔board 一致性断言（值符宫天盘干=旬首仪、值使门落宫、条件专项）与人工核算。

## 7. Modified Files

| 文件 | 变更 |
|------|------|
| `docs/qimen/QIMEN_BEHAVIOR_CONTRACT_DRAFT.md` | **新增** — 契约草稿（14 条款 + 映射） |
| `docs/qimen/QIMEN_FREEZE_GAP.md` | **新增** — 冻结缺口记录 |
| `docs/qimen/golden_vectors.json` | 21 → 24（追加 3，原 21 逐字节不变，已断言） |
| `tests/test_qimen.py` | `test_golden_vector_count` 扩展（chunfen/qiufen/late_zishi 标签 + 不换日断言） |
| `src/openmetaphysics/agents/qimen.py` | **零修改** |

## 8. Test Results

```
ruff check            ✅ All checks passed
ruff format --check   ✅ 68 files already formatted
pytest                ✅ 404 passed (21.1s)
现有 21 向量          ✅ 逐字节未变
新增 3 向量           ✅ 通过全量 golden 测试 (full-board/metadata/determinism/serialization)
契约映射              ✅ QC-001~014 × 24 向量完整
```

## 9. Recommendation: **B. Need additional rule decision**

剩余阻塞均非实现缺口，而是**政策裁定**：
1. **D2 政策决策**（必需）：批准"日号近似"为规范行为（零成本、QC-004 直接冻结）或裁定真拆补法（ACP + 24 向量迁移）—— 本 Sprint 按约束未解决
2. **D14 行为确认**：向量已就位，确认"不换日"即可关闭 Gap 2
3. 完成后即满足 **A. Proceed to final Freeze** 条件（ACP 批准契约 0.1.0-draft → 正式）

**建议下一步**：用户在 D2/D14 上作出政策裁定 → 批准后进入正式冻结 Sprint。

## Governance Compliance

```
qimen 算法 未修改 ✅   Frozen Rules 未修改 ✅   D2 未解决 ✅
最终 Behavior Contract 未创建（仅 Draft）✅   reference/ specification/ schema 未修改 ✅
无解释层/RAG/Consensus ✅   其他 Agent 未修改 ✅
```
