# Phase 4 — Characterization Evidence Review (char-001)

> **文档类型**: 治理审查记录（Evidence Review Sprint —— 只读审计）
> **审查时点 UTC**: `2026-08-29T16:37:31Z` → `2026-08-29T16:38:21Z`
> **分支**: `work/phase4/char-001-execution`（HEAD `316bbc2`, 工作树干净）
> **审查对象声明**: 指令声称 "`char-001` live characterization 已完成"
> **授权窗口**: `2026-08-30T00:30:00Z .. 2026-08-30T01:00:00Z`（登记于 `9512d5e`）
> **协议依据**: `INFRASTRUCTURE_CHARACTERIZATION_PROTOCOL.md` / `PROBE_IMPLEMENTATION_REPORT.md` / `scripts/infra_probe.py`

---

## 审查结论（先行）

```text
EVIDENCE REJECTED
```

**核心依据（两条独立事实链, 任一即足以否决）**:

1. **产物不存在**: `manifest.json` / `records.jsonl` / `results.json` 在整个仓库中
   不存在（见 Task 1 检索方法）。无产物 = 无可审查证据集。
2. **时间不可能**: 审查时点 `2026-08-29T16:38:21Z` 早于授权窗口开启
   （`2026-08-30T00:30:00Z`）约 7.9 小时; probe 自身窗口守门实测返回
   `False | now=... outside approved live window`（`cmd_run` 在窗口外
   `SystemExit` 拒绝启动）。窗口未开启 ⇒ 窗口内 live run 在时间上不可能已发生。
   且本地无任何 run 提交/新分支（HEAD 仍为止于本审查前的 `316bbc2`）。

这是本 Phase 第三次前置条件缺失（ lineage: ① 08-27 窗口过期 → ② 占位符未填
`6991912` → ③ 本次: 窗口未开即声称完成）。

---

## Task 1 — Artifact Integrity

**结论: NOT MET —— 三个产物文件均不存在。**

检索方法（全部只读）:

| 方法 | 范围 | 结果 |
|------|------|------|
| `rg --files -g "manifest.json" -g "records.jsonl" -g "results.json"`（含 hidden） | 全仓库 | 0 命中 |
| `Get-ChildItem -Recurse -Include manifest.json,records.jsonl,results.json` | 全仓库（深度 3+） | 0 命中 |
| `rg --files -g "*.jsonl" -g "*char-001*" -g "*char001*"` | 全仓库 | 0 命中 |
| 今日修改文件清单（排除 `.git`/`.venv`/`.pytest_cache`） | 全仓库 | 仅 `context/归档.md`、`scripts/infra_probe.py`（均为本审查线的登记/归档编辑）+ 1 个 `__pycache__` 编译缓存（离线 selftest 所致） |
| git 状态 | `git status --short` / `git log --decorate -8` / `git show-ref --heads` | 工作树干净; 无新提交; 无新分支 |

产出路径约定核对: probe 实现中 `CharacterizationRun._paths()` 将三产物写入
`out_dir`（`scripts/infra_probe.py` L328–330; `run` 时 `mkdir` L572）——
即任何一次真实 `run`（甚至 dry-run）都必然留下这三个文件。文件缺失与
"run 已完成" 的声称**不相容**。

交叉验证项（run-id / 时间戳 / records 数 / condition 数 / manifest↔records /
results↔records / 人工补写检查）: **全部 NOT REVIEWABLE** —— 无对象可验证。

## Task 2 — Protocol Conformance

**结论: NOT REVIEWABLE（无 records 可检）; 登记侧可验证事实如下。**

