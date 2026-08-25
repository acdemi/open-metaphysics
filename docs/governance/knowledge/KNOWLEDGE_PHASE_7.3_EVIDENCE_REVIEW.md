# Knowledge Phase 7.3 Evidence Review

> **审查模式**: 审计 Sprint（REVIEW ONLY）
> **审查对象**: commit `193779d`（parent `058c286`, 2026-08-25 10:00:32 +0800）
> **审查日期**: 2026-08-25
> **审查分支**: `work/knowledge/phase73-evidence-review`
> **触发事由**: Phase 7.3 声明 Knowledge Production = 0，但 `knowledge/ziwei_corpus.json` 的 SHA-256 发生变化，需判定变化性质。

---

## 结论

```text
METADATA_ONLY — MERGE ELIGIBLE
```

`ziwei_corpus.json` 的 SHA 变化为**单一 metadata 字段更新**（source digest 登记值），
不包含任何节点、关系、引用或语义断言的修改。
Phase 7.3 声明与实际 diff 一致：**Knowledge Production = 0 成立**。
GAP-01 / GAP-12 / GAP-13 均保持 🟡 SOURCE_DISCOVERED，未关闭，无证据就绪状态提升。

附带发现一项**非阻塞文档缺陷 DEF-01**（GAP 编号交叉错标），建议后续文档修正，不影响本结论。

---

## 1. 审查范围与方法

- Diff 基准：`git diff 058c286 193779d -- knowledge/ziwei_corpus.json`
- 全量变更清单：`git show --stat 193779d`
- 后续污染检查：`git diff 193779d HEAD -- <audited paths>` 与路径限定 `git log`
- Digest 一致性：对 git blob 原始字节及其行尾变体分别计算 SHA-256，与 corpus 登记值比对
- 跨文件检查：`SOURCE_STATUS.md`、`ZIWEI_CORPUS_GAPS.md`、`KNOWLEDGE_PHASE_7.3_REPORT.md` @193779d 及当前 HEAD

## 2. Diff 分析（逐文件逐字段）

commit `193779d` 共触及 6 个文件：

| 文件 | 变化 | 性质 |
|------|------|------|
| `knowledge/ziwei_corpus.json` | **1 行**（+1/-1）：`metadata.source_digests["source_01.yaml"]`: `1dd6851e…` → `6c27dfda…` | registry metadata |
| `knowledge/sources/ziwei/source_01.yaml` | url: null → `https://zh.wikisource.org/wiki/紫微斗數全書`；新增 `acquisition_status: discovered_blocked`、`evidence_status: not_ready`、`blocker: webfetch_transport_error`（blob 826 → 944 字节） | provenance metadata |
| `docs/governance/knowledge/ZIWEI_CORPUS_GAPS.md` | GAP-01 / GAP-12 / GAP-13 三行状态列更新 | governance 文档 |
| `knowledge/sources/ziwei/SOURCE_STATUS.md` | 新增（80 行），来源发现状态记录 | governance 文档 |
| `docs/governance/knowledge/KNOWLEDGE_PHASE_7.3_REPORT.md` | 新增（180 行），Sprint 报告 | governance 文档 |
| `context/归档.md` | +60 行对话归档 | 归档记录 |

### corpus JSON 逐字段核对

- 变化字段仅 1 个：`metadata.source_digests["source_01.yaml"]`（blob `eab0861` → `1e1232c`）。
- `metadata.counts` 未变：nodes 63 / references 10 / relations 37（diff 中未出现该区块）。
- **无节点定义修改，无关系定义修改，无引用内容修改。**
- **无新增语义断言，无删除语义断言。**

## 3. 变化分类（按授权矩阵）

| 变化 | 矩阵类别 | 是否属于 Production |
|------|----------|---------------------|
| `source_digests["source_01.yaml"]` 更新 | corpus metadata / registry metadata（仅追踪登记值随源文件元数据同步） | **否** |
| source_01.yaml 的 url / acquisition_status / evidence_status / blocker | source URL / provenance metadata（来源发现登记，非知识内容） | **否** |
| GAPS 状态行 🟡 SOURCE_DISCOVERED | governance 记录（明确"未关闭"） | 否 |
| 新增知识节点/关系/引用 | （未发生） | — |
| 修改已有 assertion/relation/reference | （未发生） | — |

**Knowledge Production = 0 与实际 diff 一致。**

## 4. SHA 变化性质的技术确认（digest 一致性验证）

### 4.1 登记值可复现性

corpus 登记的 digest 并非 git blob（LF 存储）的原始哈希，而是**工作树 CRLF 内容**的哈希 ——
`pipeline.py` 第 49–52 行 `_source_digests()` 以 `p.read_bytes()` 直接读取工作树文件，
而 `.gitattributes` 使检出的 yaml 为 CRLF。验证结果：

| 对象 | sha256(LF blob 原始字节) | sha256(CRLF 归一化) | corpus 登记 digest | 匹配 |
|------|---------------------------|----------------------|--------------------|------|
| source_01.yaml @058c286（blob 826 B） | `ca1368ed29fdece…` | `1dd6851e4f4ad05…` | `1dd6851e4f4ad05…` | ✅ CRLF 变体 |
| source_01.yaml @193779d（blob 944 B） | `5fab6c2103f78237…` | `6c27dfda7b32c9b6…` | `6c27dfda7b32c9b6…` | ✅ CRLF 变体 |

即：**新旧两个登记值均精确对应各自时点源文件的真实内容**，digest 更新是忠实追踪，
不是篡改、也不是误写。

### 4.2 当前工作树一致性

