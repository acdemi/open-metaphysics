# Phase 4 Infrastructure Characterization Protocol（基础设施表征协议）

> **模式**: 协议设计 Sprint（DESIGN ONLY）
> **状态**: ⏸ **DESIGN READY — 待人工 Protocol Review 与授权执行。本 Sprint 未执行任何 live 实验。**
> **日期**: 2026-08-25
> **分支**: `work/phase4/infra-characterization-protocol`
> **前置文档**: `docs/governance/phase4/INFRASTRUCTURE_INCIDENT_RECORD.md`（R/R2/R3 事件链, OPEN）
> **硬约束（本 Sprint 及未来执行均适用）**:
> - ❌ 本 Sprint 不发起任何 real network 请求
> - ❌ 不调用 DeepSeek API（任何端点）
> - ❌ 不修改现有实验代码
> - ❌ 不推断架构性能结论
> - ✅ 仅设计测量协议与成功/失败标准

---

## 0. 目标与根因边界声明

**本协议的目标**：

```text
characterize failure conditions
```

**本协议明确不做的事**：

```text
prove rate limiting
```

- 全部既有事实中**不存在任何 429/rate-limit 证据**（Incident Record §3 FACT：三次运行失败均为连接层异常）。
  本协议不预设、不验证、不宣布任何 rate-limit 结论。
- 协议执行前后的治理状态保持不变：
  `Root Cause: NOT ESTABLISHED` / `Construct Validity: NOT ESTABLISHED` / `Infrastructure Incident: OPEN`。
- 测量对象是**评估基础设施的传输层行为**（请求密度 ↔ 故障的关系），不是 ACIS agent 能力，
  不产出任何架构层面的性能结论。
- 执行产出的陈述类型仅限两种：某密度条件下观察到的事实（OBSERVATION），
  以及预冻标准的满足与否（PASS/FAIL）。

## 1. 测量单位定义（Per-Judge-Request Record）

每一条 Judge/probe 请求必须完整记录以下字段，缺一即视为该次测量数据无效：

| # | 字段 | 类型 | 定义与记录规则 |
|---|------|------|----------------|
| 1 | `request_id` | string | run 内唯一, 格式 `{run_id}-{seq:04d}` |
| 2 | `run_id` | string | 一次 characterization run 的标识（如 `char-001`） |
| 3 | `condition_id` | enum | `A` / `B` / `C` / `D`（归属实验矩阵单元） |
| 4 | `timestamp_start` | ISO8601 UTC | 请求发出时刻 |
| 5 | `timestamp_end` | ISO8601 UTC | 请求返回（成功或异常落地）时刻 |
| 6 | `base_url` | string | **调用时刻实际生效值**, 从 env/client 配置读取后落盘（关闭 R2/R3 端点 UNKNOWN 缺口） |
| 7 | `model` | string | 同上, 实际解析后的 model id |
| 8 | `judge_mode` | enum | `deepseek` / `rules`（调用结果回读） |
| 9 | `success/failure` | enum | `success` ≡ `judge_mode == "deepseek"`（LLM 返回且 JSON 解析成功）; `failure` ≡ 异常触发 rules fallback。判定式在运行前冻结, 不得事后调整 |
| 10 | `exception_type` | string\|null | `type(exc).__name__`, 无异常为 null |
| 11 | `exception_message` | string\|null | `str(exc)`, 无异常为 null |
| 12 | `exception_cause` | string\|null | `exc.__cause__` 链的 repr（截断至 500 字符）, 无异常为 null（关闭 R 诊断"子因未捕获"缺口） |
| 13 | `elapsed_seconds` | float | end − start |
| 14 | `inter_request_interval` | float | 本请求 `timestamp_start` 与前一请求 `timestamp_start` 之差（start-to-start 口径, 秒） |
| 15 | `rolling_requests_per_minute` | object | 尾随滚动窗口计数 `{ "1min": n, "5min": n, "10min": n }`, 按 `timestamp_start` 归属窗口 |
| 16 | `cumulative_request_number` | int | run 内 1-based 累计序号 |
| 17 | `consecutive_failures` | int | 截至本请求的连续 failure 计数, success 时清零 |

JSON 示例（字段口径见附录 A）。

## 2. Probe 设计原则（synthetic probe, 非正式实验）

