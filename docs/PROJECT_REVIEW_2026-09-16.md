# OpenMetaphysics 项目汇报与下一步工作计划

> **日期**: 2026-09-16
> **基线**: `main` @ `e5f324f`；当前分支 `work/knowledge/phase7.2b-r3`（领先 main **5 commits**，Ziwei 语料冻结，待合并 D-10）
> **实测口径**: `pytest` 收集 **618**、全绿 exit 0 · `ruff check`/`format --check` **clean** · Conformance `135/135 certified` · 语料 digest `69d6e2a6…`
> **测试构成**: 618 = Reference 核心 304 + Knowledge 29 + `reference/tests` 48 + Production 相关 237
> **方法**: 代码/文档逐项核对 + CI 命令本地复现；所有结论均带文件证据

---

## 1. 总览：各模块剩余量矩阵

| # | 模块 | 状态 | 剩余量 | 关键缺口 |
|---|------|------|--------|----------|
| 1 | Reference Runtime 核心（16 模块） | 实现齐备、测试齐备 | **小~中** | 缺 `rule_contract.json`/`pattern_contract.json`；conformance 行为覆盖空转 |
| 2 | **Conformance / 认证可信度** | 135/135 certified | **中（重点）** | 行为覆盖仅 **17/100** 且无条件通过；4 类检查恒 `passed=True`；CF-015 未满足 |
| 3 | Production Runtime · Phase 0~1 | 完成 | 0 | JSON Schema 仅运行时导出，无落盘工件 |
| 4 | Production Runtime · Phase 2 六爻 | 部分完成 | **大（10+ 文件）** | 领域 Schema 已有；缺契约/向量/`reference/liuyao/`/认证 |
| 5 | Production Runtime · Phase 3 八字 | **Integration Ready** | 0 | 无机器可读契约 MANIFEST（可选） |
| 6 | Production Runtime · Phase 4 紫微 | **Integration Ready** | 小（清理） | `ziwei/pattern_matcher.py` 死码+不可导入+越界；扩展为 ACP 阻塞 |
| 7 | Production Runtime · Phase 5 奇门 | **Certified** | 0 | — |
| 8 | Production Runtime · Phase 6 共识 | 部分完成 | 中（3~6） | 无契约适配层、无等价测试、`majority` 无表决语义、`severity` 恒定 |
| 9 | Production Runtime · Phase 7 编排+API | 部分完成（≈达成） | 小（1~2） | 五步齐全；缺 `/consensus`、知识端点、鉴权/CORS |
| 10 | Production Runtime · Phase 8 推理+RAG | 部分完成 | 中（3~6） | **RAG 全仓无 `.add()` 空转**；provider/RAG **零测试**；两个专属 explainer 坏死且未接线 |
| 11 | Production Runtime · Phase 9 运维 | **仅桩** | **大（7+）** | MCP 无 transport/无依赖；compose 无应用服务；`src/` 与 PG/Qdrant/Valkey **零连接**；无持久化 |
| 12 | Knowledge 语料（Ziwei） | **FROZEN v1.0.0**（102/47/41） | 小 | 开放登记项（非阻塞）：GAP-01/02/14/15 |
| 13 | Rust 层 | 仅 bootstrap 占位 | **大** | Calendar/SolarTime/RuleEngine/PatternMatcher/排盘引擎 |
| 14 | Go 层 | 仅 bootstrap 占位 | **大** | Gateway/Consensus/Knowledge/Evidence/Worker/Scheduler |
| 15 | TypeScript 层 | 空 | **大** | Frontend / CLI |
| 16 | 协议 `proto/` | 2 service / 5 rpc / 13 message | 中 | 无 breaking 检查、无 generate、无测试 |
| 17 | CI | 3 workflow / 10 job | 0 | 无 matrix；`develop` 不存在；pre-commit 未纳入 |
| 18 | 治理 / 文档 | 100 条合约 + 60 治理文档 | 小~中 | 19 处一致性矛盾；**ACP 范围扩张未留痕** |

> **一句话结论**：**算法内核与 4 域中的 3 域已到工程终点，语料首次冻结**；但本轮深挖暴露了
> **两类此前未被记录的问题**——① **认证可信度**（Conformance 的"135/135"含大量空转）；
> ② **治理债务**（Reference Runtime 范围扩张未走 ACP）。这两项应优先于新功能开发。

