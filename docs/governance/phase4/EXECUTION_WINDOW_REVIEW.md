# Phase 4 — Execution Window Governance Review

> **文档类型**: 治理审查（只读分析, 零网络请求, 零代码修改）
> **审查时点 UTC**: 2026-08-29（晚于 `c99ebd4` 时间门禁 STOP）
> **分支**: `work/phase4/char-001-execution`（HEAD `c99ebd4`）
> **依据**: `scripts/infra_probe.py`（frozen, `b1e352a` + 窗口登记 `6e7192b`/`9512d5e`）、
> `INFRASTRUCTURE_CHARACTERIZATION_PROTOCOL.md`、`CHAR001_EVIDENCE_REVIEW.md`（`dd29b48`）、
> 归档 lineage `6991912 → 612d5b2 → 316bbc2 → c99ebd4`

---

## 1. Current Frozen Window

```text
Current Frozen Window:
  start = 2026-08-30T00:30:00Z
  end   = 2026-08-30T01:00:00Z

Duration:
  30 minutes

Source:
  scripts/infra_probe.py L72-75  EXECUTION_WINDOW_UTC = ("2026-08-30T00:30:00Z", "2026-08-30T01:00:00Z")
  commit 9512d5e（CAO 指示整体后移 +30min, 经两轮确认; 取代 6e7192b 的 00:00Z..00:30Z 暂登记）
  治理链: 520b12d（Re-Authorization 决议 §5 预留窗口变更路径）→ 6e7192b → 9512d5e
```

登记链备注: 执行指令 §3 所引 `2026-08-27T02:00Z..06:00Z` 为已被上述治理链正式取代的
过期文本; 当前冻结窗口与任务授权窗口一致, 不构成 §3 BLOCKED。本审查未修改任何窗口。

## 2. 30-Minute Sufficiency Assessment（基于冻结状态机代码, 非估算猜测）

冻结时序事实（`execute()` / `_run_fixed_density` / `_run_condition_d` / `_recovery_observation`）:

| 阶段 | 冻结参数 | 最短耗时 |
|------|----------|----------|
| preflight（独立命令, 1 GET, G1 timeout=15s） | — | 秒级 |
| A | 20 req × 30s 间隔（sleep 仅在请求之间, 时延挤占间隔） | 19×30 = **570s** |
| Q0 静默 | `if idx > 0` —— **每个 condition 之间**各一次（A→B、B→C、C→D 共 3 次） | 3×300 = **900s** |
| B | 40 req × 5s | 39×5 = **195s** |
| C | 60 req × 1s（streak≥N=5 提前停） | ≥ **59s** |
| D（C clean → SUSTAINED_STRESS_C_DENSITY） | 120 req × 1s | **119s** |
| D（C trigger → RECOVERY_FLOW） | D1 恢复探测 15 次×60s 间隔 + D2 确认 10×5s | 至多 **840s + 50s** + 时延 |
| 中段恢复（A 或 B 触发停止规则后, §6 立即插入） | 同 D1/D2 | 至多 **840s + 50s**/次 |
| 产物落盘 | 3 文件写盘 | 秒级 |

> 注意: 探测请求未显式设置 timeout, 使用 openai SDK 默认（600s, 含 SDK 级重试 2）——
> 单次挂起请求在病态情形下可引入 10–30 分钟级时延。此为实现冻结现状, 本审查不改动。

```text
minimum expected execution time（全成功、时延趋零的理论下限）:
  570 + 900 + 195 + 59 + 119 = 1843s ≈ 30.7 分钟   →  已超过 30 分钟窗口

expected execution time（健康端点, 时延 1–3s）:
  ≈ 31–33 分钟（preflight + 进程启动另计）

maximum plausible execution time:
  快速失败路径（A/B 停止 + 中段恢复 840s + D 恢复 840s）:
    单停恢复 ≈ 38 分钟; C 停止无恢复 ≈ 42 分钟; 双连停 ABORTED ≈ 35.5 分钟
    → ≈ 42–56 分钟
  慢速失败路径（端点挂起, SDK 默认 600s/次 ×SDK 重试）: 数次挂起即 +30–90 分钟,
    理论无上界
```

**结论: 30 分钟窗口不具备 operational margin —— 连名义全成功路径（≈30.7 分钟）
都无法在窗口内完成。** 在该窗口下, 任何一次完整 run 必然发生边界碰撞
（跨窗请求违反 §0「不得在窗口外发送任何 live request」, 或被迫中途停止产生部分证据）。
此前"最坏 34 分钟"的口头估计遗漏了 3×Q0 跨条件静默与中段恢复块, 以本节代码时序为准。

## 3. Historical Execution Failures（仅基于治理记录）

| # | 事件 | 治理记录 | 层级 |
|---|------|----------|------|
| 1 | 08-27 原窗口（02:00–06:00Z）过期未用 | `520b12d` | 编排 |
| 2 | 窗口占位符未填即下发执行 | `6991912` | 编排（治理输入校验） |
| 3 | 窗口未开启即声称"已完成" | `dd29b48`（EVIDENCE REJECTED） | 编排（完成判据未锚定产物） |
| 4 | 16:43Z 到达时窗口未开, 时间门禁 STOP | `c99ebd4` | 编排（会话到达时间随机） |

**判定**:

```text
Probe correctness:            SOUND（selftest 19/19; dry-run 全状态机通过;
                              窗口守门正确拒绝窗外启动; 产物写入器确定性; 零缺陷记录）
Execution orchestration:      DEFICIENT（四次连续编排失败, 零 probe 失败;
                              根因 = 缺少 scheduled wake-up: 会话由人工在任意时刻发起,
                              而 Prompt 无法在未来时刻自我唤醒）
```

两者不得混为一谈: 现有四步失败均不构成对 probe 实现正确性的任何否定。

## 4. Recommended Window Policy

| 维度 | Option A: 30 min | Option B: 2 h | Option C: 4 h |
|------|------------------|---------------|----------------|
| operational margin | **负值**（名义路径 30.7 min 已超窗） | 名义 +89 min; 快速失败 +64 min; 可吸收 2–3 次挂起 | 名义 +209 min; 可吸收 5+ 次挂起 |
| human intervention tolerance | 无（无时间处理 preflight 异常） | 充分（窗口内可完成 preflight 检查与产物审计） | 过剩 |
| boundary collision risk | **必然发生** | 低 | 极低 |
| governance complexity | 低但不可用 | 适当（请求总量仍由冻结矩阵封顶 ≈ 241 + ≤30 恢复探测, 窗口加长不增加请求量） | 授权暴露时间最长, 收益递减 |

**推荐: Option B（2 小时窗口）**, 建议窗口起点对齐整点, 会话于窗口开启前 ~15 分钟
被唤醒完成环境核验, 窗口开启即执行 preflight + run（run 启动越早, 窗内余量越大）。
Option A 必须否决; Option C 仅在计划进行多次观察性重复运行时才考虑（当前协议不允许）。

## 5. Scheduler Requirement

正式建议的执行管线:

```text
Authorization（CAO 窗口授权, 治理链登记）
    ↓
Scheduled Wake（人工日历提醒, 或 OS 级一次性计划任务）
    ↓
Window Verification（runtime 核对 current_utc ∈ [start, end]）
    ↓
Environment Verification（openai / DEEPSEEK_API_KEY / selftest, 零网络）
    ↓
Preflight（G1–G3, 1 GET）
    ↓
Live Run（冻结状态机, 禁 retry/backoff/人工干预）
    ↓
Artifact Audit（三产物存在/可解析/run-id 一致/SHA-256）
    ↓
STOP（等待人工 Evidence Review）
```

**明确指出: Prompt 本身不能承担 future-time scheduling。** 会话只能在被人类发起的
时刻评估, 这是四次编排失败的共同根因。

当前环境可用的定时能力（仅提出, 本审查不创建、不执行）:

1. **人工日历/闹钟 + 窗口开启时手动下发执行 Prompt** —— 零新增基础设施, 已足够,
   为推荐默认;
2. **Windows Task Scheduler（`schtasks` / Register-ScheduledTask）一次性任务**:
   在窗口开启时刻运行一个非交互 wrapper（窗口核验 → 环境核验 → preflight → run →
   产物 SHA-256 清单 → 写执行报告; 无任何 retry）。该任务本身会发起 live 请求,
   其创建属于 live 授权行为, 必须经 CAO 明确授权并登记治理记录后方可创建。

## 6. Governance Change Requirement

若采纳延长窗口: **严禁直接修改 probe**。必须走:

```text
Current Window（00:30Z..01:00Z, 30 min）
      ↓
Window Change Proposal（本文件 §4 建议即为提案输入）
      ↓
Human / CAO Authorization（明确新的 start/end UTC）
      ↓
Frozen Configuration Update（唯一合法代码变更 = EXECUTION_WINDOW_UTC 常量
  + selftest 守卫样本时间戳同步, 沿 6e7192b/9512d5e 先例; 阈值/状态机零改动;
  独立分支 + 提交 + 归档）
      ↓
Execution（按 §5 管线）
```

确认: **需要新的治理变更记录**（Window Change Proposal 的 CAO 批准记录 + 登记提交 +
归档条目）, 不得沿用本审查文档作为变更授权本身。

## 7. Exact Preconditions for char-001

1. CAO 已授权且已冻结登记的窗口（start/end UTC）, probe 冻结常量与其一致;
2. runtime 核验 `current_utc >= start AND current_utc <= end`（以脚本冻结窗口为最终依据）;
3. 分支 `work/phase4/char-001-execution` 工作树干净, HEAD 为已审查提交;
4. `openai` 可导入 + `DEEPSEEK_API_KEY` 在位（不输出值）+ selftest 19/19;
5. `preflight --run-id char-001` PASS（任一 gate 失败即 STOP 并存证）;
6. `run --run-id char-001`（冻结状态机; 不 retry / 不 backoff / 不人工干预）;
7. 三产物存在于 `data/characterization/char-001/`, 可解析, run-id 一致, 记录数与
   状态机执行一致, SHA-256 已登记;
8. `CHAR001_LIVE_EXECUTION_REPORT.md` 生成（含 No causal conclusion 声明）→ STOP。
9. 附加: **run 必须在窗口开启时刻立即启动**（名义路径 ≈ 30.7 分钟, 晚启动会放大
   边界碰撞风险）。

## 8. Explicit Statement

```text
No live request was performed during this review.
```

本审查全程零网络请求、零 probe/protocol/阈值/窗口修改、零证据产物创建、
未声称 char-001 完成; 未进入 Evidence Review / CAO Decision / R4 / Phase 4.3。

---

## STOP

```text
Phase 4 Execution Window Review
        COMPLETE
              ↓
        Human Review
              ↓
   Window Authorization
              ↓
       Scheduled Execution
```