- 当前工作树 `source_01.yaml` sha256 = `6c27dfda7b32c9b6…` = corpus 登记新值 ✅ 自洽
- 当前工作树 `knowledge/ziwei_corpus.json` sha256 = `96dad292e8a8073…`

### 4.3 193779d 之后无后续变化

- `git log 193779d..HEAD -- knowledge/ziwei_corpus.json knowledge/sources/ziwei docs/governance/knowledge/ZIWEI_CORPUS_GAPS.md` → **空**
- `git diff 193779d HEAD -- knowledge/ziwei_corpus.json` → **空**
- 后续提交 `4a0ac62`（消息含 "knowledge JSON EOL normalization"）实际只触及 `.gitattributes` 与 `docs/PROJECT_STATUS.md`，通过行尾策略生效，**未重写任何 knowledge JSON**，与本审计路径零冲突。

**结论：用户观察到的 corpus SHA-256 变化全部由 193779d 内那一行 metadata 字段更新贡献；
main 上此后无任何语义或非语义变化。**

## 5. 跨文件一致性检查

### 5.1 无 "evidence ready" 隐含提升 ✅

`SOURCE_STATUS.md` @193779d：

- 四个来源 Evidence Readiness 全部为 **❌ NOT READY**；
- 明文原则：「FETCH_BLOCKED 不隐含'不可获取'」「NOT READY 是独立状态, 不因 Discovery 而自动升级」；
- 明文「🟡 SOURCE_DISCOVERED … 不关闭 GAP」。

### 5.2 Sprint 报告声明与事实一致 ✅

`KNOWLEDGE_PHASE_7.3_REPORT.md` 声明 Source Discovery PASS / Verbatim Acquisition BLOCKED /
Knowledge Production 0 —— 与第 2 节实测 diff 一致。

### 5.3 ⚠ DEF-01：SOURCE_STATUS.md 的 GAP 编号交叉错标（非阻塞）

| 来源 | SOURCE_STATUS.md 标注 | GAPS 登记簿归属 |
|------|------------------------|------------------|
| 紫微斗数全书 | GAP-13 | **GAP-12**（auxiliary_star 主源） |
| 三命通会 / 渊海子平 | GAP-12 | **GAP-13**（shen_sha 来源） |
| 紫微斗数全集 | GAP-01 | GAP-01 ✅ 一致 |

两份文档对 GAP-12/13 的**状态描述本身一致且均未关闭**，错位仅是标签映射问题，
不构成状态提升。建议在下次文档维护中修正（本次审计不修改，遵守 REVIEW ONLY）。

## 6. GAP 状态复核

| Gap | 要求状态 | 实测 @193779d | 实测 @HEAD | 判定 |
|-----|----------|---------------|------------|------|
| GAP-01 | 🟡 SOURCE_DISCOVERED 未关闭 | 🟡 SOURCE_DISCOVERED（GitHub 候选源已定位，待正文获取与核验） | 同左 | ✅ 合规 |
| GAP-12 | 🟡 SOURCE_DISCOVERED 未关闭 | 🟡 SOURCE_DISCOVERED（wikisource URL 已登记，webfetch 阻塞，未 ingest） | 同左 | ✅ 合规 |
| GAP-13 | 🟡 SOURCE_DISCOVERED 未关闭 | 🟡 SOURCE_DISCOVERED（URL 已 websearch 确认，verbatim 未核验） | 同左 | ✅ 合规 |

禁用状态词扫描：三个 GAP 行中**未出现 CLOSED / EVIDENCE_READY / VERBATIM_VERIFIED**。
（注：GAP-05/GAP-10 行中的 RESOLVED/CLOSED 字样属 Phase 7.1.5 / 7.2A 历史合法闭项，先于 7.3 存在，不在本次审查范围。）

## 7. 停止条件遵守声明

本审查为只读审计 + 本报告产出：

- ❌ 未执行合并（报告位于独立分支 `work/knowledge/phase73-evidence-review`）
- ❌ 未生产任何知识节点/关系/引用
- ❌ 未修改 corpus、sources、schema 或任何被审对象
- ❌ 未修正 DEF-01（留待人工授权的文档维护）

---

## 附录 A：复现命令

```bash
# 单行 diff
git diff 058c286 193779d -- knowledge/ziwei_corpus.json
# 全量变更清单
git show --stat 193779d
# 后续污染检查
git log --oneline 193779d..HEAD -- knowledge/ziwei_corpus.json knowledge/sources/ziwei docs/governance/knowledge/ZIWEI_CORPUS_GAPS.md
git diff 193779d HEAD -- knowledge/ziwei_corpus.json
# digest 复现（注意按 CRLF 计算，与 pipeline.py _source_digests 工作树行为一致）
git cat-file blob 193779d:knowledge/sources/ziwei/source_01.yaml   # LF blob
python - <<'PY'
import hashlib, subprocess
raw = subprocess.run(["git","cat-file","blob","193779d:knowledge/sources/ziwei/source_01.yaml"],
                     capture_output=True).stdout
print(hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest())
PY
```

## 附录 B：关键哈希速查

| 值 | 含义 |
|----|------|
| `1dd6851e4f4ad05ce69dc1a178251915c76bc1d545c009c65e37dc05457ad7be` | source_01.yaml @parent 的 CRLF sha256（旧登记值） |
| `6c27dfda7b32c9b6b251f239b6c84bdda882d142d417f220b3057a7820d77121` | source_01.yaml @193779d 的 CRLF sha256（新登记值 = 当前工作树实测） |
| `96dad292e8a8073d361f0e0d11c204db04f2300b31c442fafa5369d15ebb71ba` | 当前工作树 ziwei_corpus.json 整文件 sha256 |
