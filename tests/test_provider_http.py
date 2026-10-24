"""Offline HTTP tests for the inference providers (no network, no credentials).

These tests exercise the request shape and response parsing of Ollama and
OpenAI-compatible providers by monkeypatching ``httpx.post``. They replace the
opt-in smoke tests as the default coverage for the HTTP methods; the smoke
tests remain available for real endpoints.
"""

from __future__ import annotations

import httpx
import pytest

from openmetaphysics.inference.providers import (
    OllamaProvider,
    OpenAICompatibleProvider,
)


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://test")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("boom", request=request, response=response)


def _capture_post(monkeypatch: pytest.MonkeyPatch, payload: dict, status_code: int = 200):
    calls: list[tuple[str, dict]] = []

    def fake_post(url: str, **kwargs) -> _FakeResponse:
        calls.append((url, kwargs))
        return _FakeResponse(payload, status_code=status_code)

    monkeypatch.setattr(httpx, "post", fake_post)
    return calls


# == Ollama ==


def test_ollama_generate_request_shape_and_response(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _capture_post(monkeypatch, {"response": "  甲木  "})
    provider = OllamaProvider(base_url="http://ollama:11434", timeout=7.5)

    assert provider.generate("prompt", model="qwen2.5:7b", temperature=0.1, max_tokens=64) == "甲木"

    url, kwargs = calls[0]
    assert url == "http://ollama:11434/api/generate"
    assert kwargs["json"]["model"] == "qwen2.5:7b"
    assert kwargs["json"]["prompt"] == "prompt"
    assert kwargs["json"]["stream"] is False
    assert kwargs["json"]["options"] == {"temperature": 0.1, "num_predict": 64}
    assert kwargs["timeout"] == 7.5


def test_ollama_generate_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _capture_post(monkeypatch, {})
    assert OllamaProvider().generate("p", model="m") == ""


def test_ollama_embed_request_shape_and_response(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _capture_post(monkeypatch, {"embedding": [0.1, 0.2, 0.3]})
    provider = OllamaProvider(base_url="http://ollama:11434")

    assert provider.embed("text", model="nomic-embed-text") == [0.1, 0.2, 0.3]

    url, kwargs = calls[0]
    assert url == "http://ollama:11434/api/embeddings"
    assert kwargs["json"] == {"model": "nomic-embed-text", "prompt": "text"}


def test_ollama_embed_missing_embedding(monkeypatch: pytest.MonkeyPatch) -> None:
    _capture_post(monkeypatch, {})
    assert OllamaProvider().embed("text", model="m") == []


# == OpenAI-compatible ==


def test_openai_generate_request_shape_and_response(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _capture_post(
        monkeypatch, {"choices": [{"message": {"content": "  解释文本  "}}]}
    )
    provider = OpenAICompatibleProvider(
        "deepseek", "https://api.deepseek.com/", "sk-test", timeout=12.0
    )

    assert provider.generate("prompt", model="deepseek-chat", temperature=0.3, max_tokens=128) == "解释文本"

    url, kwargs = calls[0]
    assert url == "https://api.deepseek.com/chat/completions"
    assert kwargs["headers"]["Authorization"] == "Bearer sk-test"
    assert kwargs["json"]["messages"] == [{"role": "user", "content": "prompt"}]
    assert kwargs["json"]["max_tokens"] == 128
    assert kwargs["timeout"] == 12.0


def test_openai_generate_empty_choices(monkeypatch: pytest.MonkeyPatch) -> None:
    _capture_post(monkeypatch, {"choices": []})
    assert OpenAICompatibleProvider("qwen", "http://qwen", "sk-test").generate("p", model="m") == ""


def test_openai_embed_request_shape_and_response(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _capture_post(monkeypatch, {"data": [{"embedding": [0.5, 0.25]}]})
    provider = OpenAICompatibleProvider("qwen", "http://qwen/v1", "sk-test")

    assert provider.embed("text", model="text-embedding-v3") == [0.5, 0.25]

    url, kwargs = calls[0]
    assert url == "http://qwen/v1/embeddings"
    assert kwargs["json"] == {"model": "text-embedding-v3", "input": "text"}


def test_openai_embed_empty_data(monkeypatch: pytest.MonkeyPatch) -> None:
    _capture_post(monkeypatch, {"data": []})
    assert OpenAICompatibleProvider("qwen", "http://qwen", "sk-test").embed("t", model="m") == []


def test_http_error_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    _capture_post(monkeypatch, {"error": "unavailable"}, status_code=503)
    with pytest.raises(httpx.HTTPStatusError):
        OllamaProvider().generate("p", model="m")
