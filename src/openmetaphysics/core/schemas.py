"""Shared Pydantic v2 schemas: the inter-agent / inter-process contract.

Agent-specific input/output schemas live with their agents. Every public model
here is exportable to JSON Schema via ``Model.model_json_schema()``.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    elevation_m: float | None = None
    timezone: str | None = None  # IANA tz, e.g. "Asia/Hong_Kong"


class SexagenaryComponent(BaseModel):
    """A 干支 (stem-branch) pair, the atomic unit of Bazi/Qimen."""

    model_config = ConfigDict(frozen=True)
    heavenly_stem: str
    earthly_branch: str
    stem_index: int = Field(ge=0, le=9)
    branch_index: int = Field(ge=0, le=11)


class AgentInput(BaseModel):
    """Base input envelope. Subclasses add agent-specific fields."""

    model_config = ConfigDict(extra="forbid")
    request_id: str
    born_at: datetime
    born_location: GeoPoint | None = None
    gender: Gender = Gender.UNKNOWN
    question: str | None = None
    locale: str = "zh-CN"
    seed: int | None = None  # deterministic RNG seed (e.g. Liuyao casts)
    client_nonce: str | None = None  # idempotency/replay key

    @field_validator("born_at")
    @classmethod
    def _must_be_tz_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("born_at must be timezone-aware")
        return v


class ReasoningStep(BaseModel):
    """One auditable step of a deterministic computation."""

    model_config = ConfigDict(extra="forbid")
    step: int
    rule_ref: str  # e.g. "bazi.month_pillar.solar_term"
    description: str
    inputs: dict[str, str | int | float | bool] = Field(default_factory=dict)
    outputs: dict[str, str | int | float | bool] = Field(default_factory=dict)


class ConfidenceScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: float = Field(ge=0.0, le=1.0)
    method: str  # e.g. "rule_coverage" | "data_quality"
    factors: dict[str, float] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    """Base output envelope. Subclasses override ``result`` typing."""

    model_config = ConfigDict(extra="forbid")
    request_id: str
    agent: str  # "bazi" | "ziwei" | "qimen" | "liuyao"
    engine_version: str
    input_hash: str  # sha256 of canonical input -> replay key
    computed_at: datetime
    confidence: ConfidenceScore
    reasoning_trace: list[ReasoningStep] = Field(default_factory=list)
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)


def canonical_input(payload: BaseModel) -> str:
    """Deterministic JSON serialization of an input model (for hashing/replay)."""
    return json.dumps(
        payload.model_dump(mode="json"),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def hash_input(payload: BaseModel) -> str:
    return hashlib.sha256(canonical_input(payload).encode("utf-8")).hexdigest()


__all__ = [
    "Gender",
    "GeoPoint",
    "SexagenaryComponent",
    "AgentInput",
    "ReasoningStep",
    "ConfidenceScore",
    "AgentOutput",
    "canonical_input",
    "hash_input",
    "utcnow",
]
