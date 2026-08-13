# Knowledge Sprint 0 — Corpus Pipeline Validation Report

> **Sprint**: Phase 7.0 — Knowledge Layer Infrastructure（Pipeline Validation）
> **日期**: 2026-08-13
> **领域**: Knowledge Layer（试点: Ziwei）
> **性质**: Pipeline 验证 Sprint（非知识生产 Sprint）
> **前置**: Qimen/BaZi/Ziwei = Integration Ready; Knowledge Layer 架构冻结
> （KB-001~020 + `01_knowledge_layer_architecture.md`）

---

## 1. Executive Summary

Knowledge Layer 语料生产 Pipeline **验证通过**：

给定冻结的 KB 规范（KB-001~020，规范性实现 `reference/knowledge.py`），
从 2 个试点来源（古籍元数据）经**确定性转换**生成符合规范的 YAML 语料
（20 节点 / 12 关系 / 3 引用），经 Schema 校验（KB-001~020）、
可重放（双重运行逐字节一致）、可审计（来源 digest + SHA-256 checksum）。
Pipeline 可工作 → 全量语料建设（Phase 7.1）具备入口条件。

**核心结论**: 从无到有的语料生产链路已验证可行；剩余工作为**规模生产**，
非**基础设施**。

---

## 2. Pipeline 验证结果

| 验证项 | 结果 | 证据 |
|--------|------|------|
| `pipeline.py` 可运行 | ✅ | `python knowledge/pipeline.py` → corpus written（20/12/3）+ sha256 |
| Schema 校验 | ✅ | `validate.py` → VALIDATION PASSED（KB-001~020, reference/knowledge.py 模型） |
| 确定性（两次运行一致） | ✅ | `test_pipeline_deterministic` 逐字节一致 |
| 回归测试 | ✅ | `tests/test_knowledge_pipeline.py` 10/10 通过 |
| 全量测试 | ✅ | pytest 全量 599/599 全绿（589 + 10 新增） |
| lint | ✅ | `ruff check` / `ruff format --check` 通过 |
| 无网络/外部依赖 | ✅ | 纯本地 YAML → JSON 确定性转换（无 LLM/RAG/随机） |

---

## 3. 语料统计

| 类别 | 数量 | 覆盖类型 | 文件 |
|------|------|----------|------|
| KnowledgeNode | 20 | wuxing(5), main_star(5), palace(5), ten_god(5) | `corpus/ziwei/nodes/*.yaml` |
| KnowledgeRelation | 12 | sheng(5), ke(5), he(2) | `corpus/ziwei/relations/*.yaml` |
| KnowledgeReference | 3 | classic_text, school_commentary, oral_tradition | `corpus/ziwei/references/*.yaml` |
| 来源 | 2 | 《紫微斗数全书》《渊海子平》 | `sources/ziwei/source_0*.yaml` |

质量门控: 节点 ≥10 且 ≥3 类型 ✅ / 关系 ≥10 且 ≥3 类型 ✅ / 引用 ≥2 且 ≥2 类型 ✅ /
每条目 provenance 非空 ✅ / relation 端点 + reference 目标存在性校验 ✅ /
id 唯一性 ✅

---

## 4. 校验结果

`knowledge/validate.py` 输出: **VALIDATION PASSED**。

- 模型级（KB-001~003 / KR-001~003 / KREF-001~004）: 由规范性模型
  `reference/knowledge.py`（id pattern / 枚举 / weight∈[0,1] / extra=forbid）强制
- 跨引用完整性: rel 端点存在、ref 目标存在、无重复 id
- 来源完整性: 每个节点/关系/引用 `source.text` 非空

---

## 5. 确定性验证

- 双重运行输出 `knowledge/ziwei_corpus.json` **逐字节一致**（sort_keys=True,
  无时间戳/随机值）
- corpus metadata 内嵌 `source_digests`（每个来源文件 SHA-256）+
  pipeline 输出 checksum（sha256）—— 来源变更即可审计追踪

---

## 6. 对 Phase 7.1（全量语料建设）的入口条件声明

1. **Pipeline 已验证** ✅ —— 确定性、可重放、可校验
2. **Schema 校验链路就绪** ✅ —— 复用冻结规范层（reference/knowledge.py, 零新增实现）
3. **试点语料模型确认** ✅ —— 20 节点 / 12 关系 / 3 引用全量通过
4. **来源登记机制就绪** ✅ —— sources/*.yaml + digest 追踪
5. **Phase 7.1 待授权范围建议**: 全量 Ziwei 节点（星曜/宫位/四化/大限/流年
   边界内）+ 后续域（Qimen/BaZi）扩展须逐域授权；大规模语料生产不应
   改变 Pipeline（仅扩充 YAML 输入）

---

## 7. 验证记录

```
$ uv run python knowledge/pipeline.py
corpus written: .../knowledge/ziwei_corpus.json (20 nodes, 12 relations, 3 references)
sha256: 6ec7b8d1...

$ uv run python knowledge/validate.py
VALIDATION PASSED: all corpus entries conform to KB-001~020

$ uv run pytest tests/test_knowledge_pipeline.py -q
.......... [100%]                    # 10/10 PASS

$ uv run pytest
599 passed, 1 warning                # 589 + 10 新增

$ uv run ruff check / ruff format --check
All checks passed!
```

---

## 8. 边界门控（零触碰）

| 检查 | 结果 |
|------|------|
| `git diff -- src/` | ✅ 空（未修改任何生产代码） |
| `git diff -- docs/ziwei/` | ✅ 空（契约/向量/Reference 未动） |
| `git diff -- docs/governance/CAPABILITY_LIFECYCLE.md` | ✅ 空 |
| `git diff -- docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md` | ✅ 空（KB-001~020 未动） |
| `reference/` 新增实现 | ✅ 未创建（仅复用 reference/knowledge.py） |
| Ziwei 状态 | ✅ 保持 Integration Ready（未修改） |
| 新增文件 | `knowledge/`（8 文件）+ `tests/test_knowledge_pipeline.py` + `docs/governance/knowledge/KNOWLEDGE_SPRINT_0_REPORT.md` |

---

## 9. Knowledge Layer 状态更新

| 维度 | 之前 | 之后 |
|------|------|------|
| Architecture | FROZEN（KB-001~020） | FROZEN（未变） |
| Pipeline | 未验证 | **VALIDATED**（Phase 7.0） |
| Corpus | EMPTY | **PARTIAL**（Ziwei 试点, 20/12/3） |

> 状态指针更新于 `docs/governance/CAPABILITY_STATUS.md`（仅指针，不升级
> Knowledge Layer 为独立能力——Knowledge 不产生计算输出，属引用层）。

---

## 10. 停止声明

**本 Sprint 停止。** 等待人工 Evidence Review 与授权：

- ❌ 不进入大规模知识生产（Phase 7.1）
- ❌ 不将 Knowledge 接入 Ziwei 计算
- ❌ 不开发 RAG/LLM 集成
- ❌ 不扩展到 Qimen/BaZi 语料
