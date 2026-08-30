# Phase 4 — CAO Decision: R4 Admission after CHAR002 Gap Disposition

> **Decision ID**: CAO-P4-R4ADM-001
> **Decision Date**: 2026-08-30
> **决策性质**: R4 **准入**裁决（Admission）—— `CAO Decision ≠ R4 Execution Authorization`
> **分支**: `work/phase4/char-001-execution`（本决策零 live 操作, 零代码/配置修改）

---

## 3. Evidence Basis（Task 1 — 证据状态重构, 全部基于仓库既有文档）

| 项 | 状态 | 凭证 |
|----|------|------|
| CHAR001 Evidence Review | **EVIDENCE REJECTED**（针对当时不存在的证据集） | `dd29b48` |
| char-001 实际执行（后于该审查） | ABORTED_AUTH_OR_BILLING（HTTP 402, 1 请求, 协议中止） | `d9dcdf5`（产物+报告入库） |
| CHAR002 Evidence Review | **EVIDENCE ACCEPTED WITH GAPS** | `dc37bcb` |
| CHAR002 Gap Disposition | E1=UNRESOLVABLE / E2=UNOBSERVABLE / E3=CLOSED | `8c37c1a` |
| R4 锁定条件（冻结原文, 协议 §7） | 见下 | `INFRASTRUCTURE_CHARACTERIZATION_PROTOCOL.md` §7 |

**协议 §7 原文必录**:

```text
This protocol is a prerequisite for R4, not a substitute.
R4 will only be authorized after:
- Protocol is approved
- Characterization runs are completed
- Stability threshold is observed
```

「Stability threshold is observed」定义（协议原文）: 在冻结标准下, **至少一个密度档位
同时满足 S1–S3（及 D 已触发时的 S4）**, 并由人工 Evidence Review 确认。

**三条件逐项核对（Task 1 结论）**:

| §7 条件 | 核对 | 结果 |
|---------|------|------|
| Protocol is approved | 阈值 2026-08-25 人工冻结（实现内注释 + 治理登记）; 协议批准在案 | ✅ |
| Characterization runs are completed | char-002 完整执行冻结矩阵 A→B→C→D（240 请求, 产物齐备, `c175a9f`） | ✅ |
| Stability threshold is observed | 冻结判定式输出: **A 档位 S1–S3 同时 PASS, B 档位 S1–S3 同时 PASS**（≥1 档位即满足; S4 仅"D 已触发时"适用——本次 D 恢复流未触发, 条件分支不适用）; 人工 Evidence Review 已确认（`dc37bcb`） | ✅ |

**四概念区分（强制）**: Observed Evidence（240/240 成功、A/B S1–S3 PASS）≠ Evidence
Gap（E1/E2）≠ Causal Explanation（未授权）≠ Engineering Readiness（本决策仅裁准入,
不担保未来运行表现）。

## 4. CHAR001 Disposition

- 初始 Evidence Review = **REJECTED**（审查时证据集不存在——程序性否决, 与后续执行无矛盾）。
- 其后真实执行（授权窗口内）产生**中止事件证据**: HTTP 402 'Insufficient Balance'
  （原始报文已登记）, 协议中止路径正确, 产物完整入库。
- 定位: **计费阻塞事件证据**, 非表征数据; GAP-E3 已 CLOSED; 不得与 char-002 合并。

## 5. CHAR002 Disposition

**ACCEPTED WITH GAPS** — 作为 deepseek-v4-flash judge path 的密度档位表征 baseline
（A/B 判定档 + C 观察档 + D 持续压力档）, 完整、可信、可追溯。保留事实性结论仅限
CAO Decision §五所列 OBSERVED FACTS。

## 6. GAP-E1 Disposition — 充分性裁定

```text
GAP-E1 = UNRESOLVABLE / SUBJECT UNAVAILABLE —— 予以接受, 作为登记在案的
         R4 admission limitation（非 blocker）。
```

裁定理由:

1. 协议 §7 三项准入条件**主体无关**（未要求特定模型名）; 以 GAP-E1 为硬性 blocker
   将是在冻结准入标准之外追加新条件。
2. 原主体 `deepseek-chat` 不可用（模型目录观察, 2026-08-30, 一次性 GET /models:
   仅 v4-flash / v4-flash-vision-exp / v4-pro）——**R4 未来执行同样无法使用
   deepseek-chat**。要求对已不可获得的主体做表征, 在逻辑上不构成 R4 的前置。
3. char-002 的主体（deepseek-v4-flash）正是 R4 当前配置下**唯一可行主体**——
   表征 baseline 与 R4 可执行主体一致, 恰好满足"前置可行性输入"的本义。
4. 遵守: **NO MODEL SUBSTITUTION**（不为凑齐主体而改用其他模型表征）/ **NO
   SIMULATION** / **NO INFERENCE**（不推断 chat 下线原因）/ **NO BACKFILL**
   （不用 v4-flash 数据回填 chat 口径）。
5. **附加准入条件（约束性）**: R4 执行必须使用**已表征主体**
   （`deepseek-v4-flash` @ `https://api.deepseek.com`）; 若执行前模型/endpoint
   发生任何变更, 本准入失效, 须重新表征并重新申请准入。

## 7. GAP-E2 Disposition — 充分性裁定

```text
GAP-E2 = UNOBSERVABLE UNDER CURRENT CHARACTERIZATION —— 予以接受, 作为登记在案的
         R4 admission limitation（非 blocker）。
```

