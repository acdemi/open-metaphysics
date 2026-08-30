# Phase 4 — Evidence Review (char-001 & char-002 Evidence Set)

> **文档类型**: 治理审查记录（Evidence Review Sprint —— 只读审计）
> **审查时点 UTC**: 2026-08-30（char-002 完成后, 窗口 07:53Z..09:53Z 内）
> **分支**: `work/phase4/char-001-execution`（HEAD `c91fc81`）
> **证据集**: char-001（中止事件, `d9dcdf5`）+ char-002（完整矩阵, `c175a9f`）
> **执行报告**: `CHAR001_LIVE_EXECUTION_REPORT.md` / `CHAR002_LIVE_EXECUTION_REPORT.md`
> **协议依据**: `INFRASTRUCTURE_CHARACTERIZATION_PROTOCOL.md` + 冻结实现 `scripts/infra_probe.py`

---

## 1. Decision

```text
EVIDENCE ACCEPTED WITH GAPS
```

裁决依据（摘要, 详见 §6）: 两 run 的产物完整性、执行层协议符合性、记录纪律全部
核实通过; 但证据集存在三项已登记缺口——**表征主体变更**（CAO 授权的模型替换）、
**恢复路径证据结构性缺失**（零失败所致）、**char-001 零矩阵样本**。本裁决不批准
R4; R4 授权须独立 CAO Decision。

## 2. Task 1 — Artifact Integrity

### char-001（中止事件, HEAD `d9dcdf5` 入库）

| 项 | 结果 |
|----|------|
| 三产物存在/非空/可解析 | ✅（3418/691/921 bytes） |
| run_id 一致（manifest/records/results） | ✅ `char-001` |
| 时间戳在授权窗口 | ✅（07:54:39–49Z ⊂ 07:53Z..09:53Z 第一代执行窗） |
| records 数 == manifest requests_total | ✅ 1 == 1 |
| SHA-256 登记 | ✅（执行报告 §8） |
| 人工补写/伪造迹象 | 无（probe 原样写盘; `final_status: ABORTED_AUTH_OR_BILLING` 与唯一记录的 402 一致） |

### char-002（完整矩阵, HEAD `c175a9f` 入库）

| 项 | 结果 |
|----|------|
| 三产物存在/非空/可解析 | ✅（3444/133522/1836 bytes） |
| run_id 一致 | ✅ `char-002` |
| 时间戳在授权窗口 | ✅ 首请求 08:05:55Z / 末请求 08:37:20Z ⊂ 07:53Z..09:53Z |
| records 数 == manifest == 冻结矩阵 | ✅ 240 == 240 == 20+40+60+120 |
| manifest↔records↔results 交叉验证 | ✅（条件分布 A20/B40/C60/D120 与各 summary 一致） |
| SHA-256 登记 | ✅（char-002 执行报告 §8） |
| 人工补写/伪造迹象 | 无（逐行 `result=="success"` 与 results 汇总机械一致; 无事后编辑痕迹） |

## 3. Task 2 — Protocol Conformance（char-002 为主对象）

| 协议条目 | 核验结果 |
|----------|----------|
| §1 request record（17 字段） | ✅ 抽样全字段在位（request_id/run_id/condition_id/起止时间戳/base_url/model/judge_mode/result/异常三要素/elapsed/inter_request_interval/滚动窗口×3/累计序号/连败计数） |
| §2 configuration | ⚠️ **登记偏离一处**: model 由 `deepseek-chat` → `deepseek-v4-flash`（CAO 2026-08-30 明确指定, 提交 `f73b303`, G2 快照逐字记录）; endpoint/temperature/response_format/阈值未动 |
| §3 execution window | ✅ 启动守门通过; 240/240 请求在窗内 |
| §4 condition execution | ✅ A→B→C→D 顺序完整; 间隔纪律实测: A 29.99–30.01s, B 4.99–5.01s, C 0.99–2.33s, D 0.99–1.86s（时延挤占间隔语义, 符合冻结实现） |
| §5 C detection | ✅ C 60 请求零失败 → clean 分支; 无 stop-rule 触发 |
| §6 recovery | ✅ 按协议正确**未进入**（零失败 → 无恢复观测入口; D1/D2 NOT_TRIGGERED 为符合性结果而非缺陷） |
| §7 D branch | ✅ C clean → SUSTAINED_STRESS_C_DENSITY（120×1s, probes_sent=120） |
| no retry / no backoff | ✅（240 请求 + 3×Q0 静默, 无额外请求; 快速失败路径亦未出现） |
| no out-of-window request | ✅ |
| result 判定式 | ✅ 240 行 `judge_mode=="deepseek"` 且 JSON 解析成功 ≡ success（分组计数 240:0） |

