# Knowledge Phase 7.1.4B — Earthly Branch Nodes + xing/hai Evidence Review

> **Sprint**: Phase 7.1.4B（Gate B + Gate C, 人工授权 2026-08-13）
> **日期**: 2026-08-13
> **门控独立性**: 门 B（节点生产）与门 C（关系证据）**独立验收**——节点生产
> 成功**不推导**关系存在; 关系数量完全由 Tier 1 证据决定。
> **结果**: **12 节点 + 5 xing 关系**（证据驱动）; hai 0 条（GAP-10）。

---

## 1. Executive Summary

- **Gate B**: 12 个 `earthly_branch` 节点生产完成（渊海子平 Tier 1, wikisource
  通行本核验 + 紫微斗数全书 BC-010 宫位地支应用）。53 节点全部通过
  KB-001~020 校验与确定性构建。
- **Gate C**: 对 xing/hai 候选执行 Tier 1 原文核验（渊海子平全文检索）:
  - ✅ 验证: 三刑环「寅刑巳、巳刑申、申刑寅」（论大运篇）+「子卯相刑」
    （论命细法篇）→ **生产 5 条 xing 关系**
  - ❌ 未验证: 六害配对（6 条）与恃势之刑丑戌未（3 条）在可获取 Tier 1
    文本中**未逐对出现** → **拒绝生产**（GAP-10）, 不预设数量
- **教训固化**: 「地支关系在传统体系中存在」≠「可进入 Corpus」——
  每条关系必须通过 9 项准入检查（见 §5）。

## 2. Gate B — 12 Earthly Branch Nodes

| # | ID | branch | 五行 | 关联 |
|---|----|--------|------|------|
| 1 | kn:earthly_branch:zi | 子 | 水 | 子时（BC-004）; 与卯刑 |
| 2 | kn:earthly_branch:chou | 丑 | 土 | 丑月（隆冬建丑） |
| 3 | kn:earthly_branch:yin | 寅 | 木 | **十二宫起宫寅=0（BC-010）**; 三刑环成员 |
| 4 | kn:earthly_branch:mao | 卯 | 木 | 与子互刑 |
| 5 | kn:earthly_branch:chen | 辰 | 土 | 辰为水库 |
| 6 | kn:earthly_branch:si | 巳 | 火 | 三刑环成员 |
| 7 | kn:earthly_branch:wu | 午 | 火 | 午时; 与子对宫 |
| 8 | kn:earthly_branch:wei | 未 | 土 | 未为木库 |
| 9 | kn:earthly_branch:shen | 申 | 金 | 三刑环成员 |
| 10 | kn:earthly_branch:you | 酉 | 金 | 酉时 |
| 11 | kn:earthly_branch:xu | 戌 | 土 | 戌为火库 |
| 12 | kn:earthly_branch:hai | 亥 | 水 | 亥为木长生 |

- 每个节点含: source（渊海子平 论天干地支暗藏总诀, wikisource 通行本）/
  interpretation / tags / confidence / attributes（branch_index 按 BC-010 寅=0 约定,
  五行, 生肖）。
- **未修改**任何既有 41 节点 / 18 关系 / 7 引用。

## 3. Gate C — Tier 1 Evidence Review（xing / hai）

### 核验方法

渊海子平全文（zh.wikisource.org/wiki/渊海子平, 通行本）关键词检索:
三刑(11 处) / 六害(5 处) / 寅刑(2 处) / 子卯(1 处) / 相害(0 处) / 六害配对词(0 处)。

### 核验结果

| 候选 | 原文证据 | 结论 |
|------|----------|------|
| 寅刑巳、巳刑申、申刑寅 | ✅「忌寅刑巳、巳刑申、申刑寅」（论大运） | **生产（3 条 directed）** |
| 子刑卯、卯刑子 | ✅「子卯相刑门户，全无礼德」（论命细法） | **生产（2 条 directed, 互刑）** |
| 丑刑戌、戌刑未、未刑丑（恃势之刑） | ❌ 原文未出现 | **拒绝 → GAP-10** |
| 六害: 子未/丑午/寅巳/卯辰/申亥/酉戌 | ❌ 原文仅"六害"术语（5 处）, 未列配对 | **拒绝 → GAP-10** |

### 产出关系（5 条, 全部满足 9 项准入检查）

