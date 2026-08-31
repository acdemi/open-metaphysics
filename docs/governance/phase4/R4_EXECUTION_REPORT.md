# Phase 4 — R4 Execution Report（precheck-stop）

> **文档类型**: 执行报告（execution halted at precheck gate —— 仅事实登记）
> **授权**: CAO-P4-R4EXEC-001（`R4 EXECUTION AUTHORIZED`, 窗口 16:00Z..18:00Z）
> **分支**: `work/phase4/char-001-execution`
> **最终状态**: **FULL RUN NOT EXECUTED (0/216)** — precheck FAIL → 冻结纪律 STOP →
> 窗口在停止期间过期

---

## 1. Execution Timeline（UTC, 实测）

| 时刻 | 事件 |
|------|------|
| 16:08:37Z | 触发门禁首次测量（in-window 确认, 16:09:40Z 复核; 注意 PowerShell `[datetime]` Z 后缀 Kind 陷阱, 以 DateTimeOffset/round-trip 复测为准） |
| 16:09–16:10Z | §2 核验通过（分支/干净/harness 在位/R4 路径零覆盖）; precheck 尝试 1 **崩溃**——默认 `--compare-harness` 路径 `reports/phase4_2_harness/phase4_2_raw_results.json` 不存在（陈旧默认路径; 崩溃发生于加载对比文件阶段, **零 live 请求**） |
| ~16:11Z | 只读核查: 真实基线文件 `reports/phase4_2_raw_results.json`（mtime 2026-08-10, 即原 Phase 4.2 standalone-harness 输出, 早于 R2/R3）在位; 以显式 `--compare-harness` 指向该文件（路径解析, 非代码/矩阵/主体修改; 处置透明登记于本报告） |
| 16:12–16:22Z | precheck 尝试 2: **3 executions 全部真实执行**——judge_mode=deepseek, HTTP 200, model=deepseek-v4-flash @ api.deepseek.com（逐请求合规） |
| 16:22:18Z | precheck 报告生成: **verdict FAIL**（见 §3） |
| 16:22Z+ | 按冻结纪律 **STOP**（授权 §9; 就绪文档既定: 非 0 → STOP）——full run 未启动 |
| 18:00:00Z | 授权窗口过期（停止期间, 无任何请求） |
| 2026-08-31T03:18Z | 本次测量: 窗口已过期 558 min（本地 08-31 11:18, 系统经历 ≈11h 真实时间流逝——会话暂停/机器休眠; 非任何请求行为） |

## 2. Request Accounting（诚实口径）

| 类别 | 数量 |
|------|------|
| precheck 尝试 1 的 live 请求 | **0**（崩溃先于任何请求） |
| precheck 尝试 2 的 executions | **3**（C0/C1/C2 × case 1 × seed 42, 全部在窗内） |
| full run（216 矩阵） | **0**（未启动） |
| 窗外请求 | **0** |
| retry / backoff / 额外探索请求 | **0** |

## 3. Precheck Verdict（原始报告事实, 无因果解释）

报告: `ACIS/reports/phase4_2_r4_precheck_report.json`
（SHA-256 `c0945c8a90749d1e316aa4a7f4397e1eef800858b23db181566d44d7203a455f`, 834 bytes）
对比基线: `ACIS/reports/phase4_2_raw_results.json`（2026-08-10 生成, **deepseek-chat 时代主体**）

| config | real decision | real conf | judge_mode | harness decision | harness conf | label match | offset |
|--------|---------------|-----------|------------|------------------|--------------|-------------|--------|
| C0 | 番茄叶霉病 | 0.6 | deepseek | 番茄叶霉病 | 0.92 | match | **0.320** |
| C1 | 番茄叶霉病 | 0.62 | deepseek | 番茄叶霉病 | 0.85 | match | 0.230 |
| C2 | 无法定论（待实验室病原鉴定） | 0.2 | deepseek | 番茄叶霉病 | 0.95 | **DIFFERS（ABSTAIN）** | **0.750** |

