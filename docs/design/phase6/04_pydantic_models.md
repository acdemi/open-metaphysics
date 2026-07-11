# Pydantic v2 模型定义

> 状态：设计 v1 (2026-07-11)
> 本文件仅定义 Schema 模型（Pydantic BaseModel），不含任何业务逻辑实现。
> 未来实现阶段将放置于 `src/openmetaphysics/knowledge/schemas.py` 和 `src/openmetaphysics/rules/schemas.py`。

## 1. 共享类型

```python
from __future__ import annotations
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class MetaphysicsSystem(str, Enum):
    BAZI = "bazi"
    ZIWEI = "ziwei"
    QIMEN = "qimen"
    LIUYAO = "liuyao"
    MEIHUA = "meihua"
    LIREN = "liuren"


class Domain(str, Enum):
    CAREER = "career"
    PERSONALITY = "personality"
    MARRIAGE = "marriage"
    HEALTH = "health"
    WEALTH = "wealth"
    EDUCATION = "education"
    FAMILY = "family"
    TRAVEL = "travel"
    LEGAL = "legal"
    OVERALL = "overall"


class SourceRef(BaseModel):
    """引用来源--所有规则、知识节点、关系必须标注经典出处。"""
    model_config = ConfigDict(extra="forbid")
    text: str = Field(description="典籍名称，如 '滴天髓'")
    chapter: str | None = None
    author: str | None = None
    page: int | None = None
    url: str | None = None
    credibility: float = Field(default=0.8, ge=0.0, le=1.0)


class SchoolView(BaseModel):
    """多流派解释--同一知识节点在不同流派中的不同表达。"""
    model_config = ConfigDict(extra="forbid")
    school: str = Field(description="流派名称，如 '子平'/'盲派'/'中州派'")
    interpretation: str
    source: SourceRef
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
```

## 2. Rule 层模型

```python
class RuleType(str, Enum):
    PATTERN_RECOGNITION = "pattern_recognition"
    RELATION_DERIVATION = "relation_derivation"
    TEN_GOD_DETERMINATION = "ten_god_determination"
    YONG_SHEN_DETERMINATION = "yong_shen_determination"
    ELEMENT_BALANCE = "element_balance"
    DOMAIN_INFERENCE = "domain_inference"
    CONFLICT_RESOLUTION = "conflict_resolution"
    DA_YUN_ANALYSIS = "da_yun_analysis"


class ConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    MATCHES = "matches"


class ConflictStrategy(str, Enum):
    HIGHEST_PRIORITY_WINS = "highest_priority_wins"
    RETAIN_ALL = "retain_all"
    MERGE = "merge"


class ResultDirection(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class RuleCondition(BaseModel):
    """规则条件--指向已计算的排盘结构化数据路径。"""
    model_config = ConfigDict(extra="forbid")
    field: str = Field(description="排盘数据路径，如 'pillars[0].ten_gods_stem'")
    operator: ConditionOperator
    value: Any | None = None
    negate: bool = False
    description: str = ""


class RuleResult(BaseModel):
    """规则结果--指向领域结论。"""
    model_config = ConfigDict(extra="forbid")
    domain: Domain
    conclusion: str
    conclusion_node_id: str | None = None
    weight: float = Field(ge=0.0, le=1.0)
    direction: ResultDirection = ResultDirection.POSITIVE


class RuleScope(BaseModel):
    """规则适用范围。"""
    model_config = ConfigDict(extra="forbid")
    systems: list[MetaphysicsSystem]
    gender: list[Literal["male", "female"]] | None = None
    age_range: tuple[int, int] | None = None
    lunar_month_range: tuple[int, int] | None = None


class Rule(BaseModel):
    """规则--可结构化表示的命理推理规则。"""
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^rule:[a-z]+:[a-z_]+:v[0-9]+$")
    name: str
    name_en: str = ""
    system: MetaphysicsSystem
    rule_type: RuleType
    conditions: list[RuleCondition] = Field(min_length=1)
    results: list[RuleResult] = Field(min_length=1)
    priority: int = Field(default=50, ge=0, le=100)
    scope: RuleScope | None = None
    conflicts: list[str] = Field(default_factory=list)
    conflict_strategy: ConflictStrategy = ConflictStrategy.RETAIN_ALL
    source: SourceRef
    confidence: float = Field(ge=0.0, le=1.0)
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    deprecated: bool = False
    superseded_by: str | None = None


class RuleEvaluation(BaseModel):
    """规则评估结果--单条规则对某排盘的匹配结果。"""
    model_config = ConfigDict(extra="forbid")
    rule_id: str
    matched: bool
    results: list[RuleResult] = Field(default_factory=list)
    evaluation_trace: list[dict[str, Any]] = Field(default_factory=list)
```