- probe 使用**固定的最小合成 payload**, 不使用真实 challenge case, 不经过 agent 编排;
- 但**传输参数与 Judge 路径完全一致**：同一 base_url/model/temperature(0.1)/
  response_format(json_object)/timeout(SDK 默认)/retry(SDK 默认), 以保证测的是同一基础设施面;
- 严格串行, 单进程, 无并发;
- 未来实现必须是**全新独立脚本**, 不修改现有实验代码（`run_phase4_2_real_agent.py` 等）;
  实现本身属新的授权事项, 本 Sprint 不产出任何代码。

## 3. 运行前置门禁（Preflight Gate）

任一门禁失败 → 整个 run 取消, 不进入任何 Condition:

| 门禁 | 内容 | 通过判据 |
|------|------|----------|
| G1 | 对选定 endpoint/model 各发 1 次连通+计费探针 | HTTP 2xx 且非 402/401（承 R 诊断 remediation 建议） |
| G2 | 配置快照入 run manifest: base_url/model/key 来源/env 代理变量状态/进程启动命令 | 快照完整落盘 |
| G3 | 时段登记: run 开始/结束 UTC 时间戳 | 写入 manifest |

## 4. 实验矩阵（按 Judge request 密度划分, 非墙钟 case 时间）

| Condition | 描述 | 请求间隔 (start-to-start) | 请求总数 | 目标 | 预期观察 |
|-----------|------|---------------------------|----------|------|----------|
| A | 低密度基线 | 30 s | 20（≈10 min） | 基线 | 100% success 预期 |
| B | 中密度（接近阈值） | 5 s | 40 | 接近阈值 | 部分失败可接受 |
| C | 高密度（超过阈值） | 1 s | 60 | 超过阈值 | 观察失败模式 |
| D | 持续高密度 → 恢复测试 | 见 D 流程 | 见 D 流程 | 恢复测试 | 观察恢复行为 |

- 滚动窗口大小对**所有条件统一**为 1 / 5 / 10 分钟三档, 由 §1 字段 15 强制记录,
  不随条件变化（窗口是记录维度, 不是条件变量; 条件变量只有请求间隔）。
- 执行顺序固定 A → B → C → D, 相邻 Condition 之间静默 300 s（无任何请求）,
  使各条件起始状态可比。

### D 条件流程细化

```text
D0  停止间隔     C 终止后静默 Q0 = 300 s（无任何请求）
D1  恢复探测     以 60 s 间隔单发 probe, 上限 T_max = 900 s
                 首次 success 即刻记录 recovery_latency =
                     该 success 的 timestamp_end − C 最后一次 failure 的 timestamp_end
D2  恢复确认     恢复后以 B 密度（5 s）连发 10 次
                 ≥ 9/10 success ⇒ 判定 stable_recovery
```

- 若 C 未触发任何失败（未达故障区）: D 改为「C 密度持续 120 请求」的持续压测观察,
  D1/D2 记为 `NOT_TRIGGERED`（这本身是有效结论：该密度下未复现故障）。

## 5. 成功标准（运行前冻结, 不得事后解释）

| 编号 | 标准 | 建议默认值 | 适用范围 |
|------|------|------------|----------|
| S1 | LLM success rate ≥ **X%** | X = 90% | A、B（稳定区间候选密度） |
| S2 | maximum consecutive failures ≤ **Y** | Y = 3 | A、B |
| S3 | **no permanent failure window**（定义为: 不存在延伸至该条件结束的后缀连续失败段 ≥ W, W = 5） | W = 5 | A、B |
| S4 | recovery latency ≤ **Z seconds** | Z = 60 | D |

**冻结规则**:

1. 上表数值当前均为 PROPOSED。首次 live run 开始前, 必须将最终值写入本文件
   「§5-A 冻结记录」小节（含日期与批准人）, 自此**不可修改**;
2. **禁止运行后根据数据解释稳定性**——判定只允许引用冻结时的公式与阈值原文;
   若数据显示阈值不合理, 唯一合法路径是：本次 run 判 INCONCLUSIVE → 修订协议 → 重新评审 → 新 run;
3. C 是失败模式观察条件, **不以 S1–S4 判定通过/失败**;
   其成功标准是数据完整性（每条记录 17 字段齐全, 异常三要素 type/message/cause 非空可解析）。

