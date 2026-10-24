#!/usr/bin/env python3
"""真实浏览器端到端冒烟测试（Chrome DevTools Protocol，无第三方依赖）。

前置条件：
  1. 后端已启动并允许本页面来源跨域，例如 PowerShell：
       $env:OM_CORS_ORIGINS='http://127.0.0.1:5173'; uv run openmetaphysics
  2. 前端静态服务器已启动：
       uv run python frontend/serve.py

运行：
  uv run python frontend/tests/e2e_smoke.py
  uv run python frontend/tests/e2e_smoke.py --frontend-url http://127.0.0.1:5173/ \
      --screenshot-dir frontend/.artifacts

脚本会真实驱动页面（填表、点击、切换标签页、读取会话/追踪），断言页面渲染的是
后端返回的数据而不是占位文本；失败时以非零退出码结束。截图保存在 --screenshot-dir。
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

from websockets.asyncio.client import connect

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> bool:
    RESULTS.append((name, bool(condition), detail))
    status = "PASS" if condition else "FAIL"
    line = f"[{status}] {name}"
    if detail and not condition:
        line += f"  -> {detail}"
    print(line)
    return bool(condition)


class CDP:
    """极简 CDP 客户端：只覆盖本测试需要的方法。"""

    def __init__(self, ws) -> None:
        self.ws = ws
        self._next_id = 0

    async def send(self, method: str, params: dict | None = None) -> dict:
        self._next_id += 1
        message_id = self._next_id
        await self.ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        while True:
            raw = await asyncio.wait_for(self.ws.recv(), timeout=30)
            message = json.loads(raw)
            if message.get("id") == message_id:
                if "error" in message:
                    raise RuntimeError(f"{method}: {message['error']}")
                return message.get("result", {})

    async def evaluate(self, expression: str, *, await_promise: bool = False):
        result = await self.send(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": await_promise,
                "userGesture": True,
            },
        )
        if result.get("exceptionDetails"):
            raise RuntimeError(f"JS exception: {result['exceptionDetails']}")
        return result.get("result", {}).get("value")


async def wait_for(cdp: CDP, expression: str, *, timeout: float = 30, desc: str = ""):
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            value = await cdp.evaluate(expression)
            if value:
                return value
        except Exception as error:  # 页面切换/元素暂缺时继续等待
            last_error = error
        await asyncio.sleep(0.15)
    raise AssertionError(
        f"等待超时：{desc or expression}" + (f"（最后错误：{last_error}）" if last_error else "")
    )


def pick_chrome(explicit: str | None) -> str:
    if explicit:
        return explicit
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    found = shutil.which("chrome") or shutil.which("chromium") or shutil.which("msedge")
    if found:
        return found
    raise SystemExit("未找到 Chrome/Edge 可执行文件；请用 --chrome 指定路径。")


def wait_debug_port(port: int, timeout: float = 20) -> dict:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/json/version"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            time.sleep(0.2)
    raise SystemExit(f"Chrome 调试端口 {port} 未能启动。")


def page_target(port: int) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5) as response:
        targets = json.loads(response.read().decode("utf-8"))
    for target in targets:
        if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
            return target
    raise SystemExit("未找到可用的页面调试目标。")


async def screenshot(cdp: CDP, directory: Path, name: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    await asyncio.sleep(0.3)  # 等待 CSS 过渡结束，避免截到中间帧
    result = await cdp.send(
        "Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False}
    )
    data = result.get("data")
    if not data:
        return
    (directory / name).write_bytes(base64.b64decode(data))
    print(f"       截图: {directory / name}")


async def run(page_url: str, screenshot_dir: Path, chrome: str | None = None) -> int:
    # 0. 前端可达性
    try:
        with urllib.request.urlopen(page_url, timeout=5) as response:
            html = response.read().decode("utf-8")
    except Exception as error:
        print(f"[FAIL] 前端不可达：{page_url}（{error}）")
        print("       请先运行：uv run python frontend/serve.py")
        return 2
    check("前端页面可访问且返回 SPA 入口", "analysis-form" in html, page_url)

    chrome = pick_chrome(chrome)
    port = 9333
    profile = tempfile.mkdtemp(prefix="om-e2e-profile-")
    chrome_process = subprocess.Popen(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            f"--remote-debugging-port={port}",
            "--remote-allow-origins=*",
            f"--user-data-dir={profile}",
            "--window-size=1440,1000",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_debug_port(port)
        target = page_target(port)
        async with connect(target["webSocketDebuggerUrl"], max_size=32 * 1024 * 1024) as ws:
            cdp = CDP(ws)
            await cdp.send("Page.enable")
            await cdp.send("Runtime.enable")
            await cdp.send("Log.enable")
            await cdp.send(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": (
                        "window.__omErrors = [];"
                        "addEventListener('error', (e) => window.__omErrors.push(String(e.message)));"
                        "addEventListener('unhandledrejection', (e) => window.__omErrors.push('rejection: ' + String(e.reason)));"
                    )
                },
            )
            await cdp.send("Page.navigate", {"url": page_url})
            await wait_for(
                cdp,
                "document.body && document.body.dataset.appReady === 'true'",
                timeout=20,
                desc="页面初始化",
            )
            check("应用初始化完成（body[data-app-ready]）", True)

            # 1. 健康检查：真实请求 GET /health
            health_text = await wait_for(
                cdp,
                "document.querySelector('[data-testid=health-text]').textContent",
                timeout=25,
                desc="健康检查",
            )
            check("UI 显示后端健康状态（GET /health）", "后端正常" in health_text, health_text)
            check("健康状态包含已注册域数量", "4 个域" in health_text, health_text)
            await screenshot(cdp, screenshot_dir, "01-form-desktop.png")

            # 2. 预填示例（来自 README 已验证调用）
            values = await cdp.evaluate(
                "(() => ({date: document.getElementById('input-date').value,"
                " time: document.getElementById('input-time').value,"
                " tz: document.getElementById('input-timezone').value,"
                " gender: document.querySelector('input[name=gender]:checked').value,"
                " bazi: document.querySelector('[data-testid=domain-bazi]').checked}))()"
            )
            check(
                "预填示例与已验证 fixture 一致（1990-06-15 08:30 Asia/Shanghai 男）",
                values
                and values["date"] == "1990-06-15"
                and values["time"] == "08:30"
                and values["tz"] == "Asia/Shanghai"
                and values["gender"] == "male"
                and values["bazi"] is True,
                json.dumps(values, ensure_ascii=False),
            )

            # 3. 前端输入校验：清空日期后提交
            await cdp.evaluate(
                "(() => {const d=document.getElementById('input-date'); d.value='';"
                " d.dispatchEvent(new Event('input',{bubbles:true}));"
                " document.getElementById('btn-submit').click();})()"
            )
            errors_visible = await wait_for(
                cdp,
                "!document.getElementById('form-errors').hidden",
                timeout=5,
                desc="表单校验错误",
            )
            error_text = await cdp.evaluate("document.getElementById('form-errors').textContent")
            check(
                "缺少出生日期时显示表单校验错误",
                errors_visible and "出生日期" in error_text,
                error_text,
            )
            await cdp.evaluate(
                "(() => {const d=document.getElementById('input-date'); d.value='1990-06-15';"
                " d.dispatchEvent(new Event('input',{bubbles:true}));})()"
            )

            # 4. 单域（八字）真实分析
            await cdp.evaluate("document.getElementById('btn-submit').click()")
            await wait_for(
                cdp, "!document.getElementById('results').hidden", timeout=90, desc="单域分析结果"
            )
            summary = await cdp.evaluate("document.getElementById('results-summary').innerText")
            check("单域分析返回成功状态", "分析完成" in summary, summary[:160])
            request_id = await cdp.evaluate(
                "document.querySelector('#summary-meta dd').textContent.replace(' 复制','').trim()"
            )
            check(
                "结果携带后端 request_id",
                bool(request_id and request_id.startswith("ui-")),
                request_id,
            )

            pillars_text = await cdp.evaluate(
                "document.querySelector('[data-testid=domain-card-bazi]').innerText"
            )
            check(
                "八字卡片渲染四柱天干地支（后端真实结果）",
                "庚" in pillars_text and "辛" in pillars_text and "午" in pillars_text,
                pillars_text[:200],
            )
            check(
                "八字卡片包含日主与十神/纳音",
                "日主" in pillars_text and "纳音" in pillars_text,
                pillars_text[:200],
            )
            check(
                "八字卡片包含大运表",
                "大运" in pillars_text and "起止年龄" in pillars_text,
                pillars_text[:200],
            )
            check("计算结果标注为确定性计算", "确定性计算" in pillars_text, pillars_text[:120])
            await screenshot(cdp, screenshot_dir, "02-results-calculation.png")

            # 5. 知识证据
            await cdp.evaluate("document.querySelector('[data-testid=tab-evidence]').click()")
            await wait_for(cdp, "!document.getElementById('panel-evidence').hidden")
            evidence_count = await cdp.evaluate(
                "document.querySelectorAll('.evidence-item').length"
            )
            evidence_source = await cdp.evaluate(
                "document.querySelector('.evidence-item .evidence-source')?.textContent || ''"
            )
            evidence_text = await cdp.evaluate(
                "document.querySelector('#panel-evidence').innerText"
            )
            check("知识证据渲染后端检索片段", evidence_count >= 1, f"count={evidence_count}")
            check("知识证据带来源书名/章节", bool(evidence_source.strip()), evidence_source)
            check(
                "知识证据区明确说明「不构成证明」",
                "不是" in evidence_text and "证明" in evidence_text,
                evidence_text[:160],
            )
            await cdp.evaluate(
                "(() => {const b=document.querySelector('.evidence-toggle'); if(b) b.click();})()"
            )
            expanded = await cdp.evaluate(
                "document.querySelector('.evidence-text') && !document.querySelector('.evidence-text').classList.contains('clamped')"
            )
            check("证据片段可展开阅读全文", bool(expanded))
            await screenshot(cdp, screenshot_dir, "03-evidence.png")

            # 6. 解释
            await cdp.evaluate("document.querySelector('[data-testid=tab-explanation]').click()")
            await wait_for(cdp, "!document.getElementById('panel-explanation').hidden")
            explanation_text = await cdp.evaluate(
                "document.querySelector('[data-testid=explanation-text-bazi]')?.textContent || ''"
            )
            explanation_meta = await cdp.evaluate(
                "document.querySelector('#panel-explanation').innerText"
            )
            check(
                "解释区渲染后端 explanation 文本",
                len(explanation_text.strip()) > 10,
                explanation_text[:120],
            )
            check(
                "解释区标注离线降级（provider 未启用）",
                "离线确定性后备" in explanation_meta and "已降级" in explanation_meta,
                explanation_meta[:160],
            )
            check(
                "解释与计算事实在视觉/结构上分离",
                "生成解释" in explanation_meta and "确定性计算" not in explanation_meta,
                explanation_meta[:160],
            )

            await screenshot(cdp, screenshot_dir, "04-explanation.png")

            # 7. 单域时不应出现共识
            consensus_hidden = await cdp.evaluate("document.getElementById('tab-consensus').hidden")
            check("单域结果不显示共识标签页（后端未返回 consensus）", consensus_hidden)

            # 8. 执行详情 + 真实读取 traces
            await cdp.evaluate("document.querySelector('[data-testid=tab-execution]').click()")
            await wait_for(cdp, "!document.getElementById('panel-execution').hidden")
            execution_text = await cdp.evaluate(
                "document.getElementById('panel-execution').innerText"
            )
            execution_lower = execution_text.lower()
            check(
                "执行详情显示 request_id / 引擎版本 / input_hash",
                request_id in execution_text
                and "engine_version" in execution_lower
                and "input_hash" in execution_lower,
                execution_text[:200],
            )
            trace_count = await cdp.evaluate("document.querySelectorAll('.trace-item').length")
            check("执行详情显示推理追踪步骤", trace_count >= 4, f"steps={trace_count}")
            await cdp.evaluate("document.querySelector('[data-testid=btn-load-traces]').click()")
            traces_output = await wait_for(
                cdp,
                "(() => {const t=document.getElementById('session-trace-output').textContent;"
                " return t.includes('\"traces\"') || t.includes('读取失败') ? t : '';})()",
                timeout=15,
                desc="读取 /traces/{id}",
            )
            check(
                "点击可从后端真实读取 /traces/{request_id}",
                '"traces"' in traces_output and "读取失败" not in traces_output,
                traces_output[:160],
            )
            await cdp.evaluate("document.querySelector('[data-testid=btn-load-session]').click()")
            session_output = await wait_for(
                cdp,
                "(() => {const t=document.getElementById('session-trace-output').textContent;"
                " return t.includes('\"request\"') || t.includes('读取失败') ? t : '';})()",
                timeout=15,
                desc="读取 /sessions/{id}",
            )
            check(
                "点击可从后端真实读取 /sessions/{request_id}",
                '"request"' in session_output and "读取失败" not in session_output,
                session_output[:160],
            )
            await screenshot(cdp, screenshot_dir, "05-results-execution.png")

            # 9. 多域：触发真实共识
            await cdp.evaluate("document.querySelector('[data-testid=tab-calculation]').click()")
            await cdp.evaluate(
                "(() => {for (const id of ['ziwei','qimen','liuyao']) {"
                " const input = document.querySelector('[data-testid=domain-' + id + ']');"
                " input.checked = true; input.dispatchEvent(new Event('change', {bubbles:true}));"
                " } document.getElementById('btn-submit').click();})()"
            )
            await wait_for(
                cdp,
                "document.querySelector('#summary-meta dd').textContent.includes('ui-') && "
                "document.querySelector('#summary-meta dd').textContent.replace(' 复制','').trim() !== "
                + json.dumps(request_id),
                timeout=120,
                desc="多域分析结果",
            )
            await wait_for(
                cdp,
                "!document.getElementById('tab-consensus').hidden",
                timeout=30,
                desc="共识标签页",
            )
            check("多域分析后出现共识标签页", True)
            await cdp.evaluate("document.querySelector('[data-testid=tab-calculation]').click()")
            await screenshot(cdp, screenshot_dir, "06-multidomain-calculation.png")

            # 9b. 其余三个域的计算卡片确实渲染了后端结果
            for agent, marker, slug in (
                ("ziwei", "五行局", "06a-ziwei"),
                ("liuyao", "本卦", "06b-liuyao"),
                ("qimen", "八神", "06c-qimen"),
            ):
                card_text = await cdp.evaluate(
                    f"document.querySelector('[data-testid=domain-card-{agent}]')?.innerText || ''"
                )
                check(
                    f"{agent} 计算卡片渲染后端字段（含「{marker}」）",
                    marker in card_text and "结果渲染失败" not in card_text,
                    card_text[:150],
                )
                await cdp.evaluate(
                    f"document.querySelector('[data-testid=domain-card-{agent}]')?.scrollIntoView({{block:'center'}})"
                )
                await screenshot(cdp, screenshot_dir, f"{slug}.png")
            await cdp.evaluate("window.scrollTo(0, 0)")
            await cdp.evaluate("document.querySelector('[data-testid=tab-consensus]').click()")
            await wait_for(cdp, "!document.getElementById('panel-consensus').hidden")
            consensus_selected = await cdp.evaluate(
                "document.querySelector('[data-testid=tab-consensus]').getAttribute('aria-selected')"
            )
            calculation_selected = await cdp.evaluate(
                "document.querySelector('[data-testid=tab-calculation]').getAttribute('aria-selected')"
            )
            check(
                "共识标签页切换后处于选中态且其他标签未选中",
                consensus_selected == "true" and calculation_selected == "false",
                f"consensus={consensus_selected} calculation={calculation_selected}",
            )
            consensus_text = await cdp.evaluate(
                "document.querySelector('#panel-consensus').innerText"
            )
            contribution_rows = await cdp.evaluate(
                "document.querySelectorAll('#panel-consensus table.data tbody tr').length"
            )
            check(
                "共识卡片渲染后端 ConsensusReport",
                "综合置信度" in consensus_text and "整体" not in consensus_text,
                consensus_text[:160],
            )
            check(
                "共识包含各域贡献（≥2 个域）", contribution_rows >= 2, f"rows={contribution_rows}"
            )
            check(
                "共识展示合成结论与冲突信息",
                "synthesis" in consensus_text.lower() or "合成结论" in consensus_text,
                consensus_text[:160],
            )
            await screenshot(cdp, screenshot_dir, "07-consensus-desktop.png")

            # 10. 移动端布局
            await cdp.send(
                "Emulation.setDeviceMetricsOverride",
                {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True},
            )
            await asyncio.sleep(0.5)
            await cdp.evaluate("document.querySelector('[data-testid=tab-calculation]').click()")
            overflow = await cdp.evaluate(
                "document.documentElement.scrollWidth - window.innerWidth"
            )
            form_width = await cdp.evaluate(
                "document.getElementById('analysis-form').getBoundingClientRect().width"
            )
            check(
                "移动端宽度 390px 无横向溢出",
                isinstance(overflow, (int, float)) and overflow <= 1,
                f"overflow={overflow}",
            )
            check(
                "移动端表单仍完整可用",
                isinstance(form_width, (int, float)) and form_width > 280,
                f"width={form_width}",
            )
            await screenshot(cdp, screenshot_dir, "08-mobile.png")
            await cdp.send("Emulation.clearDeviceMetricsOverride")

            # 11. 后端不可用时的错误反馈
            await cdp.evaluate("document.getElementById('btn-settings').click()")
            await wait_for(
                cdp, "document.getElementById('settings-dialog').open", timeout=5, desc="设置对话框"
            )
            await cdp.evaluate(
                "(() => {const input=document.getElementById('settings-api-base');"
                " input.value='http://127.0.0.1:8199';"
                " document.getElementById('settings-form').requestSubmit();})()"
            )
            down_text = await wait_for(
                cdp,
                "(() => {const t=document.querySelector('[data-testid=health-text]').textContent;"
                " return t.includes('不可用') ? t : '';})()",
                timeout=25,
                desc="健康检查失败状态",
            )
            check("切换错误 API 地址后健康状态变为不可用", "不可用" in down_text, down_text)
            await cdp.evaluate("document.getElementById('btn-submit').click()")
            await wait_for(
                cdp, "!document.getElementById('results-error').hidden", timeout=40, desc="错误提示"
            )
            error_title = await cdp.evaluate("document.getElementById('error-title').textContent")
            error_hints = await cdp.evaluate("document.getElementById('error-hints').innerText")
            check(
                "后端不可达时显示明确错误（不伪装成功）", "无法连接后端" in error_title, error_title
            )
            check(
                "错误提示包含排查步骤", "uv run openmetaphysics" in error_hints, error_hints[:160]
            )
            await screenshot(cdp, screenshot_dir, "09-error-state.png")

            # 恢复默认 API 地址
            await cdp.evaluate("document.getElementById('btn-settings').click()")
            await wait_for(cdp, "document.getElementById('settings-dialog').open", timeout=5)
            await cdp.evaluate("document.getElementById('btn-settings-default').click()")
            recovered = await wait_for(
                cdp,
                "(() => {const t=document.querySelector('[data-testid=health-text]').textContent;"
                " return t.includes('后端正常') ? t : '';})()",
                timeout=25,
                desc="恢复默认 API 地址",
            )
            check("恢复默认 API 地址后健康检查重新通过", "后端正常" in recovered, recovered)

            # 12. 前端无未捕获 JS 错误
            js_errors = await cdp.evaluate("window.__omErrors || []")
            check(
                "页面运行期间无未捕获 JS 错误",
                not js_errors,
                json.dumps(js_errors, ensure_ascii=False)[:300],
            )
    finally:
        chrome_process.terminate()
        try:
            chrome_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            chrome_process.kill()
        shutil.rmtree(profile, ignore_errors=True)

    failed = [item for item in RESULTS if not item[1]]
    print()
    print(f"== 端到端冒烟结果：{len(RESULTS) - len(failed)}/{len(RESULTS)} 通过 ==")
    for name, ok, detail in RESULTS:
        if not ok:
            print(f"  FAIL: {name} -> {detail}")
    return 0 if not failed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenMetaphysics 前端 E2E 冒烟测试（CDP）")
    parser.add_argument("--frontend-url", default="http://127.0.0.1:5173/", help="前端页面地址")
    parser.add_argument("--chrome", default=None, help="Chrome/Edge 可执行文件路径")
    parser.add_argument(
        "--screenshot-dir",
        default=str(Path(__file__).resolve().parents[1] / ".artifacts"),
        help="截图输出目录",
    )
    global ARGS
    ARGS = parser.parse_args()
    return asyncio.run(run(ARGS.frontend_url, Path(ARGS.screenshot_dir), ARGS.chrome))


if __name__ == "__main__":
    sys.exit(main())
