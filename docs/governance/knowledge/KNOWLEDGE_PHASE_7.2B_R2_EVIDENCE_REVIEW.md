# Knowledge Phase 7.2B-R2 — Evidence Review（独立证据复核）

> **审查模式**: 审计（REVIEW） · **日期**: 2026-09-16 · **分支**: `work/knowledge/phase7.2b-r3`
> **审查对象**: main `0d57aa9`（生产） + `e5f324f`（报告与指针）；基线 `04bfd29`（7.2B-R, 86/37/22）
> **触发事由**: R2 以根目录状态戳 `phase_7.2b_r2_status.txt`（内容 `Phase 7.2B-R2 COMPLETE. BLOCKED for Evidence Review.`）标记门未闭合；该戳已于 2026-09-16 本门闭合后清理（内容已在此就地留档）。
> **范围**: 只读复核 + 本报告；**未生产、未修改**任何语料 / 冻结工件。

---

## 1. 结论

```text
EVIDENCE CONFIRMED — VERBATIM REPRODUCIBLE
node evidence: PASS（10/10 passage, 7/7 R2 key_quote）
gate: CLOSED（R2 证据门可闭合）
附: 非阻塞缺陷 DEF-02（pipeline EOL 写入，见 §4）
```

R2 的 7 类神煞节点及其 10 条条目级引用，**可由仓库外 revision-pinned 原文独立复现为逐字一致**；
R2 报告的关键数字（93/37/32、digest `ce3b83b7`、605 测试）全部独立实测复现。
冻结工件零触碰。**未发现任何证据虚构、静默改写或范围越界。**

## 2. 方法（可复现，不依赖 R2 会话内状态）

| 项 | 做法 |
|----|------|
| 原文获取 | 直接抓取 wikisource `action=raw&oldid=<revid>`（HTTPS，非 webfetch），与登记 sha256 比对 |
| 逐字核验 | 沿用 7.3.1 dossier §3 口径：抓取件去空白后做**子串逐字匹配**，断言串同去空白 |
| 差异登记 | 复核 V-6/V-7/V-8 是否**在原文中存在**（证明登记真实、未静默修正） |
| diff 范围 | `git show --numstat` + 逐行 `-` 行审查 |
| 冻结工件 | 路径级 diff 审查（`reference/` `src/` `docs/specification/` contracts / golden vectors / ACP） |
| 复现性 | pipeline 双跑；`validate.py`；pytest 经 junit XML 取权威计数 |

## 3. 核验结果

### 3.1 来源与 pin 完整性 ✅

| 对象 | 登记 pin | 独立抓取实测 | 判定 |
|------|----------|--------------|------|
| 三命通會/卷三（R2 主源） | revid 2184219, sha256 `2de8fc1b…488e` | **65356 B, sha256 `2de8fc1bf46eb4ecc5436b6cece6d4a06e56330565f3aa6e4cfaa581f5b0488e`** | ✅ 逐字节一致 |
| 三命通會/卷二（R2 之外的 7.2B-R 节点源） | revid 2292392 | 23087 chars（抓取成功） | ✅ |
| 紫微斗數全書/卷一（对照组） | revid 7913704, sha256 `9beb8038…818a` | **67698 B, sha256 `9beb8038a8b82154d15d81c8ff822423d4f0c7c006f536a86552adeaa594818a`** | ✅ 逐字节一致（证明抓取口径可信） |

### 3.2 逐字核验 ✅

- **10/10 passage PASS**（`phase_7.2b_r2.yaml` 全量），且**全部为连续子串**（无拼接、无省略号）：
  省略号扫描 `[…] | ... | ···` → **0 命中**。
- **7/7 R2 key_quote PASS**（kong_wang / yuan_chen / zai_sha / liu_e / gou_jiao / tian_luo_di_wang / shi_e_da_bai）。
- 附：`shen_sha.yaml` 其余 11 条 key_quote 中，8 条对卷三 PASS；余 3 条（jiang_xing / hua_gai / xian_chi）属
  **7.2B-R** 且来源为**《三命通會》卷二**——对正确的卷二抓取件复核 **3/3 PASS**。
  （初次对卷三比对时的 3 个 FAIL 系审查方法取错来源卷所致，**非缺陷**，已按正确来源复核。）
- 异文登记真实性 ✅：V-6「命后一三辰为绞」/ V-7「日值禄人空亡」/ V-8「此春义也」**均存在于原文**，
  语料保留原字形并写入 `attributes.原文异文`，**未静默修正**。

