/* 领域结果渲染：把后端真实返回的 result / explain 数据映射成可读卡片。
 *
 * 约定（与后端语义一致，不得混淆）：
 *   - 计算卡片只渲染 AgentOutput.result（确定性事实）
 *   - 证据卡片只渲染 explanation_detail[agent].knowledge（检索到的语料 + 来源）
 *   - 解释卡片只渲染 explanation_detail[agent].explanation（生成文本）
 * 渲染层不做任何推算、不补齐后端未返回的字段。
 */

import {
  escapeHtml,
  fmtDateTime,
  fmtNum,
  fmtPercent,
  hexagramName,
  jsonBlock,
  QIMEN_PALACE_ORDER,
  renderChips,
  safeToken,
} from "./ui.js";

export const DOMAIN_LABELS = {
  bazi: "八字",
  ziwei: "紫微",
  qimen: "奇门",
  liuyao: "六爻",
};

const POSITION_LABELS = {
  year: "年柱",
  month: "月柱",
  day: "日柱",
  hour: "时柱",
};

/* 后端用 ASCII 枚举（yang/yin）表示阴阳，这里只做显示层中文映射。 */
const YIN_YANG_LABELS = { yang: "阳", yin: "阴" };

export function domainLabel(agent) {
  return DOMAIN_LABELS[agent] || String(agent || "未知域");
}

function kv(label, value, { mono = false } = {}) {
  return `<div class="kv"><dt>${escapeHtml(label)}</dt><dd class="${mono ? "mono" : ""}">${value}</dd></div>`;
}

function badge(text, cls) {
  return `<span class="badge ${cls}">${escapeHtml(text)}</span>`;
}

function identityNote(kind) {
  const map = {
    fact: "此卡内容为后端确定性引擎的原始计算结果，未经前端加工。",
    evidence: "知识证据为后端从冻结语料中检索到的片段与来源；它是解释的上下文，不构成对该结论的证明。",
    interpret: "解释是对上面计算事实的自然语言重述；它不改变、也不补全计算结果。",
  };
  return `<p class="card-note">${escapeHtml(map[kind])}</p>`;
}

/* ------------------------------------------------------------ 八字 / BaZi */
function renderBazi(result) {
  const pillars = Array.isArray(result.pillars) ? result.pillars : [];
  const order = ["year", "month", "day", "hour"];
  const byPosition = {};
  for (const pillar of pillars) byPosition[pillar.position] = pillar;

  const head = order
    .map((pos) => `<div class="ph">${escapeHtml(POSITION_LABELS[pos] || pos)}</div>`)
    .join("");

  const stemRow = order
    .map((pos) => {
      const p = byPosition[pos];
      return p
        ? `<div class="glyph">${escapeHtml(p.stem)}</div>`
        : `<div class="sub">—</div>`;
    })
    .join("");
  const branchRow = order
    .map((pos) => {
      const p = byPosition[pos];
      return p
        ? `<div class="glyph-branch">${escapeHtml(p.branch)}</div>`
        : `<div class="sub">—</div>`;
    })
    .join("");
  const hiddenRow = order
    .map((pos) => {
      const p = byPosition[pos];
      return `<div class="sub">${escapeHtml((p?.hidden_stems || []).join(" · ") || "—")}</div>`;
    })
    .join("");
  const nayinRow = order
    .map((pos) => {
      const p = byPosition[pos];
      return `<div class="sub">${escapeHtml(p?.nayin || "—")}</div>`;
    })
    .join("");
  const tenGodRow = order
    .map((pos) => {
      const p = byPosition[pos];
      return `<div class="ten-god">${escapeHtml(p?.ten_god || "—")}</div>`;
    })
    .join("");

  const table = `
    <div class="pillars" role="table" aria-label="四柱">
      <div class="ph">四柱</div>${head}
      <div class="ph">天干</div>${stemRow}
      <div class="ph">地支</div>${branchRow}
      <div class="ph">藏干</div>${hiddenRow}
      <div class="ph">纳音</div>${nayinRow}
      <div class="ph">十神</div>${tenGodRow}
    </div>`;

  const dayun = Array.isArray(result.dayun) ? result.dayun : [];
  const dayunTable = dayun.length
    ? `<div class="table-wrap"><table class="data">
        <thead><tr><th>大运</th><th>起止年龄</th><th>干支</th><th>起始时间</th></tr></thead>
        <tbody>${dayun
          .map(
            (d) => `<tr>
              <td class="num">${escapeHtml(d.index)}</td>
              <td>${escapeHtml(d.start_age)}–${escapeHtml(d.end_age)} 岁</td>
              <td><strong>${escapeHtml(d.stem)}${escapeHtml(d.branch)}</strong></td>
              <td>${escapeHtml(fmtDateTime(d.start_at))}</td>
            </tr>`,
          )
          .join("")}</tbody>
      </table></div>`
    : `<div class="empty-inline">后端未返回大运数据。</div>`;

  const tenGodsMap = result.ten_gods_map && typeof result.ten_gods_map === "object" ? result.ten_gods_map : {};

  return `
    <div class="kv-grid">
      ${kv("日主", `<strong>${escapeHtml(result.day_master)}</strong>（${escapeHtml(result.day_master_element)}）`)}
      ${kv("月令（节）", escapeHtml(result.month_boundary || "—"))}
      ${kv("立春年界", escapeHtml(fmtDateTime(result.year_boundary)))}
      ${kv("性别处理", result.gender_assumed ? "未提供性别，后端按 unknown 推定" : "已按提供的性别计算大运方向")}
    </div>
    ${table}
    ${
      Object.keys(tenGodsMap).length
        ? `<div><p class="card-note" style="margin-bottom:6px">十神对照（含藏干）：</p>${renderChips(tenGodsMap)}</div>`
        : ""
    }
    <div>
      <p class="card-note" style="margin-bottom:6px">大运（${dayun.length} 步）：</p>
      ${dayunTable}
    </div>
    ${identityNote("fact")}
    ${jsonBlock(result, "raw-result-bazi")}`;
}

