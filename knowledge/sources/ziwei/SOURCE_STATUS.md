# Ziwei Source Status

> Phase 7.3 — Source Acquisition & Evidence Availability Sprint（2026-08-25，历史记录）
> **Phase 7.3.1 — Tier 1 Source Acquisition & Verbatim Evidence Verification（2026-09-15，当前）**
> 状态: 来源已获取（revision-pinned）+ 逐字证据核验通过；**不代表生产授权**

---

## 来源状态总览（Phase 7.3.1 刷新）

| Source | Discovery | Metadata | Access | Evidence Readiness | GAP |
|--------|-----------|----------|--------|-------------------|-----|
| 紫微斗数全书 | ✅ DISCOVERED | ✅ REGISTERED | ✅ **ACQUIRED**（卷一卷二卷三, revid 7913704/1963110/2268626） | ✅ **VERBATIM_VERIFIED**（卷一·諸星問答論，限 7.2B 候选集） | GAP-12 → 🟢 EVIDENCE_VERIFIED |
| 紫微斗数全集 | ✅ DISCOVERED（GitHub 候选） | ✅ PARTIAL | ⏸ NOT_ATTEMPTED | ❌ NOT READY | GAP-01 🟡 SOURCE_DISCOVERED（未变） |
| 三命通会 | ✅ DISCOVERED | ✅ REGISTERED | ✅ **ACQUIRED**（卷一~卷九, 含卷三 revid 2184219 / 卷二 2292392 / 卷六 845352） | ✅ **VERBATIM_VERIFIED**（羊刃/驿马/天乙贵人/劫煞亡神/十干禄/孤辰寡宿/将星华盖/咸池/阳刃） | GAP-13 → 🟢 EVIDENCE_VERIFIED |
| 渊海子平 | ✅ DISCOVERED | ✅ REGISTERED | ✅ **ACQUIRED**（revid 2593607） | ✅ **VERBATIM_VERIFIED**（论阳刃/论劫财，跨源对照） | GAP-13 → 🟢 EVIDENCE_VERIFIED |

**关键原则（不变）**: FETCH_BLOCKED 不隐含"不可获取"——仅表示当时环境/方法无法获取。
NOT READY 是独立状态, 不因 Discovery 而自动升级。
**新增原则**: VERBATIM_VERIFIED 是**证据层**状态, 不隐含生产授权、不隐含契约/Schema 变更。

---

## Phase 7.3.1 获取清单（revision-pinned）

抓取时间（UTC）: **2026-09-15T16:14:37Z**；方式: HTTPS `action=raw` + API `prop=revisions`。
抓取件保存在仓库之外（见报告 L-1）；下表 sha256 为**抓取件原始字节**摘要。

### Tier 1 主来源（本轮核验依据）

| 页面 | pageid | revid | rev 时间 | 字节 | sha256 |
|------|--------|-------|----------|------|--------|
| 紫微斗數全書/卷一 | 342316 | 7913704 | 2026-08-07T05:47:26Z | 67698 | `9beb8038a8b82154d15d81c8ff822423d4f0c7c006f536a86552adeaa594818a` |
| 紫微斗數全書/卷二 | 342317 | 1963110 | 2020-09-04T14:06:27Z | 106736 | `1e255c6ae99e6f89ae124ab342554ef1347fc8e68fb8908cba7290d1a38cbb72` |
| 紫微斗數全書/卷三 | 342318 | 2268626 | 2023-03-15T10:18:42Z | 36720 | `ed327a68253a89a6e8b2962932a16f75546826ffcdd2e9e4ac419ad0f389b03b` |
| 三命通會/卷二 | 335930 | 2292392 | 2023-05-28T01:06:07Z | 66693 | `e58c3f48d5f983548a35783c8f4961768a5c71edfa6d88f8fb37bc07acd53e0d` |
| 三命通會/卷三 | 335931 | 2184219 | 2022-10-03T21:50:57Z | 65356 | `2de8fc1bf46eb4ecc5436b6cece6d4a06e56330565f3aa6e4cfaa581f5b0488e` |
| 三命通會/卷六 | 335941 | 845352 | 2017-03-25T11:48:24Z | 104590 | `0953159907f689e5a77df81a9a6eb2b86d1c934bcbd8bac4fe1ecfa0e1a14919` |
| 淵海子平 | 343323 | 2593607 | 2025-08-24T18:41:12Z | 173237 | `a4447be5d95eb073857cb8cba8f0e58a500de1c283016c76cfdedb0d1b2bb133` |

### 同批备料（本轮不抽取）

| 页面 | pageid | revid | 字节 | sha256（前 16 位） |
|------|--------|-------|------|--------------------|
| 三命通會（索引） | 59146 | 1390993 | 1466 | `9c5f7f3cd46a8c57…` |
| 三命通會/卷一 | 110804 | 2271026 | 78525 | `3a83d9d38cccf678…` |
| 三命通會/卷四 | 335939 | 2119828 | 42699 | `dfcd0f49fa83eccc…` |
| 三命通會/卷五 | 335940 | 2706483 | 30616 | `df0446bc9ff7651a…` |
| 三命通會/卷七 | 335942 | 2334571 | 41443 | `1affcdc3efb47bb8…` |
| 三命通會/卷八 | 335943 | 845354 | 84730 | `78840e6664177dfd…` |
| 三命通會/卷九 | 335944 | 2613372 | 85432 | `6782b70766243cad…` |
| 紫微斗數全書（索引） | 254079 | 850736 | 3091 | `d9ad732fc3e86c21…` |

