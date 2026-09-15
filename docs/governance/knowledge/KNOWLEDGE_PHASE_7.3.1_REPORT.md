# Knowledge Phase 7.3.1 — Tier 1 Source Acquisition & Verbatim Evidence Verification Report

> **Sprint**: Phase 7.3.1 —— Tier 1 来源获取与逐字证据核验（执行 Phase 7.3 §9「下一步」1~4）
> **日期**: 2026-09-15
> **分支**: `work/knowledge/phase7.3.1-source-acquisition`（基于 main `1881e64`，独立 worktree）
> **上游**: Phase 7.3（Source Discovery PASS / Verbatim Acquisition BLOCKED / Production 0）
> **结果**: **Acquisition PASS（4/4 Tier 1 来源）· Verbatim Verification PASS（36/36 义理断言 +
> 10/10 转录差异核验）· Evidence Readiness ACHIEVED（限范围）· Knowledge Production 0**

---

## 1. Executive Summary

Phase 7.3 的阻塞点是**环境性**的（webfetch 工具 4 次 timeout / transport error），而非来源不存在。
本 Sprint 以可用的 HTTPS 通道（本会话实测可达）重新执行 7.3 §9 列出的四项下一步，结果：

```text
Source Acquisition (4/4 Tier 1)        PASS      （revision-pinned，sha256 全部登记）
Verbatim Evidence Verification         PASS      （36/36 义理断言 + 10/10 差异核验）
Evidence Readiness                     ACHIEVED  （限 7.2B 候选集范围）
Transcription Variance Registration    DONE      （V-1~V-5，机器核验）
Knowledge Production                   0         （未获 7.2B 重跑授权，且本轮不属生产 Sprint）
Corpus                                 63 / 37 / 10（数量与语义**零变化**）
```

**关键结论**: GAP-12 / GAP-13 的阻塞条件（「Tier 1 原文不可达 / 逐字核验未达成」）
**已由证据消除**——四份 Tier 1 来源均已成为 revision-pinned、逐字可回溯的证据源：

| 来源 | 7.3 状态 | 7.3.1 状态 |
|------|----------|------------|
| 紫微斗數全書（source_ziwei_01） | ❌ FETCH_BLOCKED / NOT READY | ✅ ACQUIRED / **VERBATIM_VERIFIED**（卷一·諸星問答論 13 段） |
| 三命通會（source_sanming_01） | ❌ FETCH_BLOCKED / NOT READY | ✅ ACQUIRED / **VERBATIM_VERIFIED**（卷三·论羊刃/驿马/天乙贵人/劫煞亡神/十干禄 + 卷二·将星华盖/咸池 + 卷六·论阳刃） |
| 淵海子平（source_bazi_01） | ❌ FETCH_BLOCKED / NOT READY | ✅ ACQUIRED / **VERBATIM_VERIFIED**（论阳刃 / 论劫财） |
| 紫微斗數全集（source_ziwei_02 / GAP-01） | ❌ NOT_ATTEMPTED | ⏸ 未变更（GitHub 候选源需版本核验，仍 🟡 SOURCE_DISCOVERED） |

**本 Sprint 不做的事**（硬边界，见 §6）：不生产任何节点/关系/引用；不修改任何冻结契约、
Golden Vector、Reference Runtime；不执行 7.2B 重跑；不合并 main；不启用 ACP。

> **证据就绪 ≠ 生产授权。** 生产（7.2B 重跑）需要人工在 §9 决策点 D-1 上显式授权；
> auxiliary_star 的生产另需 D-2（契约示例层）裁定。

---

## 2. Task 0 — 方法与口径

| 项 | 内容 |
|----|------|
| 通道 | HTTPS（本会话环境实测可达 wikisource；Phase 7.2B/7.3 会话的 webfetch 阻塞不重现） |
| 页面修订 | `action=query&prop=revisions` 取 pageid / revid / rev 时间戳（**revision-pinned**） |
| 原文获取 | `action=raw`（MediaWiki 原始 wikitext），一次 GET，无解析、无改写 |
| 完整性 | 每份抓取件登记 字节数 + sha256（原始字节）；本册摘要前 16 位，全量登记于 SOURCE_STATUS |
| 逐字核验 | 抓取件全文去空白后做**子串逐字匹配**（断言串取自原文，非人工转写）；任一 FAIL 即该条不成立 |
| 差异登记 | 机器核验的转录字形讹误（V-1~V-5），含**对照项**证明差异局部性 |
| 抽取 | 引文按行区间机器抽取，逐行原样（含原文换行/缩进），无字符改动 |
| 采集边界 | **不将原文批量入库**（Admission Policy §2「禁止网络爬虫自动采集入库」；仓库惯例「古籍原文不在仓库内」）；本 Sprint 只产出**元数据登记 + 逐字摘录**（见 L-1） |
| 网络依赖 | 仅本轮证据获取使用网络；pipeline / validate / tests 仍**完全离线确定性**（未引入任何运行时依赖） |

