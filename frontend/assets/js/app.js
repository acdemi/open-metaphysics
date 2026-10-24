/* OpenMetaphysics 前端 MVP 主控制器。
 *
 * 数据流（单一入口，全部来自真实 HTTP 响应）：
 *   表单 -> 校验 -> POST /orchestrate -> outputs / consensus / explanation_detail -> 渲染
 * 健康检查用 GET /health；执行详情可按需读取 GET /sessions/{id} 与 /traces/{id}。
 */

import {
  ApiError,
  getHealth,
  getSession,
  getTraces,
  isValidTimeZone,
  postOrchestrate,
  probeReachable,
  resetApiBase,
  resolveApiBase,
  saveApiBase,
  zonedToIso,
} from "./api.js";
import {
  copyText,
  escapeHtml,
  fmtDateTime,
  fmtNum,
  fmtPercent,
  jsonBlock,
  renderChips,
  safeToken,
  toast,
} from "./ui.js";
import {
  domainLabel,
  renderCalculationCard,
  renderEmptyPanel,
  renderEvidenceCard,
  renderExplanationCard,
} from "./domains.js";

const STATE = {
  apiBase: resolveApiBase(),
  health: null,
  result: null,
  lastPayload: null,
  lastValues: null,
  elapsedMs: 0,
  loading: false,
  abort: null,
  activeTab: "calculation",
  demo: window.OM_CONFIG?.demo || {},
};

const $ = (id) => document.getElementById(id);
const el = {};

const GENDERS = ["male", "female", "unknown"];
const DOMAINS = ["bazi", "ziwei", "qimen", "liuyao"];

/* ===================================================================== init */
document.addEventListener("DOMContentLoaded", init);

function init() {
  cacheElements();
  STATE.apiBase = resolveApiBase();
  window.__OM_API_BASE__ = STATE.apiBase;

  bindForm();
  bindTabs();
  bindSettings();
  bindGlobalActions();
  resetToDemo();

  updateApiBaseLabel();
  updatePreview();
  checkHealth();
  document.body.dataset.appReady = "true";
}

function cacheElements() {
  Object.assign(el, {
    form: $("analysis-form"),
    domainGrid: $("domain-grid"),
    date: $("input-date"),
    time: $("input-time"),
    timezone: $("input-timezone"),
    question: $("input-question"),
    seed: $("input-seed"),
    lat: $("input-lat"),
    lon: $("input-lon"),
    nonce: $("input-nonce"),
    submit: $("btn-submit"),
    reset: $("btn-reset"),
    formErrors: $("form-errors"),
    preview: $("request-preview"),
    healthPill: $("health-pill"),
    healthText: $("health-text"),
    footerApi: $("footer-api"),
    empty: $("results-empty"),
    loading: $("results-loading"),
    loadingElapsed: $("loading-elapsed"),
    loadingTarget: $("loading-target"),
    loadingSteps: $("loading-steps"),
    cancel: $("btn-cancel"),
    error: $("results-error"),
    errorTitle: $("error-title"),
    errorMessage: $("error-message"),
    errorHints: $("error-hints"),
    errorDetail: $("error-detail"),
    errorRaw: $("error-raw"),
    errorRetry: $("btn-error-retry"),
    errorSettings: $("btn-error-settings"),
    results: $("results"),
    summaryStatus: $("summary-status"),
    summaryMeta: $("summary-meta"),
    tabs: $("tabs"),
    panels: {
      calculation: $("panel-calculation"),
      evidence: $("panel-evidence"),
      explanation: $("panel-explanation"),
      consensus: $("panel-consensus"),
      execution: $("panel-execution"),
    },
    tabButtons: {},
    settingsDialog: $("settings-dialog"),
    settingsForm: $("settings-form"),
    settingsApiBase: $("settings-api-base"),
    settingsDefault: $("btn-settings-default"),
    settingsCorsHint: $("settings-cors-hint"),
    openSettings: $("btn-settings"),
  });
  for (const button of el.tabs.querySelectorAll("[data-tab]")) {
    el.tabButtons[button.dataset.tab] = button;
  }
}

/* ==================================================================== form */
function bindForm() {
  el.form.addEventListener("submit", handleSubmit);
  el.form.addEventListener("input", () => updatePreview());
  el.form.addEventListener("change", () => updatePreview());
  el.reset.addEventListener("click", () => {
    resetToDemo();
    updatePreview();
    clearFormErrors();
    showState("empty");
  });
  el.cancel.addEventListener("click", cancelRequest);
  el.errorRetry.addEventListener("click", () => {
    if (STATE.lastPayload) runAnalysis(STATE.lastPayload);
    else showState("empty");
  });
  el.errorSettings.addEventListener("click", openSettings);
  el.healthPill.addEventListener("click", () => checkHealth());
  el.domainGrid.addEventListener("change", (event) => {
    if (event.target.matches('input[name="domain"]')) updatePreview();
  });
}

