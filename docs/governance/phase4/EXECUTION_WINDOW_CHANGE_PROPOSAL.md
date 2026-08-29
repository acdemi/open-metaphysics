# Phase 4 — Execution Window Change Proposal

> **STATUS: PROPOSAL ONLY — NO EXECUTION / NOT AUTHORIZED**
> 本文档仅为治理提案。**不假定新窗口已获授权**; 新窗口的具体 start/end 必须由人工 CAO
> 明确指定后方可进入 Freeze Update。
> **提案输入**: `EXECUTION_WINDOW_REVIEW.md`（`ade5bb9`, 代码时序级审查）
> **当前冻结窗口**: `2026-08-30T00:30:00Z .. 2026-08-30T01:00:00Z`（30 min, `9512d5e`）
> **硬约束遵守**: 本提案起草全程零 live 请求 / 零 preflight / 零 run / 零代码修改。

---

## 1. 当前 30 分钟窗口为什么结构性不足

以下数字全部来自冻结实现代码时序（`execute()` / `_run_fixed_density` /
`_run_condition_d` / `_recovery_observation`）, 非估算猜测:

| 构成 | 冻结语义 | 最短耗时 |
|------|----------|----------|
| A | 20 req × 30s（sleep 仅在请求之间, 时延挤占间隔） | 19×30 = 570s |
| Q0 跨条件静默 | `if idx > 0` —— **A→B、B→C、C→D 共 3 次**（此前估算遗漏项） | 3×300 = 900s |
| B | 40 req × 5s | 39×5 = 195s |
| C | 60 req × 1s（streak≥N=5 提前停） | ≥ 59s |
| D（C clean → SUSTAINED_STRESS_C_DENSITY） | 120 req × 1s | 119s |
| D（C trigger → RECOVERY_FLOW） | D1: 15 探测×60s 间隔; D2: 10×(5s+req) 确认 | ≤ 840s + 50s + 时延 |
| 中段恢复 | A 或 B 触发停止规则后立即插入 §6 恢复观测 | ≤ 845s/次 |
| preflight（独立命令） | G1–G3, 1 GET, timeout 15s | 秒级 |

**nominal success duration（全成功、时延趋零的理论下限）**:

```text
570 + 900 + 195 + 59 + 119 = 1843s ≈ 30.7 分钟
（现实值含 preflight/启动/落盘 ≈ 31 分钟）
```

**名义路径已超过 30 分钟窗口** —— 不存在任何"顺利跑完"的场景。窗口内启动的完整 run
必然产生窗外请求（违反 §0）或被中途截断（产生部分证据）。**结构性不足 = 与参数取值、
端点健康度无关, 由冻结状态机自身的时序决定。**

## 2. 为什么建议 2 小时窗口

**fast failure duration（快速失败路径上界, 无挂起）**:

```text
单条件停止+中段恢复+其余名义:   125+845+300+195+300+59+300+119 ≈ 2288s ≈ 38.1 min
双连停 ABORTED（A、B 连续停止）: 125+845+300+25+845             ≈ 2140s ≈ 35.7 min
C 停止且 D 恢复无望:            570+300+195+300+~20+300+840+15L ≈ 2525s ≈ 42.1 min
→ fast failure 上界 ≈ 42 分钟（规划取 45 min）
```

**slow failure risk**: 探测调用未显式设置 timeout → openai SDK 默认 600s/次 ×
SDK 级重试 ≤2 → **单次挂起请求最坏 ≈ 30 分钟**, 快速失败路径上叠加 1–2 次挂起即
+30–60 分钟, 无可靠短时上界（此为冻结实现现状, 本提案不改动它, 见 §4/§9）。

**推荐 2 小时的理由**:

| 维度 | 30 min | 60 min | **120 min（推荐）** | 240 min |
|------|--------|--------|---------------------|---------|
| 对 nominal（31 min）裕度 | **−0.7（负）** | +29 | **+89** | +209 |
| 对 fast-fail UB（42 min）裕度 | 负 | +18（偏薄） | **+78** | +198 |
| 吸收慢速挂起能力 | 0 | ≈1 次 | **≈2–3 次** | ≈5+ 次 |
| 边界碰撞风险 | 必然 | 中 | 低 | 极低 |
| 授权暴露时间 | — | 短 | 适当 | 过长（收益递减） |