裁定理由:

1. 协议对 Stability 的定义中 **S4 为条件项**（"及 D 已触发时的 S4"）——D 恢复流
   未触发时, S4 不构成准入要件; 冻结文本未将恢复观测设为无条件前置。
2. `NOT TRIGGERED ≠ SUCCESSFUL RECOVERY`（重申）——不得解释为恢复成功、系统无需
   恢复、或恢复能力已验证。其唯一含义: 观测期内冻结触发条件未满足。
3. 零失败环境下恢复路径**结构性不可观测**; 当前表征已达到冻结协议定义下的
   **最大合法观测范围**（无失败即无恢复入口; 故障注入被禁止——协议无注入机制,
   注入即 probe/protocol 变更 + 人为制造未授权故障）。
4. 不需要故障注入、不允许人为制造失败、不需要为 R4 强行填补恢复数据。

## 8. GAP-E3 Disposition

**CLOSED**（确认, 不重开）: 完整矩阵 baseline 由 char-002 独立满足; char-001
原样保留为阻塞事件证据; 数据不合并; 不重新设计 char-001。

## 9. R4 Admission Decision（Task 3）

```text
R4 = APPROVED (ADMISSION ONLY)
```

- 选择 Option A。Option B（维持 LOCK）要求"明确、可验证、当前协议要求的 blocker"
  ——协议 §7 冻结准入条件三项全部满足, 两个 GAP 均不在冻结准入要件之内, 以 GAP
  为由维持锁等于在冻结标准之外追加准入门。Option C（要求新表征）同样不成立:
  不存在未满足的冻结准入证据项; 为"样本量/成功率/完整性"追加 run 属被禁止的
  speculative 要求。
- **含义**: 接受 CHAR002 为当前 characterization evidence baseline; 接受 GAP-E1/E2
  为**明确登记的 evidence limitations**, 不作为准入 blocker; R4 可进入下一阶段
  （执行授权评审）。**任何 R4 结果不得声称解决 E1/E2。**

**准入附带条件（约束性, 对 R4 执行授权阶段生效）**:

1. R4 执行主体 = `deepseek-v4-flash` @ `https://api.deepseek.com`（已表征主体）;
   主体/端点变更 → 本准入失效 → 重新表征 + 重新准入。
2. R4 执行授权须为**独立 CAO 决策**（含执行窗口、运行配置、端点/模型逐请求落盘
   要求——消除 R2/R3"运行期端点 UNKNOWN"缺口在设计层面的复发）。
3. R4 执行前如出现任何新的失败证据或提供方目录变化, 本准入自动暂停重审。

## 10. Explicit Non-claims（禁止扩展）

CHAR002 的 240/240、A passed、B passed、C 60/60、D 120/120 **不得**被解释为:
无限流 / 无容量问题 / 系统稳定 / 具备任何 SLA / 历史故障另有根因 / 提供方基础设施
健康 / 恢复能力已验证。以上均为**未授权结论**; Observed Evidence ≠ Causal
Explanation ≠ Engineering Readiness。

## 11. Reopening Conditions

- GAP-E1: 提供方目录（经授权核验）重新列出 deepseek-chat 且 CAO 批准原主体表征提案。
- GAP-E2: 未来授权 run 出现真实失败（自动积累 S4）, 或 CAO 批准受控恢复表征新协议。
- R4 准入: 主体/端点变更; 新失败证据; 提供方目录变化; CAO 裁量。

## 12. Phase 4.3 Status

**LOCKED unless separately authorized.** R4 准入不自动传导至 4.3。

## 13. Knowledge Layer Status

**LOCKED。** 本决策与 Knowledge Layer / 7.2B 无关, 不构成任何解锁。

## 14. Authorization Boundaries

```text
CAO Decision ≠ R4 Execution Authorization
R4 Execution:           NOT AUTHORIZED（须独立执行授权: 窗口/配置/计划）
New Live Characterization: NOT AUTHORIZED（含 /models 复核）
O-1 char-003-replication: OPTIONAL / FUTURE / REQUIRES NEW CAO AUTHORIZATION
probe / protocol / thresholds / historical artifacts: UNCHANGED
本决策允许的产出: 本文档 + 归档更新, 别无其他
```

## 15. Integrity Verification（Task 5, 离线）

- `git status` / `git diff`: 本决策仅新增本文档 + 归档条目; probe/protocol/threshold/
  artifacts 零改动（提交后复核）。
- 治理文档一致性: 三份在位（`dd29b48` / `dc37bcb` / `8c37c1a`）; 协议 §7 原文
  与本决策引用逐字一致。
- 测试: 纯文档变更, 不触及 Python 源; 无需运行（如需可离线 selftest, 零网络）。

## STOP CONDITION

```text
CAO Decision:
    APPROVED (R4 ADMISSION ONLY)

GAP-E1:
    UNRESOLVABLE / SUBJECT UNAVAILABLE（登记为 admission limitation）

GAP-E2:
    UNOBSERVABLE UNDER CURRENT CHARACTERIZATION（登记为 admission limitation）

GAP-E3:
    CLOSED

R4:
    APPROVED (ADMISSION) — EXECUTION NOT AUTHORIZED

Phase 4.3:
    LOCKED

Knowledge:
    LOCKED

Live Requests:
    ZERO

STOP
```

等待下一条 **R4 Execution Authorization**（独立决策）。本准入不自动触发任何执行。