| 协议条目 | 状态 |
|----------|------|
| §1 request record（17 字段） | NOT REVIEWABLE（无 records.jsonl） |
| §2 configuration | 登记侧 ✅: 阈值冻结未动（show-config 实测 X=90/Y=3/Z=60/W=5/Q0=300/T_max=900/N=5）; endpoint `https://api.deepseek.com` / model `deepseek-chat` |
| §3 execution window | 登记侧 ✅: `EXECUTION_WINDOW_UTC = 2026-08-30T00:30Z..01:00Z`（`9512d5e`）; 守门实测: 审查时点在窗外, run 会被拒绝 |
| §4 condition execution（A/B/C/D） | NOT REVIEWABLE（无任何执行痕迹） |
| §5 C detection | NOT REVIEWABLE |
| §6 recovery | NOT REVIEWABLE |
| §7 D branch | NOT REVIEWABLE |
| no retry / no backoff | NOT REVIEWABLE（无请求记录）; 附注: 实现本身无重试/退避代码（b1e352a 审计在案） |
| no out-of-window request | 佐证性事实: 仓库无任何请求证据存在; 本次审查线（`6991912` → `612d5b2` → `316bbc2`）累计 **零 live 请求** |

## Task 3 — Evidence Classification

仅登记观察事实, 不作任何因果解释:

| 项 | 分类 |
|----|------|
| manifest.json / records.jsonl / results.json | **NOT OBSERVED** |
| 任何 live request（含 preflight GET） | **NOT OBSERVED** |
| Condition A / B / C / D 执行 | **NOT TRIGGERED** |
| C trigger → RECOVERY_FLOW | **NOT TRIGGERED** |
| C clean → SUSTAINED_STRESS_C_DENSITY | **NOT TRIGGERED** |
| success/failure 判定数据（S1–S4） | **NOT OBSERVED** |
| 指令声称的 "char-001 已完成" | **UNKNOWN → 不成立**: 与仓库状态（无产物/无提交）及时钟（窗口未开）矛盾, 判定为**未获支持** |
| 根因 / rate limiting / provider policy / capacity | **不做任何表述**（禁止项遵守） |

## Task 4 — Anomaly Review

仅一项异常, 为**元层级**（审查前提异常）, 无请求级异常可审:

1. **原始记录位置**: 本审查文档 + 审计命令输出（Task 1 检索表; 守门实测
   `check_execution_window() → (False, "now=2026-08-29T16:38:21Z outside
   approved live window 2026-08-30T00:30:00Z..01:00:00Z")`）。
2. **时间**: `2026-08-29T16:37:31Z .. 16:38:21Z`（审查时点）。
3. **condition**: 无（无任何 condition 运行）。
4. **exception type/message**: 无运行时异常; 异常为流程异常 ——
   `EVIDENCE REVIEW REQUESTED WITHOUT EVIDENCE`（声称完成, 产物缺失, 时点先于窗口）。
5. **cause chain**: 不适用（不推测指令来源动机; 仅登记事实链: 窗口未开 +
   零产物 + 零 run 提交）。
6. **是否触发 protocol stop/recovery**: 否 —— 无 run 存在, N=5 停止条件、
   D 恢复流均未进入（NOT TRIGGERED）。
7. **超出协议的因果推断**: 无（本节不作任何归因）。

## Task 5 — Decision

```text
EVIDENCE REJECTED
```

- 裁决依据: 证据集为空（Task 1）+ 完成声称与可验证事实矛盾（时间链 + 仓库状态链）。
- 本裁决**不批准 R4**; 不产生任何新的窗口设定; 不解释任何现象。

---

## Hard Constraints 遵守声明

❌ 未执行任何网络请求（审查全程零请求; 守门实测为离线函数调用）
❌ 未修改 probe implementation / protocol / thresholds
❌ 未进入 R4 ❌ 未进入 Phase 4.3 ❌ 未触碰 Knowledge Layer / 7.2B
✅ 仅只读审计 + 本治理文档 + 归档。

## STOP CONDITION

本审查完成即 **STOP**。

```text
R4: LOCKED
```

只有新的 CAO Decision 明确授权后才能进入 R4。characterization 本身仍需在
授权窗口（`2026-08-30T00:30Z..01:00Z`）开启后、按冻结状态机真实执行并产出
三产物, 届时方可重新进入 Evidence Review。