60 分钟仅勉强覆盖 fast-fail 上界、无挂起吸收能力; 240 分钟授权暴露过长而请求总量
不变（冻结矩阵封顶 ≈ 241 请求 + ≤30 恢复探测, **窗口加长不增加请求量**, 只增加
容错时间）。120 分钟为裕度与治理暴露的最佳平衡点。

## 3. 新窗口所需最小安全裕度

```text
minimum safe window ≥ fast-fail UB(45) + 吸收 1 次挂起(10) + preflight/落盘/审计(10~15)
                    ≈ 65–70 分钟   →  即相对 nominal(31) 的最小裕度 ≈ +35–40 分钟

recommended window  = 120 min
recommended margin  = 120 − 31 ≈ +89 min（nominal 口径）
                      120 − 45 ≈ +75 min（fast-fail 口径）
```

低于 65–70 分钟的任何窗口都不满足"一次完整 run + 一次异常吸收"的最低安全要求。

## 4. 为什么不能通过压缩冻结实验逻辑解决

1. **协议冻结**: 矩阵 A/B/C/D 的 interval/count、Q0、T_max、N、S1–S4 判定式均为
   2026-08-25 人工冻结值（源码标注 DO NOT MODIFY; 协议 §5「运行前冻结, 不得事后
   解释」）。压缩 interval/Q0 = 修改实验本体, 等于用另一组参数冒充 char-001,
   产物将不可与协议对账, Evidence Review 必然拒绝。
2. **测量有效性**: A/B 的密度（30s/5s/1s）是"request 密度分档"的自变量本身;
   压缩间隔即改变被测条件, 表征结果失去对 R/R2/R3 历史数据的可比性。
3. **D 恢复语义**: Q0 静默与 60s 恢复探测间隔是恢复现象的观测尺度, 压缩后
   recovery_latency 的口径改变, S4（≤Z=60s）判定失效。
4. **治理先例**: 窗口变更走"登记常量 + selftest 样本同步"的最小 diff（`6e7192b`/
   `9512d5e` 先例）, 从不触碰实验逻辑; 任何实验逻辑变更须独立 ACP + 重新离线验证。

## 5. 为什么 Scheduled Wake 属于编排层而不是 probe 层

- **probe 层** = 冻结状态机 + 守门 + 判定式 + 产物写入器; 其正确性已在离线验证
  （selftest 19/19, dry-run 全状态机, 窗口守门正确拒绝窗外启动）, 且**与"何时被
  触发"无关**——它只在被调用时对 `current_utc` 做一次二值判定。
- **编排层** = 决定"何时有人/何物去触发它"。四次历史失败（窗口过期、占位符、
  窗口前假完成、时间门禁 STOP）全部发生在这一层: 会话由人工在任意时刻发起,
  而 **Prompt 无法在未来时刻自我唤醒**。
- 因此补救措施（日历提醒 / 计划任务）不触碰 probe 任何一行代码, 属于纯编排治理;
  两层失败记录在治理上必须分开记账, 不得以编排失败否定 probe 正确性, 反之亦然。

## 6. 人工日历唤醒 vs OS 一次性计划任务: 治理差异

| 维度 | 人工日历唤醒（推荐默认） | OS 一次性计划任务 |
|------|--------------------------|-------------------|
| 触发者 | 人在窗口开启时刻手动下发执行 Prompt | 机器在预定时刻无人值守触发 |
| live 授权语义 | 每次执行天然伴随人的一次明确指令 | **创建动作本身即预先授权机器发起 live 请求** |
| 基础设施成本 | 零 | 需新增 wrapper + 任务登记 |
| 失控面 | 无（人不发即不跑） | 存在（陈旧/错误任务可能在授权外触发） |
| 治理记录 | 常规归档 | 必须登记: 命令行、frozen commit 哈希、run-id、窗口、失败行为（停止+存证, 无 retry） |

## 7. 若采用 OS scheduled task, 为什么创建动作必须单独获得 live authorization

1. 创建即**委托**: 任务将在无人确认的情况下于未来时刻自动发起 preflight（1 GET）
   与 run（≈241+ 请求）。这等价于把 live 授权预先签署给一台机器。
2. **时效绑定**: 授权必须绑定具体窗口（start/end）+ 具体 frozen commit 哈希 +
   run-id; 否则任务可能在窗口变更/代码变更后于错误时刻、以错误版本触发。
