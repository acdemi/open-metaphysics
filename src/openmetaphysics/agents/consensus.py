"""Consensus agent — aggregates validated agent outputs.

Cross-validates modalities via shared 五行 signals, builds a pairwise agreement
matrix, detects conflicts, and produces a deterministic synthesis. Fully
deterministic; no LLM. Does not inherit BaseAgent (input is a list of outputs,
not a birth record).
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..core.engines import TraceRecorder
from ..core.models import wuxing_relation
from ..core.schemas import AgentOutput, utcnow


class ConsensusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str
    agent_outputs: list[AgentOutput] = Field(min_length=1)
    strategy: Literal["weighted", "majority", "all"] = "weighted"


class AgentContribution(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent: str
    confidence: float
    weight: float
    element: str | None
    summary: str


class Conflict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agents: list[str]
    field: str
    values: list[str]
    severity: Literal["low", "medium", "high"]


class ConsensusReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    overall_confidence: float
    contributions: list[AgentContribution]
    agreement_matrix: dict[str, dict[str, float]]
    conflicts: list[Conflict]
    synthesis: str
    recommendation: str | None = None


class ConsensusOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str
    agent: str = "consensus"
    engine_version: str
    computed_at: Any
    confidence: float
    reasoning_trace: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    result: ConsensusReport


def _result_dict(output: AgentOutput) -> dict:
    r = output.result
    return r.model_dump() if hasattr(r, "model_dump") else r


def _element_of(output: AgentOutput) -> str | None:
    r = _result_dict(output)
    name = output.agent
    if name == "bazi":
        return r.get("day_master_element")
    if name == "ziwei":
        ju = r.get("wuxing_ju", "")
        return ju[0] if ju else None
    if name == "liuyao":
        return r.get("palace_element")
    return None


def _agreement(a: str | None, b: str | None) -> float:
    if a is None or b is None:
        return 0.5
    if a == b:
        return 1.0
    rel = wuxing_relation(a, b)
    return {"sheng": 0.75, "being_sheng": 0.75, "ke": 0.4, "being_ke": 0.4}.get(rel, 0.5)


class ConsensusAgent:
    name = "consensus"
    engine_version = "0.1.0"
    input_schema = ConsensusInput
    output_schema = ConsensusOutput

    def compute(self, payload: ConsensusInput) -> ConsensusOutput:
        trace = TraceRecorder()
        outs = payload.agent_outputs
        elements = {o.agent: _element_of(o) for o in outs}
        trace.record("consensus.elements", "extract 五行 signal per modality", outputs=elements)

        # weights
        if payload.strategy == "majority" or payload.strategy == "all":
            weights = {o.agent: 1.0 for o in outs}
        else:
            weights = {o.agent: float(o.confidence.value) for o in outs}
        total_w = sum(weights.values()) or 1.0

        # agreement matrix
        matrix: dict[str, dict[str, float]] = {}
        for a in outs:
            matrix[a.agent] = {}
            for b in outs:
                matrix[a.agent][b.agent] = _agreement(elements[a.agent], elements[b.agent])
        trace.record(
            "consensus.agreement", "pairwise 五行 agreement matrix", outputs={"pairs": len(outs)}
        )

        # conflicts: ke/being_ke relations
        conflicts: list[Conflict] = []
        seen = set()
        for a in outs:
            for b in outs:
                if a.agent >= b.agent:
                    continue
                ea, eb = elements[a.agent], elements[b.agent]
                if ea and eb and ea != eb:
                    rel = wuxing_relation(ea, eb)
                    if rel in ("ke", "being_ke"):
                        key = (a.agent, b.agent)
                        if key not in seen:
                            seen.add(key)
                            conflicts.append(
                                Conflict(
                                    agents=[a.agent, b.agent],
                                    field="element",
                                    values=[ea, eb],
                                    severity="medium",
                                )
                            )
        trace.record(
            "consensus.conflicts",
            "detect 克 relations across modalities",
            outputs={"conflicts": len(conflicts)},
        )

        # overall confidence: weighted mean * agreement factor
        base = sum(float(o.confidence.value) * weights[o.agent] for o in outs) / total_w
        if len(outs) >= 2:
            pair_scores = [
                matrix[a.agent][b.agent] for i, a in enumerate(outs) for b in outs[i + 1 :]
            ]
            agreement_factor = sum(pair_scores) / len(pair_scores) if pair_scores else 1.0
        else:
            agreement_factor = 1.0
        overall = max(0.0, min(1.0, base * (0.5 + 0.5 * agreement_factor)))
        trace.record(
            "consensus.overall",
            "aggregate confidence",
            outputs={
                "base": round(base, 4),
                "agreement_factor": round(agreement_factor, 4),
                "overall": round(overall, 4),
            },
        )

        contributions = [
            AgentContribution(
                agent=o.agent,
                confidence=float(o.confidence.value),
                weight=round(weights[o.agent], 4),
                element=elements[o.agent],
                summary=self._summary(o),
            )
            for o in outs
        ]

        parts = [f"{c.agent}({c.element or 'n/a'}, conf={c.confidence:.2f})" for c in contributions]
        synthesis = "Cross-modal consensus over: " + ", ".join(parts) + "."
        if conflicts:
            synthesis += f" {len(conflicts)} element conflict(s) detected."
        else:
            synthesis += " No element conflicts."
        recommendation = self._recommend(overall, conflicts)

        report = ConsensusReport(
            overall_confidence=round(overall, 4),
            contributions=contributions,
            agreement_matrix=matrix,
            conflicts=conflicts,
            synthesis=synthesis,
            recommendation=recommendation,
        )
        return ConsensusOutput(
            request_id=payload.request_id,
            engine_version=self.engine_version,
            computed_at=utcnow(),
            confidence=round(overall, 4),
            reasoning_trace=[s.model_dump() for s in trace.steps],
            metadata={"strategy": payload.strategy, "agent_count": len(outs)},
            result=report,
        )

    @staticmethod
    def _summary(o: AgentOutput) -> str:
        r = _result_dict(o)
        if o.agent == "bazi":
            return f"日主 {r.get('day_master')}"
        if o.agent == "liuyao":
            return f"本卦#{r.get('original_hexagram')} 宫{r.get('palace')}"
        if o.agent == "ziwei":
            return f"{r.get('wuxing_ju')} 命宫#{r.get('fate_palace_index')}"
        if o.agent == "qimen":
            return f"{r.get('dun_type')}遁 局{r.get('ju')}"
        return str(o.agent)

    @staticmethod
    def _recommend(overall: float, conflicts: list[Conflict]) -> str:
        if overall >= 0.75 and not conflicts:
            return "high_agreement"
        if conflicts:
            return "review_conflicts"
        return "moderate_agreement"

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "engine_version": self.engine_version,
            "input_schema": self.input_schema.model_json_schema(),
            "output_schema": self.output_schema.model_json_schema(),
        }
