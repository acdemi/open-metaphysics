# OpenMetaphysics — Schema 设计

> Pydantic v2 模型 + 导出 JSON Schema。所有智能体间/进程间通信都对照这些 schema 验证。状态：Qimen / BaZi 契约均已 Frozen 并完成登记。
> Schema 是跨语言契约（Python / Rust / Go），由 Reference Runtime 定义。
> **契约登记**: Qimen §3.3（qimen:behavior:v1.0.0）、BaZi §3.1（bazi:behavior:v1.0.0, Phase 6.6 登记）。

## 1. 设计规则

- **一个信封，多个载荷。** 每个智能体返回相同的 AgentOutput 信封；只有
result 载荷类型按智能体变化。
- 输入扩展 AgentInput；输出扩展 AgentOutput 并带有类型化
result。
- 枚举是封闭字符串基的（JSON 跨版本稳定）。
- 所有日期时间都是时区感知的 ISO-8601。出生地点可选。
- 每个 schema 都可以通过 Model.model_json_schema() 导出为 JSON Schema，并通过 API 在 GET /agents/{name}/schema 发布。
- 公共契约中永远不会有 Any 类型；不透明扩展使用 metadata (dict[str, str | int | float | bool]) 并记录键。

## 2. 共享核心 (openmetaphysics.core.schemas)

### 2.1 基础类型

```python
class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    elevation_m: float | None = None
    timezone: str | None = None      # IANA 时区，例如 "Asia/Hong_Kong"

class SexagenaryComponent(BaseModel):
    """干支（天干地支对），八字/奇门的原子单元。"""
    heavenly_stem: str               # 甲乙丙丁戊己庚辛壬癸之一
    earthly_branch: str              # 子丑寅卯辰巳午未申酉戌亥之一
    stem_index: int = Field(ge=0, le=9)
    branch_index: int = Field(ge=0, le=11)
```

### 2.2 输入信封

```python
class AgentInput(BaseModel):
    request_id: str
    born_at: datetime                 # 时区感知
    born_location: GeoPoint | None = None
    gender: Gender = Gender.UNKNOWN
    question: str | None = None       # 自由文本占卜问题
    locale: str = "zh-CN"
    seed: int | None = None           # 确定性 RNG 种子（六爻起卦）
    client_nonce: str | None = None   # 幂等/重放密钥
```

### 2.3 输出信封

```python
class ReasoningStep(BaseModel):
    step: int
    rule_ref: str                     # 例如 "bazi.month_pillar.solar_term"
    description: str
    inputs: dict[str, str | int | float]
    outputs: dict[str, str | int | float]

class ConfidenceScore(BaseModel):
    value: float = Field(ge=0.0, le=1.0)
    method: str                       # "rule_coverage" | "data_quality" | ...
    factors: dict[str, float]         # 例如 {"solar_term_resolution": 0.98}

class AgentOutput(BaseModel):
    request_id: str
    agent: str                        # "bazi" | "ziwei" | "qimen" | "liuyao"
    engine_version: str               # 确定性引擎的语义版本
    input_hash: str                   # 规范输入 sha256 → 重放密钥
    computed_at: datetime
    confidence: ConfidenceScore
    reasoning_trace: list[ReasoningStep]
    metadata: dict[str, str | int | float | bool]
    result: dict                      # 智能体特定；子类验证
```

## 3. 智能体特定载荷

### 3.1 八字 (agents.bazi)

> **契约登记**: `bazi:behavior:v1.0.0`（Frozen, `docs/bazi/BAZI_BEHAVIOR_CONTRACT.md`
> BC-013 Schema Contract 为规范性定义）。本登记为描述性文档, 与契约冲突时
> **以契约为准**; 任何变更须 ACP。

输入：`BaziInput(AgentInput)` — 追加 `dayun_count: int = 8`（大运步数, 可配）。
出生日时分 + 性别驱动大运方向（B5/B6）。

输出
result: BaziChart（全部 `extra="forbid"`）:

