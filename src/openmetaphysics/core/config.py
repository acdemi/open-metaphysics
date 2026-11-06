"""Typed configuration. Heavy services are optional and degrade gracefully."""

from __future__ import annotations

import os
from typing import get_args

from pydantic import BaseModel


class Settings(BaseModel):
    # Inference (isolated, optional)
    enable_explainer: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    qwen_api_base: str | None = None
    qwen_api_key: str | None = None
    qwen_model: str = "qwen-plus"
    deepseek_api_base: str = "https://api.deepseek.com"
    deepseek_api_key: str | None = None
    deepseek_model: str = "deepseek-chat"
    # Embeddings are a separate model from the chat model (RAG path only).
    # None -> provider default (see ``embedding_model_for``).
    embedding_model: str | None = None
    inference_provider: str = "ollama"  # "ollama" | "qwen" | "deepseek"
    explain_temperature: float = 0.2
    explain_max_tokens: int = 512

    # Data directories for non-package runtime data (knowledge corpora, frozen
    # reference contracts). Needed after a wheel/pip/Docker install, where the
    # repository tree is not present; the source checkout is auto-detected.
    knowledge_dir: str | None = None
    reference_dir: str | None = None

    # RAG (optional)
    qdrant_url: str | None = None
    qdrant_collection: str = "openmetaphysics"
    rag_enabled: bool = False

    # Persistence (optional)
    postgres_dsn: str | None = None

    # API (optional): comma-separated allowed origins for CORS
    cors_origins: str | None = None

    # API protection (P2.2, opt-in). ``api_key`` is None by default so existing
    # deployments behave exactly as before: no 401/403 and no rate limiting.
    # When set, protected routes require ``Authorization: Bearer <key>`` or
    # ``X-API-Key``; rate limiting then applies per key/IP (60/min default).
    # NOTE: the limiter is process-local (in-memory sliding window); it is NOT
    # shared across workers/replicas and is not a distributed rate limiter.
    api_key: str | None = None
    rate_limit_per_minute: int = 60  # 0 = disabled (only relevant once api_key is set)
    # Session/trace responses normally keep birth data (compatibility default).
    # Set true to redact ``born_at`` / ``born_location`` from those responses.
    session_redact_birth: bool = False

    # Orchestration
    default_strategy: str = "weighted"

    def llm_model_for(self, provider_name: str) -> str:
        """Chat model for a provider name — never blindly the Ollama model.

        The explainer paths used to pass ``ollama_model`` ("qwen2.5:7b") to every
        provider, so a configured DeepSeek/Qwen remote call would be sent a
        non-existent model id. Each provider now has its own setting and default.
        """
        name = (provider_name or "").strip().lower()
        if name == "deepseek":
            return self.deepseek_model
        if name == "qwen":
            return self.qwen_model
        return self.ollama_model

    def embedding_model_for(self, provider_name: str) -> str:
        """Embedding model (RAG only): explicit setting wins, else provider default."""
        if self.embedding_model:
            return self.embedding_model
        name = (provider_name or "").strip().lower()
        if name == "qwen":
            return "text-embedding-v3"
        return "nomic-embed-text"

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from ``OM_<FIELD_NAME_UPPER>`` process environment vars.

        **Only the process environment is read.** This project intentionally
        ships no dotenv loader, so a ``.env`` file is NOT parsed automatically:
        export the variables in the shell, use ``docker compose --env-file``, or
        load them with your own dotenv loader before starting the app.
        ``.env.example`` is a template, not a runtime input.

        Empty values keep the field default (an optional field becomes ``None``);
        booleans accept ``1/true/yes/on``.
        """
        prefix = "OM_"
        kwargs: dict[str, object] = {}
        for name, field in cls.model_fields.items():
            raw = os.environ.get(prefix + name.upper())
            if raw is None:
                continue
            text = raw.strip()
            if field.annotation is bool:
                kwargs[name] = text.lower() in {"1", "true", "yes", "on"}
            elif text:
                kwargs[name] = text
            elif type(None) in get_args(field.annotation):
                kwargs[name] = None
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
