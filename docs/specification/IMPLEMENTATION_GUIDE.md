# Implementation Guide for Production Runtimes

> **Status**: Normative - Binding on all Production Runtime implementations.
> **Audience**: Engineers implementing the open-metaphysics runtime in
> Rust, Go, Python, or WASM.
> **Companion**: `CONFORMANCE_SPEC.md`, `REFERENCE_RUNTIME_SPEC.md`,
> `BEHAVIOR_SPEC.md`, `RUNTIME_CONTRACT.md`

---

## 1. Overview

A **Production Runtime** is any implementation of the open-metaphysics
reasoning pipeline outside the Reference Runtime (`reference/`). To be
considered correct, a Production Runtime **MUST** pass the Conformance
Suite at 100%.

The Conformance Suite works by:

1. Loading **golden vectors** (auto-generated from the Reference Runtime).
2. Feeding each vector input to the Production Runtime adapter.
3. Comparing the adapter output to the vector expected_output.
4. Running additional checks (determinism, contract validity,
   architecture boundary, behavior coverage).
5. Granting **Certified** status if and only if all checks pass.

---

## 2. RuntimeAdapter Protocol

Every Production Runtime **MUST** implement the RuntimeAdapter protocol.
This protocol has **six methods**:

    class RuntimeAdapter(Protocol):
        def evaluate_rule(self, rule_yaml: str, chart_data: dict) -> str: ...
        def match_pattern(self, pattern_yaml: str, evaluations_json: str, system: str) -> str: ...
        def match_pattern_cross_system(self, pattern_yaml: str, evaluations_by_system_json: str) -> str: ...
        def build_evidence(self, evaluations_json: str, matches_json: str, system: str) -> str: ...
        def query_knowledge(self, query_json: str, store_json: str) -> str: ...
        def build_consensus(self, evidence_json: str, config_json: str) -> str: ...

### 2.1 Common Contract

All methods share these invariants:

- **Input**: JSON strings (or dict for chart_data).
- **Output**: A canonical JSON string produced by
  json.dumps(obj, ensure_ascii=False, sort_keys=True).
- **Determinism**: Same input MUST always produce the same output string.
- **No side effects**: Methods MUST NOT mutate global state, call
  networks, or access databases.
- **No LLM**: Methods MUST NOT call any language model.
---

## 3. Method Specifications

### 3.1 evaluate_rule

**Input**: rule_yaml (str) - YAML document with Rule definitions;
chart_data (dict) - chart data to evaluate against.

**Output**: Canonical JSON of a **list** of RuleEvaluation objects.

**Behavior**: Parse YAML into Rule objects, evaluate each Rule against
chart_data, return all evaluations in stable order. An empty rule set
is invalid.

### 3.2 match_pattern

**Input**: pattern_yaml (str); evaluations_json (str) - JSON list of
RuleEvaluation; system (str) - e.g. "bazi", "qimen".

**Output**: If match: canonical JSON of PatternMatch. If no match: the
literal string "null".

### 3.3 match_pattern_cross_system

**Input**: pattern_yaml (str); evaluations_by_system_json (str) - JSON
dict mapping system name to list of RuleEvaluation.

**Output**: If match: canonical JSON of PatternMatch. If no match: the
literal string "null".

### 3.4 build_evidence

**Input**: evaluations_json (str); matches_json (str) - JSON list of
PatternMatch (may be "[]" or "null"); system (str).

**Output**: Canonical JSON of a **list** of Evidence objects.

**Behavior**: Convert each RuleEvaluation to EvidenceItem (source_type
RULE), each PatternMatch to EvidenceItem (source_type PATTERN), group
by domain and conclusion, generate deterministic evidence_id values.

### 3.5 query_knowledge

**Input**: query_json (str) - KnowledgeQuery; store_json (str) - knowledge
store with nodes, relations, references.

**Output**: Canonical JSON of a KnowledgeResult object.

**Behavior**: Execute query against in-memory store, return matching
nodes/relations/references in stable order. Knowledge MUST NOT modify
Evidence or call Rules.

### 3.6 build_consensus

**Input**: evidence_json (str) - JSON list of Evidence; config_json (str)
- ConsensusConfig.

**Output**: Canonical JSON of a ConsensusReport object.

