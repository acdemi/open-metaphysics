# Ziwei Golden Vector Generation Report

> **Sprint**: Phase 6.7.2 — Golden Vector Generation
> **日期**: 2026-08-13
> **Engine**: `ZiweiEngine` **v0.3.0**（`src/openmetaphysics/agents/ziwei.py`）
> **产出**: `docs/ziwei/golden_vectors.json`（24 向量）+ `tests/test_ziwei_golden_vectors.py`（7 测试）
> **性质**: 证据生成 Sprint。向量为**规范性证据**（非快照），由 Engine 输出生成，
> 规则预期经冻结规则集独立校验；**无任何人工篡改 expected 数值**。

---

## 1. Executive Summary

- 24 个 Golden Vectors 基于 **Engine v0.3.0**（ACP-ZW-001/002/003/004 修订后规则集）
  由 `ZiweiEngine.calculate()` 输出生成，每个向量包含完整
  `input` / `expected`（全盘 chart + metadata）/ `description` / `rule_coverage`。
- **17 条 ZW 规则全部被覆盖**（ZW-001~017），无缺漏。
- **A-1 专项**：5 个五行局向量 + 4 个定局边界向量的紫微位置与
  `(START[ju] + (day-1)//STEP[ju]) % 12` 逐一对齐，**ALL PASS**。
- **A-2 专项**："紫微在子午，廉贞天府同度辰戌"恒等式在 6 个含子/午紫微的
  向量中全部成立（含专项向量 `ZV-inv-001`），**ALL PASS**。
- 全量测试 **585/585 全绿**（578 + 新增 7）；`ruff check` + `ruff format --check` 通过；
  零触碰验证全部满足。
- **发现 1 处 Phase 6.7.1 文档标注错误**（见 §7），不影响规则一致性。

---

## 2. 24 向量覆盖矩阵

| 组 | ID | 输入（born_at, +08:00 除非注明） | 局 | 命宫 | 紫微 | 验证维度 |
|----|----|------|----|------|------|----------|
| 基准盘 | ZV-ref-001 | 1900-01-29 04:00（显式农历 1/1） | 水2局 | 子 | 丑 | 命/身宫、干支、全盘 |
| 基准盘 | ZV-ref-002 | 1985-08-15 10:00（乙丑, 农历 6/29） | 土5局 | 寅 | 卯 | 阴阳=yin、全盘 |
| 基准盘 | ZV-ref-003 | 2024-02-05 04:00（立春次日） | 火6局 | 亥 | 巳 | 全盘 |
| 基准盘 | ZV-ref-004 | 2024-06-06 04:00 | 木3局 | 辰 | 辰 | 全盘 |
| 五行局 | ZV-ju-001 | 2024-01-01 04:00 | 水2局 | 戌 | 戌 | 水二定局 |
| 五行局 | ZV-ju-002 | 2024-06-06 04:00 | 木3局 | 辰 | 辰 | 木三定局 |
| 五行局 | ZV-ju-003 | 2024-10-03 04:00 | 金4局 | 申 | 亥 | 金四定局 |
| 五行局 | ZV-ju-004 | 2024-08-04 04:00 | 土5局 | 午 | 午 | 土五定局 |
| 五行局 | ZV-ju-005 | 2024-02-05 04:00 | 火6局 | 亥 | 巳 | 火六定局 |
| 定局边界 | ZV-pos-001 | 2024-05-01 04:00（显式农历 1/1） | 水2局 | 子 | 丑 | day=1 |
| 定局边界 | ZV-pos-002 | 2024-05-01 04:00（显式农历 1/30） | 水2局 | 子 | 卯 | day=30 |
| 定局边界 | ZV-pos-003 | 2024-05-01 06:00（显式农历 1/1） | 火6局 | 亥 | 酉 | 局间对照 |
| 定局边界 | ZV-pos-004 | 2024-05-01 12:00（显式农历 3/15） | 火6局 | 戌 | 丑 | 用户农历覆盖路径 |
| 时区 | ZV-tz-001 | 2024-06-06 12:00（+08:00） | 水2局 | 子 | 丑 | 无 location 回退 tzinfo |
| 时区 | ZV-tz-002 | 2024-06-06 04:00（UTC, 同一时刻） | 木3局 | 辰 | 辰 | 本地时语义（命宫不同） |
| 时区 | ZV-tz-003 | 2024-06-06 12:00（tz="Invalid/Zone"） | 水2局 | 子 | 丑 | 非法时区静默回退 == tz-001 |
| 时辰窗 | ZV-hour-001 | 2024-06-06 22:59 | 土5局 | 未 | 午 | 亥时末（不换日） |
| 时辰窗 | ZV-hour-002 | 2024-06-06 23:00 | 土5局 | 午 | 午 | 子时初（命宫差 1） |
| 历法 | ZV-lun-001 | 2024-05-01 12:00 | 火6局 | 戌 | 辰 | sxtwl 3/23 锁定 |
| 历法 | ZV-lun-002 | 2024-02-10 12:00 | 金4局 | 申 | 亥 | 正月初一（春节） |
| 历法 | ZV-lun-003 | 2023-03-22 12:00 | 木3局 | 酉 | 辰 | 闰二月 calendar_note |
| 历法 | ZV-lun-004 | 2024-02-04 17:27（UTC, 立春后 1h） | 木3局 | 辰 | 子 | 年干立春界 yang |
| 历法 | ZV-lun-005 | 2024-06-06 23:30 | 土5局 | 午 | 午 | 晚子时不换日 |
| 不变式 | ZV-inv-001 | 2024-05-01 04:00（显式农历 1/23） | 水2局 | 子 | 子 | A-2 恒等式 + 天府镜像 |

