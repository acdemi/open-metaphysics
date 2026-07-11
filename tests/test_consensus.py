"""Consensus agent — agreement matrix, conflict detection."""

from datetime import datetime, timezone

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.agents.consensus import ConsensusAgent, ConsensusInput
from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput
from openmetaphysics.core.schemas import Gender


def _outputs():
    born = datetime(1985, 8, 15, 2, 0, tzinfo=timezone.utc)
    b = BaziAgent().compute(BaziInput(request_id="b", born_at=born, gender=Gender.MALE))
    ly = LiuyaoAgent().compute(LiuyaoInput(request_id="l", born_at=born, casts=[7, 7, 7, 7, 7, 7]))
    return [b, ly]


def test_consensus_builds_report():
    out = ConsensusAgent().compute(ConsensusInput(request_id="c", agent_outputs=_outputs()))
    r = out.result
    assert 0.0 <= r.overall_confidence <= 1.0
    assert len(r.contributions) == 2
    assert set(r.agreement_matrix) == {"bazi", "liuyao"}
    assert r.synthesis and r.recommendation


def test_consensus_matrix_symmetric():
    out = ConsensusAgent().compute(ConsensusInput(request_id="c", agent_outputs=_outputs()))
    m = out.result.agreement_matrix
    for a in m:
        for b in m:
            assert m[a][b] == m[b][a]


def test_single_agent_consensus_report():
    # ConsensusAgent always returns a report; orchestration skips it for <2 agents.
    b = BaziAgent().compute(
        BaziInput(
            request_id="b", born_at=datetime(2024, 1, 1, tzinfo=timezone.utc), gender=Gender.MALE
        )
    )
    out = ConsensusAgent().compute(ConsensusInput(request_id="c", agent_outputs=[b]))
    assert len(out.result.contributions) == 1
    assert out.result.contributions[0].agent == "bazi"
