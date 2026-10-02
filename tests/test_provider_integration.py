"""Phase D — provider integration tests (deterministic stubs, no network).

Verifies the prompt contract, the provenance of each prompt section, and the
failure taxonomy. A real provider is never called here: CI stays offline, and
``tests/test_provider_smoke.py`` holds the opt-in smoke test.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.core.config import Settings
from openmetaphysics.core.schemas import AgentOutput, Gender
from openmetaphysics.inference.explainer import (
    PROMPT_FACTS_HEADER,
    PROMPT_KNOWLEDGE_HEADER,
    PROMPT_QUESTION_HEADER,
    Explainer,
    classify_provider_error,
    get_explainer_for,
    redact,
)
from openmetaphysics.inference.providers import get_provider
from openmetaphysics.rag.retriever import get_retriever, reset_retriever

BORN = datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc)
QUESTION = "事业与财运"


@pytest.fixture(autouse=True)
def _fresh_retriever():
    reset_retriever()
    yield
    reset_retriever()


class _StubProvider:
    """Deterministic provider implementing the existing InferenceProvider protocol."""

    name = "stub"

    def __init__(self, reply: str = "【解释】基于已计算命盘的自然语言解释。") -> None:
        self.reply = reply
        self.prompt: str | None = None
        self.calls = 0

    def generate(self, prompt: str, **kwargs: Any) -> str:
        self.prompt = prompt
        self.calls += 1
        return self.reply

    def embed(self, text: str, **kwargs: Any) -> list[float]:
        return [0.0]


def _output(question: str | None = QUESTION) -> AgentOutput:
    return BaziAgent().compute(
        BaziInput(request_id="d", born_at=BORN, gender=Gender.MALE, question=question)
    )


def _ziwei_output() -> AgentOutput:
    from openmetaphysics.agents.ziwei import ZiweiAgent, ZiweiInput

    return ZiweiAgent().compute(
        ZiweiInput(request_id="dz", born_at=BORN, gender="male", question=QUESTION)  # type: ignore[arg-type]
    )


# == Prompt contract ==


def _liuyao_output(question: str | None = QUESTION) -> AgentOutput:
    from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput

    return LiuyaoAgent().compute(
        LiuyaoInput(request_id="d2", born_at=BORN, casts=[7, 7, 8, 8, 7, 8], question=question)
    )


def test_generic_prompt_has_the_three_contract_sections_in_order():
    provider = _StubProvider()
    output = _liuyao_output()
    get_explainer_for("liuyao", provider=provider, retriever=get_retriever()).explain(output)

    prompt = provider.prompt or ""
    facts = prompt.index(PROMPT_FACTS_HEADER)
    knowledge = prompt.index(PROMPT_KNOWLEDGE_HEADER)
    question = prompt.index(PROMPT_QUESTION_HEADER)
    assert facts < knowledge < question, "FACTS -> KNOWLEDGE -> USER QUESTION"
    # the LLM's limits must be stated, not implied
    assert "Do NOT modify it" in prompt
    assert "Do NOT invent any calculation result" in prompt
    assert "NOT calculation facts" in prompt


@pytest.mark.parametrize("agent", ["bazi", "ziwei"])
def test_domain_prompts_carry_the_same_contract(agent: str):
    provider = _StubProvider()
    output = _output() if agent == "bazi" else _ziwei_output()
    get_explainer_for(agent, provider=provider, retriever=get_retriever()).explain(output)

    prompt = provider.prompt or ""
    assert PROMPT_FACTS_HEADER in prompt
    assert PROMPT_KNOWLEDGE_HEADER in prompt
    assert "Do NOT modify it" in prompt and "NOT calculation facts" in prompt
    assert QUESTION in prompt, "the domain template states the user question"


def test_generic_facts_section_carries_the_evidence_json():
    provider = _StubProvider()
    output = _liuyao_output()
    get_explainer_for("liuyao", provider=provider).explain(output)

    prompt = provider.prompt or ""
    facts = prompt.split(PROMPT_FACTS_HEADER, 1)[1]
    assert output.input_hash in facts
    assert "computed_at" not in prompt, "the wall clock is not a fact"


def test_domain_facts_section_carries_the_chart():
    provider = _StubProvider()
    output = _output()
    get_explainer_for("bazi", provider=provider).explain(output)

    prompt = provider.prompt or ""
    facts = prompt.split(PROMPT_FACTS_HEADER, 1)[1]
    assert output.result.day_master in facts
    assert "computed_at" not in prompt


def test_generic_knowledge_section_carries_citations_before_the_question():
    provider = _StubProvider()
    output = _liuyao_output()
    result = get_explainer_for("liuyao", provider=provider, retriever=get_retriever()).explain(
        output
    )
    prompt = provider.prompt or ""

    assert result["knowledge"], "the fixture needs retrieved knowledge"
    assert prompt.index(PROMPT_KNOWLEDGE_HEADER) < prompt.index(PROMPT_QUESTION_HEADER)
    assert result["knowledge"][0]["text"][:12] in prompt
    assert result["knowledge"][0]["source"] in prompt, "citations keep their source"


def test_domain_knowledge_section_carries_citations_with_sources():
    provider = _StubProvider()
    output = _output()
    result = get_explainer_for("bazi", provider=provider, retriever=get_retriever()).explain(output)
    prompt = provider.prompt or ""

    assert result["knowledge"]
    assert PROMPT_KNOWLEDGE_HEADER in prompt
    assert result["knowledge"][0]["text"][:12] in prompt
    assert result["knowledge"][0]["source"] in prompt


def test_generic_question_section_carries_the_user_question():
    provider = _StubProvider()
    get_explainer_for("liuyao", provider=provider).explain(_liuyao_output(QUESTION))
    prompt = provider.prompt or ""
    question_section = prompt.split(PROMPT_QUESTION_HEADER, 1)[1]
    assert QUESTION in question_section


def test_provider_output_is_returned_as_the_explanation():
    provider = _StubProvider(reply="PROVIDER-TEXT")
    result = get_explainer_for("bazi", provider=provider).explain(_output())
    assert result["explanation"] == "PROVIDER-TEXT"
    assert result["provider"] == "stub"
    assert result["degraded"] is False
    assert result["error"] is None
    assert provider.calls == 1


# == Failure taxonomy ==


class _Timeout(Exception):
    pass


class TimeoutException(Exception):  # noqa: N818 - name matters for classification
    pass


class _Resp:
    def __init__(self, status: int) -> None:
        self.status_code = status


class RateLimitError(Exception):
    def __init__(self) -> None:
        super().__init__("429 Too Many Requests")
        self.response = _Resp(429)


class ConnectError(Exception):
    pass


class WeirdError(Exception):
    pass


@pytest.mark.parametrize(
    ("exc", "kind"),
    [
        (TimeoutException("read timed out"), "timeout"),
        (RateLimitError(), "rate_limit"),
        (ConnectError("connection refused"), "unavailable"),
        (ValueError("invalid json payload"), "invalid_response"),
        (WeirdError("something odd"), "error"),
    ],
)
def test_failure_kinds_are_classified(exc: Exception, kind: str):
    assert classify_provider_error(exc) == kind


@pytest.mark.parametrize(
    "exc",
    [
        TimeoutException("read timed out"),
        RateLimitError(),
        ConnectError("connection refused"),
        ValueError("invalid json payload"),
        WeirdError("something odd"),
    ],
)
def test_provider_failure_keeps_the_result_and_records_the_error(exc: Exception):
    class _Failing(_StubProvider):
        def generate(self, prompt: str, **kwargs: Any) -> str:
            raise exc

    output = _output()
    before = output.model_dump(mode="json")
    result = get_explainer_for("bazi", provider=_Failing()).explain(output)

    assert result["degraded"] is True
    assert result["explanation"], "degraded prose must still be produced"
    assert result["error"] is not None
    assert result["error"]["kind"] == classify_provider_error(exc)
    assert result["error"]["provider"] == "stub"
    # the deterministic result is untouched and still reported
    assert output.model_dump(mode="json") == before
    assert result["evidence"]["result"] == output.result.model_dump(mode="json")


def test_empty_provider_response_is_treated_as_invalid():
    result = get_explainer_for("bazi", provider=_StubProvider(reply="   ")).explain(_output())
    assert result["degraded"] is True
    assert result["error"] is not None
    assert result["error"]["kind"] == "invalid_response"
    assert result["explanation"]


# == Offline default ==


def test_default_configuration_is_offline():
    assert get_provider(Settings()) is None
    result = Explainer(provider=get_provider(Settings())).explain(_output())
    assert result["provider"] is None
    assert result["degraded"] is True
    assert result["error"] is None, "offline is not an error"
    assert result["explanation"]


def test_provider_is_enabled_only_by_explicit_configuration():
    assert get_provider(Settings(enable_explainer=True, inference_provider="ollama")) is not None
    # a provider that needs credentials stays off until they are configured
    assert (
        get_provider(
            Settings(enable_explainer=True, inference_provider="deepseek", deepseek_api_key=None)
        )
        is None
    )
    enabled = get_provider(
        Settings(
            enable_explainer=True,
            inference_provider="deepseek",
            deepseek_api_key="dummy-not-a-real-key",
        )
    )
    assert enabled is not None
    assert enabled.name == "deepseek"


def test_settings_read_the_documented_environment_prefix(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OM_ENABLE_EXPLAINER", "true")
    monkeypatch.setenv("OM_INFERENCE_PROVIDER", "ollama")
    settings = Settings.from_env()
    assert settings.enable_explainer is True
    assert settings.inference_provider == "ollama"
    assert get_provider(settings) is not None
    # and the default (no environment) stays off
    monkeypatch.delenv("OM_ENABLE_EXPLAINER")
    assert Settings.from_env().enable_explainer is False


# == Secrets ==


def test_credential_like_material_is_redacted():
    assert "sk-" not in redact("failed with sk-abcdef123456")
    assert redact("Authorization: Bearer abcdef123456") == "Authorization: [redacted]"


def test_provider_error_records_do_not_leak_credentials():
    class _Leaky(_StubProvider):
        def generate(self, prompt: str, **kwargs: Any) -> str:
            raise WeirdError("auth failed for sk-supersecret0001")

    result = get_explainer_for("bazi", provider=_Leaky()).explain(_output())
    assert result["error"] is not None
    assert "sk-supersecret0001" not in result["error"]["message"]
    assert "[redacted]" in result["error"]["message"]


def test_prompt_never_contains_a_credential(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OM_ENABLE_EXPLAINER", "true")
    monkeypatch.setenv("OM_INFERENCE_PROVIDER", "deepseek")
    monkeypatch.setenv("OM_DEEPSEEK_API_KEY", "sk-must-not-appear")
    settings = Settings.from_env()
    provider = get_provider(settings)
    assert provider is not None

    class _Capturing(_StubProvider):
        pass

    capturer = _Capturing()
    get_explainer_for("bazi", provider=capturer, retriever=get_retriever()).explain(_output())
    assert "sk-must-not-appear" not in (capturer.prompt or "")
