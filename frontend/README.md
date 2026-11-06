# OpenMetaphysics 前端 MVP（Vue 3 + TypeScript）

验证「确定性计算 → 知识检索 → 生成解释」这条真实链路是否可用、是否可读、是否值得继续投入的前端应用。

- **Vue 3 + TypeScript（strict）+ Vite**：Composition API + `<script setup lang="ts">`，无 Pinia / Router / 组件库。
- **只展示后端真实响应**：页面里没有任何硬编码的排盘结果、解释或知识片段。
- **严格分层**：计算事实 / 检索证据 / 生成解释在结构、配色与文案上彼此区分，并明确标注「证据不构成对结论的证明」。
- **运行时校验**：HTTP 响应在边界处解析（`src/api/parse.ts`），字段缺失或类型不符会显示「后端响应格式不符合契约」，不会把残缺数据渲染成看似完整的结论。

> 这是对早期零构建原生 JS 版本（`b1567e2`）的工程迁移，行为与已验证的 E2E 场景保持一致。旧静态服务器与 vanillia JS 入口已删除。

## 环境要求

- Node.js `^20.19.0 || >=22.12.0`
- npm（仓库提交 `package-lock.json`，用 `npm ci` 可复现安装）
- 后端：仓库既有 FastAPI（Python 3.11，`uv run openmetaphysics`）

## 安装与启动

```bash
# 1) 安装依赖（按 lockfile 复现）
cd frontend
npm ci

# 2) 启动后端（终端 1，仓库根目录）
#    PowerShell:
$env:OM_CORS_ORIGINS='http://127.0.0.1:5173'; uv run openmetaphysics
#    bash:
OM_CORS_ORIGINS=http://127.0.0.1:5173 uv run openmetaphysics

# 3) 启动前端开发服务器（终端 2）
cd frontend
npm run dev            # http://127.0.0.1:5173/
```

浏览器打开 <http://127.0.0.1:5173/>。页面右上角应显示「后端正常 · 4 个域」。

> API 地址优先级：`?api=` 查询参数 → localStorage（设置面板保存）→ `src/config/index.ts` 的 `DEFAULT_API_BASE`（默认 `http://127.0.0.1:8000`）。
> `?api=` 同时是「恢复默认」的目标地址。若未设置 CORS，页面会明确提示「浏览器拦截了跨域响应（CORS）」并给出修复命令。

### 端口被系统保留时（Windows）

`uv run openmetaphysics` 固定监听 `127.0.0.1:8000`。若该端口落在 Windows 保留区间
（`netsh interface ipv4 show excludedportrange protocol=tcp`），绑定会以 `WSAEACCES` 失败。
此时用 uvicorn 显式换端口，并用 `?api=` 告诉前端：

```powershell
$env:OM_CORS_ORIGINS='http://127.0.0.1:5173'
uv run uvicorn openmetaphysics.api.app:app --host 127.0.0.1 --port 8080
# 浏览器打开 http://127.0.0.1:5173/?api=http://127.0.0.1:8080
```

## 命令

| 命令 | 说明 |
|------|------|
| `npm ci` | 按 lockfile 安装依赖 |
| `npm run dev` | Vite 开发服务器（127.0.0.1:5173，strictPort） |
| `npm run build` | 生产构建到 `frontend/dist/` |
| `npm run preview` | 预览生产构建（127.0.0.1:5173） |
| `npm run typecheck` | `vue-tsc --noEmit`（与构建独立的类型检查） |
| `npm run test` | Vitest 单元测试（时区换算、请求构造、响应解析、错误归一化） |
| `npm run gen:api` | 由 `frontend/openapi.json` 生成 `src/api/generated.ts`（生成文件禁止手改） |

## 使用的后端端点

