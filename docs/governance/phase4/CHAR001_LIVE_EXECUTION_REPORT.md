# Phase 4 — char-001 Live Execution Report

> **文档类型**: 执行报告（characterization execution —— 仅事实登记, 无因果结论）
> **执行时点 UTC**: start `2026-08-30T07:54:39.870Z` → finish `2026-08-30T07:54:49.918Z`
> **分支**: `work/phase4/char-001-execution`（执行时 HEAD = `adce878`）
> **产物目录**: `data/characterization/char-001/`

---

## 1. Execution Timestamp

| 项 | 值（UTC） |
|----|-----------|
| run started | `2026-08-30T07:54:39.870121Z` |
| run finished | `2026-08-30T07:54:49.917763Z`（wall ≈ 10.05 s） |
| 唯一请求窗口 | `07:54:40.220Z → 07:54:49.917Z`（elapsed 9.703 s） |

## 2. Authorization Window

```text
FROZEN (adce878): 2026-08-30T07:53:00Z .. 2026-08-30T09:53:00Z  (2h, CAO immediate-execution)
run 启动时刻 07:54:39Z ∈ 窗口 ✅（cmd_run 启动守门通过）
唯一请求 07:54:40Z ∈ 窗口 ✅ —— 零窗外请求
```

窗口 provenance（本窗口为第五代登记）: 08-27 原窗口（EXPIRED）→ 00:00Z..00:30Z →
00:30Z..01:00Z → 02:00Z..04:00Z（过期未用）→ **07:53Z..09:53Z（本次执行）**。

## 3. Branch / Commit

- 分支: `work/phase4/char-001-execution`
- 执行时 HEAD: `adce878`（冻结窗口提交; 阈值/状态机零改动, selftest 19/19）
- probe 实现: `scripts/infra_probe.py`（`b1e352a` 冻结实现 + 窗口登记系列提交）

## 4. Preflight Result

```text
PREFLIGHT_PASS (exit 0)
```

`run` 内部门禁（manifest 记录）: G1_connectivity **PASS**（HTTP 200, http_2xx）/
G2_config_snapshot **PASS** / G3_time_registration **PASS**。

## 5. Live Run Result

```text
final_status = ABORTED_AUTH_OR_BILLING（协议规定的全局中止路径, exit 0）
conditions_planned  = [A, B, C, D]
conditions_executed = [A]（A 条件第 1 个请求即触发 402, 全局中止）
C→D 分支            = NOT TRIGGERED（C 未执行）
recovery flow       = NOT TRIGGERED
sustained stress    = NOT TRIGGERED
```

run 按冻结状态机正常完成其协议路径（认证/计费类错误 → 全局中止, 无 retry）。

## 6. Actual Endpoint / Model（G2 快照逐字记录）

| 项 | 值 |
|----|-----|
| base_url | `https://api.deepseek.com` |
| model | `deepseek-chat` |
| api_key_source | `env:DEEPSEEK_API_KEY`（fingerprint `98d5b340390f`, 值未输出） |
| proxy_env_vars | `{}`（无代理） |
| python / platform | 3.11.15（`.venv`）/ Windows-10-10.0.26100-SP0 |
| dry_run | **false**（live） |

## 7. Artifact Paths

```text
data/characterization/char-001/manifest.json    (3418 bytes)
data/characterization/char-001/records.jsonl    (691 bytes)
data/characterization/char-001/results.json     (921 bytes)
```

三文件均存在、非空、JSON/JSONL 可解析; run-id 一致（`char-001`）;
records 数（1）== manifest `requests_total`（1）== results 条件 A `requests`（1）。

## 8. Artifact SHA-256

```text
38fb69a563938f86bbff67b444ff7053830b0dbfa32971f359a7463b5b51f73c  manifest.json
e38fb0452615fc7463e6d508407dae394670cf16c74adba7383ce7b367087514  records.jsonl
4bc3d56a06bd756a816f17d9f1a686f8882960512762e18a4a15e3f96305892e  results.json
```

## 9. Request / Record Counts

| 项 | 值 |
|----|-----|
| requests_total（manifest） | 1 |
| records.jsonl 行数 | 1（`char-001-0001`） |
| A 计划 / 实际 | 20 / **1**（第 1 请求后全局中止, 未达 N=5 停止规则） |
| B / C / D | 0 / 0 / 0（NOT EXECUTED） |
| 与冻结矩阵的偏差原因 | 协议 §全局中止: 认证/计费类错误立即终止（非参数偏离） |