/* ---------------------------------------------------------- 紫微 / Ziwei */
function renderZiwei(result) {
  const palaces = Array.isArray(result.palaces) ? result.palaces : [];
  const ordered = [...palaces].sort((a, b) => (a.index ?? 0) - (b.index ?? 0));
  const palaceName = (index) => ordered.find((p) => p.index === index)?.name || `#${index}`;

  const cells = ordered
    .map((palace) => {
      const main = (palace.main_stars || []).map((s) => `<span class="star">${escapeHtml(s)}</span>`).join("");
      const aux = (palace.auxiliary_stars || []).map((s) => `<span class="star aux">${escapeHtml(s)}</span>`).join("");
      const flags = [
        palace.is_fate_palace ? badge("命宫", "badge-fact") : "",
        palace.is_body_palace ? badge("身宫", "badge-interpret") : "",
      ].join("");
      return `<div class="palace ${palace.is_fate_palace ? "is-fate" : ""} ${palace.is_body_palace ? "is-body" : ""}">
        <div class="palace-head">
          <span class="palace-name">${escapeHtml(palace.name || "—")}</span>
          <span class="palace-pos">#${escapeHtml(palace.index)} ${escapeHtml(palace.earthly_branch || "")}${escapeHtml(palace.heavenly_stem || "")}</span>
        </div>
        <div class="star-list">${main || aux ? main + aux : `<span class="star aux">无主星</span>`}</div>
        <div class="palace-flags">${flags}</div>
      </div>`;
    })
    .join("");

  return `
    <div class="kv-grid">
      ${kv("五行局", escapeHtml(result.wuxing_ju || "—"))}
      ${kv("阴阳", escapeHtml(YIN_YANG_LABELS[result.yin_yang] || result.yin_yang || "—"))}
      ${kv("命宫", `${escapeHtml(palaceName(result.fate_palace_index))}（索引 ${escapeHtml(result.fate_palace_index)}）`)}
      ${kv("身宫", `${escapeHtml(palaceName(result.body_palace_index))}（索引 ${escapeHtml(result.body_palace_index)}）`)}
    </div>
    <p class="card-note">十二宫按后端返回的 index 0–11 顺序展示（非传统宫位排布还原）。辅星字段由后端返回；当前该接口未填充辅星时为「无主星」占位。</p>
    <div class="palace-grid">${cells || `<div class="empty-inline">后端未返回宫位数据。</div>`}</div>
    ${result.calendar_note ? `<p class="card-note">日历备注：${escapeHtml(result.calendar_note)}</p>` : ""}
    ${identityNote("fact")}
    ${jsonBlock(result, "raw-result-ziwei")}`;
}

/* --------------------------------------------------------- 六爻 / Liuyao */
const CAST_LABELS = { 6: "老阴 ×", 7: "少阳", 8: "少阴", 9: "老阳 ○" };

