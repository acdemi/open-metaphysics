# ACP-KNOWLEDGE-001 — 知识语料 EOL 固定与跨平台 digest 复现性修复

> **Status**: **PROPOSED**（2026-10-24 · 待人工批准 · 未实施任何变更）
> **Date**: 2026-10-24
> **Domain**: Knowledge（语料冻结工件）
> **Approval required**: 是（H3 冻结工件 + Corpus 级变更流程）
> **Related**: `docs/governance/knowledge/KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md`、
> `docs/specification/RUNTIME_CONTRACT.md` 合并门、`ACP-REF-002`

---

## 1. 问题（实测证据）

1. **YAML 源未 EOL 固定**：`knowledge/sources/ziwei/*.yaml` 在 Windows 工作区为
   CRLF，且 `.gitattributes` 仅固定 `knowledge/**/*.json text eol=lf`，无 YAML 规则。
   实测 `git ls-files --eol`：Ziwei 三个 source YAML 为 `i/lf w/crlf`；
   BaZi/Qimen/Liuyao source YAML 已是 `w/lf`。

2. **digest 按原始字节计算**：`knowledge/pipeline.py:113-118` 对 source YAML
   原始字节做 SHA-256，`:146-156` 将语料 JSON 固定写为 LF。因此
   `metadata.source_digests` 与运行平台的 EOL 相关。

3. **Linux/LF 工作区会失败并改写冻结件**：`tests/test_bazi_knowledge_corpus.py:341-358`
   在 LF 源时先断言冻结 digest，随后调用 `_run_pipeline()`；pipeline 会以 LF
   源重算 digest 并**重写** `knowledge/ziwei_corpus.json`，导致
   `after == before` 失败且冻结工件被就地改写。CI
   `.github/workflows/test.yml:12,17` 在 `ubuntu-latest` 运行 `uv run pytest -q`，
   该路径必然触发。

4. **登记缺口**：Liuyao 全量 digest 无治理登记、无测试锚定；BaZi/Qimen 全量
   digest 仅存在于测试常量；`ziwei_corpus:v1.0.0` 的 `69d6e2a6…` 是 CRLF 基准，
   与 LF checkout 不兼容。

---

## 2. LF 模拟实测（只读审计时在临时副本完成）

将 YAML 转 LF 后运行 `knowledge/pipeline.py`（临时副本，未触碰仓库）：

| 项 | 当前冻结（CRLF 基准） | LF 基准（预期值） |
|----|----------------------|-------------------|
| `ziwei_corpus.json` digest | `69d6e2a6b2f82d58292bfd11847aa7d26e2cd75eabda8cdbbbb67d4f6cc5f73d` | **`93dba0673b8b0c45f083c1760465a08f2444275485c160bb2e1a02c23735257f`** |
| `source_01.yaml` digest | `40e82eca7d5fba395b87ab79a4938dfe438ade79e080c29c1773722702018597` | `8f18dccdfc45880da20a1e75ad7afa947668d8c37f8f3af01c0acfa682690079` |
| `source_02.yaml` digest | `5e6dcf1d7dfefc41ee6b9060be8a631295c0d9c478401fc6142191a2519770b3` | `186bed3e7f7254d9fd555a4d2489fe40d0d5893e12998975f5776f6443c4e367` |
| `source_03.yaml` digest | `16f7744d5e90cf59d2fc69076bce8efcc44d90cefe4c8e2d034493c4e84530ff` | `3fcb4c621e61bd265fa446475f147a5daadf8282d12c649078fcee087b0daa04` |
| `bazi_corpus.json` digest | `69b6edea…` | 不变 `69b6edeaab361ae7a27455c891acaaebeb260a5c17d0e067a1229c73542f8fcd` |
| `qimen_corpus.json` digest | `40de5c45…` | 不变 `40de5c455605e82a3031e4255f01bdb76e8ae7ba073a87e072239bb9adba3b3d` |
| `liuyao_corpus.json` digest | `52efbff5…` | 不变 `52efbff57c31e4d2a5bf8e79c7ed5eee948477d9b71ecbcb7a0fdb1b5e4c755a` |

