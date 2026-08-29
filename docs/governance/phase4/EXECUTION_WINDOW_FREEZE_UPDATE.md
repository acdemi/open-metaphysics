# Phase 4 — Execution Window Freeze Update

> **文档类型**: 治理报告（AUTHORIZED CONFIGURATION UPDATE ONLY —— 已完成登记）
> **CAO 批准**: `EXECUTION_WINDOW_UTC = 2026-08-30T02:00:00Z .. 2026-08-30T04:00:00Z`
> **决策记录**: `EXECUTION_WINDOW_CHANGE_DECISION.md` · **冻结提交**: `567ec67`
> **分支**: `work/phase4/char-001-execution`（HEAD `48784b0`, 工作树干净）
> **验证时点 UTC**: 2026-08-29T17:08:26Z

---

## 1. 变更范围（步骤 1–3, 8）

`git status --short` = 干净; 冻结更新提交 `567ec67` 的 diff 审计确认**仅两处授权面**:

| 位置 | 变更 |
|------|------|
| `scripts/infra_probe.py` L71–77 | `EXECUTION_WINDOW_UTC` → `("2026-08-30T02:00:00Z", "2026-08-30T04:00:00Z")` + provenance 注释 |
| `scripts/infra_probe.py` selftest（L774–775） | 守卫样本同步: inside `03:00:00Z` / outside `05:00:00Z` |

**未改动（禁改清单逐项确认）**: X/Y/Z/W/Q0/T_max/N（show-config 逐项核对原值）、
retry/backoff 行为（实现本无）、状态机 A→B→C→D 及 C→D 分支、probe implementation
logic、protocol、output schema、artifact schema、Knowledge Layer、R4、Phase 4.3。

## 2. Offline Validation（步骤 4–5, 零网络）

| 检查 | 结果 |
|------|------|
| `python -m scripts.infra_probe selftest` | **ALL PASS**（exit 0, 19/19, 含同步后的窗口守卫样本） |
| `show-config` 窗口段 | `"2026-08-30T02:00:00Z", "2026-08-30T04:00:00Z"` ✅ |

## 3. 时间门禁三点验证（步骤 6, 离线函数调用, 零请求）

| 测试点 | 期望 | 实测 |
|--------|------|------|
| `2026-08-30T01:59:00Z`（window_before） | reject | **False** ✅ |
| `2026-08-30T03:00:00Z`（window_inside） | allow | **True** ✅ |
| `2026-08-30T04:01:00Z`（window_after） | reject | **False** ✅ |

边界语义（实测观察事实, 未做任何修改）: 闭区间 `[start, end]` ——
`02:00:00Z → True`, `04:00:00Z → True`。
当前时刻守门: `2026-08-29T17:08:26Z → False`（窗口开启前, run 将被 SystemExit 拒绝）。

## 4. Live Request 声明（步骤 7）

```text
ZERO live requests. No preflight. No run. No network access of any kind.
All verification used offline stdlib datetime comparisons only.
No automatic window waiting. No scheduled task created.
```

## 5. Provenance（步骤 9: 旧窗口 → 新窗口, 全链留痕）

```text
2026-08-27T02:00Z..06:00Z   原始窗口（EXPIRED; 520b12d 裁决否决续用）
  → 2026-08-30T00:00Z..00:30Z   首次再登记（6e7192b; 占位符阻塞解除）
  → 2026-08-30T00:30Z..01:00Z   CAO 整体后移 +30min（9512d5e）
  → 2026-08-30T02:00Z..04:00Z   本次 2h 扩展（567ec67; 30min 结构性不足,
      见 EXECUTION_WINDOW_REVIEW.md ade5bb9 + CHANGE_PROPOSAL 4d0cdef）
```

代码内 provenance: `scripts/infra_probe.py` L72–76 注释; 旧窗口值 `00:30Z..01:00Z`
仅存于该注释, 活动常量/show-config 均为新窗口（取代完成）。

## 6. 产物清单（步骤 10）

| 产物 | 提交 |
|------|------|
| `scripts/infra_probe.py` 冻结配置更新 | `567ec67` |
| `docs/governance/phase4/EXECUTION_WINDOW_CHANGE_DECISION.md` | `567ec67` |
| 本报告 `docs/governance/phase4/EXECUTION_WINDOW_FREEZE_UPDATE.md` | 本次提交 |
| 归档条目 | 本次提交 |

## 7. 最终状态

```text
Phase 4 Execution Window Freeze Update
        COMPLETE (frozen: 2026-08-30T02:00:00Z .. 04:00:00Z, 2h)
              ↓
        Offline Validation: ALL PASS
              ↓
        Time Gate: before=REJECT / inside=ALLOW / after=REJECT
              ↓
        STOP —— 等待执行窗口开启（人工唤醒; 无自动等待, 无计划任务）
```

窗口开启前: 不得 preflight / 不得 run / 零 live request。
窗口开启后: 由人工发起 char-001 执行指令（preflight → run → 产物审计 → 报告 → STOP）。
R4: LOCKED。Phase 4.3: LOCKED。
