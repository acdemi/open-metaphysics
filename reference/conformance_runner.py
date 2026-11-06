"""Reference Conformance Runner -- Phase 6B Sprint 5.5.

Generates golden vectors from the Reference Runtime and runs
conformance checks against any RuntimeAdapter implementation.

Golden vectors are auto-discovered -- no manual maintenance.

H11/H12 (2026-10-31): the runner is **read-only** -- it never generates or
rewrites the frozen golden vectors during ``ConformanceRunner.run()``
(``build_golden_vectors()`` compares in memory; only the explicit
``generate_golden_vectors()`` tooling entry point writes). Each check carries an
explicit ``status``: ``passed``/``failed`` are real checks, while ``partial``
and ``skipped`` are reported honestly and never counted as passes. ``certified``
therefore requires a full-strength pass; a run with partial/skipped checks is
reported as ``contract_conformant`` only. See
``docs/governance/REFERENCE_FREEZE_REVIEW.md`` §2.1.

See: docs/specification/CONFORMANCE_SPEC.md
     docs/specification/IMPLEMENTATION_GUIDE.md
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from pathlib import Path
from typing import Any

from .conformance import (
    CheckStatus,
    ConformanceCategory,
    ConformanceCheckResult,
    ConformanceLayer,
    ConformanceManifest,
    ConformanceResult,
    GoldenVector,
    RuntimeAdapter,
)

GOLDEN_DIR = Path(__file__).parent / "conformance" / "golden"
CONTRACTS_DIR = Path(__file__).parent / "contracts"
SPEC_DIR = Path(__file__).parent.parent / "docs" / "specification"

# Phase 7.4 (ACP-REF-001 Option A) -- CF-015 required behavior-contract IDs.
# CF-015 ("Behavior Contract Coverage") enumerates exactly these IDs and states
# that each MUST be represented and that missing coverage MUST fail conformance.
# Before Phase 7.4 the runner hardcoded 17 of them and asserted ``passed=True``
# without verifying anything; the list below is the specification's full set.
REQUIRED_BEHAVIOR_IDS: tuple[str, ...] = (
    "BC-RE-001",
    "BC-DNF-001",
    "BC-PM-001",
    "BC-EV-001",
    "BC-JSON-001",
    "BC-DET-001",
    "BC-EDGE-001",
    *(f"KB-{i:03d}" for i in range(1, 21)),
    *(f"CS-{i:03d}" for i in range(1, 26)),
)


# == Reference Adapter (wraps existing Reference Runtime) ==


class ReferenceAdapter:
    """Adapter that wraps the Reference Runtime Python implementation.

    Used for self-testing: the Reference Runtime must pass its own
    conformance suite.
    """

    def evaluate_rule(self, rule_yaml: str, chart_data: dict) -> str:
        from .engine import RuleEngine
        from .parser import parse_rule_document

        rules = parse_rule_document(rule_yaml)
        engine = RuleEngine()
        evals = engine.evaluate_all(rules, chart_data)
        return _canonical_json([e.model_dump(mode="json") for e in evals])

    def match_pattern(self, pattern_yaml: str, evaluations_json: str, system: str) -> str:
        from .models import RuleEvaluation
        from .pattern_matcher import PatternMatcher
        from .patterns import parse_pattern_document

        pattern = parse_pattern_document(pattern_yaml)
        evals = [RuleEvaluation(**e) for e in json.loads(evaluations_json)]
        matcher = PatternMatcher()
        pm = matcher.match(pattern, evals, system)
        if pm is None:
            return "null"
        return _canonical_json(pm.model_dump(mode="json"))

    def match_pattern_cross_system(self, pattern_yaml: str, evaluations_by_system_json: str) -> str:
        from .models import RuleEvaluation
        from .pattern_matcher import PatternMatcher
        from .patterns import parse_pattern_document

        pattern = parse_pattern_document(pattern_yaml)
        raw = json.loads(evaluations_by_system_json)
        evals_by_system = {k: [RuleEvaluation(**e) for e in v] for k, v in raw.items()}
        matcher = PatternMatcher()
        pm = matcher.match_cross_system(pattern, evals_by_system)
        if pm is None:
            return "null"
        return _canonical_json(pm.model_dump(mode="json"))

    def build_evidence(self, evaluations_json: str, matches_json: str, system: str) -> str:
        from .evidence_builder import EvidenceBuilder
        from .models import RuleEvaluation
        from .patterns import PatternMatch

        evals = [RuleEvaluation(**e) for e in json.loads(evaluations_json)]
        matches_raw = json.loads(matches_json) if matches_json not in ("null", "[]") else []
        matches = [PatternMatch(**m) for m in matches_raw] if matches_raw else []
        builder = EvidenceBuilder()
        evidence = builder.build_all(evals, matches, system)
        return _canonical_json([e.model_dump(mode="json") for e in evidence])

    def query_knowledge(self, query_json: str, store_json: str) -> str:
        from .knowledge import KnowledgeNode, KnowledgeReference, KnowledgeRelation
        from .knowledge_query import KnowledgeQuery, KnowledgeStore

        q = KnowledgeQuery(**json.loads(query_json))
        store_data = json.loads(store_json)
        store = KnowledgeStore(
            nodes=[KnowledgeNode(**n) for n in store_data.get("nodes", [])],
            relations=[KnowledgeRelation(**r) for r in store_data.get("relations", [])],
            references=[KnowledgeReference(**r) for r in store_data.get("references", [])],
        )
        result = store.execute(q)
        return _canonical_json(result.model_dump(mode="json"))

    def build_consensus(self, evidence_json: str, config_json: str) -> str:
        from .consensus import ConsensusConfig, ConsensusInput
        from .consensus_builder import ConsensusBuilder
        from .evidence import Evidence

        evidence = [Evidence(**e) for e in json.loads(evidence_json)]
        config = ConsensusConfig(**json.loads(config_json))
        builder = ConsensusBuilder()
        report = builder.build(ConsensusInput(evidence=evidence, config=config))
        return _canonical_json(report.model_dump(mode="json"))


# == Golden Vector Generation ==


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def _content_hash(*parts: str) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def build_golden_vectors() -> list[GoldenVector]:
    """Generate golden vectors **in memory** from the Reference Runtime.

    Read-only: the conformance runner calls this to compare against the
    committed vectors and never writes them (H11). Use
    ``generate_golden_vectors()`` from an explicit tooling step when a new
    golden vector set must intentionally be written.
    """
    from .consensus import ConsensusConfig, ConsensusStrategy
    from .engine import RuleEngine
    from .evidence_builder import EvidenceBuilder
    from .knowledge_query import load_knowledge_store
    from .parser import parse_rule_file
    from .pattern_matcher import PatternMatcher
    from .patterns import parse_pattern_file

    examples = Path(__file__).parent / "examples"
    pat_dir = examples / "patterns"
    engine = RuleEngine()
    matcher = PatternMatcher()
    ev_builder = EvidenceBuilder()
    adapter = ReferenceAdapter()

    vectors: list[GoldenVector] = []
    chart_seal = {
        "ten_gods_map": {"values": ["伤官", "正印", "比肩"]},
        "day_master_strength": 0.35,
        "shen_sha_list": ["羊刃", "天乙贵人"],
    }
    chart_qimen = {"dun_type": "yang", "ju": 6}

    # -- Rule vectors --
    for yf in sorted((examples).glob("0[1-6]_*.yaml")):
        yaml_text = yf.read_text(encoding="utf-8")
        chart = chart_qimen if "scope" in yf.name else chart_seal
        output = json.loads(adapter.evaluate_rule(yaml_text, chart))
        vectors.append(
            GoldenVector(
                vector_id=f"gv:rule:{_content_hash(yf.name)}",
                layer=ConformanceLayer.RULE,
                name=yf.stem,
                input={"rule_yaml": yaml_text, "chart_data": chart},
                expected_output=output,
            )
        )

    # -- Pattern vectors --
    for yf in sorted(pat_dir.glob("*.yaml")):
        yaml_text = yf.read_text(encoding="utf-8")
        if "cross" in yf.name:
            be = engine.evaluate_all(
                parse_rule_file(str(examples / "01_single_condition.yaml")), chart_seal
            )
            qe = engine.evaluate_all(parse_rule_file(str(examples / "05_scope.yaml")), chart_qimen)
            evs_by_sys = {
                "bazi": [e.model_dump(mode="json") for e in be],
                "qimen": [e.model_dump(mode="json") for e in qe],
            }
            pm = matcher.match_cross_system(parse_pattern_file(str(yf)), {"bazi": be, "qimen": qe})
            output = None if pm is None else pm.model_dump(mode="json")
            vectors.append(
                GoldenVector(
                    vector_id=f"gv:pattern:{_content_hash(yf.name)}",
                    layer=ConformanceLayer.PATTERN,
                    name=yf.stem,
                    input={"pattern_yaml": yaml_text, "evaluations_by_system": evs_by_sys},
                    expected_output=output,
                )
            )
        else:
            be = engine.evaluate_all(
                parse_rule_file(str(examples / "01_single_condition.yaml")), chart_seal
            )
            evs_list = [e.model_dump(mode="json") for e in be]
            pm = matcher.match(parse_pattern_file(str(yf)), be, "bazi")
            output = None if pm is None else pm.model_dump(mode="json")
            vectors.append(
                GoldenVector(
                    vector_id=f"gv:pattern:{_content_hash(yf.name)}",
                    layer=ConformanceLayer.PATTERN,
                    name=yf.stem,
                    input={"pattern_yaml": yaml_text, "evaluations": evs_list, "system": "bazi"},
                    expected_output=output,
                )
            )

    # -- Evidence vector --
    rules = parse_rule_file(str(examples / "01_single_condition.yaml"))
    evals = engine.evaluate_all(rules, chart_seal)
    pat1 = parse_pattern_file(str(pat_dir / "01_single_rule.yaml"))
    pm1 = matcher.match(pat1, evals, "bazi")
    ev_out = json.loads(
        adapter.build_evidence(
            _canonical_json([e.model_dump(mode="json") for e in evals]),
            _canonical_json([pm1.model_dump(mode="json")]) if pm1 else _canonical_json([]),
            "bazi",
        )
    )
    vectors.append(
        GoldenVector(
            vector_id="gv:evidence:001",
            layer=ConformanceLayer.EVIDENCE,
            name="single_rule_evidence",
            input={
                "evaluations": [e.model_dump(mode="json") for e in evals],
                "matches": [pm1.model_dump(mode="json")] if pm1 else [],
                "system": "bazi",
            },
            expected_output=ev_out,
        )
    )

    # -- Knowledge vectors --
    kn_dir = examples / "knowledge"
    store = load_knowledge_store(
        nodes_path=kn_dir / "nodes.yaml",
        relations_path=kn_dir / "relations.yaml",
        references_path=kn_dir / "references.yaml",
    )
    store_data = {
        "nodes": [n.model_dump(mode="json") for n in store.all_nodes()],
        "relations": [r.model_dump(mode="json") for r in store.all_relations()],
        "references": [r.model_dump(mode="json") for r in store.all_references()],
    }
    for qt, params in [
        ("find_by_id", {"node_id": "kn:wuxing:mu"}),
        ("find_by_type", {"node_type": "wuxing"}),
        ("find_by_system", {"system": "bazi"}),
        ("find_by_tag", {"tag": "yang"}),
    ]:
        from .knowledge_query import KnowledgeQuery, KnowledgeQueryType

        q = KnowledgeQuery(query_type=KnowledgeQueryType(qt), **params)
        qj = q.model_dump(mode="json")
        result = json.loads(
            adapter.query_knowledge(_canonical_json(qj), _canonical_json(store_data))
        )
        vectors.append(
            GoldenVector(
                vector_id=f"gv:knowledge:{_content_hash(qt)}",
                layer=ConformanceLayer.KNOWLEDGE,
                name=f"knowledge_{qt}",
                input={"query": qj, "store": store_data},
                expected_output=result,
            )
        )

    # -- Consensus vectors --
    all_ev = ev_builder.build_all(evals, [pm1] if pm1 else [], "bazi")
    ev_json = _canonical_json([e.model_dump(mode="json") for e in all_ev])
    for strat in ConsensusStrategy:
        cfg = ConsensusConfig(strategy=strat)
        cfg_json = _canonical_json(cfg.model_dump(mode="json"))
        report = json.loads(adapter.build_consensus(ev_json, cfg_json))
        vectors.append(
            GoldenVector(
                vector_id=f"gv:consensus:{_content_hash(strat.value)}",
                layer=ConformanceLayer.CONSENSUS,
                name=f"consensus_{strat.value}",
                input={
                    "evidence": [e.model_dump(mode="json") for e in all_ev],
                    "config": cfg.model_dump(mode="json"),
                },
                expected_output=report,
            )
        )

    return vectors


def serialize_golden_vectors(vectors: list[GoldenVector]) -> dict[str, str]:
    """Layer file name -> canonical LF text (no filesystem access, H11)."""
    by_layer: dict[str, list[dict]] = {}
    for vector in vectors:
        by_layer.setdefault(vector.layer.value, []).append(vector.model_dump(mode="json"))
    serialized: dict[str, str] = {}
    for layer, vecs in by_layer.items():
        text = json.dumps(vecs, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        serialized[f"{layer}_vectors.json"] = text
    return serialized


def generate_golden_vectors(output_dir: Path | None = None) -> list[GoldenVector]:
    """Explicit write path for tooling only.

    The conformance runner is read-only (H11) and must never call this: it uses
    ``build_golden_vectors()`` + ``serialize_golden_vectors()`` to compare
    against the committed files in memory.
    """
    if output_dir is None:
        output_dir = GOLDEN_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    vectors = build_golden_vectors()
    for name, text in serialize_golden_vectors(vectors).items():
        (output_dir / name).write_text(text, encoding="utf-8", newline="\n")
    return vectors


def load_golden_vectors(directory: Path | None = None) -> list[GoldenVector]:
    """Load all golden vectors from the golden directory."""
    if directory is None:
        directory = GOLDEN_DIR
    vectors: list[GoldenVector] = []
    for f in sorted(directory.glob("*_vectors.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for v in data:
            vectors.append(GoldenVector(**v))
    return vectors


# == Conformance Runner ==


class ConformanceRunner:
    """Runs conformance checks against a RuntimeAdapter.

    Auto-discovers golden vectors. No manual maintenance.
    """

    CONTRACT_VERSION = "1.0.0"
    BEHAVIOR_VERSION = "1.0.0"

    def __init__(self, golden_dir: Path | None = None):
        self._golden_dir = golden_dir or GOLDEN_DIR

    def run(
        self, adapter: RuntimeAdapter, runtime_name: str = "unknown", runtime_version: str = "0.0.0"
    ) -> ConformanceResult:
        result = ConformanceResult(
            runtime_name=runtime_name,
            runtime_version=runtime_version,
            contract_version=self.CONTRACT_VERSION,
            behavior_version=self.BEHAVIOR_VERSION,
        )

        vectors = load_golden_vectors(self._golden_dir)
        if vectors:
            for vector in vectors:
                self._check_vector(adapter, vector, result)
        else:
            result.add_check(
                ConformanceCheckResult(
                    check_id="CF-GOLDEN-MISSING",
                    category=ConformanceCategory.GOLDEN_JSON,
                    name="golden_vectors_present",
                    passed=False,
                    status=CheckStatus.FAILED,
                    message=(
                        "No golden vectors on disk. The conformance runner is "
                        "read-only (H11) and will not generate or rewrite them; "
                        "run generate_golden_vectors() in a dedicated tooling step."
                    ),
                )
            )

        self._check_contract_diff(result)
        self._check_behavior_coverage(result)
        self._check_architecture_boundary(adapter, result)
        self._check_behavior_immunity(result)
        self._check_golden_auto_discovery(result)
        self._check_golden_reproducibility(result)
        self._check_layer_coverage(result)

        return result

    def _check_vector(
        self, adapter: RuntimeAdapter, vector: GoldenVector, result: ConformanceResult
    ) -> None:
        vid = vector.vector_id
        layer = vector.layer

        try:
            actual = self._run_adapter(adapter, vector)
            expected = _canonical_json(vector.expected_output)
            passed = actual == expected
            result.add_check(
                ConformanceCheckResult(
                    check_id=f"CF-GOLDEN-{vid}",
                    category=ConformanceCategory.GOLDEN_JSON,
                    layer=layer,
                    name=vector.name,
                    passed=passed,
                    message="Output matches golden vector" if passed else "Output mismatch",
                )
            )

            if passed:
                self._check_deterministic(adapter, vector, result)
                self._check_ordering(vector, result)
                self._check_hash(vector, result)
                self._check_null(vector, result)
                self._check_enum(actual, vector, result)
        except Exception as exc:
            result.add_check(
                ConformanceCheckResult(
                    check_id=f"CF-GOLDEN-{vid}",
                    category=ConformanceCategory.GOLDEN_JSON,
                    layer=layer,
                    name=vector.name,
                    passed=False,
                    message=str(exc),
                )
            )

    def _run_adapter(self, adapter: RuntimeAdapter, vector: GoldenVector) -> str:
        inp = vector.input
        if vector.layer == ConformanceLayer.RULE:
            return adapter.evaluate_rule(inp["rule_yaml"], inp["chart_data"])
        if vector.layer == ConformanceLayer.PATTERN:
            if "evaluations_by_system" in inp:
                return adapter.match_pattern_cross_system(
                    inp["pattern_yaml"], _canonical_json(inp["evaluations_by_system"])
                )
            evals_json = _canonical_json(inp.get("evaluations", []))
            return adapter.match_pattern(inp["pattern_yaml"], evals_json, inp.get("system", "bazi"))
        if vector.layer == ConformanceLayer.EVIDENCE:
            return adapter.build_evidence(
                _canonical_json(inp["evaluations"]),
                _canonical_json(inp.get("matches", [])),
                inp.get("system", "bazi"),
            )
        if vector.layer == ConformanceLayer.KNOWLEDGE:
            return adapter.query_knowledge(
                _canonical_json(inp["query"]), _canonical_json(inp["store"])
            )
        if vector.layer == ConformanceLayer.CONSENSUS:
            return adapter.build_consensus(
                _canonical_json(inp["evidence"]), _canonical_json(inp["config"])
            )
        raise ValueError(f"Unknown layer: {vector.layer}")

    def _check_deterministic(
        self, adapter: RuntimeAdapter, vector: GoldenVector, result: ConformanceResult
    ) -> None:
        try:
            a1 = self._run_adapter(adapter, vector)
            a2 = self._run_adapter(adapter, vector)
            passed = a1 == a2
            result.add_check(
                ConformanceCheckResult(
                    check_id=f"CF-DET-{vector.vector_id}",
                    category=ConformanceCategory.DETERMINISTIC_OUTPUT,
                    layer=vector.layer,
                    name=f"det:{vector.name}",
                    passed=passed,
                    message="Deterministic" if passed else "Non-deterministic",
                )
            )
        except Exception as exc:
            result.add_check(
                ConformanceCheckResult(
                    check_id=f"CF-DET-{vector.vector_id}",
                    category=ConformanceCategory.DETERMINISTIC_OUTPUT,
                    layer=vector.layer,
                    name=f"det:{vector.name}",
                    passed=False,
                    message=str(exc),
                )
            )

    def _check_ordering(self, vector: GoldenVector, result: ConformanceResult) -> None:
        """CF-010 ordering: not independently verified (H11).

        An independent ordering check needs a second implementation or an
        ordering oracle; the golden equality already covers the committed
        order, so this is reported as ``skipped`` instead of a fake pass.
        """
        result.add_check(
            ConformanceCheckResult(
                check_id=f"CF-SORT-{vector.vector_id}",
                category=ConformanceCategory.STABLE_ORDERING,
                layer=vector.layer,
                name=f"sort:{vector.name}",
                passed=False,
                status=CheckStatus.SKIPPED,
                message=(
                    "Not independently re-verified: no second implementation / "
                    "ordering oracle. Golden equality covers only the committed "
                    "vector order (H11)."
                ),
            )
        )

    def _check_hash(self, vector: GoldenVector, result: ConformanceResult) -> None:
        """CF-011 deterministic hash: not independently verified (H11)."""
        result.add_check(
            ConformanceCheckResult(
                check_id=f"CF-HASH-{vector.vector_id}",
                category=ConformanceCategory.DETERMINISTIC_HASH,
                layer=vector.layer,
                name=f"hash:{vector.name}",
                passed=False,
                status=CheckStatus.SKIPPED,
                message=(
                    "Not independently re-verified: hashing the adapter output "
                    "against itself is not a second implementation. Golden "
                    "equality only (H11)."
                ),
            )
        )

    def _check_null(self, vector: GoldenVector, result: ConformanceResult) -> None:
        """CF-012 null handling: not independently verified (H11)."""
        result.add_check(
            ConformanceCheckResult(
                check_id=f"CF-NULL-{vector.vector_id}",
                category=ConformanceCategory.NULL_HANDLING,
                layer=vector.layer,
                name=f"null:{vector.name}",
                passed=False,
                status=CheckStatus.SKIPPED,
                message=(
                    "Not independently re-verified: null paths are covered by the "
                    "golden equality; no independent null oracle exists (H11)."
                ),
            )
        )

    #: Enum-valued JSON fields checked by ``_check_enum`` (independent of the
    #: golden expected output: it validates the *serialized shape* against the
    #: Reference enums).
    _ENUM_FIELDS: dict[str, tuple[str, ...]] = {
        "node_type": (
            "wuxing",
            "ten_god",
            "heavenly_stem",
            "earthly_branch",
            "palace",
            "main_star",
            "auxiliary_star",
            "shen_sha",
            "pattern",
            "career",
            "personality",
            "marriage",
            "health",
            "wealth",
            "annual_fortune",
            "major_luck",
            "yong_shen",
            "xi_shen",
            "ji_shen",
            "tiao_hou",
        ),
        "relation_type": (
            "sheng",
            "ke",
            "chong",
            "xing",
            "he",
            "hai",
            "fuzhu",
            "zhiyue",
            "duiying",
            "yingxiang",
            "zengqiang",
            "xueroo",
            "zhixiang",
            "shuyu",
            "yinyong",
        ),
        "ref_type": (
            "classic_text",
            "school_commentary",
            "modern_interpretation",
            "oral_tradition",
        ),
        "target_type": ("node", "relation"),
        "strategy": ("retain_all", "highest_confidence", "majority"),
        "evidence_type": ("rule", "pattern", "knowledge_node", "relation"),
        "operator": (
            "equals",
            "not_equals",
            "contains",
            "not_contains",
            "in",
            "not_in",
            "greater_than",
            "less_than",
            "exists",
            "not_exists",
            "matches",
        ),
    }

    def _check_enum(self, actual: str, vector: GoldenVector, result: ConformanceResult) -> None:
        """CF-013 enum serialization: real property check on the adapter output.

        Walks the adapter JSON and asserts every known enum-valued field is a
        *string* whose value is one of the Reference enum members. This is
        independent of ``expected_output`` (it does not compare values to the
        golden vector), so it is a genuine check; if the vector contains no
        enum-valued field the result is ``partial`` rather than passed.
        """
        try:
            parsed = json.loads(actual)
        except (TypeError, json.JSONDecodeError) as exc:
            result.add_check(
                ConformanceCheckResult(
                    check_id=f"CF-ENUM-{vector.vector_id}",
                    category=ConformanceCategory.ENUM_SERIALIZATION,
                    layer=vector.layer,
                    name=f"enum:{vector.name}",
                    passed=False,
                    status=CheckStatus.FAILED,
                    message=f"adapter output is not valid JSON: {exc}",
                )
            )
            return

        checked = 0
        violations: list[str] = []

        def walk(node: Any, path: str) -> None:
            nonlocal checked
            if isinstance(node, dict):
                for key, value in node.items():
                    child = f"{path}.{key}" if path else key
                    if key in self._ENUM_FIELDS:
                        if value is None:
                            # nullable enum fields serialise as JSON null; that is
                            # valid and is covered by the golden equality.
                            continue
                        if not isinstance(value, str) or value not in self._ENUM_FIELDS[key]:
                            violations.append(f"{child}={value!r}")
                        else:
                            checked += 1
                    walk(value, child)
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{path}[{index}]")

        walk(parsed, "")
        if violations:
            result.add_check(
                ConformanceCheckResult(
                    check_id=f"CF-ENUM-{vector.vector_id}",
                    category=ConformanceCategory.ENUM_SERIALIZATION,
                    layer=vector.layer,
                    name=f"enum:{vector.name}",
                    passed=False,
                    status=CheckStatus.FAILED,
                    message=f"enum fields not serialized as declared strings: {violations[:5]}",
                )
            )
            return
        if checked == 0:
            result.add_check(
                ConformanceCheckResult(
                    check_id=f"CF-ENUM-{vector.vector_id}",
                    category=ConformanceCategory.ENUM_SERIALIZATION,
                    layer=vector.layer,
                    name=f"enum:{vector.name}",
                    passed=False,
                    status=CheckStatus.PARTIAL,
                    message="No known enum-valued field in this vector's output; nothing to verify.",
                )
            )
            return
        result.add_check(
            ConformanceCheckResult(
                check_id=f"CF-ENUM-{vector.vector_id}",
                category=ConformanceCategory.ENUM_SERIALIZATION,
                layer=vector.layer,
                name=f"enum:{vector.name}",
                passed=True,
                status=CheckStatus.PASSED,
                message=f"Validated {checked} enum-valued field(s) as declared string enums.",
            )
        )

    def _check_contract_diff(self, result: ConformanceResult) -> None:
        """CF-013: contract files must match the Reference models (real diff).

        H11: previous implementation only checked that two keys existed. It now
        validates required top-level keys, the contract version, non-empty
        golden examples, and — for every declared model — that its ``required``
        and ``field_types`` fields actually exist on the corresponding Reference
        pydantic model (unresolved models are failures, not silent passes).
        """
        for cf in sorted(CONTRACTS_DIR.glob("*.json")):
            problems: list[str] = []
            try:
                contract = json.loads(cf.read_text(encoding="utf-8"))
                for key in ("contract_name", "contract_version", "golden_examples", "models"):
                    if key not in contract:
                        problems.append(f"missing top-level key {key}")
                if contract.get("contract_version") != self.CONTRACT_VERSION:
                    problems.append(
                        f"contract_version {contract.get('contract_version')!r} "
                        f"!= suite {self.CONTRACT_VERSION!r}"
                    )
                examples = contract.get("golden_examples")
                if not isinstance(examples, list) or not examples:
                    problems.append("golden_examples must be a non-empty list")
                models = contract.get("models")
                if not isinstance(models, dict) or not models:
                    problems.append("models must be a non-empty object")
                else:
                    for model_name, spec in models.items():
                        model = _resolve_reference_model(model_name)
                        if model is None:
                            problems.append(f"model {model_name!r} has no Reference model")
                            continue
                        fields = set(model.model_fields)
                        required = set(spec.get("required") or [])
                        if not required:
                            problems.append(f"model {model_name!r}: empty required list")
                        missing_required = sorted(required - fields)
                        if missing_required:
                            problems.append(
                                f"model {model_name!r}: required fields missing on "
                                f"Reference model: {missing_required}"
                            )
                        field_types = set(spec.get("field_types") or {})
                        unknown_types = sorted(field_types - fields)
                        if unknown_types:
                            problems.append(
                                f"model {model_name!r}: field_types declare unknown fields: "
                                f"{unknown_types}"
                            )
            except Exception as exc:
                problems.append(f"unreadable contract: {exc}")

            passed = not problems
            result.add_check(
                ConformanceCheckResult(
                    check_id=f"CF-CONTRACT-{cf.stem}",
                    category=ConformanceCategory.CONTRACT_DIFF,
                    name=cf.stem,
                    passed=passed,
                    status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                    message=(
                        "Contract models/required fields match the Reference models"
                        if passed
                        else "; ".join(problems)
                    ),
                )
            )

    def _behavior_representation(self, result: ConformanceResult) -> dict[str, tuple[bool, str]]:
        """Resolve every CF-015 required ID to an EXECUTED representation.

        Phase 7.4 (ACP-REF-001 Option A). Returns ``{behavior_id: (passed, basis)}``.

        Representations, by contract family:

        * ``KB-001`` ~ ``KB-020``: executed ``KnowledgeBehavior.audit()``
          verifiers (one per contract).
        * ``CS-001`` ~ ``CS-025``: executed ``ConsensusBehavior.audit()``
          verifiers (one per contract).
        * ``BC-*``: the Rule/Pattern/Evidence layer checks and the
          JSON/determinism check families that the golden vectors actually
          exercise, plus a live edge-case probe for ``BC-EDGE-001``.

        An ID absent from the returned mapping has **no representation** and is
        therefore reported as uncovered -- which, per CF-015, fails conformance.
        """
        rep: dict[str, tuple[bool, str]] = {}

        def real_checks_ok(checks: list[ConformanceCheckResult]) -> bool:
            """Only real checks count; skipped/partial checks cannot vouch for a layer."""
            real = [c for c in checks if c.status in (CheckStatus.PASSED, CheckStatus.FAILED)]
            return bool(real) and all(c.status == CheckStatus.PASSED for c in real)

        def layer_ok(layer: ConformanceLayer) -> bool:
            return real_checks_ok([c for c in result.checks if c.layer == layer])

        def category_ok(category: ConformanceCategory) -> bool:
            return real_checks_ok([c for c in result.checks if c.category == category])

        # -- BC-* : rule/pattern/evidence behaviors exercised by the vectors --
        rep["BC-RE-001"] = (layer_ok(ConformanceLayer.RULE), "executed rule-layer golden checks")
        rep["BC-DNF-001"] = (layer_ok(ConformanceLayer.RULE), "executed rule-layer golden checks")
        rep["BC-PM-001"] = (
            layer_ok(ConformanceLayer.PATTERN),
            "executed pattern-layer golden checks",
        )
        rep["BC-EV-001"] = (
            layer_ok(ConformanceLayer.EVIDENCE),
            "executed evidence-layer golden checks",
        )
        rep["BC-JSON-001"] = (
            category_ok(ConformanceCategory.GOLDEN_JSON),
            "canonical-JSON golden comparison",
        )
        rep["BC-DET-001"] = (
            category_ok(ConformanceCategory.DETERMINISTIC_OUTPUT),
            "re-executed determinism checks",
        )
        try:
            from .engine import field_exists

            rep["BC-EDGE-001"] = (
                field_exists({}, "missing.path") is False
                and field_exists({"a": {"b": 1}}, "a.b") is True,
                "live missing-field probe",
            )
        except Exception as exc:  # pragma: no cover - defensive
            rep["BC-EDGE-001"] = (False, f"probe failed: {exc}")

        # -- KB-001 ~ KB-020 : executed knowledge behavior verifiers --
        try:
            from .knowledge_behavior import KnowledgeBehavior
            from .knowledge_query import load_knowledge_store

            kn_dir = Path(__file__).parent / "examples" / "knowledge"
            store = load_knowledge_store(
                nodes_path=kn_dir / "nodes.yaml",
                relations_path=kn_dir / "relations.yaml",
                references_path=kn_dir / "references.yaml",
            )
            kb = KnowledgeBehavior.audit(store)
            for bid, passed in kb.items():
                if bid.startswith("KB-"):
                    rep[bid] = (bool(passed), "KnowledgeBehavior.audit()")
        except Exception as exc:  # pragma: no cover - defensive
            for i in range(1, 21):
                rep.setdefault(f"KB-{i:03d}", (False, f"audit unavailable: {exc}"))

        # -- CS-001 ~ CS-025 : executed consensus behavior verifiers --
        try:
            from .consensus_behavior import ConsensusBehavior
            from .consensus_builder import ConsensusBuilder

            cs = ConsensusBehavior.audit(ConsensusBuilder())
            for bid, passed in cs.items():
                if bid.startswith("CS-"):
                    rep[bid] = (bool(passed), "ConsensusBehavior.audit()")
        except Exception as exc:  # pragma: no cover - defensive
            for i in range(1, 26):
                rep.setdefault(f"CS-{i:03d}", (False, f"audit unavailable: {exc}"))

        return rep

    def _check_behavior_coverage(self, result: ConformanceResult) -> None:
        """CF-015: every required behavior contract MUST be represented.

        Phase 7.4 (ACP-REF-001 Option A): this used to hardcode 17 IDs and add
        each with ``passed=True`` without verifying anything. It now resolves
        every required ID through ``_behavior_representation`` and reports the
        truth, including failing the IDs that have no executed representation.
        """
        rep = self._behavior_representation(result)

        unrepresented: list[str] = []
        represented = 0
        for bid in REQUIRED_BEHAVIOR_IDS:
            entry = rep.get(bid)
            if entry is None:
                unrepresented.append(bid)
                result.add_check(
                    ConformanceCheckResult(
                        check_id=f"CF-BEHAV-{bid}",
                        category=ConformanceCategory.BEHAVIOR_COVERAGE,
                        name=bid,
                        passed=False,
                        message="No executed representation for this behavior contract "
                        "(CF-015 requires coverage; missing coverage MUST fail)",
                    )
                )
                continue
            passed, basis = entry
            if passed:
                represented += 1
            else:
                unrepresented.append(bid)
            result.add_check(
                ConformanceCheckResult(
                    check_id=f"CF-BEHAV-{bid}",
                    category=ConformanceCategory.BEHAVIOR_COVERAGE,
                    name=bid,
                    passed=passed,
                    message=f"Represented by: {basis}"
                    if passed
                    else f"Representation failed: {basis}",
                )
            )

        total = len(REQUIRED_BEHAVIOR_IDS)
        result.behavior_coverage = represented / total if total else 0.0
        result.unrepresented_behaviors = unrepresented

    def _check_architecture_boundary(
        self, adapter: RuntimeAdapter, result: ConformanceResult
    ) -> None:
        """CF-ARCH-001: adapter must not carry I/O / LLM / DB capabilities.

        H11: the old check only looked for forbidden *methods* on the adapter
        object. It now also scans the adapter's module source for imports of
        network/DB/LLM/production-runtime packages. When the source is not
        available (e.g. C extension adapter) the check is reported ``partial``
        instead of passing on the attribute check alone.
        """
        forbidden_methods = [
            "call_llm",
            "query_database",
            "call_graph_db",
            "embed",
            "rag_search",
            "call_ollama",
        ]
        forbidden_modules = (
            "httpx",
            "requests",
            "urllib",
            "socket",
            "sqlalchemy",
            "psycopg",
            "qdrant_client",
            "openai",
            "anthropic",
            "ollama",
            "langchain",
            "langgraph",
            "openmetaphysics",
        )
        problems: list[str] = [
            f"forbidden method {method!r}"
            for method in forbidden_methods
            if hasattr(adapter, method)
        ]
        status = CheckStatus.PARTIAL
        source_note = "adapter source unavailable; attribute check only"
        try:
            source_path = inspect.getsourcefile(type(adapter))
        except (TypeError, OSError):
            source_path = None
        if source_path:
            try:
                source = Path(source_path).read_text(encoding="utf-8")
            except OSError:
                source = ""
            if source:
                import_hits = [
                    module
                    for module in forbidden_modules
                    if re.search(
                        rf"^\s*(?:import|from)\s+{re.escape(module)}\b", source, re.MULTILINE
                    )
                ]
                problems.extend(f"forbidden import {module!r}" for module in import_hits)
                # The Reference adapter module is allowed to mention the names
                # in its own boundary list; only real import statements count.
                status = CheckStatus.PASSED
                source_note = f"module source scanned: {Path(source_path).name}"
        passed = not problems and status == CheckStatus.PASSED
        result.add_check(
            ConformanceCheckResult(
                check_id="CF-ARCH-001",
                category=ConformanceCategory.ARCHITECTURE_BOUNDARY,
                name="architecture_boundary",
                passed=passed,
                status=(
                    CheckStatus.PASSED
                    if passed
                    else (CheckStatus.FAILED if problems else CheckStatus.PARTIAL)
                ),
                message=(
                    f"No forbidden methods/imports ({source_note})"
                    if not problems
                    else "; ".join(problems) + f" ({source_note})"
                ),
            )
        )

    def _check_behavior_immunity(self, result: ConformanceResult) -> None:
        """CF-016: every required behavior ID is declared by the specifications."""
        pattern = re.compile(r"\b(?:BC-[A-Z]+-\d{3}|KB-\d{3}|CS-\d{3})\b")
        spec_files = [
            SPEC_DIR / "BEHAVIOR_SPEC.md",
            SPEC_DIR / "KNOWLEDGE_BEHAVIOR_SPEC.md",
            SPEC_DIR / "CONSENSUS_BEHAVIOR_SPEC.md",
        ]
        declared: set[str] = set()
        missing_files: list[str] = []
        for path in spec_files:
            if path.exists():
                declared.update(pattern.findall(path.read_text(encoding="utf-8")))
            else:
                missing_files.append(path.name)
        unknown = sorted(set(REQUIRED_BEHAVIOR_IDS) - declared)
        passed = not missing_files and not unknown
        result.add_check(
            ConformanceCheckResult(
                check_id="CF-016",
                category=ConformanceCategory.ARCHITECTURE_BOUNDARY,
                name="behavior_contract_immunity",
                passed=passed,
                message=(
                    "Required behavior IDs are declared by the specifications"
                    if passed
                    else f"missing_files={missing_files} undeclared={unknown}"
                ),
            )
        )

    def _check_golden_auto_discovery(self, result: ConformanceResult) -> None:
        """CF-017: golden vectors are auto-discovered, one file per layer."""
        files = sorted(self._golden_dir.glob("*_vectors.json"))
        layer_files = {f.stem.removesuffix("_vectors") for f in files}
        expected = {layer.value for layer in ConformanceLayer}
        passed = len(files) == len(expected) and layer_files == expected
        result.add_check(
            ConformanceCheckResult(
                check_id="CF-017",
                category=ConformanceCategory.GOLDEN_JSON,
                name="golden_auto_discovery",
                passed=passed,
                message=(
                    f"discovered {len(files)} layer files"
                    if passed
                    else f"expected {sorted(expected)}, found {sorted(layer_files)}"
                ),
            )
        )

    def _check_golden_reproducibility(self, result: ConformanceResult) -> None:
        """CF-018: regenerating golden vectors in memory equals the committed bytes.

        H11: this used to call ``generate_golden_vectors(self._golden_dir)``,
        which **rewrote** the frozen golden files during a conformance run (and
        could silently "repair" a drifted vector). It now generates in memory
        and compares the serialized bytes with the files on disk; nothing is
        written.
        """
        loaded_text: dict[str, str] = {}
        try:
            for path in sorted(self._golden_dir.glob("*_vectors.json")):
                loaded_text[path.name] = path.read_text(encoding="utf-8")
        except OSError as exc:
            result.add_check(
                ConformanceCheckResult(
                    check_id="CF-018",
                    category=ConformanceCategory.GOLDEN_JSON,
                    name="golden_reproducibility",
                    passed=False,
                    status=CheckStatus.FAILED,
                    message=f"cannot read golden files: {exc}",
                )
            )
            return
        fresh_text = serialize_golden_vectors(build_golden_vectors())
        passed = loaded_text == fresh_text
        if passed:
            message = (
                f"regenerated {len(fresh_text)} layer files byte-identical to disk "
                "(read-only; no files written)"
            )
        else:
            missing = sorted(set(fresh_text) - set(loaded_text))
            extra = sorted(set(loaded_text) - set(fresh_text))
            changed = sorted(
                name
                for name in set(fresh_text) & set(loaded_text)
                if fresh_text[name] != loaded_text[name]
            )
            message = (
                "regenerated golden vectors differ from disk "
                f"(missing={missing}, extra={extra}, changed={changed}); "
                "files were NOT rewritten (H11)"
            )
        result.add_check(
            ConformanceCheckResult(
                check_id="CF-018",
                category=ConformanceCategory.GOLDEN_JSON,
                name="golden_reproducibility",
                passed=passed,
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                message=message,
            )
        )

    def _check_layer_coverage(self, result: ConformanceResult) -> None:
        """CF-019: every conformance layer has at least one golden vector."""
        present = {v.layer for v in load_golden_vectors(self._golden_dir)}
        missing = sorted(layer.value for layer in ConformanceLayer if layer not in present)
        passed = not missing
        result.add_check(
            ConformanceCheckResult(
                check_id="CF-019",
                category=ConformanceCategory.GOLDEN_JSON,
                name="layer_coverage",
                passed=passed,
                message="All five layers covered" if passed else f"missing layers: {missing}",
            )
        )


def certify(result: ConformanceResult) -> ConformanceManifest:
    """Produce a ConformanceManifest from a ConformanceResult.

    Only certified (100% pass) runtimes get certified=True.
    """
    contracts: dict[str, str] = {}
    for path in sorted(CONTRACTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        name = data.get("contract_name")
        version = data.get("contract_version")
        if isinstance(name, str) and isinstance(version, str):
            contracts[name] = version
    return ConformanceManifest(
        runtime_name=result.runtime_name,
        runtime_version=result.runtime_version,
        supported_layers=sorted({c.layer.value for c in result.checks if c.layer and c.passed}),
        supported_contracts=contracts,
        supported_behaviors=sorted(
            {
                c.name
                for c in result.checks
                if c.category == ConformanceCategory.BEHAVIOR_COVERAGE and c.passed
            }
        ),
        certified=result.certified,
        contract_conformant=result.contract_conformant,
    )


def _resolve_reference_model(name: str) -> type | None:
    """Resolve a contract model name to its Reference pydantic model class."""
    from . import (
        consensus,
        evidence,
        knowledge,
        knowledge_query,
        models,
        pattern_matcher,
        patterns,
    )

    for module in (
        models,
        knowledge,
        knowledge_query,
        evidence,
        consensus,
        patterns,
        pattern_matcher,
    ):
        candidate = getattr(module, name, None)
        if (
            isinstance(candidate, type)
            and hasattr(candidate, "model_fields")
            and candidate.__module__ == module.__name__
        ):
            return candidate
    return None