| 端点 | 用途 |
|------|------|
| `GET /health` | 顶部后端状态与已注册域；缺失的域自动置灰 |
| `POST /orchestrate` | 唯一分析入口：`outputs[]` + `explanation_detail` + `consensus`（≥2 域时） |
| `GET /sessions` | 顶部「历史会话」对话框：列出后端已持久化的会话（`request_id` / `created_at`） |
| `GET /sessions/{id}` | 恢复历史会话（请求体 + 完整响应）与执行详情中按需读取原始会话 |
| `GET /traces/{id}` | 恢复后的执行详情、以及执行详情中按需读取推理追踪 |
| `GET /knowledge/corpora` | 「知识检索」标签页的冻结语料状态/版本/节点计数 |
| `POST /knowledge/search` | 「知识检索」标签页：独立检索冻结语料（节点；可选关系/引用证据） |
| `GET /agents` | 「独立计算」入口的已注册领域 Agent 列表（名称 + 引擎版本） |
| `GET /agents/{name}/schema` | 独立计算的输入表单来源（JSON Schema：required/enum/default/领域字段） |
| `POST /agents/{name}/compute` | 「独立计算」入口：单域真实计算，返回单个 `AgentOutput`（无共识） |
| `POST /agents/{name}/explain` | 对已计算结果请求解释（不重新计算）；返回解释文本 + 解释器实际绑定的知识引用 |

> 「综合分析」走 `POST /orchestrate`（可多域 + Consensus）；「独立计算」走
> `POST /agents/{name}/compute`（单域、无编排、无共识）。两者是不同业务入口，界面明确区分。

请求体只用后端 `AgentInput` / `OrchestrationRequest` 已有字段，表单内「本次将发送的请求体」实时展示实际内容：

```json
{
  "request_id": "ui-…",
  "payload": {
    "request_id": "ui-…",
    "born_at": "1990-06-15T08:30:00+09:00",
    "gender": "male",
    "locale": "zh-CN",
    "question": "今年的工作发展如何？"
  },
  "agents": ["bazi"],
  "strategy": "weighted",
  "explain": true
}
```

`born_at` 的偏移由所选 IANA 时区换算（含历史夏令时，例如 1990 年 Asia/Shanghai 为 UTC+9），以满足后端
「必须 timezone-aware」的校验；`born_location` 只在填写经纬度时发送（后端要求经纬度成对必填）。
域专属字段（如六爻 `casts`、八字 `dayun_count`）只存在于 `/agents/{name}/compute`；「综合分析」不发送这些字段，
「独立计算」按各领域 Schema 提供并提交。

## 独立计算（单域 Agent）

顶部「独立计算」与「综合分析」是两个业务入口：

- 选择八字 / 紫微 / 奇门 / 六爻之一；
- 输入表单由 `GET /agents/{name}/schema` 驱动：required、enum（性别）、default（大运步数等）、
  领域字段（八字 `dayun_count`、紫微 `lunar_month`/`lunar_day`、六爻 `casts`）；
- `POST /agents/{name}/compute` 返回单个 `AgentOutput`，复用与 `/orchestrate` 完全相同的领域结果解析与
  `DomainCard` 渲染组件；
- 结果页可继续「请求解释」（`POST /agents/{name}/explain`，请求体携带**已计算**的 `AgentOutput`，
  后端不重新计算）：展示解释文本、provider/降级状态与解释器实际绑定的知识引用；
- 单域 explain 的知识引用只返回 `id` 与 `source`，界面只展示这两项并明确标注「不补造原文」；
  与「综合分析 → 知识检索」的独立检索结果严格区分（不能凭相同 id 推断参与本次解释）；
- 结果页标注「单域独立计算 · 不产生跨域共识」，**不伪造**其他领域结果，也不展示 Consensus。

## 预填示例

来自仓库 README 的已验证调用示例，可编辑后重新提交：

- 出生：1990-06-15 08:30（Asia/Shanghai）· 男
- 问题：今年的工作发展如何？

## 界面结构

- **分析输入**：领域多选（1 域=单域分析；≥2 域由后端返回共识）、出生日期/时间/时区、性别、问题、高级参数（seed / 经纬度 / client_nonce）、字段级校验与请求体预览。
- **独立计算**：顶部入口切换；选择单个领域 Agent，按其后端 JSON Schema 填写参数并真实调用 `POST /agents/{name}/compute`，
  结果复用领域渲染组件展示；明确标注为单域独立计算、不产生跨域共识（与「综合分析」语义分离）。
