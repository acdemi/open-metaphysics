# Rule DSL 设计文档

> 状态：Engineering Freeze v1 (2026-07-11)
> 阶段：Phase 6.5 - 工程冻结设计
> 依赖：Phase 6 Rule Schema（`docs/design/phase6/02_rule_layer_architecture.md`、`04_pydantic_models.md`）
> 约束：不修改任何 Phase 6 Schema；DSL 必须无损映射到已有 Pydantic 模型

---

## 1. 设计目标

### 1.1 为什么需要 DSL

Phase 6 定义了 Rule 的 Pydantic 模型（`Rule`、`RuleCondition`、`RuleResult`、`RuleScope`、`SourceRef`）。
这解决了**结构化验证**问题，但没有解决**规则编辑与管理**问题。

当前状态下，规则的创建方式是：在 Python 代码中实例化 `Rule` 对象。这在规则数量少时可行，
但当规则数量增长到数百甚至数千条时，将面临以下问题：

| 问题 | Python 对象方式 | DSL 方式 |
|------|-----------------|---------|
| 编辑门槛 | 需要 Python 开发能力 | YAML 文本，非技术人员可编辑 |
| 批量管理 | 散落在多个 `.py` 文件中 | 集中在 `rules/` 目录，按体系分文件 |
| 版本控制 | `.py` diff 混杂代码逻辑与规则数据 | `.yaml` diff 仅反映规则变更 |
| 序列化存储 | 需要 `model_dump()` 转换 | YAML/JSON 天然可序列化 |
| 导入导出 | 需编写自定义导入导出代码 | 标准 YAML/JSON 解析器即可 |
| AI 生成 | LLM 生成 Python 代码风险高（可执行） | LLM 生成 YAML 安全（声明式，不可执行） |
| 跨平台 | 依赖 Python 运行时 | 纯文本，任何工具可读写 |

### 1.2 为什么不能直接维护 Python Rule 对象

1. **安全性**：Python 对象可以被注入任意代码（`__init__`、`validator` 中的代码）。
   DSL 是声明式的，不含可执行逻辑，从根源上杜绝代码注入。

2. **职责分离**：规则数据（命理知识）与规则引擎（代码逻辑）应该分离。
   命理研究者负责编写规则 YAML，工程师负责维护 RuleEngine。
   Python 对象方式将两者耦合在同一代码库中。

3. **可审计性**：每条规则的变更需要可追溯。
   YAML 文件的 git diff 清晰展示「哪条规则的哪个条件变了」，
   而 Python 代码的 diff 可能混入无关的格式变更。

4. **规模化**：当规则达到数千条时，需要批量校验、冲突检测、依赖分析等工具链。
   DSL 提供统一的解析入口，使这些工具可以独立于 Python 运行时构建。

### 1.3 为什么 DSL 在大规模下更易维护

```
规则数量       Python 对象方式               DSL 方式
─────────     ──────────────────          ──────────────────
  10 条       ✅ 简单直接                  ✅ 简单直接
 100 条       ⚠️ 文件臃肿，难导航           ✅ 按体系分文件，清晰
 500 条       ❌ 难以全局搜索/校验          ✅ DSL Validator 批量校验
1000+ 条      ❌ 无法管理冲突/依赖          ✅ 冲突图谱 + 依赖分析
```

DSL 的核心价值在于：**将规则从代码资产转变为数据资产**。
数据资产可以被版本控制、批量处理、自动化校验和 AI 辅助生成，
而代码资产需要人工维护且面临安全风险。

---

## 2. DSL Design Principles

| 原则 | 说明 |
|------|------|
| **Human Readable** | 命理研究者无需编程能力即可阅读和编辑规则。YAML 为首选格式，关键词使用自然语言映射（`if`/`then`/`all`/`any`/`not`）。 |
| **Machine Readable** | 同时支持 JSON 序列化，可直接被 RuleEngine、数据库、API 消费。YAML 与 JSON 可无损互转。 |
| **Deterministic** | 相同的 DSL 文件经过解析和校验后，必须产出字节相同的 Pydantic Rule 对象。不依赖运行时状态。 |
| **Versioned** | 每条规则携带语义版本号。规则变更时版本递增，旧版本保留。DSL 文件名可包含版本号以支持并存。 |
| **Immutable** | 规则一旦发布（版本固定），其内容不可修改。变更必须创建新版本。`deprecated` + `superseded_by` 标记淘汰路径。 |
| **Extensible** | Grammar 预留扩展点（`macros`、`templates`、`variables`），未来可在不破坏现有规则的前提下增加新特性。 |
| **Compatible** | DSL 的每一个字段都必须能映射到 Phase 6 定义的 Pydantic 模型。不引入 Schema 中不存在的新字段。 |

---

## 3. Grammar

### 3.1 Grammar 概览

DSL 采用 YAML/JSON 作为具体语法，以下 BNF 定义其结构语义。
YAML 和 JSON 都是该 Grammar 的合法具体实例。

