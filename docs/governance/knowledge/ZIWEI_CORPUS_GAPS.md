# Ziwei Corpus Open Gaps（已知缺口登记）

> **Sprint**: Phase 7.1.0 — Corpus Scope & Source Freeze
> **日期**: 2026-08-13
> **状态**: 记录（GAP 不修改当前规范; 仅作为未来治理输入）
> **引用**: Pilot Audit（`ZIWEI_CORPUS_PILOT_AUDIT.md`）与 Scope
> （`ZIWEI_CORPUS_SCOPE.md`）中的 ⚠️/🔴 标记

---

| Gap ID | 描述 | 影响 | 解决阶段 | 状态 |
|--------|------|------|----------|------|
| GAP-01 | 《紫微斗数全集》原文不可获取（扫描本质量参差/版本待确认）［Phase 7.3.1: 未推进, 见决策点 D-5］ | classic_text 引用计划 3 中 1 无法落地; 星曜对照缺第二权威 | Phase 7.1.3 | 🟡 SOURCE_DISCOVERED — GitHub 候选来源已定位（`Renhuai123/ziwei-doushu`, MIT, 含 `quanji.ts`）, 待正文获取与核验; 不自动作为 Tier 1 原始来源 |
| GAP-02 | 中州派讲义（王亭之）无授权数字版; 版次/页码 provenance 不完整 | school_commentary 引用（ref:school:zhongzhou_minggong）待补充 provenance; 7.1.3 school 槽位（+1 条）因此未生产 | **Phase 7.1.3 处理结果: REMAINS OPEN** —— 已核实公开来源无可补全信息, 不虚构; 该引用标记 **not_authoritative**（仅 Pilot 历史保留, 不作为正式依据）; 待可核实来源出现或用户降级决策 | 待解决 |
| GAP-03 | Schema 无法表达「流派权重分歧的量化归属」（某解释属于哪派多重的判定） | 冲突处理依赖 SchoolView/evidence 人工赋权, 无机器可校验的归属规则 | Phase 8+（规范治理输入） | 记录（不修改 KB 规范） |
| GAP-04 | ten_god 节点属 bazi 体系, 但当前仅 Ziwei Corpus 存在（跨系统归属无独立语料位置） | 10 个 ten_god 节点的语料归属待 BaZi Corpus 授权后统一 | Phase 7.1.1（bazi 侧登记）+ 后续 | **P2.1（2026-10-03）: BaZi Corpus 已建立**（`bazi_corpus:0.1.0`, candidate）, 十神 10 节点以 `bazi_` 域前缀收录（`kn:ten_god:bazi_*`）; Ziwei 冻结语料内的 `kn:ten_god:*`（systems:[bazi]）**保持不变**（冻结件不可改）→ 同一概念暂存两份, 归属统一待 Ziwei Corpus 冻结流程修订; 跨域 ID 唯一性由 `knowledge/validate.py` 强制 | 🟡 **部分缓解（两份并存待统一）** |
| GAP-05 | 神煞/辅星体系无单一权威来源（南派/北派/中州差异大） | auxiliary_star/shen_sha 生产受阻 | **Phase 7.2A: Schema 部分 RESOLVED**（两类型均裁定 A, 无需 ACP）。**Phase 7.2B: 来源策略已定义（Tier 1 直产 / Tier 2+ 多源交叉 / 不可核实不生产）; 生产授权已获; 但实际生产因源文本不可达 → 0 节点（见 GAP-12 / GAP-13）**。**Phase 7.3.1: Tier 1 原文已获取并逐字核验（36/36 断言 + 10/10 差异核验）→ 证据侧阻塞解除**（见 KNOWLEDGE_PHASE_7.3.1_REPORT.md）。剩余阻塞 = 生产授权（D-1）+ 流派差异的 SchoolView 落地方案 | 🟢 **CLOSED（证据与生产侧）** —— Phase 7.2B-R 首批生产 23 节点（shen_sha 11 / auxiliary_star 12）; 流派差异以 `schools` 显式保留（羊刃: 子平阴干无刃说）; **Phase 7.2B-R2 追加 7 类**（空亡/元辰/灾煞/六厄/勾绞/天罗地网/十恶大败）, shen_sha 共 18 节点; **Phase 7.2B-R3 追加 9 类**（金舆/三奇/天德/月德/太极贵人/学堂/词馆/德秀/暗金的煞）, shen_sha 共 **27** 节点（限定范围: 卷三已核章节; 数量超 Phase-7.1.0 规划带 → **2026-09-16 经 D-12=A 人工追认**, 见 `KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md` §4） |
| GAP-06 | pattern（格局）收录与解释域边界（A-8: Ziwei 格局链路断裂） | pattern 节点仅作知识收录, 无计算消费者; 收录必要性待解释域 Sprint 确认 | Phase 7.1.4+（解释域授权） | 记录 |
| GAP-07 | 断事类（career/personality/marriage/health/wealth/annual_fortune/major_luck）依赖未实现能力（ZW-017 边界） | 8 种 node_type 第一波范围外 | 后续阶段（功能 Sprint 后） | 记录 |
| GAP-08 | 用神类（yong_shen/xi_shen/ji_shen/tiao_hou）属子平体系, 无跨域授权 | 4 种 node_type 范围外 | 跨域授权（BaZi 语料阶段） | 记录 |
| GAP-09 | 星曜级 xing（刑）/ hai（害）关系**无 Tier 1 来源支撑**（Phase 7.1.2 候选 9 条经契约 BC-012 数学验证 6 条不成立: 贪狼破军永不同宫/天梁巨门·太阳廉贞恒不相对/紫微破军·武曲七杀仅条件同宫无刑害语义等）; 冲刑害为**地支**关系, 而地支节点尚未创建（7.1.4） | Build Plan 24 关系目标无法达成 → 实际 18（he+3/chong+3 完成, xing/hai 缺口 6） | **Phase 7.1.4A（门 A Schema Admission）: ACP_DRAFTED → RESOLVED（无变更）** —— 审计确认 `earthly_branch` **已注册于冻结 KB-002**（任务书"无归属"前提不成立, 见 `docs/governance/ACP/ACP-SCHEMA-001_earthly_branch.md`）; Schema 阻塞移除; 当时剩余阻塞 = 门 C（xing/hai 的 Tier 1 证据评估）+ 门 B（12 地支节点生产授权，7.1.4B） | **CLOSED**（7.1.4B 地支 12 + xing 5；7.1.5 补 hai 6；星曜级不再适用） |
| GAP-10 | 地支 六害（子未/丑午/寅巳/卯辰/申亥/酉戌）与 恃势之刑（丑戌未）**未能在可获取 Tier 1 文本中逐对验证**（渊海子平 wikisource 通行本: 六害仅出现术语、未列配对; 丑戌未刑组无原文; 三刑仅验证 寅巳申环 + 子卯互刑）——按 Gate C 证据规则**拒绝生产**, 不预设数量 | 门 C 产出 xing 5 条（寅巳申×3 + 子卯×2）, hai 0 条; 传统六害/恃势之刑缺失 9 条候选 | **Phase 7.1.5 Gate A: RESOLVED（CLOSED）** —— 《三命通会》卷二（wikisource 通行本, 新增 Tier 1 来源 source_sanming_01）原文逐字验证: 论三刑「丑顺至戌，戌顺至未…恃势之刑」+ 论六害 六配对全出 → 生产 **xing 3（丑戌未环）+ hai 6（六配对）**; 9 条全部通过准入 | **CLOSED** |
| GAP-12 | auxiliary_star（紫微辅星）Tier 1 主源**原文未入库** —— `source_ziwei_01`《紫微斗数全书》source_01.yaml 已登记 URL（wikisource 公有领域）但未 ingested; `source_ziwei_02`《紫微斗数全集》GAP-01 待获取 | auxiliary_star 首批节点**0 生产**（7.2B）—— 辅星语义的权威定义在紫微全书, 无原文则无法逐字核验; 按"不可核实→不生产"原则拒绝 | Phase 7.2B → **7.3.1** | 🟢 **EVIDENCE_VERIFIED**（2026-09-15）—— 紫微全书 卷一/卷二/卷三 已获取（revision-pinned; 卷一 revid 7913704, sha256 9beb8038…818a）; 卷一·諸星問答論 輔星 11 条 + 天馬 + 羊陀/羊陀火鈴 两组总论**逐字核验 PASS**（断言 36/36, 差异核验 10/10, 见 `KNOWLEDGE_PHASE_7.3.1_EVIDENCE_DOSSIER.md`）。**Phase 7.2B-R（2026-09-15）: 12 辅星已生产**（`nodes/auxiliary_star.yaml`, 逐字核验 23/23 PASS）→ **CLOSED（限定范围: 卷一·諸星問答論）**; 《紫微斗数全集》另见 GAP-01（未推进） |
| GAP-14 | **四化（化禄/化权/化科/化忌）无对应 node_type** —— 《紫微斗數全書》卷一·諸星問答論 四节原文已获取（revid 7913704, 逐字可核验），但冻结 KB-002 `NodeType`（20 种）与 `reference/knowledge.py::NodeType` 枚举中**无四化类型**；归入 `auxiliary_star` 会混淆「星曜」与「星曜变换」语义 | 四化暂不可生产；如判定须收录，须先走 Schema Admission Gate / ACP | Phase 7.2B-R2 复核（2026-09-16）发现 | 🟡 **SCHEMA_GAP（未解决）** —— 记录不生产（H3/E7：不擅自扩 schema）。决策点 D-6 |
| GAP-13 | shen_sha（神煞）Tier 1 原文**逐字核验未达成** —— `source_sanming_01`《三命通会》/`source_bazi_01`《渊海子平》均已登记（wikisource 通行本, 7.1.5 曾成功核验卷二·三刑/六害）; 但 7.2B/7.3 会话内对 wikisource 的 webfetch 4 次失败（timeout / transport error）, 神煞章节原文未能获取 | shen_sha 首批节点**0 生产**（7.2B）—— 来源已登记且理论上可达, 但本会话无法逐字核验; 按"不虚构"原则拒绝以训练知识/网络常见度替代原文 | Phase 7.2B → **7.3.1** | 🟢 **EVIDENCE_VERIFIED**（2026-09-15）—— 三命通會 卷一~卷九 + 淵海子平 全量获取（revision-pinned; 卷三 revid 2184219 / 卷二 2292392 / 卷六 845352 / 淵海子平 2593607）; 神煞诸论**逐字核验 PASS**: 论十干禄 / 论驿马 / 论天乙贵人 / 论劫煞亡神 / 论羊刃 / 论孤辰寡宿 / 总论诸神煞（卷三）, 论将星华盖 / 论咸池（卷二）, 论阳刃（卷六）, 论阳刃/论劫财（淵海子平; 跨源对照）。**Phase 7.2B-R（2026-09-15）: 11 神煞已生产**（`nodes/shen_sha.yaml` + 12 条条目级引用）→ **CLOSED（限定范围: 已核章节）**; 转录字形差异 V-1~V-4 已在引用 passage 内就地标注 |

| GAP-15 | **星曜五行归属多源冲突**（同一星曜在不同卷给出不同五行）：卷一《紫微斗數全書》「羊陀二星总论」作「擎羊陀罗二星属火金」、同卷「羊陀火铃四星总论」韵文作「火铃陀罗金」；卷二·安身命例「分属五行」名录则作「擎羊属金…陀罗属金…火星属火…铃星属火」 | 擎羊 / 陀罗 / 火星 / 铃星 的属五行**不可单值确定**；按 Admission Policy §3「多源并列、不静默合并」，`shuyu` 只生产**无冲突**的 5 条主星关系，冲突星曜**不生产** | 2026-09-16 关系补齐时发现 | 🟡 **OPEN（多源冲突）** —— 待人工裁定口径：按流派分层（多 evidence/SchoolView 并列）生产，或维持不生产。决策点 D-11 |

---

## 治理说明

1. 本表为**未来治理输入**：解决阶段到达时重新评估, 不预先承诺。
2. 规范修订需求（GAP-03）须走独立治理流程（KB 规范为冻结文件, 本表只记录）。
3. 新发现缺口随时追加（追加式, 不覆盖历史行）。