function resetToDemo() {
  const demo = STATE.demo;
  el.date.value = demo.date || "";
  el.time.value = demo.time || "";
  el.timezone.value = demo.timezone || "Asia/Shanghai";
  el.question.value = demo.question || "";
  el.seed.value = "";
  el.lat.value = "";
  el.lon.value = "";
  el.nonce.value = "";
  const wanted = new Set(demo.domains && demo.domains.length ? demo.domains : ["bazi"]);
  for (const input of el.domainGrid.querySelectorAll('input[name="domain"]')) {
    input.checked = wanted.has(input.value);
  }
  const gender = GENDERS.includes(demo.gender) ? demo.gender : "male";
  const radio = el.form.querySelector(`input[name="gender"][value="${gender}"]`);
  if (radio) radio.checked = true;
}

function collectForm() {
  return {
    domains: [...el.domainGrid.querySelectorAll('input[name="domain"]:checked')].map((input) => input.value),
    date: el.date.value.trim(),
    time: el.time.value.trim(),
    timezone: el.timezone.value.trim(),
    gender: el.form.querySelector('input[name="gender"]:checked')?.value || "unknown",
    question: el.question.value.trim(),
    seed: el.seed.value.trim(),
    lat: el.lat.value.trim(),
    lon: el.lon.value.trim(),
    nonce: el.nonce.value.trim(),
  };
}

/** @returns {{errors: Array<{field: string|null, message: string}>, payload?: object, iso?: string}} */
function buildRequest(values) {
  const errors = [];
  if (!values.domains.length) errors.push({ field: "domains", message: "至少选择一个分析领域。" });
  if (!values.date) errors.push({ field: "date", message: "请填写出生日期。" });
  if (!values.time) errors.push({ field: "time", message: "请填写出生时间。" });
  if (!values.timezone) errors.push({ field: "timezone", message: "请填写 IANA 时区。" });
  else if (!isValidTimeZone(values.timezone)) {
    errors.push({ field: "timezone", message: `浏览器无法识别时区「${values.timezone}」，请使用 IANA 名称，如 Asia/Shanghai。` });
  }
  if (values.question.length > 500) errors.push({ field: "question", message: "问题请控制在 500 字以内。" });
  if (!GENDERS.includes(values.gender)) errors.push({ field: "gender", message: "性别取值非法。" });

  let iso = null;
  if (!errors.some((error) => ["date", "time", "timezone"].includes(error.field))) {
    try {
      const converted = zonedToIso(values.date, values.time, values.timezone);
      iso = converted.iso;
    } catch (error) {
      errors.push({ field: "date", message: `无法转换出生时间：${error.message}` });
    }
  }

  let seed;
  if (values.seed) {
    if (!/^-?\d+$/.test(values.seed)) errors.push({ field: "seed", message: "起卦种子必须是整数。" });
    else seed = Number(values.seed);
  }

  let lat;
  let lon;
  if (values.lat || values.lon) {
    if (!values.lat || !values.lon) {
      errors.push({ field: "lat", message: "经度与纬度需同时填写，或同时留空。" });
    } else {
      lat = Number(values.lat);
      lon = Number(values.lon);
      if (!Number.isFinite(lat) || lat < -90 || lat > 90) errors.push({ field: "lat", message: "纬度必须在 -90 ~ 90 之间。" });
      if (!Number.isFinite(lon) || lon < -180 || lon > 180) errors.push({ field: "lon", message: "经度必须在 -180 ~ 180 之间。" });
    }
  }

  if (errors.length) return { errors };

  const requestId = makeRequestId();
  const payload = {
    request_id: requestId,
    payload: {
      request_id: requestId,
      born_at: iso,
      gender: values.gender,
      locale: "zh-CN",
    },
    agents: values.domains,
    strategy: "weighted",
    explain: true,
  };
  if (values.question) payload.payload.question = values.question;
  if (seed !== undefined) payload.payload.seed = seed;
  if (values.nonce) payload.payload.client_nonce = values.nonce;
  if (Number.isFinite(lat) && Number.isFinite(lon)) {
    payload.payload.born_location = { latitude: lat, longitude: lon, timezone: values.timezone };
  }
  return { errors: [], payload, iso };
}

function makeRequestId() {
  const rand = Math.random().toString(36).slice(2, 8);
  return `ui-${Date.now().toString(36)}-${rand}`;
}

