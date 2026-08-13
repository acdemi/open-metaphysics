# Knowledge Phase 7.1.3 — References & Provenance Report

> **Sprint**: Phase 7.1.3 — References & Provenance（证据补全）
> **日期**: 2026-08-13
> **结果**: **+4 References**（classic +2 / modern +1 / oral +1）; 引用总数 3 → **7**
> ⚠️ **范围偏差（诚实声明）**: 计划 +5, 实际 +4 —— school_commentary 槽位
> 因 GAP-02（中州派 provenance 不可核实）按准入策略**未生产**（不虚构）。

---

## 1. Executive Summary

Phase 7.1.3 建立 Reference ↔ Claim ↔ Node/Relation 可追溯闭环：新增
4 条引用（经典 ×2、现代 ×1、口传 ×1），全部来自已登记 Tier 1/3 来源且
provenance 可核实；新增 `ZIWEI_REFERENCE_CLAIM_MAPPING.md` 形成
"Corpus 内容 → 原始来源" 审计链。GAP-02 明确处理为 **REMAINS OPEN**
（不可核实 → not_authoritative, 不虚构、不补全）。GAP-09 未触及。

## 2. 新增 References 清单（4 条）

| # | Reference ID | ref_type | target | provenance | 状态 |
|---|--------------|----------|--------|------------|------|
| 1 | ref:classic:ziwei_quanshu_tianfu | classic_text | kn:main_star:tianfu | 全书·星曜总论·天府篇, 罗洪先辑 | verified |
| 2 | ref:classic:ziwei_quanshu_guanlu | classic_text | kn:palace:guanlu | 全书·十二宫释义·官禄宫 | verified |
| 3 | ref:modern:iztro_tanlang_placement | modern_interpretation | kn:main_star:tanlang | iztro（SylarLong, MIT, github.com/SylarLong/iztro） | verified |
| 4 | ref:oral:riyue_fanbei | oral_tradition | rel:chong:taiyang_taiyin | 全书·星曜总论（日月反背口诀摘要, 契约推导交叉验证） | verified |

> school_commentary（计划 1 条）: 中州派 provenance 不可核实 → **未生产**
> （准入策略: 不可核实来源不得作为正式 Reference; 关联 GAP-02）。

## 3. GAP-02 处理结果（Task 3）

| 项 | 结果 |
|----|------|
| 核实尝试 | Source Registry + 公开来源检索: 中州派讲义（王亭之）无授权数字版、版次/出版社信息无法确认 |
| 处置 | **REMAINS OPEN**; 不推测、不补全、不降级混入 |
| 既有 Pilot 引用 | ref:school:zhongzhou_minggong 标记 **not_authoritative**（Pilot 历史保留, 不作为正式依据; 映射表 §1 明确） |
| Corpus 影响 | school_commentary 正式槽位空缺 1 条（覆盖矩阵如实标记） |

## 4. Reference ↔ Claim 映射（Task 4）

详见 `ZIWEI_REFERENCE_CLAIM_MAPPING.md`:

- 7 条 Reference 全部有明确支持对象（target_id 存在性由 validate.py 强制）;
- 证据级别: primary（经典原文）/ secondary（流派注释）/ reference（现代/口传交叉）;
- 未逐条建 ref 的节点以 node 内 source 字段（primary）追溯（机制不变, 数量可扩）。

## 5. 最终 Corpus 统计

| 类别 | 数量 |
|------|------|
| nodes | **41**（不变） |
| relations | **18**（不变） |
| references | **7**（Pilot 3 + 新增 4; 1 槽位空缺） |

## 6. Pipeline 运行结果

```
$ uv run python knowledge/pipeline.py
corpus written: .../knowledge/ziwei_corpus.json (41 nodes, 18 relations, 7 references)
sha256: 7b6be437...

$ uv run python knowledge/validate.py
VALIDATION PASSED: all corpus entries conform to KB-001~020

确定性: 双重运行 SHA-256 一致 ✅（KB-020）
```

## 7. 回归测试结果

| 套件 | 结果 |
|------|------|
| `tests/test_knowledge_pipeline.py` | 10/10 PASS |
| 全量 pytest | **599/599 PASS**（无回归） |
| ruff check / format --check | 通过 |

## 8. GAP 状态

| GAP | 状态 |
|-----|------|
| GAP-02 | **REMAINS OPEN**（明确处理, 见 §3） |
| GAP-09 | 未触及（保持 OPEN, 本 Sprint 不处理） |
| 新增 | 无（school 空缺并入 GAP-02） |

## 9. 零触碰验证

| 检查 | 结果 |
|------|------|
| `git diff -- src/` / `docs/ziwei/` / KB 规范 / CAPABILITY_LIFECYCLE | ✅ 全空 |
| 新 node_type / relation_type / ref_type | ✅ 未新增 |
| LLM / RAG / 网络爬虫 | ✅ 未引入 |
| 41 节点 / 18 关系 / Pilot 数据 | ✅ 未修改（仅新增 refs 文件 + 治理文档） |

## 10. Phase 7.1.4（Extended Nodes）入口条件声明

1. References 7/7 完成, 映射链可审计 ✅
2. Provenance 状态 AUDITED（GAP-02 REMAINS OPEN / GAP-09 OPEN）✅
3. **待人工决策项**（进入 7.1.4 前）:
   - a) GAP-09（xing/hai）: 7.1.4 将创建地支节点 → 建议按 Build Plan 以
     地支三刑/六害/六冲落地（补齐关系缺口 6 条）;
   - b) GAP-02: 维持 OPEN（可核实来源出现前不强行处理）;
   - c) GAP-01（紫微斗数全集）: 7.1.4 扩展来源时再评估。
4. 7.1.4 范围（Build Plan）: 干支节点 22（heavenly_stem 10 + earthly_branch 12）
   + shen_sha/auxiliary_star 首批（来源确认后）。

---

**本 Sprint 停止。** 不进入 7.1.4; 不解决 GAP-09; 不引入 LLM/RAG;
不修改任何冻结规范。等待人工 Evidence Review 与授权。