```
<RuleDocument>    ::= <RuleMapping>

<RuleMapping>     ::= "rule" ":" <RuleBody>

<RuleBody>        ::= <Id>
                       <Name>
                       <NameEn>?
                       <System>
                       <RuleType>
                       <If>
                       <Then>
                       <Priority>?
                       <Scope>?
                       <Conflicts>?
                       <ConflictStrategy>?
                       <Source>
                       <Confidence>?
                       <Version>
                       <Deprecated>?
                       <SupersededBy>?

─── 条件系统 ───

<If>              ::= "if" ":" <ConditionGroup>

<ConditionGroup>  ::= <AllGroup>
                    | <AnyGroup>
                    | <NotGroup>
                    | <Condition>              // 单条件简写，等价于 all: [<Condition>]

<AllGroup>        ::= "all" ":" <ConditionOrGroupList>    // 逻辑 AND
<AnyGroup>        ::= "any" ":" <ConditionOrGroupList>    // 逻辑 OR
<NotGroup>        ::= "not" ":" <ConditionGroup>           // 逻辑 NOT

<ConditionOrGroupList> ::= <ConditionOrGroup>+            // 至少 1 个
<ConditionOrGroup>     ::= <Condition>
                        | <AllGroup>
                        | <AnyGroup>
                        | <NotGroup>

<Condition>       ::= "field" ":" <String>
                       "operator" ":" <Operator>
                       "value" ":" <Value>?               // exists/not_exists 时可省略
                       "negate" ":" <Boolean>?             // 默认 false
                       "description" ":" <String>?

<Operator>        ::= "equals" | "not_equals" | "contains" | "not_contains"
                    | "in" | "not_in" | "greater_than" | "less_than"
                    | "exists" | "not_exists" | "matches"

─── 结果系统 ───

<Then>            ::= "then" ":" <ResultList>

<ResultList>      ::= <Result>+                            // 至少 1 个

<Result>          ::= "domain" ":" <Domain>
                       "conclusion" ":" <String>
                       "conclusion_node_id" ":" <String>?
                       "weight" ":" <Float>                // [0.0, 1.0]
                       "direction" ":" <Direction>?        // 默认 positive

<Domain>          ::= "career" | "personality" | "marriage" | "health"
                    | "wealth" | "education" | "family" | "travel"
                    | "legal" | "overall"

<Direction>       ::= "positive" | "negative" | "neutral"

─── 优先级与冲突 ───

<Priority>        ::= "priority" ":" <Integer>             // [0, 100], 默认 50
<Conflicts>       ::= "conflicts" ":" <RuleIdList>
<ConflictStrategy>::= "conflict_strategy" ":" <Strategy>
<Strategy>        ::= "highest_priority_wins" | "retain_all" | "merge"  // 默认 retain_all

─── 适用范围 ───

<Scope>           ::= "scope" ":" <ScopeBody>
<ScopeBody>       ::= "systems" ":" <SystemList>           // 必填
                       "gender" ":" <GenderList>?
                       "age_range" ":" <IntPair>?
                       "lunar_month_range" ":" <IntPair>?

<System>          ::= "bazi" | "ziwei" | "qimen" | "liuyao" | "meihua" | "liuren"
<GenderList>      ::= ["male"] | ["female"] | ["male", "female"]
<IntPair>         ::= [<Integer>, <Integer>]

─── 来源与版本 ───

<Source>          ::= "source" ":" <SourceBody>
<SourceBody>      ::= "text" ":" <String>                  // 必填
                       "chapter" ":" <String>?
                       "author" ":" <String>?
                       "page" ":" <Integer>?
                       "url" ":" <String>?
                       "credibility" ":" <Float>?          // [0.0, 1.0], 默认 0.8

<Confidence>      ::= "confidence" ":" <Float>             // [0.0, 1.0]
<Version>         ::= "version" ":" <SemVer>               // MAJOR.MINOR.PATCH
<Deprecated>      ::= "deprecated" ":" <Boolean>           // 默认 false
<SupersededBy>    ::= "superseded_by" ":" <RuleId>

<Id>              ::= "id" ":" <RuleId>
<RuleId>          ::= "rule:" <system> ":" <slug> ":v" <Integer>     // 如 rule:bazi:shang_guan_pei_yin:v1
<Name>            ::= "name" ":" <String>
<NameEn>          ::= "name_en" ":" <String>
<RuleType>        ::= "rule_type" ":" <RuleTypeValue>
<RuleTypeValue>   ::= "pattern_recognition" | "relation_derivation"
                    | "ten_god_determination" | "yong_shen_determination"
                    | "element_balance" | "domain_inference"
                    | "conflict_resolution" | "da_yun_analysis"
```

### 3.2 关键字速查表

| 关键字 | 必填 | 对应 Pydantic 字段 | 说明 |
|--------|------|-------------------|------|
| `rule` | 是 | （容器） | 顶层映射 |
| `id` | 是 | `Rule.id` | 规则唯一标识 |
| `name` | 是 | `Rule.name` | 中文名称 |
| `name_en` | 否 | `Rule.name_en` | 英文标识 |
| `system` | 是 | `Rule.system` | 所属体系 |
| `rule_type` | 是 | `Rule.rule_type` | 规则类型 |
| `if` | 是 | `Rule.conditions` | 条件块（见 §7 映射） |
| `then` | 是 | `Rule.results` | 结果列表 |
| `priority` | 否 | `Rule.priority` | 优先级，默认 50 |
| `scope` | 否 | `Rule.scope` | 适用范围 |
| `conflicts` | 否 | `Rule.conflicts` | 冲突规则 ID 列表 |
| `conflict_strategy` | 否 | `Rule.conflict_strategy` | 冲突策略，默认 retain_all |
| `source` | 是 | `Rule.source` | 经典出处 |
| `confidence` | 否 | `Rule.confidence` | 可信度 |
| `version` | 是 | `Rule.version` | 语义版本 |
| `deprecated` | 否 | `Rule.deprecated` | 是否废弃 |
| `superseded_by` | 否 | `Rule.superseded_by` | 替代规则 ID |

### 3.3 条件逻辑语义

`if` 块支持四种条件组形式，通过组合表达任意布尔逻辑：