### 3.3 diff 范围与边界 ✅

`0d57aa9` 仅触及 4 文件（663 插入 / 3 删除）：
`shen_sha.yaml`（+77/-1）、`references/phase_7.2b_r2.yaml`（+77/-0）、`ziwei_corpus.json`（+412/-2）、`tests/test_knowledge_corpus_r2.py`（+97/-0）。
`e5f324f` 仅触及 docs / 状态标记。

- `shen_sha.yaml` 的**唯一删除行**是文件头注释（`11 个` → `18 个 = 7.2B-R 11 + 7.2B-R2 追加 7`）——
  **既有 86 节点零语义改动**。
- `ziwei_corpus.json` 的 2 处删除仅为 metadata 计数（`nodes: 86` → 93、`references: 22` → 32），**无任何语义删除**。
- **冻结工件零触碰**：`reference/` `src/` `docs/specification/` `reference/contracts/` golden vectors / ACP 目录均无变更。

### 3.4 复现性 ✅

| 检查 | 命令 | 结果 |
|------|------|------|
| 计数与 digest | `python knowledge/pipeline.py` | 93 nodes / 37 relations / 32 references；sha256 `ce3b83b75a987f27f590d60d79d1efa823812d5663ba58bd68843d45ffb89d5a`（= R2 登记值） |
| 确定性 | pipeline 双跑 | 内部 digest 两次一致（KB-020） |
| KB 规范 | `python knowledge/validate.py` | `VALIDATION PASSED: all corpus entries conform to KB-001~020` |
| 测试 | `pytest -q`（junit XML 取数） | **tests=605 failures=0 errors=0 skipped=0, exit 0** |

## 4. 发现

### DEF-02（非阻塞，REAL，已定位到行）

`knowledge/pipeline.py:83` 用 `OUTPUT.write_text(text, encoding="utf-8")` 写入——
Windows 文本模式默认把 `\n` 翻成 CRLF，而 `.gitattributes` 规定
`knowledge/**/*.json text eol=lf`。后果：

- 跑一次 pipeline 即令 `git status` 变脏（` M knowledge/ziwei_corpus.json`）；
- 工作树文件 sha256 变为 `0149ff8a…`，与登记/存储的 LF 口径 digest `ce3b83b7…` **不一致**；
- 第 84 行 checksum 是对 LF 字符串计算的，故**登记值本身仍正确**，不影响 KB-020 确定性判定。

建议修复（一行）：`Path.write_text(text, encoding="utf-8", newline="\n")`。

## 5. 决策点（需人工裁定）

| 编号 | 事项 | 依据 |
|------|------|------|
| D-1 | 关系层是否生产（15 类 relation_type 表达力） | 沿用，未变 |
| D-6 | **四化**（化禄/化权/化科/化忌）在冻结 KB-002 `NodeType` 中**无对应类型** → 记 GAP-14，**不生产**（不得扩 schema） | 本次新发现 |
| D-7 | `auxiliary_star` 现 12，Scope 预期 12-15；卷一·諸星問答論 剩余杂曜（天空/地劫/天伤/天使/天刑/天姚/天哭/天虚）若生产将达 20+，**超出冻结预期 → 须人工批准 scope 变更** | 本次新发现 |
| D-8 | 三命通會卷三 尚有 7 个未抽取神煞章节（金舆/三奇/天月德/太极贵/学堂词馆/德秀/暗金的煞）→ shen_sha 现 18（预期 10-20），可继续生产 | 本次新发现 |

## 6. 零触碰声明

- ❌ 未生产任何节点/关系/引用；未修改任何被审语料文件
- ❌ 未修改冻结工件（契约 / 向量 / Reference / 规范 / ACP）
- ❌ 未合并 main、未推送
- ✅ 仅新增本报告（+ GAP-14 登记行）

## 附录：复现命令

```bash
# 原文（revision-pinned，与登记 sha256 比对）
curl -sL "https://zh.wikisource.org/w/index.php?title=%E4%B8%89%E5%91%BD%E9%80%9A%E6%9C%83/%E5%8D%B7%E4%B8%89&action=raw&oldid=2184219" -o j3.txt
sha256sum j3.txt   # 2de8fc1bf46eb4ecc5436b6cece6d4a06e56330565f3aa6e4cfaa581f5b0488e

# 逐字核验（去空白后子串匹配）、计数、确定性、KB 校验
python knowledge/pipeline.py && python knowledge/pipeline.py
python knowledge/validate.py
pytest -q --junitxml=junit.xml
```
