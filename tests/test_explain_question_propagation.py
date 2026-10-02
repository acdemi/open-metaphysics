"""Phase C1 — explain question propagation.

The user's question must travel the whole path:

    API -> AgentInput -> AgentOutput -> evidence_of() -> Explain -> prompt

and must be observable in the prompt. The deterministic calculation result must
be untouched by this plumbing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput
from openmetaphysics.agents.qimen import QimenAgent, QimenInput
from openmetaphysics.agents.ziwei import ZiweiAgent, ZiweiInput
from openmetaphysics.core.schemas import AgentOutput, Gender
from openmetaphysics.inference.explainer import Explainer, get_explainer_for
from openmetaphysics.rag.retriever import reset_retriever

BORN = datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc)
QUESTION = "事业与财运"
OTHER_QUESTION = "婚姻感情"
BORN_ISO = "1985-08-15T10:00:00+08:00"


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


def _bazi(question: str | None) -> AgentOutput:
    return BaziAgent().compute(
        BaziInput(request_id="q1", born_at=BORN, gender=Gender.MALE, question=question)
    )


# == Envelope ==


def test_question_is_carried_on_the_output_envelope():
    output = _bazi(QUESTION)
    assert output.metadata["question"] == QUESTION


def test_question_absent_when_not_supplied():
    output = _bazi(None)
    assert "question" not in output.metadata


def test_deterministic_calculation_is_independent_of_the_question():
    a = _bazi(QUESTION)
    b = _bazi(OTHER_QUESTION)
    c = _bazi(None)
    # the computed chart is identical; only the envelope metadata differs
    assert a.result.model_dump() == b.result.model_dump() == c.result.model_dump()
    assert a.confidence == b.confidence == c.confidence
    assert a.reasoning_trace == b.reasoning_trace == c.reasoning_trace
    # input_hash legitimately differs: the question IS part of the input
    assert a.input_hash != b.input_hash
    assert a.input_hash == _bazi(QUESTION).input_hash


# == Evidence ==


def test_question_is_visible_in_the_evidence():
    result = Explainer(provider=_CapturingProvider()).explain(_bazi(QUESTION))
    assert result["evidence"]["metadata"]["question"] == QUESTION


# == Prompt ==


@pytest.mark.parametrize("agent", ["bazi", "ziwei", "qimen", "liuyao"])
def test_question_reaches_every_explainer_prompt(agent: str):
    agents = {
        "bazi": lambda: BaziAgent().compute(
            BaziInput(request_id="q", born_at=BORN, gender=Gender.MALE, question=QUESTION)
        ),
        "ziwei": lambda: ZiweiAgent().compute(
            ZiweiInput(request_id="q", born_at=BORN, gender="male", question=QUESTION)  # type: ignore[arg-type]
        ),
        "qimen": lambda: QimenAgent().compute(
            QimenInput(request_id="q", born_at=BORN, gender=Gender.MALE, question=QUESTION)
        ),
        "liuyao": lambda: LiuyaoAgent().compute(
            LiuyaoInput(
                request_id="q",
                born_at=BORN,
                casts=[7, 7, 8, 8, 7, 8],
                question=QUESTION,
            )
        ),
    }
    provider = _CapturingProvider()
    output = agents[agent]()
    get_explainer_for(agent, provider=provider).explain(output)

    assert provider.prompt is not None
    assert QUESTION in provider.prompt, f"{agent}: question missing from the explain prompt"


def test_different_question_produces_different_explain_context():
    p1, p2 = _CapturingProvider(), _CapturingProvider()
    get_explainer_for("bazi", provider=p1).explain(_bazi(QUESTION))
    get_explainer_for("bazi", provider=p2).explain(_bazi(OTHER_QUESTION))

    assert p1.prompt != p2.prompt
    assert QUESTION in (p1.prompt or "")
    assert OTHER_QUESTION in (p2.prompt or "")
    # the retrieval query follows the question too
    assert Explainer.build_query(_bazi(QUESTION)) != Explainer.build_query(_bazi(OTHER_QUESTION))


def test_explain_context_still_does_not_depend_on_the_envelope_timestamp():
    """The question changes the prompt; the wall clock must not."""
    first = _CapturingProvider()
    get_explainer_for("bazi", provider=first).explain(_bazi(QUESTION))

    output = _bazi(QUESTION)
    output.computed_at = datetime(2030, 1, 1, tzinfo=timezone.utc)
    second = _CapturingProvider()
    get_explainer_for("bazi", provider=second).explain(output)

    assert first.prompt == second.prompt


# == HTTP ==


def test_question_survives_the_http_api():
    client = TestClient(__import__("openmetaphysics.api.app", fromlist=["app"]).app)
    response = client.post(
        "/agents/bazi/compute?explain=true",
        json={
            "request_id": "http-q",
            "born_at": BORN_ISO,
            "gender": "male",
            "question": QUESTION,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["question"] == QUESTION
    assert data["explain"]["evidence"]["metadata"]["question"] == QUESTION


def test_question_survives_orchestration_explain():
    client = TestClient(__import__("openmetaphysics.api.app", fromlist=["app"]).app)
    response = client.post(
        "/orchestrate",
        json={
            "request_id": "o-q",
            "payload": {
                "request_id": "o-q",
                "born_at": BORN_ISO,
                "gender": "male",
                "question": QUESTION,
            },
            "agents": ["bazi"],
            "explain": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["outputs"][0]["metadata"]["question"] == QUESTION
    assert data["explanation_detail"]["bazi"]["evidence"]["metadata"]["question"] == QUESTION
