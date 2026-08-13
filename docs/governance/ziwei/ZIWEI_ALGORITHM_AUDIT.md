# Ziwei Algorithm Audit

> **Sprint**: Phase 6.7.1 — Ziwei Algorithm Stabilization & Rule Decision
> **日期**: 2026-08-13
> **性质**: 计算层完整审计（真实代码提取, 非模板套用）。本 Sprint 不修改
> 任何生产算法；发现记录于此, 供规则裁定与 Phase 6.7.2 Golden Vector 使用。
> **前置工件**: Phase 7.0 评估（`ZIWEI_CAPABILITY_ASSESSMENT.md` /
> `ZIWEI_RULE_INVENTORY.md` ZW-001~017 / `ZIWEI_TEST_COVERAGE_REVIEW.md` /
> `ZIWEI_CROSS_DOMAIN_PRECHECK.md`, 本审计在其结论之上继续, 不重复其内容）。
>
> **实际路径勘误**: 任务书假设 `src/openmetaphysics/domain/ziwei/core.py` 与
> `src/domain/ziwei/` 不存在。**已核实**：src 下仅 `domain/qimen/`；
> Ziwei 实现实际位于：
> - `src/openmetaphysics/agents/ziwei.py`（引擎, 411 行）
> - `src/openmetaphysics/agents/ziwei/pattern_matcher.py`（格局匹配, 108 行, 不可达, 见 F-1）
> - `src/openmetaphysics/agents/ziwei_explainer.py`（解释层, 233 行, 未接线, 见 F-2）
> - 基础设施: `src/openmetaphysics/core/calendar.py` / `core/models.py` /
>   `core/schemas.py` / `core/engines.py`
> - 测试: `tests/test_ziwei.py`（12 例）
> - `reference/` 中无 Ziwei 计算实现（仅 Knowledge/Consensus 层
>   `system: "ziwei"` 标签, 属其他域, 不计入）。

---

## 1. 计算层审计问答（16 项）

### Q1. Ziwei 的实际入口是什么？

- **Agent**: `ZiweiAgent`（`src/openmetaphysics/agents/ziwei.py:386`）
- **引擎**: `ZiweiEngine.calculate()`（同文件 `:287`），继承
  `DeterministicEngine`（`core/engines.py:73`）
- **注册**: `agents/registry.py:41`（默认注册表四智能体之一）
- **编排**: `orchestration/graph.py` fan_out（run-all 时参与）
- **API**: `POST /agents/ziwei/compute`（`api/app.py:46`）

### Q2. 输入对象是什么？

`ZiweiInput(AgentInput)`（`agents/ziwei.py:236`）：
- 继承信封: `request_id` / `born_at`（**强制 tz-aware**, `core/schemas.py:58`）/
  `born_location: GeoPoint|None` / `gender: Gender = UNKNOWN` / `question` /
  `locale` / `seed` / `client_nonce`
- 领域追加: `lunar_month: int|None`、`lunar_day: int|None`（显式农历重放；
  None → sxtwl 自动转换）
- `extra="forbid"`（继承自 AgentInput）

### Q3. 输出对象是什么？

- 信封: `ZiweiOutput(AgentOutput)`, `agent="ziwei"`, `result: ZiweiChart`
  （`agents/ziwei.py:263`）
- 载荷: `ZiweiChart{fate_palace_index, body_palace_index, yin_yang: Literal["yin","yang"],
  wuxing_ju: str, palaces: list[Palace]×12, calendar_note: str|None}`
  （`agents/ziwei.py:253`, `extra="forbid"`）
- `Palace{index 0..11, name, earthly_branch, heavenly_stem, main_stars: list[str],
  auxiliary_stars: list[str], is_fate_palace, is_body_palace}`
  （`agents/ziwei.py:241`, `extra="forbid"`）

### Q4. 是否使用 Pydantic？

是。Pydantic v2（`pydantic>=2.0`, pyproject.toml）。所有领域模型
`BaseModel` + `ConfigDict(extra="forbid")`；信封共享 `core/schemas.py`。

### Q5. 是否存在领域 Schema？

是。`ZiweiInput` / `ZiweiChart` / `Palace` 即领域专属 Schema（位于
`agents/ziwei.py`, 与 BaZi 模式一致 —— 领域 Schema 随 agent 存放）。

### Q6. 是否存在 JSON Schema？