- **计算结果**：八字四柱（藏干/纳音/十神/大运）、紫微十二宫、六爻本卦/变卦/互卦与纳甲六亲、奇门九宫。
- **知识证据**：检索片段 + 来源书名/章节 + 节点 ID，可展开全文，并标注不构成证明。
- **知识检索**：独立检索冻结语料（`POST /knowledge/search`）：显示语料状态、检索片段、来源、文档 ID 与标签；
  可展开/收起长文本、切换「包含关系/引用证据」与返回条数，并处理空结果/错误/连续检索。
  **语义边界**：这里是「检索参考」，不是本次命理结论或解释的证据链（解释引用的知识在「知识证据」标签页）；
  接口不返回相关度分数，界面不展示、也不把相似度解释为结论正确率。
- **解释**：后端 `explanation` 原文，附 provider / 降级 / provider 错误信息；解释引用的知识条目在
  「知识证据」（orchestration 的 `explanation_detail` 带 id/来源/原文），独立计算结果的解释在结果页内直接请求
  `POST /agents/{name}/explain`（只返回 id/来源），两处均与用户主动的「知识检索」严格区分。
- **综合共识**：仅当后端生成 `consensus` 或存在部分失败/多域结果时出现；展示「共识状态」（界面按实际
  `consensus/conflicts/outputs/errors` 归纳，后端无 status 字段）、synthesis 原文、综合置信度、各域
  contributions、conflicts、agreement_matrix 与 reasoning_trace。**Consensus 响应不含 evidence/source 字段**：
  界面明确标注证据来源不可用，不把「知识证据」或「知识检索」当作 Consensus 证据。
  `/consensus/evidence` 是独立的 Reference Evidence-consensus 能力（`Evidence[]` 输入，与跨模态
  ConsensusAgent 不同），本页不调用它，也不把两者混同。
- **执行详情**：`request_id`、`engine_version`、`input_hash`、`computed_at`、置信度、`reasoning_trace`、`errors[]`、原始 JSON，以及会话/追踪读取按钮。
- **历史会话**（顶部「历史会话」按钮）：读取后端 `GET /sessions`，选择一条后用 `GET /sessions/{id}`
  恢复完整的计算/证据/解释/共识/执行详情视图，并显示「历史会话」横幅与创建时间；恢复结果可继续
  按 `request_id` 读取 `GET /traces/{id}`。默认后端使用进程内存存储，重启后列表清空；配置
  `OM_POSTGRES_DSN` 时来自持久化数据库。

## 域能力（当前后端实际行为）

| 域 | 计算 | 解释 |
|----|------|------|
| 八字 `bazi` | 四柱、藏干、纳音、十神、大运 | 域内模板解释（确定性后备），可带知识引文 |
| 紫微 `ziwei` | 十二宫、主星、五行局；辅星字段当前为空 | 域内模板解释 |
| 奇门 `qimen` | 九宫、八门、九星、八神、阴阳遁/局数 | 通用确定性后备（结果摘要，不是域内分析） |
| 六爻 `liuyao` | 本卦/变卦/互卦、纳甲、六亲、六神、世应 | 通用确定性后备（结果摘要） |

默认离线（`OM_ENABLE_EXPLAINER` 未开启）时 provider 为 `null`，解释为确定性后备；页面显示「已降级」，
不会把后备文本伪装成 LLM 生成结果。

## 类型与 API 边界

- `src/api/generated.ts`：**自动生成**（`openapi-typescript@7.13.0`），来源是后端
  `frontend/openapi.json`；不要手改，更新方式见下节。