```python
class Pillar(BaseModel):
    position: Literal["year","month","day","hour"]
    stem: str                        # 天干 甲乙丙丁戊己庚辛壬癸
    branch: str                      # 地支 子丑寅卯辰巳午未申酉戌亥
    stem_index: int                  # 0..9
    branch_index: int                # 0..11
    hidden_stems: list[str]          # 藏干
    nayin: str                       # 纳音 (例如 "海中金")
    ten_god: str                     # 本柱干相对日主的十神

class DaYun(BaseModel):              # 大运（十年运）
    index: int                       # 1..dayun_count
    start_age: int
    end_age: int
    stem: str
    branch: str
    stem_index: int
    branch_index: int
    start_at: datetime

class BaziChart(BaseModel):
    day_master: str                  # 日主（日干）
    day_master_element: str          # 日主五行
    pillars: list[Pillar]            # 恰好 4 柱 (year/month/day/hour)
    dayun: list[DaYun]               # 默认 8 步（BaziInput.dayun_count 可配）
    ten_gods_map: dict[str, str]     # 出现干支 → 十神
    year_boundary: datetime          # 立春 UTC 时刻
    month_boundary: str              # 节名 (例如 "立春")
    gender_assumed: bool             # UNKNOWN 按男处理标记
```

### 3.2 紫微斗数 (agents.ziwei)

> **状态**: 描述性登记（**未注册契约**; Ziwei = Implemented, 见
> `docs/governance/CAPABILITY_STATUS.md`）。引擎 `ZiweiEngine` v0.2.0。
> Phase 6.7.1 勘误: `calendar_note` 位于 **ZiweiChart** 而非 `Palace`;
> 全模型 `extra="forbid"`。未导出静态 JSON Schema（可经
> `Model.model_json_schema()` 动态生成, `GET /agents/ziwei/schema`）。

输入：ZiweiInput(AgentInput) — 出生日时分 + 性别（继承信封, engine 当前不
消费 gender, 见 ZW-017）。支持显式提供 lunar_month: int | None /
lunar_day: int | None 用于重放。

输出
result: ZiweiChart（全部 `extra="forbid"`）:

```python
class Palace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    index: int = Field(ge=0, le=11)   # 0..11，寅=0 符合惯例
    name: str                         # 命宫/财帛/...
    earthly_branch: str
    heavenly_stem: str
    main_stars: list[str]             # 紫微/天机/... (14 主星已完成)
    auxiliary_stars: list[str]        # 辅星 (未实现, 恒空)
    is_fate_palace: bool = False
    is_body_palace: bool = False

class ZiweiChart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fate_palace_index: int
    body_palace_index: int
    yin_yang: Literal["yin","yang"]
    wuxing_ju: str                    # 五行局 例如 "水二局"
    palaces: list[Palace]             # 12 宫
    calendar_note: str | None = None  # 历法说明（闰月等）
```

### 3.3 奇门遁甲 (agents.qimen)

输入：QimenInput(AgentInput) — 使用 born_at（或选定的问卦时间）构建时家奇门盘。

输出
result: QimenBoard:

```python
class QimenCell(BaseModel):
    palace: int = Field(ge=1, le=9)   # 后天八卦 宫位 1..9
    name: str                         # 坎/坤/震/巽/中宫/乾/兑/艮/离
    sky_plate: str | None = None      # 天盘
    earth_plate: str | None = None    # 地盘
    eight_gods: str | None = None    # 八神
    nine_stars: str | None = None    # 九星
    eight_doors: str | None = None   # 八门
    three_qi: str | None = None       # 三奇
    is_void: bool = False             # 空亡
    is_central: bool = False

class QimenBoard(BaseModel):
    solar_term: str | None = None
    ju: int                           # 局 (1..9)
    dun_type: Literal["yang","yin"]   # 阳遁/阴遁
    cells: list[QimenCell]            # 9 宫格 (宫位 1..9)
```

### 3.4 六爻 (agents.liuyao)

输入：LiuyaoInput(AgentInput) — 如果客户端已有则添加明确爻线；否则引擎从 seed 确定性起卦（后备种子使用 hash(request_id) — 确定性，永远不使用 random()）。

