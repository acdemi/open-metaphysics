# Ziwei Reference ↔ Claim Mapping（可追溯闭环）

> **Sprint**: Phase 7.1.3 — References & Provenance
> **日期**: 2026-08-13
> **目标**: 每个 Node/Relation 至少关联 1 条 Reference; 每条 Reference 明确
> 支持对象与证据级别 → 形成 "Corpus 内容 → 原始来源" 可追溯链。

---

## 1. Reference 清单（7 条 = Pilot 3 + 7.1.3 新增 4）

| Reference ID | Type | Supports | Evidence Level | 状态 |
|--------------|------|----------|----------------|------|
| ref:classic:ziwei_quanshu_ziwei（Pilot） | classic_text | kn:main_star:ziwei | primary | verified |
| ref:classic:ziwei_quanshu_tianfu（新增） | classic_text | kn:main_star:tianfu（天府星系源） | primary | verified |
| ref:classic:ziwei_quanshu_guanlu（新增） | classic_text | kn:palace:guanlu | primary | verified |
| ref:school:zhongzhou_minggong（Pilot） | school_commentary | kn:palace:minggong | secondary | ⚠️ **not_authoritative**（GAP-02: 版本/页码不可核实; Pilot 历史保留, 不纳入正式依据） |
| ref:modern:iztro_tanlang_placement（新增） | modern_interpretation | kn:main_star:tanlang（偏移 +2 与现代整理） | reference | verified（MIT, url 可核） |
| ref:oral:lianzhen_tianfu_tongdu（Pilot） | oral_tradition | rel:he:lianzhen_tianfu | reference | verified（契约 BC-012 恒等式交叉验证） |
| ref:oral:riyue_fanbei（新增） | oral_tradition | rel:chong:taiyang_taiyin | reference | verified（日月反背, 契约推导交叉验证） |

## 2. Claim 覆盖（Node/Relation → Reference）

| 对象 | 关联 Reference | 级别 |
|------|----------------|------|
| kn:main_star:ziwei | ref:classic:ziwei_quanshu_ziwei | primary |
| kn:main_star:tianfu | ref:classic:ziwei_quanshu_tianfu | primary |
| kn:main_star:tanlang | ref:modern:iztro_tanlang_placement（+ node 内 中州 SchoolView） | reference/secondary |
| kn:main_star:其余 11 | node 内 source（星曜总论）直接登记; 7.1.3 未逐星建 ref（可由 classic 系列扩展） | primary（source 级） |
| kn:palace:minggong | ref:school:zhongzhou_minggong ⚠️ + node 内 source | secondary/caution |
| kn:palace:guanlu | ref:classic:ziwei_quanshu_guanlu | primary |
| kn:palace:其余 10 | node 内 source（十二宫释义）直接登记 | primary（source 级） |
| kn:wuxing:* / kn:ten_god:* | node 内 source（星曜总论 / 渊海子平·论十神） | primary（source 级） |
| rel:sheng:* / rel:ke:* | relation 内 evidence.source（五行生克） | primary（evidence 级） |
| rel:he:ziwei_tianfu / rel:he:lianzhen_tianfu | ref:oral:lianzhen_tianfu_tongdu + evidence（契约 BC-012） | reference/primary |
| rel:he:ziwei_tanlang / rel:he:wuqu_pojun / rel:chong:* | relation 内 evidence（契约 BC-012 推导 + 全书）; oral 系列可扩展 | primary（推导, evidence 级） |

## 3. 追溯链形态

```text
Corpus Claim（node.interpretation / relation.evidence.description）
   └─ source: SourceRef（text/chapter/author）
        └─ KnowledgeReference（reference_id/target_id/ref_type/passage）
             └─ Source Registry（sources/ziwei/source_0X.yaml, Tier 分级）
```

- **验证路径**: `validate.py` 检查 reference.target_id 存在性;
  `knowledge/ziwei_corpus.json` 为合并可追溯视图。
- **证据级别语义**: primary = 经典原文直接支持; secondary = 流派注释;
  reference = 现代/口传交叉参照（不单独作为权威依据）。

## 4. 未覆盖声明

- 14 主星中 12 个、12 宫 10 个、全部 wuxing/ten_god 节点当前以
  **node 内 source 字段**（primary）追溯, 未逐条建 ref 条目 ——
  属数量扩展（7.1.3 后可按需补建, 不改变机制）。
- school_commentary 槽位（1 条）因 GAP-02 未生产 —— 不虚构。