function yaoLine(line, { showChanging = true } = {}) {
  const yin = Boolean(line.is_yin);
  const changing = Boolean(line.is_changing);
  const mark = !showChanging ? "" : changing ? (line.cast_value === 9 ? "○" : "×") : "";
  const bars = yin
    ? `<span class="yao-bar half"></span><span class="yao-gap"></span><span class="yao-bar half"></span>`
    : `<span class="yao-bar"></span>`;
  return `<div class="yao-line ${changing && showChanging ? "is-changing" : ""}" title="第 ${escapeHtml(line.position)} 爻">
    <span class="pos">${escapeHtml(line.position)}</span>
    <span class="yao-bars">${bars}</span>
    <span class="mark">${mark}</span>
  </div>`;
}

function hexagramBox(title, num, lines, { showChanging = false } = {}) {
  const sorted = [...(lines || [])].sort((a, b) => (b.position ?? 0) - (a.position ?? 0));
  const name = hexagramName(num);
  const label = num == null ? "无（无动爻）" : `第 ${num} 卦${name ? ` · ${name}` : ""}`;
  return `<div class="hexagram-box">
    <div class="hexagram-title"><span>${escapeHtml(title)}</span></div>
    <div class="hexagram-name">${escapeHtml(name || "—")}<span class="num">${escapeHtml(label)}</span></div>
    <div class="yao-lines">${sorted.map((line) => yaoLine(line, { showChanging })).join("")}</div>
  </div>`;
}

function renderLiuyao(result) {
  const original = Array.isArray(result.original) ? result.original : [];
  const rows = [...original]
    .sort((a, b) => (b.position ?? 0) - (a.position ?? 0))
    .map((line) => {
      const pos = line.position;
      const shi = pos === result.shi_position ? badge("世", "badge-fact") : "";
      const ying = pos === result.ying_position ? badge("应", "badge-interpret") : "";
      const changing = line.is_changing ? badge(CAST_LABELS[line.cast_value] || "动", "badge-warn") : "";
      return `<div>${escapeHtml(pos)}</div>
        <div>${line.is_yin ? "阴" : "阳"} ${changing}</div>
        <div>${escapeHtml((result.najia || [])[pos - 1] || "—")}</div>
        <div>${escapeHtml((result.liu_qin || [])[pos - 1] || "—")}</div>
        <div>${escapeHtml((result.liu_shen || [])[pos - 1] || "—")}</div>
        <div class="shi">${shi}${ying}</div>`;
    })
    .join("");

  const detail = `<div class="liuyao-detail scroll-x">
    <div class="liuyao-rows">
      <div class="hdr">爻位</div><div class="hdr">阴阳 / 动</div><div class="hdr">纳甲</div>
      <div class="hdr">六亲</div><div class="hdr">六神</div><div class="hdr">世应</div>
      ${rows || `<div class="empty-inline" style="grid-column:1/-1">后端未返回爻数据。</div>`}
    </div>
  </div>`;

  return `
    <div class="kv-grid">
      ${kv("本卦", `<strong>第 ${escapeHtml(result.original_hexagram)} 卦 · ${escapeHtml(hexagramName(result.original_hexagram) || "—")}</strong>`)}
      ${kv("变卦", result.changed_hexagram == null ? "无（无动爻）" : `第 ${escapeHtml(result.changed_hexagram)} 卦 · ${escapeHtml(hexagramName(result.changed_hexagram) || "—")}`)}
      ${kv("互卦", result.mutual_hexagram == null ? "—" : `第 ${escapeHtml(result.mutual_hexagram)} 卦 · ${escapeHtml(hexagramName(result.mutual_hexagram) || "—")}`)}
      ${kv("宫位", `${escapeHtml(result.palace || "—")}（${escapeHtml(result.palace_element || "—")}）`)}
      ${kv("用神", escapeHtml(result.yong_shen || "未判定"))}
      ${kv("世 / 应", `${escapeHtml(result.shi_position)} 爻 / ${escapeHtml(result.ying_position)} 爻`)}
    </div>
    <div class="hexagrams">
      ${hexagramBox("本卦", result.original_hexagram, original, { showChanging: true })}
      ${hexagramBox("变卦", result.changed_hexagram, result.changed, { showChanging: false })}
      ${hexagramBox("互卦", result.mutual_hexagram, result.mutual, { showChanging: false })}
    </div>
    ${detail}
    <p class="card-note">起卦值：${escapeHtml(
      original.map((line) => `${line.position}:${line.cast_value}`).join(" · ") || "—",
    )}（6 老阴 / 7 少阳 / 8 少阴 / 9 老阳）。未显式提供 <code>seed</code> 时，起卦由后端按请求确定性派生的种子决定。</p>
    ${identityNote("fact")}
    ${jsonBlock(result, "raw-result-liuyao")}`;
}