## 3. Knowledge 层模型

```python
class NodeType(str, Enum):
    WUXING = "wuxing"
    TEN_GOD = "ten_god"
    HEAVENLY_STEM = "heavenly_stem"
    EARTHLY_BRANCH = "earthly_branch"
    PALACE = "palace"
    MAIN_STAR = "main_star"
    AUXILIARY_STAR = "auxiliary_star"
    SHEN_SHA = "shen_sha"
    PATTERN = "pattern"
    CAREER = "career"
    PERSONALITY = "personality"
    MARRIAGE = "marriage"
    HEALTH = "health"
    WEALTH = "wealth"
    ANNUAL_FORTUNE = "annual_fortune"
    MAJOR_LUCK = "major_luck"
    YONG_SHEN = "yong_shen"
    XI_SHEN = "xi_shen"
    JI_SHEN = "ji_shen"
    TIAO_HOU = "tiao_hou"


class KnowledgeNode(BaseModel):
    """知识节点--命理知识图谱的原子单元。"""
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^kn:[a-z_]+:[a-z_0-9]+$")
    node_type: NodeType
    name_cn: str
    name_en: str
    systems: list[MetaphysicsSystem] = Field(min_length=1)
    source: SourceRef
    interpretation: str
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    schools: list[SchoolView] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="类型特定属性，按 node_type 预定义键集合"
    )
```

## 4. Relation 层模型

```python
class RelationType(str, Enum):
    SHENG = "sheng"
    KE = "ke"
    CHONG = "chong"
    XING = "xing"
    HE = "he"
    HAI = "hai"
    FUZHU = "fuzhu"
    ZHIYUE = "zhiyue"
    DUIYING = "duiying"
    YINGXIANG = "yingxiang"
    ZENGQIANG = "zengqiang"
    XUEROU = "xueroo"
    ZHIXIANG = "zhixiang"
    SHUYU = "shuyu"
    YINYONG = "yinyong"


class RelationDirection(str, Enum):
    DIRECTED = "directed"
    UNDIRECTED = "undirected"


class RelationEvidence(BaseModel):
    """关系证据--支持此关系成立的来源。"""
    model_config = ConfigDict(extra="forbid")
    description: str
    source: SourceRef
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class Relation(BaseModel):
    """知识节点间的关系--有向加权边。"""
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^rel:.+$")
    source_node_id: str
    target_node_id: str
    relation_type: RelationType
    direction: RelationDirection = RelationDirection.DIRECTED
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: list[RelationEvidence] = Field(default_factory=list)
    source: SourceRef
    conditions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="关系生效的条件（可选）"
    )
```

## 5. Evidence 层模型

```python
class EvidenceSourceType(str, Enum):
    RULE = "rule"
    PATTERN = "pattern"
    KNOWLEDGE_NODE = "knowledge_node"
    RELATION = "relation"


class EvidenceItem(BaseModel):
    """单条证据--指向规则、格局或知识点。"""
    model_config = ConfigDict(extra="forbid")
    source_type: EvidenceSourceType
    source_id: str
    source_name: str
    source_ref: str = Field(description="引用来源文本，如 '滴天髓'")
    weight: float = Field(ge=0.0, le=1.0)
    agent: str | None = None


class Evidence(BaseModel):
    """证据集--Consensus Agent 不直接输出结论，必须输出 Evidence。"""
    model_config = ConfigDict(extra="forbid")
    domain: Domain
    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_items: list[EvidenceItem] = Field(min_length=1)
```

## 6. Pattern 层模型

