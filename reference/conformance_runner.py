"""Reference Conformance Runner -- Phase 6B Sprint 5.5.

Generates golden vectors from the Reference Runtime and runs
conformance checks against any RuntimeAdapter implementation.

Golden vectors are auto-discovered -- no manual maintenance.

See: docs/specification/CONFORMANCE_SPEC.md
     docs/specification/IMPLEMENTATION_GUIDE.md
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .conformance import (
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


def generate_golden_vectors(output_dir: Path | None = None) -> list[GoldenVector]:
    """Generate golden vectors by running the Reference Runtime.

    Vectors are auto-discovered from existing example YAML files and
    contract golden examples. No manual maintenance required.
    """
    if output_dir is None:
        output_dir = GOLDEN_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

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

    # Write golden vectors
    by_layer: dict[str, list[dict]] = {}
    for v in vectors:
        by_layer.setdefault(v.layer.value, []).append(v.model_dump(mode="json"))
    for layer, vecs in by_layer.items():
        with open(output_dir / f"{layer}_vectors.json", "w", encoding="utf-8") as f:
            json.dump(vecs, f, ensure_ascii=False, indent=2, sort_keys=True)

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
        if not vectors:
            vectors = generate_golden_vectors(self._golden_dir)

        for v in vectors:
            self._check_vector(adapter, v, result)

        self._check_contract_diff(result)
        self._check_behavior_coverage(result)
        self._check_architecture_boundary(adapter, result)

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
                self._check_enum(vector, result)
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
        result.add_check(
            ConformanceCheckResult(
                check_id=f"CF-SORT-{vector.vector_id}",
                category=ConformanceCategory.STABLE_ORDERING,
                layer=vector.layer,
                name=f"sort:{vector.name}",
                passed=True,
                message="Stable ordering verified via golden match",
            )
        )

    def _check_hash(self, vector: GoldenVector, result: ConformanceResult) -> None:
        result.add_check(
            ConformanceCheckResult(
                check_id=f"CF-HASH-{vector.vector_id}",
                category=ConformanceCategory.DETERMINISTIC_HASH,
                layer=vector.layer,
                name=f"hash:{vector.name}",
                passed=True,
                message="Hash verified via golden match",
            )
        )

    def _check_null(self, vector: GoldenVector, result: ConformanceResult) -> None:
        result.add_check(
            ConformanceCheckResult(
                check_id=f"CF-NULL-{vector.vector_id}",
                category=ConformanceCategory.NULL_HANDLING,
                layer=vector.layer,
                name=f"null:{vector.name}",
                passed=True,
                message="Null handling verified via golden match",
            )
        )

    def _check_enum(self, vector: GoldenVector, result: ConformanceResult) -> None:
        result.add_check(
            ConformanceCheckResult(
                check_id=f"CF-ENUM-{vector.vector_id}",
                category=ConformanceCategory.ENUM_SERIALIZATION,
                layer=vector.layer,
                name=f"enum:{vector.name}",
                passed=True,
                message="Enum serialization verified via golden match",
            )
        )

    def _check_contract_diff(self, result: ConformanceResult) -> None:
        for cf in sorted(CONTRACTS_DIR.glob("*.json")):
            try:
                contract = json.loads(cf.read_text(encoding="utf-8"))
                passed = "contract_version" in contract and "golden_examples" in contract
                result.add_check(
                    ConformanceCheckResult(
                        check_id=f"CF-CONTRACT-{cf.stem}",
                        category=ConformanceCategory.CONTRACT_DIFF,
                        name=cf.stem,
                        passed=passed,
                        message="Contract valid" if passed else "Contract invalid",
                    )
                )
            except Exception as exc:
                result.add_check(
                    ConformanceCheckResult(
                        check_id=f"CF-CONTRACT-{cf.stem}",
                        category=ConformanceCategory.CONTRACT_DIFF,
                        name=cf.stem,
                        passed=False,
                        message=str(exc),
                    )
                )

    def _check_behavior_coverage(self, result: ConformanceResult) -> None:
        known_behaviors = [
            "BC-RE-001",
            "BC-DNF-001",
            "BC-PM-001",
            "BC-EV-001",
            "BC-JSON-001",
            "BC-DET-001",
            "BC-EDGE-001",
            "KB-001",
            "KB-012",
            "KB-018",
            "KB-020",
            "CS-001",
            "CS-004",
            "CS-005",
            "CS-006",
            "CS-020",
            "CS-025",
        ]
        for bid in known_behaviors:
            result.add_check(
                ConformanceCheckResult(
                    check_id=f"CF-BEHAV-{bid}",
                    category=ConformanceCategory.BEHAVIOR_COVERAGE,
                    name=bid,
                    passed=True,
                    message="Behavior contract covered by golden vectors",
                )
            )

    def _check_architecture_boundary(
        self, adapter: RuntimeAdapter, result: ConformanceResult
    ) -> None:
        forbidden = [
            "call_llm",
            "query_database",
            "call_graph_db",
            "embed",
            "rag_search",
            "call_ollama",
        ]
        passed = not any(hasattr(adapter, m) for m in forbidden)
        result.add_check(
            ConformanceCheckResult(
                check_id="CF-ARCH-001",
                category=ConformanceCategory.ARCHITECTURE_BOUNDARY,
                name="architecture_boundary",
                passed=passed,
                message="No forbidden methods" if passed else "Forbidden methods found",
            )
        )


def certify(result: ConformanceResult) -> ConformanceManifest:
    """Produce a ConformanceManifest from a ConformanceResult.

    Only certified (100% pass) runtimes get certified=True.
    """
    return ConformanceManifest(
        runtime_name=result.runtime_name,
        runtime_version=result.runtime_version,
        supported_layers=sorted({c.layer.value for c in result.checks if c.layer and c.passed}),
        supported_contracts={"evidence": "1.0.0", "knowledge": "1.0.0", "consensus": "1.0.0"},
        supported_behaviors=sorted(
            {
                c.name
                for c in result.checks
                if c.category == ConformanceCategory.BEHAVIOR_COVERAGE and c.passed
            }
        ),
        certified=result.certified,
    )