---

## 2. 逐模块详述

### 2.1 Reference Runtime 核心 —— 剩余：契约补全 + 冻结点

16 个模块全部实现、无 TODO/FIXME，测试 304 例全绿：

| 模块 | 行数 | 测试 | 备注 |
|------|------|------|------|
| `parser.py` / `engine.py` / `models.py`（Rule DSL） | 81/120/117 | 29 | **无 `rule_contract.json` 与生成器**（`RUNTIME_CONTRACT.md` §10 标 Planned） |
| `patterns.py` / `pattern_matcher.py` | 83/184 | 31 | **无 `pattern_contract.json`** |
| `evidence.py` / `evidence_builder.py` | 163/464 | 46 | 契约 v1.0.0 自动生成 ✓ |
| `knowledge.py` / `knowledge_query.py` | 177/526 | 71 | 契约 v1.0.0 自动生成 ✓；`knowledge_behavior.audit` 仅覆盖 6/20 条 |
| `consensus.py` / `consensus_builder.py` | 140/483 | 70 | 契约 v1.0.0 自动生成 ✓；`consensus_behavior.audit` 仅覆盖 5/25 条 |
| `conformance.py` / `conformance_runner.py` | 88/526 | 57 | 见 §2.2 |

- **契约**：`reference/contracts/` 3 份（evidence/knowledge/consensus，均 v1.0.0，均**具名生成器**且
  有 `test_contract_file_matches_runtime` diff 测试）。
- **Golden**：`reference/conformance/golden/` 5 文件 **19 向量**（Rule 6 / Pattern 5 / Evidence 1 / Knowledge 4 / Consensus 3），
  `glob` 自动发现；实测重生成与已提交**逐字节一致**（CF-018 成立）。
- **`reference/tests/` 独立套件 48 例全绿** —— 含此前"沙箱管道被拒"的 `test_ziwei_equivalence.py`
  **本次 4 passed 未复现**（`PROJECT_STATUS.md` 的沙箱豁免说明已过时）。
- **域 Reference**：qimen 63 例 / bazi 6 例 / ziwei 4 例；**无 `reference/liuyao/`**。
- 域向量（`docs/{qimen,bazi,ziwei}/golden_vectors.json` 各 24 条）**不经过 ConformanceRunner**。

### 2.2 ⚠️ Conformance / 认证可信度 —— 剩余：中（**建议列为最高优先修复项**）

实测 `ConformanceRunner().run(...)` → `passed 135 / failed 0 / certified True`，但**135 个检查中含大量无条件通过**：

| 检查 | 现状 | 问题 |
|------|------|------|
| `_check_behavior_coverage`（L527-556） | 硬编码 **17 个 ID**（BC 7/7、KB 4/20、CS 6/25），**一律 `passed=True`** | **CF-015**（`CONFORMANCE_SPEC.md` L265-278）要求覆盖 KB-001~020 + CS-001~025 → **83 个 ID 未验证** |
| `_check_ordering` / `_check_hash` / `_check_null` / `_check_enum`（L454/466/478/490） | 全部**无条件 `passed=True`** | 这四类号称"检查"实为占位 |

> 结论：**`certified=True` 的强度低于文档暗示**。这不否定已有域认证（Qimen/BaZi/Ziwei 另有
> 独立等价测试 30/30 + 24/24 + 24/24 支撑），但**核心 5 层的 Conformance 结论需重新评估**。
> 按 H3/H4：应出 **ACP**（或缺陷提案）决定是「补齐实现以符合 CF-015」还是「经 ACP 修订 CF-015」。

### 2.3 Production Runtime（Python）逐 Phase