抓取时间（UTC）: **2026-09-15T16:14:37Z**。

---

## 3. 获取清单（Acquisition Manifest）

### 3.1 Tier 1 主来源（本 Sprint 核心）

| 来源 | 页面 | pageid | revid | rev 时间 | 字节 | sha256（抓取件） |
|------|------|--------|-------|----------|------|------------------|
| source_ziwei_01 | 紫微斗數全書/卷一 | 342316 | **7913704** | 2026-08-07T05:47:26Z | 67698 | `9beb8038a8b82154d15d81c8ff822423d4f0c7c006f536a86552adeaa594818a` |
| source_ziwei_01 | 紫微斗數全書/卷二 | 342317 | 1963110 | 2020-09-04T14:06:27Z | 106736 | `1e255c6ae99e6f89ae124ab342554ef1347fc8e68fb8908cba7290d1a38cbb72` |
| source_ziwei_01 | 紫微斗數全書/卷三 | 342318 | 2268626 | 2023-03-15T10:18:42Z | 36720 | `ed327a68253a89a6e8b2962932a16f75546826ffcdd2e9e4ac419ad0f389b03b` |
| source_sanming_01 | 三命通會/卷二 | 335930 | 2292392 | 2023-05-28T01:06:07Z | 66693 | `e58c3f48d5f983548a35783c8f4961768a5c71edfa6d88f8fb37bc07acd53e0d` |
| source_sanming_01 | 三命通會/卷三 | 335931 | **2184219** | 2022-10-03T21:50:57Z | 65356 | `2de8fc1bf46eb4ecc5436b6cece6d4a06e56330565f3aa6e4cfaa581f5b0488e` |
| source_sanming_01 | 三命通會/卷六 | 335941 | **845352** | 2017-03-25T11:48:24Z | 104590 | `0953159907f689e5a77df81a9a6eb2b86d1c934bcbd8bac4fe1ecfa0e1a14919` |
| source_bazi_01 | 淵海子平 | 343323 | **2593607** | 2025-08-24T18:41:12Z | 173237 | `a4447be5d95eb073857cb8cba8f0e58a500de1c283016c76cfdedb0d1b2bb133` |

### 3.2 同批抓取的其他卷次（为后续 shen_sha 扩展备料，本轮不抽取）

| 页面 | pageid | revid | 字节 | sha256（前 16 位） |
|------|--------|-------|------|--------------------|
| 三命通會（索引页） | 59146 | 1390993 | 1466 | `9c5f7f3cd46a8c57…` |
| 三命通會/卷一 | 110804 | 2271026 | 78525 | `3a83d9d38cccf678…` |
| 三命通會/卷四 | 335939 | 2119828 | 42699 | `dfcd0f49fa83eccc…` |
| 三命通會/卷五 | 335940 | 2706483 | 30616 | `df0446bc9ff7651a…` |
| 三命通會/卷七 | 335942 | 2334571 | 41443 | `1affcdc3efb47bb8…` |
| 三命通會/卷八 | 335943 | 845354 | 84730 | `78840e6664177dfd…` |
| 三命通會/卷九 | 335944 | 2613372 | 85432 | `6782b70766243cad…` |
| 紫微斗數全書（索引页） | 254079 | 850736 | 3091 | `d9ad732fc3e86c21…` |

---

## 4. 逐字核验结果

### 4.1 auxiliary_star（《紫微斗數全書》卷一 · 諸星問答論）

11 个 7.2B 候选辅星**全部**在该卷找到**逐字定义段**（另有 天馬 / 羊陀总论 / 羊陀火鈴四星总论）：

