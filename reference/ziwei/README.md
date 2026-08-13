# Reference Ziwei

独立实现 `docs/ziwei/ZIWEI_BEHAVIOR_CONTRACT_DRAFT.md`（BC-001~014,
Engine v0.3.0 行为）的规范性 Reference。

> **性质**: 行为规范层。**禁止导入 `src/openmetaphysics` 任何模块**；
> 共享历法/干支/纳音基础设施显式复用 `reference/bazi/*`（引用而非重复实现）。

## 模块

| 模块 | 契约条款 | 职责 |
|------|----------|------|
| `tables.py` | BC-009/010/011/012 | Ziwei 规范表：十二宫（宫名/地支）、五行局、紫微定局 START/STEP 生成式、紫微星系（廉贞 -8）/天府星系偏移；共享干支/纳音表从 `reference/bazi/tables.py` 引用 |
| `astronomy.py` | BC-005 | 农历转换（`sxtwl==2.0.7` 精确锁定, 闰月同值） |
| `domain.py` | BC-001~014 | 参考引擎：输入 Schema + 校验（BC-002）、时区两级链（BC-003）、时辰分支（BC-004）、命/身宫（BC-008）、五行局（BC-009）、十二宫（BC-010）、紫微定局（BC-011）、天府镜像 + 双星系（BC-012）、阴阳/边界（BC-013） |

## 验证

- `reference/tests/test_ziwei_equivalence.py`（4 例）:
  - 24/24 Golden Vector 等价（Reference 输出 == expected chart）
  - 独立性（源扫描 + 干净子进程运行时检查, 无 src 导入）
  - Determinism / 序列化稳定

## 复用引用

| 原语 | 来源 | 条款 |
|------|------|------|
| 年干立春界 `bazi_year_index` | `reference/bazi/astronomy.py` | BC-006（引用 BaZi 原语） |
| 天干/阴阳/纳音表 `HEAVENLY_STEMS`/`STEM_YIN_YANG`/`NAYIN`/`nayin_for` | `reference/bazi/tables.py` | BC-007/009（共享基础设施, 显式引用） |
