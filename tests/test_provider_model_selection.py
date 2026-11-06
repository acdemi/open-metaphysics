"""H7 regression: each LLM provider gets its own model id; env template is honest.

Review H7: the explainer paths passed ``Settings.ollama_model`` ("qwen2.5:7b") to
every provider, so a configured DeepSeek/Qwen call would receive a model id that
does not exist there. ``Settings`` now carries ``qwen_model`` / ``deepseek_model``
and ``Settings.llm_model_for(provider_name)`` selects by provider; the same is
true for the RAG embedding model. ``.env.example`` lists the real ``OM_*`` keys
and states that the app does not parse ``.env`` itself.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput
from openmetaphysics.agents.qimen import QimenAgent, QimenInput
from openmetaphysics.agents.ziwei import ZiweiAgent, ZiweiInput
from openmetaphysics.core.config import Settings, get_settings, reset_settings
from openmetaphysics.core.schemas import Gender
from openmetaphysics.inference.explainer import get_explainer_for
from openmetaphysics.inference.providers import get_provider

ROOT = Path(__file__).resolve().parents[1]
BORN = datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _fresh_settings():
    reset_settings()
    yield
    reset_settings()


class _RecordingProvider:
    """Deterministic provider that records the exact kwargs it was called with."""

    def __init__(self, name: str, reply: str = "mock explanation") -> None:
        self.name = name
        self.reply = reply
        self.calls: list[dict] = []

    def generate(
        self,
        prompt: str,
        *,
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> str:
        self.calls.append(
            {
                "prompt": prompt,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        return self.reply

    def embed(self, text: str, *, model: str) -> list[float]:
        self.calls.append({"embed": text, "model": model})
        return [0.1, 0.2]


def _output(agent: str):
    if agent == "bazi":
        return BaziAgent().compute(BaziInput(request_id="h7", born_at=BORN, gender=Gender.MALE))
    if agent == "ziwei":
        return ZiweiAgent().compute(ZiweiInput(request_id="h7", born_at=BORN, gender=Gender.MALE))
    if agent == "qimen":
        return QimenAgent().compute(QimenInput(request_id="h7", born_at=BORN, gender=Gender.MALE))
    return LiuyaoAgent().compute(
        LiuyaoInput(request_id="h7", born_at=BORN, gender=Gender.MALE, casts=[7, 7, 8, 8, 7, 8])
    )


# -- settings ---------------------------------------------------------------


def test_each_provider_has_its_own_default_model():
    settings = Settings()
    assert settings.llm_model_for("ollama") == "qwen2.5:7b"
    assert settings.llm_model_for("qwen") == "qwen-plus"
    assert settings.llm_model_for("deepseek") == "deepseek-chat"
    # an unknown provider falls back to the local Ollama model
    assert settings.llm_model_for("") == "qwen2.5:7b"


def test_from_env_reads_per_provider_model_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OM_OLLAMA_MODEL", "llama3:8b")
    monkeypatch.setenv("OM_QWEN_MODEL", "qwen-max")
    monkeypatch.setenv("OM_DEEPSEEK_MODEL", "deepseek-reasoner")
    settings = Settings.from_env()
    assert settings.ollama_model == "llama3:8b"
    assert settings.qwen_model == "qwen-max"
    assert settings.deepseek_model == "deepseek-reasoner"


def test_from_env_empty_value_keeps_the_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OM_DEEPSEEK_MODEL", "")
    monkeypatch.setenv("OM_CORS_ORIGINS", "")
    settings = Settings.from_env()
    assert settings.deepseek_model == "deepseek-chat"
    assert settings.cors_origins is None


def test_from_env_does_not_load_a_dotenv_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # documented behaviour: the app reads the process environment only
    (tmp_path / ".env").write_text(
        "OM_INFERENCE_PROVIDER=deepseek\nOM_DEEPSEEK_MODEL=from-dotenv\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OM_INFERENCE_PROVIDER", raising=False)
    monkeypatch.delenv("OM_DEEPSEEK_MODEL", raising=False)
    settings = Settings.from_env()
    assert settings.inference_provider == "ollama"
    assert settings.deepseek_model == "deepseek-chat"


def test_env_example_lists_every_om_setting_and_no_legacy_keys():
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    keys = {
        line.split("=", 1)[0].strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    documented = {key for key in keys if key.startswith("OM_")}
    expected = {"OM_" + name.upper() for name in Settings.model_fields}
    assert documented == expected
    # the template must not advertise variables the app ignores
    assert not (keys & {"OLLAMA_MODEL", "OLLAMA_HOST", "DATABASE_URL", "QDRANT_HOST"})


def test_embedding_model_is_provider_specific():
    settings = Settings()
    assert settings.embedding_model_for("ollama") == "nomic-embed-text"
    assert settings.embedding_model_for("qwen") == "text-embedding-v3"
    assert Settings(embedding_model="custom-embed").embedding_model_for("qwen") == ("custom-embed")


# -- explainer paths --------------------------------------------------------


@pytest.mark.parametrize(
    ("provider_name", "env_var", "model", "expected"),
    [
        ("ollama", "OM_OLLAMA_MODEL", "qwen2.5:7b", "qwen2.5:7b"),
        ("ollama", "OM_OLLAMA_MODEL", "llama3:8b", "llama3:8b"),
        ("deepseek", "OM_DEEPSEEK_MODEL", "deepseek-chat", "deepseek-chat"),
        ("deepseek", "OM_DEEPSEEK_MODEL", "deepseek-reasoner", "deepseek-reasoner"),
        ("qwen", "OM_QWEN_MODEL", "qwen-plus", "qwen-plus"),
        ("qwen", "OM_QWEN_MODEL", "qwen-max", "qwen-max"),
    ],
)
def test_explainer_sends_the_provider_specific_model(
    monkeypatch: pytest.MonkeyPatch, provider_name, env_var, model, expected
):
    monkeypatch.setenv("OM_INFERENCE_PROVIDER", provider_name)
    monkeypatch.setenv(env_var, model)
    reset_settings()

    provider = _RecordingProvider(provider_name)
    result = get_explainer_for("bazi", provider=provider).explain(_output("bazi"))

    assert result["degraded"] is False
    assert result["provider"] == provider_name
    assert provider.calls, "the provider must be called"
    assert provider.calls[0]["model"] == expected
    assert get_settings().llm_model_for(provider_name) == expected


@pytest.mark.parametrize("agent", ["bazi", "ziwei", "qimen", "liuyao"])
def test_all_explainer_paths_use_the_deepseek_model(monkeypatch: pytest.MonkeyPatch, agent: str):
    monkeypatch.setenv("OM_INFERENCE_PROVIDER", "deepseek")
    monkeypatch.setenv("OM_DEEPSEEK_MODEL", "deepseek-chat")
    reset_settings()

    provider = _RecordingProvider("deepseek")
    get_explainer_for(agent, provider=provider).explain(_output(agent))

    assert provider.calls[0]["model"] == "deepseek-chat", agent
    assert provider.calls[0]["model"] != "qwen2.5:7b", agent


def test_provider_factory_keeps_the_provider_identity():
    ollama = get_provider(Settings(enable_explainer=True, inference_provider="ollama"))
    assert ollama is not None and ollama.name == "ollama"

    qwen = get_provider(
        Settings(enable_explainer=True, inference_provider="qwen", qwen_api_key="sk-test")
    )
    assert qwen is not None and qwen.name == "qwen"

    deepseek = get_provider(
        Settings(
            enable_explainer=True,
            inference_provider="deepseek",
            deepseek_api_key="sk-test",
        )
    )
    assert deepseek is not None and deepseek.name == "deepseek"
    # nothing is called here: only provider/model construction is asserted
    assert Settings().llm_model_for(deepseek.name) == "deepseek-chat"
