"""H8 regression: confidence is a *declared baseline*, not statistical coverage.

Review H8: every domain returned a fixed ``0.95`` with ``method="rule_coverage"``,
which falsely suggests a measured coverage ratio. Decision B keeps the numeric
value (API / Consensus compatibility) but declares its meaning honestly:
``method="placeholder_baseline"`` and ``factors["calibrated"] == 0.0``, plus the
schema/docs statement that it is not a probability. The dead ``< 0.6`` explainer
warning (never reachable with a constant 0.95) is replaced by an unconditional
semantic note in the Bazi/Ziwei prompts.

Consensus impact is asserted explicitly: the legacy ``weighted`` strategy keeps
using the value (0.95), so its numbers do not change; only the value would
change if a calibrated scorer ever replaces the placeholder.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.agents.consensus import ConsensusAgent, ConsensusInput
from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput
from openmetaphysics.agents.qimen import QimenAgent, QimenInput
from openmetaphysics.agents.ziwei import ZiweiAgent, ZiweiInput
from openmetaphysics.api.app import app
from openmetaphysics.core.engines import (
    PLACEHOLDER_CONFIDENCE_METHOD,
    PLACEHOLDER_CONFIDENCE_VALUE,
)
from openmetaphysics.core.schemas import ConfidenceScore, Gender
from openmetaphysics.inference.explainer import get_explainer_for
from openmetaphysics.rag.retriever import get_retriever

BORN = datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc)
AGENTS = ("bazi", "ziwei", "qimen", "liuyao")


def _output(agent: str):
    if agent == "bazi":
        return BaziAgent().compute(BaziInput(request_id="h8", born_at=BORN, gender=Gender.MALE))
    if agent == "ziwei":
        return ZiweiAgent().compute(ZiweiInput(request_id="h8", born_at=BORN, gender=Gender.MALE))
    if agent == "qimen":
        return QimenAgent().compute(QimenInput(request_id="h8", born_at=BORN, gender=Gender.MALE))
    return LiuyaoAgent().compute(
        LiuyaoInput(request_id="h8", born_at=BORN, gender=Gender.MALE, casts=[7, 7, 8, 8, 7, 8])
    )


class _CapturingProvider:
    name = "capture"

    def __init__(self) -> None:
        self.prompt = ""

    def generate(self, prompt: str, **kwargs) -> str:
        self.prompt = prompt
        return "解释文本"

    def embed(self, text: str, **kwargs) -> list[float]:
        return [0.0]


# -- declaration ------------------------------------------------------------


@pytest.mark.parametrize("agent", AGENTS)
def test_every_domain_declares_the_placeholder_baseline(agent: str):
    output = _output(agent)
    confidence = output.confidence

    assert confidence.value == PLACEHOLDER_CONFIDENCE_VALUE == 0.95
    assert confidence.method == PLACEHOLDER_CONFIDENCE_METHOD == "placeholder_baseline"
    assert confidence.factors["calibrated"] == 0.0, "0.0 = not calibrated against ground truth"
    assert confidence.factors["steps"] == float(len(output.reasoning_trace))
    assert confidence.method != "rule_coverage", "the old misleading method must be gone"


def test_confidence_is_identical_across_domains_not_a_coverage_score():
    confidences = {agent: _output(agent).confidence for agent in AGENTS}
    assert {c.value for c in confidences.values()} == {0.95}
    assert {c.method for c in confidences.values()} == {"placeholder_baseline"}


def test_schema_documents_the_non_statistical_semantics():
    schema = ConfidenceScore.model_json_schema()
    assert "declared baseline" in schema["description"]
    assert "NOT a calibrated probability" in schema["properties"]["value"]["description"]
    assert "placeholder_baseline" in schema["properties"]["method"]["description"]
    assert "calibrated" in schema["properties"]["factors"]["description"]

    openapi_schema = app.openapi()["components"]["schemas"]["ConfidenceScore"]
    assert "declared baseline" in openapi_schema.get("description", "")
    assert "NOT a calibrated probability" in (
        openapi_schema["properties"]["value"].get("description", "")
    )


def test_http_surface_exposes_the_placeholder_method():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/agents/bazi/compute",
        json={"request_id": "h8-http", "born_at": BORN.isoformat(), "gender": "male"},
    )
    assert response.status_code == 200, response.text
    confidence = response.json()["confidence"]
    assert confidence["method"] == "placeholder_baseline"
    assert confidence["value"] == 0.95
    assert confidence["factors"]["calibrated"] == 0.0
    assert confidence["method"] != "rule_coverage"


# -- explainer prompts ------------------------------------------------------


@pytest.mark.parametrize("agent", ["bazi", "ziwei"])
def test_domain_prompts_drop_the_dead_threshold_warning(agent: str):
    provider = _CapturingProvider()
    get_explainer_for(agent, provider=provider, retriever=get_retriever()).explain(_output(agent))
    prompt = provider.prompt

    # the warning could never fire with a constant 0.95 -> it is removed
    assert "低于阈值" not in prompt
    assert "Confidence < 0.6" not in prompt
    # ... and replaced by an explicit, unconditional semantic note
    assert "placeholder_baseline" in prompt
    assert "声明式基线" in prompt
    assert "不是统计概率" in prompt


@pytest.mark.parametrize("agent", ["qimen", "liuyao"])
def test_generic_prompts_state_the_declared_baseline(agent: str):
    provider = _CapturingProvider()
    get_explainer_for(agent, provider=provider, retriever=get_retriever()).explain(_output(agent))
    assert "declared baseline, not a calibrated probability" in provider.prompt
    assert "placeholder_baseline" in provider.prompt


# -- Consensus impact -------------------------------------------------------


def _consensus(outputs):
    return (
        ConsensusAgent()
        .compute(ConsensusInput(request_id="h8-consensus", agent_outputs=outputs))
        .result
    )


def test_weighted_consensus_keeps_using_the_declared_value():
    bazi = _output("bazi")
    liuyao = _output("liuyao")
    report = _consensus([bazi, liuyao])

    # value (not method) is the weight; both are the declared 0.95 baseline
    assert [c.weight for c in report.contributions] == [0.95, 0.95]
    assert [c.confidence for c in report.contributions] == [0.95, 0.95]

    pair = report.agreement_matrix["bazi"]["liuyao"]
    expected = round(0.95 * (0.5 + 0.5 * pair), 4)
    assert report.overall_confidence == pytest.approx(expected, abs=1e-4)


def test_method_label_does_not_change_consensus_numbers():
    bazi = _output("bazi")
    liuyao = _output("liuyao")
    baseline = _consensus([bazi, liuyao])

    relabelled = [
        o.model_copy(
            update={"confidence": o.confidence.model_copy(update={"method": "future_calibrated"})}
        )
        for o in (bazi, liuyao)
    ]
    assert _consensus(relabelled).overall_confidence == baseline.overall_confidence
