"""Typed configuration. Heavy services are optional and degrade gracefully."""

from __future__ import annotations

import os

from pydantic import BaseModel


class Settings(BaseModel):
    # Inference (isolated, optional)
    enable_explainer: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    qwen_api_base: str | None = None
    qwen_api_key: str | None = None
    deepseek_api_base: str = "https://api.deepseek.com"
    deepseek_api_key: str | None = None
    inference_provider: str = "ollama"  # "ollama" | "qwen" | "deepseek"
    explain_temperature: float = 0.2
    explain_max_tokens: int = 512

    # RAG (optional)
    qdrant_url: str | None = None
    qdrant_collection: str = "openmetaphysics"
    rag_enabled: bool = False

    # Persistence (optional)
    postgres_dsn: str | None = None

    # Orchestration
    default_strategy: str = "weighted"

    @classmethod
    def from_env(cls) -> Settings:
        prefix = "OM_"
        fields = {f: t for f, t in cls.model_fields.items()}
        kwargs: dict[str, object] = {}
        for name, field in fields.items():
            env_key = prefix + name.upper()
            raw = os.environ.get(env_key)
            if raw is None:
                continue
            if field.annotation is bool:
                kwargs[name] = raw.strip().lower() in {"1", "true", "yes", "on"}
            else:
                kwargs[name] = raw.strip() if raw.strip() else None
        return cls(**kwargs)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def reset_settings() -> None:
    global _settings
    _settings = None