3. **失败行为预绑定**: 无人值守时必须预先声明失败策略（任何 gate 失败 → 停止 +
   保存证据 + 退出; 无 retry/backoff/重试调度）, 否则自动化会引入协议禁止的
   重试倾向。
4. 因此"创建任务"这一动作本身就是一次 live 授权事件: 须独立 CAO 批准 + 治理记录,
   不得随窗口变更一并默认通过。**本提案不创建任何计划任务。**

## 8. 新窗口变更需要修改的冻结配置（最小 diff, 沿 `6e7192b`/`9512d5e` 先例）

1. `scripts/infra_probe.py` 中 `EXECUTION_WINDOW_UTC` 常量（含来源注释更新）;
2. selftest 窗口守卫样本时间戳（与新窗口绑定, 否则 selftest 必破）;
3. 独立分支提交 + 归档登记。
（除此之外无任何合法改动面。）

## 9. 绝对不能修改的配置

```text
X=90 / Y=3 / Z=60 / W=5 / Q0=300 / T_max=900 / N=5        （冻结阈值, S1–S4 判定式）
conditions A(30s×20) / B(5s×40) / C(1s×60) / D(flow)       （矩阵与密度自变量）
状态机顺序 A→B→C→D 与 C→D 分支（RECOVERY_FLOW / SUSTAINED_STRESS_C_DENSITY）
17 字段 request record 与 result 判定式（success ≡ judge_mode=="deepseek" 且 JSON 解析成功）
no retry / no backoff 语义
RECORD_KEYS / 产物三件套格式（manifest.json / records.jsonl / results.json）
协议文档与其 §5 冻结记录
```

另注（独立 ACP 事项, 不随本窗口变更捆绑）: probe 未显式设置请求 timeout 依赖 SDK
默认值, 是 slow-fail 无上界的根源; 若未来要显式设 timeout, 属于 probe 行为变更,
须独立 ACP + 重新离线验证, **不得在本窗口变更中夹带**。

## 10. 完整门控链

```text
Execution Window Change Proposal（本文档, PROPOSAL ONLY）
      ↓
Human / CAO Decision（明确批准新窗口的具体 start/end UTC; 可采纳/修改/否决本提案）
      ↓
Freeze Update（独立分支: 仅 §8 两处最小 diff; selftest 19/19 复验; 提交 + 归档;
               若采用 OS task, 此处附单独的 live-authorization 治理记录）
      ↓
Pre-Execution Readiness（分支/工作树审计; openai / API key / selftest; 零请求）
      ↓
Scheduled Wake（人工日历默认; OS 任务仅在被单独授权时）
      ↓
Window Verification（runtime: current_utc ∈ [start, end], 以冻结常量为最终依据）
      ↓
Preflight（G1–G3; 失败即 STOP 存证）
      ↓
Live Run（--run-id char-001; 冻结状态机; 窗口开启即刻启动以用满裕度）
      ↓
Artifact Audit（三产物存在/可解析/run-id 一致/记录数一致/SHA-256; git 状态审计）
      ↓
Execution Report（CHAR001_LIVE_EXECUTION_REPORT.md; 无因果结论声明）
      ↓
STOP → 人工 Evidence Review → （如批准）R4 Authorization
```

---

## 汇总计算表

| 项 | 值 |
|----|-----|
| nominal success duration | **≈ 30.7 min**（1843s; 现实 ≈31 min）—— 已超当前窗口 |
| fast failure duration（上界, 无挂起） | **≈ 42 min**（规划取 45; 情景 35.7 / 38.1 / 42.1） |
| slow failure risk | 无短时上界; 单次挂起 ≈ ≤30 min（SDK 默认 600s × ≤3 次尝试） |
| recommended window / margin | **120 min**; 裕度 +89 min（nominal 口径）/ +75 min（fast-fail 口径） |
| minimum safe window | ≈ 65–70 min（fast-fail UB + 1 次挂起 + 审计） |

## Explicit Statement

```text
No live request was performed during this proposal.
No frozen configuration was modified. No scheduled task was created.
This proposal does NOT authorize any window, execution, or review decision.
```

## STOP

本提案提交后立即 STOP, 等待人工 CAO Decision（批准 / 修改 / 否决新窗口）。
在获得明确授权与 Freeze Update 之前, 不执行任何 live 操作, 不修改窗口, 不创建
计划任务, 不进入 Evidence Review / R4 / Phase 4.3。
