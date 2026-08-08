# Qimen Freeze Gap

> **状态**: Phase 5.6 — 冻结缺口已全部关闭（Closed）；剩余风险已分类。
> **冻结产物**: `docs/specification/QIMEN_BEHAVIOR_CONTRACT.md` v1.0.0（Frozen）

---

## Gap 1 — D2 三元划分（政策裁定） ✅ Closed

| 项 | 内容 |
|----|------|
| 当前行为 | 日号近似: 公历日号 1-10 → 上元(+0)、11-20 → 中元(+3)、21-30 → 下元(+6) |
| Phase 5.6 决策 | **Option A**：日号近似定为**规范行为**（Qimen Runtime v0.3.0），
  契约 `QIMEN_BEHAVIOR_CONTRACT.md` QC-004 冻结生效 |
| 影响 | 全部 24 向量升级为 normative fixtures；`ju`/`triple_offset` 字段冻结 |
| 改判路径 | 真拆补法 = 未来 ACP + 契约主版本递增 v1.0.0 → v2.0.0 + 24 向量迁移
  （迁移计划见 `QIMEN_D2_IMPACT_ANALYSIS.md`）—— **已分类为 future extension** |

## Gap 2 — D14 晚子时（行为裁定） ✅ Closed

| 项 | 内容 |
|----|------|
| 当前行为 | 23:00-24:00 时支=子（当日），**不换日柱** |
| Phase 5.6 决策 | **冻结"不换日柱"**为规范行为；向量 `N_late_zishi`
  （2024-05-15 23:30，day_of_month=15）锁定 |
| 改判路径 | 若未来改判换日 = ACP + 契约主版本递增 + N_late_zishi 向量重生成 |
  —— **已分类为 future extension** |

## Gap 3 — 覆盖缺口（春分/秋分/晚子时向量） ✅ Closed

| 缺口 | 向量 | 状态 |
|------|------|------|
| 春分 | N_chunfen（2024-03-20 12:00，阳遁 1 局） | ✅ Closed |
| 秋分 | N_qiufen（2024-09-23 12:00，阴遁 4 局，值符星天禽） | ✅ Closed |
| 晚子时 | N_late_zishi（2024-05-15 23:30，阳遁 4 局） | ✅ Closed |

## Gap 4 — ACP / 契约批准 ✅ Closed

| 项 | 内容 |
|----|------|
| Phase 5.6 动作 | 契约草稿 0.1.0-draft → **Frozen v1.0.0**
  （`docs/specification/QIMEN_BEHAVIOR_CONTRACT.md`）；向量
  candidate normative → **normative regression fixtures** |
| 版本流程 | engine_version / rule_set_version = 0.3.0（算法未变，无需递增） |

---

## 剩余风险分类

### 已冻结行为（Frozen behavior — 契约覆盖，变更须 ACP）

- 日号三元近似（D2 Option A）
- 晚子时不换日柱（D14）
- 12 条冻结规则（D1/D3-D13）全部契约化（QC-001~QC-014）

### 已知局限（Known limitation — 文档化，不阻塞）

- 与主流拆补法排盘存在系统性差异（日号近似）；契约 QC-004 显式声明
- 天禽星不寄宫（简化）；八神阴遁不逆布（流派选择）—— 均记录于
  `QIMEN_ALGORITHM_ASSUMPTIONS.md`
- 24 向量覆盖 13/24 节气（未覆盖节气走相同代码路径，风险低）

### 未来扩展（Future extension — 需独立授权）

- 真拆补法 / 置闰法（D2 改判，v2.0.0 路径）
- 格局判断 / 用神 / 应期 / 暗干
- RAG / Consensus integration / LLM 解释层
- Reference Runtime Qimen 域（以本契约为对齐基线）
- 跨语言实现（Rust/Go，届时需 RuntimeAdapter）
