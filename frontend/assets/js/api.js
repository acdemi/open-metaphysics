/* 后端 HTTP 客户端：只调用仓库已存在的端点。
 *
 *   GET  /health              -> 后端存活 + 已注册 agent 列表
 *   POST /orchestrate         -> outputs[] + consensus + explanation_detail
 *   GET  /sessions/{id}       -> 持久化会话
 *   GET  /traces/{id}         -> 单次请求的推理追踪
 *
 * 所有失败都被归一化成 ApiError，并保留后端返回的 error.kind / detail，
 * 绝不把失败响应当作成功结果返回。
 */

const API_BASE_KEY = "om.apiBase";

export class ApiError extends Error {
  /**
   * @param {"network"|"timeout"|"cancelled"|"http"} transport
   * @param {string} message
   * @param {{status?: number, kind?: string, body?: any, elapsedMs?: number}} [info]
   */
  constructor(transport, message, info = {}) {
    super(message);
    this.name = "ApiError";
    this.transport = transport; // 传输层失败原因
    this.status = info.status ?? 0;
    this.kind = info.kind || transport; // 后端 error.kind 优先
    this.body = info.body ?? null;
    this.elapsedMs = info.elapsedMs ?? 0;
  }
}

export function defaultApiBase() {
  // `?api=` 表示本次会话的默认后端地址（例如后端不在 8000 端口时），
  // 因此「恢复默认」同样回到该地址，而不是硬编码的 config.js 值。
  const fromQuery = new URLSearchParams(window.location.search).get("api");
  const fromConfig = fromQuery || window.OM_CONFIG?.apiBase || "http://127.0.0.1:8000";
  return String(fromConfig).replace(/\/+$/, "");
}

export function resolveApiBase() {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("api");
  if (fromQuery) {
    try {
      localStorage.setItem(API_BASE_KEY, fromQuery);
    } catch {
      /* localStorage 不可用时忽略 */
    }
    return String(fromQuery).replace(/\/+$/, "");
  }
  try {
    const stored = localStorage.getItem(API_BASE_KEY);
    if (stored) return stored.replace(/\/+$/, "");
  } catch {
    /* 忽略 */
  }
  return defaultApiBase();
}

export function saveApiBase(base) {
  const clean = String(base || "").trim().replace(/\/+$/, "");
  try {
    if (clean) localStorage.setItem(API_BASE_KEY, clean);
    else localStorage.removeItem(API_BASE_KEY);
  } catch {
    /* 忽略 */
  }
  return clean || defaultApiBase();
}

export function resetApiBase() {
  try {
    localStorage.removeItem(API_BASE_KEY);
  } catch {
    /* 忽略 */
  }
  return defaultApiBase();
}

function timeoutMs() {
  const configured = Number(window.OM_CONFIG?.timeoutMs);
  return Number.isFinite(configured) && configured > 0 ? configured : 90000;
}

async function readBody(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text.slice(0, 2000);
  }
}

/**
 * 发送一个 JSON 请求。成功返回 `{data, status, elapsedMs}`；失败抛 ApiError。
 * @param {string} path 形如 "/orchestrate"
 */
export async function request(path, { method = "GET", body = undefined, signal = null, timeout = timeoutMs() } = {}) {
  const base = window.__OM_API_BASE__ || resolveApiBase();
  const controller = new AbortController();
  const started = performance.now();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeout);
  const onExternalAbort = () => controller.abort();
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener("abort", onExternalAbort, { once: true });
  }

  try {
    const init = {
      method,
      cache: "no-store",
      headers: { Accept: "application/json" },
      signal: controller.signal,
    };
    if (body !== undefined) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(body);
    }
    const response = await fetch(`${base}${path}`, init);
    const elapsedMs = Math.round(performance.now() - started);
    const data = await readBody(response);
    if (!response.ok) {
      const backendKind = data && typeof data === "object" && data.error ? data.error.kind : "";
      const message =
        (data && typeof data === "object" && data.error && data.error.message) ||
        (typeof data === "object" && data && data.detail ? JSON.stringify(data.detail) : "") ||
        `HTTP ${response.status}`;
      throw new ApiError("http", message, {
        status: response.status,
        kind: backendKind || `http_${response.status}`,
        body: data,
        elapsedMs,
      });
    }
    return { data, status: response.status, elapsedMs };
  } catch (error) {
    if (error instanceof ApiError) throw error;
    const elapsedMs = Math.round(performance.now() - started);
    if (error && error.name === "AbortError") {
      if (timedOut) {
        throw new ApiError("timeout", `请求超时（${Math.round(timeout / 1000)} 秒）`, { elapsedMs });
      }
      throw new ApiError("cancelled", "请求已取消", { elapsedMs });
    }
    throw new ApiError("network", error?.message || "网络请求失败", { elapsedMs });
  } finally {
    clearTimeout(timer);
    if (signal) signal.removeEventListener("abort", onExternalAbort);
  }
}

