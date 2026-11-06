#!/usr/bin/env python3
"""真实浏览器端到端冒烟测试（Chrome DevTools Protocol，无第三方依赖）。

触发方式：**nightly / 手动**，不在 PR CI 必跑。`.github/workflows/frontend.yml`
只执行 typecheck / vitest / build / OpenAPI TS 漂移校验；e2e 需要后端 + 前端 dev
server + 可用 Chrome，故保留为本地或 nightly 任务。

前置条件：
  1. 后端已启动并允许本页面来源跨域，例如 PowerShell：
       $env:OM_CORS_ORIGINS='http://127.0.0.1:5173'; uv run openmetaphysics
  2. 前端静态服务器已启动：
       cd frontend && npm run dev

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
        print("       请先运行：cd frontend && npm run dev")
        return 2
    check("前端页面可访问且返回 SPA 入口", 'id="app"' in html, page_url)

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
            check(
                "知识证据明确区分独立知识检索",
                "知识检索" in evidence_text and "独立检索" in evidence_text,
                evidence_text[:200],
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
            # 像真实用户一样逐个勾选（每次点击后让 Vue 完成一次渲染再点下一个）
            for domain in ("ziwei", "qimen", "liuyao"):
                checked = await cdp.evaluate(
                    f"(() => {{const input = document.querySelector('[data-testid=domain-{domain}]');"
                    " if (!input.checked) input.click(); return input.checked;})()"
                )
                check(f"勾选领域 {domain}", checked is True, str(checked))
                await asyncio.sleep(0.15)
            await cdp.evaluate("document.getElementById('btn-submit').click()")
            await wait_for(
                cdp,
                "document.querySelector('#summary-meta dd').textContent.includes('ui-') && "
                "document.querySelector('#summary-meta dd').textContent.replace(' 复制','').trim() !== "
                + json.dumps(request_id),
                timeout=120,
                desc="多域分析结果",
            )
            multi_request_id = await cdp.evaluate(
                "document.querySelector('#summary-meta dd').textContent.replace(' 复制','').trim()"
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
            consensus_status = await cdp.evaluate(
                "document.querySelector('[data-testid=consensus-status-label]').innerText"
            )
            check(
                "共识状态与实际数据对应（后端无 status 字段，界面按响应归纳）",
                "共识已生成" in consensus_status or "部分共识" in consensus_status,
                consensus_status,
            )
            participant_count = await cdp.evaluate(
                "document.querySelectorAll('[data-testid^=consensus-participant-]').length"
            )
            check(
                "展示实际参与共识的领域（result.contributions）",
                participant_count >= 2,
                f"count={participant_count}",
            )
            uncertainty_text = await cdp.evaluate(
                "document.querySelector('[data-testid=consensus-uncertainty]').innerText"
            )
            check(
                "展示后端冲突与一致性矩阵（不计算支持率）",
                "一致性矩阵" in uncertainty_text
                and ("冲突" in uncertainty_text or "conflicts" in uncertainty_text),
                uncertainty_text[:160],
            )
            evidence_unavailable = await cdp.evaluate(
                "document.querySelector('[data-testid=consensus-evidence-unavailable]').innerText"
            )
            check(
                "明确标注 Consensus 无证据来源并区分解释/知识检索",
                "不含 evidence" in evidence_unavailable
                and "知识证据" in evidence_unavailable
                and "知识检索" in evidence_unavailable,
                evidence_unavailable[:200],
            )
            consensus_fake_evidence = await cdp.evaluate(
                "document.querySelectorAll('#panel-consensus .evidence-item').length"
            )
            check(
                "Consensus 区域未伪造证据条目",
                consensus_fake_evidence == 0,
                f"evidence-items={consensus_fake_evidence}",
            )
            trace_steps = await cdp.evaluate(
                "document.querySelectorAll('[data-testid=consensus-trace-step]').length"
            )
            check(
                "展示后端 reasoning_trace 审计步骤（非证据来源）",
                trace_steps >= 1,
                f"steps={trace_steps}",
            )
            await screenshot(cdp, screenshot_dir, "07-consensus-desktop.png")

            # 9b. 重新分析（单域）后旧 Consensus 不得残留
            await cdp.evaluate("document.querySelector('[data-testid=domain-ziwei]').click()")
            await cdp.evaluate("document.querySelector('[data-testid=domain-qimen]').click()")
            await cdp.evaluate("document.querySelector('[data-testid=domain-liuyao]').click()")
            await cdp.evaluate("document.getElementById('btn-submit').click()")
            await wait_for(
                cdp,
                "document.getElementById('tab-consensus').hidden && "
                "!!document.querySelector('[data-testid=domain-card-bazi]') && "
                "!document.querySelector('[data-testid=domain-card-ziwei]')",
                timeout=120,
                desc="单域重新分析（旧共识重置）",
            )
            stale_consensus = await cdp.evaluate(
                "document.getElementById('panel-consensus').innerText"
            )
            check(
                "重新分析后共识标签页隐藏且不残留旧共识",
                "综合置信度" not in stale_consensus
                and "Cross-modal consensus" not in stale_consensus,
                stale_consensus[:160],
            )

            # 9c. 历史会话：GET /sessions → 恢复 → 按 request_id 读取 /traces
            await cdp.evaluate("document.getElementById('btn-history').click()")
            await wait_for(
                cdp,
                "document.getElementById('session-history-dialog').open",
                timeout=10,
                desc="历史会话对话框",
            )
            await wait_for(
                cdp,
                "document.querySelectorAll('.session-item').length >= 1",
                timeout=20,
                desc="会话列表",
            )
            session_count = await cdp.evaluate("document.querySelectorAll('.session-item').length")
            check(
                "历史会话列出后端持久化会话（≥2 条）", session_count >= 2, f"count={session_count}"
            )
            has_multi = await cdp.evaluate(
                f"!!document.querySelector('[data-session-id={json.dumps(multi_request_id)}]')"
            )
            check("会话列表包含本次多域分析 request_id", bool(has_multi), multi_request_id)
            await cdp.evaluate(
                f"document.querySelector('[data-session-id={json.dumps(multi_request_id)}]"
                " .session-restore').click()"
            )
            await wait_for(
                cdp,
                "!document.getElementById('session-history-dialog').open && "
                "!!document.getElementById('restored-banner')",
                timeout=20,
                desc="恢复历史会话",
            )
            restored_banner = await cdp.evaluate(
                "document.getElementById('restored-banner').innerText"
            )
            restored_count = await cdp.evaluate(
                "document.querySelectorAll('[data-testid^=domain-card-]').length"
            )
            restored_id = await cdp.evaluate(
                "document.querySelector('#summary-meta dd').textContent.replace(' 复制','').trim()"
            )
            check("恢复后显示历史会话横幅", "历史会话" in restored_banner, restored_banner[:160])
            check(
                "恢复的 request_id 与所选会话一致",
                restored_id == multi_request_id,
                f"{restored_id} != {multi_request_id}",
            )
            check("恢复后多域结果全部还原", restored_count >= 4, f"cards={restored_count}")
            consensus_restored = await cdp.evaluate(
                "!document.getElementById('tab-consensus').hidden"
            )
            check("恢复后共识标签页仍可见", bool(consensus_restored))
            await cdp.evaluate("document.querySelector('[data-testid=tab-execution]').click()")
            await wait_for(cdp, "!document.getElementById('panel-execution').hidden")
            await cdp.evaluate("document.querySelector('[data-testid=btn-load-traces]').click()")
            restored_traces = await wait_for(
                cdp,
                "(() => {const t=document.getElementById('session-trace-output').textContent;"
                " return t.includes('\"traces\"') || t.includes('读取失败') ? t : '';})()",
                timeout=15,
                desc="恢复会话后读取 /traces",
            )
            check(
                "恢复会话后可按 request_id 读取 /traces",
                '"traces"' in restored_traces and "读取失败" not in restored_traces,
                restored_traces[:160],
            )
            await screenshot(cdp, screenshot_dir, "07b-history-restored.png")
            await cdp.evaluate("document.querySelector('[data-testid=tab-calculation]').click()")

            # 9d. 知识检索：POST /knowledge/search（独立检索参考，不是结论依据）
            await cdp.evaluate("document.querySelector('[data-testid=tab-knowledge]').click()")
            await wait_for(
                cdp, "!document.getElementById('panel-knowledge').hidden", desc="知识检索标签页"
            )
            await wait_for(
                cdp,
                "document.querySelectorAll('[data-testid=knowledge-corpora] .chip').length >= 4",
                timeout=20,
                desc="语料状态",
            )
            corpora_text = await cdp.evaluate(
                "document.querySelector('[data-testid=knowledge-corpora]').innerText"
            )
            check(
                "知识检索显示冻结语料状态与计数",
                "ziwei_corpus" in corpora_text
                and "frozen" in corpora_text
                and "节点" in corpora_text,
                corpora_text[:160],
            )
            disclaimer = await cdp.evaluate(
                "document.querySelector('[data-testid=knowledge-disclaimer]').innerText"
            )
            check(
                "明确标注「检索参考」而非本次结论依据",
                "不是本次命理结论或解释的证据链" in disclaimer,
                disclaimer[:200],
            )
            await cdp.evaluate(
                "(() => {const i=document.getElementById('knowledge-query'); i.value='紫微';"
                " i.dispatchEvent(new Event('input',{bubbles:true}));})()"
            )
            await cdp.evaluate("document.querySelector('[data-testid=btn-knowledge-search]').click()")
            await wait_for(
                cdp,
                "document.querySelectorAll('.knowledge-result').length >= 1",
                timeout=30,
                desc="知识检索结果",
            )
            result_count = await cdp.evaluate("document.querySelectorAll('.knowledge-result').length")
            first_text = await cdp.evaluate(
                "document.querySelector('[data-testid=knowledge-text-0]').innerText"
            )
            first_source = await cdp.evaluate(
                "document.querySelector('[data-testid=knowledge-source-0]').innerText"
            )
            first_id = await cdp.evaluate("document.querySelector('[data-testid=knowledge-id]').innerText")
            check(
                "真实返回知识片段",
                result_count >= 1 and len(first_text.strip()) >= 10,
                f"count={result_count} text={first_text[:80]}",
            )
            check(
                "检索结果展示真实来源",
                "来源：" in first_source and len(first_source.strip()) > 4,
                first_source[:120],
            )
            check("检索结果带文档标识", first_id.startswith("kn:"), first_id)
            clamped_before = await cdp.evaluate(
                "document.querySelector('[data-testid=knowledge-text-0]').classList.contains('clamped')"
            )
            await cdp.evaluate("document.querySelector('[data-testid=knowledge-toggle-0]').click()")
            clamped_after = await cdp.evaluate(
                "document.querySelector('[data-testid=knowledge-text-0]').classList.contains('clamped')"
            )
            check(
                "知识片段可展开/收起",
                clamped_before is True and clamped_after is False,
                f"{clamped_before}->{clamped_after}",
            )
            await cdp.evaluate(
                "(() => {const i=document.getElementById('knowledge-query');"
                " i.value='qqqqzzzz'; i.dispatchEvent(new Event('input',{bubbles:true}));})()"
            )
            await cdp.evaluate("document.querySelector('[data-testid=btn-knowledge-search]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=knowledge-empty]')",
                timeout=30,
                desc="知识检索空结果",
            )
            check("无匹配时显示空结果状态", True)
            await cdp.evaluate(
                "(() => {const i=document.getElementById('knowledge-query'); i.value='八字';"
                " i.dispatchEvent(new Event('input',{bubbles:true}));})()"
            )
            await cdp.evaluate("document.querySelector('[data-testid=btn-knowledge-search]').click()")
            await wait_for(
                cdp,
                "document.querySelectorAll('.knowledge-result').length >= 1",
                timeout=30,
                desc="再次检索",
            )
            check("连续查询可再次返回结果（旧响应未覆盖）", True)
            await screenshot(cdp, screenshot_dir, "09b-knowledge-search.png")
            await cdp.evaluate("document.querySelector('[data-testid=tab-calculation]').click()")

            # 9e. 独立计算：四个领域分别真实调用 POST /agents/{name}/compute
            await cdp.evaluate("document.querySelector('[data-testid=mode-agent]').click()")
            await wait_for(
                cdp, "!!document.getElementById('agent-compute')", timeout=15, desc="独立计算入口"
            )
            await wait_for(
                cdp,
                "document.querySelectorAll('[data-testid=agent-domain-list] button').length === 4",
                timeout=20,
                desc="四个领域选择",
            )
            check("独立计算入口列出四个领域", True)
            await cdp.evaluate("document.querySelector('[data-testid=agent-domain-bazi]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=agent-dayun-count]')",
                timeout=20,
                desc="八字领域参数",
            )
            bazi_has_casts = await cdp.evaluate(
                "!!document.querySelector('[data-testid=agent-casts]')"
            )
            check("八字表单含 dayun_count 且不含六爻 casts", not bazi_has_casts)
            await cdp.evaluate("document.querySelector('[data-testid=btn-agent-compute]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=domain-card-bazi]')",
                timeout=60,
                desc="八字独立计算",
            )
            bazi_domain = await cdp.evaluate(
                "document.querySelector('[data-testid=agent-result-domain]').innerText.trim()"
            )
            check("八字独立计算返回真实结果", bazi_domain == "bazi", bazi_domain)
            isolation_note = await cdp.evaluate(
                "document.querySelector('[data-testid=agent-isolation-note]').innerText"
            )
            no_consensus_tabs = await cdp.evaluate(
                "document.querySelectorAll('[data-testid^=tab-]').length === 0"
            )
            check(
                "独立计算不产生跨域共识",
                "不产生跨域共识" in isolation_note and bool(no_consensus_tabs),
                isolation_note[:160],
            )
            # 9f. 独立计算 → 请求解释 → 展示真实知识引用（不重新计算）
            await cdp.evaluate("document.querySelector('[data-testid=btn-agent-explain]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=agent-explain-text]')",
                timeout=60,
                desc="八字解释",
            )
            bazi_explain = await cdp.evaluate(
                "document.querySelector('[data-testid=agent-explain-text]').innerText"
            )
            check(
                "独立计算后可请求解释并展示真实解释文本",
                len(bazi_explain.strip()) >= 20,
                bazi_explain[:120],
            )
            await wait_for(
                cdp,
                "document.querySelectorAll('[data-testid=agent-knowledge-ref]').length >= 1",
                timeout=20,
                desc="解释知识引用",
            )
            knowledge_count = await cdp.evaluate(
                "document.querySelectorAll('[data-testid=agent-knowledge-ref]').length"
            )
            knowledge_id = await cdp.evaluate(
                "document.querySelector('[data-testid=agent-knowledge-id]').innerText"
            )
            knowledge_source = await cdp.evaluate(
                "document.querySelector('[data-testid=agent-knowledge-source]').innerText"
            )
            check(
                "解释展示后端绑定的知识引用（id）",
                knowledge_count >= 1 and knowledge_id.strip().startswith("kn:"),
                f"count={knowledge_count} id={knowledge_id}",
            )
            check(
                "解释知识引用带真实来源",
                "来源：" in knowledge_source and len(knowledge_source.strip()) > 6,
                knowledge_source[:120],
            )
            boundary_text = await cdp.evaluate(
                "document.querySelector('[data-testid=agent-knowledge-boundary]').innerText"
            )
            check(
                "解释引用与独立知识检索明确区分",
                "不是" in boundary_text and "独立检索" in boundary_text,
                boundary_text[:160],
            )
            check(
                "独立计算模式不混入知识检索面板",
                bool(await cdp.evaluate("!document.querySelector('[data-testid=knowledge-search]')")),
            )

            await cdp.evaluate("document.querySelector('[data-testid=agent-domain-ziwei]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=agent-lunar-month]') && "
                "!!document.querySelector('[data-testid=agent-lunar-day]')",
                timeout=20,
                desc="紫微领域参数",
            )
            check("紫微表单含农历月/日字段", True)
            await cdp.evaluate("document.querySelector('[data-testid=btn-agent-compute]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=domain-card-ziwei]')",
                timeout=60,
                desc="紫微独立计算",
            )
            check("紫微独立计算返回真实结果", True)
            await cdp.evaluate("document.querySelector('[data-testid=btn-agent-explain]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=agent-explain-text]')",
                timeout=60,
                desc="紫微解释",
            )
            ziwei_explain = await cdp.evaluate(
                "document.querySelector('[data-testid=agent-explain-text]').innerText"
            )
            check("紫微可独立请求解释", len(ziwei_explain.strip()) >= 20, ziwei_explain[:120])

            await cdp.evaluate("document.querySelector('[data-testid=agent-domain-qimen]').click()")
            await wait_for(
                cdp,
                "!document.querySelector('[data-testid=agent-dayun-count]') && "
                "!document.querySelector('[data-testid=agent-lunar-month]') && "
                "!document.querySelector('[data-testid=agent-casts]')",
                timeout=20,
                desc="奇门领域参数",
            )
            check("奇门表单不包含其他领域专属参数", True)
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=agent-schema-status]')",
                timeout=20,
                desc="奇门 Schema",
            )
            await cdp.evaluate("document.querySelector('[data-testid=btn-agent-compute]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=domain-card-qimen]')",
                timeout=60,
                desc="奇门独立计算",
            )
            check("奇门独立计算返回真实结果", True)
            await cdp.evaluate("document.querySelector('[data-testid=btn-agent-explain]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=agent-explain-text]')",
                timeout=60,
                desc="奇门解释",
            )
            qimen_explain = await cdp.evaluate(
                "document.querySelector('[data-testid=agent-explain-text]').innerText"
            )
            check("奇门可独立请求解释", len(qimen_explain.strip()) >= 20, qimen_explain[:120])

            await cdp.evaluate("document.querySelector('[data-testid=agent-domain-liuyao]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=agent-casts]')",
                timeout=20,
                desc="六爻领域参数",
            )
            await cdp.evaluate(
                "(() => {const i=document.querySelector('[data-testid=agent-casts]');"
                " i.value='7,8,9'; i.dispatchEvent(new Event('input',{bubbles:true}));})()"
            )
            await cdp.evaluate("document.querySelector('[data-testid=btn-agent-compute]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=agent-field-error-casts]')",
                timeout=10,
                desc="六爻 casts 前端校验",
            )
            casts_error = await cdp.evaluate(
                "document.querySelector('[data-testid=agent-field-error-casts]').innerText"
            )
            check("六爻 casts 非法值被前端校验拦截", "6 个" in casts_error, casts_error[:120])
            await cdp.evaluate(
                "(() => {const i=document.querySelector('[data-testid=agent-casts]');"
                " i.value='7,8,9,6,7,8'; i.dispatchEvent(new Event('input',{bubbles:true}));})()"
            )
            await cdp.evaluate("document.querySelector('[data-testid=btn-agent-compute]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=domain-card-liuyao]')",
                timeout=60,
                desc="六爻独立计算",
            )
            liuyao_result = await cdp.evaluate(
                "document.querySelector('[data-testid=agent-result]').innerText"
            )
            check(
                "六爻独立计算返回真实结果且带后端 request_id",
                "liuyao" in liuyao_result and "ui-" in liuyao_result,
                liuyao_result[:160],
            )
            await cdp.evaluate("document.querySelector('[data-testid=btn-agent-explain]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=agent-explain-text]')",
                timeout=60,
                desc="六爻解释",
            )
            liuyao_explain = await cdp.evaluate(
                "document.querySelector('[data-testid=agent-explain-text]').innerText"
            )
            check("六爻可独立请求解释", len(liuyao_explain.strip()) >= 20, liuyao_explain[:120])

            # 解释失败不得清除原计算结果（仅拦截 /explain 请求，其他请求不受影响）
            await cdp.evaluate(
                "window.__omOrigFetch = window.fetch;"
                " window.fetch = (u, i) => String(u).includes('/explain')"
                " ? Promise.reject(new TypeError('Failed to fetch')) : window.__omOrigFetch(u, i)"
            )
            await cdp.evaluate("document.querySelector('[data-testid=btn-agent-explain]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=agent-explain-error]')",
                timeout=30,
                desc="解释失败错误",
            )
            explain_error = await cdp.evaluate(
                "document.querySelector('[data-testid=agent-explain-error]').innerText"
            )
            retained = await cdp.evaluate(
                "!!document.querySelector('[data-testid=domain-card-liuyao]') && "
                "!!document.querySelector('[data-testid=agent-result]')"
            )
            check(
                "解释失败显示明确错误",
                "无法连接后端" in explain_error or "解释" in explain_error,
                explain_error[:160],
            )
            check("解释失败时原计算结果仍然存在", bool(retained))
            await cdp.evaluate("window.fetch = window.__omOrigFetch")
            await screenshot(cdp, screenshot_dir, "09c-agent-compute.png")
            await cdp.evaluate("document.querySelector('[data-testid=mode-analysis]').click()")
            await wait_for(
                cdp, "!!document.getElementById('analysis-form')", timeout=15, desc="回到综合分析"
            )
            check("可切回综合分析入口", True)

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
                " input.dispatchEvent(new Event('input',{bubbles:true}));"
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
            # 历史会话的错误状态：后端不可达时必须显示错误，而不是空列表/静默失败
            await cdp.evaluate("document.getElementById('btn-history').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=history-error]')",
                timeout=25,
                desc="历史会话错误状态",
            )
            history_error = await cdp.evaluate(
                "document.querySelector('[data-testid=history-error]').innerText"
            )
            check(
                "后端不可达时历史会话显示明确错误",
                "无法连接后端" in history_error or "请求失败" in history_error,
                history_error[:160],
            )
            await cdp.evaluate(
                "document.querySelector('[data-testid=btn-history-close]').click()"
            )
            # 知识检索的错误状态：后端不可达时不得静默
            await cdp.evaluate("document.querySelector('[data-testid=tab-knowledge]').click()")
            await cdp.evaluate(
                "(() => {const i=document.getElementById('knowledge-query'); i.value='紫微';"
                " i.dispatchEvent(new Event('input',{bubbles:true}));})()"
            )
            await cdp.evaluate("document.querySelector('[data-testid=btn-knowledge-search]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=knowledge-error]')",
                timeout=30,
                desc="知识检索错误状态",
            )
            knowledge_error = await cdp.evaluate(
                "document.querySelector('[data-testid=knowledge-error]').innerText"
            )
            check(
                "后端不可达时知识检索显示明确错误",
                "无法连接后端" in knowledge_error or "检索超时" in knowledge_error,
                knowledge_error[:160],
            )
            # 独立计算在后端不可达时同样必须显示错误
            await cdp.evaluate("document.querySelector('[data-testid=mode-agent]').click()")
            await wait_for(
                cdp,
                "!!document.querySelector('[data-testid=agent-schema-error]')",
                timeout=30,
                desc="独立计算 Schema 错误状态",
            )
            agent_schema_error = await cdp.evaluate(
                "document.querySelector('[data-testid=agent-schema-error]').innerText"
            )
            check(
                "后端不可达时独立计算显示明确错误",
                "无法连接后端" in agent_schema_error,
                agent_schema_error[:160],
            )
            await cdp.evaluate("document.querySelector('[data-testid=mode-analysis]').click()")
            await wait_for(
                cdp, "!!document.getElementById('btn-submit')", timeout=15, desc="回到综合分析表单"
            )
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

            # 12. 请求取消：真实网络节流下点击「取消请求」
            await cdp.send("Network.enable")
            await cdp.send(
                "Network.emulateNetworkConditions",
                {"offline": False, "latency": 4000, "downloadThroughput": -1, "uploadThroughput": -1},
            )
            await cdp.evaluate("document.getElementById('btn-submit').click()")
            await wait_for(
                cdp,
                "!!document.getElementById('results-loading') && !document.getElementById('results-loading').hidden",
                timeout=10,
                desc="加载状态",
            )
            await cdp.evaluate("document.getElementById('btn-cancel').click()")
            cancelled_title = await wait_for(
                cdp,
                "(() => {const title=document.getElementById('error-title');"
                " const view=document.getElementById('results-error');"
                " if (!title || !view || view.hidden) return ''; return title.textContent;})()",
                timeout=20,
                desc="取消后的状态",
            )
            check("取消请求后显示「已取消」状态", "已取消" in cancelled_title, cancelled_title)
            await cdp.send(
                "Network.emulateNetworkConditions",
                {"offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1},
            )
            await cdp.send("Network.disable")

            # 13. 前端无未捕获 JS 错误
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