| DSL 形式 | 逻辑含义 | 映射方式 |
|----------|---------|---------|
| `if: { field: ..., operator: ... }` | 单条件 | 直接映射为 `conditions: [cond]` |
| `if: { all: [c1, c2] }` | c1 AND c2 | 直接映射为 `conditions: [c1, c2]` |
| `if: { any: [c1, c2] }` | c1 OR c2 | **编译器展开**为 2 条 Rule（见 §7.3） |
| `if: { not: { ... } }` | NOT 条件 | 映射为 `conditions: [{..., negate: true}]` |

嵌套组合示例：

```yaml
if:
  all:
    - field: day_master
      operator: equals
      value: 甲
    - any:
        - field: ten_gods_map.values
          operator: contains
          value: 正官
        - field: ten_gods_map.values
          operator: contains
          value: 七杀
    - not:
        field: day_master_strength
        operator: greater_than
        value: 0.7
```

语义：日主为甲 **AND** (命局有正官 **OR** 有七杀) **AND** 日主不偏强

编译器将此嵌套表达式规范化为析取范式（DNF），展开为多条 Rule（见 §7.3）。

---

## 4. YAML Examples

### 4.1 单条件规则

```yaml
rule:
  id: rule:bazi:yang_ren_ge:v1
  name: 羊刃格
  name_en: yang_blade_pattern
  system: bazi
  rule_type: pattern_recognition

  if:
    field: shen_sha_list
    operator: contains
    value: 羊刃
    description: 命局中有羊刃

  then:
    - domain: personality
      conclusion: 性格刚毅果敢
      conclusion_node_id: kn:personality:resolute
      weight: 0.75
      direction: positive

  priority: 60
  source:
    text: 三命通会
    chapter: 羊刃
    credibility: 0.85
  confidence: 0.9
  version: 1.0.0
```

### 4.2 多条件 AND 规则

```yaml
rule:
  id: rule:bazi:shang_guan_pei_yin:v1
  name: 伤官佩印
  name_en: wounded_officer_adorned_by_seal
  system: bazi
  rule_type: pattern_recognition

  if:
    all:
      - field: ten_gods_map.values
        operator: contains
        value: 伤官
        description: 命局中有伤官
      - field: ten_gods_map.values
        operator: contains
        value: 正印
        description: 命局中有正印
      - field: day_master_strength
        operator: less_than
        value: 0.4
        description: 日主偏弱

  then:
    - domain: career
      conclusion: 适合科研
      conclusion_node_id: kn:career:research
      weight: 0.91
      direction: positive
    - domain: personality
      conclusion: 聪慧好学
      conclusion_node_id: kn:personality:intellectual
      weight: 0.85
      direction: positive

  priority: 80
  scope:
    systems: [bazi]
  conflicts:
    - rule:bazi:shang_guan_jian_sha:v1
  conflict_strategy: retain_all
  source:
    text: 滴天髓
    chapter: 伤官
    credibility: 0.95
  confidence: 1.0
  version: 1.0.0
```

### 4.3 OR (any) 规则

```yaml
rule:
  id: rule:bazi:cai_xing_ge:v1
  name: 财星格
  name_en: wealth_star_pattern
  system: bazi
  rule_type: pattern_recognition

  if:
    any:
      - field: ten_gods_map.values
        operator: contains
        value: 正财
        description: 命局中有正财
      - field: ten_gods_map.values
        operator: contains
        value: 偏财
        description: 命局中有偏财

  then:
    - domain: wealth
      conclusion: 命中有财星，主财运
      conclusion_node_id: kn:wealth:star_present
      weight: 0.80
      direction: positive

  priority: 65
  source:
    text: 子平真诠
    chapter: 论财
    credibility: 0.90
  confidence: 0.85
  version: 1.0.0
```

> **注意**：`any` 在编译时展开为 2 条 Rule（见 §7.3），分别检查正财和偏财。
> 两条 Rule 共享相同的 `then`、`priority`、`source`、`version`。

### 4.4 NOT 规则

```yaml
rule:
  id: rule:bazi:shang_guan_wu_yin:v1
  name: 伤官无印
  name_en: wounded_officer_without_seal
  system: bazi
  rule_type: pattern_recognition

  if:
    all:
      - field: ten_gods_map.values
        operator: contains
        value: 伤官
        description: 命局中有伤官
      - not:
          field: ten_gods_map.values
          operator: contains
          value: 正印
          description: 命局中无正印

  then:
    - domain: personality
      conclusion: 伤官无印，傲慢不羁
      conclusion_node_id: kn:personality:arrogant
      weight: 0.70
      direction: negative

  priority: 70
  conflicts:
    - rule:bazi:shang_guan_pei_yin:v1
  conflict_strategy: retain_all
  source:
    text: 滴天髓
    chapter: 伤官
    credibility: 0.95
  confidence: 0.85
  version: 1.0.0
```

### 4.5 Scope 规则

```yaml
rule:
  id: rule:qimen:yang_dun_jin:v1
  name: 阳遁金局
  name_en: yang_dun_metal_ju
  system: qimen
  rule_type: pattern_recognition

  if:
    all:
      - field: dun_type
        operator: equals
        value: yang
        description: 阳遁
      - field: ju
        operator: in
        value: [6, 7]
        description: 六七局（金）

  then:
    - domain: overall
      conclusion: 阳遁金局，主肃杀果断
      weight: 0.65
      direction: neutral

  priority: 55
  scope:
    systems: [qimen]
    gender: [male]
    age_range: [25, 60]
    lunar_month_range: [1, 6]
  source:
    text: 烟波钓叟歌
    credibility: 0.80
  confidence: 0.80
  version: 1.0.0
```

### 4.6 复合逻辑（AND + OR + NOT）

