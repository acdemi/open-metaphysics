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
import re
from typing import Any, Protocol

from ..core.config import get_settings
from ..core.schemas import AgentOutput
from .providers import InferenceProvider, get_provider

__all__ = ["Explainer", "KnowledgeRetrieverProtocol", "get_explainer", "get_explainer_for"]

# Deterministic, semantic query construction for knowledge retrieval (Phase C2).
#
# Priority order:
#   1. domain-specific semantic fields (star / element / god / palace names)
#   2. the request question, when present (the user's own domain terms)
#   3. CJK-bearing semantic strings found anywhere in the result
#
# Deliberately excluded: dates and timestamps, input_hash, large JSON blobs,
# reasoning_trace, and bare numbers -- they carry no retrieval semantics and
# were the main source of irrelevant hits.
_QUERY_FIELDS: dict[str, tuple[str, ...]] = {
    "bazi": (
        "day_master",
        "day_master_element",
        "year_pillar",
        "month_pillar",
        "day_pillar",
        "hour_pillar",
    ),
    "ziwei": ("wuxing_ju",),
    "qimen": ("dun_type", "ju"),
    "liuyao": ("palace", "palace_element", "yong_shen"),
}
_MAX_QUERY_VALUES = 6
_MAX_VALUE_LEN = 24

# a string worth querying contains at least one CJK ideograph
_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")

# == Prompt contract (Phase D) ==
# The prompt separates the three kinds of material explicitly and states the
# LLM's limits. Shared with the domain explainers so that every provider prompt
# carries the same contract.
PROMPT_FACTS_HEADER = "## FACTS (deterministic calculation output)"
PROMPT_KNOWLEDGE_HEADER = "## KNOWLEDGE (authoritative citations -- NOT calculation facts)"
PROMPT_QUESTION_HEADER = "## USER QUESTION"
PROMPT_RULES = (
    "RULES:\n"
    "- FACTS is the complete, authoritative calculation result. Do NOT modify it and do\n"
    "  not add, remove, correct or recompute any value in it.\n"
    "- Do NOT invent any calculation result that is not present in FACTS.\n"
    "- KNOWLEDGE entries are citations provided for context only. They are NOT calculation\n"
    "  facts and must never be reported as part of the result.\n"
    "- Explain only what FACTS contains, as natural language."
)

# credential-like material must never be echoed into a prompt or an error record
_SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_\-]{6,}|Bearer\s+\S+)")


def redact(text: str) -> str:
    """Remove anything that looks like an API credential."""
    return _SECRET_RE.sub("[redacted]", text)


def classify_provider_error(exc: BaseException) -> str:
    """Map a provider failure onto a stable, reportable kind.

    Kinds: ``timeout`` | ``rate_limit`` | ``unavailable`` | ``invalid_response``
    | ``error``.
    """
    name = type(exc).__name__
    if name in {"TimeoutException", "ReadTimeout", "ConnectTimeout", "PoolTimeout", "Timeout"}:
        return "timeout"
    if name in {"ConnectError", "ConnectionError", "RemoteProtocolError", "NetworkError"}:
        return "unavailable"
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if status == 429:
        return "rate_limit"
    if isinstance(status, int) and status >= 500:
        return "unavailable"
    if isinstance(status, int) and 400 <= status < 500:
        return "invalid_response"
    if isinstance(exc, (ValueError, KeyError, TypeError)):
        return "invalid_response"
    text = redact(str(exc)).lower()
    if "timed out" in text or "timeout" in text:
        return "timeout"
    if "rate limit" in text or "429" in text:
        return "rate_limit"
    if "connection" in text or "unavailable" in text:
        return "unavailable"
    return "error"


