# 概念：盘面模型（Board）

> 契约条款: [QC-001](../../../docs/specification/QIMEN_BEHAVIOR_CONTRACT.md) / QC-002
> 流派记录: [schools.md](schools.md)

## 定义

奇门盘 = 洛书九宫 + 各宫叠置的多层符号。输入 `QimenInput`（born_at +
born_location），输出 `QimenBoard`。

## 九宫（洛书序）

| 宫位 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|------|---|---|---|---|---|---|---|---|---|
| 宫名 | 坎 | 坤 | 震 | 巽 | 中宫 | 乾 | 兑 | 艮 | 离 |
| 后天八卦 | 北 | 西南 | 东 | 东南 | — | 西北 | 西 | 东北 | 南 |

## 每宫字段（Schema §3.3，冻结）

- `palace` 1..9 唯一；`name` 宫名
- `sky_plate` 天盘干 / `earth_plate` 地盘干
- `eight_gods` / `nine_stars` / `eight_doors`（天盘后状态）
- `three_qi` 三奇落宫（乙丙丁 各恰一宫）
- `is_void` 空亡 / `is_central` 中宫

## 规范不变量

1. 恒 9 宫，palace 1..9 无遗漏无重复（QC-002）
2. 仅 palace 5 `is_central=True`
3. 中宫无八门八神；非中宫满布
4. 天盘干/地盘干/九星各 9 个互异；八门/八神各 8 个互异
5. 三奇恰 3 宫，集合 {乙丙丁}

## 可观察输出

`QimenBoard.model_dump(mode="json")` 键序稳定：
`solar_term, ju, dun_type, day_of_month, triple_offset, cells`；
cell 键序：`palace, name, sky_plate, earth_plate, eight_gods,
nine_stars, eight_doors, three_qi, is_void, is_central`。
