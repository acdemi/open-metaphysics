"""Reference Evidence Layer -- Phase 6B Sprint 3.

The Evidence Layer is the Canonical Exchange Model for the entire
reasoning system. From this Sprint onward, Rule, Pattern, Knowledge,
and Consensus modules do NOT couple directly. All inter-module data
exchange flows through Evidence.

    RuleEvaluation  -->  EvidenceItem
    PatternMatch    -->  EvidenceItem
    KnowledgeNode   -->  EvidenceItem  (future, protocol only)

    EvidenceItem  -->  Evidence  (grouped by domain + conclusion)
    Evidence[]    -->  ConsensusEngine  (future Sprint)

Design rationale:
  - EvidenceItem is the Core Domain Model. Every reasoning result
    must be converted to EvidenceItem before entering the Evidence
    Layer.
  - The Consensus Engine (future) will consume Evidence (grouped
    EvidenceItems), never raw RuleEvaluation or PatternMatch.
  - Future metaphysics systems (bazi, ziwei, qimen, liuren, meihua)
    must convert their outputs to EvidenceItem before participating
    in consensus.

See: docs/design/phase6/03_json_schemas.md  (Evidence JSON Schema)
     docs/design/phase6/06_flow_diagram.md  (Evidence flow)
     docs/design/phase6/09_test_plan.md     (Evidence layer tests)
"""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from .models import Domain, ResultDirection

# == Enums ==


class EvidenceType(str, Enum):
    """The type of source that produced this evidence.

    Maps to Phase 6 EvidenceItem.source_type enum:
    rule | pattern | knowledge_node | relation
    """

    RULE = "rule"
    PATTERN = "pattern"
    KNOWLEDGE_NODE = "knowledge_node"
    RELATION = "relation"


# == Deterministic ID generation ==


def _content_hash(*parts: str) -> str:
    """Generate a deterministic 12-char hex hash from string parts."""
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def make_evidence_item_id(
    source_type: str,
    source_id: str,
    system: str,
    conclusion: str,
    index: int = 0,
) -> str:
    """Generate a deterministic EvidenceItem ID.

    Same inputs always produce the same ID (content-addressed).
    Format: ``ev:<system>:<12-char-hash>``
    """
    h = _content_hash(source_type, source_id, system, conclusion, index)
    return f"ev:{system}:{h}"


def make_evidence_group_id(
    domain: str,
    conclusion: str,
    item_ids: list[str],
) -> str:
    """Generate a deterministic Evidence (group) ID.

    The ID is derived from the domain, conclusion, and the sorted
    set of member EvidenceItem IDs, so identical groupings always
    produce the same ID.
    """
    h = _content_hash(domain, conclusion, "|".join(sorted(item_ids)))
    return f"ev:{domain}:{h}"


# == EvidenceSource ==


class EvidenceSource(BaseModel):
    """Describes the citation source of an evidence item.

    Carries human-readable provenance: which text, which chapter,
    and how credible the source is. Built from Phase 6 ``SourceRef``
    or from PatternMatch metadata.
    """

    model_config = ConfigDict(extra="forbid")
    source_type: EvidenceType
    source_id: str = Field(description="Rule / Pattern / KnowledgeNode ID")
    source_name: str = Field(default="", description="Human-readable name")
    source_ref: str = Field(default="", description="Citation text (e.g. 典籍名称)")
    credibility: float = Field(default=0.8, ge=0.0, le=1.0)


# == EvidenceItem ==


class EvidenceItem(BaseModel):
    """Atomic, self-contained evidence unit -- the Core Domain Model.

    Every reasoning result (rule match, pattern match, future
    knowledge node) must be converted to EvidenceItem before
    entering the Evidence Layer.

    Required fields (per Sprint 3 contract):
      evidence_id, source_type, source_id, system, confidence,
      conclusion, trace, metadata, version

    Additional fields for consensus support:
      domain, direction, weight
    """

    model_config = ConfigDict(extra="forbid")
    evidence_id: str = Field(description="Deterministic content-based ID")
    source_type: EvidenceType
    source_id: str = Field(description="ID of the originating rule/pattern/node")
    system: str = Field(description="Metaphysics system: bazi, ziwei, qimen, ...")
    domain: Domain
    confidence: float = Field(ge=0.0, le=1.0)
    conclusion: str
    direction: ResultDirection | None = None
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    trace: list[str] = Field(
        default_factory=list,
        description="Ordered traceability chain of source IDs",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible provenance and enrichment data",
    )
    timestamp: str | None = Field(default=None, description="ISO-8601 timestamp, optional")
    version: str = Field(default="1.0.0", description="Contract version")


# == Evidence (grouped container) ==


class Evidence(BaseModel):
    """A grouped collection of EvidenceItems sharing a domain + conclusion.

    Corresponds to Phase 6 Evidence JSON Schema:
    ``{domain, conclusion, confidence, evidence_items}``

    The Consensus Engine consumes ``list[Evidence]``.
    Items within one Evidence all support the same conclusion.
    """

    model_config = ConfigDict(extra="forbid")
    evidence_id: str = Field(description="Deterministic group ID")
    domain: Domain
    conclusion: str
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Aggregated confidence (max of item confidences)",
    )
    system: str = Field(description="Primary system, or 'multi' for cross-system")
    items: list[EvidenceItem] = Field(min_length=1)
    version: str = Field(default="1.0.0")


# == Knowledge Protocol (interface only, no implementation) ==


@runtime_checkable
class KnowledgeEvidenceProvider(Protocol):
    """Protocol for converting Knowledge nodes to Evidence.

    NOT implemented in Sprint 3. This interface exists so that
    future sprints can provide a concrete implementation backed
    by KnowledgeStore without changing the Evidence Layer contract.

    Contract:
      - ``from_knowledge_node`` returns an EvidenceItem for a single
        knowledge node, or None if the node is not found / not
        applicable.
      - ``from_knowledge_nodes`` returns EvidenceItems for all
        applicable nodes (non-None results).

    Any future KnowledgeStore adapter MUST implement this protocol.
    """

    def from_knowledge_node(
        self,
        node_id: str,
        system: str,
    ) -> EvidenceItem | None:
        """Convert a single knowledge node to an EvidenceItem."""
        ...

    def from_knowledge_nodes(
        self,
        node_ids: list[str],
        system: str,
    ) -> list[EvidenceItem]:
        """Convert multiple knowledge nodes to EvidenceItems."""
        ...
