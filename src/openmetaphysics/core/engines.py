"""Deterministic engine + agent base classes.

The defining contract: ``calculate``/``compute`` are pure functions of input.
No I/O, no wall-clock, no unseeded RNG. An optional, isolated ``explainer``
(LLM) lives behind a separate ``explain`` method and can never reach the engine.
"""

from __future__ import annotations

import hashlib
import random
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from .schemas import (
    AgentInput,
    AgentOutput,
    ConfidenceScore,
    ReasoningStep,
    hash_input,
    utcnow,
)

# Declared baseline, NOT a calibrated probability / measured rule coverage (H8).
# All four deterministic domains run a fixed, fully-applied rule pipeline, so
# there is no held-out population or ground truth to calibrate against. Keeping
# the number stable preserves API/Consensus compatibility; only the *meaning*
# is declared honestly via ``method``/``factors``.
PLACEHOLDER_CONFIDENCE_VALUE = 0.95
PLACEHOLDER_CONFIDENCE_METHOD = "placeholder_baseline"


class _TraceState:
    """Steps and counter for exactly one computation (context-local)."""

    __slots__ = ("n", "steps")

    def __init__(self) -> None:
        self.steps: list[ReasoningStep] = []
        self.n = 0


_CURRENT_TRACE: ContextVar[_TraceState | None] = ContextVar(
    "openmetaphysics_current_trace", default=None
)


class TraceRecorder:
    """Accumulates auditable ReasoningStep records during a computation.

    The recorder is a *view* over the context-local trace: while
    ``DeterministicEngine.isolated_trace`` is active every thread/async task
    records into its own state, so concurrent computes never interleave.
    Outside such a scope it falls back to an instance-owned state, keeping
    direct ``engine.calculate`` use working as before.
    """

    def __init__(self) -> None:
        self._own = _TraceState()

    @property
    def _state(self) -> _TraceState:
        current = _CURRENT_TRACE.get()
        return current if current is not None else self._own

    @property
    def steps(self) -> list[ReasoningStep]:
        return self._state.steps

    def record(
        self,
        rule_ref: str,
        description: str,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
    ) -> None:
        state = self._state
        state.n += 1
        state.steps.append(
            ReasoningStep(
                step=state.n,
                rule_ref=rule_ref,
                description=description,
                inputs=_coerce(inputs),
                outputs=_coerce(outputs),
            )
        )

    def apply(self, rule_ref: str, description: str, fn, inputs: dict[str, Any]):
        """Run ``fn(**inputs)``, recording inputs/outputs. Returns fn's result."""
        result = fn(**inputs)
        self.record(rule_ref, description, inputs=inputs, outputs=_as_outputs(result))
        return result

    def reset(self) -> None:
        """Clear the trace visible in the current context."""
        current = _CURRENT_TRACE.get()
        if current is None:
            self._own = _TraceState()
        else:
            current.steps.clear()
            current.n = 0


def _coerce(d: dict[str, Any] | None) -> dict[str, str | int | float | bool]:
    if not d:
        return {}
    out: dict[str, str | int | float | bool] = {}
    for k, v in d.items():
        out[str(k)] = v if isinstance(v, (str, int, float, bool)) else str(v)
    return out


def _as_outputs(result: Any) -> dict[str, str | int | float | bool]:
    if isinstance(result, dict):
        return _coerce(result)
    return {"result": str(result)}


class DeterministicEngine(ABC):
    """Base class for all calculation engines. Subclasses implement ``calculate``."""

    version: str = "0.0.0"

    def __init__(self) -> None:
        self.trace = TraceRecorder()

    @contextmanager
    def isolated_trace(self) -> Iterator[TraceRecorder]:
        """Bind a fresh, context-local trace to one computation.

        Used by ``BaseAgent.compute``: an engine instance may be shared by
        concurrent requests, so the trace must never be written to shared
        state. A ``ContextVar`` (not a lock) gives every thread/async task its
        own recorder while keeping the public ``engine.trace`` API unchanged.
        """
        token = _CURRENT_TRACE.set(_TraceState())
        try:
            yield self.trace
        finally:
            _CURRENT_TRACE.reset(token)

    @abstractmethod
    def calculate(self, payload: AgentInput) -> dict[str, Any]:
        """Pure function: same input -> byte-identical output. No LLM, no I/O."""

    def reset(self) -> None:
        self.trace.reset()


def deterministic_rng(seed: int) -> random.Random:
    """A seeded PRNG. ``random.Random`` is stable across runs for a given seed."""
    return random.Random(seed)


