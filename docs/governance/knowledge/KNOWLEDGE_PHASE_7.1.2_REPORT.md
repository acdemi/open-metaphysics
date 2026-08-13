# Knowledge Phase 7.1.2 — Ziwei Relations Production Report

> **Sprint**: Phase 7.1.2 — Relations Production（受控语料生产）
> **日期**: 2026-08-13
> **依据**: Build Plan 7.1.2（范围依据）+ Admission Policy + 冻结契约 BC-012
> **结果**: **+6 关系**（he +3 / chong +3）; 关系总数 12 → **18**
> ⚠️ **范围偏差（诚实声明）**: Build Plan 目标 +12（含 xing 3 / hai 3）,
> 实际 +6 —— 候选经**契约数学验证**后 6 条不成立/无来源, 按
> "禁止制造关系"原则**拒绝**（GAP-09）。

---

## 1. Executive Summary

Phase 7.1.2 生产 6 条新关系（he 同宫 ×3 / chong 六宫相对 ×3），
全部关系**由冻结契约 BC-012 偏移表数学推导验证**（脚本核验，非杜撰），
端点均为既有 41 节点。任务书 9 条候选关系中 6 条经验证**不成立**
（如"贪狼破军合"——两星永不同宫；"天梁巨门刑/太阳廉贞害"——恒不相对），
按硬约束"禁止为了填数而制造关系"拒绝并登记 GAP-09。
xing（刑）/ hai（害）在星曜层面无 Tier 1 经典依据（冲刑害为地支关系），
缺口 6 条留待 7.1.4 地支节点落地或用户授权改型。

## 2. 新增关系清单（6 条）

| # | ID | type | source → target | 数学验证 | provenance |
|---|----|------|-----------------|----------|------------|
| 1 | rel:he:ziwei_tanlang | he | kn:main_star:ziwei → kn:main_star:tanlang | 同宫 zw∈{1,7}（卯酉） | 契约 BC-012 推导 + 全书星曜总论 |
| 2 | rel:he:taiyang_taiyin | he | kn:main_star:taiyang → kn:main_star:taiyin | 同宫 zw∈{2,8}（丑未, 日月同宫） | 同上 |
| 3 | rel:he:wuqu_pojun | he | kn:main_star:wuqu → kn:main_star:pojun | 同宫 zw∈{1,7}（巳亥） | 同上 |
| 4 | rel:chong:tianfu_qisha | chong | kn:main_star:tianfu → kn:main_star:qisha | **恒**六宫相对（全部 zw） | 同上 |
| 5 | rel:chong:tianxiang_pojun | chong | kn:main_star:tianxiang → kn:main_star:pojun | **恒**六宫相对（全部 zw） | 同上 |
| 6 | rel:chong:taiyang_taiyin | chong | kn:main_star:taiyang → kn:main_star:taiyin | 六宫相对 zw∈{5,11}（日月反背） | 同上 |

> 每条含 `evidence`（描述 + 全书来源）与 `conditions`（条件化关系的
> `ziwei_index` 触发条件），direction=undirected, weight=1.0。
> 文件名: `knowledge/corpus/ziwei/relations/he_chong.yaml`。

## 3. 候选验证记录（任务书 9 条 + 自检）

| 候选 | 验证结果 | 处置 |
|------|----------|------|
| 紫微-he-天府 / 廉贞-he-天府 | Pilot 已存在（2 条） | 不重复 |
| 贪狼-he-破军 | ❌ **永不同宫**（天府系偏移 +2 vs +10） | 拒绝（GAP-09） |
| 紫微-chong-破军 | ❌ 仅条件相对（zw∈{2,8}）, 无冲语义依据 | 拒绝 |
| 天府-chong-七杀 | ✅ **恒六宫相对** | 采纳（#4） |
| 太阳-chong-太阴 | ✅ 条件六宫相对（zw∈{5,11}, 反背结构） | 采纳（#6） |
| 武曲-xing-七杀 | ❌ 仅条件同宫, "金金刑"无经典依据 | 拒绝 |
| 天梁-xing-巨门 | ❌ 恒不同宫 | 拒绝 |
| 天机-xing-天梁 | ❌ 条件同宫, 刑无依据 | 拒绝 |
| 太阳-hai-廉贞 / 天府-hai-太阴 / 贪狼-hai-七杀 | ❌ 恒不相对 / 无害语义依据 | 拒绝（GAP-09） |

> 补充自检采纳: 天相-破军恒六宫相对（#5）; 紫微贪狼/武曲破军同宫（#1/#3）。

## 4. 端点完整性确认

- 6 条新关系全部端点 ∈ 41 节点（main_star ×12 使用, palace/ten_god/wuxing 未使用）。
- `validate.py` 端点存在性检查 PASS（12 旧 + 6 新 = 18 全部通过）。

## 5. 最终统计

| 类别 | 数量 |
|------|------|
| nodes | **41**（不变） |
| relations | **18**（sheng 5 / ke 5 / he 5 / chong 3） |
| references | 3（不变） |

## 6. Pipeline 运行结果

```
$ uv run python knowledge/pipeline.py
corpus written: .../knowledge/ziwei_corpus.json (41 nodes, 18 relations, 3 references)
sha256: a166b929...

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

## 8. 遇到的 GAP（记录，不解决）

| GAP | 说明 | 状态 |
|-----|------|------|
| GAP-09（新增） | 星曜级 xing/hai 无 Tier 1 来源（冲刑害为地支关系; 候选 6 条数学不成立）; 关系目标 24 → 18 | 记录; 待 7.1.4 地支节点或授权改型 |
| GAP-02 | 中州派 provenance（未触碰, 维持） | 记录 |

## 9. 零触碰验证

| 检查 | 结果 |
|------|------|
| `git diff -- src/` / `docs/ziwei/` / KB 规范 / CAPABILITY_LIFECYCLE | ✅ 全空 |
| 新 node_type / relation_type / ref_type | ✅ 未新增（he/chong 为既有枚举） |
| LLM / RAG / 网络 | ✅ 未引入 |
| GAP-02 | ✅ 未修改 |

## 10. Phase 7.1.3（References & Provenance）入口条件声明

1. 关系 18/18 完成并通过校验 ✅
2. Coverage Matrix / GAPS 已更新 ✅
3. **待人工决策项**（进入 7.1.3 前）:
   - a) xing/hai 缺口 6 条: 待 7.1.4（地支节点）或授权改用 `duiying`
     （对宫, 全书十二宫有坚实来源, 6 条宫对关系）;
   - b) 中州派 provenance（GAP-02）在 7.1.3 处理。
4. 7.1.3 范围（Build Plan）: references +5（classic +2 / school +1 /
   modern +1 / oral +1）+ yinyong/shuyu 关系随引用建立。

---

**本 Sprint 停止。** 不进入 7.1.3; 不扩展 shen_sha/pattern; 不引入 LLM/RAG;
不修改任何冻结规范。等待人工 Evidence Review 与授权。
