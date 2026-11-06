"""H2 regression: concurrent compute() on a shared singleton agent must not mix traces.

Review H2: ``BaseAgent.compute`` used to reset the ``TraceRecorder`` owned by the
engine that lives as a **class attribute** of the singleton agent. FastAPI runs
sync endpoints in a worker-thread pool, so two requests for the same agent
appended their reasoning steps to one shared recorder: duplicated step numbers,
rule records from the other request, and (because the counter was shared)
non-contiguous traces.

The fix binds a context-local trace to each ``compute`` call. These tests force
the interleaving deterministically, stress every singleton agent through the
registry, and exercise the real ASGI threadpool path.
"""

from __future__ import annotations

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import httpx
import pytest

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.agents.liuyao import LiuyaoInput
from openmetaphysics.agents.qimen import QimenInput
from openmetaphysics.agents.registry import get_registry
from openmetaphysics.agents.ziwei import ZiweiInput
from openmetaphysics.api.app import create_app
from openmetaphysics.core.engines import TraceRecorder
from openmetaphysics.core.schemas import Gender

BORN = datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc)

PAYLOADS = {
    "bazi": BaziInput(request_id="concurrent", born_at=BORN, gender=Gender.MALE),
    "ziwei": ZiweiInput(request_id="concurrent", born_at=BORN, gender=Gender.MALE),
    "qimen": QimenInput(request_id="concurrent", born_at=BORN, gender=Gender.MALE),
    "liuyao": LiuyaoInput(request_id="concurrent", born_at=BORN, gender=Gender.MALE, seed=42),
}


def _rule_refs(output) -> list[str]:
    return [step.rule_ref for step in output.reasoning_trace]


def _assert_trace_is_self_contained(output, expected_rules: list[str]) -> None:
    """One compute()'s trace: contiguous steps, no duplicated or mixed records."""
    trace = output.reasoning_trace
    steps = [step.step for step in trace]
    assert steps == list(range(1, len(trace) + 1)), f"step numbers must be contiguous, got {steps}"
    rules = _rule_refs(output)
    assert len(rules) == len(set(rules)), f"rules must not repeat within one trace: {rules}"
    assert rules == expected_rules, (
        f"trace must hold exactly this agent's rules: expected {expected_rules}, got {rules}"
    )


def test_two_threads_do_not_mix_the_shared_engine_trace(monkeypatch):
    """Deterministic interleaving: both threads record step 1, then continue."""
    agent = BaziAgent()
    payload = PAYLOADS["bazi"]
    expected_rules = _rule_refs(agent.compute(payload))

    barrier = threading.Barrier(2, timeout=10)
    local = threading.local()
    original_record = TraceRecorder.record

    def synchronised_record(self, rule_ref, description, inputs=None, outputs=None):
        original_record(self, rule_ref, description, inputs=inputs, outputs=outputs)
        if not getattr(local, "synced", False):
            local.synced = True
            barrier.wait()  # both threads have recorded their first step

    monkeypatch.setattr(TraceRecorder, "record", synchronised_record)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outputs = list(pool.map(lambda _index: agent.compute(payload), range(2)))

    for output in outputs:
        _assert_trace_is_self_contained(output, expected_rules)
    assert outputs[0].result == outputs[1].result
    assert outputs[0].input_hash == outputs[1].input_hash
    assert outputs[0].confidence == outputs[1].confidence


@pytest.mark.parametrize("agent_name", sorted(PAYLOADS))
def test_concurrent_compute_matches_serial_output(agent_name):
    """The registry singleton keeps producing its serial trace under contention."""
    agent = get_registry().get(agent_name)
    payload = PAYLOADS[agent_name]
    reference = agent.compute(payload)
    expected_rules = _rule_refs(reference)

    def run(_index: int):
        return agent.compute(payload)

    for _round in range(10):
        with ThreadPoolExecutor(max_workers=2) as pool:
            outputs = list(pool.map(run, range(2)))
        for output in outputs:
            _assert_trace_is_self_contained(output, expected_rules)
            assert output.result == reference.result
            assert output.input_hash == reference.input_hash
            assert output.confidence == reference.confidence


def test_api_concurrent_compute_keeps_traces_clean():
    """Two concurrent requests through the ASGI threadpool keep separate traces."""
    app = create_app()
    body = {
        "request_id": "api-concurrent",
        "born_at": BORN.isoformat(),
        "gender": "male",
    }

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await asyncio.gather(
                *(client.post("/agents/bazi/compute", json=body) for _ in range(2))
            )

    responses = asyncio.run(scenario())
    payloads = []
    for response in responses:
        assert response.status_code == 200, response.text
        payloads.append(response.json())

    baseline_rules = [step["rule_ref"] for step in payloads[0]["reasoning_trace"]]
    for data in payloads:
        steps = [step["step"] for step in data["reasoning_trace"]]
        rules = [step["rule_ref"] for step in data["reasoning_trace"]]
        assert steps == list(range(1, len(steps) + 1)), f"non-contiguous steps: {steps}"
        assert len(rules) == len(set(rules)), f"duplicated rules: {rules}"
        assert rules == baseline_rules, f"mixed traces: {rules} != {baseline_rules}"
    assert payloads[0]["result"] == payloads[1]["result"]
    assert payloads[0]["input_hash"] == payloads[1]["input_hash"]
