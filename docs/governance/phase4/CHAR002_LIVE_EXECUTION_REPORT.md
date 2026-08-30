# Phase 4 — char-002 Live Execution Report

> **文档类型**: 执行报告（characterization execution —— 仅事实登记, 无因果结论）
> **执行时点 UTC**: start `2026-08-30T08:05:55Z` → finish `2026-08-30T08:37:20Z`（wall ≈ 31.4 min）
> **分支**: `work/phase4/char-001-execution`（执行时 HEAD = `f73b303`）
> **产物目录**: `data/characterization/char-002/`
> **前置事件**: char-001（deepseek-chat）于 07:54:49Z 因 HTTP 402 按协议全局中止
> （报告 `CHAR001_LIVE_EXECUTION_REPORT.md`, `d9dcdf5`）; CAO 处置计费后授权重跑并
> 指定模型替换。

---

## 1. Execution Timestamp

| 项 | 值（UTC） |
|----|-----------|
| run started | `2026-08-30T08:05:55Z`（manifest `started_utc`） |
| run finished | `2026-08-30T08:37:20Z`（manifest `finished_utc`; wall ≈ 31 分 25 秒, 与窗口审查 nominal 预测 30.7 min 一致） |
| 首请求 / 末请求 | `08:05:55Z` / `08:37:20Z`（240 请求全部在窗内） |

## 2. Authorization Window

```text
FROZEN (adce878): 2026-08-30T07:53:00Z .. 2026-08-30T09:53:00Z (2h, CAO immediate-execution)
run 启动 08:05:55Z ∈ 窗口 ✅（cmd_run 启动守门通过）
全部 240 请求 ∈ [08:05:55Z, 08:37:20Z] ⊂ 窗口 ✅ —— 零窗外请求
```

## 3. Branch / Commit

- 分支: `work/phase4/char-001-execution`
- 执行时 HEAD: `f73b303`（模型替换提交; 阈值/状态机零改动, selftest 19/19）
- probe 实现: `scripts/infra_probe.py`（`b1e352a` 冻结实现 + 窗口登记 + 本次模型替换）

## 4. Preflight Result

```text
PREFLIGHT_PASS (exit 0, --run-id char-002)
```

run 内部门禁（manifest）: G1_connectivity PASS / G2_config_snapshot PASS / G3_time_registration PASS。

## 5. Live Run Result

```text
final_status = COMPLETED（全矩阵完成, 无中止, 无 stop-rule 触发）
conditions_executed = [A, B, C, D]（全部按冻结顺序执行）
C→D 分支 = C clean → SUSTAINED_STRESS_C_DENSITY（D1/D2 RECOVERY_FLOW 未触发）
recovery flow = NOT TRIGGERED（零失败, 无恢复观测入口）
```

## 6. Actual Endpoint / Model（G2 快照逐字记录）

| 项 | 值 |
|----|-----|
| base_url | `https://api.deepseek.com` |
| model | **`deepseek-v4-flash`**（CAO 于 2026-08-30 指定替换, 原 `deepseek-chat`; ID 经 GET /models 核验存在; 先例: INFRASTRUCTURE_INCIDENT_RECORD R3 压力探针 30/30） |
| api_key_source | `env:DEEPSEEK_API_KEY`（fingerprint 见 manifest, 值未输出） |
| python / platform | 3.11.15（`.venv`）/ Windows-10-10.0.26100-SP0 |
| dry_run | **false**（live） |

**表征对象变更声明（事实登记）**: char-002 表征的 judge path 为
`deepseek-chat → deepseek-v4-flash`（CAO 指定）; 与历史事件记录 R/R2/R3 所用
deepseek-chat 路径**不构成同主体可比序列**——此为主体范围声明, 非因果结论。

## 7. Artifact Paths

```text
data/characterization/char-002/manifest.json    (3444 bytes)
data/characterization/char-002/records.jsonl    (133522 bytes)
data/characterization/char-002/results.json     (1836 bytes)
```

三文件均存在、非空、JSON/JSONL 可解析; run-id 一致（`char-002`）;
records 行数（240）== manifest `requests_total`（240）== 冻结矩阵总和（20+40+60+120）。

char-001 产物保留未动（`d9dcdf5` 入库版本, 作为前置事件证据）。

## 8. Artifact SHA-256

```text
581178e6aa5acbba8cc1f67602064640f36edd63bcef7e897a278176441fb22d  manifest.json
c8007670d739ebcc41ceea05861951b0b10284e2bec1bad1118315d59ccac260  records.jsonl
fe8eab636f3a22dec1d2aa5c7f894b873f3cd4597a2d5ea8f2cf442a910f06bf  results.json
```

