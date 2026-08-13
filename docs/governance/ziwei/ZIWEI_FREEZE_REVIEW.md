# Ziwei Freeze Review

> **Sprint**: Phase 6.7.3 — Freeze Review & Gate Decision
> **日期**: 2026-08-13
> **性质**: 证据审查 Sprint。不生成代码、不创建 Contract 正式版、不推进 Reference。
> **输入工件**: ZIWEI_RULE_DECISION / ZIWEI_ALGORITHM_ASSUMPTIONS /
> ZIWEI_DECISION_RESOLUTION / golden_vectors.json（24, v0.3.0）/
> test_ziwei_golden_vectors.py（7）/ test_ziwei.py（33）/ Engine v0.3.0

---

## 1. Golden Vector Evidence Review

| # | 审查项 | 证据 | 结果 |
|---|--------|------|------|
| 1 | 24 向量全部基于 Engine v0.3.0 生成 | `golden_vectors.json` metadata `engine_version=0.3.0`；逐向量 `expected.metadata`；`test_engine_version`（断言 == `ZiweiEngine.version` == 0.3.0） | ✅ PASS |
| 2 | 17/17 ZW 规则全部覆盖 | `test_rule_coverage_complete`：union(rule_coverage) ⊇ ZW-001~017，无缺漏（映射表见 §4） | ✅ PASS |
| 3 | A-1 定局生成式：5 局全类型 + 边界 1/30 | 独立脚本重算 `(START[ju]+(day-1)//STEP[ju])%12` == Engine 紫微位置：ju-001~005（5 局）+ pos-001（day1）/pos-002（day30）/pos-003（局间）/pos-004（覆盖路径）/inv-001（day23）全部一致 | ✅ PASS |
| 4 | A-2 廉贞 -8：子/午紫微恒等式 | 6 个紫微在子(10)/午(4) 向量（ju-004, hour-001/002, lun-004/005, inv-001）全部满足"紫微在子→廉贞天府同度辰；在午→同度戌"（`(-zw)%12` 镜像 + `(zw-8)%12` 双核对） | ✅ PASS |
| 5 | Determinism：双重运行逐字节一致 | `test_determinism`：24 向量双重 `engine.calculate()` 输出相等且 == expected | ✅ PASS |
| 6 | 序列化稳定性 | `test_serialization_stable`：sort_keys 规范化 dump 与文件字节一致 + 二次 dump 稳定 | ✅ PASS |

**结论**: **PASS** —— 无缺失项。向量为规范性证据（Engine 输出生成，无人工篡改，
生成方法见 `ZIWEI_GOLDEN_VECTOR_REPORT.md` §9）。

---

## 2. Boundary Decision Review

### A-3 晚子时（23:00 不换日）→ **FROZEN**

- **当前行为**: 农历日 = 本地民用日期（sxtwl）；23:00 后不换日（Engine 无换日逻辑）。
- **证据**: ZV-hour-001（22:59 亥时）、ZV-hour-002（23:00 子时, 命宫差 1 且同日）、
  ZV-lun-005（23:30 子时, 与 2024-06-06 同日）。
- **跨域**: 与 **Qimen D14 不换日一致**（ZQ-02, 巧合一致）；与 **BaZi BC-004
  23:00 换日真实差异**（ZB-01, 已登记）。
- **理由**: 行为确定性已被 3 个向量锁定；流派变体（子初/子正换日）在本项目
  规范定义为**不换日**（与 Qimen 对齐, 跨域差异显式声明）。歧义 A-3 关闭,
  转为显式规范条款（契约草案 BC-005）。

### A-4 时区回退链（非法时区静默回退）→ **FROZEN**

- **当前行为**: `born_location.tz → born_at.tzinfo` 两级链, **无 UTC 兜底**, 静默。
- **证据**: ZV-tz-003（tz="Invalid/Zone"）与 ZV-tz-001（无 location）输出**逐字节一致**。
- **跨域**: 与 BaZi BC-012 三级链（含 UTC 兜底）链定义差异（ZB-06）；因 Ziwei
  `born_at` 强制 tz-aware，两级链与三级链**行为等价**。
- **理由**: 行为已被向量锁定（D-ZW-2 确认）；差异已登记 ZB-06。裁定 FROZEN,
  契约草案 BC-003 显式声明。

### A-6 闰月同值安星 → **FROZEN**

- **当前行为**: 闰月与平月使用相同月号安星 + `calendar_note` 记录。
- **证据**: ZV-lun-003（2023-03-22 → 闰二月, `calendar_note="leap month 2 (闰月)
  using month number 2 for placement"`）。
- **理由**: 行为确定性已被向量锁定；流派变体（闰月作下月/上月/专用盘）本项目
  规范定义为**月号同值 + 记录**（D-ZW-4 确认）。歧义 A-6 关闭, 契约草案 BC-005 固化。

### A-7 年干立春界 → **FROZEN**

- **当前行为**: 年干以立春（UTC 时刻）为界, 复用 BaZi 原语（ZW-005, 引用非重复实现）。
- **证据**: ZV-lun-004（2024 立春 16:26 UTC 后 1h 采样 → 年干甲辰, `yin_yang=yang`）。
- **理由**: 行为已被向量锁定；传统紫微"正月初一取年干"变体在本项目显式声明为
  **随 BaZi 立春界**（D-ZW-5 确认）。歧义 A-7 关闭, 契约草案 BC-006 固化。

**汇总**: 4/4 边界裁定完成（全部 FROZEN, 均为显式规范声明 + 向量锁定 +
跨域差异登记引用）。未遗留 DEFERRED 项。

---

## 3. Documentation Errata

