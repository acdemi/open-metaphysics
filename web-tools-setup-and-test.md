# Web 工具安装与抓取能力测试报告

> 生成日期：2026-07-16
> 目标：把 browser-use 安装为 Codex skill；安装 crawl4ai 并测试其抓取网页内容转 Markdown 的能力。

## 一、环境

| 项 | 值 |
|---|---|
| 包管理器 | uv 0.11.19 |
| 系统 Chrome | `C:\Program Files\Google\Chrome\Application\chrome.exe` |
| 默认 python/pip | hermes-agent venv（Python 3.11，不可污染） |
| crawl4ai 运行环境 | 独立 venv `C:\Users\lkl\webtools-venv`（Python 3.12.7） |

说明：系统默认 `python`/`pip` 指向 hermes-agent 的 venv，所有安装均用 `uv` 隔离，不污染该环境。

## 二、browser-use 安装与 Codex skill 注册

### 1. 安装（隔离环境）
```powershell
uv tool install browser-use --python 3.12
```
- 版本：browser-use 0.13.4（MIT），102 个依赖，暴露命令 `browser-use`（位于 `C:\Users\lkl\.local\bin`）。
- 该目录默认不在 PATH，使用前需：`$env:PATH = "C:\Users\lkl\.local\bin;$env:PATH"`。

### 2. 注册为 Codex skill
```powershell
C:/Users/lkl/.local/bin/browser-use.exe skill install --target codex --no-install
```
- 结果：已写入 `C:\Users\lkl\.codex\skills\browser-use\SKILL.md`，下次 Codex 会话即生效。
- `--target codex` 指定装到 Codex skill 目录；`--no-install` 跳过重复安装，直接用已装好的 browser-use。

### 3. browser-use skill 用法
- 通过 CDP 直接控制浏览器，适合自动化、抓取、测试、截图、站点操作。
- 调用方式（heredoc，helpers 已预导入）：
```bash
browser-use <<'PY'
ensure_real_tab()
print(page_info())
PY
```
- 首次导航用 `new_tab(url)`；本地流程会附加到运行中的 Chrome CDP 端点。
- 需本机 Chrome 开启远程调试。连不上时运行 `browser-use --doctor` 诊断，并按提示在 `chrome://inspect/#remote-debugging` 勾选允许远程调试。
- 也支持 Browser Use Cloud 远程浏览器（适合无头服务器/并发子任务）。

## 三、crawl4ai 安装

### 1. 创建独立 venv 并安装
```powershell
uv venv "C:/Users/lkl/webtools-venv" --python 3.12
uv pip install --python "C:/Users/lkl/webtools-venv/Scripts/python.exe" crawl4ai
```
- 版本：crawl4ai 0.9.2（Apache-2.0），93 个依赖（含 playwright 1.61、patchright 1.61）。

### 2. 浏览器内核：遇到的问题与解决
- `crawl4ai-setup` 默认下载 Playwright Chromium（约 183MB），来源 `storage.googleapis.com` 在当前网络下 30s 超时失败。
- **解决**：crawl4ai 可复用系统已装 Chrome，无需下载。通过 `BrowserConfig(chrome_channel="chrome")` 指定（注意字段是 `chrome_channel`，不是 `channel`；后者不生效，见 crawl4ai 源码 `browser_manager.py` 第 1119-1120 行）。
- 如需自托管 Playwright Chromium，可设代理或 `PLAYWRIGHT_DOWNLOAD_HOST` 镜像后重跑 `crawl4ai-setup`。

## 四、抓取能力测试

测试脚本：`test_crawl4ai.py`，用系统 Chrome（headless）抓取 3 个代表性网页并转 Markdown。

| URL | 页面类型 | success | Markdown 长度 | 标题 |
|---|---|---|---|---|
| https://example.com | 静态 | True | 166 | Example Domain |
| https://github.com/browser-use/browser-use | JS 重 | True | 37,015 | GitHub - browser-use/browser-use ... |
| https://news.ycombinator.com | 文本密集 | True | 17,766 | Hacker News |

- 三页全部成功。GitHub（JS 重）拿到 37KB 渲染后内容，说明 crawl4ai 能处理动态页面。
- 抓取结果已保存到 `webtools-test-output/`（3 个 .md 文件）。
- 单页耗时约 1.5–4s（FETCH + SCRAPE）。

## 五、crawl4ai 用法模板
```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def main():
    cfg = BrowserConfig(chrome_channel="chrome", headless=True, verbose=False)
    async with AsyncWebCrawler(config=cfg) as crawler:
        result = await crawler.arun(url="https://example.com")
        print(result.markdown)          # Markdown 正文
        print(result.metadata.title)    # 页面标题等元数据

asyncio.run(main())
```
- 运行：`C:/Users/lkl/webtools-venv/Scripts/python.exe your_script.py`
- Windows 控制台输出含 emoji 时建议设 `$env:PYTHONIOENCODING="utf-8"`，避免 GBK 编码报错。

## 六、注意事项
- **网络**：Playwright/cdn 下载在国内网络易超时；crawl4ai 用系统 Chrome 可绕过，browser-use 同样连接本机 Chrome。
- **编码**：Windows 控制台默认 GBK，抓取内容含 emoji 时 print 可能报 UnicodeEncodeError，设 `PYTHONIOENCODING=utf-8` 即可。
- **license**：browser-use（MIT）、crawl4ai（Apache-2.0）均可商用；若后续引入 Skyvern 注意其为 AGPL-3.0（传染性）。
- **未完成项**：`crawl4ai-setup` 的 Playwright Chromium 下载未完成（已用系统 Chrome 绕过）；如需独立 Chromium 可设代理后重跑。

## 七、产物清单
- Codex skill：`C:\Users\lkl\.codex\skills\browser-use\SKILL.md`
- crawl4ai venv：`C:\Users\lkl\webtools-venv`
- 测试脚本：`E:\knowledge_database\open-metaphysics\test_crawl4ai.py`
- 抓取输出：`E:\knowledge_database\open-metaphysics\webtools-test-output\*.md`
- 本文档：`E:\knowledge_database\open-metaphysics\web-tools-setup-and-test.md`
