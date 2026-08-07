"""Reference Knowledge Layer Models -- Phase 6B Sprint 4.

Faithful reimplementation of Phase 6 KnowledgeNode, Relation, and
SchoolView models, plus the new KnowledgeReference model for
citation/reference tracking.

Architecture Boundary:
  Knowledge is a READ-ONLY citation/reference provider.
  It CANNOT participate in reasoning, generate conclusions,
  modify Evidence, increase Confidence, or call Rule.
  See: docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md

See: docs/design/phase6/01_knowledge_layer_architecture.md
     docs/design/phase6/03_json_schemas.md (KnowledgeNode, Relation)
     docs/design/phase6/04_pydantic_models.md
"""

from __future__ import annotations

from enum import Enum
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .models import MetaphysicsSystem, SourceRef

# == Enums ==


class NodeType(str, Enum):
    """Knowledge node type -- 20 categories per Phase 6."""

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


class RelationType(str, Enum):
    """Relation type -- 15 categories per Phase 6."""

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


class ReferenceType(str, Enum):
    """Type of knowledge reference/citation."""

    CLASSIC_TEXT = "classic_text"
    SCHOOL_COMMENTARY = "school_commentary"
    MODERN_INTERPRETATION = "modern_interpretation"
    ORAL_TRADITION = "oral_tradition"


class ReferenceTarget(str, Enum):
    """Whether a reference points to a node or a relation."""

    NODE = "node"
    RELATION = "relation"


# == Shared models ==


class SchoolView(BaseModel):
    """Multi-school interpretation of a knowledge node."""

    model_config = ConfigDict(extra="forbid")
    school: str = Field(description="School name, e.g. 'ziping'/'mangpai'")
    interpretation: str
    source: SourceRef
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


class RelationEvidence(BaseModel):
    """Evidence supporting a relation."""

    model_config = ConfigDict(extra="forbid")
    description: str
    source: SourceRef
    weight: float = Field(default=1.0, ge=0.0, le=1.0)


# == KnowledgeNode ==


class KnowledgeNode(BaseModel):
    """Knowledge node -- atomic unit of the metaphysics knowledge graph.

    Structure only. No database, no cache, no index.
    Implements Phase 6 KnowledgeNode schema.
    """

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
        description="Type-specific attributes, keyed by node_type",
    )


# == KnowledgeRelation ==


class KnowledgeRelation(BaseModel):
    """Directed weighted edge between knowledge nodes.

    Implements Phase 6 Relation schema.
    Supports: citation relations, classic text origins, school origins,
    multiple sources (via evidence list and source field).
    """

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
        description="Optional conditions for relation activation",
    )


# == KnowledgeReference ==


class KnowledgeReference(BaseModel):
    """A citation/reference linking a knowledge node or relation to
    a source text.

    Supports multiple sources per node (multiple KnowledgeReference
    entries with the same target_id), classic text origins, school
    commentary origins, and modern interpretations.
    """

    model_config = ConfigDict(extra="forbid")
    reference_id: str = Field(pattern=r"^ref:[a-z_]+:[a-z_0-9]+$")
    target_type: ReferenceTarget
    target_id: str = Field(description="Node ID or relation ID being referenced")
    ref_type: ReferenceType
    source: SourceRef
    passage: str = Field(default="", description="Quoted passage or summary")
    school: str | None = Field(
        default=None, description="School name if ref_type is school_commentary"
    )
    credibility: float = Field(default=0.8, ge=0.0, le=1.0)


# == YAML Parsers ==


def parse_nodes_document(yaml_text: str) -> list[KnowledgeNode]:
    """Parse a YAML document with a top-level ``nodes`` list."""
    doc = yaml.safe_load(yaml_text)
    if not isinstance(doc, dict) or "nodes" not in doc:
        raise ValueError("YAML must contain a top-level nodes list")
    return [KnowledgeNode(**n) for n in doc["nodes"]]


def parse_nodes_file(path: str) -> list[KnowledgeNode]:
    """Parse a YAML file containing knowledge nodes."""
    with open(path, encoding="utf-8") as f:
        return parse_nodes_document(f.read())


def parse_relations_document(yaml_text: str) -> list[KnowledgeRelation]:
    """Parse a YAML document with a top-level ``relations`` list."""
    doc = yaml.safe_load(yaml_text)
    if not isinstance(doc, dict) or "relations" not in doc:
        raise ValueError("YAML must contain a top-level relations list")
    return [KnowledgeRelation(**r) for r in doc["relations"]]


def parse_relations_file(path: str) -> list[KnowledgeRelation]:
    """Parse a YAML file containing knowledge relations."""
    with open(path, encoding="utf-8") as f:
        return parse_relations_document(f.read())


def parse_references_document(yaml_text: str) -> list[KnowledgeReference]:
    """Parse a YAML document with a top-level ``references`` list."""
    doc = yaml.safe_load(yaml_text)
    if not isinstance(doc, dict) or "references" not in doc:
        raise ValueError("YAML must contain a top-level references list")
    return [KnowledgeReference(**r) for r in doc["references"]]


def parse_references_file(path: str) -> list[KnowledgeReference]:
    """Parse a YAML file containing knowledge references."""
    with open(path, encoding="utf-8") as f:
        return parse_references_document(f.read())