function updatePreview() {
  const values = collectForm();
  const { errors, payload } = buildRequest(values);
  if (errors.length) {
    el.preview.textContent = `// 请求体尚未可生成：\n// ${errors.map((error) => error.message).join("\n// ")}`;
    return;
  }
  const preview = structuredClone(payload);
  preview.request_id = "ui-<提交时生成>";
  preview.payload.request_id = "ui-<提交时生成>";
  el.preview.textContent = JSON.stringify(preview, null, 2);
}

function showFormErrors(errors) {
  el.formErrors.hidden = false;
  el.formErrors.innerHTML = `<strong>请修正以下 ${errors.length} 处输入：</strong><ul>${errors
    .map((error) => `<li>${escapeHtml(error.message)}</li>`)
    .join("")}</ul>`;
  for (const input of el.form.querySelectorAll("[aria-invalid]")) input.removeAttribute("aria-invalid");
  for (const error of errors) {
    const target = fieldElement(error.field);
    if (target) target.setAttribute("aria-invalid", "true");
  }
  const first = errors.map((error) => fieldElement(error.field)).find(Boolean);
  if (first) first.focus({ preventScroll: false });
}

function clearFormErrors() {
  el.formErrors.hidden = true;
  el.formErrors.innerHTML = "";
  for (const input of el.form.querySelectorAll("[aria-invalid]")) input.removeAttribute("aria-invalid");
}

function fieldElement(field) {
  switch (field) {
    case "date":
      return el.date;
    case "time":
      return el.time;
    case "timezone":
      return el.timezone;
    case "question":
      return el.question;
    case "seed":
      return el.seed;
    case "lat":
      return el.lat;
    case "lon":
      return el.lon;
    default:
      return null;
  }
}

/* ================================================================= submit */
async function handleSubmit(event) {
  event.preventDefault();
  if (STATE.loading) return;
  const values = collectForm();
  const { errors, payload } = buildRequest(values);
  clearFormErrors();
  if (errors.length) {
    showFormErrors(errors);
    return;
  }
  STATE.lastValues = values;
  await runAnalysis(payload);
}

function cancelRequest() {
  if (STATE.abort) STATE.abort.abort();
}

