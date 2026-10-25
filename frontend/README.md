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

## 使用的后端端点

| 端点 | 用途 |
|------|------|
| `GET /health` | 顶部后端状态与已注册域；缺失的域自动置灰 |
| `POST /orchestrate` | 唯一分析入口：`outputs[]` + `explanation_detail` + `consensus`（≥2 域时） |
| `GET /sessions/{id}` | 执行详情中按需读取持久化会话 |
| `GET /traces/{id}` | 执行详情中按需读取推理追踪 |

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
域专属字段（如六爻 `casts`、八字 `dayun_count`）只存在于 `/agents/{name}/compute`，本页面走 `/orchestrate`，
因此不提供这些字段，也未做任何本地补算。

## 预填示例

来自仓库 README 的已验证调用示例，可编辑后重新提交：

- 出生：1990-06-15 08:30（Asia/Shanghai）· 男
- 问题：今年的工作发展如何？

## 界面结构

- **分析输入**：领域多选（1 域=单域分析；≥2 域由后端返回共识）、出生日期/时间/时区、性别、问题、高级参数（seed / 经纬度 / client_nonce）、字段级校验与请求体预览。
- **计算结果**：八字四柱（藏干/纳音/十神/大运）、紫微十二宫、六爻本卦/变卦/互卦与纳甲六亲、奇门九宫。
- **知识证据**：检索片段 + 来源书名/章节 + 节点 ID，可展开全文，并标注不构成证明。
- **解释**：后端 `explanation` 原文，附 provider / 降级 / provider 错误信息。
- **综合共识**：仅当后端返回 `consensus` 时出现；展示综合置信度、各域贡献、冲突、一致性矩阵与 synthesis 原文。
- **执行详情**：`request_id`、`engine_version`、`input_hash`、`computed_at`、置信度、`reasoning_trace`、`errors[]`、原始 JSON，以及会话/追踪读取按钮。

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

- `src/api/types.ts`：手写类型，来源为后端 `core/schemas.py`、各域 agent 模型、`orchestration/graph.py`、
  `api/app.py` 与实测响应（每个类型有注释）。
- `src/api/parse.ts`：运行时逐字段收窄；未知域保留为通用输出，不伪造专用结果。
- `src/api/errors.ts`：HTTP / 网络 / 超时 / 取消统一为 `ApiError`；`src/api/client.ts` 是唯一 `fetch` 出口。
- `src/config/index.ts`：API 地址解析（含 `?api=` 与 localStorage）、预填示例、领域元数据。
- `src/utils/timezone.ts`：IANA 时区 → 带偏移 ISO 8601（含历史夏令时与 DST 边界修正）。
- `src/utils/validation.ts`：表单校验与 `/orchestrate` 请求构造的唯一入口。
- `src/composables/`：`useAnalysis`（分析工作流）、`useConnection`（健康检查/API 地址）、`useToast`。

## 端到端测试（真实浏览器）

前置：后端与前端开发服务器均已启动。

```bash
uv run python frontend/tests/e2e_smoke.py \
  --frontend-url 'http://127.0.0.1:5173/?api=http://127.0.0.1:8000'
```

脚本通过 Chrome DevTools Protocol 驱动真实 Chrome/Edge 无头浏览器，覆盖：健康检查、预填示例、
表单校验、单域分析（断言四柱来自后端真实结果）、知识证据展开、解释降级标注、执行详情与
`/sessions`、`/traces` 读取、四域共识、390px 移动端无横向溢出、错误 API 地址提示、恢复默认、
真实网络节流下的取消请求、未捕获 JS 错误检查。截图输出到 `frontend/.artifacts/`（已 gitignore）。

生产构建同样可用：`npm run preview` 后把 `--frontend-url` 指向 `http://127.0.0.1:5173/`。

## 目录

```
frontend/
├── index.html                # Vite 入口
├── vite.config.ts            # 端口 / 构建配置
├── tsconfig.json             # strict TypeScript（含 tests）
├── package.json              # 依赖与脚本（package-lock.json 提交）
├── src/
│   ├── main.ts / App.vue     # 入口与应用外壳（健康状态、设置、toast）
│   ├── api/                  # types / parse / errors / client
│   ├── config/               # API 地址、预填示例、领域元数据、时区与性别选项
│   ├── composables/          # useAnalysis / useConnection / useToast
│   ├── components/           # 表单、状态视图、结果标签页、执行详情、设置
│   │   ├── panels/           # 计算 / 证据 / 解释 / 共识 / 执行详情
│   │   └── domains/          # 八字、紫微、奇门、六爻渲染器
│   ├── utils/                # timezone / format / validation / clipboard
│   └── styles/app.css        # 迁移自旧版样式（配色、响应式布局）
└── tests/
    ├── e2e_smoke.py          # CDP 端到端冒烟（真实后端）
    └── unit/                 # Vitest 单元测试
```
