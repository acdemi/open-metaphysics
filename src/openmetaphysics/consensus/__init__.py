"""Production Consensus Layer.

Independent implementation of the frozen Reference Consensus contract
v1.0.0: ``Evidence[] + ConsensusConfig -> ConsensusReport``.

See ``docs/specification/CONSENSUS_BEHAVIOR_SPEC.md`` for the normative
behavior contracts (CS-001 ~ CS-025) this layer must satisfy.
"""

from __future__ import annotations

from .engine import ConsensusEngine
from .models import (
    ConsensusConclusion,
    ConsensusConfig,
    ConsensusInput,
    ConsensusReport,
    ConsensusStrategy,
    Domain,
    Evidence,
    EvidenceItem,
    EvidenceType,
    ResultDirection,
    make_conclusion_id,
    make_report_id,
)

__all__ = [
    "ConsensusConclusion",
    "ConsensusConfig",
    "ConsensusEngine",
    "ConsensusInput",
    "ConsensusReport",
    "ConsensusStrategy",
    "Domain",
    "Evidence",
    "EvidenceItem",
    "EvidenceType",
    "ResultDirection",
    "make_conclusion_id",
    "make_report_id",
]