- `src/api/types.ts`：以生成类型为主（请求 / 响应 envelope、`ConsensusOutput`、
  `ConsensusReport`、`/health`、`/agents`、`/agents/{name}/schema`、`/agents/{name}/compute`、
  `/knowledge/corpora`、`/knowledge/search`）；
  只有 OpenAPI 无法表达的部分才手写并注明原因：
  四个域的 `result` 图表（OpenAPI 中 `AgentOutput.result` 是 free-form object）、
  `explanation_detail` / `POST /agents/{name}/explain` 的 explain 块（`dict[str, Any]`，且单域 explain
  会剥离 `text`；为保持 wire 不变故手写 `ExplainDetail` / `AgentExplainResponse`）、
  错误响应体（路由直接返回 `JSONResponse`），
  以及 `/sessions`、`/sessions/{id}`（后端返回 store 原始 dict，OpenAPI 尚无响应模型）。
- `src/api/parse.ts`：运行时逐字段收窄；未知域保留为通用输出，不伪造专用结果；
  `parseSessionList` / `parseStoredSession` 负责历史会话的边界校验；
  `parseKnowledgeSearchResponse` / `parseKnowledgeCorporaResponse` 负责知识检索的边界校验；
  `parseAgentComputeResponse` **复用** `parseOutput` 解析单域 `AgentOutput`，不复制领域解析逻辑；
  `parseAgentExplainResponse` **复用** `parseExplainDetail`，与综合分析 `explanation_detail` 共用同一套 explain 解析。
- `src/api/errors.ts`：HTTP / 网络 / 超时 / 取消统一为 `ApiError`；`src/api/client.ts` 是唯一 `fetch` 出口。
- `src/config/index.ts`：API 地址解析（含 `?api=` 与 localStorage）、预填示例、领域元数据。
- `src/utils/timezone.ts`：IANA 时区 → 带偏移 ISO 8601（含历史夏令时与 DST 边界修正）。
- `src/utils/validation.ts`：表单校验与 `/orchestrate` 请求构造的唯一入口。
- `src/utils/agentSchema.ts`：受限 JSON Schema 读取（字段/required/enum/default/可空），不实现通用表单引擎。
- `src/utils/agentForm.ts`：独立计算草稿 → 校验 → `AgentInput` payload（含 casts/农历/大运与出生时刻换算）。
- `src/utils/consensus.ts`：Consensus 展示状态归纳（generated/partial/none/unavailable）与「无证据字段」边界文案；
  只读 `/orchestrate` 响应，不请求 `/consensus/evidence`、不计算支持率。
- `src/composables/`：`useAnalysis`（分析工作流 + 历史结果恢复）、`useConnection`（健康检查/API 地址）、
  `useSessionHistory`（会话列表/读取/恢复状态）、`useKnowledgeSearch`（知识检索状态机/取消/连续查询）、
  `useAgentCompute`（单域独立计算状态机/取消/切域防覆盖）、`useAgentExplain`（单域解释状态机/取消/旧响应隔离）、
  `useToast`。

## API 类型生成（OpenAPI → TypeScript）

后端路由的响应模型（`OrchestrationResponse`、`AgentOutput`、`ConsensusOutput`、
`ConsensusReport`、`HealthResponse`、`AgentsResponse`、`AgentSchemaResponse`、
`AgentComputeResponse`、`KnowledgeSearchResponse`、`KnowledgeCorporaResponse`）会进入 FastAPI 的
`/openapi.json`。前端类型以该文档为单一来源：

```bash
# 1) 后端 OpenAPI 有变化时，刷新快照（仓库根目录）
uv run python scripts/export_openapi.py     # 写 frontend/openapi.json（确定性：排序键 + 2 空格缩进）

# 2) 由快照生成 TypeScript 类型（frontend 目录）
cd frontend
npm run gen:api                              # openapi-typescript@7.13.0 → src/api/generated.ts
```

约束：

- `src/api/generated.ts` 与 `frontend/openapi.json` 都是产物；**只允许脚本重写，禁止手改**。
  重复执行 `npm run gen:api` 不产生额外 diff（工具版本固定在 `package.json`）。
