# Ziwei Reference Audit

> **Sprint**: Phase 6.7.4 — Reference Certification
> **日期**: 2026-08-13
> **对象**: `reference/ziwei/`（tables / astronomy / domain）
> **基准**: `docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT_DRAFT.md`（BC-001~014）+
> `docs/ziwei/golden_vectors.json`（24, Engine v0.3.0）
> **性质**: 逐条审计契约条款 vs Reference 行为; 确认无 src 导入、无额外
> 默认值/回退、输入输出字段与契约一致。

---

## 审计结论

| Clause | Contract Requirement | Reference Behavior | Evidence | Verdict |
|--------|----------------------|--------------------|----------|---------|
| BC-001 | 确定性输出（纯函数, 无随机/时钟/I-O/LLM） | `compute()` 为输入纯函数; 无全局可变状态 | `test_determinism_reference`（24/24 双重运行一致） | **PASS** |
| BC-002 | 输入 Schema + 校验（month∈[1,12], day∈[1,30], 同给同省, ValueError） | `ZiweiReferenceInput`（pydantic, `extra="forbid"`）+ `model_validator` 三项校验; born_at 必须 tz-aware | 24 向量输入全量重放通过; `test_24_golden_vectors_equivalent` | **PASS** |
| BC-003 | 时区两级链（location.tz → born_at.tzinfo, 静默, 无 UTC 兜底） | `_local_tz`: ZoneInfo 失败 → 回退 `born_at.tzinfo`; 无警告 | ZV-tz-003（Invalid/Zone）== ZV-tz-001 输出一致 | **PASS** |
| BC-004 | 时辰分支 `((hour+1)//2)%12`, 子时 23:00~00:59, 钟表时 | `_hour_branch` 同公式; 无真太阳时 | ZV-hour-001（22:59 亥）/ 002（23:00 子, 命宫差 1）/ lun-005（23:30 子） | **PASS** |
| BC-005 | 农历转换 sxtwl==2.0.7, 本地民用日期, 晚子时不换日, 闰月同值 + calendar_note | `solar_to_lunar`（sxtwl 直接调用, 独立封装）; 闰月字符串逐字节一致 | ZV-lun-001（3/23）/ 002（春节）/ 003（闰二月 note）/ 005（23:30 同日） | **PASS** |
| BC-006 | 年干立春界, 引用 BaZi 原语 | `bazi_year_index` 自 `reference/bazi/astronomy.py`（显式引用, 引用非重复实现） | ZV-lun-004（立春后 1h → 甲辰 yang） | **PASS** |
| BC-007 | 五虎遁 `(year_stem_idx*2+2)%10` | 同公式; 干支表自 `reference/bazi/tables.py`（显式引用） | 全部向量十二宫干支一致 | **PASS** |
| BC-008 | 命宫 `((m-1)-h)%12` / 身宫 `((m-1)+h)%12` | 同公式 | ZV-ref-001（命宫子/身宫辰）; 全部向量 | **PASS** |
| BC-009 | 命宫天干 + 五行局（纳音末字 → `{元素}{数}局`） | `nayin_for`（reference/bazi）→ 末字 → `JU_NUMBER`; 局名格式一致 | ZV-ju-001~005（5 局全类型）; ZV-ref-001（水2局） | **PASS** |
| BC-010 | 十二宫布局（宫名/地支/干, 命身标志） | `PALACE_BRANCHES`/`PALACE_NAMES` 显式定义于 `reference/ziwei/tables.py` | ZV-ref-001~004 全盘 12 宫一致 | **PASS** |
| BC-011 | 紫微定局生成式 `(START[ju]+(day-1)//STEP[ju])%12` | `ziwei_index`（tables.py 显式 START/STEP 表） | ZV-ju-001~005 / ZV-pos-001~004 / ZV-inv-001（A-1 公式对齐） | **PASS** |
| BC-012 | 天府镜像 `(-zw)%12` + 紫微星系（廉贞 -8）/天府星系偏移; 14 星各一次 | 同公式; 星系偏移表显式定义于 tables.py; 紫微星系先、天府星系后的追加顺序与 Production 一致 | 全部向量 14 星断言; ZV-inv-001（紫微在子, 廉贞天府同度辰, A-2） | **PASS** |
| BC-013 | 阴阳标记 + 能力边界（aux 恒空, gender 不读） | `yin_yang` 按年干阴阳表; `auxiliary_stars` 恒空; engine 全文无 `gender` 读取 | ZV-ref-002（yin）/ ZV-lun-004（yang）; 全部向量 aux 空 | **PASS** |
| BC-014 | 24 Golden Vectors 为规范回归装置 | 24/24 逐字节等价（Reference 输出 == expected chart） | `test_24_golden_vectors_equivalent` | **PASS** |

**汇总: 14/14 PASS。**

---

## 独立性确认（审计要求逐项）

1. **无 src 导入**: `reference/ziwei/` 源码扫描零匹配 `openmetaphysics`;
   干净子进程运行时验证 `sys.modules` 不含任何 src 模块
   （`test_reference_independent_of_production`）。
2. **共享原语显式引用**（契约允许, 已明确标注）:
   - `reference/bazi/astronomy.py::bazi_year_index`（BC-006 立春界）
   - `reference/bazi/tables.py::HEAVENLY_STEMS / STEM_YIN_YANG / NAYIN / nayin_for`
     （BC-007/009 干支纳音）
   - `sxtwl==2.0.7`（外部依赖, BC-005 精确 pin, 独立封装于 `astronomy.py`）
3. **无 Production 额外默认值/回退**: 输入默认值（gender="unknown",
   locale="zh-CN"）与 Production `AgentInput` 缺省一致; 时区回退为契约
   BC-003 规定的两级链, 无第三级 UTC 兜底; born_at naive → ValueError
   （与 Production schema 校验语义一致, 非新增行为）。
4. **输入/输出字段与契约一致**: 输出 chart 字段集
   `fate_palace_index / body_palace_index / yin_yang / wuxing_ju /
   palaces[12]（index/name/earthly_branch/heavenly_stem/main_stars/
   auxiliary_stars/is_fate_palace/is_body_palace）/ calendar_note`
   与 BC-013 Schema 定义逐字段对应; 无多余字段。
5. **中间计算步骤与契约一致**: 步骤链
   时区 → 时辰 → 农历 → 命/身宫 → 年干 → 五虎遁 → 阴阳 → 命宫干支 →
   纳音 → 五行局 → 十二宫 → 紫微定局 → 天府镜像 → 双星系安星,
   与 BC-003~013 定义一一对应（见上表逐条）。

---

## 验证记录

| 检查 | 结果 |
|------|------|
| `uv run pytest`（全量, 含 4 例新增等价测试） | ✅ **589/589 全绿**（585 + 4） |
| `uv run ruff check reference/ziwei reference/tests/test_ziwei_equivalence.py` | ✅ 通过 |
| `uv run ruff format --check` | ✅ 通过 |
| `git diff -- src/` | ✅ 空（未修改 Production） |
| `git diff -- docs/qimen/ docs/bazi/` | ✅ 空 |
| `git diff -- docs/governance/CAPABILITY_LIFECYCLE.md` | ✅ 空 |
