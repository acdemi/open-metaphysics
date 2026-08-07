"""Reference Rule models -- Phase 6B Reference Implementation Sprint 1.

Faithful reimplementation of Phase 6 Pydantic models for the Rule layer.
See: docs/design/phase6/04_pydantic_models.md

This is a REFERENCE implementation, not the formal production code.
Pure Python, in-memory, single-threaded. No DB, no gRPC, no LLM.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ── Enums ──────────────────────────────────────────────────────────


class MetaphysicsSystem(str, Enum):
    BAZI = "bazi"
    ZIWEI = "ziwei"
    QIMEN = "qimen"
    LIUYAO = "liuyao"
    MEIHUA = "meihua"
    LIREN = "liren"


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


# ── Shared models ──────────────────────────────────────────────────


class SourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(description="典籍名称")
    chapter: str | None = None
    author: str | None = None
    page: int | None = None
    url: str | None = None
    credibility: float = Field(default=0.8, ge=0.0, le=1.0)


# ── Rule layer models ──────────────────────────────────────────────


class RuleCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str = Field(description="排盘数据路径")
    operator: ConditionOperator
    value: Any | None = None
    negate: bool = False
    description: str = ""


class RuleResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    domain: Domain
    conclusion: str
    conclusion_node_id: str | None = None
    weight: float = Field(ge=0.0, le=1.0)
    direction: ResultDirection = ResultDirection.POSITIVE


class RuleScope(BaseModel):
    model_config = ConfigDict(extra="forbid")
    systems: list[MetaphysicsSystem]
    gender: list[Literal["male", "female"]] | None = None
    age_range: tuple[int, int] | None = None
    lunar_month_range: tuple[int, int] | None = None


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(
        pattern=r"^rule:[a-z]+:[a-z_]+:v[0-9]+(#\d+)?$",
        description="Rule ID, optionally with #N suffix for DNF-expanded rules",
    )
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
    """Result of evaluating a single Rule against chart data."""

    model_config = ConfigDict(extra="forbid")
    rule_id: str
    matched: bool
    results: list[RuleResult] = Field(default_factory=list)
    priority: int = 0
    confidence: float = 0.0
