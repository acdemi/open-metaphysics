# Phase 4 — CAO Execution Window Decision

> **文档类型**: 治理决策记录（Human CAO Decision）+ Freeze Update 登记
> **决策时点**: 2026-08-29（晚于 `4d0cdef` 提案）
> **决策依据**: `EXECUTION_WINDOW_CHANGE_PROPOSAL.md`（`4d0cdef`）+
> `EXECUTION_WINDOW_REVIEW.md`（`ade5bb9`）+ 治理归档链
> **分支**: `work/phase4/char-001-execution`

---

## 1. CAO Decision（人工裁定, 逐项登记）

1. **否决**继续使用当前窗口 `2026-08-30T00:30:00Z .. 01:00:00Z`。
2. **批准** Phase 4 char-001 execution window 扩展为:

```text
AUTHORIZED EXECUTION WINDOW (FROZEN):
  START = 2026-08-30T02:00:00Z
  END   = 2026-08-30T04:00:00Z
  DURATION = 120 minutes
```

3. 本授权**仅针对 execution window governance change**。
4. **不授权**: 修改 probe logic / protocol / X,Y,Z,W,Q0,T_max,N / 实验状态机 /
   Knowledge Layer; 进入 R4; 进入 Phase 4.3; 任何 causal interpretation。
5. **Scheduled Wake**: 优先人工日历/人工唤醒; **不授权创建 OS scheduled task**;
   代理不得声称自己能够在未来自动唤醒。
6. 门控链: Window Change → Freeze Update → Offline Validation → STOP。
7. 新窗口真正开启前: 不得 preflight / 不得 run / 零 live request。

## 2. Freeze Update（已执行, 最小 diff）

| 文件 | 变更 | 性质 |
|------|------|------|
| `scripts/infra_probe.py` L71-77 | `EXECUTION_WINDOW_UTC` → `("2026-08-30T02:00:00Z", "2026-08-30T04:00:00Z")` + 完整 provenance 注释 | CAO 明确授权的唯一配置变更 |
| `scripts/infra_probe.py` selftest 窗口守卫样本 | inside `2026-08-30T03:00:00Z` / outside `2026-08-30T05:00:00Z`（与新窗口绑定的必要 fixture 同步） | 必要同步（否则 selftest 必破） |

**Provenance 链（窗口取代顺序, 全部留痕）**:

```text
2026-08-27T02:00Z..06:00Z（原始, EXPIRED, 520b12d 裁决）
  → 2026-08-30T00:00Z..00:30Z（6e7192b, 占位符阻塞解除后首次登记）
  → 2026-08-30T00:30Z..01:00Z（9512d5e, CAO 整体后移 +30min）
  → 2026-08-30T02:00Z..04:00Z（本次, 结构性不足被 ade5bb9/4d0cdef 证实, CAO 批准 2h）
```

旧窗口 `00:30Z..01:00Z` 已被取代: 代码中仅存于 provenance 注释（L75）,
活动常量与 show-config 输出均为新窗口。

## 3. Offline Validation（全部通过, 零请求）

| 检查 | 结果 |
|------|------|
| `python -m scripts.infra_probe selftest` | **ALL PASS**（19/19, 含新窗口守卫样本 03:00Z 内 / 05:00Z 外） |
| `show-config` 窗口段 | `"2026-08-30T02:00:00Z", "2026-08-30T04:00:00Z"` ✅ |
| 冻结阈值逐项核对 | X=90 / Y=3 / Z=60 / W=5 / Q0=300 / T_max=900 / N=5 ✅ **未动** |
| 状态机 / 判定式 / record schema | 零改动 ✅ |
| 旧窗口残留 | 仅 provenance 注释 ✅ |
| diff 范围 | 仅 §2 表列两处 ✅（`git diff` 审计） |

## 4. 执行前置状态与 Scheduled Wake

- 环境就绪（本治理链早前已验证）: `openai==3.6.0` / `DEEPSEEK_API_KEY` 在位（不输出值）。
- **唤醒方式**: 人工日历/人工唤醒（CAO 决策第 5 条）; 无 OS 计划任务;
  代理无未来自动唤醒能力——**须由人在窗口开启（`02:00:00Z`）后发起执行指令**。
- 建议窗口开启即刻启动 preflight + run（名义路径 ≈ 30.7 min, 2h 窗口裕度 +89 min;
  越早启动, 异常吸收空间越大）。
- 窗口开启前: 零请求（preflight 亦属 live 边界）。

## 5. Explicit Statement

```text
This decision record authorizes ONLY the execution-window configuration change.
No live request was performed. No preflight, no run, no char-001 execution.
Probe logic, protocol, thresholds, and state machine are UNCHANGED.
R4: LOCKED. Phase 4.3: LOCKED. Evidence Review: pending future artifacts.
```

## STOP

Freeze Update 与 Offline Validation 完成, 即刻 STOP。等待人工在
`2026-08-30T02:00:00Z .. 04:00:00Z` 窗口内发起 char-001 执行指令。
