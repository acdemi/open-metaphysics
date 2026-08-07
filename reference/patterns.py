"""Reference Pattern models -- Phase 6B Sprint 2.

Extends Phase 6 Pattern/PatternMatch with PatternRequirement,
PatternEvidence, and PatternCategory for the reference matcher.

See: docs/design/phase6/04_pydantic_models.md (Pattern Layer)
     docs/design/phase6/07_adr.md (ADR-004: Pattern as cross-system comparison unit)
"""

from __future__ import annotations

from enum import Enum

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .models import Domain, SourceRef

# ── Enums ──────────────────────────────────────────────────────────


class PatternCategory(str, Enum):
    GEJU = "geju"
    SHENSHA = "shensha"
    RELATION = "relation"
    WUXING = "wuxing"
    CROSS_SYSTEM = "cross_system"
    PERSONALITY = "personality"
    CAREER = "career"


class RequirementLogic(str, Enum):
    ALL = "all"
    ANY = "any"


# ── Models ─────────────────────────────────────────────────────────


class PatternRequirement(BaseModel):
    """Defines which rules must match for a pattern to trigger."""

    model_config = ConfigDict(extra="forbid")
    rule_ids: list[str] = Field(min_length=1)
    logic: RequirementLogic = RequirementLogic.ALL
    min_matches: int = Field(default=1, ge=1)


class PatternEvidence(BaseModel):
    """Evidence from a single rule evaluation contributing to a pattern."""

    model_config = ConfigDict(extra="forbid")
    rule_id: str
    system: str
    matched: bool
    conclusions: list[str] = Field(default_factory=list)


class Pattern(BaseModel):
    """A definable pattern that can be identified from rule evaluations."""

    model_config = ConfigDict(extra="forbid")
    pattern_id: str = Field(pattern=r"^pattern:[a-z_]+:[a-z_0-9]+:v[0-9]+$")
    name: str
    description: str = ""
    rule_ids: list[str] = Field(default_factory=list)
    knowledge_node_ids: list[str] = Field(default_factory=list)
    category: PatternCategory
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    systems: list[str] = Field(default_factory=list)
    requirements: list[PatternRequirement] = Field(default_factory=list)
    domain_tags: list[Domain] = Field(default_factory=list)
    source: SourceRef | None = None
    version: str = "1.0.0"


class PatternMatch(BaseModel):
    """Result of attempting to match a Pattern against rule evaluations."""

    model_config = ConfigDict(extra="forbid")
    pattern_id: str
    pattern_name: str
    matched: bool
    matched_by: str = Field(description="System or agent that identified this pattern")
    confidence: float = Field(ge=0.0, le=1.0)
    matched_rule_ids: list[str] = Field(default_factory=list)
    evidence: list[PatternEvidence] = Field(default_factory=list)
    knowledge_node_ids: list[str] = Field(default_factory=list)
    category: PatternCategory | None = None


# ── Pattern YAML parser ────────────────────────────────────────────


def parse_pattern_document(yaml_text: str) -> Pattern:
    """Parse a YAML pattern document into a Pattern object."""
    doc = yaml.safe_load(yaml_text)
    if not isinstance(doc, dict) or "pattern" not in doc:
        raise ValueError("YAML must contain a top-level pattern mapping")
    return Pattern(**doc["pattern"])


def parse_pattern_file(path: str) -> Pattern:
    """Parse a YAML pattern file into a Pattern object."""
    with open(path, encoding="utf-8") as f:
        return parse_pattern_document(f.read())


def parse_pattern_files(directory: str) -> list[Pattern]:
    """Parse all .yaml pattern files in a directory."""
    import pathlib

    d = pathlib.Path(directory)
    patterns = []
    for p in sorted(d.glob("*.yaml")):
        patterns.append(parse_pattern_file(str(p)))
    return patterns
