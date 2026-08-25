# Phase 4 Infrastructure Incident Record（基础设施事件记录）

> **模式**: 归档 Sprint（ARCHIVE ONLY）
> **日期**: 2026-08-25
> **分支**: `work/phase4/infra-incident-record`
> **事件状态**: **OPEN**（未关闭）
> **范围**: 将 Phase 4.2 实验系列受到的基础设施干扰统一记录为**单一事件链**（R / R2 / R3）。
> 本文件是记录，不是根因报告。

---

## 0. 事实源与审计方法

本记录的每一个数字均由**实验归档原件重算**得出，不采信任何对话摘要或转述数字：

| 运行 | 原始结果 JSON | Trace 归档 | 门禁记录 |
|------|----------------|-------------|----------|
| R | `ACIS/projects/ACIS_diagnostic/reports/raw_results.json`（started 2026-08-12T10:46:54Z） | `ACIS/logs/phase4_2_real_agent/`（445 trace json） | — |
| R2 | `ACIS/reports/phase4_2_r2_raw_results.json` | `ACIS/logs/phase4_2_r2/`（441 trace json） | PREFLIGHT_PASS（`ACIS/phase4_2_r2_status.txt`；单例预检 `logs/phase4_2_r2_preflight/`） |
| R3 | `ACIS/reports/phase4_2_r3_raw_results.json` | `ACIS/logs/phase4_2_r3/`（441 trace json） | STRESS_PASS（`ACIS/phase4_2_r3_status.txt`；30 连发压力报告 `reports/phase4_2_r3_stress_test.md`） |

辅助档案：`reports/phase4_2_real_agent/diagnosis_judge_fallback.md`（R 数据诊断）、
`environment_diff.md`（4.1 vs R 环境对比）、`scripts/run_phase4_2_real_agent.py`
（R3 `DELAY_SECONDS = 3.0` 的代码事实）。

审计方法：
- 成功/回退计数 ← raw JSON 逐记录 `judge_mode` 字段重算；
- 回退原因分布 ← 遍历全部 trace JSON 提取 `missing_evidence` 字符串，
  按「含该原因的 trace 数」统计；
- 时间窗 ← raw JSON manifest `started`/`finished` 与记录时间戳
  （下文时间均为 UTC；+08 = UTC+8）。

## 1. 数据审计结果

### 1.1 与授权声明的数字核对

| 授权声明（FACT 候选） | 归档重算值 | 判定 |
|------------------------|------------|------|
| R3: 110/216 deepseek | `judge_mode`: deepseek=110, rules=106（共 216） | ✅ 吻合 |
| R3: 106 fallback events | rules-mode 记录 = 106 | ✅ 吻合 |
| R3: 105 Connection error | 含 `…已回退规则裁决：Connection error.` 的 trace = 105 | ✅ 吻合 |
| R3: 1 Request timed out | 含 `…已回退规则裁决：Request timed out.` 的 trace = 1 | ✅ 吻合 |

### 1.2 三次运行执行级统计

| 维度 | R（08-12） | R2（08-13） | R3（08-15） |
|------|-----------|-------------|-------------|
| 总 judge 调用 | 216 | 216 | 216 |
| deepseek 成功 | **25**（11.6%） | **19**（8.8%） | **110**（50.9%） |
| rules 回退 | **191**（88.4%） | **197**（91.3%） | **106**（49.1%） |
| 回退原因：Connection error | 191 | 197 | 105 |
| 回退原因：Request timed out | 0 | 0 | **1** |
| 其他原因（429/解析/显式规则路径） | 0 | 0 | 0 |
| 运行时长 | 10:46:54–12:30:52（≈1h44m） | 11:43:55–13:49:45（≈2h06m） | 14:01:53–17:37:47（≈3h36m） |

### 1.3 分 seed / 分 config 分布（deepseek/rules）

| 维度 | R | R2 | R3 |
|------|----|----|----|
| seed42 | 25 / 47 | 19 / 53 | 47 / 25 |
| seed43 | 0 / 72 | 0 / 72 | 63 / 9 |
| seed44 | 0 / 72 | 0 / 72 | **0 / 72** |
| C0 | 24 / 48 | 19 / 53 | 48 / 24 |
| C1 | 1 / 71 | 0 / 72 | 30 / 42 |
| C2 | 0 / 72 | 0 / 72 | 32 / 40 |