```python
class YaoLine(BaseModel):
    position: int = Field(ge=1, le=6) # 初爻..上爻
    is_yin: bool                      # True=阴爻，False=阳爻
    is_changing: bool                 # 动爻
    cast_value: int                   # 6,7,8,9 (老阴/少阳/少阴/老阳)

class LiuyaoChart(BaseModel):
    original: list[YaoLine]           # 本卦 (6 线，下→上)
    changed: list[YaoLine]            # 变卦 (不变爻位置为空)
    mutual: list[YaoLine]             # 互卦
    original_hexagram: int            # 文王卦序 1..64
    changed_hexagram: int | None
    najia: list[str]                  # 每爻纳甲（干支）
    liu_qin: list[str]                # 每爻六亲（父母/兄弟/子孙/妻财/官鬼）
    liu_shen: list[str]               # 六神 (青龙/朱雀/勾陈/螣蛇/白虎/玄武)
    shi_position: int                 # 世爻 位置 1..6
    ying_position: int                # 应爻 位置 1..6
    yong_shen: str | None = None      # 用神
```

### 3.5 共识 (agents.consensus)

输入：ConsensusInput:

```python
class ConsensusInput(BaseModel):
    request_id: str
    agent_outputs: list[AgentOutput]  # 1..N 验证过的信封
    strategy: Literal["weighted","majority","all"] = "weighted"
```

输出
result: ConsensusReport:

```python
class AgentContribution(BaseModel):
    agent: str
    confidence: float
    weight: float
    summary: str

class Conflict(BaseModel):
    agents: list[str]
    field: str
    values: list[str]
    severity: Literal["low","medium","high"]

class ConsensusReport(BaseModel):
    overall_confidence: float
    contributions: list[AgentContribution]
    agreement_matrix: dict[str, dict[str, float]]
    conflicts: list[Conflict]
    synthesis: str                    # 结构化自然语言总结（确定性）
    recommendation: str | None = None
```

## 4. JSON Schema 发布

AgentRegistry 对每个智能体暴露：

```python
{
  "name": "liuyao",
  "input_schema":  LiuyaoInput.model_json_schema(),
  "output_schema": LiuyaoOutput.model_json_schema(),
  "engine_version": "0.1.0"
}
```

这是 FastAPI 层、MCP 桩和任何外部客户端消费的唯一真相来源。Schemas 在测试中对照示例 fixtures 验证。

---

## 5. Reference Runtime 与 Production Runtime 的关系

### 5.1 双重 Schema 体系

OpenMetaphysics 存在两套 Schema：

| Schema 体系 | 位置 | 用途 | 状态 |
|-------------|------|------|------|
| Production Schema | `src/openmetaphysics/core/schemas` | API 层、智能体信封 | 设计完成，部分实现 |
| Reference Schema | `reference/models.py` 等 | 行为规范、Contract | 完成，已冻结 |

**Reference Schema 是行为规范的唯一来源。** Production Schema 必须与
Reference Schema 保持兼容。

### 5.2 映射关系

    Production Schema (src/)           Reference Schema (reference/)
    AgentOutput                        RuleEvaluation / Evidence / ConsensusReport
    AgentInput                         chart_data (dict)
    ConfidenceScore                    confidence (float)
    ReasoningStep                      trace (list[str])

Production Schema 关注 API 层的信封结构（request_id, computed_at 等）。
Reference Schema 关注推理结果的确定性结构（RuleEvaluation, Evidence,
ConsensusReport）。

---

## 6. Schema 作为跨语言契约

### 6.1 跨语言一致性

Schema 不仅是 Python Pydantic 模型，更是**跨语言契约**：

- **Python**: Pydantic v2 模型（Reference Runtime + AI Layer）
- **Rust**: serde struct（计算核心、Rule Engine、Calendar）
- **Go**: struct + JSON tags（API、Consensus、Worker）

所有实现必须对同一输入产生**字节相同的 JSON 输出**。

### 6.2 契约验证

跨语言一致性通过以下机制保证：

1. **Contract JSON**（`reference/contracts/*.json`）：由 Reference Runtime
   自动生成，包含 golden examples。
2. **Golden Vectors**（`reference/conformance/golden/*.json`）：由
   Reference Runtime 自动生成，用于 Conformance Suite 验证。
3. **Conformance Suite**（`reference/conformance_runner.py`）：验证
   Production Runtime 输出与 Reference Runtime 完全一致。

### 6.3 JSON 序列化规则（跨语言通用）

- `ensure_ascii=False`：保留 Unicode（中文不转义）
- `sort_keys=True`：键名字典序排列
- 无 trailing whitespace，无 pretty-printing
- 详见 `docs/specification/CONFORMANCE_SPEC.md` CF-001 ~ CF-003
