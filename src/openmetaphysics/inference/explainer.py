"""Explainer — renders an already-computed AgentOutput to natural language.

Explain pipeline (this module owns the closure):

    AgentOutput (deterministic calculation result)
        -> evidence          (already-computed facts: result + reasoning_trace + confidence)
        -> knowledge retrieval (RAG over the frozen corpus, query derived from the result)
        -> prompt / request
        -> provider (LLM) or deterministic offline rendering
        -> explanation

Discipline (H4 / Rule First. Knowledge Second. LLM Last.):

* The explainer NEVER computes or recomputes a chart. It only reads what the
  deterministic engine already put into ``AgentOutput``.
* The retrieved knowledge is injected as authoritative context; it never
  changes the result.
* When no provider is configured (or the provider fails) the pipeline still
  runs end to end and degrades to deterministic templated prose.

There is no separate "evidence" type: the deterministic evidence already
exists as ``AgentOutput.result`` + ``reasoning_trace`` + ``confidence``.
"""

from __future__ import annotations

import json
from typing import Any, Protocol

from ..core.config import get_settings
from ..core.schemas import AgentOutput
from .providers import InferenceProvider, get_provider

__all__ = ["Explainer", "KnowledgeRetrieverProtocol", "get_explainer", "get_explainer_for"]

# Bounded, deterministic result flattening for knowledge queries.
_QUERY_FIELDS = (
    "day_master",
    "day_master_element",
    "month_pillar",
    "wuxing_ju",
    "ju",
    "dun_type",
    "palace_element",
    "original_hexagram",
    "fate_palace_index",
)
_MAX_QUERY_VALUES = 12
_MAX_VALUE_LEN = 24


