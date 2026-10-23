# Liuyao Rule Inventory（六爻规则清单）

> **状态**: **FROZEN**（2026-10-23，ACP-LIUYAO-001）· **日期**: 2026-09-16 · **阶段**: Phase B 契约化
> **来源**: `src/openmetaphysics/agents/liuyao.py`（既有实现，未做算法改动）
> **Reference**: `reference/liuyao/domain.py`
> **Golden Vectors**: `docs/liuyao/golden_vectors.json`（25 条）

本清单只记录**现有实现已经具备的行为**，不设计新行为。每条的"依据"是既有代码位置。

---

## 1. 已实现规则（FROZEN）

| ID | 规则 | 实现 | Golden Vector 覆盖 |
|----|------|------|-------------------|
| **LY-01** | **掷卦获取**：显式 `casts` 优先；否则三次投币（每爻 3 枚、每枚 2 或 3）求和，值域 6..9 | `_casts` | LY_norm_006（显式 seed） |
| **LY-02** | **本卦爻性**：`6/8 → 阴`，`7/9 → 阳`；`6/9 → 动爻` | `_yao` | 全部 normal |
| **LY-03** | **变卦**：动爻翻转（`9→8` 阳变阴、`6→7` 阴变阳），稳定爻保持；无动爻时 `changed_hexagram = null` | `_changed_yao` | LY_norm_003/004/007，LY_norm_010（null） |
| **LY-04** | **互卦**：下卦取第 2/3/4 爻、上卦取第 3/4/5 爻，强制稳定（恒存在） | `calculate` | LY_edge_005 |
| **LY-05** | **卦序识别**：内外卦 → King Wen 卦号 1..64 | `hexagram_from_lines` | 全部 normal |
| **LY-06** | **八宫**：京房八宫表（宫名 + 宫内序号 1..8） | `_PALACE_OF`/`_PALACE_POS` | 全部 normal |
| **LY-07** | **世应**：世 = `SHI_BY_POS[宫内序号]`；应 = `((世+2) mod 6)+1` | `SHI_BY_POS` | 全部 normal |
| **LY-08** | **纳甲**：按内外卦的天干表 + 阴阳爻位取地支 | `NAJIA_STEM`/`_najia_branch` | LY_norm_001/002 |
| **LY-09** | **六亲**：宫五行 与 地支五行 的关系 → 兄弟/子孙/父母/妻财/官鬼 | `LIU_QIN_BY_RELATION` | LY_norm_001/002 |
| **LY-10** | **六神**：由**日干**（`sexagenary_day_index % 10`，含 **23:00 换日**）定起始六神，顺序循环 | `SPIRIT_START_BY_STEM` | LY_edge_006，LY_bound_001~005 |
| **LY-11** | **用神**：问题关键词命中规则表 → 六亲；无问题或无命中 → `世爻` | `YONG_SHEN_RULES` | LY_norm_008/009，LY_edge_001~004 |

## 2. 输入校验（既有，属契约前置）

| ID | 规则 | 行为 |
|----|------|------|
| **LY-V01** | `casts` 必须恰好 6 个（bottom→top） | `ValueError: casts must have exactly 6 values (bottom->top)` |
| **LY-V02** | 每个 cast 值必须 ∈ {6,7,8,9} | `ValueError: each cast value must be 6,7,8 or 9` |
| **LY-V03** | `born_at` 必须时区感知 | pydantic `born_at must be timezone-aware` |

## 3. 已知边界（契约承认的未实现范围）

| ID | 边界 | 说明 |
|----|------|------|
| **LY-D01** | 无卦辞/爻辞文本 | 输出只有结构化字段，不含经文引文 |
| **LY-D02** | 无应期/旺衰/月建日辰 | 未实现传统断卦的旺衰与应期推算 |
| **LY-D03** | 六神取**日干**而非日支 | 依现行实现 |
| **LY-D04** | 自动 seed 跨进程不可复现 | `derive_seed` 使用 `hash((request_id, client_nonce))`，受 `PYTHONHASHSEED` 影响；**显式 `seed` 或显式 `casts` 可复现** |
| **LY-D05** | 互卦不参与变卦判定 | 互卦恒为稳定爻 |

## 4. Golden Vector 覆盖矩阵

| 类别 | 数量 | 说明 |
|------|------|------|
| normal | 10 | 乾坤稳定/全动/老阴、混合动爻、单动爻、seed 掷卦、用神关键词 |
| edge | 6 | 无用神默认、多关键词、出行/考试、互卦、22:00 不换日 |
| boundary | 5 | 23:00 与 23:30 换日、00:00、闰日 2024-02-29、跨年 2023-12-31T23:59 |
| invalid | 4 | 5 爻、cast=5、cast=10、tz-naive `born_at` |

## 5. 与 Production 的关系

- **Reference**: `reference/liuyao/domain.py`（自包含，不导入 `openmetaphysics`）
- **等价证明**: `reference/tests/test_liuyao_equivalence.py`（25 向量中 21 条合法路径 + 4 条拒绝路径 + 40 生成输入 + 换日边界 + 表一致性）
- **生产回归**: `tests/test_liuyao_golden_vectors.py`