```yaml
rule:
  id: rule:bazi:guan_sha_hun:v1
  name: 官杀混杂
  name_en: mixed_official_and_killer
  system: bazi
  rule_type: pattern_recognition

  if:
    all:
      - field: ten_gods_map.values
        operator: contains
        value: 正官
        description: 命局中有正官
      - field: ten_gods_map.values
        operator: contains
        value: 七杀
        description: 命局中有七杀
      - not:
          field: shen_sha_list
          operator: contains
          value: 天乙贵人
          description: 无天乙贵人化解

  then:
    - domain: career
      conclusion: 官杀混杂，事业多变动
      conclusion_node_id: kn:career:unstable
      weight: 0.72
      direction: negative
    - domain: marriage
      conclusion: 感情复杂，易有纠葛
      conclusion_node_id: kn:marriage:complicated
      weight: 0.68
      direction: negative

  priority: 75
  conflicts:
    - rule:bazi:guan_yin_xiang_sheng:v1
  conflict_strategy: retain_all
  source:
    text: 子平真诠
    chapter: 论官杀
    credibility: 0.90
  confidence: 0.85
  version: 1.0.0
```

---

## 5. JSON Examples

JSON 是 DSL 的第二种一等序列化格式。以下 JSON 与 §4 中的 YAML 示例一一对应，
可通过标准 YAML 解析器（`yaml.safe_load`）无损互转。

### 5.1 单条件规则（对应 §4.1）

```json
{
  "rule": {
    "id": "rule:bazi:yang_ren_ge:v1",
    "name": "羊刃格",
    "name_en": "yang_blade_pattern",
    "system": "bazi",
    "rule_type": "pattern_recognition",
    "if": {
      "field": "shen_sha_list",
      "operator": "contains",
      "value": "羊刃",
      "description": "命局中有羊刃"
    },
    "then": [
      {
        "domain": "personality",
        "conclusion": "性格刚毅果敢",
        "conclusion_node_id": "kn:personality:resolute",
        "weight": 0.75,
        "direction": "positive"
      }
    ],
    "priority": 60,
    "source": {
      "text": "三命通会",
      "chapter": "羊刃",
      "credibility": 0.85
    },
    "confidence": 0.9,
    "version": "1.0.0"
  }
}
```

### 5.2 多条件 AND 规则（对应 §4.2）

```json
{
  "rule": {
    "id": "rule:bazi:shang_guan_pei_yin:v1",
    "name": "伤官佩印",
    "name_en": "wounded_officer_adorned_by_seal",
    "system": "bazi",
    "rule_type": "pattern_recognition",
    "if": {
      "all": [
        { "field": "ten_gods_map.values", "operator": "contains", "value": "伤官", "description": "命局中有伤官" },
        { "field": "ten_gods_map.values", "operator": "contains", "value": "正印", "description": "命局中有正印" },
        { "field": "day_master_strength", "operator": "less_than", "value": 0.4, "description": "日主偏弱" }
      ]
    },
    "then": [
      { "domain": "career", "conclusion": "适合科研", "conclusion_node_id": "kn:career:research", "weight": 0.91, "direction": "positive" },
      { "domain": "personality", "conclusion": "聪慧好学", "conclusion_node_id": "kn:personality:intellectual", "weight": 0.85, "direction": "positive" }
    ],
    "priority": 80,
    "scope": { "systems": ["bazi"] },
    "conflicts": ["rule:bazi:shang_guan_jian_sha:v1"],
    "conflict_strategy": "retain_all",
    "source": { "text": "滴天髓", "chapter": "伤官", "credibility": 0.95 },
    "confidence": 1.0,
    "version": "1.0.0"
  }
}
```

### 5.3 OR (any) 规则（对应 §4.3）

```json
{
  "rule": {
    "id": "rule:bazi:cai_xing_ge:v1",
    "name": "财星格",
    "name_en": "wealth_star_pattern",
    "system": "bazi",
    "rule_type": "pattern_recognition",
    "if": {
      "any": [
        { "field": "ten_gods_map.values", "operator": "contains", "value": "正财", "description": "命局中有正财" },
        { "field": "ten_gods_map.values", "operator": "contains", "value": "偏财", "description": "命局中有偏财" }
      ]
    },
    "then": [
      { "domain": "wealth", "conclusion": "命中有财星，主财运", "conclusion_node_id": "kn:wealth:star_present", "weight": 0.80, "direction": "positive" }
    ],
    "priority": 65,
    "source": { "text": "子平真诠", "chapter": "论财", "credibility": 0.90 },
    "confidence": 0.85,
    "version": "1.0.0"
  }
}
```

### 5.4 NOT 规则（对应 §4.4）

```json
{
  "rule": {
    "id": "rule:bazi:shang_guan_wu_yin:v1",
    "name": "伤官无印",
    "name_en": "wounded_officer_without_seal",
    "system": "bazi",
    "rule_type": "pattern_recognition",
    "if": {
      "all": [
        { "field": "ten_gods_map.values", "operator": "contains", "value": "伤官", "description": "命局中有伤官" },
        { "not": { "field": "ten_gods_map.values", "operator": "contains", "value": "正印", "description": "命局中无正印" } }
      ]
    },
    "then": [
      { "domain": "personality", "conclusion": "伤官无印，傲慢不羁", "conclusion_node_id": "kn:personality:arrogant", "weight": 0.70, "direction": "negative" }
    ],
    "priority": 70,
    "conflicts": ["rule:bazi:shang_guan_pei_yin:v1"],
    "conflict_strategy": "retain_all",
    "source": { "text": "滴天髓", "chapter": "伤官", "credibility": 0.95 },
    "confidence": 0.85,
    "version": "1.0.0"
  }
}
```

---

## 6. Rule Validation

### 6.1 验证流水线

DSL 规则从文本到可执行 Rule 对象，经过 5 个阶段的验证：

