/* 通用 UI 工具：转义、时间格式化、JSON 展示、复制、toast、六十四卦名表。 */

export function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** 仅用于受控标签名（domain id / badge class），避免把外部字符串注入 class。 */
export function safeToken(value, allowed = /[^a-z0-9_-]/gi) {
  return String(value ?? "").replace(allowed, "");
}

export function fmtDateTime(iso) {
  if (!iso) return "—";
  const d = new Date(String(iso).replace(/(\.\d{3})\d+/, "$1"));
  if (Number.isNaN(d.getTime())) return String(iso);
  try {
    const base = new Intl.DateTimeFormat("zh-CN", {
      dateStyle: "medium",
      timeStyle: "medium",
    }).format(d);
    const zone = timeZoneLabel(d);
    return zone ? `${base} ${zone}` : base;
  } catch {
    return d.toISOString();
  }
}

function timeZoneLabel(date) {
  try {
    const parts = new Intl.DateTimeFormat("en-US", { timeZoneName: "short" }).formatToParts(date);
    return parts.find((part) => part.type === "timeZoneName")?.value || "";
  } catch {
    return "";
  }
}

export function fmtOffset(minutes) {
  const sign = minutes >= 0 ? "+" : "-";
  const abs = Math.abs(minutes);
  const hh = String(Math.floor(abs / 60)).padStart(2, "0");
  const mm = String(abs % 60).padStart(2, "0");
  return `UTC${sign}${hh}:${mm}`;
}

/** 数字保留固定小数位，非数字返回「—」。 */
export function fmtNum(value, digits = 2) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "—";
}

export function fmtPercent(value, digits = 1) {
  return typeof value === "number" && Number.isFinite(value) ? `${(value * 100).toFixed(digits)}%` : "—";
}

export function isPlainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** 人类可读的 JSON 块（原始响应展示）。 */
export function jsonBlock(value, testid = "") {
  const idAttr = testid ? ` data-testid="${escapeHtml(testid)}"` : "";
  return `<details class="raw"><summary>查看原始 JSON</summary><pre${idAttr}>${escapeHtml(
    JSON.stringify(value, null, 2),
  )}</pre></details>`;
}

export function renderChips(obj) {
  const entries = Object.entries(obj || {});
  if (!entries.length) return "";
  const chips = entries
    .map(([k, v]) => `<span class="chip"><b>${escapeHtml(k)}</b>${escapeHtml(formatScalar(v))}</span>`)
    .join("");
  return `<div class="chips">${chips}</div>`;
}

function formatScalar(value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(3);
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    try {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand("copy");
      ta.remove();
      return ok;
    } catch {
      return false;
    }
  }
}

let toastEl = null;
let toastTimer = null;
export function toast(message) {
  if (!toastEl) {
    toastEl = document.createElement("div");
    toastEl.className = "toast";
    toastEl.setAttribute("role", "status");
    document.body.appendChild(toastEl);
  }
  toastEl.textContent = message;
  toastEl.dataset.show = "true";
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.dataset.show = "false";
  }, 2200);
}

/* 六十四卦（King Wen 序）— 与 src/openmetaphysics/core/models.py::HEXAGRAMS 同名同序。
 * 仅用于把后端返回的卦序号渲染成卦名，不参与任何计算。 */
export const HEXAGRAM_NAMES = [
  "乾", "坤", "屯", "蒙", "需", "讼", "师", "比", "小畜", "履", "泰", "否",
  "同人", "大有", "谦", "豫", "随", "蛊", "临", "观", "噬嗑", "贲", "剥", "复",
  "无妄", "大畜", "颐", "大过", "坎", "离", "咸", "恒", "遯", "大壮", "晋", "明夷",
  "家人", "睽", "蹇", "解", "损", "益", "夬", "姤", "萃", "升", "困", "井",
  "革", "鼎", "震", "艮", "渐", "归妹", "丰", "旅", "巽", "兑", "涣", "节",
  "中孚", "小过", "既济", "未济",
];

export function hexagramName(num) {
  if (!Number.isInteger(num) || num < 1 || num > 64) return null;
  return HEXAGRAM_NAMES[num - 1];
}

/** 九宫（洛书方位）显示顺序：巽4 离9 坤2 / 震3 中5 兑7 / 艮8 坎1 乾6 */
export const QIMEN_PALACE_ORDER = [4, 9, 2, 3, 5, 7, 8, 1, 6];
