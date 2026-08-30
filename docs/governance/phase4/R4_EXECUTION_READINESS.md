# Phase 4 — R4 Execution Readiness（窗口 16:00Z..18:00Z）

> **文档类型**: 执行就绪登记（零 live 操作; 窗口开启前冻结）
> **时点**: 2026-08-30T09:4xZ（窗口开启前 ≈6.3h）
> **授权**: CAO-P4-R4EXEC-001（`R4 EXECUTION AUTHORIZED`, 窗口已按 CAO 指令
> 「晚上十二点」填定 = 2026-08-30T16:00:00Z .. 18:00:00Z 当地午夜 00:00–02:00 UTC+8）

---

## 1. Harness 就绪核验（全部离线完成）

| 项 | 结果 |
|----|------|
| Runner | `E:\knowledge_database\ACIS\scripts\run_phase4_2_real_agent.py`（R/R2/R3 同一 harness; 3 arms C0/C1/C2 × 3 seeds 42/43/44 × 24 cases = **216 executions**, checkpointed; precheck/full 两模式） |
| 主体配置机制 | **env 覆盖, 零代码改动**: judge/critic/planner 均读 `AGRI_AI_*_MODEL` → `DEEPSEEK_MODEL` → 默认 deepseek-chat; 启动时设 `DEEPSEEK_MODEL=deepseek-v4-flash` 即满足授权主体 |
| endpoint | `ACIS/.env` `DEEPSEEK_BASE_URL=https://api.deepseek.com` ✅（与授权一致, 无需改动） |
| API key | `ACIS/.env` `DEEPSEEK_API_KEY` 在位（计费问题已由 CAO 处置）; runner 经 `load_env()` 读取 |
| ACIS venv | `openai 2.45.0` ✅（`E:\knowledge_database\ACIS\.venv`） |
| R4 目标路径 | `reports/phase4_2_r4_raw_results.json` / `logs/phase4_2_r4/` / `phase4_2_r4_status.txt` 均不存在 ✅（零覆盖风险; 路径沿 R2/R3 先例） |

## 2. 窗口内执行序列（16:00:00Z 起人工触发）

```powershell
# 0) 环境设定（窗口内, 零额外请求）
cd E:\knowledge_database\ACIS
$env:DEEPSEEK_MODEL = "deepseek-v4-flash"

# 1) Preflight（授权 §5; 沿 R2 单例预检先例: 3 configs × case 1, seed 42）
$env:PYTHONIOENCODING = "utf-8"
.venv\Scripts\python.exe scripts\run_phase4_2_real_agent.py --mode precheck `
  --log-dir logs\phase4_2_r4_preflight `
  --output reports\phase4_2_r4_precheck_report.json
# exit 0 = PASS → 继续; 非 0 或模型/端点/认证不符 → STOP（授权 §5/§9）

# 2) Live Run（216 executions, checkpointed）
.venv\Scripts\python.exe scripts\run_phase4_2_real_agent.py --mode full `
  --output reports\phase4_2_r4_raw_results.json `
  --log-dir logs\phase4_2_r4

# 3) Post-run: status 文件（沿 R3 先例措辞）+ SHA-256 登记 + R4_EXECUTION_REPORT.md
#    "Phase 4.2-R4 Full Run COMPLETE. BLOCKED for Evidence Review."
#    → Artifact Audit → STOP → 人工 Evidence Review（授权 §14）
```

## 3. 时长与风险预算

- 每次 execution = 完整 agent 管线（planner/debate/critic/memory + judge, 多次 LLM
  调用, char-002 实测 v4-flash ≈3.7s/调用）→ 估算 **≈1–1.5h**（R/R2/R3 期间大量
  调用快速失败使历史 run 偏短; 本次 v4-flash 健康将显著变长）。
- 2h 窗口 + checkpoint 机制: 若临近 END（18:00Z）未完成 → 停止并保存已完成
  checkpoint 证据（授权 §9）; 不重试、不续跑授权外窗口。

## 4. 硬约束确认（对 16:00Z 执行生效）

- 主体/端点严格 = deepseek-v4-flash @ api.deepseek.com（env 唯一合法配置面）;
- 216-request 冻结矩阵, 零增删/改序/改间隔/retry/backoff/探索性请求;
- 逐请求证据落盘（model/base_url/时间戳/arm/序号/outcome/异常三要素）;
- 零因果结论; GAP-E1/E2 处置不变; Phase 4.3 / Knowledge LOCKED 不因执行解除;
- 窗口外零请求; 提前执行禁止（当前 09:4xZ, 窗口未开）。

## 5. 状态

**READY — STOP, 等待窗口开启（2026-08-30T16:00:00Z, 当地午夜）后人工触发执行。**
