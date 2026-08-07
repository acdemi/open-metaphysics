"""Reference Consensus Layer Models -- Phase 6B Sprint 5.

The Consensus Engine consumes Evidence[] and produces
ConsensusConclusion[] grouped into a ConsensusReport.

Architecture Boundary:
  Consensus ONLY consumes Evidence. It does NOT call RuleEngine,
  PatternMatcher, KnowledgeStore, or LLM. It does NOT re-reason,
  re-calculate rules, modify Evidence, or add new Patterns.

  Evidence[] --> ConsensusConclusion[] --> ConsensusReport

See: docs/design/phase6/03_json_schemas.md (EvidenceConsensusReport)
     docs/design/phase6/06_flow_diagram.md
     docs/specification/CONSENSUS_BEHAVIOR_SPEC.md
"""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .evidence import Evidence
from .models import Domain, ResultDirection

# == Enums ==


class ConsensusStrategy(str, Enum):
    """Conflict resolution strategy for the Consensus Engine."""

    RETAIN_ALL = "retain_all"
    HIGHEST_CONFIDENCE = "highest_confidence"
    MAJORITY = "majority"


# == Deterministic ID generation ==


def _content_hash(*parts: str) -> str:
    """Generate a deterministic 12-char hex hash from string parts."""
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def make_conclusion_id(
    domain: str,
    conclusion: str,
    evidence_ids: list[str],
) -> str:
    """Generate a deterministic ConsensusConclusion ID."""
    h = _content_hash(domain, conclusion, "|".join(sorted(evidence_ids)))
    return f"cc:{domain}:{h}"


def make_report_id(conclusion_ids: list[str]) -> str:
    """Generate a deterministic ConsensusReport ID."""
    if not conclusion_ids:
        return "cr:" + _content_hash("empty")
    h = _content_hash("|".join(sorted(conclusion_ids)))
    return f"cr:{h}"


# == ConsensusConfig ==


class ConsensusConfig(BaseModel):
    """Configuration for the Consensus Engine.

    All parameters are configurable. No complex mathematical models.
    """

    model_config = ConfigDict(extra="forbid")
    strategy: ConsensusStrategy = ConsensusStrategy.RETAIN_ALL
    cross_system_bonus_per_system: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Bonus added per additional system contributing to a conclusion",
    )
    max_cross_system_bonus: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Maximum total cross-system bonus",
    )
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    max_confidence: float = Field(default=1.0, ge=0.0, le=1.0)


# == ConsensusInput ==


class ConsensusInput(BaseModel):
    """Input to the Consensus Engine.

    ONLY accepts Evidence[]. RuleEvaluation, PatternMatch, and
    KnowledgeNode are NOT accepted -- they must be converted to
    Evidence first via the Evidence Layer.
    """

    model_config = ConfigDict(extra="forbid")
    evidence: list[Evidence] = Field(
        default_factory=list,
        description="Evidence list to consensus",
    )
    config: ConsensusConfig = Field(default_factory=ConsensusConfig)


# == ConsensusConclusion ==


class ConsensusConclusion(BaseModel):
    """A single consensus conclusion derived from one or more Evidence.

    Multiple Evidence supporting the same (domain, conclusion) are
    merged into one ConsensusConclusion with aggregated confidence.
    """

    model_config = ConfigDict(extra="forbid")
    conclusion_id: str = Field(description="Deterministic content-based ID")
    domain: Domain
    conclusion: str
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Aggregated confidence (base + cross-system bonus)",
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="All Evidence IDs supporting this conclusion",
    )
    evidence_count: int = Field(default=0, ge=0)
    systems: list[str] = Field(
        default_factory=list,
        description="Distinct systems contributing, sorted",
    )
    direction: ResultDirection | None = None
    is_conflict: bool = Field(
        default=False,
        description="True if other conclusions existed in the same domain",
    )
    strategy: ConsensusStrategy = ConsensusStrategy.RETAIN_ALL
    metadata: dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"


# == ConsensusReport ==


class ConsensusReport(BaseModel):
    """Full consensus report produced by the Consensus Engine.

    Corresponds to Phase 6 EvidenceConsensusReport schema.
    """

    model_config = ConfigDict(extra="forbid")
    report_id: str = Field(description="Deterministic report ID")
    overall_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Average of surviving conclusion confidences",
    )
    domains: list[Domain] = Field(
        default_factory=list,
        description="All domains with conclusions, sorted",
    )
    conclusions: list[ConsensusConclusion] = Field(
        default_factory=list,
        description="Surviving conclusions, sorted by domain then confidence",
    )
    conflicts: list[ConsensusConclusion] = Field(
        default_factory=list,
        description="Conclusions dropped by the conflict strategy",
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="All Evidence IDs consumed, sorted",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"