```python
class Pattern(BaseModel):
    """格局/模式--连接规则、知识节点和智能体。

    Consensus Agent 不直接比较 JSON，而比较 Pattern。
    多个 Agent 可共同识别同一个 Pattern。
    """
    model_config = ConfigDict(extra="forbid")
    id: str = Field(pattern=r"^pattern:[a-z_]+:[a-z_0-9]+:v[0-9]+$")
    name_cn: str
    name_en: str
    systems: list[MetaphysicsSystem] = Field(min_length=1)
    rule_ids: list[str] = Field(
        default_factory=list,
        description="组成此格局的规则 ID 列表"
    )
    knowledge_node_ids: list[str] = Field(
        default_factory=list,
        description="关联的知识节点 ID"
    )
    agent_identifiers: list[str] = Field(
        default_factory=list,
        description="能识别此格局的智能体名称"
    )
    domain_tags: list[Domain] = Field(default_factory=list)
    interpretation: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: SourceRef
    version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")


class PatternMatch(BaseModel):
    """格局匹配结果--某排盘中识别到的格局实例。"""
    model_config = ConfigDict(extra="forbid")
    pattern_id: str
    pattern_name: str
    matched_by: str = Field(description="识别此格局的智能体名称")
    confidence: float = Field(ge=0.0, le=1.0)
    matched_rule_ids: list[str] = Field(default_factory=list)
    matched_node_ids: list[str] = Field(default_factory=list)
```

## 7. Evidence-Based Consensus 模型

```python
class ConclusionWithEvidence(BaseModel):
    """带证据的结论--支持多个不同结论同时存在。"""
    model_config = ConfigDict(extra="forbid")
    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_items: list[EvidenceItem] = Field(min_length=1)
    contributing_agents: list[str] = Field(default_factory=list)


class DomainConsensus(BaseModel):
    """单领域共识--该领域内多结论并存，按置信度降序。"""
    model_config = ConfigDict(extra="forbid")
    domain: Domain
    conclusions: list[ConclusionWithEvidence] = Field(
        min_length=1,
        description="多个不同结论同时存在，按 confidence 降序排列"
    )


class ConsensusConflict(BaseModel):
    """跨智能体冲突。"""
    model_config = ConfigDict(extra="forbid")
    agents: list[str]
    domain: Domain
    conclusions: list[str]
    severity: Literal["low", "medium", "high"]
    resolution: Literal["retain_all", "highest_confidence", "merged"] = "retain_all"


class EvidenceConsensusReport(BaseModel):
    """Evidence-Based Consensus 报告--取代旧的 Weighted Average ConsensusReport。

    共识不是投票，而是 Evidence Aggregation：
    - 收集所有智能体的 PatternMatch 和 RuleEvaluation
    - 按领域聚合证据
    - 同一领域内多个结论可并存
    - 每个结论附带全部支持证据
    """
    model_config = ConfigDict(extra="forbid")
    request_id: str
    domains: list[DomainConsensus] = Field(
        min_length=1,
        description="每个领域的共识结果"
    )
    aggregation_method: Literal["evidence_based"] = "evidence_based"
    cross_domain_patterns: list[str] = Field(
        default_factory=list,
        description="跨体系识别到的 Pattern ID 列表"
    )
    conflicts: list[ConsensusConflict] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)
```

## 8. 与现有 Schema 的关系

| 现有模型（core/schemas.py） | Phase 6 新模型 | 关系 |
|------------------------------|----------------|------|
| `ReasoningStep.rule_ref` | `Rule.id` | rule_ref 值映射到 Rule.id |
| `ConfidenceScore` | `Evidence.confidence` | confidence 现可由证据聚合推导 |
| `ConsensusReport`（旧） | `EvidenceConsensusReport`（新） | 新报告取代旧报告，支持多结论并存 |
| `AgentOutput.result` | `RuleEvaluation` + `PatternMatch` | 引擎计算后追加规则评估和格局匹配 |
| `Conflict` | `ConsensusConflict` | 扩展支持领域和消解策略 |

> **向后兼容**：现有 `ConsensusReport` 保留为 legacy 模式，新报告通过 `aggregation_method="evidence_based"` 区分。
> 现有引擎代码**不修改**--规则评估和格局匹配作为**后处理步骤**附加。
