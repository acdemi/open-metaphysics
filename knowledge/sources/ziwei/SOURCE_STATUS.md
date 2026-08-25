# Ziwei Source Status

> Phase 7.3 — Source Acquisition & Evidence Availability Sprint
> 日期: 2026-08-25
> 状态: 记录（来源发现与登记, 不等于证据就绪）

---

## 来源状态总览

| Source | Discovery | Metadata | Access | Evidence Readiness | GAP |
|--------|-----------|----------|--------|-------------------|-----|
| 紫微斗数全书 | ✅ DISCOVERED (wikisource) | ✅ PARTIAL | ❌ FETCH_BLOCKED | ❌ NOT READY | GAP-13 |
| 紫微斗数全集 | ✅ DISCOVERED (GitHub candidate) | ✅ PARTIAL | ❌ NOT_ATTEMPTED | ❌ NOT READY | GAP-01 |
| 三命通会 | ✅ DISCOVERED (wikisource) | ✅ PARTIAL | ❌ FETCH_BLOCKED | ❌ NOT READY | GAP-12 |
| 渊海子平 | ✅ DISCOVERED (wikisource) | ✅ PARTIAL | ❌ FETCH_BLOCKED | ❌ NOT READY | GAP-12 |

**关键原则**: FETCH_BLOCKED 不隐含"不可获取"——仅表示当前环境/方法无法获取。NOT READY 是独立状态, 不因 Discovery 而自动升级。

---

## 来源详情

### 紫微斗数全书 (GAP-13)

| 维度 | 状态 | 说明 |
|------|------|------|
| Discovery | ✅ DISCOVERED | websearch 确认 wikisource 存在 |
| URL | `https://zh.wikisource.org/wiki/紫微斗數全書` | 传统字 URL; 公有领域（清朝, 作者逝世 >100年） |
| 结构 | 卷一/卷二/卷三 | 卷一含诸星问答论（文昌/文曲/左辅/右弼/天魁天钺/禄存/擎羊/陀罗/火星/铃星定义） |
| Access | ❌ FETCH_BLOCKED | webfetch 4 次超时/transport error（7.2B ×2, 7.3 ×2） |
| Evidence Readiness | ❌ NOT READY | 原文未入库, 未逐字核验 |
| 备选来源 | GitHub `Renhuai123/ziwei-doushu`（MIT）含 `quanshu.ts` | 需额外治理裁定后方可使用 |

### 紫微斗数全集 (GAP-01)

| 维度 | 状态 | 说明 |
|------|------|------|
| Discovery | ✅ DISCOVERED | GitHub 仓库 `Renhuai123/ziwei-doushu` 含 `quanji.ts`（清代古本） |
| URL | `https://github.com/Renhuai123/ziwei-doushu` | MIT License; 含全书+全集+骨髓赋 |
| Access | ❌ NOT_ATTEMPTED | 未尝试获取 |
| Evidence Readiness | ❌ NOT READY | 版本核验/对应关系确认未完成 |
| 治理要求 | 需额外裁定 | 版本核验、对应关系确认后方可作为 Tier 1 原始来源 |

### 三命通会 (GAP-12)

| 维度 | 状态 | 说明 |
|------|------|------|
| Discovery | ✅ DISCOVERED | websearch 确认 wikisource 存在 |
| URL | `https://zh.wikisource.org/wiki/三命通會` | 卷一至卷九（缺十至十二）; 公有领域 |
| 备选 URL | `https://zh.wikisource.org/wiki/三命通會(四庫全書本)/全覽` | 四库全书本全文 |
| 备选 URL | `https://ctext.org/wiki.pl?if=gb&res=532360` | Chinese Text Project |
| Access | ❌ FETCH_BLOCKED | webfetch 超时 |
| Evidence Readiness | ❌ NOT READY | 神煞章节（论羊刃/论驿马/论亡神劫煞/论天乙贵人/论禄等）未获取 |

### 渊海子平 (GAP-12)

| 维度 | 状态 | 说明 |
|------|------|------|
| Discovery | ✅ DISCOVERED | 已登记于 source_02.yaml; wikisource 通行本 |
| URL | `https://zh.wikisource.org/wiki/渊海子平` | 已知存在（7.1.5 曾成功核验卷二·三刑/六害） |
| Access | ❌ FETCH_BLOCKED | webfetch 超时（本次会话） |
| Evidence Readiness | ❌ NOT READY | 神煞相关章节未获取 |

---

## 环境限制说明

- **webfetch 工具**: 本会话（7.2B + 7.3）共 4 次调用全部 timeout/transport error
- **websearch 工具**: 正常工作, 确认了所有来源的可访问性
- **来源可访问性**: websearch 结果确认 wikisource 页面存在且公有领域, 环境限制不等于来源不可获取

---

## 下一步（需人工授权）

1. **webfetch 重试**: 环境恢复后重试 wikisource URL
2. **紫微全书入库**: 获取原文并逐字核验辅星定义
3. **紫微全集核验**: GitHub 仓库版本核验 + 对应关系确认
4. **三命通会/渊海子平重试**: 获取神煞章节原文
