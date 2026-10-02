"""Production Consensus Layer models.

Independent Production-Runtime implementation of the frozen Reference
Consensus Layer contract (``reference/contracts/consensus_contract.json``
v1.0.0). Mirrors the observable contract only; it does not import the
Reference Runtime.

Architecture boundary: this layer consumes Evidence only. It does not call
rule engines, pattern matchers, knowledge stores, or any LLM.
"""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# == Enums ==


class Domain(str, Enum):
    """Result domains (10 values), mirroring the frozen contract."""

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


class ResultDirection(str, Enum):
    """Result direction (3 values)."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class EvidenceType(str, Enum):
    """Evidence source types (4 values)."""

    RULE = "rule"
    PATTERN = "pattern"
    KNOWLEDGE_NODE = "knowledge_node"
    RELATION = "relation"


class ConsensusStrategy(str, Enum):
    """Conflict resolution strategy."""

    RETAIN_ALL = "retain_all"
    HIGHEST_CONFIDENCE = "highest_confidence"
    MAJORITY = "majority"


# == Deterministic ID generation ==


def _content_hash(*parts: str) -> str:
    """Deterministic 12-char hex hash from string parts."""
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def make_conclusion_id(domain: str, conclusion: str, evidence_ids: list[str]) -> str:
    """Deterministic ConsensusConclusion ID (``cc:<domain>:<hash>``)."""
    h = _content_hash(domain, conclusion, "|".join(sorted(evidence_ids)))
    return f"cc:{domain}:{h}"


def make_report_id(conclusion_ids: list[str]) -> str:
    """Deterministic ConsensusReport ID (``cr:<hash>``)."""
    if not conclusion_ids:
        return "cr:" + _content_hash("empty")
    h = _content_hash("|".join(sorted(conclusion_ids)))
    return f"cr:{h}"


# == Evidence ==


class EvidenceItem(BaseModel):
    """A single evidence item produced by an upstream layer."""

    model_config = ConfigDict(extra="forbid")
    evidence_id: str
    source_type: EvidenceType
    source_id: str
    system: str
    domain: Domain
    confidence: float
    conclusion: str
    direction: ResultDirection | None = None
    weight: float = 1.0
    trace: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: str | None = None
    version: str = "1.0.0"


class Evidence(BaseModel):
    """Evidence consumed by the Consensus Engine."""

    model_config = ConfigDict(extra="forbid")
    evidence_id: str
    domain: Domain
    conclusion: str
    confidence: float
    system: str
    items: list[EvidenceItem] = Field(min_length=1)
    version: str = "1.0.0"


# == ConsensusConfig ==


class ConsensusConfig(BaseModel):
    """Configuration for the Consensus Engine."""

    model_config = ConfigDict(extra="forbid")
    strategy: ConsensusStrategy = ConsensusStrategy.RETAIN_ALL
    cross_system_bonus_per_system: float = Field(default=0.1, ge=0.0, le=1.0)
    max_cross_system_bonus: float = Field(default=0.3, ge=0.0, le=1.0)
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    max_confidence: float = Field(default=1.0, ge=0.0, le=1.0)


# == ConsensusInput ==


class ConsensusInput(BaseModel):
    """Input to the Consensus Engine: Evidence[] + config."""

    model_config = ConfigDict(extra="forbid")
    evidence: list[Evidence] = Field(default_factory=list)
    config: ConsensusConfig = Field(default_factory=ConsensusConfig)


# == ConsensusConclusion ==


class ConsensusConclusion(BaseModel):
    """A consensus conclusion derived from one or more Evidence."""

    model_config = ConfigDict(extra="forbid")
    conclusion_id: str
    domain: Domain
    conclusion: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)
    evidence_count: int = Field(default=0, ge=0)
    systems: list[str] = Field(default_factory=list)
    direction: ResultDirection | None = None
    is_conflict: bool = False
    strategy: ConsensusStrategy = ConsensusStrategy.RETAIN_ALL
    metadata: dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"


# == ConsensusReport ==


class ConsensusReport(BaseModel):
    """Full consensus report produced by the Consensus Engine."""

    model_config = ConfigDict(extra="forbid")
    report_id: str
    overall_confidence: float = Field(ge=0.0, le=1.0)
    domains: list[Domain] = Field(default_factory=list)
    conclusions: list[ConsensusConclusion] = Field(default_factory=list)
    conflicts: list[ConsensusConclusion] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"