内容对账：Ziwei 的 `nodes` / `relations` / `references` / `counts` 全部逐对象相等，
**零内容变化；仅 `metadata.source_digests` 与由此产生的文件 digest 变化**。

---

## 3. 请求批准事项（D1-D4）

1. **D1**：`.gitattributes` 增加 `knowledge/**/*.yaml text eol=lf`，把
   `sources/**` 与 `corpus/**` 的 YAML 一并固定为规范 LF。
2. **D2**：在 LF 工作区重新生成 `knowledge/ziwei_corpus.json`；接受
   `metadata.source_digests` 变为 §2 的三个 LF 值，并接受新 digest
   `93dba067…`。**版本处理**：内容零变化，建议 `ziwei_corpus:v1.0.0 → v1.0.1`
   （兼容性 metadata 修订）或记为 v1.0.0 勘误；最终由人工在批准时裁定。
3. **D3**：修复 `tests/test_bazi_knowledge_corpus.py:341-358` 的门控方向
   （对齐 `tests/test_qimen_knowledge_corpus.py:432-439`），并以 LF 基准更新
   四域 digest 常量与治理登记：Ziwei 新值、BaZi/Qimen 补文档、Liuyao 新增锚定。
4. **D4**：同步状态指针：`knowledge/README.md`、`CAPABILITY_STATUS.md`、
   `PROJECT_STATUS.md` 的 digest/版本/候选状态记录；把本 ACP 结果登记入
   ACP README 与 `KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md`。

批准语：`批准 ACP-KNOWLEDGE-001（D1-D4）。`

---

## 4. 批准后实施步骤

1. 修改 `.gitattributes`；`git add --renormalize knowledge` 并复核
   `git ls-files --eol knowledge` 全部为 `w/lf`。
2. LF 工作区运行 `knowledge/pipeline.py` 构建四域；双跑确认 digest 稳定。
3. 更新 `KNOWLEDGE_PHASE_7.1.6_CORPUS_FREEZE.md`（digest 表、验证回执）与
   四域 digest 常量/测试锚定；修正 `test_bazi_knowledge_corpus.py` 门控。
4. 在 LF 工作区与 Windows 工作区分别运行全量 pytest、`ruff`、
   `knowledge/validate.py`。
5. 更新 `knowledge/README.md`、`CAPABILITY_STATUS.md`、`PROJECT_STATUS.md`。
6. 取得 H7 合并授权后 `git merge --no-ff`；合并后归档 ≤15 行。

---

## 5. 验证矩阵（批准后必须回执）

| 检查 | 预期 |
|------|------|
| `knowledge/pipeline.py` 双跑 | Ziwei digest 稳定等于 `93dba067…` |
| 内容对账 | Ziwei nodes/relations/references 与 v1.0.0 逐对象相等 |
| `knowledge/validate.py` | `VALIDATION PASSED` |
| LF 工作区全量 pytest | 1026 collected / 1024 passed + 2 skipped；冻结件不被改写 |
| Windows 工作区全量 pytest | 同上 |
| `ruff check src reference tests tools` | PASS |
| digest 登记 | Ziwei 新值 + BaZi/Qimen/Liuyao 全量值均入治理文档并被测试锚定 |

---

## 6. 兼容性与风险

- **内容零变化**：节点/关系/引用与计数不变，RAG/Explain/API 行为不变。
- **digest 变化**：任何外部或文档引用 `69d6e2a6…` 的 pin 需同步更新；
  这是本 ACP 的预期影响。
- **版本引用**：若 D2 定为 `v1.0.1`，需更新测试/文档中的 `ziwei_corpus:v1.0.0`
  字样；若定为勘误，则保留 v1.0.0 但登记新 digest。
- **窗口纪律**：不改动 `docs/specification/`、`reference/` 行为实现、其他域。

---

## 7. 回滚

若本 ACP 被否决或撤销：恢复 `.gitattributes` 原状与
`knowledge/ziwei_corpus.json` 原字节（`69d6e2a6…`），恢复测试门控；Liuyao
digest 登记可独立保留（候选语料，不涉冻结变更）。