- **可导出**: `BaseAgent.schema()` 通过 `Model.model_json_schema()` 动态生成,
  经 `GET /agents/ziwei/schema` 发布（`core/engines.py:160`, `api/app.py:38`）。
- **静态 JSON Schema 文件**: **不存在**（无 `ziwei_contract.schema.json` 类工件）。
- SCHEMAS.md §3.2 已登记 Ziwei 模型（Phase 7.0 确认存在 1 处勘误,
  本 Sprint 修复, 见 §3）。

### Q7. 核心计算模块有哪些？

| 模块 | 位置 | 职责 |
|------|------|------|
| ZiweiEngine | `agents/ziwei.py:284` | 命宫/身宫/五行局/宫垣/十四主星 |
| ZIWEI_POS 定局表 | `agents/ziwei.py:49-210` | 5 局 × 30 日紫微定位查表 |
| 双星系偏移表 | `agents/ziwei.py:214-233` | 紫微星系 6 星（逆行）+ 天府星系 8 星（顺行） |
| calendar 原语 | `core/calendar.py` | 立春/年序（Meeus）+ `solar_to_lunar`（sxtwl） |
| 参考表 | `core/models.py` | 天干/阴阳/纳音/地支 |
| 引擎基座 | `core/engines.py` | DeterministicEngine/BaseAgent/TraceRecorder |
| 信封 | `core/schemas.py` | AgentInput/AgentOutput/Gender/GeoPoint |

### Q8. 是否存在历法/天文基础设施？

- **自有**: `core/calendar.py` —— Meeus 截断太阳黄经（~0.01°）, 24 节气
  /立春时刻/干支年序, `lru_cache` 纯缓存, 无网络无星历文件。
- **外部**: `sxtwl`（寿星天文历, `sxtwl>=1.6`）—— `solar_to_lunar` 公历转农历,
  `compute()` 内**唯一外部依赖**（惰性 import, 位于 `core/calendar.py:174`）。
- **无**: 真太阳时（Ziwei 不使用; `core/solar_time.py` 仅供 Qimen D13）。

### Q9. 是否存在确定性纯函数？

是。`calculate()` 为纯函数：无 RNG、无 IO、无 LLM、无时钟（`computed_at`
仅信封层, 由 `BaseAgent.compute` 注入）。证据: `test_replay_identical`
（逐字节 replay, `tests/test_ziwei.py:151`）。推理轨迹 4 步
（`ziwei.fate_body_palace` / `ziwei.wuxing_ju` / `ziwei.ziwei_position` /
`ziwei.main_stars`）, 置信度固定 0.95（rule_coverage, 基类默认）。

### Q10. 是否存在隐式默认值？

| 隐式默认 | 行为 | 位置 |
|----------|------|------|
| `gender=UNKNOWN` | 继承但 **engine 从不读取**（ZW-017） | schemas.py:52 |
| `lunar_month/day=None` | 自动走 sxtwl 转换 | ziwei.py:295 |
| `born_location=None` | 时区回退 `born_at.tzinfo` | ziwei.py:268-276 |
| 时区字符串非法 | ZoneInfo 异常 → **静默回退** `born_at.tzinfo` | ziwei.py:272-275 |
| 闰月 | 月号与平月同值安星 + `calendar_note` 记录 | ziwei.py:299-303 |
| `locale/seed/client_nonce/question` | 继承但 Ziwei 计算不使用 | schemas.py |
| 置信度 | 固定 0.95（基类默认公式, factors={"steps": 4.0}） | engines.py:141 |

### Q11. 是否存在异常/回退行为？

| 场景 | 实际行为 | 备注 |
|------|----------|------|
| `lunar_day` 越界（0/31+） | **无校验** → `ZIWEI_POS[ju][day]` `KeyError` 直抛 | 已列为开放裁定（ZW-001）; API 层 500 |
| sxtwl 缺失 | `ImportError` 直抛（compute 路径） | 依赖声明于 pyproject; 无运行时降级 |
| `solar_term_time` 未找到 | `ValueError`（通用原语, 非 Ziwei 特有） | calendar.py:96 |
| 时区非法/缺失 | 静默回退（见 Q10）, **无警告** | 与 BaZi BC-012 回退链差异（ZB-06） |
| 解释层失败 | `Explainer.render` try/except → 确定性 fallback | 见 F-2 |