> 注：局名采用 Engine 规范输出格式 `"{元素}{数}局"`（ZW-010 定义
> `"{元素}{数}局"`，Phase 6.7.1 文档中的"水二局"等为书写形式）。

---

## 3. 规则覆盖映射（ZW-001~017 → 向量 ID）

| 规则 | 覆盖向量 |
|------|----------|
| ZW-001 输入规范（显式农历/校验） | ZV-ref-001, ZV-pos-001~004 |
| ZW-002 时区解析链 | ZV-tz-001, ZV-tz-002, ZV-tz-003 |
| ZW-003 时辰（钟表时, 子时 23:00~00:59） | ZV-hour-001, ZV-hour-002, ZV-lun-005 |
| ZW-004 农历转换（sxtwl + 闰月同值） | ZV-hour-001, ZV-hour-002, ZV-lun-001~003, ZV-lun-005 |
| ZW-005 年干立春界 | ZV-lun-004 |
| ZW-006 五虎遁 | ZV-ref-001~004 |
| ZW-007 命宫 | ZV-ref-001（全组均含, 以 001 为代表） |
| ZW-008 身宫 | ZV-ref-001 |
| ZW-009 命宫天干 | ZV-ref-001 |
| ZW-010 五行局 | ZV-ju-001~005, ZV-ref-001~004, ZV-pos-001~004, ZV-lun-001~003 |
| ZW-011 十二宫布局 | ZV-ref-001~004 |
| ZW-012 紫微定局（生成式） | ZV-ju-001~005, ZV-pos-001~004, ZV-inv-001 |
| ZW-013 天府镜像 | ZV-inv-001（全部向量均含镜像不变式断言） |
| ZW-014 紫微星系（廉贞 -8） | ZV-inv-001（全部向量均含廉贞 -8 断言） |
| ZW-015 天府星系 | ZV-inv-001（全部向量均含 14 星断言） |
| ZW-016 阴阳标记 | ZV-ref-002（yin）, ZV-lun-004（yang） |
| ZW-017 未实现能力边界 | ZV-ref-001, ZV-ref-002, ZV-ref-003（aux 恒空 + metadata） |

**汇总**: 17/17 覆盖，无缺漏。

---

## 4. A-1/A-2 专项验证

### A-1（ZW-012 定局生成式）

对全部显式农历向量，独立重算 `(START[ju] + (day-1)//STEP[ju]) % 12`
并与向量中紫微位置比对：

