"""Orchestration end-to-end."""

from datetime import datetime, timezone

from openmetaphysics.core.schemas import AgentInput, Gender
from openmetaphysics.orchestration.graph import OrchestrationRequest, orchestrate


def _req(agents=None, explain=False):
    return OrchestrationRequest(
        request_id="o",
        payload=AgentInput(
            request_id="o",
            born_at=datetime(2024, 3, 1, 6, 0, tzinfo=timezone.utc),
            gender=Gender.FEMALE,
            question="财运",
        ),
        agents=agents,
        explain=explain,
    )


def test_run_all_four_agents():
    resp = orchestrate(_req())
    assert [o.agent for o in resp.outputs] == ["bazi", "liuyao", "qimen", "ziwei"]
    assert resp.consensus is not None
    assert resp.errors == []


def test_selected_agents():
    resp = orchestrate(_req(agents=["bazi", "liuyao"]))
    assert [o.agent for o in resp.outputs] == ["bazi", "liuyao"]
    assert resp.consensus is not None


def test_unknown_agent_recorded_as_error():
    resp = orchestrate(_req(agents=["bazi", "nope"]))
    assert "bazi" in [o.agent for o in resp.outputs]
    assert any("nope" in e for e in resp.errors)


def test_explain_offline_is_deterministic_string():
    resp = orchestrate(_req(agents=["bazi"], explain=True))
    assert resp.explanation["bazi"]
    assert isinstance(resp.explanation["bazi"], str)