```
DSL 文本 (YAML/JSON)
       │
       ▼
┌──────────────────┐
│ 1. Parse         │  YAML/JSON 解析为 dict
│ Validation       │  检查：语法是否合法 YAML/JSON
└───────┬──────────┘
        ▼
┌──────────────────┐
│ 2. Grammar       │  检查：关键字是否完整、必填字段是否存在
│ Validation       │  检查：if/then 结构是否符合 Grammar
└───────┬──────────┘
        ▼
┌──────────────────┐
│ 3. Field         │  检查：field 路径是否为已知的排盘结构路径
│ Validation       │  检查：operator 是否在枚举内
│                  │  检查：value 类型是否与 operator 匹配
│                  │  检查：domain/direction/system 是否合法枚举
└───────┬──────────┘
        ▼
┌──────────────────┐
│ 4. Scope         │  检查：scope.systems 是否包含 rule.system
│ Validation       │  检查：age_range/lunar_month_range 是否合法
│                  │  检查：gender 值是否合法
└───────┬──────────┘
        ▼
┌──────────────────┐
│ 5. Schema        │  将 dict 通过 Pydantic Rule.model_validate()
│ Validation       │  验证：所有字段约束（pattern, ge, le, min_length）
│                  │  验证：confidence/weight/credibility 范围
│                  │  验证：version 格式、ID 格式
└───────┬──────────┘
        ▼
┌──────────────────┐
│ 6. Version       │  检查：deprecated=true 时 superseded_by 必须存在
│ Validation       │  检查：同 ID 的旧版本是否已注册
│                  │  检查：conflicts 引用的规则 ID 是否存在
└───────┬──────────┘
        ▼
  Pydantic Rule 对象 (或编译后的多个 Rule 对象)
```

### 6.2 各阶段验证规则

#### Stage 1: Parse Validation

| 检查项 | 失败行为 |
|--------|---------|
| YAML/JSON 语法合法 | 报错，拒绝加载 |
| 顶层有 `rule` 键 | 报错，拒绝加载 |

#### Stage 2: Grammar Validation

| 检查项 | 失败行为 |
|--------|---------|
| `id` 存在且非空 | 报错 |
| `name` 存在且非空 | 报错 |
| `system` 存在 | 报错 |
| `rule_type` 存在 | 报错 |
| `if` 存在 | 报错 |
| `then` 存在且非空 | 报错 |
| `source` 存在且 `text` 非空 | 报错 |
| `version` 存在 | 报错 |
| `if` 块为 `all`/`any`/`not`/单条件之一 | 报错 |
| `all`/`any` 的列表至少 1 个元素 | 报错 |

#### Stage 3: Field Validation

| 检查项 | 失败行为 |
|--------|---------|
| `operator` 在 11 种枚举值内 | 报错 |
| `field` 为已注册的排盘结构路径 | 警告（允许自定义路径，但标记为 unverified） |
| `value` 类型与 `operator` 匹配 | 报错（如 `greater_than` 的 value 不是数字） |
| `domain` 在 10 种枚举值内 | 报错 |
| `direction` 在 3 种枚举值内 | 报错 |
| `rule_type` 在 8 种枚举值内 | 报错 |
| `system` 在 6 种枚举值内 | 报错 |

#### Stage 4: Scope Validation

| 检查项 | 失败行为 |
|--------|---------|
| `scope.systems` 包含 `rule.system` | 报错（规则体系与 scope 不一致） |
| `age_range` 为 2 元素数组且 min < max | 报错 |
| `lunar_month_range` 为 2 元素数组且 1 <= min, max <= 12 | 报错 |
| `gender` 值为 "male" 或 "female" | 报错 |

#### Stage 5: Schema Validation

此阶段直接委托给 Pydantic 的 `Rule.model_validate(dict)`。
所有字段约束（`pattern`、`ge`、`le`、`min_length`）由 Pydantic 强制执行。
这是与 Phase 6 Schema 的**直接对接点**。

#### Stage 6: Version Validation

| 检查项 | 失败行为 |
|--------|---------|
| `deprecated=true` 时 `superseded_by` 非空 | 报错 |
| `superseded_by` 指向的规则 ID 已注册 | 警告（允许前向引用，但标记为 unresolved） |
| `conflicts` 中的规则 ID 格式合法 | 报错 |
| 同一 `id` 的旧版本已注册且版本号递增 | 警告（允许同版本覆盖，但标记为 re-registration） |

### 6.3 RuleValidator 接口（仅设计，不实现）

```python
from typing import Protocol
from pydantic import ValidationError


class RuleValidationResult:
    """规则验证结果。"""
    valid: bool
    errors: list[str]               # 阻断性错误
    warnings: list[str]             # 非阻断性警告
    rule: "Rule | None"             # 验证通过后的 Rule 对象（编译后可能为多个）
    expanded_rules: list["Rule"]    # any 展开后的 Rule 列表（见 §7.3）


class RuleValidator(Protocol):
    """DSL 规则验证器接口。"""

    def validate_text(self, text: str, format: str = "yaml") -> RuleValidationResult:
        """验证 DSL 文本（YAML 或 JSON）。

        Args:
            text: DSL 文本内容
            format: "yaml" 或 "json"

        Returns:
            RuleValidationResult，包含验证结果和编译后的 Rule 对象
        """
        ...

    def validate_dict(self, data: dict) -> RuleValidationResult:
        """验证已解析的 dict 结构。

        跳过 Stage 1（Parse），从 Stage 2 开始。
        """
        ...

    def validate_file(self, path: str) -> RuleValidationResult:
        """验证 DSL 文件。

        自动检测格式（.yaml/.yml -> yaml, .json -> json）。
        """
        ...

    def validate_directory(self, dir_path: str) -> list[RuleValidationResult]:
        """批量验证目录下所有 DSL 文件。"""
        ...
```

