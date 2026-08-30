# Phase 4 — CHAR002 Gap Disposition

> **文档类型**: 治理处置文档（GAP Disposition & Design —— 只读分析, 零 live 操作）
> **CAO 输入**: 「CHAR002 Evidence Accepted With Gaps」Decision（本对话, 2026-08-30）
> **依据**: `CHAR002_EVIDENCE_REVIEW.md`（`dc37bcb`）/ 两 run 执行报告 / 治理归档链
> **分支**: `work/phase4/char-001-execution`
> **硬约束**: 本文档起草全程零 preflight / 零 run / 零 API 请求; 未修改 probe、
> protocol、阈值、历史 artifacts、Knowledge Layer、R4/4.3 状态。

---

## 0. 总览与状态建议

| GAP | 内容 | 状态建议 |
|-----|------|----------|
| GAP-E1 | 表征主体变更（deepseek-chat → deepseek-v4-flash） | **UNRESOLVABLE / SUBJECT UNAVAILABLE** |
| GAP-E2 | 恢复路径不可观测（D1/D2/S4 未触发） | **UNOBSERVABLE UNDER CURRENT CHARACTERIZATION** |
| GAP-E3 | char-001 零矩阵样本 | **CLOSED**（baseline 由 char-002 满足; char-001 保留为事件证据; 不合并数据） |

---

## 1. GAP-E1 — 主体变更

### 1.1 当前证据

- char-002 全部 240 行记录的 `model` 字段与 G2 快照均为 `deepseek-v4-flash`;
  证据集中**不存在任何** deepseek-chat 的表征数据点（NOT OBSERVED）。
- char-001 的唯一请求（model=deepseek-chat 时段）返回 HTTP 402 计费错误——
  这是计费状态证据, **不是**模型可用性证据。
- **模型目录观察（一次性, 已记录）**: 2026-08-30 ~08:04Z（char-002 预检前, 授权窗口内）
  以 `GET /models` 对 `https://api.deepseek.com` 做过一次只读枚举, 返回目录为:
  `deepseek-v4-flash` / `deepseek-v4-flash-vision-exp` / `deepseek-v4-pro`。
  **`deepseek-chat` 不在该目录中。**（该次调用系模型替换前的环境核验, 此后未再请求;
  目录为时点观察, 非持续性状态声明。）

### 1.2 能否通过 CHAR003（Original Subject Characterization）关闭？

**不能（当前时点）**。理由:

1. CHAR003 的前提是原主体可执行; 目录观察显示 `deepseek-chat` 不在提供方当前
   模型列表中 → 原主体不可达。
2. 按 CAO Decision §二: 主体不可用时「不要模拟、替代或推断」——不得以 v4-flash
   冒充、不得以任何 alias 重试、不得推断"chat 已下线所以历史事件主体作废"。
3. 也不得为"验证 chat 是否真的下线"而反复探测 API——每次探测都是 live 请求,
   且不产生表征价值, 未获授权。

### 1.3 状态建议与重开条件

```text
GAP-E1 = UNRESOLVABLE / SUBJECT UNAVAILABLE
重开条件: 提供方目录（经授权的 GET /models 或提供方公告）再次列出 deepseek-chat,
          且 CAO 批准 CHAR003 提案。
```

登记义务（延续）: 任何报告中不得将 `deepseek-v4-flash` 与 `deepseek-chat` 静默等同;
不得将 CHAR002 改写为 "deepseek-chat characterization"。

## 2. GAP-E2 — 恢复路径不可观测

### 2.1 当前证据

- char-002: 240/240 success, 零失败记录 → 冻结触发条件（N=5 连续失败 /
  认证计费中止）全程未满足 → D1（恢复探测）/ D2（恢复确认）/ S4（recovery ≤ Z=60s）
  均为 NOT TRIGGERED / NOT OBSERVABLE。
- 该结果为**符合性正确输出**（零失败时状态机正确走 clean 分支）, 非执行缺陷。

### 2.2 是否存在合法可观测路径？

逐项核对 CAO Decision §三的四问:

| 问题 | 分析 |
|------|------|
| 1. 合法、可重复的触发条件是否存在？ | 冻结协议内的触发条件只有**真实失败**（连接类连败或计费中止——后者直接全局终止, 反而关闭观测）。失败的发生不由实验者控制。 |
| 2. 能否在不修改冻结协议的情况下观察 recovery path？ | 能——但仅以**有机方式**: 任何未来授权 run 天然携带恢复观测仪器; 一旦出现真实失败, D1/D2/S4 自动积累数据, 无需任何协议改动。 |
| 3. 是否存在不人为制造故障的测试方式？ | 在冻结协议内**不存在**。协议无故障注入机制; 注入（代理劫持/DNS 操纵/自我限流/假端点）= 修改实验传输路径 = probe/protocol 变更 + 人为制造未授权故障, 双重违反。 |
| 4. 是否需要新的 CAO live authorization？ | 若未来设计独立的「Recovery Characterization / Trigger Validation」协议（受控故障注入类）, 则属于**新协议提案**, 需独立 ACP 级评审 + CAO 授权, 完全在当前冻结体系之外。 |