| 候选 | 定位 | 逐字定义（首句，原文形状） |
|------|------|----------------------------|
| 文昌 | 卷一 354–361 | 「答曰：文昌主科甲，守身命主人幽閑儒雅…」（繁体） |
| 文曲 | 卷一 363–367 | 「答曰：文曲属水，北斗第四星也，主科甲文车之宿。」（简体） |
| 左輔 | 卷一 379–381 | 「希夷先生答曰：左辅帝极主宰之星，守身命诸宫降福。」 |
| 右弼 | 卷一 383–392 | 「希夷先生答曰：右弼帝极主宰之星，守身命文墨精通。」 |
| 天魁 · 天鉞 | 卷一 394–401 | 「希夷先生答曰：魁钺斗中司科之星…」（另有「天乙贵人众所钦」歌诀） |
| 祿存 | 卷一 403–415 | 「希夷先生答曰：禄存北斗第三星，真人之宿，主人贵爵，掌人寿基。」 |
| 天馬 | 卷一 417–419 | 「诸宫各有制化，如身命临之谓之驿马。」（含禄马交驰/折鞭马等名目） |
| 擎羊 | 卷一 438–440 | 「希夷先生答曰：擎羊北斗之助星。守身命性粗行暴…」 |
| 陀羅 | 卷一 442–444 | 「希夷先生答曰：陀罗北斗之助星。」 |
| 火星 | 卷一 458–468 | 「答曰：火星乃南斗浮星也。」＋希夷先生歌 |
| 鈴星 | 卷一 470–481 | 「答曰：铃星乃南斗助星也。」＋希夷先生歌 |
| （附）羊陀 / 羊陀火鈴总论 | 卷一 446–456 / 483–489 | 玉蟾先生总论两段 |

### 4.2 shen_sha（《三命通會》/《淵海子平》）

| 候选族 | 定位 | 逐字依据要点 |
|--------|------|--------------|
| 祿（祿神 / 十干祿） | 三命通會/卷三·论十干禄 | 「禄，爵禄也，当得势而享，乃谓之禄」＋十干禄起例「甲禄寅，乙禄卯，庚禄申，辛禄酉，壬禄亥，癸禄子」 |
| 驛馬 | 三命通會/卷三·论驿马 | 立法（三合数）＋四局马位「寅午戌生人，马在申」「申子辰人，马在寅」「巳酉丑人，马在亥」「亥卯未人，马在巳」＋十二马名目 |
| 天乙貴人 | 三命通會/卷三·论天乙贵人 | 义理（「其神最尊贵，所至之处，一切凶煞隐然而避」）＋取象散文「所以牛羊为贵」「所以鼠猴为贵」「故以马虎为贵」（**韵文体口诀未见** → L-3） |
| 劫煞 · 亡神 | 三命通會/卷三·论劫煞亡神 | 定义「劫在五行绝处，亡在五行临官，俱属寅申巳亥」＋四局配对（申子辰以巳为劫煞/以亥为亡神 等 8 条）＋古歌 |
| 羊刃 / 陽刃 | 三命通會/卷三·论羊刃 ＋ 卷六·论阳刃 ＋ 淵海子平·论阳刃 | 「故羊刃常居禄前一辰」；卷六「即禄前一位，言旺越其分」＋「阳刃有三，有劫财刃…」；淵海子平「以禄前一位是也；如甲禄在寅，卯为阳刃」 |
| 將星 · 華蓋 | 三命通會/卷二·论将星华盖 | 「故以三合中位谓之将星」「故以三合底处得库谓之华盖」＋「凡人命得华盖，多主孤寡」 |
| 咸池（桃花煞） | 三命通會/卷二·论咸池 | 「五行沐浴之地，名咸池」＋四局「寅午戌卯、已酉丑午、申子辰酉、亥卯未子」 |
| 孤辰寡宿 | 三命通會/卷三·论孤辰寡宿 | 「进前一辰见寅为孤，退后一辰见戌为寡」 |
| （纲）总论诸神煞 | 三命通會/卷三·总论诸神煞 | 「神煞，古有百二十名…除羊刃、空亡、劫煞、灾煞、大煞、元辰、勾绞、咸池…已备论于前矣」 |
| 劫財（逆刃） | 淵海子平·论劫财 | 「亦名『逆刃』，如乙见甲为劫财」＋五阳/五阴劫财败财之别 |

### 4.3 核验回执