**Verdict: FAIL** — C0 offset 0.320 > 0.3（超阈 0.02）; C2 label DIFFERS + offset 0.750。

**观察登记（非结论）**: 三次执行的链路与主体完全合规（judge_mode=deepseek ×3,
HTTP 200 ×3）; 失败发生在 real-agent 输出与 **08-10 deepseek-chat 时代基线**的
对比门上。该对比为跨主体比较——与 GAP-E1（主体变更）的登记口径一致。本报告
不对其作任何成因解释; 处置选项由人工 CAO 裁定（见 §6）。

## 4. Evidence Inventory（全部保全, SHA-256 登记）

| 证据 | SHA-256（前 16 位…） | 大小 |
|------|---------------------|------|
| `ACIS/logs/phase4_2_r4_preflight/precheck_seed42/c0_bare_baseline/runner/metrics.csv` | cded504c506ae165… | 661b |
| …/c0_bare_baseline/runner/summary.md | c9cf4ca4e8beb6e0… | 1388b |
| …/c0_bare_baseline/runner/traces/a85e767a….json | 8f10f53071d4a873… | 57429b |
| …/c1_all_on/runner/metrics.csv | 62a847222b5a646f… | 665b |
| …/c1_all_on/runner/summary.md | 0248c5448895337d… | 1386b |
| …/c1_all_on/runner/traces/2a6ab584….json | 02c839b332625ac6… | 102955b |
| …/c2_no_memory/runner/metrics.csv | 8bacca6e587f5c35… | 688b |
| …/c2_no_memory/runner/summary.md | 1420b90d11928e90… | 1412b |
| …/c2_no_memory/runner/traces/def3b26a….json | 2fd2d3a9b289086f… | 69485b |
| …/_flattened/challenge_set_v1_flattened.json | f652666520a4d2fb… | 914b |
| `ACIS/reports/phase4_2_r4_precheck_report.json` | c0945c8a90749d1e… | 834b |

原始产物位于外部 ACIS 工作区, 未修改、未删除、未复制改写。

## 5. Hard-Constraint Verification

| 约束 | 状态 |
|------|------|
| 窗口纪律 | ✅ 全部 3 请求在窗内; 窗口过期后零请求 |
| 主体/端点 | ✅ deepseek-v4-flash @ api.deepseek.com（env `DEEPSEEK_MODEL`, 零代码改动） |
| 不修改 probe/protocol/阈值/harness/矩阵 | ✅（`--compare-harness` 为路径实参, 非代码变更） |
| precheck FAIL → STOP 不续跑 | ✅（full run 0/216 未启动） |
| 失败记录保全 | ✅（precheck FAIL 报告与全部执行日志原样保留） |
| 零因果解释 | ✅ |
| Phase 4.3 / Knowledge | LOCKED（未触碰） |

## 6. Open Items（由人工 CAO 裁定, 本报告不预设）

1. **precheck 对比基线的主体口径**: 现基线为 deepseek-chat 时代（08-10）产物,
   与授权主体（v4-flash）跨主体对比。CAO 须裁定: (a) 授权以"链路检查口径"重新
   解释 precheck（链路已证实可执行）并另行授权 full run 新窗口; (b) 先在 v4-flash
   主体下重建 harness 基线再预检; (c) 其他处置。
2. **新窗口授权**: 原窗口已过期; 任何续跑须新 CAO Decision（窗口 + 本报告事实）。
3. 路径处置先例登记: `--compare-harness` 显式路径本次已使用（陈旧默认路径问题）,
   未来执行计划应显式指定。

## 7. Explicit Statement

```text
No causal, rate-limiting, capacity, stability, or root-cause conclusion is made.
R4 full matrix NOT executed (0/216). Precheck evidence preserved unmodified.
Phase 4.3: LOCKED. Knowledge: LOCKED. GAP-E1/E2 dispositions unchanged.
```

## STOP

等待人工 CAO Review 与下一步授权。