async function runAnalysis(payload) {
  STATE.loading = true;
  STATE.abort = new AbortController();
  STATE.lastPayload = payload;
  STATE.lastValues = STATE.lastValues || collectForm();
  setSubmitLoading(true);
  showState("loading");
  startLoadingUi(payload);

  const started = performance.now();
  try {
    const { data, elapsedMs } = await postOrchestrate(payload, { signal: STATE.abort.signal });
    STATE.result = data;
    STATE.elapsedMs = elapsedMs || Math.round(performance.now() - started);
    stopLoadingUi(true);
    renderResult(data);
    showState("results");
    toast("分析完成");
    if (window.matchMedia("(max-width: 1040px)").matches) {
      el.results.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  } catch (error) {
    stopLoadingUi(false);
    if (error instanceof ApiError && error.kind === "cancelled") {
      showErrorCard({
        title: "已取消请求",
        message: "本次分析已取消，后端可能仍完成了计算；可重新提交。",
        hints: [],
      });
    } else {
      await showRequestError(error);
    }
  } finally {
    STATE.loading = false;
    STATE.abort = null;
    setSubmitLoading(false);
  }
}

function setSubmitLoading(loading) {
  el.submit.disabled = loading;
  el.submit.dataset.loading = loading ? "true" : "false";
  el.submit.querySelector(".btn-label").textContent = loading ? "分析中…" : "开始分析";
  el.reset.disabled = loading;
}

let loadingTimer = null;
function startLoadingUi(payload) {
  const domains = (payload.agents || []).map((agent) => domainLabel(agent)).join(" · ");
  el.loadingTarget.textContent = `${domains} → ${STATE.apiBase}/orchestrate`;
  for (const item of el.loadingSteps.querySelectorAll("li")) delete item.dataset.state;
  setStep("submit", "active");
  const start = performance.now();
  el.loadingElapsed.textContent = "0.0";
  clearInterval(loadingTimer);
  loadingTimer = setInterval(() => {
    el.loadingElapsed.textContent = ((performance.now() - start) / 1000).toFixed(1);
  }, 100);
  // 请求发出后进入等待阶段（后端在一次请求内完成计算 + 检索 + 解释）
  setTimeout(() => {
    if (STATE.loading) setStep("compute", "active");
  }, 150);
}

function setStep(name, stateName) {
  const item = el.loadingSteps.querySelector(`li[data-step="${name}"]`);
  if (item) item.dataset.state = stateName;
}

function stopLoadingUi(success) {
  clearInterval(loadingTimer);
  loadingTimer = null;
  if (success) {
    setStep("submit", "done");
    setStep("compute", "done");
    setStep("render", "done");
  } else {
    for (const item of el.loadingSteps.querySelectorAll("li")) delete item.dataset.state;
  }
}

/* ================================================================ results */
function showState(name) {
  el.empty.hidden = name !== "empty";
  el.loading.hidden = name !== "loading";
  el.error.hidden = name !== "error";
  el.results.hidden = name !== "results";
}

function showErrorCard({ title, message, hints = [], raw = null }) {
  el.errorTitle.textContent = title;
  el.errorMessage.textContent = message;
  el.errorHints.innerHTML = hints.map((hint) => `<li>${hint}</li>`).join("");
  el.errorDetail.hidden = !raw;
  el.errorRaw.textContent = raw ? (typeof raw === "string" ? raw : JSON.stringify(raw, null, 2)) : "";
  showState("error");
}

async function showRequestError(error) {
  const apiError = error instanceof ApiError ? error : null;
  const base = STATE.apiBase;

  if (!apiError || apiError.transport === "network") {
    const reachable = await probeReachable(base);
    if (reachable) {
      showErrorCard({
        title: "浏览器拦截了跨域响应（CORS）",
        message:
          "后端端口可达，但浏览器未能读取响应，通常是后端未允许当前页面来源。请按下面的方式重启后端后重试。",
        hints: [
          `当前页面来源：<code>${escapeHtml(window.location.origin)}</code>`,
          "启动后端时加入：<code>OM_CORS_ORIGINS=http://127.0.0.1:5173</code>（PowerShell：<code>$env:OM_CORS_ORIGINS='http://127.0.0.1:5173'</code>）",
          "也可以把前端与后端放在同一来源，或在上方 ⚙ 设置中改用可访问的 API 地址。",
        ],
        raw: apiError?.message,
      });
    } else {
      showErrorCard({
        title: "无法连接后端",
        message: `请求 ${base}/orchestrate 失败，浏览器没有收到任何响应。`,
        hints: [
          "确认后端已启动：<code>uv run openmetaphysics</code>（默认监听 127.0.0.1:8000）",
          `确认当前 API 地址正确：<code>${escapeHtml(base)}</code>（可在 ⚙ 设置中修改）`,
          "确认没有防火墙/代理拦截本地端口。",
        ],
        raw: apiError?.message || String(error),
      });
    }
    return;
  }

  if (apiError.transport === "timeout") {
    showErrorCard({
      title: "请求超时",
      message: apiError.message,
      hints: [
        "多域联合分析（尤其包含解释与知识检索）可能较慢；可减少领域后重试。",
        "确认后端进程仍在运行，且没有被调试器/代理挂起。",
      ],
      raw: apiError.body || null,
    });
    return;
  }

  if (apiError.transport === "http") {
    const kind = apiError.kind || "";
    const body = apiError.body;
    const fieldErrors =
      body && typeof body === "object" && body.error && Array.isArray(body.error.fields)
        ? body.error.fields.map((loc) => (Array.isArray(loc) ? loc.join(".") : String(loc)))
        : [];
    const detailMessages =
      body && typeof body === "object" && Array.isArray(body.detail)
        ? body.detail.map((item) => (item && item.msg ? `${(item.loc || []).join(".")}: ${item.msg}` : String(item)))
        : [];

    const titles = {
      invalid_request: "请求参数未通过后端校验（422）",
      unknown_agent: "未知的分析领域（404）",
      calculation_failed: "后端确定性计算失败（500）",
      internal_error: "后端内部错误（500）",
      not_found: "资源不存在（404）",
    };
    const hints = [];
    if (fieldErrors.length) hints.push(`后端指出的字段：<code>${escapeHtml(fieldErrors.join("、"))}</code>`);
    if (detailMessages.length) hints.push(`校验详情：${detailMessages.map((m) => `<code>${escapeHtml(m)}</code>`).join("；")}`);
    if (!fieldErrors.length && !detailMessages.length) hints.push(`后端返回：<code>${escapeHtml(JSON.stringify(body || {}).slice(0, 400))}</code>`);

    showErrorCard({
      title: titles[kind] || `请求失败（HTTP ${apiError.status}）`,
      message: apiError.message || `后端返回 HTTP ${apiError.status}`,
      hints,
      raw: body,
    });
    return;
  }

  showErrorCard({
    title: "请求失败",
    message: apiError?.message || String(error),
    hints: ["可重试；如果持续失败，请查看后端日志。"],
    raw: error,
  });
}

/* -------------------------------------------------------------- summary */
function renderResult(data) {
  const outputs = Array.isArray(data.outputs) ? data.outputs : [];
  const errors = Array.isArray(data.errors) ? data.errors : [];
  const consensus = data.consensus || null;
  const detail = data.explanation_detail || {};

  const statusBadge =
    errors.length > 0
      ? `<span class="badge badge-warn">部分完成</span>`
      : `<span class="badge badge-ok">分析完成</span>`;
  const domainNames = outputs.map((output) => domainLabel(output.agent)).join(" · ") || "（无结果）";
  const computedAt = outputs
    .map((output) => output.computed_at)
    .filter(Boolean)
    .sort()
    .pop();

  el.summaryStatus.innerHTML = `
    ${statusBadge}
    <h2>${escapeHtml(domainNames)} 分析结果</h2>
    <button type="button" class="btn btn-small" data-action="rerun" style="margin-left:auto">再次分析</button>`;

  el.summaryMeta.innerHTML = `
    <div><dt>请求 ID</dt><dd>${escapeHtml(data.request_id || "—")} <button type="button" class="copy-inline" data-action="copy-request-id">复制</button></dd></div>
    <div><dt>耗时</dt><dd>${(STATE.elapsedMs / 1000).toFixed(2)} s</dd></div>
    <div><dt>计算完成时间</dt><dd>${escapeHtml(fmtDateTime(computedAt))}</dd></div>
    <div><dt>共识</dt><dd>${consensus ? "已返回" : "未返回（需 ≥2 个域成功）"}</dd></div>
    <div><dt>后端</dt><dd>${escapeHtml(STATE.apiBase)}</dd></div>`;

  // counts
  const knowledgeCount = Object.values(detail).reduce(
    (sum, item) => sum + (Array.isArray(item?.knowledge) ? item.knowledge.length : 0),
    0,
  );
  setTabCount("calculation", outputs.length ? `${outputs.length}` : "");
  setTabCount("evidence", knowledgeCount ? `${knowledgeCount}` : "");
  setTabCount("explanation", outputs.length ? `${outputs.length}` : "");

  // consensus tab visibility
  el.tabButtons.consensus.hidden = !consensus;
  if (!consensus && STATE.activeTab === "consensus") STATE.activeTab = "calculation";

  // panels
  el.panels.calculation.innerHTML =
    outputs.map((output, index) => renderCalculationCard(output, index)).join("") ||
    renderEmptyPanel("后端未返回任何域的计算结果。");

  el.panels.evidence.innerHTML =
    outputs.map((output, index) => renderEvidenceCard(output.agent, detail[output.agent], index)).join("") ||
    renderEmptyPanel("没有可展示的知识证据。");

  el.panels.explanation.innerHTML =
    outputs.map((output, index) => renderExplanationCard(output.agent, detail[output.agent], index)).join("") ||
    renderEmptyPanel("没有可展示的解释。");

  el.panels.consensus.innerHTML = consensus
    ? renderConsensus(consensus)
    : renderEmptyPanel("本次运行没有返回共识：/orchestrate 仅在至少两个域都成功产出结果时生成共识。");

  el.panels.execution.innerHTML = renderExecution(data, outputs, errors);

  if (errors.length) {
    el.panels.calculation.insertAdjacentHTML(
      "afterbegin",
      `<div class="card"><div class="card-head"><h3>运行时有部分域失败</h3><div class="source-strip"><span class="badge badge-warn">errors</span></div></div>
        <div class="card-body"><ul class="error-hints">${errors
          .map((message) => `<li>${escapeHtml(message)}</li>`)
          .join("")}</ul></div></div>`,
    );
  }

  activateTab(STATE.activeTab || "calculation");
}

function setTabCount(name, value) {
  const node = el.tabs.querySelector(`[data-count="${name}"]`);
  if (node) node.textContent = value || "";
}

/* ----------------------------------------------------------- consensus */
function renderConsensus(consensus) {
  const result = consensus.result || {};
  const contributions = Array.isArray(result.contributions) ? result.contributions : [];
  const conflicts = Array.isArray(result.conflicts) ? result.conflicts : [];
  const matrix = result.agreement_matrix && typeof result.agreement_matrix === "object" ? result.agreement_matrix : {};
  const agents = Object.keys(matrix);
  const overall = typeof result.overall_confidence === "number" ? result.overall_confidence : null;

  const contributionRows = contributions
    .map(
      (item) => `<tr>
        <td>${escapeHtml(domainLabel(item.agent) || item.agent)}</td>
        <td class="num">${fmtPercent(item.confidence)}</td>
        <td class="num">${fmtNum(item.weight, 2)}</td>
        <td>${escapeHtml(item.element || "—")}</td>
        <td>${escapeHtml(item.summary || "—")}</td>
      </tr>`,
    )
    .join("");

  const matrixHead = `<tr><th>—</th>${agents.map((a) => `<th>${escapeHtml(domainLabel(a))}</th>`).join("")}</tr>`;
  const matrixRows = agents
    .map(
      (row) => `<tr><th>${escapeHtml(domainLabel(row))}</th>${agents
        .map((col) => {
          const value = matrix[row]?.[col];
          const level = typeof value === "number" ? (value >= 0.7 ? "high" : value >= 0.45 ? "mid" : "low") : "low";
          return `<td data-level="${level}">${typeof value === "number" ? value.toFixed(2) : "—"}</td>`;
        })
        .join("")}</tr>`,
    )
    .join("");

  const conflictItems = conflicts.length
    ? conflicts
        .map(
          (conflict) => `<div class="conflict-item">
        <span class="badge badge-warn">${escapeHtml(conflict.severity || "conflict")}</span>
        <span>字段 <code>${escapeHtml(conflict.field || "—")}</code>：
          ${(conflict.agents || []).map((a) => escapeHtml(domainLabel(a))).join(" / ")}
          给出不同值 ${(conflict.values || []).map((v) => `<strong>${escapeHtml(v)}</strong>`).join(" vs ")}</span>
      </div>`,
        )
        .join("")
    : `<div class="empty-inline">后端未检测到跨域冲突。</div>`;

  return `<article class="card" data-testid="consensus-card">
    <div class="card-head">
      <h3>综合共识 <span class="card-sub">${escapeHtml(consensus.engine_version || "")} · ${escapeHtml(consensus.request_id || "")}</span></h3>
      <div class="source-strip">
        <span class="badge badge-fact">后端 Consensus 引擎</span>
        ${result.recommendation ? `<span class="badge badge-interpret">建议：${escapeHtml(result.recommendation)}</span>` : ""}
      </div>
    </div>
    <div class="card-body">
      <div class="consensus-hero">
        <div class="confidence-gauge">
          <div class="confidence-value">${overall == null ? "—" : fmtPercent(overall, 1)}</div>
          <div class="confidence-label">综合置信度 overall_confidence</div>
          <div class="meter"><span style="width:${overall == null ? 0 : Math.max(0, Math.min(100, overall * 100))}%"></span></div>
          <div class="confidence-label" style="margin-top:8px">策略 ${escapeHtml(consensus.metadata?.strategy || "—")} · ${escapeHtml(consensus.metadata?.agent_count ?? "—")} 个域</div>
        </div>
        <div>
          <p class="card-note" style="margin-bottom:6px"><strong>合成结论（后端 synthesis 字段原文）：</strong></p>
          <div class="synthesis-text">${escapeHtml(result.synthesis || "—")}</div>
        </div>
      </div>

      <div>
        <p class="card-note" style="margin-bottom:6px">各域贡献：</p>
        <div class="table-wrap"><table class="data">
          <thead><tr><th>域</th><th>置信度</th><th>权重</th><th>五行</th><th>摘要</th></tr></thead>
          <tbody>${contributionRows || `<tr><td colspan="5">无</td></tr>`}</tbody>
        </table></div>
      </div>

      <div>
        <p class="card-note" style="margin-bottom:6px">冲突：</p>
        <div style="display:flex;flex-direction:column;gap:6px">${conflictItems}</div>
      </div>

      <div>
        <p class="card-note" style="margin-bottom:6px">一致性矩阵：</p>
        <div class="table-wrap"><table class="matrix">${matrixHead}${matrixRows}</table></div>
      </div>

      <p class="card-note">共识由后端 <code>ConsensusAgent</code> 基于各域已算出的置信度与五行标签合成；前端不做任何加权或再计算。</p>
      ${jsonBlock(consensus, "raw-consensus")}
    </div>
  </article>`;
}

/* ----------------------------------------------------------- execution */
function renderExecution(data, outputs, errors) {
  const cards = outputs
    .map((output, index) => {
      const confidence = output.confidence || {};
      const metaChips = renderChips(output.metadata || {});
      const trace = Array.isArray(output.reasoning_trace) ? output.reasoning_trace : [];
      const traceHtml = trace.length
        ? `<ul class="trace-list">${trace
            .map(
              (step) => `<li class="trace-item">
            <span class="trace-step">${escapeHtml(step.step)}</span>
            <div>
              <div class="trace-head">
                <span class="trace-ref">${escapeHtml(step.rule_ref)}</span>
                <span class="trace-desc">${escapeHtml(step.description)}</span>
              </div>
              ${renderChips({ ...prefixKeys("in", step.inputs), ...prefixKeys("out", step.outputs) })}
            </div>
          </li>`,
            )
            .join("")}</ul>`
        : `<div class="empty-inline">该域未返回 reasoning_trace。</div>`;

      return `<article class="card" data-testid="execution-card-${safeToken(output.agent)}">
        <div class="card-head">
          <h3>${escapeHtml(domainLabel(output.agent))} 执行信封</h3>
          <div class="source-strip"><span class="badge badge-neutral">AgentOutput</span></div>
        </div>
        <div class="card-body">
          <div class="kv-grid">
            ${execKv("request_id", output.request_id, true)}
            ${execKv("agent", output.agent)}
            ${execKv("engine_version", output.engine_version)}
            ${execKv("computed_at", fmtDateTime(output.computed_at))}
            ${execKv("confidence", `${fmtPercent(confidence.value)} · ${confidence.method || "—"}`)}
            ${execKv("input_hash", output.input_hash, true)}
          </div>
          ${metaChips}
          <div>
            <p class="card-note" style="margin-bottom:6px">推理追踪（reasoning_trace，共 ${trace.length} 步）：</p>
            ${traceHtml}
          </div>
          ${jsonBlock(output, `raw-output-${safeToken(output.agent)}`)}
        </div>
      </article>`;
    })
    .join("");

  const errorBlock = errors.length
    ? `<ul class="error-hints">${errors.map((message) => `<li>${escapeHtml(message)}</li>`).join("")}</ul>`
    : `<div class="empty-inline">本次运行没有 per-agent 错误。</div>`;

  return `<article class="card" data-testid="execution-overview">
      <div class="card-head">
        <h3>请求级执行信息</h3>
        <div class="source-strip"><span class="badge badge-neutral">/orchestrate</span></div>
      </div>
      <div class="card-body">
        <div class="kv-grid">
          ${execKv("request_id", data.request_id, true)}
          ${execKv("agents（请求）", (STATE.lastValues?.domains || []).join(", ") || "—")}
          ${execKv("explain", "true")}
          ${execKv("strategy", "weighted")}
          ${execKv("HTTP 耗时", `${(STATE.elapsedMs / 1000).toFixed(2)} s`)}
          ${execKv("会话 / 追踪", "可按下按钮从后端读取")}
        </div>
        <div class="state-actions" style="margin-top:0">
          <button type="button" class="btn btn-small" data-action="load-session" data-request-id="${escapeHtml(data.request_id || "")}" data-testid="btn-load-session">读取会话 GET /sessions/{id}</button>
          <button type="button" class="btn btn-small" data-action="load-traces" data-request-id="${escapeHtml(data.request_id || "")}" data-testid="btn-load-traces">读取追踪 GET /traces/{id}</button>
        </div>
        <pre id="session-trace-output" data-testid="session-trace-output" hidden></pre>
        <div>
          <p class="card-note" style="margin-bottom:6px">per-agent 错误（errors[]）：</p>
          ${errorBlock}
        </div>
        <div>
          <p class="card-note" style="margin-bottom:6px">本次请求体（与发送内容一致，仅 request_id 由提交时生成）：</p>
          ${jsonBlock(STATE.lastPayload, "raw-request")}
        </div>
      </div>
    </article>${cards}`;
}

function execKv(label, value, mono = false) {
  return `<div class="kv"><dt>${escapeHtml(label)}</dt><dd class="${mono ? "mono" : ""}">${escapeHtml(value)}</dd></div>`;
}

function prefixKeys(prefix, obj) {
  const out = {};
  for (const [key, value] of Object.entries(obj || {})) out[`${prefix}:${key}`] = value;
  return out;
}

/* ------------------------------------------------------------- tabs */
function bindTabs() {
  el.tabs.addEventListener("click", (event) => {
    const button = event.target.closest("[data-tab]");
    if (!button || button.hidden) return;
    activateTab(button.dataset.tab);
  });
  el.tabs.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    const buttons = [...el.tabs.querySelectorAll("[data-tab]")].filter((button) => !button.hidden);
    const current = buttons.findIndex((button) => button.dataset.tab === STATE.activeTab);
    let next = current;
    if (event.key === "ArrowRight") next = (current + 1) % buttons.length;
    if (event.key === "ArrowLeft") next = (current - 1 + buttons.length) % buttons.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = buttons.length - 1;
    if (next >= 0 && buttons[next]) {
      event.preventDefault();
      activateTab(buttons[next].dataset.tab);
      buttons[next].focus();
    }
  });
}

