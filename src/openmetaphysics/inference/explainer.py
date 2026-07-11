"""Explainer — renders an already-computed AgentOutput to natural language.

Receives only the serialized output; it has no handle to any engine or raw
input beyond what the output exposes. Falls back to deterministic templated
prose when no provider is available, so the system works fully offline.
"""

from __future__ import annotations

import json
from typing import Protocol

from ..core.config import get_settings
from ..core.schemas import AgentOutput
from .providers import InferenceProvider, get_provider


class Explainer:
    def __init__(
        self,
        provider: InferenceProvider | None = None,
        retriever: KnowledgeRetrieverProtocol | None = None,
    ) -> None:
        self.provider = provider
        self.retriever = retriever

    def render(self, output: AgentOutput, *, style: str = "concise") -> str:
        if self.provider is None:
            return self._fallback(output, style)
        try:
            return self._llm_render(output, style)
        except Exception as exc:  # graceful degradation, never crash compute paths
            return self._fallback(output, style, note=f"llm_unavailable: {type(exc).__name__}")

    def _llm_render(self, output: AgentOutput, style: str) -> str:
        s = get_settings()
        context = ""
        if self.retriever is not None:
            try:
                chunks = self.retriever.retrieve(output.agent, k=3)
                context = "\n".join(f"- {c.text}" for c in chunks) if chunks else ""
            except Exception:
                context = ""
        payload = json.dumps(output.model_dump(mode="json"), ensure_ascii=False)
        prompt = (
            f"You are explaining a deterministic metaphysics result. Do NOT recompute "
            f"any numbers; describe the given structured result in {style} prose.\n"
            f"Agent: {output.agent}\nConfidence: {output.confidence.value}\n"
            f"Result JSON:\n{payload}\n"
        )
        if context:
            prompt += f"Authoritative context:\n{context}\n"
        prompt += "Output only the explanation."
        return self.provider.generate(  # type: ignore[union-attr]
            prompt,
            model=s.ollama_model,
            temperature=s.explain_temperature,
            max_tokens=s.explain_max_tokens,
        )

    @staticmethod
    def _fallback(output: AgentOutput, style: str, note: str = "") -> str:
        head = f"[{output.agent}] deterministic result (engine {output.engine_version}, "
        head += f"confidence {output.confidence.value:.2f})."
        body = json.dumps(output.model_dump(mode="json"), ensure_ascii=False)[:400]
        return (head + " " + note + " " + body).strip()


class KnowledgeRetrieverProtocol(Protocol):
    def retrieve(self, query: str, *, k: int = 5) -> list: ...


def get_explainer() -> Explainer:
    provider = get_provider()
    retriever = None
    try:
        from ..rag.retriever import get_retriever

        retriever = get_retriever()
    except Exception:
        retriever = None
    return Explainer(provider=provider, retriever=retriever)