/* ---------------------------------------------------------- 奇门 / Qimen */
function renderQimen(result) {
  const cells = Array.isArray(result.cells) ? result.cells : [];
  const byPalace = new Map(cells.map((cell) => [cell.palace, cell]));
  const dunLabel = result.dun_type === "yang" ? "阳遁" : result.dun_type === "yin" ? "阴遁" : result.dun_type || "—";

  const grid = QIMEN_PALACE_ORDER.map((palaceNum) => {
    const cell = byPalace.get(palaceNum);
    if (!cell) {
      return `<div class="qimen-cell"><div class="qimen-cell-head"><span class="qimen-cell-name">#${palaceNum}</span></div><div class="empty-inline">未返回</div></div>`;
    }
    const rows = [
      ["天盘", cell.sky_plate],
      ["地盘", cell.earth_plate],
      ["八神", cell.eight_gods],
      ["九星", cell.nine_stars],
      ["八门", cell.eight_doors],
      ["三奇", cell.three_qi],
    ]
      .filter(([, value]) => value !== null && value !== undefined && value !== "")
      .map(
        ([key, value]) =>
          `<div class="qimen-row"><span class="k">${escapeHtml(key)}</span><span class="v">${escapeHtml(value)}</span></div>`,
      )
      .join("");
    const flags = [
      cell.is_central ? badge("中宫", "badge-neutral") : "",
      cell.is_void ? badge("空亡", "badge-warn") : "",
    ].join("");
    return `<div class="qimen-cell ${cell.is_central ? "is-central" : ""} ${cell.is_void ? "is-void" : ""}">
      <div class="qimen-cell-head">
        <span class="qimen-cell-name">${escapeHtml(cell.name || "—")}</span>
        <span class="qimen-cell-idx">#${escapeHtml(cell.palace)}</span>
      </div>
      ${rows}
      <div class="palace-flags">${flags}</div>
    </div>`;
  }).join("");

  return `
    <div class="kv-grid">
      ${kv("节气", escapeHtml(result.solar_term || "—"))}
      ${kv("遁 / 局", `${escapeHtml(dunLabel)} · ${escapeHtml(result.ju)} 局`)}
      ${kv("日", escapeHtml(result.day_of_month))}
      ${kv("三奇偏移", escapeHtml(result.triple_offset))}
    </div>
    <p class="card-note">九宫按洛书方位排布：巽4 · 离9 · 坤2 / 震3 · 中5 · 兑7 / 艮8 · 坎1 · 乾6；宫位数据本身来自后端逐宫返回。</p>
    <div class="qimen-grid">${grid || `<div class="empty-inline">后端未返回盘面数据。</div>`}</div>
    ${identityNote("fact")}
    ${jsonBlock(result, "raw-result-qimen")}`;
}

const RENDERERS = { bazi: renderBazi, ziwei: renderZiwei, liuyao: renderLiuyao, qimen: renderQimen };

/** 单域计算卡片（AgentOutput）。 */
export function renderCalculationCard(output, index = 0) {
  const agent = output?.agent || "unknown";
  const result = output?.result;
  const renderer = RENDERERS[agent];
  const confidence = output?.confidence;
  const meta = [
    badge("确定性计算", "badge-fact"),
    output?.engine_version ? badge(`engine ${output.engine_version}`, "badge-neutral") : "",
    typeof confidence?.value === "number" ? badge(`置信度 ${fmtPercent(confidence.value)}`, "badge-neutral") : "",
  ]
    .filter(Boolean)
    .join("");

  let body;
  if (!renderer) {
    body = `<div class="empty-inline">该域（${escapeHtml(agent)}）暂无专用渲染器，原始结果见 JSON。</div>${jsonBlock(result, `raw-result-${safeToken(agent)}`)}`;
  } else if (!result || typeof result !== "object") {
    body = `<div class="empty-inline">后端未返回 <code>result</code>。</div>`;
  } else {
    try {
      body = renderer(result);
    } catch (error) {
      body = `<div class="empty-inline">结果渲染失败：${escapeHtml(error.message)}；原始 JSON 见下。</div>${jsonBlock(result, `raw-result-${safeToken(agent)}`)}`;
    }
  }

  return `<article class="card" data-testid="domain-card-${safeToken(agent)}" data-index="${index}">
    <div class="card-head">
      <h3>${escapeHtml(domainLabel(agent))} <span class="card-sub">${escapeHtml(agent)} · ${escapeHtml(output?.request_id || "")}</span></h3>
      <div class="source-strip">${meta}</div>
    </div>
    <div class="card-body">${body}</div>
  </article>`;
}

