"""Phase D — opt-in real-provider smoke test.

Never runs by default: the test suite must stay offline and deterministic.
Enable it explicitly before a release/manual check::

    OM_SMOKE_PROVIDER=1 \
    OM_ENABLE_EXPLAINER=1 \
    OM_INFERENCE_PROVIDER=ollama        # or qwen / deepseek (+ key via env) \
    pytest tests/test_provider_smoke.py -v

No credential is read from the repository; everything comes from the
environment through the existing ``Settings.from_env()`` path.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.core.config import Settings
from openmetaphysics.core.schemas import AgentOutput, Gender
from openmetaphysics.inference.explainer import get_explainer_for
from openmetaphysics.inference.providers import get_provider

BORN = datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc)
QUESTION = "事业与财运"


def _opted_in() -> bool:
    return os.environ.get("OM_SMOKE_PROVIDER", "").strip().lower() in {"1", "true", "yes", "on"}


pytestmark = pytest.mark.skipif(
    not _opted_in(),
    reason="opt-in smoke test: set OM_SMOKE_PROVIDER=1 and configure OM_* to call a real provider",
)


def _output() -> AgentOutput:
    return BaziAgent().compute(
        BaziInput(request_id="smoke", born_at=BORN, gender=Gender.MALE, question=QUESTION)
    )


def test_real_provider_smoke():
    """One real call: the provider explains, and never touches the facts."""
    settings = Settings.from_env()
    provider = get_provider(settings)
    if provider is None:
        pytest.skip("OM_ENABLE_EXPLAINER / provider credentials are not configured")

    output = _output()
    before = output.model_dump(mode="json")

    result = get_explainer_for("bazi", provider=provider).explain(output)

    assert result["provider"] == provider.name
    assert result["explanation"], "the real provider returned no prose"
    if result["error"] is not None:
        # a network failure is acceptable for a smoke run, but it must be
        # reported as a classified degradation rather than an exception
        assert result["degraded"] is True
        assert result["error"]["kind"] in {
            "timeout",
            "rate_limit",
            "unavailable",
            "invalid_response",
            "error",
        }
    else:
        assert result["degraded"] is False

    # facts are never modified by the LLM
    assert output.model_dump(mode="json") == before
    assert result["evidence"]["result"] == output.result.model_dump(mode="json")


def test_real_provider_prompt_follows_the_contract(monkeypatch: pytest.MonkeyPatch):
    """Capture the real prompt shape without calling the network twice."""
    settings = Settings.from_env()
    provider = get_provider(settings)
    if provider is None:
        pytest.skip("OM_ENABLE_EXPLAINER / provider credentials are not configured")

    captured: dict[str, str] = {}
    original = provider.generate  # type: ignore[attr-defined]

    def _capture(prompt: str, **kwargs: object) -> str:
        captured["prompt"] = prompt
        return original(prompt, **kwargs)  # type: ignore[operator]

    monkeypatch.setattr(provider, "generate", _capture, raising=False)

    from openmetaphysics.inference.explainer import (
        PROMPT_FACTS_HEADER,
        PROMPT_KNOWLEDGE_HEADER,
        PROMPT_RULES,
    )

    get_explainer_for("bazi", provider=provider).explain(_output())
    prompt = captured.get("prompt", "")
    assert PROMPT_FACTS_HEADER in prompt
    assert PROMPT_KNOWLEDGE_HEADER in prompt
    assert PROMPT_RULES.splitlines()[0] in prompt