## 9. Request / Record Counts

| Condition | 冻结计划 | 实际请求 | records 行 |
|-----------|----------|----------|------------|
| A | 20 | 20 | 20 |
| B | 40 | 40 | 40 |
| C | 60 | 60 | 60 |
| D（SUSTAINED_STRESS_C_DENSITY） | 120（1s 密度） | 120 | 120 |
| **合计** | **240** | **240** | **240** |

（Q0 跨条件静默 3×300s 按冻结逻辑执行, 不产生记录。）

## 10. Condition-Level Status（冻结判定式输出, 原样登记）

| Condition | requests | success | failure | success_rate | S1(≥X) | S2(≤Y) | S3 | passed |
|-----------|----------|---------|---------|--------------|--------|--------|----|--------|
| A（30s×20） | 20 | 20 | 0 | 100.0% | ✅ | ✅ | ✅ | **true** |
| B（5s×40） | 40 | 40 | 0 | 100.0% | ✅ | ✅ | ✅ | **true** |
| C（1s×60, 观察档） | 60 | 60 | 0 | 100.0% | — | — | — | NOT_APPLIED_OBSERVATIONAL |
| D（C clean 持续压力 1s×120） | 120 | 120 | 0 | 100.0% | — | — | — | D1/D2 NOT_TRIGGERED |

D 明细（results.json 原文）: `variant: SUSTAINED_STRESS_C_DENSITY`;
`recovery_latency_seconds: null`; `stable_recovery: null`; `S4_pass: null`;
`note: "C finished without stop rule; D1/D2 NOT_TRIGGERED"`; `probes_sent: 120`。
**未触发路径登记**: RECOVERY_FLOW / D1 恢复探测 / D2 恢复确认 / N=5 停止规则 /
双连停 ABORTED / 全局认证计费中止 —— 全部 NOT TRIGGERED（零失败所致）。

## 11. Failures / Exceptions

```text
零失败记录: records.jsonl 240 行全部 result=="success"（ConvertFrom-Json 全量核验, 非成功计数=0）
零异常: 无任何 exception_type/exception_message/cause 条目
零 stop-rule: 无 [stop-rule] 输出, 无 stopped_by_failure_rule=true
```

无可审异常条目（Task 4 异常审查对象为零）。

## 12. Hard-Constraint Verification

| 约束 | 状态 |
|------|------|
| 窗口内执行（240 请求零窗外） | ✅ |
| 不修改 probe logic / protocol / 阈值 / 状态机 | ✅（阈值 X=90/Y=3/Z=60/W=5/Q0=300/T_max=900/N=5 逐项一致; 模型替换为 CAO 明确指定的唯一配置变更, `f73b303`） |
| run-id = char-002（char-001 证据保留未动） | ✅ |
| 不 retry / 不 backoff / 不人工干预状态机 | ✅（矩阵按冻结节奏自然完成） |
| 不伪造/补写证据 | ✅（probe 原样写盘, SHA-256 登记） |
| dry_run=false | ✅ |
| Evidence Review / R4 / Phase 4.3 未进入 | ✅（本报告后即 STOP） |

## 13. Explicit Statement

```text
No causal, rate-limiting, capacity, or root-cause conclusion is made at the
execution stage.
```

本报告仅登记 OBSERVED 事实: 240/240 请求成功（A/B/C/D 四档位）、零失败、零异常、
S1–S3 判定式对 A/B 输出 PASS（判定式输出为冻结公式结果, 非本报告推断）、
D 持续压力档 120/120。表征对象为 deepseek-v4-flash judge path。

---

## Phase 4 char-002 Live Execution — COMPLETE

```text
Authorization Window:  2026-08-30T07:53:00Z .. 09:53:00Z (frozen adce878)
Execution Time:        2026-08-30T08:05:55Z .. 08:37:20Z (UTC, wall ≈31.4 min)
Preflight:             PASS
Live Run:              COMPLETED (full A→B→C→D matrix)
Run ID:                char-002
Artifacts:             manifest.json PRESENT / records.jsonl PRESENT / results.json PRESENT
Evidence Integrity:    PASS (parseable, run-id consistent, counts == frozen matrix, SHA-256 registered)
Code/Protocol Changes: model substitution only (CAO-authorized, f73b303); thresholds/state machine UNCHANGED
Live Requests:         240 (all in-window, zero retry)
Causal Interpretation: NOT PERFORMED
Next Gate:             Human Evidence Review
R4:                    LOCKED
```

## STOP

本报告完成即 STOP。不进行 Evidence Review 裁决、不作 CAO Decision、不进入 R4、
不追加任何实验、不对 100% 成功率作任何稳定性/容量/限流推断。