def _dump(value: Any) -> dict[str, Any]:
    """Dump a pydantic model or pass through a mapping."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return {}


def _semantic_token(text: str) -> list[str]:
    """A query token worth keeping: short, non-empty and CJK-bearing."""
    token = text.strip()
    if token and len(token) <= _MAX_VALUE_LEN and _CJK.search(token):
        return [token]
    return []


def _iter_semantic_strings(value: Any, limit: int = _MAX_QUERY_VALUES) -> list[str]:
    """Deterministically collect short CJK-bearing strings from a nested result.

    Anything without a CJK character (dates, numbers, hashes, ISO stamps,
    ASCII flags) is skipped: it cannot usefully match the Chinese knowledge
    corpus and only diluted the ranking.
    """
    out: list[str] = []

    def walk(node: Any) -> None:
        if len(out) >= limit:
            return
        if isinstance(node, str):
            text = node.strip()
            if text and len(text) <= _MAX_VALUE_LEN and _CJK.search(text):
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
            # carries the caller's question through the explain chain (Phase C1)
            "metadata": dict(output.metadata),
        }

    @staticmethod
    def build_query(output: AgentOutput) -> str:
        """Deterministic semantic query for knowledge retrieval (Phase C2).

        Order: agent name, domain-specific semantic fields, the request
        question, then CJK-bearing strings found in the result. Dates, numbers,
        hashes and other non-semantic values are never included.
        """
        result = _dump(output.result)
        parts: list[str] = [output.agent]

        for field in _QUERY_FIELDS.get(output.agent, ()):
            value = result.get(field)
            if isinstance(value, str):
                parts.extend(_semantic_token(value))
            elif isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, str):
                        parts.extend(_semantic_token(item))

        question = output.metadata.get("question")
        if isinstance(question, str) and question.strip():
            parts.append(question.strip())

        parts.extend(_iter_semantic_strings(result))

        # de-duplicate while preserving order
        seen: set[str] = set()
        ordered = [p for p in parts if p and not (p in seen or seen.add(p))]
        return " ".join(ordered)

    def retrieve(self, output: AgentOutput, *, k: int = 3) -> list[Any]:
        """Retrieve authoritative knowledge for this output; never raises.

        Candidates are restricted to the agent's own domain tags first: a Ziwei
        explanation must not cite BaZi-only knowledge. ``k`` candidates are
        over-fetched before filtering so the domain still fills the quota when
        adjacent domains rank higher on raw character overlap. If no
        domain-tagged candidate exists (sparse corpus), retrieval degrades to
        the unfiltered result instead of dropping its context.
        """
        if self.retriever is None:
            return []
        try:
            query = self.build_query(output)
            domain = str(getattr(output, "agent", "") or "")
            candidates = list(self.retriever.retrieve(query, k=max(k * 20, 60)))
            domain_chunks = [
                chunk for chunk in candidates if domain and domain in getattr(chunk, "tags", [])
            ]
            if domain_chunks:
                return domain_chunks[:k]
            return candidates[:k]
        except Exception:
            return []

    # -- the chain ----------------------------------------------------------

    def explain(self, output: AgentOutput, *, style: str = "concise", k: int = 3) -> dict[str, Any]:
        """Run the full explain chain and return prose plus provenance.

        Returns a plain dict (no new schema): ``agent``, ``explanation``,
        ``evidence``, ``knowledge``, ``provider``, ``degraded``, ``error``,
        ``style``.

        A provider failure -- timeout, rate limit, unavailable service or an
        unusable response -- must never fail the request: the deterministic
        result is already computed and stays available, the explanation degrades
        to deterministic prose, and the failure is recorded under ``error``.
        """
        evidence = self.evidence_of(output)
        chunks = self.retrieve(output, k=k)
        provider_name = getattr(self.provider, "name", None) if self.provider else None
        degraded = self.provider is None
        error: dict[str, Any] | None = None
        text: str

        if self.provider is None:
            text = self._fallback(output, style, chunks=chunks)
        else:
            try:
                text = self._llm_render(output, style, chunks=chunks)
                if not str(text).strip():
                    raise ValueError("provider returned an empty response")
            except Exception as exc:  # provider must never break the pipeline
                degraded = True
                error = {
                    "kind": classify_provider_error(exc),
                    "type": type(exc).__name__,
                    "message": redact(str(exc))[:200],
                    "provider": provider_name,
                }
                text = self._fallback(output, style, note=error["kind"], chunks=chunks)

        return {
            "agent": output.agent,
            "explanation": text,
            "evidence": evidence,
            "knowledge": [{"id": c.id, "source": c.source, "text": c.text} for c in chunks],
            "provider": provider_name,
            "degraded": degraded,
            "error": error,
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
        """Build a provider prompt following the Phase D prompt contract.

        Only the fact layer enters the FACTS section: the output envelope
        carries a wall-clock timestamp, which would make identical requests
        produce different prompts (and therefore non-deterministic
        explanations).
        """
        payload = json.dumps(Explainer.evidence_of(output), ensure_ascii=False)
        prompt = (
            f"You are explaining a deterministic metaphysics result in {style} prose.\n"
            f"Agent: {output.agent}\nConfidence: {output.confidence.value}\n\n"
            f"{PROMPT_FACTS_HEADER}\n{payload}\n\n"
        )
        if chunks:
            prompt += f"{PROMPT_KNOWLEDGE_HEADER}\n"
            for chunk in chunks:
                citation = f" ({chunk.source})" if getattr(chunk, "source", "") else ""
                prompt += f"- {chunk.text}{citation}\n"
            prompt += "\n"
        question = output.metadata.get("question")
        if isinstance(question, str) and question.strip():
            prompt += f"{PROMPT_QUESTION_HEADER}\n{question.strip()}\n\n"
        prompt += f"{PROMPT_RULES}\n"
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
    # P2.2: Qimen joins the same explainer chain (query construction only; the
    # prompt contract and the offline fallback stay the generic ones).
    "qimen": ("openmetaphysics.agents.qimen_explainer", "QimenExplainer"),
    # P2.3: Liuyao joins the same chain for the same reason (卦名/六神/世应/纳甲
    # never entered the generic query, which is filled by the six 六亲 values).
    "liuyao": ("openmetaphysics.agents.liuyao_explainer", "LiuyaoExplainer"),
}


def get_explainer_for(
    agent: str | None = None,
    provider: InferenceProvider | None = None,
    retriever: KnowledgeRetrieverProtocol | None = None,
) -> Explainer:
    """Return the explainer for an agent, falling back to the generic Explainer.

    Wires the existing domain explainers (Bazi / Ziwei / Qimen / Liuyao) that
    previously had no caller. If the provider or retriever is omitted, the
    configured ones are used.
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
