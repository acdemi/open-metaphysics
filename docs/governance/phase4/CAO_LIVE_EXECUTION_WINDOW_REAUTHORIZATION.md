# CAO Decision — Phase 4 Live Execution Window Re-Authorization

> **文档类型**: 治理决议（CAO Decision, 审计 Sprint —— 只读核实 + 决议登记）
> **日期**: 2026-08-29 · 审计时点 UTC: `2026-08-29T15:56:31Z`
> **分支**: `work/phase4/cao-window-reauthorization`（基于 `work/phase4/probe-implementation` tip `2cbbb7e`）
> **审计范围**: 仅 Re-Authorization Review。本任务**不执行** characterization。
> **协议依据**: `INFRASTRUCTURE_CHARACTERIZATION_PROTOCOL.md` · `PROBE_IMPLEMENTATION_REPORT.md`
> · `scripts/infra_probe.py`（均在 `work/phase4/probe-implementation` 分支, 本分支同树）

---

## 1. Decision

```text
ORIGINAL EXECUTION WINDOW: EXPIRED
LIVE EXECUTION: NOT AUTHORIZED UNDER ORIGINAL WINDOW
```

原执行窗口 `2026-08-27T02:00:00Z .. 2026-08-27T06:00:00Z` 已于审计时点
（`2026-08-29T15:56:31Z`）过期约 2 天 10 小时。窗口硬锁
（`scripts/infra_probe.py::EXECUTION_WINDOW_UTC`, 窗口外 `run` 直接 `SystemExit` 拒绝）
与本决议一致：**原窗口下不存在任何合法的 live 执行路径**。

在新窗口由人工 CAO 明确授权之前：

- 不执行 `preflight`（含其唯一 GET 门禁请求）；
- 不执行 `run`；
- 不发起任何 live request。

## 2. Probe Status

```text
IMPLEMENTATION: COMPLETE
OFFLINE VERIFICATION: PASS
LIVE REQUESTS DURING IMPLEMENTATION: ZERO
```

核实证据（本审计只读复核, 与实现报告一致）：

| 项 | 声称 | 审计核实 |
|----|------|----------|
| 实现工件 | `scripts/infra_probe.py` / `scripts/README.md` / `PROBE_IMPLEMENTATION_REPORT.md` | 均存在于 `work/phase4/probe-implementation`（`git ls-tree -r 2cbbb7e`）；实现提交 `b1e352a` + 归档 `2cbbb7e` |
| offline selftest | 19/19 PASS | 报告 §offline selftest: 字段完整性/异常三要素/cause 链截断/滚动窗口算术/冻结判定式/S1–S3 判定/C 观察/计费检测/窗口守卫 |
| dry-run | A/B/C/D 状态机完整通过 | 报告 §dry-run smoke: full A/B/C/D 离线跑通（零网络请求） |
| live requests | 0 | 实现报告 ❌ 不执行 preflight（等待执行窗口内指示）；dry-run 强制零网络；live `run` 仅懒加载 `openai` |
| retry/backoff | 不存在 | 实现明确无重试机制（符合协议：失败即记录, 不重试） |
| execution thresholds | 已冻结 | `CONFIG["thresholds"]` 硬编码, 源码标注 "frozen by human review on 2026-08-25 - DO NOT MODIFY" |
| CLI | `--help` 正常 | 审计时直接执行: usage = `show-config / selftest / preflight / run`（preflight/run 未执行） |
| ruff | PASS | `ruff check scripts/infra_probe.py` → All checks passed! |

> 环境备注: `python -m scripts.infra_probe --help` 模块路径方式要求脚本位于仓库工作树
> （probe 实现未合入 main, 工作树无该文件）；审计以临时目录提取 + 直接文件方式执行
> `--help`, 语义等价, 零网络、零仓库改动。

## 3. Frozen Parameters

冻结来源: `scripts/infra_probe.py` `CONFIG["thresholds"]`（源码内注释: 2026-08-25 人工
冻结, DO NOT MODIFY）。协议 `§5` 与实现一致。

| 参数 | 值 | 语义（协议原文摘要） |
|------|----|----------------------|
| `X` | **90** | S1: LLM success rate ≥ X%（A、B） |
| `Y` | **3** | S2: maximum consecutive failures ≤ Y（A、B） |
| `Z` | **60** | S4: recovery latency ≤ Z seconds（D） |
| `W` | **5** | S3: 永久失败窗判定——后缀连续失败段 ≥ W 即 fail（A、B） |
| `Q0` | **300** | D0: C 终止后静默间隔（秒, 无任何请求） |
| `T_max` | **900** | D1: 恢复探测上限（秒）；60 s 间隔单发 probe |
| `N` | **5** | 失败停止条件: 连续 N 次 Connection error 类失败立即停该 condition |