### 6.4 验证错误报告格式

```yaml
validation_result:
  valid: false
  errors:
    - stage: grammar
      message: "必填字段 'source.text' 缺失"
      rule_id: "rule:bazi:xxx:v1"
      field: "source.text"
    - stage: field
      message: "operator 'greater_than' 的 value 必须为数值，实际为字符串 '甲'"
      rule_id: "rule:bazi:xxx:v1"
      field: "if.all[2].value"
  warnings:
    - stage: field
      message: "field 路径 'custom_field' 不在已注册路径列表中"
      rule_id: "rule:bazi:xxx:v1"
      field: "if.all[0].field"
    - stage: version
      message: "conflicts 引用的规则 'rule:bazi:yyy:v1' 尚未注册"
      rule_id: "rule:bazi:xxx:v1"
```

---

## 7. Compatibility

### 7.1 转换流水线总览

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│ DSL 文本     │────▶│ DSL Parser   │────▶│ DSL Compiler  │────▶│ Pydantic     │
│ (YAML/JSON) │     │ (yaml/json)  │     │ (条件规范化)   │     │ Rule 对象    │
└─────────────┘     └──────────────┘     └───────────────┘     └──────┬───────┘
                                                                    │
                                                          ┌─────────▼─────────┐
                                                          │ RuleRegistry      │
                                                          │ (.register())     │
                                                          └─────────┬─────────┘
                                                                    │
                                                          ┌─────────▼─────────┐
                                                          │ RuleEngine        │
                                                          │ (.evaluate())     │
                                                          └─────────┬─────────┘
                                                                    │
                                                          ┌─────────▼─────────┐
                                                          │ RuleEvaluation    │
                                                          └───────────────────┘
```

### 7.2 字段映射表

DSL 的每个关键字直接映射到 Phase 6 Pydantic 模型的字段，**无新增字段、无字段重命名**：

| DSL 路径 | Pydantic 模型 | 字段 | 映射方式 |
|----------|--------------|------|---------|
| `rule.id` | `Rule` | `id` | 直接赋值 |
| `rule.name` | `Rule` | `name` | 直接赋值 |
| `rule.name_en` | `Rule` | `name_en` | 直接赋值（默认 ""） |
| `rule.system` | `Rule` | `system` | 枚举转换 |
| `rule.rule_type` | `Rule` | `rule_type` | 枚举转换 |
| `rule.if` | `Rule` | `conditions` | 见 §7.3 条件编译 |
| `rule.then` | `Rule` | `results` | 列表映射，每项 -> `RuleResult` |
| `rule.priority` | `Rule` | `priority` | 直接赋值（默认 50） |
| `rule.scope` | `Rule` | `scope` | 映射为 `RuleScope` |
| `rule.conflicts` | `Rule` | `conflicts` | 直接赋值（默认 []） |
| `rule.conflict_strategy` | `Rule` | `conflict_strategy` | 枚举转换（默认 retain_all） |
| `rule.source` | `Rule` | `source` | 映射为 `SourceRef` |
| `rule.confidence` | `Rule` | `confidence` | 直接赋值 |
| `rule.version` | `Rule` | `version` | 直接赋值 |
| `rule.deprecated` | `Rule` | `deprecated` | 直接赋值（默认 False） |
| `rule.superseded_by` | `Rule` | `superseded_by` | 直接赋值（默认 None） |
| `if -> condition.field` | `RuleCondition` | `field` | 直接赋值 |
| `if -> condition.operator` | `RuleCondition` | `operator` | 枚举转换 |
| `if -> condition.value` | `RuleCondition` | `value` | 直接赋值 |
| `if -> condition.negate` | `RuleCondition` | `negate` | 直接赋值（默认 False） |
| `if -> condition.description` | `RuleCondition` | `description` | 直接赋值（默认 ""） |
| `then -> result.domain` | `RuleResult` | `domain` | 枚举转换 |
| `then -> result.conclusion` | `RuleResult` | `conclusion` | 直接赋值 |
| `then -> result.conclusion_node_id` | `RuleResult` | `conclusion_node_id` | 直接赋值 |
| `then -> result.weight` | `RuleResult` | `weight` | 直接赋值 |
| `then -> result.direction` | `RuleResult` | `direction` | 枚举转换（默认 positive） |

### 7.3 条件编译（Condition Compilation）

DSL 的 `if` 块支持 `all`/`any`/`not` 嵌套组合，而 Phase 6 的 `Rule.conditions` 是一个扁平列表
（隐含 AND 语义，通过 `negate` 支持 NOT）。编译器负责将嵌套条件树**规范化为析取范式（DNF）**，
然后为每个析取项生成一个独立的 `Rule` 对象。

#### 7.3.1 编译规则

```
输入：DSL if 块（条件树）
  │
  ▼
Step 1: 解析条件树为 AST
  │
  ▼
Step 2: 推入否定（Push NOT inward）
  │   NOT(ALL[a, b])  ->  ANY[NOT(a), NOT(b)]    （De Morgan）
  │   NOT(ANY[a, b])  ->  ALL[NOT(a), NOT(b)]    （De Morgan）
  │   NOT(NOT(a))     ->  a
  │
  ▼
Step 3: 分配 AND over OR（转换为 DNF）
  │   ALL[a, ANY[b, c]]  ->  ANY[ALL[a, b], ALL[a, c]]
  │
  ▼
Step 4: 每个 ALL 子句 -> 一个 Rule.conditions 列表
  │   条件中的 NOT(cond) -> RuleCondition(negate=True)
  │
  ▼
输出：N 个 Pydantic Rule 对象
```

#### 7.3.2 编译示例

**输入 DSL（any）**:
```yaml
if:
  any:
    - { field: ten_gods_map.values, operator: contains, value: 正财 }
    - { field: ten_gods_map.values, operator: contains, value: 偏财 }