逐字引文与核验回执: `docs/governance/knowledge/KNOWLEDGE_PHASE_7.3.1_EVIDENCE_DOSSIER.md`

---

## 来源详情（Phase 7.3.1 状态）

### 紫微斗数全书 (GAP-12)

| 维度 | 状态 | 说明 |
|------|------|------|
| Discovery | ✅ DISCOVERED | wikisource 存在，公有领域（清朝，作者逝世 >100 年，`{{PD-old}}`） |
| URL | `https://zh.wikisource.org/wiki/紫微斗數全書` | 子页: /卷一 /卷二 /卷三 /全覽 |
| 结构 | 卷一（羅序/太微賦/形性賦/星垣論/斗數準繩/斗數發微論/重補斗數彀率/增補太微賦/**諸星問答論**/斗数骨髓赋/女命骨髓赋…）/ 卷二 / 卷三 | 諸星問答論为星曜定义权威段落 |
| Access | ✅ **ACQUIRED** | 卷一卷二卷三均获取；本轮核验依据 = 卷一 revid 7913704 |
| Evidence Readiness | ✅ **VERBATIM_VERIFIED**（卷一·諸星問答論） | 文昌/文曲/左辅/右弼/天魁天钺/禄存/天马/擎羊/陀罗/火星/铃星 + 羊陀总论/羊陀火铃总论；断言全 PASS |
| 转录状态 | 繁简混排（V-5） | 前段繁体，自「问文曲星」起转简体；引文按原样登记 |
| 备选来源 | GitHub `Renhuai123/ziwei-doushu`（MIT）含 `quanshu.ts` | 需版本核验治理裁定（D-5），本轮未使用 |
| 未覆盖 | 卷二/卷三已获取未抽取（属后续扩展） | — |

### 紫微斗数全集 (GAP-01)

| 维度 | 状态 | 说明 |
|------|------|------|
| Discovery | ✅ DISCOVERED | GitHub 仓库 `Renhuai123/ziwei-doushu` 含 `quanji.ts` |
| Access | ⏸ NOT_ATTEMPTED | 本轮未尝试（GAP-01 未被 7.3.1 纳入） |
| Evidence Readiness | ❌ NOT READY | 版本核验/对应关系确认未完成 |
| 治理要求 | 需额外裁定 | 现代整理本（MIT）能否作为 Tier 1 原始来源需人工裁定（D-5） |

### 三命通会 (GAP-13)

| 维度 | 状态 | 说明 |
|------|------|------|
| Discovery | ✅ DISCOVERED | wikisource 卷一~卷九（页面明记「缺卷十至卷十二」；公有领域） |
| Access | ✅ **ACQUIRED** | 卷一~卷九全部获取（本轮核验依据: 卷三 revid 2184219 / 卷二 2292392 / 卷六 845352） |
| Evidence Readiness | ✅ **VERBATIM_VERIFIED** | 卷三: 论十干禄 / 论驿马 / 论天乙贵人 / 论劫煞亡神 / 论羊刃 / 论孤辰寡宿 / 总论诸神煞；卷二: 论将星华盖 / 论咸池；卷六: 论阳刃 |
| 转录状态 | 简体（存在「巳/己/已」「辛/幸」字形混录，V-1~V-4） | 差异局部、已登记并机器核验 |
| 未覆盖 | 卷三其余神煞（空亡/元辰/勾绞/灾煞/六厄/天罗地网/十恶大败） | 不在 7.2B 候选集内（L-5） |
| 备选 URL | `三命通會(四庫全書本)/全覽` / ctext.org | 本轮未使用 |

### 渊海子平 (GAP-13)

| 维度 | 状态 | 说明 |
|------|------|------|
| Discovery | ✅ DISCOVERED | wikisource 单页全文（公有领域；转录含 `{{No source}}` / `{{傳統漢字化}}` 模板，需注意） |
| Access | ✅ **ACQUIRED** | revid 2593607（2025-08-24T18:41:12Z），173237 字节 |
| Evidence Readiness | ✅ **VERBATIM_VERIFIED**（限所用章节） | 论阳刃（「以禄前一位是也；如甲禄在寅，卯为阳刃」）/ 论劫财（「亦名『逆刃』」）；作跨源对照项 |
| 未覆盖 | 其余章节（十神/格局等） | 本轮不抽取 |

---

## 环境限制说明（Phase 7.3 记录，已解除）

- **Phase 7.3**: webfetch 工具 4 次 timeout / transport error → 判定为**环境性阻塞**。
- **Phase 7.3.1**: 以 HTTPS 直取（curl / MediaWiki API）在同一网络环境成功获取全部目标页面，
  且逐字核验通过 → 该阻塞**解除**；7.3「FETCH_BLOCKED 不隐含不可获取」的原则得到实测支持。

---

## 下一步（需人工授权）

1. ~~**D-1**: 7.2B 重跑授权~~ → **已执行（Phase 7.2B-R, 2026-09-15）**: 生产 23 节点 + 12 引用
2. ~~**D-2**: auxiliary_star 契约示例层是否先走 ACP~~ → **已裁定: 无需 ACP**（golden_examples 为 query 级; node_types 已含两类型）
3. **D-3**: Tier 1 抓取件（原文快照）是否入库
4. **D-4**: 天乙贵人韵文体口诀缺位的处置
5. **D-5**: GAP-01《紫微斗数全集》是否推进版本核验
