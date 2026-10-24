# Knowledge H6 Evidence Expansion Protocol（外网来源获取授权协议）

> **Status**: **AUTHORIZED**（用户 2026-10-24 选择 “H6 授权 + 语料证据扩展” Sprint）
> **Date**: 2026-10-24 · **Branch**: `work/knowledge/h6-evidence-expansion`
> **依据**: `AGENTS.md` **H6**（外网/外部主体实验：人工授权 + 冻结窗口 + 证据保全 + 零 retry）
> **目标**: 获取 BaZi/Qimen candidate 语料的 revision-pinned 原文，补足逐字证据；不虚构、不外推。

---

## 1. 授权范围（请求清单）

| # | 来源 | URL（`action=raw`） | 用途 |
|---|------|---------------------|------|
| 1 | 淵海子平 | `https://zh.wikisource.org/w/index.php?title=淵海子平&oldid=2593607&action=raw` | BaZi 摘要引用逐字核验（十神/干支/合冲刑害） |
| 2 | 三命通會/卷二 | `https://zh.wikisource.org/w/index.php?title=三命通會/卷二&oldid=2292392&action=raw` | BaZi 五合/三刑/六害复核 |
| 3 | 奇門遁甲統宗 | `https://zh.wikisource.org/w/index.php?title=奇門遁甲統宗&oldid=1378608&action=raw` | Qimen revision pin 登记 + 抽样逐字核验 |
| 4 | 煙波釣叟歌 | `https://zh.wikisource.org/w/index.php?title=煙波釣叟歌&action=raw` | Qimen 佐证来源 revision pin（抓取后登记 revid） |
| 5 | （可选）煙波釣叟歌 revid | `https://zh.wikisource.org/w/api.php?action=query&prop=revisions&rvprop=ids|timestamp|sha1&titles=煙波釣叟歌&format=json` | 固定 revid |

**请求预算**: ≤ 5 次 GET；**零 retry**；单次执行；仅在 2026-10-24 会话窗口内。

## 2. 禁止

- 禁止任何付费 API、账号登录、批量爬取、站外跳转。
- 禁止对失败请求重试；首个失败即停止并记录。
- 禁止以训练知识/网络常见说法替代原文；不可核实 → 记 GAP（H5）。
- 禁止将抓取件提交入库（仓库外保留）。

## 3. 证据保全

1. 原始字节保存至仓库外目录：`%TEMP%/om-h6-2026-10-24/`。
2. 每个文件登记 SHA-256 + 字节数 + HTTP 状态；与既有 revision pin（`a4447be5…`、`e58c3f48…`）比对。
3. 若 sha256 与既有登记不一致 → 停止并出报告（不得静默覆盖）。
4. 回执登记至 `knowledge/sources/{bazi,qimen}/*.yaml` 与 `SOURCE_STATUS` 类文档。

## 4. 批准记录

| 项 | 内容 |
|----|------|
| 批准人 | 用户 |
| 日期 | 2026-10-24 |
| 方式 | Sprint 选择 “H6 授权 + 语料证据扩展” |
| 批准范围 | 上述 §1 请求清单 + §3 证据规则 |

## 5. 尝试记录

### 尝试 1（2026-10-24，已停止）

| 项 | 值 |
|----|-----|
| 请求 | `淵海子平 oldid=2593607 action=raw`（第 1 条） |
| 结果 | **HTTP 403**（Wikimedia robot policy） |
| 响应体 | 已保全：`%TEMP%/om-h6-2026-10-24/yuanhai.txt`，2185 B，sha256 `7f5c7e602b1ef1a2ad1ee2f060000b0cf54ab6f417cf0c340507638582453587` |
| 处置 | 依 §2「零 retry / 首个失败即停止」，**未发起第 2~5 条请求** |
| 诊断 | Wikimedia 要求可识别的 User-Agent（含联系信息）；`httpx` 自定义 UA 仍被策略判定为自动化客户端 |

### 二次授权（2026-10-24，已批准）

用户批准按下列修订执行**单次**二次抓取（新窗口，2026-10-24）：

- UA：`OpenMetaphysics-Evidence/1.0 (https://github.com/acdemi/open-metaphysics; research)`
- 请求清单不变（§1，≤5 GET）；零 retry；首个非 200 即终止并记录。

### 尝试 2（2026-10-24，成功）

| 来源 | HTTP | 字节 | sha256 | 与既有 pin |
|------|------|------|--------|------------|
| 淵海子平 oldid=2593607 | 200 | 173237 | `a4447be5…` | 一致 |
| 三命通會/卷二 oldid=2292392 | 200 | 66693 | `e58c3f48…` | 一致 |
| 奇門遁甲統宗 oldid=1378608 | 200 | 141759 | `b4d0271d…` | 新 pin |
| 煙波釣叟歌 | 200 | 5935 | `702f6311…` | 新 pin |
| 煙波釣叟歌 revid API | 200 | 251 | `666c1a20…` | revid 1336835 |

结果见 `KNOWLEDGE_H6_EVIDENCE_DOSSIER.md`；BaZi 9/14 逐字核验通过。

### 拟议修订（历史）

| 项 | 拟议 |
|----|------|
| UA | 采用符合 Wikimedia 机器人政策的长格式 UA（含项目标识与联系 URL） |
| 备用路径 | `api.php?action=parse&oldid=<revid>&prop=wikitext&format=json`（API 与 raw 同一策略） |
| 预算 | 二次窗口单次执行，≤5 GET，零 retry；仍仅限 §1 清单 |
| 停止条件 | 再次非 200 即终止并出报告 |