```

**编译输出（2 个 Rule 对象）**:

```
Rule #1:
  id: rule:bazi:cai_xing_ge:v1#1
  conditions: [{ field: ten_gods_map.values, operator: contains, value: 正财, negate: false }]
  results: [...]   # 与原 DSL 的 then 相同
  priority: 65     # 与原 DSL 相同
  source: ...      # 与原 DSL 相同

Rule #2:
  id: rule:bazi:cai_xing_ge:v1#2
  conditions: [{ field: ten_gods_map.values, operator: contains, value: 偏财, negate: false }]
  results: [...]   # 与 Rule #1 相同
  priority: 65
  source: ...
```

**输入 DSL（嵌套 AND + OR + NOT）**:
```yaml
if:
  all:
    - { field: day_master, operator: equals, value: 甲 }
    - any:
        - { field: ten_gods_map.values, operator: contains, value: 正官 }
        - { field: ten_gods_map.values, operator: contains, value: 七杀 }
    - not: { field: day_master_strength, operator: greater_than, value: 0.7 }
```

**编译输出（2 个 Rule 对象）**:

```
Rule #1:
  id: rule:bazi:guan_sha_jia#1
  conditions: [
    { field: day_master, operator: equals, value: 甲, negate: false },
    { field: ten_gods_map.values, operator: contains, value: 正官, negate: false },
    { field: day_master_strength, operator: greater_than, value: 0.7, negate: true }
  ]

Rule #2:
  id: rule:bazi:guan_sha_jia#2
  conditions: [
    { field: day_master, operator: equals, value: 甲, negate: false },
    { field: ten_gods_map.values, operator: contains, value: 七杀, negate: false },
    { field: day_master_strength, operator: greater_than, value: 0.7, negate: true }
  ]
```

#### 7.3.3 派生 Rule ID 规则

当 DSL 规则通过 `any` 展开为多个 Pydantic Rule 时：

- **基础 ID**：DSL 中声明的 `id`（如 `rule:bazi:cai_xing_ge:v1`）
- **派生 ID**：基础 ID + `#N` 后缀（如 `rule:bazi:cai_xing_ge:v1#1`）
- **N 从 1 开始**，按析取项顺序编号
- **单条件规则不展开**：`if` 为单条件或纯 `all` 时，直接映射为 1 个 Rule，ID 不加后缀
- **冲突引用**：`conflicts` 字段使用基础 ID；RuleEngine 在匹配时自动展开为基础 ID 的所有派生规则
- **Pattern 引用**：`Pattern.rule_ids` 使用基础 ID；PatternMatcher 自动匹配所有派生规则

> **设计依据**：Phase 6 的 `Rule.id` pattern 为 `^rule:[a-z]+:[a-z_]+:v[0-9]+$`。
> 派生 ID 添加 `#N` 后缀，需要在实现阶段扩展 pattern 为 `^rule:[a-z]+:[a-z_]+:v[0-9]+(#[0-9]+)?$`。
> 此扩展仅放宽正则约束，不改变 Rule 模型的任何字段定义，属于**实现阶段**的兼容性调整，
> 不在 Phase 6.5 设计阶段修改。

### 7.4 反向映射（Pydantic -> DSL）

Pydantic Rule 对象也可以反向导出为 DSL YAML/JSON：

```python
# 仅设计，不实现
class RuleExporter(Protocol):
    def to_yaml(self, rule: "Rule") -> str: ...
    def to_json(self, rule: "Rule") -> str: ...
    def to_yaml_file(self, rule: "Rule", path: str) -> None: ...
```

反向映射规则：
- `conditions` 列表长度为 1 且 `negate=False` -> `if: { 单条件 }`
- `conditions` 列表长度 > 1 且全部 `negate=False` -> `if: { all: [...] }`
- `conditions` 中有 `negate=True` 的条件 -> `if: { all: [..., not: {...}] }`
- 多个派生 Rule（同基础 ID）-> 合并为 `if: { any: [...] }`

---

## 8. Future Extension

以下扩展特性**不在当前 Sprint 范围内**，但 Grammar 和编译器架构已预留接入点。
未来扩展不得破坏现有 DSL 文件的向后兼容性。

### 8.1 Macro（宏）

**目标**：定义可复用的条件组合，在多条规则中引用。

```yaml
# 宏定义（未来格式）
macro:
  name: has_wealth_star
  body:
    any:
      - { field: ten_gods_map.values, operator: contains, value: 正财 }
      - { field: ten_gods_map.values, operator: contains, value: 偏财 }

# 规则中引用宏
rule:
  id: rule:bazi:cai_wang_shen_ruo:v1
  if:
    all:
      - macro: has_wealth_star
      - { field: day_master_strength, operator: less_than, value: 0.3 }
  then:
    - { domain: wealth, conclusion: 财多身弱, weight: 0.80, direction: negative }
```

**编译**：宏在编译时展开为内联条件，产出标准 Rule 对象。不改变 Pydantic 模型。

### 8.2 Template（模板）

**目标**：参数化规则模板，批量生成相似规则。

```yaml
# 模板定义（未来格式）
template:
  name: ten_god_pattern
  params: [ten_god_name, conclusion_text, weight_val]
  body:
    rule:
      id: "rule:bazi:{{ten_god_name}}_pattern:v1"
      if:
        field: ten_gods_map.values
        operator: contains
        value: "{{ten_god_name}}"
      then:
        - domain: personality
          conclusion: "{{conclusion_text}}"
          weight: "{{weight_val}}"

# 实例化
instances:
  - ten_god_name: 食神
    conclusion_text: 性格温和有才艺
    weight_val: 0.75
  - ten_god_name: 伤官
    conclusion_text: 性格聪明但傲气
    weight_val: 0.70
```