## 10. Condition-Level Status

| Condition | 状态 | requests | success | failure | S1 | S2 | S3 | passed |
|-----------|------|----------|---------|---------|----|----|----|--------|
| A | ABORTED（1 请求后全局中止） | 1 | 0 | 1 | false | true | true | false |
| B | NOT EXECUTED | 0 | — | — | — | — | — | — |
| C | NOT EXECUTED | 0 | — | — | — | — | — | — |
| D | NOT TRIGGERED | 0 | — | — | — | — | — | — |

注: A 的 `passed=false` 为 1 样本下的机械判定（S1: 0% < 90%），**不构成任何表征结论**。

## 11. Failures / Exceptions（原始记录, 逐要素）

- **原始记录位置**: `records.jsonl` 行 1（`request_id: char-001-0001`）
- **时间**: start `2026-08-30T07:54:40.220Z` / end `07:54:49.917Z`（9.703 s）
- **condition**: A
- **exception_type**: `APIStatusError`
- **exception_message**: `Error code: 402 - {'error': {'message': 'Insufficient Balance', 'type': 'unknown_error', 'param': None, 'code': 'invalid_request_error'}}`
- **cause chain**: `exception_cause = null`（无底层 cause）
- **判定**: 该错误命中协议定义的认证/计费类全局中止条件（`is_auth_or_billing`）,
  状态机按冻结规则立即终止——**触发了 protocol-defined stop**（非 N=5 连败规则,
  `stopped_by_failure_rule=false`）
- **超出协议的因果推断**: 无。仅登记: 服务端返回的响应报文如上所引。

## 12. Hard-Constraint Verification

| 约束 | 状态 |
|------|------|
| 窗口内执行（零窗外请求） | ✅（启动守门 + 唯一请求均在 07:53Z..09:53Z 内） |
| 不修改 probe/protocol/阈值/状态机 | ✅（执行时 HEAD=`adce878`, diff 仅窗口常量+selftest 样本） |
| 冻结阈值 X=90/Y=3/Z=60/W=5/Q0=300/T_max=900/N=5 | ✅（manifest `thresholds_frozen` 逐项一致） |
| run-id = char-001 | ✅（manifest/records/results 三处一致） |
| 不 retry / 不 backoff / 不人工追加 | ✅（requests_total=1, 无第二次请求） |
| 不伪造/补写证据 | ✅（三产物为 probe 原样写盘, SHA-256 已登记） |
| 不把 dry-run 当 live | ✅（`dry_run: false`） |
| 不进入 Evidence Review / R4 / Phase 4.3 | ✅（本报告后即 STOP） |

## 13. Explicit Statement

```text
No causal, rate-limiting, capacity, or root-cause conclusion is made at the
execution stage.
```

登记的原始事实仅为: 服务端对第 1 个 chat completion 请求返回 HTTP 402
（响应报文见 §11）; 该响应属账户计费状态类返回, **不是**表征测量数据点;
本次 run 未产生任何密度档位（A/B/C/D）的有效表征样本。

---

## Phase 4 char-001 Live Execution — COMPLETE（状态机按协议走完中止路径）

```text
Authorization Window:  2026-08-30T07:53:00Z .. 09:53:00Z (frozen, adce878)
Execution Time:        2026-08-30T07:54:39Z .. 07:54:49Z (UTC)
Preflight:             PASS
Live Run:              TERMINATED PER PROTOCOL — ABORTED_AUTH_OR_BILLING
Run ID:                char-001
Artifacts:             manifest.json PRESENT / records.jsonl PRESENT / results.json PRESENT
Evidence Integrity:    PASS（可解析/run-id 一致/计数一致/SHA-256 登记）
Code/Protocol Changes: NONE（执行时 HEAD=adce878, 仅此前授权的窗口登记）
Live Requests:         1（窗口内, 无 retry）
Causal Interpretation: NOT PERFORMED
Next Gate:             Human Evidence Review（或人工处置计费状态后的新授权）
R4:                    LOCKED
```

## STOP

本报告完成即 STOP。不进入 Evidence Review 裁决、不进入 CAO Decision、不进入 R4、
不自行发起新 run、不对 402 作任何超出原始记录的解释。