| Phase | 状态 | 剩余量 | 关键事实（实测） |
|-------|------|--------|------------------|
| 0 脚手架 | 完成 | 0 | `pyproject.toml` src 布局 + sxtwl==2.0.7 锁定 |
| 1 基础 core | 完成 | 小 | 6 模块全实现；**JSON Schema 导出仅运行时**（`GET /agents/{n}/schema`），无落盘工件 |
| 2 六爻 | 部分完成 | **大** | `liuyao.py` 361 行：`LiuyaoInput/Chart/YaoLine/Output`（**领域 Schema 已存在**，与 `CAPABILITY_STATUS.md:321` 矛盾）、纳甲/六亲/六神/世应/用神/本变互卦；6 例测试。**缺：规则清单、`docs/liuyao/golden_vectors.json`、行为契约、`reference/liuyao/`、等价测试、Freeze/认证 = 10+ 文件，零算法创新** |
| 3 八字 | Integration Ready | 0 | 契约 v1.0.0 BC-001~014；**无机器可读 MANIFEST/adapter**（Qimen 有 `qimen_contract.py` 348 行） |
| 4 紫微 | Integration Ready | 小（清理） | Engine v0.3.0；契约 v1.0.0 + ZW-001~017；ZW-017 为**契约承认的未实现边界**（`auxiliary_stars` 恒空、测试锁定）。扩展须 ACP |
| 5 奇门 | Certified | 0 | `qimen.py` 507 + `qimen_contract.py` 348 + `domain/qimen/` 四文件 + ABI；测试 93 例 + 等价 3 |
| 6 共识 | 部分完成 | 中 | `consensus.py` 234 行已接线；**无契约适配层、无生产↔Reference 等价测试**；`majority`/`all` 与 `weighted` **仅差权重全 1.0（无多数票语义）**；`Conflict.severity` 恒 `medium`；生产侧仅 3 例测试 |
| 7 编排 + API | 部分完成（≈达成） | 小 | 五步齐全（`_validate`/`_route`/`_fan_out`/`_consensus`/`_respond`）；6 端点；OpenAPI 自动生成。缺 `/consensus`、知识端点、鉴权/CORS |
| 8 推理 + RAG | 部分完成 | 中 | provider（Ollama + OpenAI 兼容）与 InMemory/Qdrant 检索器均实现、确定性后备已生效；**但 ① RAG 全仓无任何 `.add(KnowledgeChunk(...))` → 检索恒空、`context` 恒 `""` ② provider/RAG/explainer 零测试 ③ `BaziExplainer`/`ZiweiExplainer` 未接线且坏死** |
| 9 运维 + 可扩展性 | **仅桩** | **大** | `mcp/server.py` 49 行契约桩（无 transport），`pyproject.toml` **无 mcp 依赖**；`docker-compose.yml` 仅有 PG(apache/age)/Qdrant/Valkey/Ollama，**无应用服务**；`settings.postgres_dsn` 仅声明无消费者、`persist` extra 的 sqlalchemy/psycopg **零导入**；会话/追踪持久化未实现 |

**代码级新发现（此前未记录，均实测）**

1. `src/openmetaphysics/agents/ziwei/pattern_matcher.py`（108 行）**不只是死代码，而且不可导入**：
   `agents/ziwei/` 目录**缺 `__init__.py`** → `openmetaphysics.agents.ziwei` 解析为模块 `ziwei.py`，
   `import ...ziwei.pattern_matcher` 抛 `ModuleNotFoundError: … is not a package`；且落在紫微契约 §4
   显式排除的「格局识别」范围内。目录内残留历史 `.pyc`。
2. `ZiweiExplainer` **连自己的后备文案都不可达**：读取不存在的 `ZiweiChart.patterns`、
   `AgentOutput.input_payload`、`self.provider.settings` → `_fallback` 抛异常 → 静默降级到通用 fallback
   （输出 `[ziwei] deterministic result (engine 0.3.0, …)`）。`BaziExplainer` 的 `_llm_render` 同样不可达。
   已有先例登记（`ZIWEI_ALGORITHM_AUDIT.md` F-2）。
3. **零测试模块 7 个**：`inference/providers.py`、`inference/explainer.py`、`rag/retriever.py`、
   `mcp/server.py`、`agents/ziwei/pattern_matcher.py`、`agents/ziwei_explainer.py`、`core/config.py`。

### 2.4 计算域能力 —— 剩余：六爻域契约化