| # | 位置 | 标注 | 实际 | 处置 |
|---|------|------|------|------|
| E-1 | `ZIWEI_GOLDEN_VECTOR_READINESS.md` ZV-ref-002（Phase 6.7.1） | "木三局" | **土5局**（1985-08-15 10:00 → 农历 6/29 巳时, 命宫寅, 戊寅城头土 → 土5局；公式链与 Engine v0.3.0 双一致） | **记录于本报告**；Phase 6.7.1 文档按历史保留, 不修改。正式契约以 golden_vectors.json + 契约草案为准 |

> 说明: E-1 为 Phase 6.7.1 文档标注错误, 不影响向量/规则一致性——
> Engine v0.3.0 输出与 ZW-007/009/010 公式链一致, 向量已按正确局名采样。

---

## 4. Rule Finalization Table

| Rule | Status（Freeze Review 后） | Evidence（Golden Vectors） | Notes |
|------|---------------------------|----------------------------|-------|
| ZW-001 | **IMPLEMENTED** | ZV-pos-001~004 | 输入校验（ACP-ZW-003: month∈[1,12], day∈[1,30], 同给同省, ValueError/422） |
| ZW-002 | **FROZEN** | ZV-tz-001~003 | 时区两级链, 静默回退（A-4 裁定） |
| ZW-003 | **FROZEN** | ZV-hour-001, ZV-hour-002, ZV-lun-005 | 钟表时, 子时 23:00~00:59 |
| ZW-004 | **FROZEN** | ZV-lun-001~003, ZV-lun-005 | sxtwl==2.0.7 锁定; 闰月同值 + 记录（A-6）; 不换日（A-3） |
| ZW-005 | **FROZEN** | ZV-lun-004 | 年干立春界, 引用 BaZi 原语（A-7） |
| ZW-006 | **FROZEN** | ZV-ref-001~004 | 五虎遁 |
| ZW-007 | **FROZEN** | ZV-ref-001 | 命宫公式 |
| ZW-008 | **FROZEN** | ZV-ref-001 | 身宫公式 |
| ZW-009 | **FROZEN** | ZV-ref-001 | 命宫天干 |
| ZW-010 | **FROZEN** | ZV-ju-001~005, ZV-ref-001~004 | 五行局（纳音末字映射） |
| ZW-011 | **FROZEN** | ZV-ref-001~004 | 十二宫布局 |
| ZW-012 | **IMPLEMENTED** | ZV-ju-001~005, ZV-pos-001~004, ZV-inv-001 | A-1 定局生成式（ACP-ZW-001） |
| ZW-013 | **FROZEN** | ZV-inv-001（全部向量镜像断言） | 天府镜像 `(-zw)%12` |
| ZW-014 | **IMPLEMENTED** | ZV-inv-001, ZV-lun-004（全部向量廉贞断言） | A-2 廉贞 -8（ACP-ZW-002） |
| ZW-015 | **FROZEN** | ZV-inv-001（全部向量 14 星断言） | 天府星系八星偏移 |
| ZW-016 | **FROZEN** | ZV-ref-002（yin）, ZV-lun-004（yang） | 阴阳标记 |
| ZW-017 | **FROZEN** | ZV-ref-001~003 | 未实现能力边界（aux 恒空, star_placement） |

**状态汇总**: 3 IMPLEMENTED（ACP 修订, 规范定义）+ 14 FROZEN（候选确认）= 17/17。

---

## 5. Freeze Review Verdict

> **PASS** ✅

- 17/17 规则状态明确（3 IMPLEMENTED + 14 FROZEN, 无遗留候选）。
- 24 个 Golden Vectors 证据充分（全部重放通过, A-1/A-2 专项 PASS, 确定性/序列化锁定）。
- 4 项边界裁定全部完成（A-3/A-4/A-6/A-7 → FROZEN, 显式声明）。
- 文档勘误记录（E-1）不阻塞冻结。
- **Contract Candidate 入口条件满足** → 产出契约草案
  `docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT_DRAFT.md`（BC-001~014, 对齐
  Qimen QC-001~014 / BaZi BC-001~014 结构）。

---

## 6. Contract Candidate（本次产出）

- **契约草案**: `docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT_DRAFT.md`
  - contract_id: `ziwei:behavior:0.1.0-draft`
  - 对齐 Qimen QC-001~014 结构与 BaZi BC-001~014 编号
  - 14 条款覆盖 17 条 ZW 规则 + 4 项边界裁定 + 2 项跨域声明（ZB-01/ZB-06）
  - 引用 24 个 Golden Vectors（`docs/ziwei/golden_vectors.json`）
- **状态保持**: CAPABILITY_STATUS.md 中 Ziwei = **Implemented**（Gate 通过后
  升级为 Contract Candidate 由人工决定; 本 Sprint 不升级）。

---

## 7. 验证

| 检查 | 结果 |
|------|------|
| pytest 全量 | ✅ 585/585 全绿（含 7 黄金向量测试 + 33 ziwei 测试） |
| ruff check / format --check | ✅ 通过 |
| git diff -- src/ | ✅ 空 |
| git diff -- docs/qimen/ docs/bazi/ | ✅ 空 |
| git diff -- docs/governance/CAPABILITY_LIFECYCLE.md | ✅ 空 |
| reference/ziwei/ | ✅ 未创建 |
| 新增文件 | `docs/governance/ziwei/ZIWEI_FREEZE_REVIEW.md` + `docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT_DRAFT.md` |

---

## 8. 停止声明

本 Sprint 停止。等待人工 Evidence Review 与授权。
**不自动进入 Phase 6.7.4（Reference Certification）。**
Ziwei 状态保持 **Implemented**（契约草案交付, 升级与否由人工 Gate 决定）。
