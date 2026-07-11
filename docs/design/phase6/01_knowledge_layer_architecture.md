# Knowledge Layer Architecture（知识层架构）

> 状态：设计 v1 (2026-07-11)
> 层级定位：Layer 2.6 - 位于基础层（Schema/历法/引擎）之上，智能体层之下
> 原则：Rule First. Knowledge Second. LLM Last.

## 1. 设计目标

知识层为全部六大命理体系（八字、紫微、奇门、六爻、梅花、六壬）提供**统一的知识表示基础**，
成为 Consensus Agent、Explain Agent、RAG、未来 MCP 的共同数据底座。

核心职责：
- 将命理知识从「散落在代码注释和 LLM prompt 中」提取为**结构化、可查询、可审计**的数据。
- 支持知识节点的**多流派**表达--同一概念在不同流派（子平、三命、紫微三派等）中可有不同解释。
- 支持知识节点之间的**有向加权关系**（生克冲刑合害等），形成知识图谱。
- 知识层是**只读参考层**：智能体引擎查询知识节点用于解释和规则匹配，但不依赖知识层做计算--
  计算仍由确定性引擎完成。

## 2. 分层位置

```
┌─────────────────────────────────────────────────────────┐
│ 5. API / 编排层        FastAPI + LangGraph              │
├─────────────────────────────────────────────────────────┤
│ 4. 智能体层         八字 | 紫微 | 奇门 | 六爻 | 共识     │
│    每个智能体 = 确定性引擎 + (可选) 解释器              │
├─────────────────────────────────────────────────────────┤
│ 3.5 Pattern Layer    格局/模式匹配（连接规则-知识-Agent）│
├─────────────────────────────────────────────────────────┤
│ 3. 推理层             Ollama/Qwen/DeepSeek + RAG        │
│    （严格隔离，仅用于自然语言解释）                      │
├─────────────────────────────────────────────────────────┤
│ 2.6 Knowledge Layer  知识图谱：节点 + 关系 + 多流派      │  ← 本文档
├─────────────────────────────────────────────────────────┤
│ 2.5 Rule Layer       规则引擎：条件-结果-优先级-冲突     │
├─────────────────────────────────────────────────────────┤
│ 2. 基础层             Schema(Pydantic) | 领域模型        │
│                       历法/节气 | 确定性引擎             │
├─────────────────────────────────────────────────────────┤
│ 1. 持久化             PostgreSQL | Qdrant (RAG)          │
└─────────────────────────────────────────────────────────┘
```

## 3. 知识节点分类（NodeType 枚举）

知识层以**多态节点**为核心。所有节点共享基础字段，通过 `node_type` 区分语义类别。

| node_type          | 中文       | 典型实例                    | 适用体系                     |
|--------------------|-----------|----------------------------|------------------------------|
| `wuxing`           | 五行      | 木/火/土/金/水              | 全部                         |
| `ten_god`          | 十神      | 比肩/劫财/食神/伤官/偏财... | 八字                         |
| `heavenly_stem`    | 天干      | 甲乙丙丁戊己庚辛壬癸         | 八字/奇门                    |
| `earthly_branch`   | 地支      | 子丑寅卯辰巳午未申酉戌亥     | 全部                         |
| `palace`           | 十二宫    | 命宫/财帛/官禄/夫妻...      | 紫微                         |
| `main_star`        | 十四主星  | 紫微/天机/太阳/武曲...      | 紫微                         |
| `auxiliary_star`   | 辅星      | 左辅/右弼/文昌/文曲...      | 紫微                         |
| `shen_sha`         | 神煞      | 天乙贵人/驿马/桃花/羊刃...  | 八字/紫微                    |
| `pattern`          | 格局      | 伤官佩印/官印相生...        | 八字/紫微                    |
| `career`           | 职业      | 科研/管理/创业/艺术...      | 全部（推断结果）             |
| `personality`      | 性格      | 刚毅/柔顺/机智/沉稳...      | 全部（推断结果）             |
| `marriage`         | 婚姻      | 晚婚/早婚/配偶贤能...       | 全部（推断结果）             |
| `health`           | 健康      | 肝胆/心血管/脾胃...         | 全部（推断结果）             |
| `wealth`           | 财富      | 正财丰厚/偏财起伏...        | 全部（推断结果）             |
| `annual_fortune`   | 流年      | 甲子年/乙丑年...            | 八字/紫微                    |
| `major_luck`       | 大运      | 某步大运干支                | 八字                         |
| `yong_shen`        | 用神      | 扶抑用神/调候用神...        | 八字                         |
| `xi_shen`          | 喜神      | 喜用五行                    | 八字                         |
| `ji_shen`          | 忌神      | 忌讳五行                    | 八字                         |
| `tiao_hou`         | 调候      | 调候用神                    | 八字                         |

