"""Deterministic engine + agent base classes.

The defining contract: ``calculate``/``compute`` are pure functions of input.
No I/O, no wall-clock, no unseeded RNG. An optional, isolated ``explainer``
(LLM) lives behind a separate ``explain`` method and can never reach the engine.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
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


class TraceRecorder:
    """Accumulates auditable ReasoningStep records during a computation."""

    def __init__(self) -> None:
        self.steps: list[ReasoningStep] = []
        self._n = 0

    def record(
        self,
        rule_ref: str,
        description: str,
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
    ) -> None:
        self._n += 1
        self.steps.append(
            ReasoningStep(
                step=self._n,
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

    @abstractmethod
    def calculate(self, payload: AgentInput) -> dict[str, Any]:
        """Pure function: same input -> byte-identical output. No LLM, no I/O."""

    def reset(self) -> None:
        self.trace = TraceRecorder()


def deterministic_rng(seed: int) -> random.Random:
    """A seeded PRNG. ``random.Random`` is stable across runs for a given seed."""
    return random.Random(seed)


def derive_seed(payload: AgentInput) -> int:
    """Deterministic seed from input: explicit ``seed`` else hash of request_id."""
    if payload.seed is not None:
        return payload.seed
    return abs(hash((payload.request_id, payload.client_nonce))) % (2**31)


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
        self.engine.reset()
        result = self._compute_result(validated)
        confidence = self._confidence(result, self.engine.trace.steps)
        return self.output_schema(
            request_id=validated.request_id,
            agent=self.name,
            engine_version=self.engine_version,
            input_hash=hash_input(validated),
            computed_at=utcnow(),
            confidence=confidence,
            reasoning_trace=list(self.engine.trace.steps),
            metadata=self._metadata(),
            result=result,
        )

    @abstractmethod
    def _compute_result(self, payload: AgentInput) -> dict[str, Any]: ...

    def _confidence(self, result: dict[str, Any], steps: list[ReasoningStep]) -> ConfidenceScore:
        """Default confidence: high for fully rule-covered deterministic output."""
        return ConfidenceScore(
            value=0.95, method="rule_coverage", factors={"steps": float(len(steps))}
        )

    def _metadata(self) -> dict[str, str | int | float | bool]:
        return {"engine_version": self.engine_version, "deterministic": True}

    def explain(self, output: AgentOutput, style: str = "concise") -> str:
        if self.explainer is not None and getattr(self.explainer, "provider", None) is not None:
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