| 域 | 状态 | 剩余 |
|----|------|------|
| Qimen | Integration Ready（Certified） | 0 |
| BaZi | Integration Ready | 0（可选 Manifest） |
| Ziwei | Integration Ready | 0（ZW-017 边界，改须 ACP） |
| **Liuyào** | **Implemented（Stage 1）** | **中**：Schema 定稿 → 规则清单 → 向量 → Freeze Review → 契约 → `reference/liuyao/` → 认证 → 治理注册 |

### 2.5 Knowledge 语料 —— 剩余：开放登记项

- **已冻结** `ziwei_corpus:v1.0.0`：102 节点 / 47 关系 / 41 引用，digest `69d6e2a6…`；
  Coverage Matrix §1/§2 **无未闭合项**；此后变更须走 **Corpus 级审查**。
- 唯一权威 GAP 登记：`ZIWEI_CORPUS_GAPS.md`（GAP-01~15，**GAP-11 缺号**）；OPEN = GAP-01/02/14/15。
- 范围外（须授权）：pattern / 断事类 ×8 / 用神类 ×4。

### 2.6 多语言层 / 构建链 / CI —— 剩余：大

- Rust：`crates/om-calendar` **1 crate / 18 行 lib.rs**（占位 + `VERSION` + 1 测试；4 个声明依赖**零使用**）。
- Go：`services/gateway` **1 module / 12 行 main.go**（仅打印 "not yet implemented"；无测试）。
- TS：`packages/ apps/ frontend/ python/ tools/` **仅 README + `.gitkeep`**。
- `proto/`：2 service / 5 rpc / 13 message；`buf.gen.yaml` 声明 5 个 remote plugin → 3 个输出目录
  **全部不存在且被 .gitignore 忽略**（codegen 从未执行）。
- **CI 缺口**：触发为 `push:[main,develop]` 但**无 `develop` 分支** → 实为 main-only；
  proto 无 `buf breaking`（虽已配 WIRE_JSON）、无 generate、无测试；`.pre-commit-config.yaml` 未纳入 CI；
  Makefile 与 Taskfile 命令分歧（Taskfile 漏 `reference/`），二者均无 CI 的 Conformance 步骤。
- **工具链缺口**：本机 `cargo`/`go`/`buf`/`task`/`make` **全部缺失** → Rust/Go/proto 的 CI 命令**无法本地复现**。

### 2.7 治理 / 文档 —— 剩余：小~中

- **规范层健康**：`docs/specification/` **100 条合约**（BC 35 + KB 20 + CS 25 + CF 20）全部声明 Frozen，
  **TODO/FIXME/TBD 全仓 0 命中**。
- **⚠️ ACP 缺口（治理债务）**：`REFERENCE_RUNTIME_SPEC.md` §3.2（L93-107）明确把
  **KnowledgeStore 实现 / Consensus Engine 列为 Out of Scope 且「MUST NOT be added without ACP」**，
  而二者**已实现并各有 v1.0.0 契约**——**未见对应 ACP**；§10 Revision History 仅 1 条（2026-07-12）。
  ACP 目录现有 6 文件（4 IMPLEMENTED + 1 NOT REQUIRED + 1 self-review），**无索引/模板**，
  **无 Reference Runtime 范围或冻结相关提案**。
- **Reference Runtime 最终冻结**：**不存在任何 Reference 级冻结审查工件**；
  `CAPABILITY_STATUS.md` **无 Reference Runtime 登记行** → **无退出标准**。
- 文档规模：specification 10 / governance 60 / design 10 / engineering 4 / 域文档 43；
  `context/` 仅 `归档.md`（1156 行）+ 3 份快照（最新 2026-08-25，早于 Corpus Freeze）。

---

## 3. 开放缺口与决策点

### 3.1 GAP 登记（权威唯一：`ZIWEI_CORPUS_GAPS.md`）

| GAP | 描述 | 状态 |
|-----|------|------|
| GAP-01 | 《紫微斗數全集》未获取（第二权威缺位） | 🟡 OPEN |
| GAP-02 | 中州派无可核实来源 → `school_commentary` 缺 1 条 | 🟡 OPEN（唯一引用缺口） |
| GAP-03 / 04 | 流派权重量化归属 / `ten_god` 跨系统归属 | 记录 |
| GAP-05 / 09 / 10 / 12 / 13 | 神煞辅星来源 / 刑害来源 / 六害 / 辅星源 / 神煞核验 | 🟢 CLOSED |
| GAP-06 / 07 / 08 | pattern / 断事类 / 用神类（范围外） | 记录 |
| GAP-11 | **未分配（缺号）** | N/A |
| GAP-14 | 四化无 `node_type`（须 ACP） | 🟡 OPEN |
| GAP-15 | 星曜五行多源冲突（擎羊/陀罗/火星/铃星） | 🟡 OPEN |