char-001 符合性: 执行层全部符合（启动守门/单请求/协议中止路径/零 retry）;
详见其执行报告。

## 4. Task 3 — Evidence Classification（仅观察事实）

| 项 | 分类 |
|----|------|
| char-002 A: 20/20 success, S1/S2/S3 = PASS（冻结判定式输出） | **OBSERVED** |
| char-002 B: 40/40 success, S1/S2/S3 = PASS | **OBSERVED** |
| char-002 C: 60/60 success（观察档, NOT_APPLIED_OBSERVATIONAL） | **OBSERVED** |
| char-002 D: SUSTAINED_STRESS_C_DENSITY 120/120 | **OBSERVED** |
| char-002 失败/异常记录 | **NOT OBSERVED**（0/240） |
| char-002 RECOVERY_FLOW / D1 / D2 / S4 | **NOT TRIGGERED**（零失败的结构性结果） |
| char-002 N=5 停止规则 / 双连停 / 计费中止 | **NOT TRIGGERED** |
| char-001 表征矩阵数据 | **NOT OBSERVED**（1 请求即中止, 零矩阵样本） |
| char-001 HTTP 402（'Insufficient Balance' 原文） | **OBSERVED**（计费阻塞事件证据） |
| 表征主体 = deepseek-v4-flash judge path | **OBSERVED**（G2 快照 + 240 行记录逐条 model 字段） |
| deepseek-chat 路径的表征数据 | **NOT OBSERVED**（本证据集不含） |
| 根因 / rate limiting / capacity / provider policy | **不做任何表述** |

## 5. Task 4 — Anomaly Review

**char-002**: 零异常（无失败记录、无异常条目、无 stop-rule、无窗外请求、无间隔
越界）。无可审异常对象。

**char-001**: 唯一异常已在其执行报告中逐要素登记（HTTP 402 'Insufficient Balance',
APIStatusError, cause=null, 触发协议全局中止; 记录位置 `records.jsonl` 行 1）。
本次审查复核确认: 该异常**按冻结协议处置正确**（认证/计费类 → 全局中止, 无 retry）,
处置本身不构成缺陷。

超出协议的因果推断: 无。

## 6. Task 5 — Decision Rationale

**为什么不是 EVIDENCE ACCEPTED（无保留）**: 三项缺口使其不满足"完整无保留"标准——

- **GAP-E1（主体变更）**: 表征对象由 deepseek-chat（历史事件 R/R2/R3 的 judge path）
  变更为 deepseek-v4-flash（CAO 指定）。因此本证据集**不回答**原协议针对
  deepseek-chat 路径的表征问题; 两者不构成同主体可比序列。
- **GAP-E2（恢复路径缺失）**: 240/240 成功 → 协议 §6 恢复观测与 S4（recovery ≤ Z）
  在本次运行中**结构性不可观测**（无失败即无恢复）。恢复路径的表征证据仍然空缺。
- **GAP-E3（char-001 零样本）**: char-001 未产出任何矩阵数据（仅登记 402 阻塞事件）。

**为什么不是 EVIDENCE REJECTED**: 产物完整性、执行层符合性、记录纪律、窗口纪律、
判定式一致性全部核实通过; 缺口均为**已登记、可解释、有治理授权链**的偏差
（GAP-E1 有明确 CAO 决策; GAP-E2/GAP-E3 为客观运行结果, 非执行缺陷）。

**结论**: 证据集作为"deepseek-v4-flash judge path 的密度档位表征（含持续压力档）"
是完整、可信、可追溯的; 作为"原始事件主体（deepseek-chat）的表征"与"恢复路径
表征"则存在登记缺口。→ **EVIDENCE ACCEPTED WITH GAPS**。

## 7. Explicit Statement

```text
No causal, rate-limiting, capacity, or root-cause conclusion is made at the
evidence-review stage. S1–S3 PASS states are frozen-formula outputs, not
reviewer interpretations. 100% success rate is an observed fact only.
```

## 8. STOP

```text
Evidence Review:        COMPLETE — EVIDENCE ACCEPTED WITH GAPS
R4:                     LOCKED（进入 R4 须新的 CAO Decision 明确授权, 并说明
                        GAP-E1 主体口径与 GAP-E2 恢复路径缺口的处置）
Phase 4.3:              LOCKED
Knowledge Layer / 7.2B: LOCKED
```

本审查全程零网络请求、零产物修改、零配置变更。