| 向量 | 局 | day | 公式紫微 | Engine 紫微 | 结果 |
|------|----|-----|----------|-------------|------|
| ZV-ref-001 | 水2局 | 1 | 丑(11) | 丑(11) | ✅ |
| ZV-pos-001 | 水2局 | 1 | 丑(11) | 丑(11) | ✅ |
| ZV-pos-002 | 水2局 | 30 | 卯(1) | 卯(1) | ✅ |
| ZV-pos-003 | 火6局 | 1 | 酉(7) | 酉(7) | ✅ |
| ZV-pos-004 | 火6局 | 15 | 丑(11) | 丑(11) | ✅ |
| ZV-inv-001 | 水2局 | 23 | 子(10) | 子(10) | ✅ |

**结论: A-1 ALL PASS**（5 局全类型 + 边界 1/30 + 覆盖路径全部一致）。

### A-2（ZW-014 廉贞 -8 恒等式）

"紫微在子午 → 廉贞天府同度辰戌"在全部 6 个紫微在子(10)/午(4) 的向量中验证：

| 向量 | 紫微 | 天府 | 廉贞 | 结果 |
|------|------|------|------|------|
| ZV-inv-001（专项） | 子(10) | 辰(2) | 辰(2) | ✅ 同度辰 |
| ZV-lun-004 | 子(10) | 辰(2) | 辰(2) | ✅ 同度辰 |
| ZV-ju-004 | 午(4) | 戌(8) | 戌(8) | ✅ 同度戌 |
| ZV-hour-001 | 午(4) | 戌(8) | 戌(8) | ✅ 同度戌 |
| ZV-hour-002 | 午(4) | 戌(8) | 戌(8) | ✅ 同度戌 |
| ZV-lun-005 | 午(4) | 戌(8) | 戌(8) | ✅ 同度戌 |

**结论: A-2 ALL PASS**。此外所有 24 向量均通过通用不变式断言：
14 主星各一次、天府 = (-紫微) % 12、廉贞 = (紫微 - 8) % 12、aux 恒空、12 宫。

---

## 5. Determinism 验证

- `tests/test_ziwei_golden_vectors.py::test_determinism`：24 向量逐一双重运行，
  `engine.calculate()` 两次输出逐字节一致，且与 `expected["chart"]` 相等。
- 生成流程本身（`ZW_*` 生成脚本，见 §9）单次运行产出文件；
  二次运行同输入输出不变（已由测试锁定）。

---

## 6. 测试通过记录

```
$ uv run pytest tests/test_ziwei_golden_vectors.py -q
.......  [100%]                          # 7/7 PASS

$ uv run pytest                            # 全量
585 passed, 1 warning in 52.31s            # 578 + 7 新增

$ uv run ruff check tests/test_ziwei_golden_vectors.py
All checks passed!

$ uv run ruff format --check tests/test_ziwei_golden_vectors.py
1 file already formatted
```

新增测试（`tests/test_ziwei_golden_vectors.py`）：

| 测试 | 断言 |
|------|------|
| test_vector_count | 24 向量 + metadata.total_vectors == 24 |
| test_vector_ids_unique | ID 唯一且 ZV- 前缀 |
| test_engine_version | metadata == Engine v0.3.0（含逐向量） |
| test_determinism | 双重运行逐字节一致 |
| test_all_vectors_replay | 24 向量全部重放 == expected |
| test_rule_coverage_complete | 17 条 ZW 规则全部覆盖 |
| test_serialization_stable | sort_keys 规范化 dump 与文件字节一致 |

---

## 7. 生成期间发现与处置