/** GET /health */
export async function getHealth(base) {
  window.__OM_API_BASE__ = base;
  const { data, elapsedMs } = await request("/health", { timeout: 8000 });
  if (!data || !Array.isArray(data.agents)) {
    throw new ApiError("http", "健康检查响应格式不符合预期（缺少 agents 数组）", {
      kind: "invalid_response",
      body: data,
      elapsedMs,
    });
  }
  return { ...data, elapsedMs };
}

/** POST /orchestrate —— 前端唯一的分析入口 */
export async function postOrchestrate(payload, { signal } = {}) {
  return request("/orchestrate", { method: "POST", body: payload, signal });
}

export async function getSession(requestId, { timeout = 10000 } = {}) {
  window.__OM_API_BASE__ = window.__OM_API_BASE__ || defaultApiBase();
  return request(`/sessions/${encodeURIComponent(requestId)}`, { timeout });
}

export async function getTraces(requestId, { timeout = 10000 } = {}) {
  window.__OM_API_BASE__ = window.__OM_API_BASE__ || defaultApiBase();
  return request(`/traces/${encodeURIComponent(requestId)}`, { timeout });
}

/**
 * 用 no-cors 探测后端是否可达：能拿到 opaque 响应说明 TCP/HTTP 可达，
 * 从而把「跨域被浏览器拦截」与「后端未启动」区分开。
 * @returns {Promise<boolean>}
 */
export async function probeReachable(base, { timeout = 5000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    await fetch(`${String(base).replace(/\/+$/, "")}/health`, {
      mode: "no-cors",
      cache: "no-store",
      signal: controller.signal,
    });
    return true;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

/** 校验 IANA 时区名在浏览器中是否可用。 */
export function isValidTimeZone(zone) {
  try {
    new Intl.DateTimeFormat("en-US", { timeZone: zone });
    return true;
  } catch {
    return false;
  }
}

/**
 * 把「本地日期 + 本地时间 + IANA 时区」转换为带偏移的 ISO 8601 字符串，
 * 因为后端要求 born_at 必须 timezone-aware。
 * @returns {{iso: string, offsetMinutes: number}}
 */
export function zonedToIso(dateStr, timeStr, zone) {
  const [y, mo, d] = dateStr.split("-").map(Number);
  const [hh, mi] = timeStr.split(":").map(Number);
  if (![y, mo, d, hh, mi].every((n) => Number.isFinite(n))) {
    throw new Error("日期或时间格式非法");
  }
  if (!isValidTimeZone(zone)) throw new Error(`无效的 IANA 时区：${zone}`);

  const offsetFor = (instant) => {
    const dtf = new Intl.DateTimeFormat("en-US", {
      timeZone: zone,
      hourCycle: "h23",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    const parts = {};
    for (const part of dtf.formatToParts(instant)) {
      if (part.type !== "literal") parts[part.type] = part.value;
    }
    const asUtc = Date.UTC(
      Number(parts.year),
      Number(parts.month) - 1,
      Number(parts.day),
      Number(parts.hour),
      Number(parts.minute),
      Number(parts.second),
    );
    return Math.round((asUtc - instant.getTime()) / 60000);
  };

  const naiveUtc = Date.UTC(y, mo - 1, d, hh, mi, 0);
  let offset = offsetFor(new Date(naiveUtc));
  let ts = naiveUtc - offset * 60000;
  // DST 边界修正：用真实时刻再算一次偏移
  const corrected = offsetFor(new Date(ts));
  if (corrected !== offset) {
    offset = corrected;
    ts = naiveUtc - offset * 60000;
  }
  const local = new Date(ts + offset * 60000);
  const pad = (n) => String(n).padStart(2, "0");
  const sign = offset >= 0 ? "+" : "-";
  const abs = Math.abs(offset);
  const iso =
    `${local.getUTCFullYear()}-${pad(local.getUTCMonth() + 1)}-${pad(local.getUTCDate())}` +
    `T${pad(local.getUTCHours())}:${pad(local.getUTCMinutes())}:00` +
    `${sign}${pad(Math.floor(abs / 60))}:${pad(abs % 60)}`;
  return { iso, offsetMinutes: offset };
}
