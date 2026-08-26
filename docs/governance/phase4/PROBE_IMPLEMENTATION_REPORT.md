# Phase 4 Probe Implementation Report（探针实现报告）

> **模式**: 实现 Sprint（IMPLEMENTATION ONLY —— 本 Sprint 未发起任何 live API 请求）
> **日期**: 2026-08-26
> **分支**: `work/phase4/probe-implementation`（基于 `work/phase4/infra-characterization-protocol` @ `90f14dd`）
> **协议依据**: `docs/governance/phase4/INFRASTRUCTURE_CHARACTERIZATION_PROTOCOL.md`（已批准，阈值已冻结）
> **状态**: ✅ 实现完成并离线验证 —— 待执行窗口（**2026-08-27 02:00–06:00 UTC**）人工确认后进行 preflight + live runs

---

## 1. 交付物清单

| 文件 | 说明 | 状态 |
|------|------|------|
| `scripts/infra_probe.py` | 独立探针脚本（约 830 行），实现协议 §1–§7 全部逻辑 | 新增 |
| `scripts/README.md` | 追加探针章节（用法/配置/输出格式/依赖说明），原有内容保留 | 修改 |
| `docs/governance/phase4/PROBE_IMPLEMENTATION_REPORT.md` | 本报告 | 新增 |

零触碰确认：`src/openmetaphysics/**`、`benchmarks/**`、ACIS 实验脚本（`run_phase4_2*.py` 等）均未修改。

## 2. 协议要求 → 实现映射

| 协议条款 | 要求 | 实现 |
|----------|------|------|
| §1 测量单位 | 17 字段逐请求记录 | `RECORD_KEYS` 冻结字段表 + `CharacterizationRun._probe_once()`；`base_url`/`model` 取调用时刻生效值；异常记 type/message/`__cause__` 链（repr 截断 500 字符） |
| §1 result 判定 | success ≡ judge_mode==deepseek 且 JSON 解析成功 | `classify()` 冻结判定式，运行期不可覆盖 |
| §2 synthetic probe | 固定最小 payload，传输参数与 Judge 路径一致 | `_PROBE_SYSTEM_PROMPT`/`_PROBE_USER_PROMPT` 固定；temperature=0.1、response_format=json_object、SDK 默认 timeout/retry；每次调用新建 client（对齐 JudgeAgent 行为） |
| §3 门禁 G1 | GET /models 返回 2xx 且非 402/401 | `g1_connectivity()`（纯标准库 urllib，带 Authorization 头） |
| §3 门禁 G2 | 配置快照入 manifest | `g2_config_snapshot()`：base_url/model/key 来源+指纹（非明文）/代理 env 变量/启动命令/平台信息 |
| §3 门禁 G3 | 时段登记 | manifest `started_utc`/`finished_utc`（UTC, Z 后缀） |
| §4 实验矩阵 | A(30s×20)→300s→B(5s×40)→300s→C(1s×60)→300s→D | `_run_fixed_density()` start-to-start 目标时刻调度；条件间 `_quiet_pause(Q0)` |
| §4 D 流程 | C 触发停止→D0/D1/D2 恢复流程；C 干净跑完→C 密度持续 120 请求 | `_run_condition_d()` 双分支：`RECOVERY_FLOW`（60s 间隔探测至 T_max=900s，测 recovery_latency，10×5s 恢复确认 ≥9/10）与 `SUSTAINED_STRESS_C_DENSITY`（D1/D2 记 NOT_TRIGGERED） |
| §5 成功标准 | S1≥90% / S2≤3 / S3 无永久失败窗(W=5) / S4 恢复≤60s，冻结不可改 | `CONFIG["thresholds"]` 硬编码冻结值 + `evaluate_condition()` 判定式；A/B 输出 S1–S3 与 `passed`；C 标注 `NOT_APPLIED_OBSERVATIONAL` |
| §6 停止条件 | 连续 N=5 次 Connection error → 停该 condition → 恢复观测；不硬冲、无重试 | `_stop_rule_fired()` + `_recovery_observation()`；代码中不存在任何 retry/backoff 路径 |
| §6 全局中止 | 402/401 计费认证错误；preflight 复核失败；连续两个 condition 失败停止 | `is_auth_or_billing()`（类型名/status_code/消息三重检测）→ `ABORTED_*`；`ABORTED_TWO_CONSECUTIVE_CONDITION_STOPS` |
| §7 与 R4 关系 | prerequisite, not substitute | 本脚本不产出任何 R4 授权判断；结果仅供人工 Evidence Review |
| §8 输出 | manifest.json / records.jsonl / results.json | `data/characterization/<run_id>/`（或 `--out-dir`）；results 仅含事实与 PASS/FAIL |