### Q12. 是否存在版本号？

是。审计时 `ZiweiEngine.version = "0.2.0"`（`agents/ziwei.py`）;
**Phase 6.7.1.6（ACP 实施）后为 v0.3.0**（定局表生成式 + 廉贞 -8 + 输入校验）;
metadata 断言 `engine_version == "0.3.0"`（`tests/test_ziwei.py`）。

### Q13. 当前测试数量是多少？

- `tests/test_ziwei.py`: **12 例**（唯一直接文件）
- 间接涉及: `tests/test_api.py`（list_agents 断言 ziwei 在册）×1 +
  `tests/test_orchestration.py`（run-all 四智能体）×1
- `reference/tests/`: 无 Ziwei 测试
- 全仓库基线（本 Sprint 开始时）: 557 例全绿

### Q14. 当前测试覆盖哪些规则？

| 覆盖 | 测试 |
|------|------|
| 命宫 canonical（正月寅时→子, 水二局） | `test_fate_palace_canonical` |
| 身宫 canonical（辰） | `test_body_palace_position` |
| 十二宫名称集合 | `test_all_12_palaces_have_correct_names` |
| 宫干支存在性（弱 smoke） | `test_all_palaces_have_stem_branch` |
| 十四主星存在性（无位置） | `test_14_major_stars_all_present` |
| 紫微/天府镜像 | `test_ziwei_tianfu_mirror_relationship` |
| sxtwl 历法数值 ×3（5/1、春节、闰月） | `test_lunar_conversion_*` |
| replay 确定性 | `test_replay_identical` |
| 用户农历覆盖（弱 smoke） | `test_user_provided_lunar_used_directly` |
| metadata | `test_metadata_updated` |

规则级矩阵见 `ZIWEI_TEST_COVERAGE_REVIEW.md`（Phase 7.0 §2 + Phase 6.7.1 §6 补测后矩阵）。

### Q15. 哪些行为已经可以视为规范候选？

- 命宫公式 / 身宫公式（ZW-007/008）
- 时辰定义（钟表时, 子时 23:00~00:59, ZW-003）
- 年干立春界（复用 BaZi B1 原语, ZW-005）
- 五虎遁（ZW-006）
- 命宫天干（ZW-009）
- 五行局映射（纳音末字 → {水2,木3,金4,土5,火6}, ZW-010）
- 十二宫布局（干/支/名/标志, ZW-011）
- 天府镜像（ZW-013）
- 阴阳字段（ZW-016）
- 未实现边界（辅星/四化/大限/gender, ZW-017）
- 紫微定局表（ZW-012）与紫微星系偏移（ZW-014）: **可作规范候选但存在
  与主流歌诀的系统性差异, 须人工裁定**（F-3/F-4, 见 §2）

### Q16. 哪些行为仍属于实现细节？

- reasoning_trace 步文案/步序（4 步 rule_ref 命名）
- `calendar_note` 英文措辞（`"leap month 2 (闰月) using month number 2 for placement"`）
- 主星列表追加顺序（紫微星系先于天府星系; 同宫星序）
- 置信度 0.95 固定值（基类默认, 非 Ziwei 专属）
- 解释层（ZiweiExplainer/pattern_matcher, 计算域外, 见 F-1/F-2）

---

## 2. 关键发现（Findings Register）