def derive_seed(payload: AgentInput) -> int:
    """Deterministic seed from input: explicit ``seed`` else SHA-256 of the envelope.

    Python's built-in ``hash()`` is salted per process (``PYTHONHASHSEED``), so
    using it made the auto-cast Liuyao path unreproducible across processes.
    SHA-256 of ``request_id`` + ``client_nonce`` is stable everywhere; the
    explicit ``seed`` path is unchanged.
    """
    if payload.seed is not None:
        return payload.seed
    material = f"{payload.request_id}\x1f{payload.client_nonce or ''}".encode()
    digest = hashlib.sha256(material).digest()
    return int.from_bytes(digest[:8], "big") % (2**31)


@runtime_checkable
class ExplainerProtocol(Protocol):
    def render(self, output: AgentOutput, *, style: str = "concise") -> str: ...


class BaseAgent(ABC):
    """Template-method base for all agents.

    Concrete agents implement ``_compute_result`` (deterministic) and may
    override ``_explain_fallback`` (deterministic templated prose). Attaching an
    ``explainer`` enables LLM prose via ``explain`` without touching ``compute``.
    """

    name: str
    engine_version: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    engine: DeterministicEngine
    explainer: ExplainerProtocol | None = None

    def compute(self, payload: AgentInput) -> AgentOutput:
        validated = self.input_schema.model_validate(payload.model_dump())
        # The engine is shared by the singleton agents, so its trace is bound
        # context-locally for the duration of this call: concurrent requests get
        # independent step lists and cannot pollute each other's reasoning_trace.
        with self.engine.isolated_trace() as trace:
            result = self._compute_result(validated)
            steps = list(trace.steps)
        confidence = self._confidence(result, steps)
        return self.output_schema(
            request_id=validated.request_id,
            agent=self.name,
            engine_version=self.engine_version,
            input_hash=hash_input(validated),
            computed_at=utcnow(),
            confidence=confidence,
            reasoning_trace=steps,
            metadata=self._output_metadata(validated),
            result=result,
        )

    @abstractmethod
    def _compute_result(self, payload: AgentInput) -> dict[str, Any]: ...

    def _confidence(self, result: dict[str, Any], steps: list[ReasoningStep]) -> ConfidenceScore:
        """Declared baseline confidence — explicitly NOT statistical coverage.

        The previous ``method="rule_coverage"`` was misleading: the value was a
        constant 0.95, not a ratio of covered rules, and there is no calibrated
        ground truth behind it. ``placeholder_baseline`` + ``calibrated == 0.0``
        make that machine-readable. A real scorer must change method and value
        together and re-derive the Consensus weighting (which uses the value).
        """
        return ConfidenceScore(
            value=PLACEHOLDER_CONFIDENCE_VALUE,
            method=PLACEHOLDER_CONFIDENCE_METHOD,
            factors={"steps": float(len(steps)), "calibrated": 0.0},
        )

    def _metadata(self) -> dict[str, str | int | float | bool]:
        return {"engine_version": self.engine_version, "deterministic": True}

    def _output_metadata(
        self, payload: AgentInput | None = None
    ) -> dict[str, str | int | float | bool]:
        """Envelope metadata, plus the caller's question.

        The question is carried on the output so the explain pipeline can see
        what the user actually asked. ``metadata`` is an existing free-form dict
        on ``AgentOutput``: no field is added or retyped, and the deterministic
        ``result`` is unaffected. Subclasses keep overriding ``_metadata``
        unchanged.
        """
        metadata = dict(self._metadata())
        question = getattr(payload, "question", None)
        if question:
            metadata["question"] = str(question)
        return metadata

    def explain(self, output: AgentOutput, style: str = "concise") -> str:
        """Explain a computed output.

        Delegates to the attached explainer whenever one is present: the
        explainer owns the offline path too (deterministic prose + retrieved
        knowledge), so the chain must not be skipped just because no LLM
        provider is configured.
        """
        if self.explainer is not None:
            return self.explainer.render(output, style=style)
        return self._explain_fallback(output, style=style)

    def _explain_fallback(self, output: AgentOutput, *, style: str) -> str:
        return (
            f"[{self.name}] deterministic result (engine {self.engine_version}); no LLM attached."
        )

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "engine_version": self.engine_version,
            "input_schema": self.input_schema.model_json_schema(),
            "output_schema": self.output_schema.model_json_schema(),
        }


__all__ = [
    "TraceRecorder",
    "DeterministicEngine",
    "deterministic_rng",
    "derive_seed",
    "ExplainerProtocol",
    "BaseAgent",
]