def _dump(value: Any) -> dict[str, Any]:
    """Dump a pydantic model or pass through a mapping."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return {}


def _iter_strings(value: Any, limit: int = _MAX_QUERY_VALUES) -> list[str]:
    """Deterministically collect short non-empty strings from a nested result."""
    out: list[str] = []

    def walk(node: Any) -> None:
        if len(out) >= limit:
            return
        if isinstance(node, str):
            text = node.strip()
            if text and len(text) <= _MAX_VALUE_LEN:
                out.append(text)
        elif isinstance(node, dict):
            for key in sorted(node):
                walk(node[key])
        elif isinstance(node, (list, tuple)):
            for item in node:
                walk(item)

    walk(value)
    return out[:limit]


class Explainer:
    def __init__(
        self,
        provider: InferenceProvider | None = None,
        retriever: KnowledgeRetrieverProtocol | None = None,
    ) -> None:
        self.provider = provider
        self.retriever = retriever

    # -- deterministic evidence (read-only; never recomputed) ---------------

    @staticmethod
    def evidence_of(output: AgentOutput) -> dict[str, Any]:
        """The already-computed facts an explanation is allowed to explain."""
        return {
            "agent": output.agent,
            "engine_version": output.engine_version,
            "input_hash": output.input_hash,
            "confidence": output.confidence.model_dump(mode="json"),
            "result": _dump(output.result),
            "reasoning_trace": [s.model_dump(mode="json") for s in output.reasoning_trace],
        }

    @staticmethod
    def build_query(output: AgentOutput) -> str:
        """Knowledge query derived from the deterministic result."""
        result = _dump(output.result)
        parts = [output.agent]
        for field in _QUERY_FIELDS:
            value = result.get(field)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
        parts.extend(_iter_strings(result))
        # de-duplicate while preserving order
        seen: set[str] = set()
        ordered = [p for p in parts if p and not (p in seen or seen.add(p))]
        return " ".join(ordered)

    def retrieve(self, output: AgentOutput, *, k: int = 3) -> list[Any]:
        """Retrieve authoritative knowledge for this output; never raises."""
        if self.retriever is None:
            return []
        try:
            return list(self.retriever.retrieve(self.build_query(output), k=k))
        except Exception:
            return []

    # -- the chain ----------------------------------------------------------

    def explain(self, output: AgentOutput, *, style: str = "concise", k: int = 3) -> dict[str, Any]:
        """Run the full explain chain and return prose plus provenance.

        Returns a plain dict (no new schema): ``agent``, ``explanation``,
        ``evidence``, ``knowledge``, ``provider``, ``degraded``, ``style``.
        """
        evidence = self.evidence_of(output)
        chunks = self.retrieve(output, k=k)
        degraded = self.provider is None
        note = ""
        if self.provider is None:
            text = self._fallback(output, style, chunks=chunks)
        else:
            try:
                text = self._llm_render(output, style, chunks=chunks)
            except Exception as exc:  # provider must never break the pipeline
                degraded = True
                note = f"llm_unavailable: {type(exc).__name__}"
                text = self._fallback(output, style, note=note, chunks=chunks)
        return {
            "agent": output.agent,
            "explanation": text,
            "evidence": evidence,
            "knowledge": [{"id": c.id, "source": c.source, "text": c.text} for c in chunks],
            "provider": getattr(self.provider, "name", None) if self.provider else None,
            "degraded": degraded,
            "style": style,
        }

    def render(self, output: AgentOutput, *, style: str = "concise", k: int = 3) -> str:
        """Explain as prose. Single code path: always the full chain."""
        return str(self.explain(output, style=style, k=k)["explanation"])

    # -- providers ----------------------------------------------------------

    def _build_prompt(
        self,
        output: AgentOutput,
        style: str,
        chunks: list[Any] | tuple[Any, ...] = (),
    ) -> str:
        # Only the fact layer enters the prompt: the output envelope carries a
        # wall-clock timestamp, which would make identical requests produce
        # different prompts (and therefore non-deterministic explanations).
        payload = json.dumps(Explainer.evidence_of(output), ensure_ascii=False)
        prompt = (
            f"You are explaining a deterministic metaphysics result. Do NOT recompute "
            f"any numbers; describe the given structured result in {style} prose.\n"
            f"Agent: {output.agent}\nConfidence: {output.confidence.value}\n"
            f"Result JSON:\n{payload}\n"
        )
        if chunks:
            context = "\n".join(f"- {c.text}" for c in chunks)
            prompt += f"Authoritative context:\n{context}\n"
        prompt += "Output only the explanation."
        return prompt

    def _llm_render(
        self,
        output: AgentOutput,
        style: str,
        chunks: list[Any] | tuple[Any, ...] = (),
    ) -> str:
        s = get_settings()
        if self.provider is None:
            return self._fallback(output, style, chunks=chunks)
        return self.provider.generate(
            self._build_prompt(output, style, chunks),
            model=s.ollama_model,
            temperature=s.explain_temperature,
            max_tokens=s.explain_max_tokens,
        )

    @staticmethod
    def _fallback(
        output: AgentOutput,
        style: str,
        note: str = "",
        chunks: list[Any] | tuple[Any, ...] = (),
    ) -> str:
        head = f"[{output.agent}] deterministic result (engine {output.engine_version}, "
        head += f"confidence {output.confidence.value:.2f})."
        # Render from the fact layer only: including the envelope's wall-clock
        # timestamp would make the same request yield different explanations.
        body = json.dumps(Explainer.evidence_of(output), ensure_ascii=False)[:400]
        text = (head + " " + note + " " + body).strip()
        if chunks:
            cited = "; ".join(f"{c.source or c.id}" for c in chunks[:3])
            text += f" [knowledge: {cited}]"
        return text


class KnowledgeRetrieverProtocol(Protocol):
    def retrieve(self, query: str, *, k: int = 5) -> list: ...


# agent name -> (module, class); resolved lazily to avoid an import cycle
_DOMAIN_EXPLAINERS: dict[str, tuple[str, str]] = {
    "bazi": ("openmetaphysics.agents.bazi_explainer", "BaziExplainer"),
    "ziwei": ("openmetaphysics.agents.ziwei_explainer", "ZiweiExplainer"),
}


def get_explainer_for(
    agent: str | None = None,
    provider: InferenceProvider | None = None,
    retriever: KnowledgeRetrieverProtocol | None = None,
) -> Explainer:
    """Return the explainer for an agent, falling back to the generic Explainer.

    Wires the existing domain explainers (Bazi / Ziwei) that previously had no
    caller. If the provider or retriever is omitted, the configured ones are used.
    """
    if provider is None:
        provider = get_provider()
    if retriever is None:
        try:
            from ..rag.retriever import get_retriever

            retriever = get_retriever()
        except Exception:
            retriever = None

    entry = _DOMAIN_EXPLAINERS.get(agent or "")
    if entry is not None:
        module_name, class_name = entry
        try:
            import importlib

            cls = getattr(importlib.import_module(module_name), class_name)
            return cls(provider=provider, retriever=retriever)  # type: ignore[no-any-return]
        except Exception:
            pass
    return Explainer(provider=provider, retriever=retriever)


def get_explainer(agent: str | None = None) -> Explainer:
    return get_explainer_for(agent)