三次运行共同的形态：**成功集中于最先执行的 arm 窗口，随后坍缩**
（R：seed42 前 25 次；R2：seed42/C0 前 19 次；R3：seed42+seed43 大部分成功，
但最后执行的 seed44 全部 72 次失败）。

### 1.4 事件前基线（供对照）

| 运行 | 日期 | 调用数 | 结果 |
|------|------|--------|------|
| Phase 4.1 pilot | 08-09 | 72 | 72/72 LLM judge 成功（~2h） |
| Harness validation | 08-10 | 216 | 216/216 成功（10:59–11:27 +08） |
| R3 前压力探针 | 08-14（01:35–03:05 +08） | 30 | 30/30 成功（opencode 网关, deepseek-v4-flash, 单 case 连发） |

## 2. 事件链（按时间顺序）

```text
2026-08-09  Phase 4.1 pilot
    72 次 LLM judge 全部成功 —— 基线健康

2026-08-10  Harness validation
    216/216 成功 —— 评估管线本身可全量跑通

2026-08-12  Phase 4.2-R（真机全量）
    baseline infrastructure failure
    25/216 deepseek（11.6%），191 次 fallback（全部 Connection error）
    成功窗口 10:51:50–11:05:37 UTC，其后至运行结束持续失败

2026-08-13  R 数据诊断 + R2 预检
    diagnosis_judge_fallback.md：触发机制 CONFIRMED，连接层不可达 PROBABLE，子因 UNKNOWN
    R2 PREFLIGHT_PASS（单例预检）

2026-08-13  Phase 4.2-R2（端点替换后重跑）
    endpoint substitution
    → failure pattern persisted
    19/216 deepseek（8.8%），197 次 fallback（全部 Connection error）
    运行期实际端点未被日志记录（raw JSON 与 trace 均无 base_url 字段）

2026-08-14  R3 门禁压力探针
    STRESS_PASS：30/30 连发成功（网关端点，deepseek-v4-flash）

2026-08-15  Phase 4.2-R3（arm 间强制 3 秒编排延迟，DELAY_SECONDS=3.0）
    → success rate improved（110/216 = 50.9%，相对 R2 的 8.8%）
    → stability threshold NOT achieved
      （seed44 整段 0/72 失败；成功率随执行时点衰减的形态未消除）
```

## 3. 证据分层

### FACT（归档可直接复核）

- R3：110/216 deepseek；106 次 fallback（105 Connection error + 1 Request timed out）。
- R：25/216 deepseek；191 次 fallback，全部 Connection error。
- R2：19/216 deepseek；197 次 fallback，全部 Connection error。
- 三次运行均无 429/rate-limit 响应痕迹、无 JSON 解析失败、无显式 rules-only 配置；
  全部 fallback 由 `_run_llm_judge` 异常分支触发（代码路径见 R 诊断文档 §2）。
- R3 runner 存在 arm 间 3.0 秒强制延迟（`run_phase4_2_real_agent.py` `DELAY_SECONDS = 3.0`）。
- 事件前基线（4.1 pilot 72/72、harness 216/216、R3 前 30/30 探针）均全部成功。
- R2/R3 全量运行的运行期实际端点未落盘（无 base_url 记录）→ 该项为 UNKNOWN，不是 FACT。

### OBSERVATION（由数据重建的关系性陈述）

- 3-second delay improved success rate relative to R2
  （8.8% → 50.9%；相对 R 的 11.6% 亦提升）。
- 三次运行的失败均呈时间窗口相关形态（先执行的 arm 成功率高，随后坍缩），
  且与 seed/config/case 内容无关（R3 中 seed44 作为最后执行段全军失败）。
- 小流量探针（30/30）通过不能预测全量运行行为（R3 门禁 PASS 后仍出现 49% fallback）。
- 由于三次运行的 judge_mode 构成差异巨大（rules 占比 88%/91%/49%），
  跨运行的 accuracy/ECE/coherence 等下游指标不具备可比基础。