### §5-A 冻结记录（待 Protocol Review 填写）

```text
X = ____ %    Y = ____    Z = ____ s    N = ____    W = ____
Q0 = ____ s   T_max = ____ s
批准人：________    冻结日期：________
```

## 6. 失败停止条件

```text
连续 N 次 Connection error 类失败（建议 N = 5）
    ↓
立即停止该 condition（不修改参数继续硬冲）
    ↓
转入恢复观测（§4 D 流程: 固定间隔单发 probe, 直至恢复或超时）
    ↓
记录 recovery behavior（自动恢复 / 超时未恢复 + recovery_latency 或 timeout 事实）
```

**全局中止条件**（任一触发 → 整个 run 终止, 已采数据原样封存, 不补测）:

- 出现 402 Insufficient Balance 或 401 认证错误（基础设施状态已改变, 后续数据失效）;
- preflight 复核失败（本地网络不可用）;
- 连续 2 个 Condition 均触发失败停止（故障区间已越过研究价值边界）。

## 7. 与 R4 的关系（原文必录）

```text
This protocol is a prerequisite for R4, not a substitute.
R4 will only be authorized after:
- Protocol is approved
- Characterization runs are completed
- Stability threshold is observed
```

- 本协议的产出**不构成** R4 重跑的证据, 仅构成 R4 的**前置可行性输入**;
- 「Stability threshold is observed」指: 在冻结标准下, 至少一个密度档位
  同时满足 S1–S3（及 D 已触发时的 S4）, 并由人工 Evidence Review 确认。

## 8. 待人工决策项（Protocol Review 清单）

| # | 决策项 | 说明 |
|---|--------|------|
| 1 | 阈值冻结 | §5-A 中 X / Y / Z / N / W / Q0 / T_max 最终值 |
| 2 | 目标端点裁定 | opencode 网关 vs `api.deepseek.com` —— 必须**唯一确定**并写入每次记录（R2/R3 的运行期端点歧义不得带入本协议） |
| 3 | 探针实现授权 | 新独立脚本（零触碰现有实验代码）的实现 Sprint 是否批准 |
| 4 | 执行时段授权 | live run 的日期/时段（避开已知业务高峰, 由用户指定） |

---

## 附录 A：单条记录 JSON 示例

```json
{
  "request_id": "char-001-0007",
  "run_id": "char-001",
  "condition_id": "B",
  "timestamp_start": "2026-08-26T02:00:07.123Z",
  "timestamp_end": "2026-08-26T02:00:11.456Z",
  "base_url": "<调用时刻实际生效值>",
  "model": "<调用时刻实际解析值>",
  "judge_mode": "rules",
  "result": "failure",
  "exception_type": "APIConnectionError",
  "exception_message": "Connection error.",
  "exception_cause": "<__cause__ 链 repr 或 null>",
  "elapsed_seconds": 4.333,
  "inter_request_interval": 5.012,
  "rolling_requests_per_minute": { "1min": 12, "5min": 38, "10min": 41 },
  "cumulative_request_number": 7,
  "consecutive_failures": 1
}
```

## 附录 B：Incident Record 遗留 UNKNOWN → 本协议关闭手段对照

| Incident 遗留问题 | 本协议关闭手段 |
|--------------------|----------------|
| 运行期实际端点未落盘（R2/R3 UNKNOWN） | §1 字段 6/7: base_url/model 逐条强制落盘 + §3 G2 配置快照 |
| 异常底层子因未捕获（仅存 str(exc)） | §1 字段 10–12: exception type/message/cause 三要素 |
| 小流量探针（30/30 PASS）无法预测全量行为 | §4 密度矩阵 + 滚动窗口计数, 将「密度」变为受控自变量 |
| 恢复行为从未被观测 | §4 D 条件 D0–D2 恢复流程 + S4 恢复延迟标准 |
| 稳定工作区间未知 | §5 冻结标准下的 A/B 判定 + 人工确认 |

## 附录 C：本 Sprint 停止条件遵守声明

- ❌ 未执行 live 实验, 未发起任何网络请求, 未调用任何 API
- ❌ 未修改任何现有实验代码或产品代码
- ❌ 未生成架构性能结论
- ✅ 仅产出本协议文档
- ⏸ 等待人工 Protocol Review 与授权后方可进入实现/执行阶段