| # | 发现 | 严重度 | 处理 |
|---|------|--------|------|
| F-1 | `agents/ziwei/pattern_matcher.py` **不可导入**: 模块 `ziwei.py` 与目录 `ziwei/` 同名, 目录无 `__init__.py`, `ziwei.py` 遮蔽命名空间包 → `openmetaphysics.agents.ziwei.pattern_matcher` 为死代码, `match_patterns` 从未被任何代码/测试调用（实测 `ModuleNotFoundError`） | 高（死代码） | 记录; 不在本 Sprint 修改（解释域）; 候选裁定见 RULE_DECISION §6 |
| F-2 | `ZiweiExplainer` 引用不存在的 `chart.patterns`（ZiweiChart 无此字段且 `extra="forbid"`）与 `output.input_payload`（AgentOutput 无此字段）→ LLM 路径必然 AttributeError（被 render try/except 兜底至 fallback）; 且 **ZiweiExplainer 未接线**（API/编排用通用 `Explainer`）→ 格局识别全链路断裂（matcher 未跑、输出无 patterns、解释层读不到） | 中（解释域, 不影响排盘） | 记录; 计算域契约不受影响; 列入开放问题 |
| F-3 | `ZIWEI_POS` 定局表与主流《紫微星诀》存在**系统性差异**: 水二局与主流一致（起丑, 两日一宫）; 木三局（现: 起寅两日一宫 vs 主流: 起辰三日一宫）、金四局（现: 起丑三日一宫 vs 主流: 起亥四日一宫）、土五局（现: 起丑三日一宫 vs 主流: 起午五日一宫）、火六局（现: 起丑四日一宫 vs 主流: 起酉六日一宫）均不一致 | **高（待裁定）** | **不修改代码**; 记录为内部歧义 A-1; 提出候选裁定（维持现状/ACP 修正） |
| F-4 | 廉贞偏移 `-9`（紫微星系表）vs 主流 `-8`（例: 紫微在子 → 现廉贞在卯, 主流廉贞在辰与天府同宫） | **高（待裁定）** | 同上, 歧义 A-2 |
| F-5 | SCHEMAS.md §3.2 勘误: `Palace` 列表含 `calendar_note`（实际位于 `ZiweiChart`）; 未标注 `extra="forbid"` 与 engine 版本 | 低（文档漂移） | 本 Sprint 修复（纯文档, 无行为变化） |
| F-6 | `gender` 接受但未使用; `yin_yang` 计算但未使用（四化/大限未实现时的占位字段） | 低 | ZW-017 冻结"未实现"为边界 |
| F-7 | 晚子时无换日逻辑: 农历日 = 本地民用日期（sxtwl）, 23:00 后不换日 —— 与 BaZi B3（23:00 换日）相反, 与 Qimen D14（不换日）巧合一致但未裁定 | 中 | ZB-01 跨域登记; 开放裁定 |
| F-8 | `sxtwl>=1.6` 非精确锁版; compute() 内唯一外部依赖; 升级可能改变农历转换 → replay 漂移风险 | 中 | ZW-004 开放裁定（建议契约化时精确锁版 + 历法数值向量 3 例已锁行为） |
| F-9 | 测试注释与实现不符（`test_fate_palace_canonical` 注释称"甲年", 实际立春前 1900 年为己亥）—— 不影响断言, 属文档漂移 | 低 | 记录; 新测试中以实际值为准 |
| F-10 | 用户显式农历（lunar_month/lunar_day）优先于公历, 但年干仍取自公历立春界（两条时间语义并存） | 低 | ZW-001 行为锁定测试已补（见 COVERAGE §6） |
| F-11 | 五行局全 5 类型此前仅水二局有测试; 本 Sprint 用真实日期锚点补齐 5 局断言（2024-01-01 水二 / 2024-06-06 木三 / 2024-10-03 金四 / 2024-08-04 土五 / 2024-02-05 火六, 均为 sxtwl 真实转换, 非构造） | 中（已闭合） | 已补测试, 见 §3 |

---

## 3. 本 Sprint 允许范围内的动作清单

| 动作 | 是否执行 | 依据 |
|------|----------|------|
| 修改生产算法 | ❌ | Sprint 约束（先测量, 再修改） |
| 新增确定性测试（锁定当前行为） | ✅ | Step 10; `tests/test_ziwei.py` +21 例（12 → 33） |
| 修复 SCHEMAS.md §3.2 勘误 | ✅ | Step 8（纯文档, 无行为变化） |
| 冻结契约 / 生成 normative 向量 | ❌ | 禁制清单 |
| 创建 `reference/ziwei/` | ❌ | 禁制清单（Phase 6.7.2 之后） |
| 升级 Ziwei 状态 | ❌ | 保持 **Implemented** |

---

## 4. 结论

- Ziwei 计算层 = **Implemented**, 实质满足 Stage 1（确定性 + 领域 Schema +
  测试）。与 Phase 7.0 评估结论一致。
- 本轮审计新增 11 项发现, 其中 **F-1/F-2（格局链路断裂, 解释域）** 与
  **F-3/F-4（定局表/廉贞与主流差异, 计算域）** 为最高优先级开放裁定项。
- 计算域规则稳定性: 17 条规则中 12 条直接 Freeze Candidate, 2 条带注记,
  3 条 Deferred（见 `ZIWEI_RULE_DECISION.md`）。