/* ------------------------------------------------------------- 知识证据 */
export function renderEvidenceCard(agent, detail, index = 0) {
  const knowledge = Array.isArray(detail?.knowledge) ? detail.knowledge : [];
  const withText = knowledge.filter((item) => typeof item.text === "string" && item.text.trim());
  const items = withText.length
    ? withText
        .map(
          (item, i) => `<div class="evidence-item">
        <div class="evidence-head">
          <span class="evidence-source">${escapeHtml(item.source || "（未提供来源）")}</span>
          <span class="evidence-id">${escapeHtml(item.id || "")}</span>
        </div>
        <div class="evidence-text clamped" data-evidence-text="${i}">${escapeHtml(item.text)}</div>
        <button type="button" class="btn btn-small evidence-toggle" data-action="toggle-evidence" data-target="${i}" data-testid="btn-evidence-toggle-${safeToken(agent)}-${i}">展开全文</button>
      </div>`,
        )
        .join("")
    : `<div class="empty-inline">本次解释链路未返回可展示的知识片段（或该域未配置检索器）。</div>`;

  const note = withText.length
    ? `<p class="card-note"><strong>如何阅读：</strong>以下片段由后端在冻结知识语料中检索后随解释返回，含来源书名 / 章节与节点 ID；它们用于给解释提供语境，<strong>不是</strong>对上方计算结论的证明。当前接口只返回 <code>id</code>、<code>source</code> 与片段原文。</p>`
    : `<p class="card-note">该域本次没有返回知识片段；页面不会用本地知识或模型记忆补齐。</p>`;

  return `<article class="card" data-testid="evidence-card-${safeToken(agent)}" data-index="${index}">
    <div class="card-head">
      <h3>${escapeHtml(domainLabel(agent))} 的知识证据 <span class="card-sub">${knowledge.length} 条</span></h3>
      <div class="source-strip">${badge("检索证据", "badge-evidence")}</div>
    </div>
    <div class="card-body">${note}<div class="evidence-list">${items}</div></div>
  </article>`;
}

/* ----------------------------------------------------------------- 解释 */
export function renderExplanationCard(agent, detail, index = 0) {
  const explanation = typeof detail?.explanation === "string" ? detail.explanation.trim() : "";
  const provider = detail?.provider ?? null;
  const degraded = detail?.degraded === true;
  const error = detail?.error || null;
  const knowledgeCount = Array.isArray(detail?.knowledge) ? detail.knowledge.length : 0;

  const meta = [
    badge("生成解释", "badge-interpret"),
    badge(provider ? `provider: ${provider}` : "离线确定性后备", "badge-neutral"),
    degraded ? badge("已降级", "badge-partial") : badge("未降级", "badge-ok"),
    knowledgeCount ? badge(`引用 ${knowledgeCount} 条知识`, "badge-evidence") : "",
  ]
    .filter(Boolean)
    .join("");

  const errorBlock = error
    ? `<div class="provider-error"><strong>解释服务错误（不影响计算结果）：</strong>
        kind=<code>${escapeHtml(error.kind || "unknown")}</code>
        ${error.type ? ` · type=<code>${escapeHtml(error.type)}</code>` : ""}
        ${error.provider ? ` · provider=<code>${escapeHtml(error.provider)}</code>` : ""}
        <div>${escapeHtml(error.message || "")}</div>
      </div>`
    : "";

  const body = explanation
    ? `<div class="explain-body" data-testid="explanation-text-${safeToken(agent)}">${escapeHtml(explanation)}</div>`
    : `<div class="empty-inline">后端本次未返回解释文本。</div>`;

  const degradedNote = degraded
    ? `<p class="card-note">当前为<strong>降级模式</strong>：未配置 LLM provider（或 provider 调用失败），解释由确定性模板/结果摘要生成，不含任何模型推断。</p>`
    : `<p class="card-note">解释由已配置的 LLM provider 基于 FACTS + 检索知识生成；FACTS 仍以后端计算结果为准。</p>`;

  return `<article class="card" data-testid="explanation-card-${safeToken(agent)}" data-index="${index}">
    <div class="card-head">
      <h3>${escapeHtml(domainLabel(agent))} 的解释 <span class="card-sub">${escapeHtml(agent)}</span></h3>
      <div class="source-strip">${meta}</div>
    </div>
    <div class="card-body">
      ${body}
      ${degradedNote}
      ${errorBlock}
      <div class="explain-meta">
        <span>解释来源：<code>explanation_detail["${escapeHtml(agent)}"]</code></span>
        <span>与「${escapeHtml(domainLabel(agent))}」的计算结果一一对应</span>
      </div>
    </div>
  </article>`;
}

export function renderEmptyPanel(message) {
  return `<div class="empty-inline">${escapeHtml(message)}</div>`;
}

export { fmtNum };