function activateTab(name) {
  if (!el.tabButtons[name] || el.tabButtons[name].hidden) name = "calculation";
  STATE.activeTab = name;
  for (const [tabName, button] of Object.entries(el.tabButtons)) {
    const selected = tabName === name;
    button.setAttribute("aria-selected", selected ? "true" : "false");
    button.tabIndex = selected ? 0 : -1;
  }
  for (const [panelName, panel] of Object.entries(el.panels)) {
    panel.hidden = panelName !== name;
  }
}

/* ------------------------------------------------------------- actions */
function bindGlobalActions() {
  document.addEventListener("click", async (event) => {
    const actionEl = event.target.closest("[data-action]");
    if (!actionEl) return;
    const action = actionEl.dataset.action;

    if (action === "toggle-evidence") {
      const item = actionEl.closest(".evidence-item");
      const text = item?.querySelector(".evidence-text");
      if (!text) return;
      const clamped = text.classList.toggle("clamped");
      actionEl.textContent = clamped ? "展开全文" : "收起";
      return;
    }

    if (action === "copy-request-id") {
      const text = STATE.result?.request_id || "";
      const ok = await copyText(text);
      toast(ok ? "已复制请求 ID" : "复制失败，请手动选择");
      return;
    }

    if (action === "rerun") {
      if (!STATE.lastPayload) return;
      const values = collectForm();
      const { errors, payload } = buildRequest(values);
      clearFormErrors();
      if (errors.length) {
        showFormErrors(errors);
        showState("results");
        return;
      }
      STATE.lastValues = values;
      await runAnalysis(payload);
      return;
    }

    if (action === "load-session" || action === "load-traces") {
      const requestId = actionEl.dataset.requestId;
      if (!requestId) return;
      const target = $("session-trace-output");
      if (!target) return;
      target.hidden = false;
      target.textContent = "读取中…";
      actionEl.disabled = true;
      try {
        const response = action === "load-session" ? await getSession(requestId) : await getTraces(requestId);
        target.textContent = JSON.stringify(response.data, null, 2);
        toast(action === "load-session" ? "已读取会话" : "已读取追踪");
      } catch (error) {
        const message = error instanceof ApiError ? `${error.kind}: ${error.message}` : String(error);
        target.textContent = `读取失败（${message}）`;
        toast("读取失败");
      } finally {
        actionEl.disabled = false;
      }
    }
  });
}