### 2.3 状态建议

```text
GAP-E2 = UNOBSERVABLE UNDER CURRENT CHARACTERIZATION（正式保留结果）
登记义务: 不得将 D1/D2 NOT TRIGGERED 解释为 recovery successful /
          system never requires recovery; 其唯一含义是观测期内冻结触发条件未满足。
重开条件: 未来授权 run 中出现真实失败（自动积累 S4 证据）, 或 CAO 批准独立的
          受控恢复表征协议提案。
```

## 3. GAP-E3 — char-001 零矩阵样本

### 3.1 当前证据

- char-001: 1 请求 → HTTP 402 → 协议全局中止; 零矩阵样本; 产物与报告已入库
  （`d9dcdf5`）, 保留完好。
- char-002: 完整冻结矩阵 240 请求（A20/B40/C60/D120）, 独立 run-id、独立产物、
  独立 provenance（`c175a9f`）。计费阻塞已由人工解除（CAO 声明）。

### 3.2 是否需要重新执行？

**不需要**, 两层理由:

1. **v4-flash 主体**: 完整 baseline 已由 char-002 提供; 重跑（同配置）仅为重复性
   观测, 不关闭任何 GAP, 亦非本决策所要求。若 CAO 未来需要重复性证据, 见 §5
   可选项（独立提案 + 新授权）。
2. **deepseek-chat 主体**: 重跑被 GAP-E1 阻断（主体不可用）; 若强行以其他模型
   重跑并沿用 char-001 之名, 只会制造 provenance 矛盾（参见被否决的重跑指令处置）。

**禁止事项（重申）**: 不得将 char-001 与 char-002 数据拼接成"完整矩阵";
不得覆盖/改写 char-001 历史产物; char-001 的身份 = 计费阻塞事件证据。

### 3.3 状态建议

```text
GAP-E3 = CLOSED
理由: 完整矩阵 baseline 已由 char-002 独立满足（当前主体口径）; char-001 作为
      阻塞事件证据原样保留; 数据不合并; 无重跑需求。
备注: 若未来 GAP-E1 重开（deepseek-chat 恢复可用）, 其原主体 baseline 需求
      随 GAP-E1 一并重开, 届时方可讨论原主体 rerun。
```

## 4. 若需新 run 的 Execution Plan（模板, 当前无一被授权或排期）

当前**无任何必需的新 run**。仅登记可选项供未来 CAO 参考:

### 可选项 O-1 — char-003-replication（v4-flash 重复性观测, 可选, 未推荐为必需）

- 目的: 为 char-002 的 240/240 观察提供重复性参照（repeatability, 非因果）。
- 方案: 冻结 probe/protocol/阈值原样; 新 run-id `char-003`; 模型维持
  `deepseek-v4-flash`（或 CAO 另行指定）; 新冻结窗口（沿用 2h 建议）; 独立产物
  `data/characterization/char-003/`; 与 char-002 独立保存、独立报告、不合并。
- 前置: 新 CAO live authorization（窗口授权 + freeze update 提交 + 归档）。
- 预计: preflight 1 GET + 矩阵 240 请求 + 3×Q0, wall ≈ 31 min（nominal）。

### 明确不立项

- CHAR003「原主体表征」: 主体不可用（GAP-E1）, 不设计、不模拟、不替代。
- 受控故障注入式恢复表征: 超出冻结体系, 须独立协议提案, 当前不提出。

## 5. 新 run 不得修改冻结 Protocol（不变式清单, 对任何未来 run 生效）

```text
阈值 X=90 / Y=3 / Z=60 / W=5 / Q0=300 / T_max=900 / N=5 —— 不可修改
矩阵 A(30s×20) / B(5s×40) / C(1s×60) / D(flow) 与 A→B→C→D 顺序 —— 不可修改
17 字段 record schema / result 判定式 / 三产物格式 —— 不可修改
no retry / no backoff / 窗口守门 —— 不可修改
唯一合法变更面: EXECUTION_WINDOW_UTC（+ selftest 样本同步）与 CAO 明确指定的
模型/endpoint 替换（沿 f73b303 先例, 须逐字登记 provenance）
```

## 6. 需要新的 CAO live Authorization 的事项

1. 任何新 run（含可选项 O-1）: 窗口授权 + freeze update + run-id 指定。
2. 对 `GET /models` 或任何端点的再次访问（包括复核 GAP-E1 的目录状态）。
3. 模型或 endpoint 的任何再次替换。
4. 任何受控故障注入/恢复表征新协议的立项（属新协议提案, 非 live 授权本身）。

**当前已授权且仅已授权**: 本处置文档 + 归档更新。此外的一切 live 操作均未授权。

## 7. Explicit Statement

```text
No live request was performed during this disposition.
No causal, rate-limiting, capacity, or root-cause conclusion is made.
Observed Evidence ≠ Causal Explanation — 本文档仅登记观察事实与处置建议。
```

## 8. STOP

本文档提交即 STOP。不执行 preflight / live run / API 请求; 不修改 probe、
protocol、阈值、历史 artifacts; 不进入 R4、Phase 4.3、Knowledge Layer。
等待下一次人工 CAO Review。
