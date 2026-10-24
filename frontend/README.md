# OpenMetaphysics 前端 MVP

验证「确定性计算 → 知识检索 → 生成解释」这条真实链路是否可用、是否可读、是否值得继续投入的前端原型。

- **零构建**：原生 HTML + CSS + ES modules，无 npm / Node 依赖、无打包步骤、无外部 CDN。
- **只展示后端真实响应**：页面里没有任何硬编码的排盘结果、解释或知识片段。
- **严格分层**：计算事实 / 检索证据 / 生成解释在结构、配色与文案上彼此区分，并明确标注「证据不构成对结论的证明」。

## 启动

需要两个进程（后端是仓库已有的 FastAPI 应用，前端只是一个静态服务器）。

```powershell
# 终端 1：后端（允许前端来源跨域，这是仓库既有的 OM_CORS_ORIGINS 配置项）
$env:OM_CORS_ORIGINS='http://127.0.0.1:5173'
uv run openmetaphysics

# 终端 2：前端
uv run python frontend/serve.py
```

浏览器打开 <http://127.0.0.1:5173/>。页面右上角应显示「后端正常 · 4 个域」。

bash / macOS：

```bash
OM_CORS_ORIGINS=http://127.0.0.1:5173 uv run openmetaphysics
uv run python frontend/serve.py
```

> 前端默认 API 地址是 `http://127.0.0.1:8000`，可在 `frontend/assets/js/config.js` 修改，
> 也可用 `http://127.0.0.1:5173/?api=http://127.0.0.1:8000` 或页面右上角 ⚙ 设置覆盖。
> 若未设置 CORS，页面会明确提示「浏览器拦截了跨域响应（CORS）」并给出修复命令。

### 端口被系统保留时（Windows）

`uv run openmetaphysics` 固定监听 `127.0.0.1:8000`。若该端口落在 Windows 保留区间
（`netsh interface ipv4 show excludedportrange protocol=tcp` 列出的范围内），绑定会以
`WSAEACCES` 失败。此时用 uvicorn 显式换端口，并用 `?api=` 告诉前端即可：

```powershell
$env:OM_CORS_ORIGINS='http://127.0.0.1:5173'
uv run uvicorn openmetaphysics.api.app:app --host 127.0.0.1 --port 8080
# 浏览器打开 http://127.0.0.1:5173/?api=http://127.0.0.1:8080
```

`?api=` 同时是「恢复默认」的目标地址，因此重置设置不会失联。

## 使用的后端端点

| 端点 | 用途 |
|------|------|
| `GET /health` | 顶部后端状态与已注册域；缺失的域会自动置灰 |
| `POST /orchestrate` | 唯一分析入口：`outputs[]`（计算事实）+ `explanation_detail`（解释与知识证据）+ `consensus`（≥2 域时） |
| `GET /sessions/{id}` | 执行详情中按需读取持久化会话 |
| `GET /traces/{id}` | 执行详情中按需读取推理追踪 |

请求体只使用后端 `AgentInput` / `OrchestrationRequest` 已有的字段，页面内「本次将发送的请求体」
可随时查看实际发送内容：

```json
{
  "request_id": "ui-…",
  "payload": {
    "request_id": "ui-…",
    "born_at": "1990-06-15T08:30:00+08:00",
    "gender": "male",
    "locale": "zh-CN",
    "question": "今年的工作发展如何？",
    "born_location": { "latitude": 39.9, "longitude": 116.4, "timezone": "Asia/Shanghai" }
  },
  "agents": ["bazi"],
  "strategy": "weighted",
  "explain": true
}
```

`born_location` 只在填写经纬度时发送（后端要求经纬度必填）；`born_at` 的偏移由所选 IANA 时区换算，
以满足后端「必须 timezone-aware」的校验。域专属字段（如六爻 `casts`、八字 `dayun_count`）只存在于
`/agents/{name}/compute`，本页面走 `/orchestrate`，因此不提供这些字段，也未做任何本地补算。

## 预填示例

来自仓库 README 的已验证调用示例，可编辑后重新提交：

- 出生：1990-06-15 08:30（Asia/Shanghai）· 男
- 问题：今年的工作发展如何？

## 界面结构

- **分析输入**：领域多选（1 域=单域分析；≥2 域由后端返回共识）、出生日期/时间/时区、性别、问题、高级参数（seed / 经纬度 / client_nonce）、输入校验与请求体预览。
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

默认离线（`OM_ENABLE_EXPLAINER` 未开启）时 provider 为 `null`，解释为确定性后备；页面会显示「已降级」，
不会把后备文本伪装成 LLM 生成结果。

## 端到端测试（真实浏览器）

前置：后端与前端均已启动（见上）。

```powershell
uv run python frontend/tests/e2e_smoke.py
```

脚本通过 Chrome DevTools Protocol 驱动真实 Chrome/Edge 无头浏览器，覆盖：健康检查、预填示例、
表单校验、单域分析（断言四柱来自后端真实结果）、知识证据展开、解释降级标注、执行详情与
`/traces/{id}` 读取、多域共识、390px 移动端无横向溢出、错误 API 地址时的失败提示、恢复后重新连通、
未捕获 JS 错误检查。截图输出到 `frontend/.artifacts/`（已 gitignore）。

## 目录

```
frontend/
├── index.html              # 页面骨架（语义化标签 + data-testid 供 E2E 使用）
├── serve.py                # 零依赖静态服务器（默认 127.0.0.1:5173）
├── assets/css/app.css      # 样式：桌面双栏 / 移动单栏，宣纸+朱砂配色
├── assets/js/config.js     # API 地址与预填示例
├── assets/js/api.js        # fetch 封装、错误归一化、时区换算
├── assets/js/ui.js         # 转义、时间格式化、JSON 展示、六十四卦名表（仅显示用）
├── assets/js/domains.js    # 各域计算/证据/解释渲染器
├── assets/js/app.js        # 表单、状态机、标签页、共识、执行详情
└── tests/e2e_smoke.py      # CDP 端到端冒烟测试
```
