# Ziwei Corpus Admission Policy（知识准入策略）

> **Sprint**: Phase 7.1.0 — Corpus Scope & Source Freeze
> **日期**: 2026-08-13
> **状态**: **FROZEN**
> **适用**: 一切进入正式 Ziwei Corpus 的节点/关系/引用（含 Pilot 迁移与新增）。

---

## 1. 必须满足（六项准入条件）

| # | 条件 | 验收方式 |
|---|------|----------|
| 1 | **Schema validity** | 符合 KB-001~020（`reference/knowledge.py` 模型解析 + `validate.py` 校验通过） |
| 2 | **Semantic validity** | 概念明确、无歧义；`interpretation` 描述可独立理解；不依赖上下文推测 |
| 3 | **Provenance** | 每条目 `source.text`（典籍/著作名）非空；引用条目 `passage` 可回溯（chapter/page） |
| 4 | **Source attribution** | 来源必须先登记于 `ZIWEI_SOURCE_REGISTRY.md`（或 sources/*.yaml）；Tier 4 禁用为唯一依据 |
| 5 | **Deterministic serialization** | `pipeline.py` 双重运行 JSON 逐字节一致（KB-020） |
| 6 | **Conflict handling** | 多流派分歧 → `SchoolView`（node）/ `evidence` 多源（relation）保留差异，不静默合并 |

## 2. 禁止

| 禁止项 | 说明 |
|--------|------|
| 无来源"默认接受" | 每个条目必须有显式 provenance 引用 |
| 静默合并冲突知识 | 冲突必须显式（SchoolView / evidence / GAP 记录） |
| LLM 生成内容入 Corpus | 未经人工审查的生成内容禁止入库（Pipeline 亦无 LLM） |
| 网络爬虫自动采集 | 禁止自动采集入库；来源须人工登记审查 |
| 修改冻结规范以适应数据 | Schema 缺口 → GAP 记录（不修改 KB-001~020） |

## 3. 冲突处理

1. **多流派分歧**（星曜赋性/格局/神煞等）:
   - 节点: 主 `interpretation` 取共识部分 + `schools[]`（SchoolView）逐派保留差异
   - 关系: `evidence[]` 多源并列, 权重按来源 credibility
2. **冻结规范已明确规定**（如 Ziwei Contract BC-011 定局、BC-012 廉贞 -8）:
   - 以规范为准, 来源作为 provenance（`rel:he:*` 已示范: source 引契约条款）
3. **分歧无法消解且无规范依据**: 条目不进入正式 Corpus, 记 GAP
   （`ZIWEI_CORPUS_GAPS.md`）

## 4. 准入流程

```text
候选条目（来源已登记）
   ↓ 1. Schema 校验（pipeline/validate）
   ↓ 2. 语义审查（人工 Evidence Review）
   ↓ 3. Provenance/Attribution 核对
   ↓ 4. 冲突处理（SchoolView/evidence/GAP）
   ↓ 5. 确定性验证（双重运行一致）
   ↓ 6. 进入正式 Corpus（本轮 Scope 内）
```

## 5. 与 Pilot 的关系

- Pilot 数据（Phase 7.0, 20/12/3）为**历史产物**, 不直接修改;
  按 `ZIWEI_CORPUS_PILOT_AUDIT.md` 处置: 符合 Scope → 第一波保留
  （随 7.1.1 正式化时并入, 内容不变仅流程走查）; 不符 → 迁移/废弃。
