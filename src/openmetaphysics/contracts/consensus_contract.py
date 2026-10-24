"""Consensus Contract Adapter — machine-verifiable contract layer.

职责:
- 承载冻结共识契约 v1.0.0 的机器可读清单 (MANIFEST)
- validate_input:  校验输入满足契约前置条件
- validate_output: 校验输出满足契约可观察要求 (CS-001 ~ CS-025 中机器可检查部分)
- validate_vector: 单条规范向量 → 运行时逐字节复算比对
- validate_golden_vectors: 全部规范向量校验

纪律:
- 不修改运行时 (openmetaphysics.consensus 只读导入)
- 不新增任何共识规则 (校验项全部源自冻结契约条款)
- 不改变运行时行为

契约真源:
- reference/contracts/consensus_contract.json   (冻结契约 v1.0.0, 自动生成)
- reference/conformance/golden/consensus_vectors.json  (3 条规范向量)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..consensus import (
    ConsensusConclusion,
    ConsensusConfig,
    ConsensusEngine,
    ConsensusInput,
    ConsensusReport,
    ConsensusStrategy,
    Domain,
)

__version__ = "1.0.0"

_CONTRACT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _CONTRACT_DIR.parents[2]

CONTRACT_FILE = _REPO_ROOT / "reference" / "contracts" / "consensus_contract.json"
VECTOR_FILE = _REPO_ROOT / "reference" / "conformance" / "golden" / "consensus_vectors.json"

# ---------------------------------------------------------------------------
# 契约清单 (机器可读; 与冻结契约共识一致)
# ---------------------------------------------------------------------------

MANIFEST: dict[str, Any] = {
    "contract_id": "consensus:behavior:v1.0.0",
    "version": "1.0.0",
    "status": "Frozen",
    "layer": "consensus",
    "engine_version": ConsensusEngine.CONTRACT_VERSION,
    "strategies": [s.value for s in ConsensusStrategy],
    "domains": [d.value for d in Domain],
    "cs_ids": [f"CS-{i:03d}" for i in range(1, 26)],
    "golden_vector_count": 3,
    "vector_classification": "normative_fixture",
    "vector_store": "reference/conformance/golden/consensus_vectors.json",
    "contract_file": "reference/contracts/consensus_contract.json",
    "contract_doc": "docs/specification/CONSENSUS_BEHAVIOR_SPEC.md",
}

# 契约声明的模型必填字段 (reference/contracts/consensus_contract.json -> models.*.required)
_CONTRACT_REQUIRED: dict[str, list[str]] = {
    "ConsensusInput": ["evidence", "config"],
    "ConsensusConfig": ["strategy"],
    "ConsensusConclusion": [
        "conclusion_id",
        "domain",
        "conclusion",
        "confidence",
        "evidence_ids",
        "evidence_count",
        "systems",
        "is_conflict",
        "strategy",
        "metadata",
        "version",
    ],
    "ConsensusReport": [
        "report_id",
        "overall_confidence",
        "domains",
        "conclusions",
        "conflicts",
        "evidence_ids",
        "metadata",
        "version",
    ],
}


def _canonical_json(obj: Any) -> str:
    """CF-001 canonical form."""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


class ConsensusContractAdapter:
    """Machine-verifiable adapter for the frozen Consensus contract v1.0.0."""

    CONTRACT_VERSION = "1.0.0"

    # -- 文件加载 ------------------------------------------------------------

    def load_manifest(self) -> dict[str, Any]:
        return dict(MANIFEST)

    def load_contract(self) -> dict[str, Any]:
        return json.loads(CONTRACT_FILE.read_text(encoding="utf-8"))

    def load_vectors(self) -> list[dict[str, Any]]:
        return json.loads(VECTOR_FILE.read_text(encoding="utf-8"))

    # -- 清单与契约对齐 ------------------------------------------------------

    def validate_manifest(self, manifest: dict | None = None) -> list[str]:
        """清单自洽性: 版本/状态/策略/域/CS 编号/向量数。"""
        target = manifest if manifest is not None else MANIFEST
        errs: list[str] = []
        if target.get("version") != self.CONTRACT_VERSION:
            errs.append(f"manifest version != {self.CONTRACT_VERSION}")
        if target.get("status") != "Frozen":
            errs.append("manifest status must be Frozen")
        if target.get("strategies") != [s.value for s in ConsensusStrategy]:
            errs.append("manifest strategies mismatch")
        if len(target.get("domains", [])) != 10:
            errs.append("manifest must declare 10 domains")
        if len(target.get("cs_ids", [])) != 25:
            errs.append("manifest must declare CS-001 ~ CS-025")
        if target.get("golden_vector_count") != len(self.load_vectors()):
            errs.append("manifest golden_vector_count mismatch")
        return errs

    def validate_contract_alignment(self) -> list[str]:
        """适配层声明的必填字段与冻结契约文件一致 (单一真源)。"""
        errs: list[str] = []
        try:
            contract = self.load_contract()
        except Exception as exc:  # pragma: no cover - defensive
            return [f"cannot load contract: {exc}"]

        if contract.get("contract_version") != self.CONTRACT_VERSION:
            errs.append("contract file version mismatch")
        if contract.get("strategies") != [s.value for s in ConsensusStrategy]:
            errs.append("contract strategies mismatch")

        models = contract.get("models", {})
        for name, declared in models.items():
            required = declared.get("required", [])
            if list(required) != _CONTRACT_REQUIRED.get(name):
                errs.append(f"required-field drift for {name}")
        if set(models) != set(_CONTRACT_REQUIRED):
            errs.append("contract model set mismatch")
        return errs

    def validate_runtime_alignment(self) -> list[str]:
        """运行时模型必填字段与契约声明一致 (生产实现向契约对齐)。"""
        errs: list[str] = []
        runtime = {
            "ConsensusInput": ConsensusInput,
            "ConsensusConfig": ConsensusConfig,
            "ConsensusConclusion": ConsensusConclusion,
            "ConsensusReport": ConsensusReport,
        }
        for name, model in runtime.items():
            required = [f for f, v in model.model_fields.items() if v.is_required()]
            declared = _CONTRACT_REQUIRED[name]
            missing = [f for f in declared if f not in model.model_fields]
            if missing:
                errs.append(f"{name}: missing contract fields {missing}")
            if not set(required) <= set(model.model_fields):
                errs.append(f"{name}: required-field mismatch")
        return errs

    # -- 输入 / 输出校验 -----------------------------------------------------

    def validate_input(self, payload: Any) -> list[str]:
        """输入须为合法 ConsensusInput (evidence[] + config)。"""
        if isinstance(payload, ConsensusInput):
            return []
        if not isinstance(payload, dict):
            return ["input must be an object with 'evidence' and 'config'"]
        try:
            ConsensusInput.model_validate(payload)
        except Exception as exc:
            return [f"invalid input: {exc}"]
        return []

    def validate_output(self, report: Any) -> list[str]:
        """输出须满足契约可观察不变量。"""
        if isinstance(report, ConsensusReport):
            data = report.model_dump(mode="json")
        elif isinstance(report, dict):
            data = report
        else:
            return ["output must be a ConsensusReport"]

        errs: list[str] = []
        for field in _CONTRACT_REQUIRED["ConsensusReport"]:
            if field not in data:
                errs.append(f"report missing required field: {field}")

        if not str(data.get("report_id", "")).startswith("cr:"):
            errs.append("report_id must match cr:<hash>")

        conclusions = data.get("conclusions", [])
        for cc in conclusions:
            for field in _CONTRACT_REQUIRED["ConsensusConclusion"]:
                if field not in cc:
                    errs.append(f"conclusion missing required field: {field}")
                    break
            if not str(cc.get("conclusion_id", "")).startswith("cc:"):
                errs.append("conclusion_id must match cc:<domain>:<hash>")

        # CS-011 / CS-012 / CS-023: sorted domains, conclusions, evidence_ids
        if data.get("domains") != sorted(data.get("domains", [])):
            errs.append("CS-011: domains must be sorted")
        if data.get("evidence_ids") != sorted(data.get("evidence_ids", [])):
            errs.append("CS-023: evidence_ids must be sorted")
        keys = [
            (c["domain"], -c["confidence"], c["conclusion"], c["conclusion_id"])
            for c in conclusions
        ]
        if keys != sorted(keys):
            errs.append("CS-012: conclusions must be sorted")

        # CS-022: overall_confidence == mean of surviving conclusions
        if conclusions:
            expected = round(sum(c["confidence"] for c in conclusions) / len(conclusions), 6)
        else:
            expected = 0.0
        if abs(data.get("overall_confidence", 0.0) - expected) > 1e-9:
            errs.append("CS-022: overall_confidence mismatch")

        return errs

    # -- RuntimeAdapter protocol (consensus layer) ---------------------------

    def build_consensus(self, evidence_json: str, config_json: str) -> str:
        """RuntimeAdapter entry point: ``Evidence[] + Config -> Report`` JSON.

        Mirrors the Reference Runtime adapter contract so this adapter can
        participate in a future composite production ``RuntimeAdapter``.
        """
        evidence = json.loads(evidence_json)
        config = json.loads(config_json)
        report = ConsensusEngine().build(
            ConsensusInput(evidence=evidence, config=config)
        )
        return _canonical_json(report.model_dump(mode="json"))

    # -- 规范向量 ------------------------------------------------------------

    def validate_vector(self, vector: dict) -> tuple[list[str], list[str]]:
        """单条规范向量: 运行时复算结果须与冻结 expected_output 逐字节一致。"""
        errs: list[str] = []
        warns: list[str] = []
        vid = vector.get("vector_id", "?")

        for field in ("vector_id", "layer", "name", "input", "expected_output"):
            if field not in vector:
                errs.append(f"{vid}: missing field {field}")
        if errs:
            return errs, warns

        if vector.get("layer") != "consensus":
            warns.append(f"{vid}: layer != consensus")

        inp = vector["input"]
        errs.extend(f"{vid}: {e}" for e in self.validate_input(inp))
        if errs:
            return errs, warns

        try:
            produced = ConsensusEngine().build(ConsensusInput.model_validate(inp))
        except Exception as exc:
            errs.append(f"{vid}: runtime error: {exc}")
            return errs, warns

        actual = produced.model_dump(mode="json")
        expected = vector["expected_output"]
        if _canonical_json(actual) != _canonical_json(expected):
            errs.append(f"{vid}: runtime output != frozen expected_output")

        errs.extend(f"{vid}: {e}" for e in self.validate_output(actual))
        return errs, warns

    def validate_golden_vectors(self) -> dict[str, Any]:
        """全部规范向量校验。"""
        report: dict[str, Any] = {"total": 0, "ok": 0, "errors": {}, "warnings": {}}
        for vector in self.load_vectors():
            errs, warns = self.validate_vector(vector)
            report["total"] += 1
            if errs:
                report["errors"][vector.get("vector_id", "?")] = errs
            else:
                report["ok"] += 1
            if warns:
                report["warnings"][vector.get("vector_id", "?")] = warns
        return report

    # -- 汇总 ----------------------------------------------------------------

    def validate_all(self) -> dict[str, Any]:
        """所有可机器检查项汇总。"""
        vectors = self.validate_golden_vectors()
        return {
            "manifest": self.validate_manifest(),
            "contract_alignment": self.validate_contract_alignment(),
            "runtime_alignment": self.validate_runtime_alignment(),
            "vectors": vectors,
        }


def load_manifest() -> dict[str, Any]:
    return ConsensusContractAdapter().load_manifest()


def validate_vectors() -> dict[str, Any]:
    return ConsensusContractAdapter().validate_golden_vectors()