| ID | source → target | 证据来源 | 章节 | 9 项检查 |
|----|-----------------|----------|------|----------|
| rel:xing:yin_si | 寅 → 巳 | 渊海子平 | 论大运 | ✅ 9/9 |
| rel:xing:si_shen | 巳 → 申 | 渊海子平 | 论大运 | ✅ 9/9 |
| rel:xing:shen_yin | 申 → 寅 | 渊海子平 | 论大运 | ✅ 9/9 |
| rel:xing:zi_mao | 子 → 卯 | 渊海子平 | 论命细法 | ✅ 9/9 |
| rel:xing:mao_zi | 卯 → 子 | 渊海子平 | 论命细法 | ✅ 9/9 |

## 4. 每候选 9 项检查（以 rel:xing:yin_si 为例, 全部 5 条同构）

| # | 问题 | 回答 |
|---|------|------|
| 1 | Relation 是什么？ | 地支三刑之「寅刑巳」（无恩之刑环） |
| 2 | 两个 endpoint 是否均为 earthly_branch？ | ✅ kn:earthly_branch:yin / kn:earthly_branch:si |
| 3 | Tier 1 来源是什么？ | 渊海子平（source_bazi_01, Tier 1） |
| 4 | 来源具体支持什么 claim？ | 「寅刑巳、巳刑申、申刑寅」原文 |
| 5 | claim 如何支持该 relation？ | 原文逐字对应（引文在 evidence.passage） |
| 6 | provenance 是否可追溯？ | ✅ source + chapter（论大运）+ url（wikisource） |
| 7 | 是否存在冲突 SchoolView？ | 无（三刑为通识经典; 无流派分歧） |
| 8 | 是否通过 Schema validation？ | ✅（validate.py PASS, 18+5=23 全通过） |
| 9 | 是否通过 deterministic build？ | ✅（双重 SHA-256 一致） |

## 5. 证据 → claim → relation 映射（Gate C）

| 原文引文 | claim | relation |
|----------|-------|----------|
| 忌寅刑巳、巳刑申、申刑寅 | 寅巳申三刑环 | rel:xing:yin_si / si_shen / shen_yin |
| 子卯相刑门户，全无礼德 | 子卯互刑（无礼之刑） | rel:xing:zi_mao / mao_zi |
| （未验证）六害配对 | — | 拒绝（GAP-10） |
| （未验证）丑戌未恃势之刑 | — | 拒绝（GAP-10） |

## 6. Corpus 最终统计

| 类别 | 数量 | 变化 |
|------|------|------|
| nodes | **53** | +12（earthly_branch） |
| relations | **23** | +5（xing） |
| references | **8** | +1（ref:classic:yuanhai_sanxing） |

## 7. Pipeline / 测试结果

```
$ uv run python knowledge/pipeline.py
corpus written: .../knowledge/ziwei_corpus.json (53 nodes, 23 relations, 8 references)
sha256: 58d9baea...

$ uv run python knowledge/validate.py
VALIDATION PASSED: all corpus entries conform to KB-001~020

确定性: 双重运行 SHA-256 一致 ✅
pytest tests/test_knowledge_pipeline.py: 10/10 PASS
pytest 全量: 599/599 PASS
ruff check / format --check: PASS
```

## 8. GAP 更新

| GAP | 状态 |
|-----|------|
| GAP-09 | **RESOLVED（门 A + 门 C 均完成）** —— Schema 已注册（7.1.4A）; xing 以地支 5 条落地; 星曜级不再适用 |
| GAP-10（新增） | 六害（6）+ 恃势之刑（3）**证据未验证** → 拒绝生产; 后续以三命通会/五行精纪 补充来源后重新评估 |
| GAP-02 | REMAINS OPEN（未触碰） |
| GAP-01/03~08 | 未触碰（范围外） |

## 9. 零触碰验证

| 检查 | 结果 |
|------|------|
| 既有 41 节点 / 18 关系 / 7 引用 | ✅ 未修改 |
| src/ / docs/ziwei/ / KB 规范 / CAPABILITY_LIFECYCLE | ✅ 全空 |
| 新 node_type / relation_type / ref_type | ✅ 未新增 |
| LLM / RAG / 网络爬虫 | ✅ 未引入（来源核验为只读检索, 非采集） |
| 来源修正 | ✅ source_02.yaml URL 勘误（mymmscs → mymmsc, 实测仓库名） |

## 10. 停止声明

**本 Sprint 停止。** 未进入 Phase 7.1.5; 未自行关闭 GAP-10（待补充来源）;
未处理 GAP-01/02、shen_sha、pattern、Interpretation Layer。
等待人工 Evidence Review 与裁决。
