# Ziwei Decision Resolution

> **Sprint**: Phase 6.7.1.5 — Ziwei Decision Resolution（纯决策 Sprint）
> **日期**: 2026-08-13
> **性质**: 解决 Phase 6.7.1 遗留的 4 项决策点（A-1 / A-2 / ZW-001 / sxtwl 锁版）。
> 本 Sprint **不生成代码、不修改 src/、不创建 Contract、不生成 Golden
> Vectors、不执行任何 ACP** —— 仅产出裁定记录。
> **输入工件**: `ZIWEI_ALGORITHM_AUDIT.md` / `ZIWEI_ALGORITHM_ASSUMPTIONS.md` /
> `ZIWEI_RULE_DECISION.md` / `ZIWEI_GOLDEN_VECTOR_READINESS.md` /
> `tests/test_ziwei.py`（33 例）。
> **更正**: 任务书将 A-2 标注为"廉贞 -9（天府星系）"—— 廉贞属**紫微星系**
> （天府星系为太阴/贪狼/巨门/天相/天梁/七杀/破军）。裁定按紫微星系处理。

---

## 1. Executive Summary

| # | 决策点 | Decision | 修改 src/? | ACP Required | 本 Sprint 执行 ACP |
|---|--------|----------|-----------|--------------|--------------------|
| A-1 | ZW-012 定局表 | **REVISED**（统一生成规则, 5 行全替换） | YES | **YES** | NO |
| A-2 | ZW-014 廉贞偏移 | **REVISED**（-9 → **-8**） | YES | **YES** | NO |
| ZW-001 | 输入校验策略 | **分层裁定**（Contract 要求显式校验; 当前实现"待修复"） | YES | **YES** | NO |
| sxtwl | 历法版本锁定 | **固定版本** `sxtwl==2.0.7` | pyproject only | **YES**（pin 动作） | NO |

**结论**: 4 项决策全部裁定为需要 ACP 的修订; **本 Sprint 不执行任何 ACP**。
Phase 6.7.2（Golden Vector Generation）**必须等待 ACP 执行完成后**才能基于
修订后的规则集生成向量; 在此之前不得生成任何全盘向量。

**现状核查**: Phase 6.7.1 已合并 main（commit `1c3e2f7`）; 环境实测
`sxtwl==2.0.7`（pyproject 声明 `>=1.6`）。

---

## 2. A-1 裁定记录（ZW-012 定局表）

```text
ZW-012
Decision: REVISED
Chosen rule: 紫微定位 = 统一生成规则 (start + (day-1)//step) % 12, 5 行全替换:
  水二局: start=丑(11), step=2  → 初一初二丑, 初三初四寅, …, 廿九三十卯
  木三局: start=辰(2),  step=3  → 初一~初三辰, 初四~初六巳, …, 廿八~三十丑
  金四局: start=亥(9),  step=3  → 初一~初三亥, 初四~初六子, …, 廿八~三十申
  土五局: start=午(4),  step=3  → 初一~初三午, 初四~初六未, …, 廿八~三十卯
  火六局: start=酉(7),  step=3  → 初一~初三酉, 初四~初六戌, …, 廿八~三十午
Rationale: 结构证据, 非"传统一般认为":
  (1) 当前表无统一生成规则（起宫/步长组合 丑2/寅2/丑3/丑3/丑4, 各局访问宫数
      12/12/11/11/8, 无模式）; 修订规则为单一生成式, 访问宫数 12/10/10/10/10。
  (2) 著名结构不变式（紫微速见表性质）: 木三局紫微不落寅卯、金四局不落酉戌、
      土五局不落辰巳、火六局不落未申 —— 修订规则全部满足; 当前表全部违反
      （木三 day1-2 紫微落寅; 金四/土五/火六 无缺对模式）。
  (3) 当前表异常模式与生成错误特征一致: 木三起寅（= 数组默认 index 0）;
      金四/土五/火六起丑（= 复制水二局起宫）; 步长 = ju-1（系统性 off-by-one）;
      水二局"初一独在丑"是统一规则的 +1 日错位。
  (4) 结合 A-2（廉贞 -8）: 著名恒等式"紫微在子午, 廉贞天府同度辰戌"仅在
      修订规则下可恢复（见 §3）。
Alternative rejected: 维持现状（当前表作为规范）—— 违反四项著名结构不变式
  (2), 且无任何已知流派对应; 冻结它将使全部全盘向量承载系统性错位。
Compatibility impact: 修改 src/openmetaphysics/agents/ziwei.py 的 ZIWEI_POS
  表（建议改为生成函数, 消除 150 值硬编码）。测试影响（已逐条核查）:
  - 需随 ACP 迁移: test_ziwei_pos_values_snapshot（SHA-256 快照重生成）;
  - 自动一致无需改: test_ziwei_pos_table_structure（结构断言）/
    test_ziwei_tianfu_mirror_multiple_ju / test_user_lunar_override_flows_into_placement
    （读同一模块表）; test_fate_palace_canonical（day1 水二局→丑, 不变）;
  - 与表无关不受影响: 命宫/身宫 sweep、五行局锚点、时区、时辰窗、双星系偏移
    （公式类）、序列化。
ACP required: YES（本 Sprint 不执行）
```

