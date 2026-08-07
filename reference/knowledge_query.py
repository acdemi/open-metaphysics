"""Reference Knowledge Query Engine -- Phase 6B Sprint 4.

In-memory KnowledgeStore with deterministic query behavior.
All query results are sorted by ID for stable, reproducible output.

Architecture Boundary:
  KnowledgeStore is a READ-ONLY query engine.
  It does NOT participate in reasoning, generate conclusions,
  modify Evidence, increase Confidence, or call Rule.
  See: docs/specification/KNOWLEDGE_BEHAVIOR_SPEC.md

See: docs/design/phase6/01_knowledge_layer_architecture.md
     docs/design/phase6/06_flow_diagram.md
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .knowledge import (
    KnowledgeNode,
    KnowledgeReference,
    KnowledgeRelation,
    NodeType,
    ReferenceType,
    RelationDirection,
    RelationType,
    parse_nodes_file,
    parse_references_file,
    parse_relations_file,
)

# == Enums ==


class KnowledgeQueryType(str, Enum):
    """Query types supported by KnowledgeStore."""

    FIND_BY_ID = "find_by_id"
    FIND_BY_TYPE = "find_by_type"
    FIND_BY_SYSTEM = "find_by_system"
    FIND_BY_TAG = "find_by_tag"
    FIND_RELATION = "find_relation"
    FIND_REFERENCE = "find_reference"


# == KnowledgeQuery ==


class KnowledgeQuery(BaseModel):
    """Query specification for the KnowledgeStore.

    Only fields relevant to the query_type need to be set.
    """

    model_config = ConfigDict(extra="forbid")
    query_type: KnowledgeQueryType
    node_id: str | None = None
    node_type: NodeType | None = None
    system: str | None = None
    tag: str | None = None
    relation_type: RelationType | None = None
    direction: RelationDirection | None = None
    target_id: str | None = None


# == KnowledgeResult ==


class KnowledgeResult(BaseModel):
    """Result of a knowledge query.

    Always contains nodes, relations, references, and metadata,
    even if some are empty lists.
    """

    model_config = ConfigDict(extra="forbid")
    query_type: KnowledgeQueryType
    found: bool = False
    nodes: list[KnowledgeNode] = Field(default_factory=list)
    relations: list[KnowledgeRelation] = Field(default_factory=list)
    references: list[KnowledgeReference] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"


# == KnowledgeStore ==


class KnowledgeStore:
    """In-memory knowledge store with deterministic queries.

    All query results are sorted by ID (lexicographic ascending)
    to guarantee deterministic output.

    Rules:
      - Duplicate node IDs are rejected (ValueError).
      - Duplicate relation IDs are rejected (ValueError).
      - Duplicate reference IDs are rejected (ValueError).
      - find_by_id for unknown node returns None (not exception).
      - All list results are sorted by ID.
    """

    def __init__(
        self,
        nodes: list[KnowledgeNode] | None = None,
        relations: list[KnowledgeRelation] | None = None,
        references: list[KnowledgeReference] | None = None,
    ):
        self._nodes: dict[str, KnowledgeNode] = {}
        self._relations: dict[str, KnowledgeRelation] = {}
        self._references: dict[str, KnowledgeReference] = {}

        for node in nodes or []:
            self.add_node(node)
        for rel in relations or []:
            self.add_relation(rel)
        for ref in references or []:
            self.add_reference(ref)

    # -- Mutation (build-time only) --

    def add_node(self, node: KnowledgeNode) -> None:
        """Add a node. Raises ValueError on duplicate ID."""
        if node.id in self._nodes:
            raise ValueError(f"Duplicate node ID: {node.id}")
        self._nodes[node.id] = node

    def add_relation(self, relation: KnowledgeRelation) -> None:
        """Add a relation. Raises ValueError on duplicate ID."""
        if relation.id in self._relations:
            raise ValueError(f"Duplicate relation ID: {relation.id}")
        self._relations[relation.id] = relation

    def add_reference(self, reference: KnowledgeReference) -> None:
        """Add a reference. Raises ValueError on duplicate ID."""
        if reference.reference_id in self._references:
            raise ValueError(f"Duplicate reference ID: {reference.reference_id}")
        self._references[reference.reference_id] = reference

    # -- Queries --

    def find_by_id(self, node_id: str) -> KnowledgeNode | None:
        """Find a single node by ID. Returns None if not found."""
        return self._nodes.get(node_id)

    def find_by_type(self, node_type: NodeType) -> list[KnowledgeNode]:
        """Find all nodes of a given type, sorted by ID."""
        return sorted(
            [n for n in self._nodes.values() if n.node_type == node_type],
            key=lambda n: n.id,
        )

    def find_by_system(self, system: str) -> list[KnowledgeNode]:
        """Find all nodes belonging to a system, sorted by ID."""
        return sorted(
            [n for n in self._nodes.values() if any(s.value == system for s in n.systems)],
            key=lambda n: n.id,
        )

    def find_by_tag(self, tag: str) -> list[KnowledgeNode]:
        """Find all nodes with a given tag, sorted by ID."""
        return sorted(
            [n for n in self._nodes.values() if tag in n.tags],
            key=lambda n: n.id,
        )

    def find_relation(
        self,
        node_id: str,
        relation_type: RelationType | None = None,
        direction: RelationDirection | None = None,
    ) -> list[KnowledgeRelation]:
        """Find all relations involving a node (as source or target).

        Optionally filter by relation_type and/or direction.
        Results are sorted by relation ID.
        """
        results = [
            r
            for r in self._relations.values()
            if r.source_node_id == node_id or r.target_node_id == node_id
        ]
        if relation_type is not None:
            results = [r for r in results if r.relation_type == relation_type]
        if direction is not None:
            results = [r for r in results if r.direction == direction]
        return sorted(results, key=lambda r: r.id)

    def find_reference(self, target_id: str) -> list[KnowledgeReference]:
        """Find all references pointing to a target (node or relation).

        Results are sorted by reference_id.
        """
        return sorted(
            [r for r in self._references.values() if r.target_id == target_id],
            key=lambda r: r.reference_id,
        )

    # -- Execute (dispatch) --

    def execute(self, query: KnowledgeQuery) -> KnowledgeResult:
        """Execute a KnowledgeQuery and return a KnowledgeResult."""
        qt = query.query_type

        if qt == KnowledgeQueryType.FIND_BY_ID:
            node = self.find_by_id(query.node_id or "")
            return KnowledgeResult(
                query_type=qt,
                found=node is not None,
                nodes=[node] if node else [],
                metadata={"query_type": qt.value, "node_id": query.node_id},
            )

        if qt == KnowledgeQueryType.FIND_BY_TYPE:
            nodes = self.find_by_type(query.node_type or NodeType.WUXING)
            return KnowledgeResult(
                query_type=qt,
                found=len(nodes) > 0,
                nodes=nodes,
                metadata={
                    "query_type": qt.value,
                    "node_type": query.node_type.value if query.node_type else None,
                    "total": len(nodes),
                },
            )

        if qt == KnowledgeQueryType.FIND_BY_SYSTEM:
            nodes = self.find_by_system(query.system or "")
            return KnowledgeResult(
                query_type=qt,
                found=len(nodes) > 0,
                nodes=nodes,
                metadata={
                    "query_type": qt.value,
                    "system": query.system,
                    "total": len(nodes),
                },
            )

        if qt == KnowledgeQueryType.FIND_BY_TAG:
            nodes = self.find_by_tag(query.tag or "")
            return KnowledgeResult(
                query_type=qt,
                found=len(nodes) > 0,
                nodes=nodes,
                metadata={
                    "query_type": qt.value,
                    "tag": query.tag,
                    "total": len(nodes),
                },
            )

        if qt == KnowledgeQueryType.FIND_RELATION:
            relations = self.find_relation(
                query.node_id or "",
                relation_type=query.relation_type,
                direction=query.direction,
            )
            return KnowledgeResult(
                query_type=qt,
                found=len(relations) > 0,
                relations=relations,
                metadata={
                    "query_type": qt.value,
                    "node_id": query.node_id,
                    "relation_type": query.relation_type.value if query.relation_type else None,
                    "direction": query.direction.value if query.direction else None,
                    "total": len(relations),
                },
            )

        if qt == KnowledgeQueryType.FIND_REFERENCE:
            references = self.find_reference(query.target_id or "")
            return KnowledgeResult(
                query_type=qt,
                found=len(references) > 0,
                references=references,
                metadata={
                    "query_type": qt.value,
                    "target_id": query.target_id,
                    "total": len(references),
                },
            )

        raise ValueError(f"Unknown query type: {qt}")

    # -- Bulk accessors (sorted) --

    def all_nodes(self) -> list[KnowledgeNode]:
        """All nodes, sorted by ID."""
        return sorted(self._nodes.values(), key=lambda n: n.id)

    def all_relations(self) -> list[KnowledgeRelation]:
        """All relations, sorted by ID."""
        return sorted(self._relations.values(), key=lambda r: r.id)

    def all_references(self) -> list[KnowledgeReference]:
        """All references, sorted by reference_id."""
        return sorted(self._references.values(), key=lambda r: r.reference_id)

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def relation_count(self) -> int:
        return len(self._relations)

    @property
    def reference_count(self) -> int:
        return len(self._references)


# == Store builder from YAML files ==


def load_knowledge_store(
    nodes_path: str | Path | None = None,
    relations_path: str | Path | None = None,
    references_path: str | Path | None = None,
) -> KnowledgeStore:
    """Build a KnowledgeStore from YAML files."""
    nodes = parse_nodes_file(str(nodes_path)) if nodes_path else []
    relations = parse_relations_file(str(relations_path)) if relations_path else []
    references = parse_references_file(str(references_path)) if references_path else []
    return KnowledgeStore(nodes=nodes, relations=relations, references=references)


# == Contract Export ==

KNOWLEDGE_CONTRACT_PATH = Path(__file__).parent / "contracts" / "knowledge_contract.json"


def _build_golden_examples(store: KnowledgeStore) -> list[dict[str, Any]]:
    """Build golden examples by running the KnowledgeStore."""
    examples: list[dict[str, Any]] = []

    # Example 1: find_by_id (found)
    node = store.find_by_id("kn:wuxing:mu")
    if node:
        examples.append(
            {
                "name": "find_by_id_found",
                "description": "Query a known node by ID.",
                "query": {"query_type": "find_by_id", "node_id": "kn:wuxing:mu"},
                "result": KnowledgeResult(
                    query_type=KnowledgeQueryType.FIND_BY_ID,
                    found=True,
                    nodes=[node],
                    metadata={"query_type": "find_by_id", "node_id": "kn:wuxing:mu"},
                ).model_dump(mode="json"),
            }
        )

    # Example 2: find_by_id (not found)
    examples.append(
        {
            "name": "find_by_id_not_found",
            "description": "Query an unknown node by ID returns None (null behavior).",
            "query": {"query_type": "find_by_id", "node_id": "kn:unknown:nonexistent"},
            "result": KnowledgeResult(
                query_type=KnowledgeQueryType.FIND_BY_ID,
                found=False,
                nodes=[],
                metadata={"query_type": "find_by_id", "node_id": "kn:unknown:nonexistent"},
            ).model_dump(mode="json"),
        }
    )

    # Example 3: find_by_type
    wuxing_nodes = store.find_by_type(NodeType.WUXING)
    examples.append(
        {
            "name": "find_by_type_wuxing",
            "description": "Query all wuxing nodes, sorted by ID.",
            "query": {"query_type": "find_by_type", "node_type": "wuxing"},
            "result": KnowledgeResult(
                query_type=KnowledgeQueryType.FIND_BY_TYPE,
                found=len(wuxing_nodes) > 0,
                nodes=wuxing_nodes,
                metadata={
                    "query_type": "find_by_type",
                    "node_type": "wuxing",
                    "total": len(wuxing_nodes),
                },
            ).model_dump(mode="json"),
        }
    )

    # Example 4: find_by_system
    bazi_nodes = store.find_by_system("bazi")
    examples.append(
        {
            "name": "find_by_system_bazi",
            "description": "Query all nodes belonging to the bazi system, sorted by ID.",
            "query": {"query_type": "find_by_system", "system": "bazi"},
            "result": KnowledgeResult(
                query_type=KnowledgeQueryType.FIND_BY_SYSTEM,
                found=len(bazi_nodes) > 0,
                nodes=bazi_nodes,
                metadata={
                    "query_type": "find_by_system",
                    "system": "bazi",
                    "total": len(bazi_nodes),
                },
            ).model_dump(mode="json"),
        }
    )

    # Example 5: find_by_tag
    tagged_nodes = store.find_by_tag("yang")
    examples.append(
        {
            "name": "find_by_tag_yang",
            "description": "Query all nodes tagged 'yang', sorted by ID.",
            "query": {"query_type": "find_by_tag", "tag": "yang"},
            "result": KnowledgeResult(
                query_type=KnowledgeQueryType.FIND_BY_TAG,
                found=len(tagged_nodes) > 0,
                nodes=tagged_nodes,
                metadata={"query_type": "find_by_tag", "tag": "yang", "total": len(tagged_nodes)},
            ).model_dump(mode="json"),
        }
    )

    # Example 6: find_relation
    mu_relations = store.find_relation("kn:wuxing:mu")
    examples.append(
        {
            "name": "find_relation_mu",
            "description": "Query all relations involving kn:wuxing:mu, sorted by ID.",
            "query": {"query_type": "find_relation", "node_id": "kn:wuxing:mu"},
            "result": KnowledgeResult(
                query_type=KnowledgeQueryType.FIND_RELATION,
                found=len(mu_relations) > 0,
                relations=mu_relations,
                metadata={
                    "query_type": "find_relation",
                    "node_id": "kn:wuxing:mu",
                    "total": len(mu_relations),
                },
            ).model_dump(mode="json"),
        }
    )

    # Example 7: find_reference
    mu_refs = store.find_reference("kn:wuxing:mu")
    examples.append(
        {
            "name": "find_reference_mu",
            "description": "Query all references pointing to kn:wuxing:mu, sorted by ID.",
            "query": {"query_type": "find_reference", "target_id": "kn:wuxing:mu"},
            "result": KnowledgeResult(
                query_type=KnowledgeQueryType.FIND_REFERENCE,
                found=len(mu_refs) > 0,
                references=mu_refs,
                metadata={
                    "query_type": "find_reference",
                    "target_id": "kn:wuxing:mu",
                    "total": len(mu_refs),
                },
            ).model_dump(mode="json"),
        }
    )

    return examples


def export_knowledge_contract(
    store: KnowledgeStore | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Export the Knowledge Layer contract from golden examples.

    Auto-generated by running the Reference Runtime. NOT hand-written.
    """
    if store is None:
        examples_dir = Path(__file__).parent / "examples" / "knowledge"
        store = load_knowledge_store(
            nodes_path=examples_dir / "nodes.yaml",
            relations_path=examples_dir / "relations.yaml",
            references_path=examples_dir / "references.yaml",
        )

    golden = _build_golden_examples(store)

    contract: dict[str, Any] = {
        "contract_name": "knowledge",
        "contract_version": "1.0.0",
        "description": (
            "Reference Runtime Knowledge Layer Contract. "
            "Generated from golden examples. "
            "All future implementations must conform to this contract."
        ),
        "generated_by": "reference.knowledge_query.export_knowledge_contract",
        "node_types": [t.value for t in NodeType],
        "relation_types": [t.value for t in RelationType],
        "reference_types": [t.value for t in ReferenceType],
        "query_types": [t.value for t in KnowledgeQueryType],
        "models": {
            "KnowledgeNode": {
                "type": "object",
                "required": [
                    "id",
                    "node_type",
                    "name_cn",
                    "name_en",
                    "systems",
                    "source",
                    "interpretation",
                    "confidence",
                ],
                "optional": ["tags", "schools", "attributes"],
                "field_types": {
                    "id": "string (pattern: ^kn:[a-z_]+:[a-z_0-9]+$)",
                    "node_type": "enum (20 values)",
                    "name_cn": "string",
                    "name_en": "string",
                    "systems": "array<enum> (min_length=1)",
                    "source": "SourceRef",
                    "interpretation": "string",
                    "tags": "array<string>",
                    "confidence": "number [0,1]",
                    "schools": "array<SchoolView>",
                    "attributes": "object",
                },
            },
            "KnowledgeRelation": {
                "type": "object",
                "required": [
                    "id",
                    "source_node_id",
                    "target_node_id",
                    "relation_type",
                    "direction",
                    "weight",
                    "source",
                ],
                "optional": ["evidence", "conditions"],
                "field_types": {
                    "id": "string (pattern: ^rel:.+$)",
                    "source_node_id": "string",
                    "target_node_id": "string",
                    "relation_type": "enum (15 values)",
                    "direction": "enum (directed|undirected)",
                    "weight": "number [0,1]",
                    "evidence": "array<RelationEvidence>",
                    "source": "SourceRef",
                    "conditions": "array<object>",
                },
            },
            "KnowledgeReference": {
                "type": "object",
                "required": [
                    "reference_id",
                    "target_type",
                    "target_id",
                    "ref_type",
                    "source",
                ],
                "optional": ["passage", "school", "credibility"],
                "field_types": {
                    "reference_id": "string (pattern: ^ref:[a-z_]+:[a-z_0-9]+$)",
                    "target_type": "enum (node|relation)",
                    "target_id": "string",
                    "ref_type": "enum (4 values)",
                    "source": "SourceRef",
                    "passage": "string",
                    "school": "string | null",
                    "credibility": "number [0,1]",
                },
            },
            "KnowledgeResult": {
                "type": "object",
                "required": [
                    "query_type",
                    "found",
                    "nodes",
                    "relations",
                    "references",
                    "metadata",
                    "version",
                ],
                "field_types": {
                    "query_type": "enum (6 values)",
                    "found": "boolean",
                    "nodes": "array<KnowledgeNode>",
                    "relations": "array<KnowledgeRelation>",
                    "references": "array<KnowledgeReference>",
                    "metadata": "object",
                    "version": "string",
                },
            },
        },
        "golden_examples": golden,
    }

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(contract, f, ensure_ascii=False, indent=2, sort_keys=True)

    return contract