### HYPOTHESIS（未证实，禁止作为结论引用）

- Request density may interact with gateway or connection-layer stability
  （请求密度可能与网关/连接层稳定性存在交互——3 秒间隔伴随成功率上升仅是
  时间相关的共变，不构成因果证明）。
- 对端边缘节流/封锁表现为连接层失败；或本地网络路径在特定时段不稳定
  （承自 R 环境 diff 的 HYPOTHESIS 区，至今无区分证据）。
- R 运行期存在配置/端点歧义候选（审计声明网关 vs 重建配置付费端点，G 类候选）。

> ⚠ 以上 HYPOTHESIS 均未获得直接证据支持。本记录不将其写为已证明的根因。

## 4. 根因状态

```text
Root Cause: NOT ESTABLISHED
Construct Validity: NOT ESTABLISHED
Infrastructure Incident: OPEN
```

- **Root Cause: NOT ESTABLISHED** —— 已确认的只有触发机制（LLM judge 异常 → 规则回退）
  与异常类别（连接层为主）；连接失败的底层子因（被拒/TLS/DNS/节流/本地网络）
  无证据区分。"Connection error." 与 "Request timed out." 的具体成因均未知。
- **Construct Validity: NOT ESTABLISHED** —— 三次运行的测量构成
  （judge_mode 分布）受基础设施状态主导且互不相同，实验系列无法支撑
  架构层面的性能结论；R/R2/R3 的指标差异不得用于架构判断。
- **Infrastructure Incident: OPEN** —— 干扰源未识别、未消除，复发风险未评估。

## 5. 状态与禁止事项遵守声明

- ❌ 不写 RESOLVED
- ❌ 不写 RATE LIMITING CONFIRMED（全程无 429 证据）
- ❌ 不启动 R4
- ❌ 不解锁 Phase 4.3（Phase 4.3 保持锁定）
- ❌ 不产生架构结论、不修改实验设计、不做 remediation 动作

---

## 附录 A：归档文件清单（本记录全部数字来源）

```text
E:\knowledge_database\ACIS\
├── reports\
│   ├── phase4_2_raw_results.json                    # 08-10 harness 216/216
│   ├── phase4_2_r2_raw_results.json                 # R2 原始结果（19/197）
│   ├── phase4_2_r3_raw_results.json                 # R3 原始结果（110/106）
│   ├── phase4_2_r2_stability_report.md              # R2 指标层报告
│   ├── phase4_2_r3_stability_report.md              # R3 指标层报告
│   ├── phase4_2_r3_stress_test.md                   # R3 门禁 30/30（STRESS_PASS）
│   └── phase4_2_real_agent\
│       ├── diagnosis_judge_fallback.md              # R 触发机制/异常类别诊断
│       ├── environment_diff.md                      # 4.1 vs R 环境对比
│       ├── precheck_report.md                       # R 运行前检查
│       └── stability_report.md                      # R 指标层报告
├── logs\
│   ├── phase4_2_real_agent\                         # R traces（445 json）
│   ├── phase4_2_r2\                                 # R2 traces（441 json）
│   ├── phase4_2_r2_preflight\                       # R2 预检（PREFLIGHT_PASS）
│   └── phase4_2_r3\                                 # R3 traces（441 json）
├── projects\ACIS_diagnostic\reports\raw_results.json # R 原始结果（25/191）
├── scripts\run_phase4_2_real_agent.py               # DELAY_SECONDS=3.0（R3）
├── phase4_2_r2_status.txt                           # PREFLIGHT_PASS
└── phase4_2_r3_status.txt                           # STRESS_PASS
```

## 附录 B：复现方式

```text
1. 成功/回退计数：解析各 raw JSON 的 results[].judge_mode，Counter 聚合。
2. 回退原因：遍历对应 logs 目录全部 *.json，提取 missing_evidence 字符串，
   按 trace 去重计数（每条 trace 内该字符串序列化出现两次，须按 trace 计一次）。
3. 时间窗：raw JSON manifest.started / finished（UTC）。
```