- **义理断言: 36 / 36 PASS**（逐字子串匹配；断言串取自原文）
- **转录差异核验: 10 / 10 PASS**（V-1~V-5，含对照项）

全部引文与回执表见 **`KNOWLEDGE_PHASE_7.3.1_EVIDENCE_DOSSIER.md`**（575 行，机器生成）。

### 4.4 转录差异（已登记，非义理分歧）

| 编号 | 现象 | 处置 |
|------|------|------|
| V-1 | 卷三「乙丁**巳**辛癸五阴干无刃」（对照：卷六/淵海子平均作「乙丁**己**辛癸」） | 字形以卷六/淵海子平为准；本册保留原样 |
| V-2 | 卷三「丙禄**已**，丁禄午，戊寄**已**，**已**寄午」 | 同上（巳/己 混录） |
| V-3 | 卷二·咸池「**已**酉丑午」（对照：卷三·驿马同格式作「**巳**酉丑人」） | 同上，差异为局部 |
| V-4 | 卷三「**六幸**阴金」（对照：口诀「六辛逢马虎」） | 同上 |
| V-5 | 卷一「諸星問答論」繁简混排（「問紫微所主若何」与「问文曲星所主若何」并存） | 引文原样；生产时 interpretation 用仓库统一字形，passage 回指原文 |

---

## 5. Evidence Readiness 判定（限范围）

| 来源 | 7.3 | 7.3.1 | 范围 |
|------|-----|-------|------|
| source_ziwei_01 紫微斗數全書 | NOT READY | **VERBATIM_VERIFIED** | 卷一·諸星問答論（辅星 11 条 + 天馬 + 两组总论）；卷二/卷三已获取未抽取 |
| source_sanming_01 三命通會 | NOT READY | **VERBATIM_VERIFIED** | 卷三（羊刃/驿马/天乙贵人/劫煞亡神/十干禄/孤辰寡宿/总论诸神煞）+ 卷二（将星华盖/咸池）+ 卷六（阳刃） |
| source_bazi_01 淵海子平 | NOT READY | **VERBATIM_VERIFIED** | 论阳刃 / 论劫财（跨源对照项） |
| source_ziwei_02 紫微斗數全集 | NOT_ATTEMPTED | NOT_ATTEMPTED（未变） | GAP-01 保持 🟡 SOURCE_DISCOVERED |

**该判定的边界**（防止状态夸大）：

1. 仅覆盖 **7.2B 候选集**（shen_sha / auxiliary_star 首批）；未覆盖卷三其余神煞（L-5）。
2. 「逐字核验」= 与 wikisource **指定修订版**逐字一致；非刻本影印校勘（L-2），沿用 7.1.5 GAP-10 的既有口径。
3. 抓取件**未入库**（L-1）：可回溯性由 revid + sha256 + 逐字摘录保证。
4. **不隐含**任何生产授权、Schema 变更或契约变更。

---

## 6. 硬边界与零触碰验证

| 检查 | 命令 | 结果 |
|------|------|------|
| 无新增/修改知识条目 | `git diff --stat -- knowledge/corpus/` | ✅ 空 |
| 无语义断言变化 | `git diff -- knowledge/ziwei_corpus.json` | ✅ 仅 `metadata.source_digests`（登记值随来源元数据同步，同 7.3 口径） |
| 未触碰 Schema / 契约 | `git diff -- reference/ docs/specification/` | ✅ 空 |
| 未触碰域实现 | `git diff -- src/ reference/qimen/ reference/bazi/ reference/ziwei/` | ✅ 空 |
| 未新增 ACP | `docs/governance/ACP/` | ✅ 空（无新增文件） |
| 未合并 / 未推送 main | `git log main..HEAD` | ✅ 仅本分支提交 |
| 生产数量 | corpus counts | ✅ **63 / 37 / 10 不变** |
| 运行时依赖 | `knowledge/pipeline.py` | ✅ 仍为离线确定性（网络仅用于本轮抓取，不在 pipeline 内） |

---

## 7. Pipeline 与回归

```text
python knowledge/pipeline.py
  corpus written: knowledge/ziwei_corpus.json (63 nodes, 37 relations, 10 references)
  sha256: b4af74abfb7c4a9fe3d4986ab87823247a4f18037a0530569fae68b32890089c

python knowledge/validate.py
  VALIDATION PASSED: all corpus entries conform to KB-001~020

pytest -q
  599 passed（exit 0；599 结果点, 0 failed / 0 error；含 reference/tests 独立套件）
```

