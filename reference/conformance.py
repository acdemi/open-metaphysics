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

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CheckStatus(str, Enum):
    """Strength of one conformance check (H11/H12).

    ``passed``/``failed`` are real checks. ``partial`` means the check executed
    but only proves a weaker property than the check name implies; ``skipped``
    means it was **not** independently verified (e.g. it needs a second
    implementation). Neither partial nor skipped may be reported as passed, and
    neither contributes to certification.
    """

    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


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
    # H11/H12: explicit strength. ``passed`` is kept for the frozen
    # CONFORMANCE_SPEC field set; ``status`` is the truthful one. When the
    # caller omits it, it is derived from ``passed``.
    status: CheckStatus | None = None

    @model_validator(mode="after")
    def _sync_status(self) -> ConformanceCheckResult:
        if self.status is None:
            object.__setattr__(
                self, "status", CheckStatus.PASSED if self.passed else CheckStatus.FAILED
            )
        object.__setattr__(self, "passed", self.status == CheckStatus.PASSED)
        return self


class ConformanceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    runtime_name: str
    runtime_version: str
    passed: int = 0
    failed: int = 0
    partial: int = 0
    skipped: int = 0
    total: int = 0
    coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    contract_version: str = "1.0.0"
    behavior_version: str = "1.0.0"
    checks: list[ConformanceCheckResult] = Field(default_factory=list)
    certified: bool = False
    # Phase 7.4 (ACP-REF-001 Option A): CF-015 behavior-contract coverage.
    # ``behavior_coverage`` is represented/required over the 52 IDs CF-015
    # enumerates; ``unrepresented_behaviors`` lists the IDs that could not be
    # traced to an executed representation (these are also emitted as failing
    # checks, because CF-015 states missing coverage MUST fail).
    behavior_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    unrepresented_behaviors: list[str] = Field(default_factory=list)

    def add_check(self, check: ConformanceCheckResult) -> None:
        status = check.status or (CheckStatus.PASSED if check.passed else CheckStatus.FAILED)
        self.checks.append(check)
        self.total += 1
        if status == CheckStatus.PASSED:
            self.passed += 1
        elif status == CheckStatus.FAILED:
            self.failed += 1
        elif status == CheckStatus.PARTIAL:
            self.partial += 1
        else:
            self.skipped += 1
        # CONFORMANCE_SPEC (frozen): certified iff failed == 0, total > 0 and
        # coverage == 1.0. partial/skipped are not failures but they keep
        # coverage below 1.0, so they cannot certify a runtime (H11/H12).
        self.coverage = self.passed / self.total if self.total else 0.0
        self.certified = self.failed == 0 and self.total > 0 and self.passed == self.total

    @property
    def contract_conformant(self) -> bool:
        """No failures, but possibly partial/skipped checks (not certified)."""
        return self.failed == 0 and self.total > 0 and self.behavior_coverage >= 1.0


class ConformanceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    runtime_name: str
    runtime_version: str
    supported_layers: list[str] = Field(default_factory=list)
    supported_contracts: dict[str, str] = Field(default_factory=dict)
    supported_behaviors: list[str] = Field(default_factory=list)
    certified: bool = False
    # H12: "certified" is only claimed for full-strength runs. Contract
    # conformance with partial/skipped checks is recorded separately.
    contract_conformant: bool = False


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