/* ------------------------------------------------------------- health */
async function checkHealth() {
  el.healthPill.dataset.state = "checking";
  el.healthText.textContent = "正在检测后端…";
  el.healthPill.title = "点击重新检测后端状态";
  try {
    const health = await getHealth(STATE.apiBase);
    STATE.health = health;
    el.healthPill.dataset.state = "ok";
    el.healthText.textContent = `后端正常 · ${health.agents.length} 个域`;
    el.healthPill.title = `已注册域：${health.agents.join(", ")}\n耗时 ${health.elapsedMs}ms\n点击重新检测`;
    updateDomainAvailability(health.agents);
  } catch (error) {
    STATE.health = null;
    el.healthPill.dataset.state = "down";
    el.healthText.textContent = "后端不可用";
    el.healthPill.title = `${error instanceof ApiError ? `${error.kind}: ${error.message}` : String(error)}\n点击重试`;
  }
}

function updateDomainAvailability(agents) {
  const available = new Set(agents || []);
  for (const input of el.domainGrid.querySelectorAll('input[name="domain"]')) {
    const supported = available.has(input.value);
    input.disabled = !supported;
    const card = input.closest(".domain-card");
    if (card) {
      card.title = supported ? "" : `后端未注册该域（${input.value}）`;
    }
    if (!supported) input.checked = false;
  }
  if (![...el.domainGrid.querySelectorAll('input[name="domain"]:checked')].length) {
    const bazi = el.domainGrid.querySelector('input[name="domain"][value="bazi"]');
    if (bazi && !bazi.disabled) bazi.checked = true;
  }
  const extras = [...available].filter((name) => !DOMAINS.includes(name));
  if (extras.length) {
    el.footerApi.textContent = `后端地址：${STATE.apiBase} · 后端还注册了未在此界面展示的域：${extras.join(", ")}`;
  } else {
    updateApiBaseLabel();
  }
}

