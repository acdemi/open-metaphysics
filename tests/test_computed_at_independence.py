"""Phase C3 — ``computed_at`` boundary.

``AgentOutput.computed_at`` (and ``ConsensusOutput.computed_at``) is a
wall-clock stamp written by the envelope. This module proves the three things
that must NOT depend on it:

    calculation facts   result / confidence / reasoning_trace / input_hash
    consensus           ConsensusAgent output
    explanation         prompt and rendered prose

No contract change is required to obtain this: the stamp stays an envelope
field and nothing downstream reads it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.agents.consensus import ConsensusAgent, ConsensusInput
from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput
from openmetaphysics.agents.ziwei import ZiweiAgent, ZiweiInput
from openmetaphysics.api.app import app
from openmetaphysics.core.schemas import AgentOutput, Gender
from openmetaphysics.inference.explainer import get_explainer_for
from openmetaphysics.rag.retriever import reset_retriever

BORN = datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc)
PAYLOAD = {
    "request_id": "c3",
    "born_at": "1985-08-15T10:00:00+08:00",
    "gender": "male",
    "question": "事业与财运",
}
_FUTURE = datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _fresh_retriever():
    reset_retriever()
    yield
    reset_retriever()


class _CapturingProvider:
    name = "capturing-stub"

    def __init__(self) -> None:
        self.prompt: str | None = None

    def generate(self, prompt: str, **kwargs: Any) -> str:
        self.prompt = prompt
        return "解释文本"

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        return [0.0]


def _bazi() -> AgentOutput:
    return BaziAgent().compute(
        BaziInput(request_id="c3", born_at=BORN, gender=Gender.MALE, question="事业与财运")
    )


# == What the envelope stamp is ==


def test_computed_at_is_an_envelope_field_only():
    output = _bazi()
    assert output.computed_at.tzinfo is not None
    assert "computed_at" not in output.result.model_dump()
    assert "computed_at" not in output.metadata


def test_calculation_facts_are_identical_across_builds():
    a, b = _bazi(), _bazi()
    assert a.result.model_dump() == b.result.model_dump()
    assert a.confidence == b.confidence
    assert a.reasoning_trace == b.reasoning_trace
    assert a.input_hash == b.input_hash


# == Facts ==


def test_facts_do_not_read_computed_at():
    output = _bazi()
    before = output.result.model_dump()
    evidence_before = get_explainer_for("bazi").explain(output)["evidence"]

    output.computed_at = _FUTURE

    assert output.result.model_dump() == before
    assert get_explainer_for("bazi").explain(output)["evidence"] == evidence_before


# == Consensus ==


def test_consensus_is_independent_of_computed_at():
    b = _bazi()
    z = ZiweiAgent().compute(
        ZiweiInput(request_id="c3z", born_at=BORN, gender="male", question="事业")  # type: ignore[arg-type]
    )
    ly = LiuyaoAgent().compute(
        LiuyaoInput(request_id="c3l", born_at=BORN, casts=[7, 7, 8, 8, 7, 8])
    )

    first = (
        ConsensusAgent()
        .compute(ConsensusInput(request_id="c3", agent_outputs=[b, z, ly]))
        .result.model_dump(mode="json")
    )

    b.computed_at = _FUTURE
    z.computed_at = _FUTURE
    ly.computed_at = _FUTURE

    second = (
        ConsensusAgent()
        .compute(ConsensusInput(request_id="c3", agent_outputs=[b, z, ly]))
        .result.model_dump(mode="json")
    )

    assert first == second


# == Explanation ==


def test_explanation_is_independent_of_computed_at():
    first = _CapturingProvider()
    output = _bazi()
    get_explainer_for("bazi", provider=first).explain(output)

    output.computed_at = _FUTURE
    second = _CapturingProvider()
    get_explainer_for("bazi", provider=second).explain(output)

    assert first.prompt == second.prompt
    assert first.prompt is not None
    assert "2099" not in first.prompt, "the wall clock must not leak into the prompt"


# == HTTP envelope ==


def test_http_response_differs_only_by_the_envelope_timestamp():
    client = TestClient(app, raise_server_exceptions=False)
    request = {
        "request_id": "c3-http",
        "payload": PAYLOAD,
        "agents": ["bazi", "ziwei"],
        "explain": True,
    }
    first = client.post("/orchestrate", json=request).json()
    second = client.post("/orchestrate", json=request).json()

    def strip(resp: dict[str, Any]) -> dict[str, Any]:
        clone = {k: v for k, v in resp.items() if k != "outputs"}
        clone["outputs"] = [
            {k: v for k, v in o.items() if k != "computed_at"} for o in resp["outputs"]
        ]
        if resp.get("consensus"):
            consensus = dict(resp["consensus"])
            consensus.pop("computed_at", None)
            clone["consensus"] = consensus
        return clone

    assert strip(first) == strip(second)
    # the only volatile values are the wall-clock stamps
    assert any(o["computed_at"] for o in first["outputs"])
