"""Inference providers — the ONLY network-capable path, used solely for NL
explanation. Calculation cores never see these. All calls degrade gracefully.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import httpx

from ..core.config import Settings, get_settings


@runtime_checkable
class InferenceProvider(Protocol):
    name: str

    def generate(
        self, prompt: str, *, model: str, temperature: float = 0.2, max_tokens: int = 512
    ) -> str: ...

    def embed(self, text: str, *, model: str) -> list[float]: ...


class OllamaProvider:
    """Local Ollama (http://localhost:11434 by default)."""

    name = "ollama"

    def __init__(self, base_url: str | None = None, timeout: float = 60.0) -> None:
        self.base_url = base_url or "http://localhost:11434"
        self.timeout = timeout

    def generate(
        self, prompt: str, *, model: str, temperature: float = 0.2, max_tokens: int = 512
    ) -> str:
        resp = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return str(resp.json().get("response", "")).strip()

    def embed(self, text: str, *, model: str) -> list[float]:
        resp = httpx.post(
            f"{self.base_url}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return list(resp.json().get("embedding", []))


class OpenAICompatibleProvider:
    """Qwen / DeepSeek via OpenAI-compatible chat completions (opt-in remote)."""

    def __init__(self, name: str, base_url: str, api_key: str, timeout: float = 60.0) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def generate(
        self, prompt: str, *, model: str, temperature: float = 0.2, max_tokens: int = 512
    ) -> str:
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        choices = resp.json().get("choices", [])
        return choices[0]["message"]["content"].strip() if choices else ""

    def embed(self, text: str, *, model: str) -> list[float]:
        resp = httpx.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": model, "input": text},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return list(data[0]["embedding"]) if data else []


def get_provider(settings: Settings | None = None) -> InferenceProvider | None:
    """Build the configured provider, or None if disabled/unconfigured."""
    s = settings or get_settings()
    if not s.enable_explainer:
        return None
    if s.inference_provider == "ollama":
        return OllamaProvider(base_url=s.ollama_base_url)
    if s.inference_provider == "deepseek" and s.deepseek_api_key:
        return OpenAICompatibleProvider("deepseek", s.deepseek_api_base, s.deepseek_api_key)
    if s.inference_provider == "qwen" and s.qwen_api_key:
        base = s.qwen_api_base or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        return OpenAICompatibleProvider("qwen", base, s.qwen_api_key)
    return None
