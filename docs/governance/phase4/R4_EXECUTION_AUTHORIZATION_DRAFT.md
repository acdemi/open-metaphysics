# R4 Execution Authorization — DRAFT（待人工 CAO 批准）

> **STATUS: DRAFT — NOT AUTHORIZED**
> 本文档为下一阶段人工 CAO Decision 的**草案**。在人工以明确语句
> `R4 EXECUTION AUTHORIZED` 批准并填定 §2 窗口等留白项之前, 本草案**不生效**,
> 不得执行任何 R4 操作。
> 前置: `CAO-P4-R4ADM-001`（R4 ADMISSION APPROVED）/ `R4_EXECUTION_PREP_AUDIT.md`

---

## 1. R4 Run ID

```text
R4（延续 R / R2 / R3 序列; 历史产物为外部 ACIS 归档, 本仓库仅存治理记录）
```

## 2. Execution Window UTC

```text
FROZEN per CAO-P4-R4EXEC-001（CAO 指令「晚上十二点」, 2h duration Option B）:
START = 2026-08-30T16:00:00Z   （当地 UTC+8 = 2026-08-31 00:00, 晚上十二点）
END   = 2026-08-30T18:00:00Z   （当地 UTC+8 = 2026-08-31 02:00）
约束: 全部 R4 请求必须落在 [START, END) 内; 窗口外请求 = 越权。
临近 END 未完成 → 按停止条件停止并保存已产生证据（runner 为 checkpointed）。
```

## 3. Model

```text
deepseek-v4-flash（严格固定）
禁止: deepseek-chat（SUBJECT UNAVAILABLE）/ 任何其他模型 / 自动 fallback /
      隐式替换。模型变更 = 准入失效 + 重新表征。
```

## 4. Endpoint

```text
https://api.deepseek.com（严格固定; 任何 endpoint 变更 = 准入失效）
```

## 5. Characterization Binding

```text
R4 subject（deepseek-v4-flash @ api.deepseek.com）
    == CHAR002 characterization evidence 的表征主体（c175a9f, 240/240）
绑定成立方可执行; 绑定断裂（模型/端点/目录变化）→ 本授权自动失效 → 重新表征 + 重新准入。
```

## 6. Allowed Requests

```text
R4 = Phase 4 ablation 完整 run, 与 R / R2 / R3 同构（216 judge 请求的冻结实验矩阵,
     ACIS harness 执行）。
允许: 且仅允许该矩阵的全部请求 + 实验固有开销（arm 间延迟等, 沿冻结实验设计）。
禁止: 额外请求 / 手工补测 / GET /models / retry / backoff / 重跑"修好"实验。
预检: R2/R3 先例（PREFLIGHT_PASS / STRESS_PASS 状态文件）是否沿用, 由人工在本节
      批准时明确。
```

## 7. Artifact Output Location

```text
R4 原始产物: 外部 ACIS 工作区, 沿用 R/R2/R3 既有结构
  （报告: ACIS/reports/phase4_2_r4_raw_results.json（命名沿先例）
   traces: ACIS/logs/phase4_2_r4/（沿先例）
   状态:   ACIS/phase4_2_r4_status.txt（沿先例））
—— 具体路径以人工批准时的钉死值为准（ACIS harness 不在本仓库, 本仓库无法代定）。
本仓库收录: 执行报告 docs/governance/phase4/R4_EXECUTION_REPORT.md
  + 产物 SHA-256 登记 + 关键计数字段的治理转录（原始产物不修改）。
```

## 8. Evidence Preservation Requirements

```text
每个 R4 request 必须落盘运行时实际值（强制, 消除 R2/R3 "运行期端点 UNKNOWN" 缺口）:
  model / base_url / timestamp(start/end) / condition(arm) / sequence /
  request outcome / exception 三要素（type/message/cause 链）/ 实验状态机必需字段。
原始产物一经写盘不得修改; run 完成后立即计算并登记 SHA-256;
governance 报告只转录事实, 不改写原始记录。
```

## 9. Stop Conditions（任一触发即停, 不重试）

```text
- 窗口外（临近 END 未完成 → 停止并保存已产生证据）
- 认证/计费类错误（401/402）
- 连通性/preflight 失败（若 §6 批准预检）
- unexpected configuration / missing dependency / API key 失效
- 任何协议不一致或未预期运行时行为
失败不得通过 retry / backoff / rerun "修好"。
```

## 10. Causal Interpretation

```text
执行阶段与报告阶段均禁止: 根因 / rate limiting / capacity / stability / SLA /
provider policy / infrastructure bottleneck 结论。
Observed Evidence ≠ Causal Explanation。
```

## 11. GAP-E1 Treatment

```text
维持 UNRESOLVABLE / SUBJECT UNAVAILABLE。R4 结果不得声称解决 GAP-E1;
不得将 R4（v4-flash 主体）与历史 deepseek-chat 事件主体作同主体比较结论。
```

## 12. GAP-E2 Treatment

```text
维持 UNOBSERVABLE UNDER CURRENT CHARACTERIZATION。
R4 期间若出现真实失败: 其恢复行为仅作事实记录, 不改变 GAP-E2 状态;
E2 重开条件以 CHAR002_GAP_DISPOSITION.md 为准。
NOT TRIGGERED ≠ SUCCESSFUL RECOVERY（持续有效）。
```

## 13. Phase 4.3

```text
LOCKED unless separately authorized。R4 执行授权不自动传导至 Phase 4.3。
```

## 14. Knowledge

```text
LOCKED。本授权与 Knowledge Layer / 7.2B 无关。
```

---

## 批准语句（已由人工 CAO 签发）

```text
R4 EXECUTION AUTHORIZED
批准人: 人工 CAO（本会话 CAO Decision 消息, Decision ID: CAO-P4-R4EXEC-001）
批准时间(UTC): 2026-08-30（会话内签发; 精确时刻以消息时序为准）
START: 2026-08-30T16:00:00Z    END: 2026-08-30T18:00:00Z    Run ID: R4
（窗口值按 CAO 指令「晚上十二点」填定 = 当地午夜 00:00 UTC+8; §1–§14 全部生效）
```

## STOP

本草案提交即 STOP。在收到人工 `R4 EXECUTION AUTHORIZED` 之前:
不执行 R4、不 preflight、不发送任何 API 请求、不修改任何冻结配置。