**本轮新增登记（建议）**：GAP-16 Conformance 行为覆盖空转（17/100）；GAP-17 Reference Runtime 范围扩张未走 ACP；
GAP-18 `ZiweiExplainer` 坏死未接线；GAP-19 RAG 检索恒空。

### 3.2 决策点

> ⚠️ **D-x 无全局登记且编号局部复用**（`D-1`/`D-2`/`D-6` 在不同报告指不同事项）。

| 编号 | 事项 | 状态 |
|------|------|------|
| **D-10** | 分支 `work/knowledge/phase7.2b-r3` 合并 / 保留 / 关闭（领先 main 5 commits） | 🔴 待裁 |
| D-11 | GAP-15 口径（流派并列 vs 不生产） | 🔴 待裁 |
| D-6 | 四化 schema（须 Schema Gate / ACP） | 🔴 待裁 |
| D-7 | `auxiliary_star` 是否扩至卷一杂曜（须 scope 批准） | 🔴 待裁 |
| D-3 / D-4 / D-5 | 抓取快照入库 / 天乙贵人韵文口诀 / GAP-01 推进 | 🔴 待裁 |
| D-1（7.2B-R 系列） | 关系层 15 类表达力 | 🟡 部分解决（yinyong/shuyu 已产出） |
| D-1 / D-2 / D-8 / D-9 / D-12 | 7.2B 重跑授权 / 示例层 ACP / 卷三余章 / shen_sha 超带 / 冻结 | ✅ CLOSED |
| DEF-01 | GAP 编号交叉错标 | 🟡 部分修复（`7.3_REPORT.md` §3/§5 仍错） |
| **新增建议** | D-13 Conformance 空转处置；D-14 Reference 范围扩张 ACP 补正；D-15 Phase 4 事件链收口 | 🔴 待裁 |

### 3.3 文档 / 仓库一致性缺陷（19 项，逐项核对）