- **确定性**: pipeline 双重运行输出逐字节一致（KB-020）。
- **数量**: 63 节点 / 37 关系 / 10 引用 —— 与 7.1.6/7.2B/7.3 完全一致（零生产）。
- **corpus sha256 变化**: 仅因 `source_01.yaml / source_02.yaml / source_03.yaml` 的来源登记
  字段更新（registry metadata），**无任何语义内容变化**——与 7.3 Evidence Review 的
  `METADATA_ONLY` 判定同类（见 §6 表）。

### 7.1 测试结果（实测）

| 项 | 结果 |
|----|------|
| 收集/执行 | **599** |
| 通过 | **599**（exit code 0） |
| 失败 / 错误 | **0 / 0** |
| 既有沙箱限制 | 不再出现（本会话文件策略为完全访问，此前 4 个「子进程管道」测试的 WinError 5 未复现） |

> 与权威全绿口径 599/599 一致；本轮未新增/修改任何测试文件。

---

## 8. GAP 更新

| GAP | 变化 | 新状态 |
|-----|------|--------|
| GAP-12（auxiliary_star Tier 1 主源不可达） | 紫微斗數全書卷一已获取并逐字核验（辅星 11 条） | 🟢 **EVIDENCE_VERIFIED**（阻塞条件消除）；**生产待 7.2B 重跑授权 + 契约示例层裁定** |
| GAP-13（shen_sha Tier 1 逐字核验未达成） | 三命通會/淵海子平神煞章节已获取并逐字核验（36/36 断言） | 🟢 **EVIDENCE_VERIFIED**（阻塞条件消除）；**生产待 7.2B 重跑授权** |
| GAP-05（神煞/辅星无单一权威来源） | 来源策略（7.2B）+ 证据（7.3.1）均就绪；流派差异（如羊刃阴阳干、天乙贵人起例表述）仍需 SchoolView 显式保留 | 🟡 来源与证据部分 RESOLVED；**SchoolView 归属待生产时落地** |
| GAP-01（紫微斗數全集不可获取） | 未触及（GitHub 候选源需版本核验，D-5） | 🟡 SOURCE_DISCOVERED（未变） |
| GAP-02/03/06/07/08 | 未触及 | 记录（未变） |
| GAP-09 / GAP-10 | 未触及（历史已闭合项） | CLOSED（未变） |

> 状态词纪律：GAP-01 未出现 CLOSED / EVIDENCE_READY 等升级词；GAP-12/13 的升级限定为
> **证据层**（EVIDENCE_VERIFIED），未标注为「已解决」或「已生产」。

---

## 9. 人工决策点（本 Sprint 停在门口）

| 编号 | 决策点 | 选项 | 说明 |
|------|--------|------|------|
| **D-1** | **7.2B 重跑（生产）是否授权** | 授权 / 不授权 / 限定范围 | 7.2B 的生产授权此前已获，但其重跑在 7.2B §14 被列为「待人工决策」；本轮只消除了来源阻塞。授权后即可按本册证据生产 shen_sha 节点 |
| **D-2** | auxiliary_star 生产是否需先走 **契约示例层 ACP** | 先 ACP / 不需要 / 一并授权 | 7.2B §12 记：冻结契约 `knowledge_contract.json` 的示例层若需补 auxiliary_star，须走 ACP（不得直接修改） |
| **D-3** | Tier 1 抓取件（原文快照）是否入库 | 不入仓（维持现状）/ 入仓 evidence archive / 折中（仅入关键段） | 现行惯例为「古籍原文不在仓库内」；入库将改变仓库体积与证据持久性策略 |
| **D-4** | 天乙贵人**韵文体口诀**缺位如何处置（L-3） | 由散文推导并标注 / 另选来源 / 该节点暂不生产 | 影响 shen_sha「天乙贵人」节点的起例表内容 |
| **D-5** | GAP-01《紫微斗數全集》是否推进 | 推进版本核验 / 暂缓 | GitHub 候选源为 MIT 现代整理本，需治理裁定后方可作为 Tier 1 |
| **D-6** | 本分支处置 | 合并 / 保留 / 关闭 | 分支 `work/knowledge/phase7.3.1-source-acquisition`（合并由用户执行或授权执行） |