- `frontend/openapi.json` 必须与 `app.openapi()` 的确定性导出逐字节一致；
  `tests/test_api_openapi_contract.py::test_frontend_openapi_snapshot_is_current` 会强制这一点。
- 领域 `result` 仍由 `parse.ts` 运行时校验并以手写图表类型呈现，直到 OpenAPI 真实携带
  四个域的 Output 结构为止；生成类型不会假装具备域级类型安全。
- 新增依赖的审计入口：`openapi-typescript` 仅作为 devDependency（固定版本，见 `package-lock.json`）。

## 端到端测试（真实浏览器）

触发方式：**nightly / 手动**，不在 PR CI 必跑；PR CI（`.github/workflows/frontend.yml`）
只执行 typecheck / vitest / build / OpenAPI TS 漂移校验。e2e 需要后端 + 前端
dev server + 可用 Chrome，故保留为本地或 nightly 任务。

前置：后端与前端开发服务器均已启动。

```bash
uv run python frontend/tests/e2e_smoke.py \
  --frontend-url 'http://127.0.0.1:5173/?api=http://127.0.0.1:8000'
```

脚本通过 Chrome DevTools Protocol 驱动真实 Chrome/Edge 无头浏览器，覆盖：健康检查、预填示例、
表单校验、单域分析（断言四柱来自后端真实结果）、知识证据展开、解释降级标注、执行详情与
`/sessions`、`/traces` 读取、四域共识、**历史会话列表 → 恢复结果 → 恢复后读取 `/traces`**、
**知识检索（语料状态 → 真实 `/knowledge/search` → 来源/文档 ID → 展开/收起 → 空结果 → 连续查询 → 错误态）**、
**独立计算（四个领域分别真实调用 `/agents/{name}/compute` → 八字/紫微/奇门/六爻结果 → 表单随领域变化 →
六爻 casts 校验 → 无共识标注 → 不可达错误态）**、
**解释（独立计算后请求 `/agents/{name}/explain` → 真实解释文本 → 真实知识引用 id/来源 → 四个领域各一次 →
解释与独立知识检索的边界标注 → 解释失败时计算结果保留）**、
**Consensus（真实四域共识 → 状态/参与领域/冲突/一致性矩阵 → 证据不可用与语义边界 → 单域重新分析后旧共识重置）**、
390px 移动端无横向溢出、错误 API 地址提示、恢复默认、
真实网络节流下的取消请求、未捕获 JS 错误检查。截图输出到 `frontend/.artifacts/`（已 gitignore）。

生产构建同样可用：`npm run preview` 后把 `--frontend-url` 指向 `http://127.0.0.1:5173/`。

## 目录

```
frontend/
├── index.html                # Vite 入口
├── vite.config.ts            # 端口 / 构建配置
├── tsconfig.json             # strict TypeScript（含 tests）
├── package.json              # 依赖与脚本（package-lock.json 提交）
├── openapi.json              # 后端 OpenAPI 快照（由 scripts/export_openapi.py 生成）
├── src/
│   ├── main.ts / App.vue     # 入口与应用外壳（健康状态、设置、toast）
│   ├── api/                  # generated（自动生成）/ types / parse / errors / client
│   ├── config/               # API 地址、预填示例、领域元数据、时区与性别选项
│   ├── composables/          # useAnalysis / useConnection / useSessionHistory / useKnowledgeSearch / useAgentCompute / useAgentExplain / useToast
│   ├── components/           # 表单、状态视图、结果标签页、执行详情、设置、历史会话、独立计算
│   │   ├── panels/           # 计算 / 证据 / 知识检索 / 解释 / 共识 / 执行详情
│   │   └── domains/          # 八字、紫微、奇门、六爻渲染器
│   ├── utils/                # timezone / format / validation / clipboard / agentSchema / agentForm
│   └── styles/app.css        # 迁移自旧版样式（配色、响应式布局）
└── tests/
    ├── e2e_smoke.py          # CDP 端到端冒烟（真实后端）
    └── unit/                 # Vitest 单元测试
```