| # | 位置 | 问题 | 处置 |
|---|------|------|------|
| 1 | `PROJECT_STATUS.md` §1/§2 | Corpus 写 `Partial（63/37/10）`，与头部 `FROZEN-v1.0.0（102/47/41）` 矛盾 | **✅ 已修** |
| 2 | `PROJECT_STATUS.md` §5.1 | 测试总写 `599`（2026-08-17）↔ 同文件 §7 `618`。**对账：599+6+7+6=618** | 待刷新 |
| 3 | `PROJECT_STATUS.md` §4 | Phase 6「未开始」、Phase 8「未开始」**严重过时**（均已实现并接线）；§2 L53「Production Runtime Draft 尚未开始」亦过时 | 待刷新 |
| 4 | `PROJECT_STATUS.md` §4/§5.2 | Production `457`、Reference `304`；§5.2 明细表**漏列 3 个 knowledge 测试文件**（6+7+6=19） | 待刷新 |
| 5 | `PROJECT_STATUS.md` §5.2 | 把 `test_ziwei_equivalence.py` 标「环境性（沙箱拒绝）」——本次实测 **4 passed 未复现**；同述「`reference/tests` 独立收集报错」也未复现 | 待刷新 |
| 6 | `PROJECT_STATUS.md` §7 | 「已交付历史 Sprint」止于 7.2B-R2，缺 R3 与 Corpus Freeze | 待刷新 |
| 7 | `PROJECT_STATUS.md` §11/§9 | 仍写「每对话必须归档 + 必须开分支 + 禁止直接改 main」（与 AGENTS.md E3/E4 冲突）；索引仍称 AGENTS.md 含「Sprint Discipline」 | 待刷新 |
| 8 | `CAPABILITY_STATUS.md` L19 | 同一单元格内既写 `FROZEN-v1.0.0（…63 节点 + 37 关系 + 10 引用` 又写 `→ 102/47/41`；且违反 E3「1~3 行指针」 | 待刷新 |
| 9 | `CAPABILITY_STATUS.md` | Qimen 行测试列 `全仓库 530`；Liuyào 节写「无领域专属 Schema」（实际已有） | 待刷新 |
| 10 | `ROADMAP.md` | L5/L36「当前开发位置」停在 Phase 7.3；L38 写「BaZi/Ziwei/Liuyào 均 Implemented」（前二者实为 Integration Ready）；Phase 3/4 无完成标记 | 待刷新 |
| 11 | `REFERENCE_RUNTIME_SPEC.md` §6.1 | 四个「(not yet implemented)」中 Consensus Engine / Knowledge Service **已实现**；§3.1 组件清单止于 Sprint 1-3 / 106 测试 | 待刷新 |
| 12 | `RUNTIME_CONTRACT.md` / `reference/golden/README.md` | 数字陈旧（「106 tests」「35 BCs」，实为 618/100） | 待刷新 |
| 13 | `reference/contracts/README.md` | 清单漏 Knowledge、把 Consensus 列为 future；只给 Evidence 的重生成命令 | 待刷新 |
| 14 | Qimen Schema 双份 | `docs/specification/qimen_contract.schema.json`(`CCAA58B5…`) ≠ `src/.../contracts/qimen_contract.schema.json`(`3D4CD776…`) | 待澄清权威 |
| 15 | 编号复用 | **Phase 7.1.6 被两个无关 Sprint 复用**（天干五合 vs Corpus Freeze）；**7.1.3 同样重复** | 待治理 |
| 16 | 根目录 | `phase_7.2b_r2_status.txt` 状态戳仍被跟踪；`scripts/infra_probe.py` 不在 main（仅未合并分支） | 可清理 |
| 17 | `docs/governance/项目进展梳理.md` | 自报 31 分支/1 未合并/599/main=38ee24e ↔ 实测 13/8/618/e5f324f | 待刷新/归档 |
| 18 | 分支 | **8 条本地分支未合并**（archify +42、phase4/char-001 +40、本分支 +5 等） | 见 §4 |
| 19 | `docs/governance/phase4/INFRASTRUCTURE_INCIDENT_RECORD.md` | 自报「事件状态 **OPEN**」 | 待显式收口 |

---

## 4. 下一步工作计划

### 4.1 P0 — 立即（无需新授权，半天内）

| # | 任务 | 理由 | 产出 |
|---|------|------|------|
| P0-1 | **合并 `work/knowledge/phase7.2b-r3` → main**（D-10） | 冻结只在 main 生效；main 落后 5 commits；分支未过 CI | 合并 commit + CI 首次验证 |
| P0-2 | **状态指针刷新**（§3.3 #2~#13、#17） | 消除 19 处自相矛盾；E3 收尾动作 | 4~6 文件小改 |
| P0-3 | **代码清理**：`ziwei/pattern_matcher.py`（死码+不可导入+越界）删除或移出；根目录状态戳清理 | 越界 + 死码 + 误导 | 2 项清理 |
| P0-4 | **分支清账**：8 条未合并分支逐一给结论 | 审计/回滚成本 | 决议清单 |
| P0-5 | 合并后跑 CI 等价命令（ruff/pytest/conformance） | H7 合并门 | 回执 |

### 4.2 P1 — 可信度与治理债务（建议紧接着做，比新功能更优先）

| # | 任务 | 依据 | 备注 |
|---|------|------|------|
| **P1-1** | **Conformance 空转处置**：出 **ACP/缺陷提案**，二选一——(a) 补齐 `_check_behavior_coverage` 至 100 个 ID 并做真实验证、去掉 4 类无条件通过；(b) 经 ACP 修订 CF-015 与相关检查定义 | §2.2；CF-015；H3/H4 | **不得静默修改** `reference/` 行为实现（须 ACP） |
| **P1-2** | **ACP 补正**：为 KnowledgeStore / Consensus / Conformance 的范围扩张补 `ACP-REF-*`，同步修订 `REFERENCE_RUNTIME_SPEC.md` §3.1/§3.2/§6.1 + §10 | §2.7；§3.2 L93-107「MUST NOT without ACP」 | 治理债清零 |
| P1-3 | **契约补全**：新增 `rule_contract.json` / `pattern_contract.json` + 生成器 + diff 测试 | §2.1；`RUNTIME_CONTRACT.md` §10 Planned | 5 层契约齐平 |
| P1-4 | **坏死/空转修复**：`ZiweiExplainer` 字段契约修复或删除；RAG 接线（灌入 KnowledgeChunk）；为 provider/retriever 补测试 | §2.3 新发现 2/3 | 属功能缺陷修复 |