---

## 10. 产出物清单

| 文件 | 说明 | 状态 |
|------|------|------|
| `docs/governance/knowledge/KNOWLEDGE_PHASE_7.3.1_EVIDENCE_DOSSIER.md` | 逐字证据册（575 行，机器生成：引文 + 36 条断言回执 + 10 条差异核验 + 限制） | 新增 |
| `docs/governance/knowledge/KNOWLEDGE_PHASE_7.3.1_REPORT.md` | 本 Sprint 报告 | 新增 |
| `knowledge/sources/ziwei/SOURCE_STATUS.md` | 来源状态登记（ACQUIRED / VERBATIM_VERIFIED + 抓取清单） | 更新 |
| `knowledge/sources/ziwei/source_01.yaml` | 紫微斗數全書：url/revid/digest/证据状态 | 更新 |
| `knowledge/sources/ziwei/source_02.yaml` | 淵海子平：revid/digest/证据状态 | 更新 |
| `knowledge/sources/ziwei/source_03.yaml` | 三命通會：revid/digest/证据状态 | 更新 |
| `docs/governance/knowledge/ZIWEI_CORPUS_GAPS.md` | GAP-12/13 → EVIDENCE_VERIFIED；GAP-05 更新；GAP-01 未变 | 更新 |
| `docs/governance/CAPABILITY_STATUS.md` | Knowledge Layer 条目指针（Phase 7.3.1 证据就绪） | 更新 |
| `docs/PROJECT_STATUS.md` | 当前 Sprint / 历史 Sprint / Next Sprint 指针（来源阻塞解除） | 更新 |
| `knowledge/ziwei_corpus.json` | 仅 `metadata.source_digests` 同步（零语义变化） | 更新 |
| `context/归档.md` | 本轮对话归档 | 更新 |

---

## 附录 A — 未主张事项（anti-overclaim）

- ❌ 未主张 GAP-12/13 **已解决**（仅主张**证据层就绪**，生产未发生）
- ❌ 未主张 evidence readiness 覆盖全部神煞/辅星体系（仅 7.2B 候选集）
- ❌ 未主张「来源权威性已确认」之外的版本学结论（转录本口径，L-2）
- ❌ 未主张任何生产/契约/向量层面的进展
- ❌ 未修改任何冻结工件

## 附录 B — 复现命令

```bash
# 1) 取修订信息（pageid / revid / 时间戳）
curl -sS "https://zh.wikisource.org/w/api.php?action=query&format=json&formatversion=2\
&prop=revisions&rvprop=ids|timestamp&titles=紫微斗數全書/卷一|三命通會/卷三|淵海子平"

# 2) 取原文（原始 wikitext），并计算 sha256
curl -sS -A 'OpenMetaphysics-evidence-verify/1.0' \
  "https://zh.wikisource.org/w/index.php?title=%E7%B4%AB%E5%BE%AE%E6%96%97%E6%95%B8%E5%85%A8%E6%9B%B8/%E5%8D%B7%E4%B8%80&action=raw" \
  -o ziwei_juan1.wiki
python -c "import hashlib,sys;print(hashlib.sha256(open('ziwei_juan1.wiki','rb').read()).hexdigest())"
# 期望: 9beb8038a8b82154d15d81c8ff822423d4f0c7c006f536a86552adeaa594818a

# 3) 逐字断言核验（去空白子串匹配，示例）
python - <<'PY'
import re
t = re.sub(r"\s+", "", open("ziwei_juan1.wiki", encoding="utf-8").read())
print("祿存北斗第三星，真人之宿，主人贵爵，掌人寿基" in t)   # True
PY
```

## 附录 C — 与 7.3 的口径差异说明

Phase 7.3 记录的四次 webfetch 失败（timeout / transport error）属**工具/环境**问题。
本 Sprint 以 HTTPS 直取（curl / MediaWiki API）在同一网络环境下成功，且**逐字核验通过**，
故：

- 7.3 的「FETCH_BLOCKED **不隐含**不可获取」判断被实测证实（该原则成立）；
- GAP-12/13 的「来源已登记但未 ingest」缺口，其**证据侧**在本轮闭合。

---

*本报告止于证据层；生产、契约与向量层面的任何推进均待 §9 决策点人工裁定。*