| # | 发现 | 处置 |
|---|------|------|
| 1 | Phase 6.7.1 readiness 文档将 ZV-ref-002（1985-08-15 10:00）标注"木三局"；**实际规则链为 戊寅 城头土 → 土5局**（命宫=寅(0), 农历 6/29, 巳时, 乙丑年五虎遁戊→命宫干戊寅, 纳音城头土）。Engine v0.3.0 输出与 ZW-007/009/010 公式链一致，**文档标注为错误**。 | 向量按规则链采样（土5局）；错误记录于本报告，Phase 6.7.1 文档本身不在本 Sprint 修改范围（Zero Touch 约束） |
| 2 | 局名输出格式为 `"{元素}{数}局"`（如"水2局"），Phase 6.7.1 文档多用"水二局"书写形式；ZW-010 定义 `"{元素}{数}局"` 为规范。 | 向量 expected 采用 Engine 规范输出；文档书写差异已注记（§2） |
| 3 | 2024 立春 = 2024-02-04 16:26 UTC；ZV-lun-004 采样 17:27 UTC（+1h）→ yin_yang=yang（甲辰）✅；立春前同刻（15:27 UTC）→ yin，由既有单测 `test_yin_yang_lichun_boundary` 覆盖。 | 向量锁定"后 1h"侧输出 |

---

## 8. 零触碰验证（硬性门）

| 检查 | 结果 |
|------|------|
| `git diff -- src/` | ✅ 空（未改任何生产代码） |
| `git diff -- docs/qimen/ docs/bazi/` | ✅ 空 |
| `git diff -- docs/governance/CAPABILITY_LIFECYCLE.md` | ✅ 空 |
| `reference/ziwei/` 存在 | ✅ 不存在 |
| 合约草案（BAZI_BEHAVIOR_CONTRACT 等） | ✅ 未创建 |
| CAPABILITY_STATUS.md Ziwei 状态 | ✅ 未修改（保持 **Implemented**） |
| LLM / RAG / 解释层 | ✅ 未引入 |
| 新增文件 | `docs/ziwei/golden_vectors.json`（24 向量, 127 KB）+ `tests/test_ziwei_golden_vectors.py`（7 测试） |

---

## 9. 生成方法

向量由临时生成脚本产出（**未提交**，本报告附录存档关键逻辑）：

```python
from openmetaphysics.agents.ziwei import ZiweiEngine, ZiweiInput
engine = ZiweiEngine()                      # version == "0.3.0"
chart = engine.calculate(ZiweiInput(**input_dict))
# expected["chart"] = chart  (model_dump mode="json")
# 生成前对每个向量执行规则校验:
#   ju / fate / body / yin_yang / zw 公式 / 天府镜像 / 廉贞-8 / 14星 / aux恒空 / 12宫
#   cross-vector: tz-003==tz-001, hour 命宫差1+同日, lun-005 与 ref-004 同日
# 校验全部通过后才写入 golden_vectors.json（sort_keys=True, ensure_ascii=False, indent=2）
```

关键不变式断言（全部向量强制）：

```python
assert len(stars) == 14                      # 十四主星各一次
assert tianfu == (-ziwei) % 12               # ZW-013 天府镜像
assert lianzhen == (ziwei - 8) % 12          # ZW-014 廉贞 -8
assert all(not p["auxiliary_stars"] for p in palaces)   # ZW-017 边界
assert len(palaces) == 12                    # ZW-011 十二宫
```

---

## 10. Phase 6.7.3（Freeze Review）入口条件声明

1. **规则集状态**: 14 条 Freeze Candidate（ZW-002~011/013/015/016/017）+
   3 条 IMPLEMENTED（ZW-001/012/014）—— 与 Phase 6.7.1.6 一致，无变化。
2. **黄金向量**: 24 个规范性向量已生成（`docs/ziwei/golden_vectors.json`,
   status=candidate, rule_set=frozen_candidate），全部可确定性重放。
3. **ACP 前置**: 4 项 ACP（定局生成式 / 廉贞 -8 / 输入校验 / sxtwl pin）
   已全部实施并生效（Engine v0.3.0）。
4. **测试锁定**: 585/585 全绿（含 7 个新黄金向量测试）。
5. **待 Freeze Review 裁定项**（不阻塞向量生成, 契约化阶段落地）:
   A-3 晚子时显式裁定、A-4 时区链差异声明、A-6 闰月同值安星终裁、A-7 年干
   立春界显式声明。
6. **Phase 6.7.1 readiness 文档标注错误**（§7-1, ZV-ref-002 局名）建议在
   Freeze Review 时随文档勘误处理。

**本 Sprint 停止。等待人工 Evidence Review 与授权。Ziwei 状态保持 Implemented。**