实验矩阵（冻结）: A(30s×20) / B(5s×40) / C(1s×60, `NOT_APPLIED_OBSERVATIONAL`) /
D(flow: pause→probe→confirm)。

执行窗口（冻结于实现）:

```text
EXECUTION_WINDOW_UTC = ("2026-08-27T02:00:00Z", "2026-08-27T06:00:00Z")
```

> 协议 `§5-A 冻结记录`表格的签字栏（批准人/冻结日期）在协议文档中留白待填, 实现侧
> 以源码注释形式登记冻结（2026-08-25 人工审查）。本决议不修改任何阈值, 亦不代填
> 协议签字栏。

本决议**不修改、不重申变更、不重新解释**以上任何阈值。任何阈值变更须经 ACP。

## 4. Authorization Boundary

```text
No live request is authorized by this decision.
```

- 本决议仅登记窗口过期事实与守门状态, 不产生任何 live 执行授权；
- `preflight`（G1–G3, 含一次 GET 门禁请求）同属 live 边界, 一并禁止；
- 允许且仅允许: 只读审计、离线 `show-config` / `selftest`（零网络）、本决议文档本身；
- 任何网络请求（包括一次性的门禁 GET）在新窗口授权前均视为越权。

## 5. Required Next Decision

> **Establish a new explicitly authorized UTC execution window.**

新窗口必须由人工 CAO 明确指定（起始/结束 UTC 时间戳）, 并相应更新实现中的
`EXECUTION_WINDOW_UTC`（该更新本身是代码变更, 须按治理流程另行授权与提交,
不在本决议内执行）。本决议**不设定、不建议、不预定**任何新窗口时间。

## 6. Locked Stages

```text
Evidence Review: LOCKED
R4: LOCKED
Phase 4.3: LOCKED
```

解锁前置（协议原文）: 新窗口授权 + characterization 完成 + 冻结标准下观察到稳定
阈值, 三者齐备前 R4 不授权（prerequisite, not substitute）。Evidence Review 与
Phase 4.3 依存于其上游阶段, 维持锁定。

---

## 附: 审计轨迹（Task 1–4, 全部只读）

| Task | 命令/方法 | 结果 |
|------|-----------|------|
| 1 仓库状态 | `git status --short` / `git branch --show-current` / `git log --oneline --decorate -10` | 审计起点 main@`1881e64` 工作树干净, 无 unresolved merge state, 未做任何 stash/reset/修改；`work/phase4/probe-implementation` 存在（`2cbbb7e`）, 提交链 `030e415→078f1dc→90f14dd→b1e352a→2cbbb7e` 完整 |
| 2 Probe 实现 | `git ls-tree -r 2cbbb7e` / 报告核对 / 临时目录 `--help` / `ruff check` | 四项工件在位; selftest 19/19、dry-run A/B/C/D、live=0 与报告一致; CLI 正常; ruff PASS |
| 3 冻结参数 | `git show 2cbbb7e:scripts/infra_probe.py` + 协议 `§5` 交叉核对 | X=90 / Y=3 / Z=60 / W=5 / Q0=300 / T_max=900 / N=5；窗口 `2026-08-27T02:00Z..06:00Z` 与任务书一致 |
| 4 窗口判定 | 审计时点 UTC `2026-08-29T15:56:31Z` | 早于窗口结束 `2026-08-27T06:00:00Z` 不成立 → `original window = EXPIRED` → 不执行 preflight/run/任何 live request |

## Hard Constraints 遵守声明

本审计: ❌ 未执行 live preflight ❌ 未执行 `infra_probe run` ❌ 未发送任何网络请求
❌ 未修改 probe implementation ❌ 未修改 protocol ❌ 未修改 thresholds
❌ 未触碰主工作树（无 merge conflict 需处理, 亦未做 stash/reset）
❌ 未进入 Evidence Review ❌ 未进入 R4 ❌ 未进入 Phase 4.3。

## STOP CONDITION

本决议文档提交后, Re-Authorization Review **立即终止**。等待人工 CAO 指定新的
UTC execution window。在此之前不执行 characterization, 不解锁任何锁定阶段。