### 修订后表定义（规范性候选, ACP 执行依据）

| 局 | 起宫 | 步长（日/宫） | 30 日访问宫序列（索引 0..11, 寅=0） | 不落宫 |
|----|------|---------------|--------------------------------------|--------|
| 水二局 | 丑(11) | 2 | 丑丑寅寅卯卯辰辰巳巳午午未未申申酉酉戌戌亥亥子子丑丑寅寅卯卯 | （无, 遍十二宫） |
| 木三局 | 辰(2) | 3 | 辰辰辰巳巳巳午午午未未未申申申酉酉酉戌戌戌亥亥亥子子子丑丑丑 | 寅卯 |
| 金四局 | 亥(9) | 3 | 亥亥亥子子子丑丑丑寅寅寅卯卯卯辰辰辰巳巳巳午午午未未未申申申 | 酉戌 |
| 土五局 | 午(4) | 3 | 午午午未未未申申申酉酉酉戌戌戌亥亥亥子子子丑丑丑寅寅寅卯卯卯 | 辰巳 |
| 火六局 | 酉(7) | 3 | 酉酉酉戌戌戌亥亥亥子子子丑丑丑寅寅寅卯卯卯辰辰辰巳巳巳午午午 | 未申 |

公式: `idx = (START + (lunar_day - 1) // STEP) % 12`, START/STEP 如上表。
（数值结构已在本 Sprint 用脚本独立验证, 见验证节。）

---

## 3. A-2 裁定记录（ZW-014 廉贞偏移）

```text
ZW-014
Decision: REVISED
Chosen offset: -8（紫微星系: 紫微0 / 天机-1 / 太阳-3 / 武曲-4 / 天同-5 / 廉贞-8）
Rationale:
  (1) 歌诀结构: "紫微天机逆行旁, 隔一阳武天同居, 又隔二位廉贞地" —— 天机(1)
      之后隔一宫为太阳(3); 天同(5) 之后隔二宫为廉贞(8)。-8 与歌诀逐宫吻合,
      -9 多隔一宫。
  (2) 著名同宫恒等式: 紫微在子 → 天府在辰（镜像）; 廉贞 -8 时廉贞亦在辰,
      即"廉贞天府同度于辰"（紫微在午 → 同度于戌）。-9 时廉贞落卯, 恒等式
      破坏。该恒等式是与 A-1 修订表相互独立的验证点。
  (3) 本项目规范定义为 -8, 而非历史原因: 当前 -9 与任何已知流派歌诀均不符,
      属偏移值录入/推导误差; 天府星系八星（ZW-015）与主流完全一致, 同源
      紫微星系亦应对齐同源规范。
Alternative rejected: 维持 -9 —— 无歌诀/恒等式支持, 且与 A-1 修订后规则
  组合时无法满足廉贞天府同宫恒等式。
Compatibility impact: 修改 src/openmetaphysics/agents/ziwei.py 的 ZIWEI_XINGXI
  表一值（廉贞 -9 → -8）。测试影响:
  - test_ziwei_xingxi_offsets（公式断言, 读同一模块表）自动一致;
  - 无其他测试硬编码廉贞绝对位置。
ACP required: YES（本 Sprint 不执行）
```

---

## 4. ZW-001 分层裁定记录（输入校验）

```text
ZW-001
Layer separation:
  - Contract requirement（领域规范层）:
      1. lunar_month ∈ [1,12], lunar_day ∈ [1,30]（显式提供时）;
      2. 两字段必须同时提供或同时省略; 部分提供 → 校验拒绝（422 语义）;
      3. born_at 必须 tz-aware（既有信封契约, 已实现）;
      4. 显式农历与公历不一致: 合法（重放特性）, 不做一致性校验;
      5. 越界输入 → 明确校验错误（ValueError/422）, 不得以 KeyError 形式
         从查表底层意外泄漏。
  - Implementation behavior（当前工程实现）:
      1. 无任何显式范围校验;
      2. lunar_day 越界 → ZIWEI_POS[ju][day] KeyError（意外行为, 非设计错误）;
      3. lunar_month 越界 → 公式静默回绕（比 KeyError 更隐蔽, 输出错误盘）;
      4. 部分提供（仅 month 或仅 day）→ 静默走公历转换路径（另一隐蔽行为）。
Decision: KeyError 属工程实现意外, 不是领域规范。Contract 层要求显式校验;
  当前实现不满足 Contract 要求 → 记为"待修复"（REVISED）; 修复 = 在
  ZiweiInput 增加字段校验器, 行为变化仅限非法输入路径, 合法输入输出不变。
Modification required: YES（ACP 时执行; 本 Sprint 不修改 src/）
  随 ACP 迁移: test_lunar_day_out_of_range_raises_keyerror
  → test_lunar_day_out_of_range_rejected（断言 ValueError 语义）。
```

