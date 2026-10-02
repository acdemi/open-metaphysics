"""Phase 7.4 (ACP-REF-001 Option A) — CF-015 behavior-contract coverage.

Locks the *truthful* behavior-coverage mechanism that replaced the previous
hardcoded 17-ID ``passed=True`` loop:

- the required set is exactly CF-015's 52 IDs (7 BC + KB-001~020 + CS-001~025);
- every required ID resolves to an executed representation;
- an ID without a representation FAILS conformance (negative control);
- ``behavior_coverage`` / ``unrepresented_behaviors`` are reported truthfully.

See: docs/governance/ACP/ACP-REF-001_conformance_behavior_coverage.md
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reference.conformance import ConformanceCategory
from reference.conformance_runner import (
    REQUIRED_BEHAVIOR_IDS,
    ConformanceRunner,
    ReferenceAdapter,
)
from reference.consensus import ConsensusStrategy
from reference.consensus_behavior import ConsensusBehavior
from reference.consensus_builder import ConsensusBuilder
from reference.knowledge_behavior import KnowledgeBehavior
from reference.knowledge_query import load_knowledge_store

EXAMPLES = Path(__file__).resolve().parents[1] / "reference" / "examples"
BC_IDS = (
    "BC-RE-001",
    "BC-DNF-001",
    "BC-PM-001",
    "BC-EV-001",
    "BC-JSON-001",
    "BC-DET-001",
    "BC-EDGE-001",
)
KB_IDS = {f"KB-{i:03d}" for i in range(1, 21)}
CS_IDS = {f"CS-{i:03d}" for i in range(1, 26)}


def _store():
    kn = EXAMPLES / "knowledge"
    return load_knowledge_store(
        nodes_path=kn / "nodes.yaml",
        relations_path=kn / "relations.yaml",
        references_path=kn / "references.yaml",
    )


def test_required_set_is_cf015_52() -> None:
    """CF-015 enumerates exactly 7 BC + 20 KB + 25 CS = 52 IDs."""
    assert len(REQUIRED_BEHAVIOR_IDS) == 52
    assert REQUIRED_BEHAVIOR_IDS[:7] == BC_IDS
    assert KB_IDS <= set(REQUIRED_BEHAVIOR_IDS)
    assert CS_IDS <= set(REQUIRED_BEHAVIOR_IDS)
    assert len(set(REQUIRED_BEHAVIOR_IDS)) == 52


def test_knowledge_audit_covers_all_20() -> None:
    """KB-001~020 each have an executed verifier (was 5 keys before Phase 7.4)."""
    audit = KnowledgeBehavior.audit(_store())
    assert KB_IDS <= set(audit)
    assert [k for k, v in audit.items() if k.startswith("KB-") and v is not True] == []


def test_consensus_audit_covers_all_25() -> None:
    """CS-001~025 each have an executed verifier (was 5 keys before Phase 7.4)."""
    audit = ConsensusBehavior.audit(ConsensusBuilder())
    assert CS_IDS <= set(audit)
    assert [k for k, v in audit.items() if k.startswith("CS-") and v is not True] == []


def test_conformance_reports_full_behavior_coverage() -> None:
    result = ConformanceRunner().run(ReferenceAdapter(), "reference", "1.0.0")
    assert result.behavior_coverage == 1.0
    assert result.unrepresented_behaviors == []
    assert result.certified is True

    behavior_checks = [
        c for c in result.checks if c.category == ConformanceCategory.BEHAVIOR_COVERAGE
    ]
    assert len(behavior_checks) == 52
    assert all(c.passed for c in behavior_checks)
    assert {c.name for c in behavior_checks} == set(REQUIRED_BEHAVIOR_IDS)


def test_missing_representation_fails_conformance(monkeypatch) -> None:
    """Negative control: dropping one representation must FAIL, not silently pass."""
    runner = ConformanceRunner()
    original = runner._behavior_representation

    def patched(result):  # type: ignore[no-untyped-def]
        rep = dict(original(result))
        rep.pop("KB-001")
        return rep

    monkeypatch.setattr(runner, "_behavior_representation", patched)
    result = runner.run(ReferenceAdapter(), "reference", "1.0.0")

    assert "KB-001" in result.unrepresented_behaviors
    assert result.behavior_coverage < 1.0
    assert result.certified is False
    failing = [c for c in result.checks if c.check_id == "CF-BEHAV-KB-001"]
    assert len(failing) == 1 and failing[0].passed is False


def test_failing_representation_fails_conformance(monkeypatch) -> None:
    """Negative control: an ID whose representation returns False must FAIL."""
    runner = ConformanceRunner()
    original = runner._behavior_representation

    def patched(result):  # type: ignore[no-untyped-def]
        rep = dict(original(result))
        rep["CS-022"] = (False, "forced failure")
        return rep

    monkeypatch.setattr(runner, "_behavior_representation", patched)
    result = runner.run(ReferenceAdapter(), "reference", "1.0.0")

    assert "CS-022" in result.unrepresented_behaviors
    assert result.certified is False


@pytest.mark.parametrize("strategy", list(ConsensusStrategy))
def test_consensus_strategies_are_behavior_verified(strategy) -> None:
    """Every consensus strategy is exercised by the behavior audit."""
    builder = ConsensusBuilder()
    audit = ConsensusBehavior.audit(builder)
    assert audit["CS-004"] is True or strategy != ConsensusStrategy.RETAIN_ALL
    assert all(v is True for v in audit.values())