**Behavior**: Group evidence by domain and conclusion, apply conflict
strategy (retain_all / highest_confidence / majority), apply
cross-system bonus, sort conclusions deterministically. Consensus MUST
NOT call Rule Engine, Pattern Matcher, Knowledge Query, or LLM.
---

## 4. Running the Conformance Suite

### 4.1 Python

Implement RuntimeAdapter and run:

    from reference.conformance_runner import ConformanceRunner, certify

    class MyAdapter:
        def evaluate_rule(self, rule_yaml, chart_data): ...
        def match_pattern(self, pattern_yaml, evaluations_json, system): ...
        def match_pattern_cross_system(self, pattern_yaml, evaluations_by_system_json): ...
        def build_evidence(self, evaluations_json, matches_json, system): ...
        def query_knowledge(self, query_json, store_json): ...
        def build_consensus(self, evidence_json, config_json): ...

    result = ConformanceRunner().run(MyAdapter(), "my-runtime", "1.0.0")
    print(result.certified, result.coverage)
    if result.certified:
        manifest = certify(result)

### 4.2 Rust / Go

Production Runtimes in Rust or Go have two options:

1. **FFI bridge**: Expose the runtime as a Python C extension or via
   PyO3 (Rust) / cgo (Go), then wrap in a Python RuntimeAdapter.
2. **Standalone runner**: Load golden vectors from
   `reference/conformance/golden/`, execute each vector locally,
   produce a ConformanceResult JSON, and compare against expected
   output using the same canonical JSON rules (CF-001 through CF-003).

In both cases, the golden vector files on disk are the source of truth.
The Production Runtime MUST produce byte-identical canonical JSON for
each vector.

---

## 5. Golden Vector Format

Each golden vector is a JSON object:

    {
      "vector_id": "gv:rule:4ac4eda17425",
      "layer": "rule",
      "name": "01_single_condition",
      "description": "",
      "input": {
        "rule_yaml": "...",
        "chart_data": { ... }
      },
      "expected_output": [ ... ]
    }

The `expected_output` field type varies by layer:

| Layer | expected_output type |
|-------|---------------------|
| rule | list (RuleEvaluation[]) |
| pattern | dict (PatternMatch) or null |
| evidence | list (Evidence[]) |
| knowledge | dict (KnowledgeResult) |
| consensus | dict (ConsensusReport) |

Golden vectors are stored per-layer in
`reference/conformance/golden/{layer}_vectors.json`.

---

## 6. Certification

### 6.1 Certification Process

1. Implement RuntimeAdapter (Section 2).
2. Run ConformanceRunner (Section 4).
3. Check result.certified (must be True).
4. Call certify(result) to obtain a ConformanceManifest.
5. Store the manifest as proof of certification.

### 6.2 Certification Requirements

- All GOLDEN_JSON checks MUST pass (byte-identical output).
- All DETERMINISTIC_OUTPUT checks MUST pass.
- All CONTRACT_DIFF checks MUST pass.
- All BEHAVIOR_COVERAGE checks MUST pass.
- The ARCHITECTURE_BOUNDARY check MUST pass.
- A single failure prevents certification.
- Coverage MUST be 1.0 (100%).

### 6.3 Revocation

Certification is revoked if any conformance check fails on re-run, if
contract or behavior version changes without an ACP, or if the runtime
produces non-deterministic output.

---

## 7. Key References

| Document | Purpose |
|----------|---------|
| `CONFORMANCE_SPEC.md` | CF-001 through CF-020 rules |
| `BEHAVIOR_SPEC.md` | 35 Behavior Contracts (Rule/Pattern/Evidence) |
| `KNOWLEDGE_BEHAVIOR_SPEC.md` | 20 Knowledge Behavior Contracts |
| `CONSENSUS_BEHAVIOR_SPEC.md` | 25 Consensus Behavior Contracts |
| `REFERENCE_RUNTIME_SPEC.md` | Reference Runtime authority + ACP process |
| `RUNTIME_CONTRACT.md` | Contract lifecycle + merge gate |
| `CONTRACT_VERSIONING.md` | Version bump rules |
| `docs/engineering/01_rule_dsl.md` | Rule DSL grammar and YAML format |
