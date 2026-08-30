# Phase 4 — R4 Execution Preparation Audit（Tasks 0–4）

> **文档类型**: 治理准备审计（只读 + 提案, 零 live 操作, 零配置修改）
> **时点**: 2026-08-30 · **分支**: `work/phase4/char-001-execution`（HEAD `32f6f6c`）
> **上游**: CAO-P4-R4ADM-001（`c64a904`, R4 ADMISSION APPROVED / EXECUTION NOT AUTHORIZED）

---

## Task 0 — 状态与边界审计

| 项 | 结果 |
|----|------|
| HEAD / branch / working tree | `32f6f6c` @ `work/phase4/char-001-execution`, **干净** |
| `CAO-P4-R4ADM-001` 存在且一致 | ✅（`c64a904`; 含 "R4 = APPROVED (ADMISSION ONLY)"、Phase 4.3 "LOCKED unless separately authorized"、Knowledge LOCKED） |
| R4 状态 | **APPROVED (ADMISSION) — EXECUTION NOT AUTHORIZED** ✅ |
| Phase 4.3 / Knowledge | **LOCKED** ✅ |
| 未授权 R4 执行产物 | **无**（`data/characterization/` 仅 char-001、char-002） |
| live request | **ZERO**（本阶段全程零网络操作） |

## Task 1 — R4 Execution Configuration Audit（主体绑定）

绑定链（当前冻结配置 == char-002 实测执行值, 逐字一致）:

```text
R4 subject
    ↓  model = deepseek-v4-flash   （scripts/infra_probe.py L53, CAO 授权替换 f73b303）
deepseek-v4-flash
    ↓  endpoint = https://api.deepseek.com   （CONFIG L52）
api.deepseek.com
    ↓  == CHAR002 G2 快照实测执行值（manifest: base_url/model 逐字一致, c175a9f）
CHAR002 characterization evidence（240/240, 判定档 A/B PASS）
```

绑定**可证明** ✅。禁止项登记: 不得使用 `deepseek-chat`（SUBJECT UNAVAILABLE）/ 其他
模型 / 自动 fallback / 隐式替换——任何变更即 CAO-P4-R4ADM-001 准入失效。

## Task 2 — Frozen Protocol Integrity Audit

`git diff b1e352a..HEAD -- scripts/infra_probe.py` = **+14/−5, 仅三个授权面**:

| 变更面 | 授权 | 内容 |
|--------|------|------|
| 窗口常量 + provenance 注释 | 窗口治理链 | 现值 `2026-08-30T07:53Z..09:53Z`（char 执行窗口） |
| selftest 窗口守卫样本 | 窗口治理链必要同步 | `08:53Z`(内) / `10:53Z`(外) |
| model 字段 + provenance 注释 | CAO 指定（`f73b303`） | `deepseek-chat → deepseek-v4-flash` |

**未改动（逐项确认）**: 阈值 X=90/Y=3/Z=60/W=5/Q0=300/T_max=900/N=5;状态机
A→B→C→D 及 C→D 分支;no retry/backoff（实现本无, 未引入）;窗口机制本身;
artifact/record schema;Q0/N 语义。

**OBSERVED BASELINE ISSUE（只记录, 不修复）**: 探测/实验请求未显式设置 timeout,
依赖 openai SDK 默认（600s, SDK 级重试 ≤2）→ 慢速失败无短时上界。此为实现冻结
基线现状, R4 执行授权草案将其列为风险登记项, 本阶段不做任何修改。

## Task 3 — R4 Execution Window Proposal（PROPOSAL ONLY, 未冻结）

```text
Option A — 30 min : REJECTED
    Reason: 结构性不足（EXECUTION_WINDOW_REVIEW.md, ade5bb9: nominal 30.7 min 已超窗;
            失败/恢复路径 42–56 min;SDK timeout 无短时上界）

Option B — 2 hours : PROPOSED（非 Authorization）
    Reason: 容纳 nominal 执行（R4 同构 R/R2/R3:216 judge 请求, 按 char-002 实测
            ~3.7s/req 估算 ≈ 14 min 请求时间 + 实验开销）+ 恢复观测裕度 + 审计时间
```

边界登记: ① 本提案不修改 `EXECUTION_WINDOW_UTC`（该常量属 characterization probe,
R4 运行的是外部 ACIS harness——**R4 的窗口执行为程序性约束**, 由授权文档 + 人工
计时承担, 除非未来另行授权将窗口机制扩展至 R4 harness）; ② 具体 start/end UTC 必须
由批准授权的人工 CAO 明确指定。

## Task 4 — Execution Authorization Checklist

### Governance
- [x] R4 Admission approved（CAO-P4-R4ADM-001）
- [x] Protocol approved（阈值 2026-08-25 冻结）
- [x] Characterization evidence accepted（char-002, ACCEPTED WITH GAPS）
- [x] GAP-E1 disposition acknowledged（UNRESOLVABLE / SUBJECT UNAVAILABLE）
- [x] GAP-E2 disposition acknowledged（UNOBSERVABLE）
- [x] GAP-E3 closed

### Subject
- [x] model = `deepseek-v4-flash`（CONFIG 与 char-002 G2 逐字一致）
- [x] endpoint = `api.deepseek.com`
- [x] no fallback / no substitution（登记为执行禁止项）

### Runtime
- [ ] execution window explicitly authorized —— **待人工指定**（本阶段仅 PROPOSED 2h）
- [x] API key available（env:DEEPSEEK_API_KEY, len=35, 值未输出）
- [x] `openai` runtime dependency available（3.6.0, .venv）
- [x] working tree suitable for execution（干净, HEAD `32f6f6c`）
- [ ] run ID explicitly authorized —— 草案提议 `R4`（延续 R/R2/R3 序列）, 待批准

### Evidence（R4 每 request 必须落盘的运行时实际值）
- [ ] harness 侧字段核验 —— 由执行授权批准时确认: model / base_url / timestamp /
      condition(arm) / sequence / request outcome / exception 三要素 + cause 链 /
      状态机必需字段（**消除 R2/R3"运行期端点 UNKNOWN"缺口为强制设计项**）

### Safety
- [x] no retry / no backoff / no unauthorized request / no fault injection /
      no causal interpretation during execution —— 登记为执行硬约束

## STOP

准备审计完成即停止本阶段。执行授权草案见
`R4_EXECUTION_AUTHORIZATION_DRAFT.md`（DRAFT, 待人工批准）。
