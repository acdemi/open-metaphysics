"""Reference Conformance Framework Models -- Phase 6B Sprint 5.5.

Defines the models for validating Production Runtimes (Rust/Go/Python)
against the Reference Runtime's contracts and behavior specifications.

Architecture Boundary:
  Conformance does NOT implement business logic, modify the Runtime,
  call LLM, or call databases. It only validates outputs.

See: docs/specification/CONFORMANCE_SPEC.md
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field


class ConformanceLayer(str, Enum):
    RULE = "rule"
    PATTERN = "pattern"
    EVIDENCE = "evidence"
    KNOWLEDGE = "knowledge"
    CONSENSUS = "consensus"


class ConformanceCategory(str, Enum):
    SCHEMA = "schema"
    GOLDEN_JSON = "golden_json"
    STABLE_ORDERING = "stable_ordering"
    DETERMINISTIC_HASH = "deterministic_hash"
    CONTRACT_DIFF = "contract_diff"
    NULL_HANDLING = "null_handling"
    EMPTY_INPUT = "empty_input"
    DUPLICATE_HANDLING = "duplicate_handling"
    DETERMINISTIC_OUTPUT = "deterministic_output"
    ENUM_SERIALIZATION = "enum_serialization"
    BEHAVIOR_COVERAGE = "behavior_coverage"
    ARCHITECTURE_BOUNDARY = "architecture_boundary"


class GoldenVector(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vector_id: str
    layer: ConformanceLayer
    name: str
    description: str = ""
    input: dict[str, Any] = Field(default_factory=dict)
    expected_output: Any = None


class ConformanceCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    check_id: str
    category: ConformanceCategory
    layer: ConformanceLayer | None = None
    name: str
    passed: bool
    message: str = ""


class ConformanceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    runtime_name: str
    runtime_version: str
    passed: int = 0
    failed: int = 0
    total: int = 0
    coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    contract_version: str = "1.0.0"
    behavior_version: str = "1.0.0"
    checks: list[ConformanceCheckResult] = Field(default_factory=list)
    certified: bool = False

    def add_check(self, check: ConformanceCheckResult) -> None:
        self.checks.append(check)
        self.total += 1
        if check.passed:
            self.passed += 1
        else:
            self.failed += 1
        self.certified = self.failed == 0 and self.total > 0
        if self.total > 0:
            self.coverage = self.passed / self.total


class ConformanceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    runtime_name: str
    runtime_version: str
    supported_layers: list[str] = Field(default_factory=list)
    supported_contracts: dict[str, str] = Field(default_factory=dict)
    supported_behaviors: list[str] = Field(default_factory=list)
    certified: bool = False


@runtime_checkable
class RuntimeAdapter(Protocol):
    """Protocol that Production Runtimes implement for conformance testing."""

    def evaluate_rule(self, rule_yaml: str, chart_data: dict) -> str: ...
    def match_pattern(self, pattern_yaml: str, evaluations_json: str, system: str) -> str: ...
    def match_pattern_cross_system(
        self, pattern_yaml: str, evaluations_by_system_json: str
    ) -> str: ...
    def build_evidence(self, evaluations_json: str, matches_json: str, system: str) -> str: ...
    def query_knowledge(self, query_json: str, store_json: str) -> str: ...
    def build_consensus(self, evidence_json: str, config_json: str) -> str: ...