### 关键实现决策（已在代码内文档化）

1. **openai 懒加载**：本仓库 `.venv` 未安装 `openai`。导入检查、config 检查、selftest、
   preflight、dry-run 全部仅需标准库；仅 live `run` 在请求时懒加载 `openai`。
   执行 live run 的环境必须预先安装 `openai`（见 §5 操作规程）。
2. **执行窗口硬锁**：`EXECUTION_WINDOW_UTC = ("2026-08-27T02:00:00Z", "2026-08-27T06:00:00Z")`；
   live run 窗口外直接拒绝（`SystemExit`）。dry-run 不受窗口限制但发零网络请求。
3. **dry-run 时间压缩**：`--dry-run-interval-scale` 仅在 `--dry-run` 下合法
   （live 强制 1.0，构造器显式拒绝），用于离线验证状态机而不扭曲冻结配置。
4. **滚动窗口半开区间语义**：`(now - W分钟, now]`，恰在边界的请求不计入（附录验证案例）。

## 3. 验证证据（全部离线执行）

```text
=== ruff check ===            All checks passed!
=== import ===                OK
=== config integrity ===      CONFIG OK   (X=90, N=5, endpoint=api.deepseek.com)
=== no-live-on-import ===     NO LIVE REQUESTS SENT
=== offline selftest ===      19/19 PASS（字段完整性/异常三要素/cause 链截断/
                              滚动窗口算术/冻结判定式/S1-S3 判定/C 观察/
                              计费检测/窗口守卫）
=== dry-run smoke ===         full A/B/C/D 状态机离线跑通：
                              final_status=COMPLETED, requests_total=240
                              (20+40+60+120), G1=SKIPPED_DRY_RUN,
                              A/B passed=true, C=NOT_APPLIED_OBSERVATIONAL,
                              D=SUSTAINED_STRESS(120 probes, D1/D2 NOT_TRIGGERED)
```

验证过程中发现并修复两个实现缺陷（修复后全绿）：

1. 自测代码误用赋值形态的 `from` 子句（语法错误）—— 改为显式设置 `__cause__`；
2. 滚动窗口边界计数歧义 —— 固化为半开区间 `(now-W, now]` 并写入 docstring。

## 4. 硬约束遵守声明

- ❌ 本 Sprint 未发起任何 real network 请求（唯一网络路径 `g1_connectivity`/live probe 均未执行）
- ❌ 未调用 DeepSeek API
- ❌ 未修改任何现有实验代码（新增文件仅 `scripts/infra_probe.py`；`scripts/README.md` 为增量追加）
- ❌ 结果结构中无任何架构性能解释字段（results.json 固定输出事实 + PASS/FAIL）
- ✅ 阈值按 2026-08-25 人工冻结值硬编码，代码内标注 DO NOT MODIFY

## 5. 执行窗口操作规程（待人工触发，本 Sprint 不执行）

前置：执行环境安装 `openai` 包（当前仓库 `.venv` 无）；环境变量 `DEEPSEEK_API_KEY` 有效。

```bash
# ① 窗口开始后先过门禁（一次 GET）
python -m scripts.infra_probe preflight --run-id char-preflight

# ② 门禁通过后执行全矩阵（live, 约 3.5~4 小时, 含 Q0 静默段）
python -m scripts.infra_probe run --run-id char-001

# ③ 产物位于 data/characterization/char-001/{manifest,records.jsonl,results}.json
#    → 提交归档 + 人工 Evidence Review（R4 授权前提之一）
```

## 6. 停止条件遵守

实现与验证完成后立即停止：

- ❌ 不执行 preflight（等待您在执行窗口内指示）
- ❌ 不运行 characterization
- ❌ 不启动 R4 / 不解锁 Phase 4.3
- ❌ 不生成架构结论
