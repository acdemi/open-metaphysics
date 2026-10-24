# Knowledge 语料库（Knowledge Corpus）

> **阶段**: Phase 7.1.6 —— **Ziwei Corpus Freeze v1.0.0**（2026-09-16, D-12=A 批准）
> + **P2.1 BaZi Knowledge Integration**（2026-10-03, BaZi Corpus candidate 0.1.0）
> + **P2.2 Qimen Knowledge Integration**（2026-10-03, Qimen Corpus candidate 0.1.0）
> + **P2.3 Liuyao Knowledge Integration**（2026-10-19, Liuyao Corpus candidate 0.1.0）
> + **P2.4 Liuyao Knowledge Enrichment II**（2026-10-19, Liuyao Corpus candidate 0.2.0
>   → **2026-10-24 Corpus Freeze v1.0.0**）
> **状态**: **Pipeline Validated**；Ziwei Corpus **FROZEN（`ziwei_corpus:v1.0.0`）**；
> BaZi / Qimen Corpus **CANDIDATE（各 `0.1.0`）**；Liuyao Corpus **CANDIDATE（`0.2.0`）**
> **规范基准**: `docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md`（KB-001~020, Frozen）+
> `docs/design/phase6/01_knowledge_layer_architecture.md`（Frozen）+
> 规范性模型 `reference/knowledge.py`
> **边界**: Knowledge 为**只读引用层**，不参与任何计算、不产生结论、
> 不修改 Evidence / Confidence（KB 契约架构边界）。

---

## 1. 范围

- **语料域**: Ziwei（冻结 v1.0.0）+ BaZi（P2.1 候选 0.1.0）+ Qimen（P2.2 候选 0.1.0）
  + Liuyao（P2.3/P2.4 候选 0.2.0）。