---

## 5. sxtwl 锁版策略裁定

```text
sxtwl Locking Strategy
Decision: 固定版本（精确 pin）
Chosen version/range: sxtwl==2.0.7（环境实测安装版本; pyproject 当前声明 >=1.6）
Verification method: 既有 3 例历法数值测试（test_lunar_conversion_2024_05_01 /
  2024_02_10 / leap_month_2023, 已锁定 2.0.7 输出）+ replay 测试 +
  Phase 6.7.2 历法向量（ZV-lun-001~003）生成后纳入机器回归。
Rationale:
  (1) sxtwl 是 compute() 路径内唯一外部依赖, 农历输出直接进入命宫/五行局/
      定局计算 —— 任何版本变动都可能静默改变排盘结果;
  (2) 范围声明已跨越大版本（>=1.6 已解析到 2.0.7）—— 范围策略在该依赖上
      无法提供确定性保障;
  (3) 精确 pin + 历法向量回归 = 唯一可审计的确定性契约; 未来升级须
      ACP + 向量迁移 + 全量回归。
  本 Sprint 不修改 pyproject.toml（pin 动作随 ACP 执行）。
ACP required: YES（pin 动作, 不改运行时行为）
```

---

## 6. Phase 6.7.2 入口条件声明

1. **规则集状态**: 17 条规则中 14 条 Freeze Candidate（ZW-002~011/013/015/016/017,
   其中 ZW-002/004 带注记）+ 3 条 REVISED（ZW-001/012/014）;
   FROZEN 仍需 Phase 6.7.3 Freeze Review。
2. **ACP 前置（硬性）**: 3 项行为 ACP（ZW-012 表替换、ZW-014 廉贞 -8、
   ZW-001 校验）+ 1 项依赖 ACP（sxtwl pin）**必须在向量生成前执行**。
3. **测试锁定状态**: 14 条 Freeze Candidate 规则均已被确定性测试锁定
   （详见 ZIWEI_TEST_COVERAGE_REVIEW §5）; 3 条 REVISED 规则的修订后行为
   由"公式类测试自动一致 + 快照/KeyError 测试随 ACP 迁移"覆盖。
4. **向量生成**: 可在 ACP 执行完成后启动, **必须基于修订后规则集**
   （修正定局表 + 廉贞 -8）; ZV-pos 组向量按修订表生成; 全盘向量
   （ZV-ref/ZV-ju）须在 ACP 后重新采样记录。
5. 本 Sprint 不升级 Ziwei 状态（保持 **Implemented**）; 不创建 Contract /
   Golden Vectors / `reference/ziwei/`。

---

## 7. 验证（数值独立复核, 非 src 修改）

| 验证项 | 结果 |
|--------|------|
| 修订表访问宫数 | 水二 12 / 木三 10 / 金四 10 / 土五 10 / 火六 10 ✓ |
| 不落宫不变式 | 木三无寅卯 / 金四无酉戌 / 土五无辰巳 / 火六无未申 ✓ |
| 当前表访问宫数 | 12/12/11/11/8（无模式, 违反全部不变式）✗ |
| 廉贞 -8 恒等式 | 紫微在子 → 廉贞在辰 = 天府在辰（同宫）✓; -9 → 廉贞在卯 ✗ |
| sxtwl 环境版本 | 2.0.7（`uv pip show sxtwl`） |
| pytest | 578/578 全绿（本 Sprint 不新增/修改测试） |
| ruff check / format --check | 通过 |
| ZERO TOUCH | Qimen / BaZi / Framework / src/ diff 全空 |

---

## 8. 约束合规声明

- ✅ 未修改 src/（4 项 ACP 仅记录, 未执行）
- ✅ 未创建 Contract / Golden Vectors / `reference/ziwei/`
- ✅ 未修改 Qimen / BaZi / Framework
- ✅ 未引入 LLM / RAG / 解释层
- ✅ Ziwei 状态保持 **Implemented**
- ✅ 本 Sprint 仅文档更新（`docs/governance/ziwei/**` + CAPABILITY_STATUS 节 +
  context 归档）
