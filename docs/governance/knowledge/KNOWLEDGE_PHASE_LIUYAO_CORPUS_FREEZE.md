# Liuyao Corpus Freeze v1.0.0（冻结记录·已批准）

> **日期**: 2026-10-24 · **分支**: `work/knowledge/bazi-liuyao-freeze-review`
> **批准**: 用户 2026-10-24 选择“只冻结 Liuyao”；评审见 `LIUYAO_CORPUS_FREEZE_REVIEW.md`
> **依据**: `KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md` §2 变更流程（corpus 级审查）

---

## 1. 冻结声明

| 项 | 值 |
|----|----|
| 冻结产物 | `knowledge/liuyao_corpus.json` |
| 版本 | **`liuyao_corpus:v1.0.0`** |
| digest (SHA-256) | `3a09a08eccd72a24363b64fa28fee4d01f80a4bfae8d4a366ae75360e2c8a53b` |
| 计数 | **61 nodes / 66 relations / 41 references** |
| 规范输入 | `knowledge/corpus/liuyao/{nodes,relations,references}/*.yaml`（与产物同源、同提交） |
| 来源登记 | `knowledge/sources/liuyao/source_liuyao_01.yaml`（主页 revid 2572918 + 24 子页 revid/SHA-256） |
| 证据级别 | `revision_pinned_verbatim_verified`（逐章逐字核验） |
| 生成器 | `knowledge/pipeline.py`（确定性；LF 输出） |
| 生效 | 本记录提交后 |

**覆盖（冻结基线）**

| 类别 | 分布 |
|------|------|
| node_type | wuxing 5 / palace 9 / liuqin 6 / liushen 7 / yongshen 3 / pattern 31 |
| relation_type | sheng/ke/shuyu/duiying/roles/structure 家族共 66 条 |
| ref_type | classic_text 41 |

## 2. 范围与变更流程

**冻结对象**：上述产物 + 规范输入 YAML + `source_liuyao_01` 的 revision pin。

**变更流程**：任何 node/relation/reference 的新增、修改、删除须走 corpus 级审查：
提案（范围+来源）→ 证据逐字核验（revision-pinned 原文子串回执）→
pipeline/validate/确定性双跑/回归测试 → 人工批准 → 版本递增 + 本记录更新。

## 3. 证据基线

- 24 个已核子页 + 主页卷之二第二十七~三十二章；passage 为原文字符串（仅去维基标记与空白）。
- 8 条转录异文逐条登记（辰在內→艮、天地觀→风地观、元武/滕蛇/靑龍、𨿽、原劍按语、
  反伏/伏呤、進退章标题）；语料按 engine 用名收录，引文保留原字。
- 抓取件保存在仓库外；如需第三方复核可在 H6 授权窗口内按 revid/SHA-256 重放。

## 4. 随冻结载入的开放项（不得静默丢弃）

| 项 | 状态 | 含义 |
|----|------|------|
| GAP-LIUYAO-01~04 | OPEN | 六亲/结构法则/元神/仇神无专用 node_type（承载方式见 `knowledge/README.md` §7） |
| GAP-LIUYAO-05 | 不生产 | 互卦无定义性原文（H5） |
| GAP-LIUYAO-06 | 延后 | 星煞章未收录（schema 归属/价值密度未定） |
| relation 级引用覆盖 | 1/66 | 关系条目以 relation `evidence`/`source` 归属；非阻塞 |

## 5. 验证回执（2026-10-24）

| 检查 | 结果 |
|------|------|
| pipeline 双跑 digest | 一致 **`3a09a08e…`** |
| 文件字节哈希 == 登记 digest | ✅ |
| `validate.py` | `VALIDATION PASSED`（KB-001~020） |
| 定向测试 | `tests/test_liuyao_knowledge_corpus.py` **79 passed** |
| BaZi 处置 | 推迟冻结（`BAZI_CORPUS_FREEZE_READINESS.md`；待 H6 证据扩展） |
