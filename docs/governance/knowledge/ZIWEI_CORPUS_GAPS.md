# Ziwei Corpus Open Gaps（已知缺口登记）

> **Sprint**: Phase 7.1.0 — Corpus Scope & Source Freeze
> **日期**: 2026-08-13
> **状态**: 记录（GAP 不修改当前规范; 仅作为未来治理输入）
> **引用**: Pilot Audit（`ZIWEI_CORPUS_PILOT_AUDIT.md`）与 Scope
> （`ZIWEI_CORPUS_SCOPE.md`）中的 ⚠️/🔴 标记

---

| Gap ID | 描述 | 影响 | 解决阶段 | 状态 |
|--------|------|------|----------|------|
| GAP-01 | 《紫微斗数全集》原文不可获取（扫描本质量参差/版本待确认） | classic_text 引用计划 3 中 1 无法落地; 星曜对照缺第二权威 | Phase 7.1.3 | 🟡 SOURCE_DISCOVERED — GitHub 候选来源已定位（`Renhuai123/ziwei-doushu`, MIT, 含 `quanji.ts`）, 待正文获取与核验; 不自动作为 Tier 1 原始来源 |
| GAP-02 | 中州派讲义（王亭之）无授权数字版; 版次/页码 provenance 不完整 | school_commentary 引用（ref:school:zhongzhou_minggong）待补充 provenance; 7.1.3 school 槽位（+1 条）因此未生产 | **Phase 7.1.3 处理结果: REMAINS OPEN** —— 已核实公开来源无可补全信息, 不虚构; 该引用标记 **not_authoritative**（仅 Pilot 历史保留, 不作为正式依据）; 待可核实来源出现或用户降级决策 | 待解决 |
| GAP-03 | Schema 无法表达「流派权重分歧的量化归属」（某解释属于哪派多重的判定） | 冲突处理依赖 SchoolView/evidence 人工赋权, 无机器可校验的归属规则 | Phase 8+（规范治理输入） | 记录（不修改 KB 规范） |
| GAP-04 | ten_god 节点属 bazi 体系, 但当前仅 Ziwei Corpus 存在（跨系统归属无独立语料位置） | 10 个 ten_god 节点的语料归属待 BaZi Corpus 授权后统一 | Phase 7.1.1（bazi 侧登记）+ 后续 | 待解决（保留于 Ziwei Corpus 为共享概念, 标注 systems:[bazi]） |
| GAP-05 | 神煞/辅星体系无单一权威来源（南派/北派/中州差异大） | auxiliary_star/shen_sha 生产受阻 | **Phase 7.2A: Schema 部分 RESOLVED**（两类型均裁定 A, 无需 ACP）。**Phase 7.2B: 来源策略已定义（Tier 1 直产 / Tier 2+ 多源交叉 / 不可核实不生产）; 生产授权已获; 但实际生产因源文本不可达 → 0 节点（见 GAP-12 / GAP-13）**。剩余阻塞 = Tier 1 原文可达性 | 待源文本可达 |
| GAP-06 | pattern（格局）收录与解释域边界（A-8: Ziwei 格局链路断裂） | pattern 节点仅作知识收录, 无计算消费者; 收录必要性待解释域 Sprint 确认 | Phase 7.1.4+（解释域授权） | 记录 |
| GAP-07 | 断事类（career/personality/marriage/health/wealth/annual_fortune/major_luck）依赖未实现能力（ZW-017 边界） | 8 种 node_type 第一波范围外 | 后续阶段（功能 Sprint 后） | 记录 |
| GAP-08 | 用神类（yong_shen/xi_shen/ji_shen/tiao_hou）属子平体系, 无跨域授权 | 4 种 node_type 范围外 | 跨域授权（BaZi 语料阶段） | 记录 |
| GAP-09 | 星曜级 xing（刑）/ hai（害）关系**无 Tier 1 来源支撑**（Phase 7.1.2 候选 9 条经契约 BC-012 数学验证 6 条不成立: 贪狼破军永不同宫/天梁巨门·太阳廉贞恒不相对/紫微破军·武曲七杀仅条件同宫无刑害语义等）; 冲刑害为**地支**关系, 而地支节点尚未创建（7.1.4） | Build Plan 24 关系目标无法达成 → 实际 18（he+3/chong+3 完成, xing/hai 缺口 6） | **Phase 7.1.4A（门 A Schema Admission）: ACP_DRAFTED → RESOLVED（无变更）** —— 审计确认 `earthly_branch` **已注册于冻结 KB-002**（任务书"无归属"前提不成立, 见 `docs/governance/ACP/ACP-SCHEMA-001_earthly_branch.md`）; Schema 阻塞移除; 剩余阻塞 = **门 C**（xing/hai 的 Tier 1 证据评估）+ **门 B**（12 地支节点生产授权, 7.1.4B） | 待门 B/C |
| GAP-10 | 地支 六害（子未/丑午/寅巳/卯辰/申亥/酉戌）与 恃势之刑（丑戌未）**未能在可获取 Tier 1 文本中逐对验证**（渊海子平 wikisource 通行本: 六害仅出现术语、未列配对; 丑戌未刑组无原文; 三刑仅验证 寅巳申环 + 子卯互刑）——按 Gate C 证据规则**拒绝生产**, 不预设数量 | 门 C 产出 xing 5 条（寅巳申×3 + 子卯×2）, hai 0 条; 传统六害/恃势之刑缺失 9 条候选 | **Phase 7.1.5 Gate A: RESOLVED（CLOSED）** —— 《三命通会》卷二（wikisource 通行本, 新增 Tier 1 来源 source_sanming_01）原文逐字验证: 论三刑「丑顺至戌，戌顺至未…恃势之刑」+ 论六害 六配对全出 → 生产 **xing 3（丑戌未环）+ hai 6（六配对）**; 9 条全部通过准入 | **CLOSED** |
| GAP-12 | auxiliary_star（紫微辅星）Tier 1 主源**原文未入库** —— `source_ziwei_01`《紫微斗数全书》source_01.yaml 已登记 URL（wikisource 公有领域）但未 ingested; `source_ziwei_02`《紫微斗数全集》GAP-01 待获取 | auxiliary_star 首批节点**0 生产**（7.2B）—— 辅星语义的权威定义在紫微全书, 无原文则无法逐字核验; 按"不可核实→不生产"原则拒绝 | Phase 7.2B | 🟡 SOURCE_DISCOVERED — 紫微全书 wikisource URL 已登记（`https://zh.wikisource.org/wiki/紫微斗數全書`）, 但 webfetch 阻塞（4 次超时）, 未完成 ingesting + verbatim 核验 |
| GAP-13 | shen_sha（神煞）Tier 1 原文**逐字核验未达成** —— `source_sanming_01`《三命通会》/`source_bazi_01`《渊海子平》均已登记（wikisource 通行本, 7.1.5 曾成功核验卷二·三刑/六害）; 但 7.2B/7.3 会话内对 wikisource 的 webfetch 4 次失败（timeout / transport error）, 神煞章节原文未能获取 | shen_sha 首批节点**0 生产**（7.2B）—— 来源已登记且理论上可达, 但本会话无法逐字核验; 按"不虚构"原则拒绝以训练知识/网络常见度替代原文 | Phase 7.2B | 🟡 SOURCE_DISCOVERED — 三命通会/渊海子平 wikisource URL 已确认（websearch 验证）, 但 webfetch 阻塞, 未完成 verbatim 核验 |

---

## 治理说明

1. 本表为**未来治理输入**：解决阶段到达时重新评估, 不预先承诺。
2. 规范修订需求（GAP-03）须走独立治理流程（KB 规范为冻结文件, 本表只记录）。
3. 新发现缺口随时追加（追加式, 不覆盖历史行）。