/* ------------------------------------------------------------- settings */
function bindSettings() {
  el.openSettings.addEventListener("click", openSettings);
  el.settingsForm.addEventListener("submit", (event) => {
    event.preventDefault();
    STATE.apiBase = saveApiBase(el.settingsApiBase.value);
    window.__OM_API_BASE__ = STATE.apiBase;
    updateApiBaseLabel();
    el.settingsDialog.close();
    checkHealth();
  });
  el.settingsDefault.addEventListener("click", () => {
    STATE.apiBase = resetApiBase();
    window.__OM_API_BASE__ = STATE.apiBase;
    el.settingsApiBase.value = STATE.apiBase;
    updateApiBaseLabel();
    checkHealth();
  });
}

function openSettings() {
  el.settingsApiBase.value = STATE.apiBase;
  el.settingsCorsHint.textContent = `OM_CORS_ORIGINS=${window.location.origin}`;
  if (typeof el.settingsDialog.showModal === "function") el.settingsDialog.showModal();
  else el.settingsDialog.setAttribute("open", "");
}

function updateApiBaseLabel() {
  el.footerApi.textContent = `后端地址：${STATE.apiBase}`;
}

/* ------------------------------------------------------- bootstrapping */
export { STATE, collectForm, buildRequest, runAnalysis };