- **Ziwei 演进**: Phase 7.0 试点（20 节点/12 关系/3 引用，验证 Pipeline）→
  Phase 7.1.1~7.1.6 全量建设（核心词汇 → 天干/地支/关系/引用扩展）→
  Phase 7.2A Schema 门 → 7.2B-R/·R2/·R3 证据驱动生产（辅星/神煞）→
  **Phase 7.1.6 关系层补齐（yinyong/shuyu）+ Corpus Freeze v1.0.0**。
  当前 **102 节点 + 47 关系 + 41 引用**（`ziwei_corpus.json` 实测, digest `93dba067…`；2026-10-24 EOL 勘误后）。
  治理进展见 `docs/governance/knowledge/`（Scope/Source/Admission/Build Plan/
  Coverage Matrix/Gaps/各 Phase 报告/**7.1.6 FREEZE**）。
- **BaZi 演进（P2.1, 2026-10-03）**: 首批**最小而有实际价值**的结构化语料 ——
  五行基础（5+旺衰 1）/ 十神全量（10）/ 日主与月令（2）/ 十天干（10）/ 十二地支（12）
  = **40 节点**；关系（五行生克 / 天干五合 / 地支六合 / 六冲 / 三合 / 三会 /
  刑（含自刑）/ 六害 / 六破）= **67 关系**；条目级引用 **14**（`bazi_corpus.json`）。
  目标链路（已由测试锁定）:
  `BaZi calculation → deterministic result → BaZi knowledge retrieval →
  explanation context → /agents/bazi/explain → HTTP response`。
  证据级别与剩余缺口见本文件 §7 与 P2.1 交付报告（章节级逐字核验范围有限，
  未核验原文一律不引用）。
- **Qimen 演进（P2.2, 2026-10-03）**: 第二批**有限、结构化、高价值**的语料 ——
  九宫（9 + 总纲 1）/ 八门（8 + 总纲 1）/ 九星（9 + 总纲 1）/ 八神（8 + 总纲 1）/
  奇门结构与法则（阳遁·阴遁·值符·值使·六仪·三奇·旬首·空亡·三元）= **47 节点**；
  关系（各子项**属于**总纲 + 地盘**宫↔星·宫↔门**固定配属 + 结构对应）= **60 关系**；
  条目级引用 **15**（`qimen_corpus.json`）。
  目标链路（已由测试锁定）:
  `Qimen calculation → deterministic result → Qimen knowledge retrieval →
  explanation context → /agents/qimen/explain → HTTP response`。
  **不重复建设 BaZi 语料**: 十天干/十二地支沿用既有 BaZi 节点（同一 retriever
  已索引，跨域复用），Qimen 侧只收录奇门特有的六仪/三奇/旬首/空亡概念。
  证据级别与剩余缺口见 §7。
- **Liuyao 演进（P2.3 / P2.4, 2026-10-19）**: 第三/四批**有限、结构化、高价值**的语料 ——
  六亲（六亲总纲 + 父母/兄弟/子孙/妻财/官鬼）= 6 / 六神（总纲 + 青龙·朱雀·勾陈·
  螣蛇·白虎·玄武）= 7 / 京房八宫（八宫总纲 + 乾坎艮震巽离坤兑）= 9 /
  结构与法则 = 31（P2.3 本卦·变卦·动爻·世应·纳甲·月建·日辰·旬空·六冲卦·六合卦·
  三合局·三刑·仇神 + P2.4 暗动·动散·卦变生克墓绝·反吟·伏吟·生旺墓绝·应期·
  游魂·归魂·月破·飞神·伏神·进神·退神·随鬼入墓·独发·独静·两现）/ 五行域内端点 = 5 /
  用神体系（用神·元神·忌神）= 3 = **61 节点**；关系（成员归属 + 宫属五行 + 生克 +
  结构对应 + 月建/日辰作用）= **66 关系**；条目级引用 **41**
  （`liuyao_corpus.json` 1.0.0，**frozen**）。
  本语料是 P2 系列新增语料中**首个在 Sources 侧完成 revision-pinned 抓取 +
  逐章逐字核验**的域（《增刪卜易》主页 revid 2572918 + 24 个子页 revid/SHA-256
  登记 + 主页卷之二第 27–32 章逐字核验）。
  目标链路（已由测试锁定）:
  `Liuyao calculation → deterministic result → Liuyao knowledge retrieval →
  explanation context → /agents/liuyao/explain → HTTP response`。
  **与既有域的关系**: 五行节点为六爻生克端点，语义与 engine 一致但**域内单独
  登记**（`liuyao_` 前缀），避免与 Ziwei 冻结 `kn:wuxing:*` / BaZi 节点 ID 冲突。
  证据级别与剩余缺口见 §7。
- **变更流程（Ziwei 冻结后）**: 任何 node/relation/reference 变更须走 **Corpus 级审查**
  （提案 → 逐字证据核验 → validate/确定性/回归 → 人工批准 → 版本递增）。
  见 `docs/governance/knowledge/KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md`。
  BaZi / Qimen 语料为 candidate，同样遵守 `ZIWEI_CORPUS_ADMISSION_POLICY.md`
  的准入原则（Schema 有效 / 语义有效 / provenance 非空 / 来源已登记 /
  确定性序列化 / 冲突显式）。
- **来源**: Tier 1 来源（`sources/ziwei/` 紫微斗数全书; `渊海子平`; `三命通会`；
  `sources/bazi/` 复用同一已 revision-pinned 获取的 `渊海子平` + `三命通会`；
  `sources/qimen/` 新增 `奇门遁甲统宗` + `烟波钓叟歌`，**书级来源归属 +
  已读章节锚点，无 revision-pin 抓取件**；
  `sources/liuyao/` 新增 `增刪卜易`，**主页 revid 2572918 + 24 个子页
  revision pin / 原始字节 SHA-256 / 逐章逐字核验 + 主页卷之二第 27–32 章逐字核验**）——原始数据引用，
  **不包含**古籍全文

## 2. 目录结构

```text
knowledge/
├── README.md                  # 本文件
├── sources/<domain>/          # 来源元数据（引用，非数据）
├── corpus/<domain>/
│   ├── nodes/                 # KnowledgeNode
│   ├── relations/             # KnowledgeRelation
│   └── references/            # KnowledgeReference
│   # <domain> ∈ {ziwei, bazi, qimen, liuyao}
├── pipeline.py                # 确定性合并 + 校验 + checksum（多域）
├── validate.py                # Schema 校验（KB-001~020，多域 + 跨域 ID 唯一性）
├── ziwei_corpus.json          # Pipeline 输出（确定性 JSON, 勿手改）
├── bazi_corpus.json           # Pipeline 输出（确定性 JSON, 勿手改）
├── qimen_corpus.json          # Pipeline 输出（确定性 JSON, 勿手改）
└── liuyao_corpus.json         # Pipeline 输出（确定性 JSON, 勿手改）
```

## 3. 统计

| 语料 | 状态 | nodes | relations | references |
|------|------|-------|-----------|------------|
| `ziwei_corpus` | frozen 1.0.0 (digest `93dba067…`；EOL 勘误) | 102 | 47 | 41 |
| `bazi_corpus` | candidate 0.1.0 (digest `69b6edea…`) | 40 | 67 | 14 |
| `qimen_corpus` | candidate 0.1.0 (digest `40de5c45…`) | 47 | 60 | 15 |
| `liuyao_corpus` | frozen 1.0.0 (digest `3a09a08e…`) | 61 | 66 | 41 |

Ziwei 类型覆盖: nodes wuxing(5)/main_star(14)/palace(12)/ten_god(10)/
heavenly_stem(10)/earthly_branch(12)/auxiliary_star(12)/shen_sha(27);
relations sheng(5)/ke(5)/he(10)/chong(3)/xing(8)/hai(6)/shuyu(5)/yinyong(5)。

BaZi 类型覆盖: nodes wuxing(6: 木火土金水 + 旺衰)/ten_god(10)/
heavenly_stem(11: 十干 + 日主)/earthly_branch(13: 十二支 + 月令);
relations 五行生克(10, sheng/ke)、天干五合(5, he)、地支六合(6, he)、
六冲(6, chong)、三合(8, he)、三会(8, he)、刑(12, xing, 含自刑 4)、
六害(6, hai)、六破(6, duiying + `relation_subtype=po`, 见 §7 GAP)。

Qimen 类型覆盖: nodes palace(10: 九宫 9 + 九宫总纲)/main_star(10: 九星 9 + 九星总纲)/
shen_sha(18: 八门 8 + 八门总纲 + 八神 8 + 八神总纲)/pattern(9: 阳遁·阴遁·值符·值使·
六仪·三奇·旬首·空亡·三元);
relations shuyu(36: 九宫/八门/九星/八神 成员 + 值符属九星 + 值使属八门)、
duiying(24: 地盘宫↔星 9 + 地盘宫↔门 8 + 值符↔值符神 + 阳遁↔阴遁 + 旬首↔六仪 +
三奇↔六仪 + 空亡↔旬首 + 三元↔阴阳遁 2)。

Liuyao 类型覆盖: nodes ten_god(6: 六亲总纲 + 五类六亲)/shen_sha(7: 六神总纲 + 六神)/
palace(9: 八宫总纲 + 八宫)/pattern(31: P2.3 结构 + P2.4 暗动·动散·卦变生克墓绝·
反吟·伏吟·生旺墓绝·应期·游魂·归魂·月破·飞神·伏神·进神·退神·随鬼入墓·独发·独静·两现)/
wuxing(5)/yong_shen(1)/xi_shen(1: 元神)/ji_shen(1: 忌神);
relations shuyu(29: 八宫成员 8 + 宫属五行 8 + 六亲成员 5 + 六神成员 6 + 游魂/归魂属八宫 2)、
sheng(7: 五行相生 5 + 元神生用神 + 仇神生忌神)、ke(7: 五行相克 5 + 忌神克用神 +
仇神克元神)、duiying(21: P2.3 对应 11 + P2.4 月破/飞伏/进退/反伏/暗动/两现/卦变/随鬼 10)、
zhiyue(2: 月建作用用神 + 日辰作用用神)。

> 数量以 JSON 产物为准；node_type / relation_type / ref_type 具体枚举以
> 冻结 KB-002 / KB-007 / KB-011 & `reference/knowledge.py` 为准（上表为语义概览）。
> BaZi / Qimen / Liuyao 节点 slug 带 `bazi_` / `qimen_` / `liuyao_` 域前缀，ID 形式仍为
> KB-001 的 `kn:<type>:<slug>`，以与 Ziwei 冻结语料在**同一检索库**中保持 ID 唯一
> （`validate.py` 跨域校验）。

## 4. 运行

```bash
uv run python knowledge/pipeline.py            # 生成全部域 corpus + sha256
uv run python knowledge/pipeline.py bazi       # 仅生成 BaZi corpus
uv run python knowledge/pipeline.py qimen      # 仅生成 Qimen corpus
uv run python knowledge/pipeline.py liuyao     # 仅生成 Liuyao corpus
uv run python knowledge/validate.py            # 多域校验（PASS/FAIL 报告）
uv run pytest tests/test_knowledge_pipeline.py tests/test_bazi_knowledge_corpus.py \
              tests/test_qimen_knowledge_corpus.py tests/test_liuyao_knowledge_corpus.py \
              tests/test_liuyao_explain_integration.py -q
```

Pipeline 确定性要求（硬性）：无时钟/随机/网络；`sort_keys=True`；
来源 digest（SHA-256）嵌入 corpus metadata 用于版本追踪。

## 5. 添加新来源 / 节点

1. `sources/<domain>/source_XX.yaml` 登记来源元数据（title/author/school/url）
2. `corpus/<domain>/nodes|relations|references/*.yaml` 追加条目
   （顶层 `nodes:`/`relations:`/`references:` 列表；字段按 reference/knowledge.py）
3. 重跑 `pipeline.py` + `validate.py` + 回归测试
4. 保持 `provenance`（source.text）非空；id 唯一（含跨域）；relation 端点必须存在
5. 新增语料域: 在 `pipeline.py::DOMAINS`、`validate.py::DOMAINS` 与
   `src/openmetaphysics/rag/corpus.py::DOMAIN_CORPUS_FILES` 登记（复用同一
   Pipeline / 校验器 / Retriever，不新建第二套架构）

## 6. 边界

- ❌ 语料不参与 Ziwei/BaZi/Qimen/Liuyao 计算（只读引用层）
- ❌ 不引入 LLM/RAG 重写/embedding/向量库/外部检索服务到 Pipeline
- ❌ 不修改冻结规范（KB-001~020）；Schema 变更须 ACP/门控
- ❌ 不生产无 Tier 1 来源的节点/关系（Gate C 证据规则）
- ❌ 不修改已冻结的 Ziwei 语料（P2.1 / P2.2 / P2.3 / P2.4 均未改动内容）；
  2026-10-24 经 `ACP-KNOWLEDGE-001` 仅做 EOL/digest 勘误（内容零变化），digest 由
  `69d6e2a6…` 变为 `93dba067…`；BaZi（`69b6edea…`）与 Qimen（`40de5c45…`）
  语料在 P2.4 及本次勘误中逐字节未变
- ❌ 可检索节点文本（`name_cn + interpretation`）不写 ASCII 技术标识符：字符级评分
  的稀有度权重（`1 + ln(N/df)`）会把 "engine" / "normative" 一类拉丁词当成极稀有
  「字符」，压过真正的中文术语命中。技术字段写进 `attributes` / `tags` / `name_en`。

## 7. 已知语料缺口（P2.1 / P2.2 / P2.3 / P2.4 记录）

| 缺口 | 说明 | 处置 |
|------|------|------|
| 破（相破）无 relation_type | 冻结 KB-007 的 15 类中没有 `po` | 以中性 `duiying` 承载 + `relation_subtype=po` + evidence 保留规范名；未修改冻结契约，记为待裁定 |
| 日主/月令 无专用 node_type | 冻结 KB-002 的 20 类无「命局结构位概念」 | 分别以 `heavenly_stem` / `earthly_branch` 收录（日主即日干、月令即月支），记为 schema 缺口 |
| **GAP-QIMEN-01**: 八门无专用 node_type | 冻结 KB-002 的 20 类无「门 / 门户」类别 | 八门 8 节点 + 总纲以 `shen_sha`（象义类符号实体）承载，语义经 `tags`/`attributes` 保留；**未修改冻结 Schema**；建议未来经 ACP 评估新增 `door` 类（P2.2 不修改 NodeType） |
| **GAP-QIMEN-02**: 奇门结构/法则无专用 node_type | 冻结 KB-002 无「结构 / 法则 / 概念」类别 | 阳遁·阴遁·值符·值使·六仪·三奇·旬首·空亡·三元 9 节点以 `pattern`（具名配置）承载；**未修改冻结 Schema**；待裁定 |
| **GAP-QIMEN-03**: 八神流派命名差异 | 《奇门遁甲统宗》卷之二作「五勾陈、六朱雀，朱雀下有玄武、勾陈下又白虎」 | 语料按 deterministic engine 实际用名（白虎/玄武）收录，异名保留在 `attributes.tongzong_name` 与 `bashen_variant`；不改 engine |
| **GAP-LIUYAO-01**: 六亲无专用 node_type | 冻结 KB-002 的 20 类无「六亲」类别 | 六亲总纲 + 五类六亲（6 节点）以 `ten_god`（亲属角色）承载，语义经 `tags`/`attributes` 保留；**未修改冻结 Schema**；待裁定（同 GAP-QIMEN-02 模式） |
| **GAP-LIUYAO-02**: 六爻结构/法则无专用 node_type | 冻结 KB-002 无「结构 / 法则 / 概念」类别 | 本卦/变卦/动爻/世应/纳甲/月建/日辰/旬空/六冲卦/六合卦/三合局/三刑 + P2.4 暗动/动散/卦变生克墓绝/反吟/伏吟/生旺墓绝/应期/游魂/归魂/月破/飞神/伏神/进神/退神/随鬼入墓/独发/独静/两现 等 31 节点以 `pattern`（具名配置）承载；**未修改冻结 Schema**；待裁定 |
| **GAP-LIUYAO-03**: 元神无专用 node_type | 冻结 KB-002 无「元神」类别（用神/喜神/忌神之外） | 元神以 `xi_shen`（喜神/有益之神）承载，语义经 `tags`/`attributes` 显式保留；**未修改冻结 Schema**；待裁定 |
| **GAP-LIUYAO-04**: 仇神无专用 node_type | 同上 | 仇神以 `pattern` 承载，其「克元神而生忌神」生克链以独立 `ke`/`sheng` 关系表达；**未修改冻结 Schema**；待裁定 |
| **GAP-LIUYAO-05**: 互卦无定义性原文 | 《增刪卜易》已核章节仅见「伏神無用又尋互卦」一句提及互卦，**无定义性原文** | **不生产该节点**（不可核实 → 不生产，H5）；待可核验出处后补充 |
| **GAP-LIUYAO-06**: 星煞章未收录 | P2.4 已读 `星煞章第三十三`，但星煞体系庞杂、与六神/神煞边界及 `shen_sha`/`pattern` 归属未定，价值密度低于本轮结构法则 | **本轮不生产**；留待专门 Sprint 先做 schema 归属裁定与占验价值筛选 |
| Liuyao 转录异文 | 转录本 `/4「辰在內」`（八宫纳甲当为艮）、`/6「天地觀」`（乾宫第四卦当为风地观）、`/18「元武/滕蛇/靑龍」`、`/20「𨿽」`（雖之异体）、`/5「原劍按」`（转录者按语） | 逐条登记于 `sources/liuyao/source_liuyao_01.yaml`「转录异文登记」；语料按 engine/八宫用名收录并注明异文，引文保留原字；**不静默改写** |
| 逐字核验修订锚定（Liuyao） | 已核验 24 个子页章节（卦象圖/八宮圖/渾天甲子/六親歌/世應/動變/用神/用神元神忌神仇神/五行相生·相克/月將/日辰/六神/六合/六沖/三刑/旬空/暗動/動散/卦變生克墓絕/反伏/生旺墓絕/應期總注/歸魂遊魂）+ 主页卷之二第 27–32 章，主页 revid 2572918 + 子页 revid/SHA-256 逐条登记 | `evidence_status: revision_pinned_verbatim_verified`；未核验章节的原文一律不引用（本 Sprint 无此类引用） |
| 章节级逐字核验范围有限（BaZi） | 仅 三命通会 卷二·论十干化气/论三刑/论六害 与 渊海子平 论大运/论命细法 为已核验章节 | 其余条目为书级来源归属，不引用未核验原文；待后续 Evidence Review |
| 章节级逐字核验范围有限（Qimen） | `奇门遁甲统宗` 仅在线通读章节结构与短锚点，**无 revision-pin 抓取件**；`烟波钓叟歌` 仅确认来源存在 | `evidence_status: source_level_attributed`；所有 `passage` 明示「非逐字核验 / 不据以做逐字核验」；**不声称 VERBATIM_VERIFIED** |
| 默认 k=3 检索排序 | 确定性字符重叠评分偏好覆盖面广的长文（Phase C 已记录） | BaZi 专项查询命中 BaZi 语料 top-1/3；Qimen 八项必需术语（九宫/八门/九星/八神/阴遁/阳遁/值符/值使）均 top-1 命中；Liuyao 组合/单术语查询 36 项（P2.3 18 项 + 暗动/动散/反吟/伏吟/生旺墓绝/应期/游魂/归魂/月破/飞神/伏神/进神/退神/随鬼入墓/独发/独静/两现/卦变回头生克）top-1 命中（测试已锁定实测值；容器术语「六亲/六神」短查询会先命中总纲节点，属预期） |
| **跨平台 EOL 与 `source_digests`** | `source_digests` 为来源 YAML 的**原始字节**摘要；此前 `.gitattributes` 只固定 JSON，YAML 未固定，digest 随 checkout EOL 漂移 | **已解决（`ACP-KNOWLEDGE-001`，2026-10-24）**：`.gitattributes` 增加 `knowledge/**/*.yaml text eol=lf`；Ziwei digest 重登记为 `93dba067…`（内容零变化）；BaZi/Qimen/Liuyao digest 由测试锚定；Linux/LF 与 Windows 均可复现，pipeline 不再改写冻结件 |
| 未覆盖范畴 | BaZi: 格局/用神/大运/流年/神煞等细目、藏干独立节点；Qimen: 三奇喜怒/八门迫制/九星旺相/格局（龙回首·鸟跌穴等）/克应/占法，以及完整的节气局数对照表；Liuyao: 六十四卦各卦本体/卦辞/爻辞、互卦（GAP-LIUYAO-05）、六亲取用细则、神煞（星煞章本轮未收）、卦变全组合与占验案例 | 后续 Knowledge Sprint（本轮不做完整体命理百科） |
