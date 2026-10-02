# Liuyao Behavior Contract v1.0.0（候补）

> **状态**: **candidate**（Phase B 契约化产物，与 BaZi / Ziwei / Qimen 同级形态）
> **范围**: 六爻（Liuyao）域的可观测行为
> **依据**: `docs/liuyao/LIUYAO_RULE_INVENTORY.md`（LY-01~LY-11）+ `src/openmetaphysics/agents/liuyao.py`
> **Reference**: `reference/liuyao/domain.py`（自包含）
> **Golden Vectors**: `docs/liuyao/golden_vectors.json`（24，normative fixtures）
> **Engine version**: 0.1.0

本契约**不引入新行为**；全部条款均可回指既有实现与既有输出。

---

## 1. 输入契约

| ID | 条款 | 级别 |
|----|------|------|
| **LC-001** | `LiuyaoInput.casts` 若提供，**必须**恰好 6 个整数值，顺序为自下而上（初爻→上爻） | MUST |
| **LC-002** | 每个 cast 值 **必须** ∈ {6, 7, 8, 9}；违反时 **必须** 以 `ValueError` 拒绝 | MUST |
| **LC-003** | `born_at` **必须**时区感知 | MUST |
| **LC-004** | `casts` 缺省时，**必须**由确定性 RNG 以显式 `seed` 生成 6 个 6..9 的值；同一 `seed` **必须**产生同一结果 | MUST |

## 2. 结构契约（本卦 / 变卦 / 互卦）

| ID | 条款 | 级别 |
|----|------|------|
| **LC-010** | `original` **必须**含 6 爻，`position` 1..6 自下而上 | MUST |
| **LC-011** | 爻性：cast ∈ {6,8} → `is_yin=true`；cast ∈ {7,9} → `is_yin=false` | MUST |
| **LC-012** | 动爻：cast ∈ {6,9} → `is_changing=true`，且仅在本卦成立 | MUST |
| **LC-013** | `changed` **必须**为 6 爻：动爻翻转为稳定爻（9→8，6→7），稳定爻不变 | MUST |
| **LC-014** | `changed_hexagram` **必须**仅在存在动爻时给出；无动爻时为 `null` | MUST |
| **LC-015** | `mutual` **必须**含 6 爻：下卦取第 2/3/4 爻、上卦取第 3/4/5 爻，且全部为稳定爻 | MUST |
| **LC-016** | `mutual_hexagram` **必须**恒存在 | MUST |

## 3. 卦序与宫位

| ID | 条款 | 级别 |
|----|------|------|
| **LC-020** | `original_hexagram` **必须**为 King Wen 卦号 1..64 | MUST |
| **LC-021** | `changed_hexagram` / `mutual_hexagram` 若存在，**必须**为 1..64 | MUST |
| **LC-022** | `palace` **必须**为京房八宫之一（乾坎艮震巽离坤兑） | MUST |
| **LC-023** | `palace_element` **必须**为 `palace` 对应卦五行 | MUST |
| **LC-024** | `shi_position` ∈ 1..6，由宫内序号依 `SHI_BY_POS` 决定 | MUST |
| **LC-025** | `ying_position` **必须** = `((shi_position + 2) mod 6) + 1` | MUST |

## 4. 纳甲 / 六亲 / 六神

| ID | 条款 | 级别 |
|----|------|------|
| **LC-030** | `najia` **必须**含 6 项，每项为「天干+地支」，顺序自下而上 | MUST |
| **LC-031** | `liu_qin` **必须**含 6 项，取值 ∈ {兄弟, 子孙, 父母, 妻财, 官鬼} | MUST |
| **LC-032** | 六亲 **必须**由宫五行与地支五行的关系决定（同→兄弟，生→子孙，被生→父母，克→妻财，被克→官鬼） | MUST |
| **LC-033** | `liu_shen` **必须**含 6 项，为六神循环（青龙朱雀勾陈螣蛇白虎玄武）的连续片段 | MUST |
| **LC-034** | 六神起始 **必须**由**日干**决定，且**日界为 23:00**（`born_at.hour >= 23` 时按次日取日干） | MUST |

## 5. 用神与输出

| ID | 条款 | 级别 |
|----|------|------|
| **LC-040** | `yong_shen` **必须**由问题关键词规则表决定；无问题或无命中时 **必须**为 `世爻` | MUST |
| **LC-041** | 关键词规则 **必须**按既定的 5 组顺序匹配，首组命中即返回 | MUST |
| **LC-042** | `LiuyaoOutput.agent` **必须**为 `"liuyao"` | MUST |
| **LC-043** | 输出 **必须**可确定性复现：同一输入两次计算 **必须**逐字段一致 | MUST |
| **LC-044** | 输出 **必须**满足 `LiuyaoChart` 的 `extra="forbid"` 结构 | MUST |

## 6. 架构边界

| ID | 条款 | 级别 |
|----|------|------|
| **LC-050** | `compute()` **MUST NOT** 调用 LLM 或任何网络 | MUST |
| **LC-051** | `compute()` **MUST NOT** 读写外部存储 | MUST |
| **LC-052** | 解释层 **MUST NOT** 改写任何计算字段 | MUST |

## 7. 契约承认的未实现边界（Deferred）

| ID | 边界 |
|----|------|
| **LC-D01** | 不含卦辞/爻辞文本 |
| **LC-D02** | 不含应期 / 旺衰 / 月建日辰 |
| **LC-D03** | 六神依日干（非日支） |
| **LC-D04** | 自动 seed 跨进程不可复现（受 `PYTHONHASHSEED` 影响）；显式 `seed`/`casts` 可复现 |
| **LC-D05** | 互卦恒为稳定爻，不参与变卦判定 |

## 8. 验证

| 层 | 工件 |
|----|------|
| Golden Vectors | `docs/liuyao/golden_vectors.json`（24：normal 10 / edge 6 / boundary 5 / invalid 3） |
| 生产回归 | `tests/test_liuyao_golden_vectors.py` |
| 等价证明 | `reference/tests/test_liuyao_equivalence.py`（Production == Reference，逐字节） |
| Reference | `reference/liuyao/domain.py` |

## 9. 变更治理

本契约一旦 **Frozen**，算法/规则/向量的变更 **MUST** 经 ACP 并递增契约版本。
当前为 **candidate**：与既有实现一一对应，未冻结。
