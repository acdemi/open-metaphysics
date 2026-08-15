# ACP-SCHEMA-001 — earthly_branch Schema Admission Gate（门 A 裁定记录）

> **Sprint**: Phase 7.1.4A — Schema/Ontology Admission Gate
> **日期**: 2026-08-13
> **状态**: **NOT REQUIRED（无需 ACP）** —— 门 A 裁定: `earthly_branch`
> **已在冻结 Schema 中注册**; 本文件为 Gate 审计记录, 非变更请求。
> **性质**: 不修改任何冻结规范, 不生产任何数据。

---

## 1. Change ID

| 项 | 值 |
|----|-----|
| ACP ID | ACP-SCHEMA-001（原拟: 新增 earthly_branch） |
| 日期 | 2026-08-13 |
| 状态 | **WITHDRAWN AS UNNECESSARY**（前提不成立, 见 §4） |
| 性质 | 门 A（Schema Admission）审计记录 |

## 2. 原定变更类型

Schema Change: 在 KB-002 node_type 枚举中新增 `earthly_branch`（20 → 21）。

## 3. 变更描述（原拟）

在冻结 KB-002 枚举中增加 `earthly_branch` 值。

## 4. ⚠️ 审计发现（前提不成立）

**冻结规范已包含 `earthly_branch`**:

| 权威位置 | 证据 |
|----------|------|
| `docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md` KB-002 | 20 种类型清单第 4 位: `heavenly_stem, earthly_branch, palace, main_star, ...` |
| `reference/knowledge.py` NodeType（规范性模型） | `EARTHLY_BRANCH = "earthly_branch"` |
| `reference/contracts/knowledge_contract.json` | `"earthly_branch"`（契约 JSON） |

**任务书前提与冻结规范不符**: 任务书所列 20 类型清单
（`gans / zodiac / spirit / luck / transformation / school / author / classic_text /
concept / relation_type / method / example / yin_yang` 等）**不存在于冻结 KB-002**
—— 该清单为早期设计示例（与 Phase 7.0/7.1.0 任务书同源笔误）。
冻结枚举实际为（20 种, 含 earthly_branch）:

```
wuxing, ten_god, heavenly_stem, earthly_branch, palace, main_star,
auxiliary_star, shen_sha, pattern, career, personality, marriage,
health, wealth, annual_fortune, major_luck, yong_shen, xi_shen,
ji_shen, tiao_hou
```

**结论**: 无 "gans 覆盖不全" / "zodiac 不等价" 问题 —— 这些类型本就不在
冻结枚举中; `earthly_branch` 作为**天干-地支体系**的既有成员自 Phase 6B
起已注册。**新增枚举 = 重复添加, 不合法, 也无必要。**

## 5. 门 A 裁定

| 检查 | 结果 |
|------|------|
| earthly_branch 是否允许进入 ontology | ✅ **已允许**（冻结 KB-002 注册, 无需任何变更） |
| 是否需要 Schema Change / ACP | ❌ **不需要**（枚举已存在） |
| 是否修改任何冻结规范 | ❌ 不修改（本记录不触碰 KB-002） |

> 三个门控保持分离（门 A 已天然通过）:
> - 门 A Schema Admission: **PASS（已注册, 无操作）**
> - 门 B Corpus Production（12 地支节点）: 未启动（7.1.4B, 待授权）
> - 门 C Relation Admission（xing/hai 的 Tier 1 证据）: 未启动（GAP-09 关联, 待评估）

## 6. 语义理由（记录, 供门 B/C 引用）

- 地支（子丑寅卯辰巳午未申酉戌亥）为数术基础概念, 与天干构成干支体系;
  冻结枚举以 `heavenly_stem` / `earthly_branch` 对称命名, 语义不相交。
- 12 地支节点 ID 预案: `kn:earthly_branch:zi, chou, yin, mao, chen, si, wu,
  wei, shen, you, xu, hai`（符合 KB-001 ID 模式）。

## 7. 向后兼容性 / 影响评估 / 迁移

全部 **N/A**（无变更发生）:
- 41 节点 / 18 关系 / 7 引用零影响
- validate.py / pipeline.py / 测试零影响
- Capability / Reference / Production 零影响

## 8. 非目标（显式）

- ❌ 本记录不包含 12 地支节点生产（门 B, 7.1.4B）
- ❌ 本记录不包含 xing/hai 关系生产（门 C）
- ❌ 本记录不扩展其他 node_type / relation_type / ref_type
- ❌ 本记录不修改 KB-001~020

## 9. 后续路径（等待人工 Review）

1. 认可本裁定后: GAP-09 的 **Schema 阻塞项移除**（原本误判）;
   GAP-09 剩余阻塞 = 门 C（xing/hai 的 Tier 1 证据评估）与 门 B（生产授权）。
2. 若人工不认可本裁定（坚持走 ACP 流程验证）: 可提交"确认性 ACP"
   （Confirmatory ACP, 零变更）—— 本记录可作为其背景证据。
