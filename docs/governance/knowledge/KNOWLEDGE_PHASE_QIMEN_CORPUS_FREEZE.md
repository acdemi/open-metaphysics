# Qimen Corpus Freeze v1.0.0（有界冻结记录·已批准）

> **日期**: 2026-10-24 · **分支**: `work/knowledge/qimen-verbatim`
> **批准**: 用户 2026-10-24 批准有界冻结（接受 5 条摘要边界）
> **评审**: `QIMEN_CORPUS_FREEZE_REVIEW.md` · **证据**: `KNOWLEDGE_H6_EVIDENCE_DOSSIER.md`

---

## 1. 冻结声明

| 项 | 值 |
|----|----|
| 冻结产物 | `knowledge/qimen_corpus.json` |
| 版本 | **`qimen_corpus:v1.0.0`（bounded evidence）** |
| digest (SHA-256) | `ffeb3319fcd8e8b01b1834c8b174587814cf2d4f5abd911fcaa06118f72d2032` |
| 计数 | **47 nodes / 60 relations / 15 references** |
| 规范输入 | `knowledge/corpus/qimen/**` |
| 来源登记 | `source_qimen_01`（統宗 oldid 1378608）、`source_qimen_02`（煙波 revid 1336835） |
| 生成器 | `knowledge/pipeline.py`（确定性；LF 输出） |
| 生效 | 本记录提交后 |

## 2. 证据边界（冻结基线）

| 级别 | 数量 | 引用 |
|------|------|------|
| A. revision-pinned 逐字核验 | 10/15 | jiugong、bamen、bamen_suozhu、jiuxing_suozhu、bashen、bashen_leishen、yangdun、yindun、yanbo_yinyang、liuyi |
| B. 书级/章节级摘要 | 5/15 | jiuxing、zhifu、zhishi、sanqi、xunshou_kongwang |

B 级不宣称逐字；与 engine 表一致性由语料测试锁定。

## 3. 变更流程

任何 node/relation/reference 的新增、修改、删除须走 corpus 级审查：
提案 → 证据（逐字或摘要边界说明）→ pipeline/validate/双跑/回归 → 人工批准
→ 版本递增 + 本记录更新。

## 4. 验证回执（2026-10-24）

| 检查 | 结果 |
|------|------|
| pipeline 双跑 digest | 一致 **`ffeb3319…`** |
| `validate.py` | `VALIDATION PASSED` |
| 定向测试 | `tests/test_qimen_knowledge_corpus.py` **31 passed** |
| 其他域 | Ziwei/Liuyao/BaZi 冻结件未变 |