### 4.3 P2 — 主线候选（1~2 周，择一，需授权）

| 选项 | 内容 | 剩余量 | 前置 |
|------|------|--------|------|
| **A（推荐）** | **六爻域契约化**（Stage 1 → Integration Ready）：Schema 定稿 → 规则清单 → 向量 → Freeze Review → 契约 v1.0.0 → `reference/liuyao/` → 24/24 等价 → 治理注册 | 中（10+ 文件，**零算法创新**，算法已在） | 用户授权 |
| B | **Reference Runtime 最终冻结**：按 §2.7 的完成条件（冻结审查工件 + Reference 登记行 + 契约补全 + 范围 ACP 补正 + 文档刷新 + 验证门槛）推进 | 中（依赖 P1-2/P1-3） | 需先定冻结退出条件 |
| C | **Production Runtime Phase 9 收口**：MCP transport 接线 + 依赖声明；compose 补 API/worker；会话/追踪持久化；RAG 接线 | 中 | 用户授权 |

### 4.4 P3 — 中长期（需立项）

| 项 | 说明 |
|----|------|
| D | **多语言生产层迁移**（Rust → Go → TS）。目标架构已工程冻结（57 组件），数百文件级；建议分阶段（先 Rust Calendar+SolarTime 供 PyO3/WASM，再 Go Gateway，最后前端）。**前置：补 `cargo`/`go`/`buf` 工具链方可本地验证** |
| E | **编号与登记体系治理**：建立单一 D 决策登记表；消除 Phase 7.1.3/7.1.6 编号复用；统一契约存放位置；补 ACP 索引/模板 |
| F | Knowledge 扩展（pattern / 断事类 / 用神类 / 其它古籍）—— 须先解冻 + scope 批准 |
| G | 六爻算法补强（六神、用神规则完整化）—— 可与 A 并行 |

### 4.5 明确不建议现在做

- ❌ 一次性铺开全部 Rust/Go/TS（无消费者、违背 E7 YAGNI）
- ❌ 在未追认下继续扩 Knowledge 语料（你已指示"停止扩大"）
- ❌ 直接改 `reference/` 行为实现或冻结契约/向量（须 ACP）
- ❌ 为"补 CI 覆盖率"给空骨架加测试

---

## 5. 风险提示

1. **成果只在本地产分支且未过 CI** —— Ziwei 冻结（5 commits）尚未进 main。**P0-1 最紧急。**
2. **认证可信度被高估** —— "135/135 certified"含 83 个未验证 ID 与 4 类空转检查；对外表述需修正，
   否则可能误导后续决策（这是本轮最重要的发现）。
3. **治理债已形成** —— KnowledgeStore/Consensus 属"未走 ACP 的范围扩张"，若不补正，
   `REFERENCE_RUNTIME_SPEC.md` §3.2 与仓库现状将持续冲突。
4. **分支膨胀** —— 8 条未合并分支（最多 +42），审计与回滚成本上升。
5. **文档漂移成规模** —— 19 处具体矛盾，含同文件自相矛盾与编号复用。
6. **多语言骨架"绿灯假象"** —— CI 全绿但 Rust/Go 仅占位、`buf.gen` 从未执行、proto 无 breaking 检查。
7. **本地工具链缺口** —— 缺 `cargo`/`go`/`buf`/`make`/`task`，非 Python 部分只能依赖 CI 验证。

---

*本报告全部结论基于本机实测（pytest 618/618、ruff clean、conformance 135/135、向量重生成逐字节一致、
契约 diff 测试通过）与代码/文档逐项核对；未修改任何被审对象（除 §3.3 #1 的状态指针修正）。*