## 4. 知识节点结构

每个知识节点（KnowledgeNode）必须拥有：

| 字段             | 类型                 | 说明                                      |
|-----------------|----------------------|------------------------------------------|
| `id`            | string               | 全局唯一 ID，格式 `kn:{type}:{slug}`      |
| `node_type`     | NodeType (enum)      | 上表 20 种之一                            |
| `name_cn`       | string               | 中文名称                                  |
| `name_en`       | string               | 英文标识（snake_case）                    |
| `systems`       | list[string]         | 所属体系（可跨体系）                      |
| `source`        | SourceRef            | 引用来源                                  |
| `interpretation`| string               | 标准解释                                  |
| `tags`          | list[string]         | 语义标签                                  |
| `confidence`    | float [0,1]          | 可信度                                    |
| `schools`       | list[SchoolView]     | 多流派解释                                |
| `attributes`    | dict                 | 类型特定属性（多态扩展）                  |

### 4.1 多流派支持（SchoolView）

同一知识节点在不同流派中可能有不同解释。例如「七杀」在子平派和盲派中的侧重不同。

```
SchoolView:
  school: string          # 流派名称（"子平"/"盲派"/"紫微三派旧"/"中州派"）
  interpretation: string  # 该流派的解释
  source: SourceRef       # 该流派的引用来源
  weight: float           # 该流派解释的权重
```

### 4.2 类型特定属性（attributes）

`attributes` 是多态扩展点，不同 `node_type` 携带不同结构化属性。例如：

- `wuxing`：`{ yin_yang, season, direction, color, organ }`
- `ten_god`：`{ relation_to_day_master, element, polarity }`
- `main_star`：`{ wuxing_attribute, brightness_levels, palace_association }`
- `career`：`{ industry, element_preference, risk_level }`

`attributes` 中的键是**有记录的**（每种 node_type 有预定义键集合），不是自由 dict。

## 5. 知识查询接口（设计契约）

知识层向消费者暴露以下查询能力（Protocol 定义，Phase 6 仅设计不实现）：

```
KnowledgeStore Protocol:
  get_node(node_id) -> KnowledgeNode | None
  query_nodes(node_type, tags, systems) -> list[KnowledgeNode]
  get_relations(node_id, relation_type, direction) -> list[Relation]
  find_path(source_id, target_id, max_depth) -> list[Relation]
  resolve_school(node_id, school) -> SchoolView | None
```

## 6. 与现有架构的集成点

- **不修改** `src/openmetaphysics/agents/` 下任何已稳定模块。
- 知识层是**只读参考层**：现有引擎的 `calculate()` 逻辑不变。
- 知识节点 ID 可被 `ReasoningStep.rule_ref` 引用，使推理链可追溯到具体知识点。
- RAG 检索器（`KnowledgeRetriever`）可将知识节点作为检索增强来源，而非取代计算。
- Pattern Layer（文件 3）通过知识节点 ID 引用知识点，构建格局定义。