**编译**：模板在编译时实例化为多个标准 Rule 对象。

### 8.3 Reusable Condition（可复用条件）

**目标**：命名条件，在 `all`/`any` 中通过名称引用。

```yaml
conditions:
  - name: day_master_is_jia
    field: day_master
    operator: equals
    value: 甲

  - name: has_zheng_guan
    field: ten_gods_map.values
    operator: contains
    value: 正官

rules:
  - id: rule:bazi:jia_with_guan:v1
    if:
      all: [day_master_is_jia, has_zheng_guan]
    then:
      - { domain: career, conclusion: 适合体制内, weight: 0.80 }
```

### 8.4 Variable（变量）

**目标**：在规则中引用排盘上下文变量，避免硬编码。

```yaml
rule:
  id: rule:bazi:day_master_element:v1
  if:
    field: day_master_element
    operator: equals
    value: $day_master_element    # 变量引用
```

**编译**：变量在编译时替换为具体值，或在运行时由 RuleEngine 注入。
后者需要扩展 `RuleCondition.value` 的语义，属于未来 Schema 演进。

### 8.5 Expression（表达式）

**目标**：支持简单的算术/逻辑表达式作为条件值。

```yaml
rule:
  id: rule:bazi:element_imbalance:v1
  if:
    field: element_weights.wood
    operator: greater_than
    value: expr(sum(element_weights.values()) * 0.5)    # 木占五行总和 > 50%
```

**编译**：表达式在编译时求值（如果可静态求值）或在运行时由 RuleEngine 计算。
需要扩展 `ConditionOperator` 枚举和 `RuleCondition.value` 类型，属于未来 Schema 演进。

### 8.6 Function（函数）

**目标**：注册自定义判定函数，用于复杂条件。

```yaml
rule:
  id: rule:bazi:complex_check:v1
  if:
    field: chart
    operator: function
    value: is_chart_balanced        # 已注册的判定函数名
```

**约束**：函数必须在 RuleEngine 启动时注册，接受排盘结构作为输入，返回布尔值。
函数注册机制属于实现阶段设计，不在 Phase 6.5 范围内。

### 8.7 扩展兼容性矩阵

| 扩展特性 | 改动范围 | 向后兼容 | 需要 Schema 变更 |
|---------|---------|---------|-----------------|
| Macro | DSL Compiler | ✅ 宏展开为标准条件 | ❌ 不需要 |
| Template | DSL Compiler | ✅ 模板实例化为标准 Rule | ❌ 不需要 |
| Reusable Condition | DSL Compiler | ✅ 命名条件内联展开 | ❌ 不需要 |
| Variable | DSL Compiler / RuleEngine | ⚠️ 静态替换兼容；运行时注入需扩展 | ⚠️ 可能需要 |
| Expression | RuleEngine | ⚠️ 需扩展 operator/value 语义 | ✅ 需要 |
| Function | RuleEngine | ⚠️ 需新增 operator 枚举值 | ✅ 需要 |

> **原则**：Macro、Template、Reusable Condition 三项可在不修改 Phase 6 Schema 的前提下实现，
> 优先纳入 Phase 7 实现范围。Variable、Expression、Function 需要 Schema 演进，
> 留待 Phase 8+ 评估。

---

## 附录 A：DSL 文件组织建议

```
rules/
├── bazi/
│   ├── patterns.yaml          # 格局识别规则
│   ├── ten_gods.yaml          # 十神判定规则
│   ├── yong_shen.yaml         # 用神判定规则
│   ├── domain_inference.yaml  # 领域推断规则
│   └── da_yun.yaml            # 大运分析规则
├── ziwei/
│   ├── patterns.yaml
│   └── stars.yaml
├── qimen/
│   └── patterns.yaml
├── liuyao/
│   └── rules.yaml
└── shared/
    ├── macros.yaml            # 未来：跨体系宏定义
    └── templates.yaml         # 未来：模板定义
```

每个 YAML 文件可包含多条规则（使用 YAML 多文档 `---` 分隔）或单条规则。

## 附录 B：与 Phase 6 Schema 的兼容性确认

| Phase 6 模型 | DSL 覆盖 | 兼容性 |
|-------------|---------|--------|
| `Rule` | ✅ 全部字段 | 直接映射 |
| `RuleCondition` | ✅ 全部字段 | `negate` 支持 NOT |
| `RuleResult` | ✅ 全部字段 | 直接映射 |
| `RuleScope` | ✅ 全部字段 | 直接映射 |
| `SourceRef` | ✅ 全部字段 | 直接映射 |
| `RuleEvaluation` | N/A（运行时产出） | DSL 不涉及 |
| `RuleType` 枚举 | ✅ 全部 8 种 | 直接映射 |
| `ConditionOperator` 枚举 | ✅ 全部 11 种 | 直接映射 |
| `ConflictStrategy` 枚举 | ✅ 全部 3 种 | 直接映射 |
| `ResultDirection` 枚举 | ✅ 全部 3 种 | 直接映射 |
| `Domain` 枚举 | ✅ 全部 10 种 | 直接映射 |
| `MetaphysicsSystem` 枚举 | ✅ 全部 6 种 | 直接映射 |

> **结论**：DSL 的全部字段可无损映射到 Phase 6 Pydantic 模型，不修改任何已有 Schema。
> `any` 的展开通过编译器在 Rule 对象层面处理，不引入新的 Schema 字段。
> 派生 Rule ID 的 `#N` 后缀需要在实现阶段放宽 `Rule.id` 的正则约束，属于兼容性扩展而非 Schema 变更。
