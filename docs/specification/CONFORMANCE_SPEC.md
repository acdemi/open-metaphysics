# Conformance Specification (Normative)

> **Status**: Normative - Binding on all implementations.
> **Authority**: Defines immutable Runtime Conformance rules for
> validating Production Runtimes (Rust / Go / Python / WASM) against
> the Reference Runtime.
> **Keywords**: RFC 2119 (**MUST**, **MUST NOT**, **SHALL**,
> **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **MAY**).
> **Companion**: `REFERENCE_RUNTIME_SPEC.md`, `BEHAVIOR_SPEC.md`,
> `RUNTIME_CONTRACT.md`, `CONTRACT_VERSIONING.md`

---

## 1. Purpose

This document defines the **Conformance Rules** (CF-001 through
CF-020) for the open-metaphysics project.

The Conformance Framework validates that any Production Runtime
produces **byte-identical** output to the Reference Runtime for the
same inputs. Only runtimes that pass **100%** of conformance checks
are granted **Certified** status.

These rules are **immutable**. Any modification requires an
Architecture Change Proposal (ACP), as defined in
`REFERENCE_RUNTIME_SPEC.md` Section 8.

---

## 2. Architecture Boundary

### 2.1 What Conformance IS

```
Golden Vectors (auto-generated)
        │
        ▼
ConformanceRunner ──► RuntimeAdapter ──► Production Runtime
        │                                       │
        │   expected (Reference)    actual (Production)
        │              │                   │
        └──────────────┴────── diff ───────┘
                             │
                    ConformanceResult
                    (passed / failed / certified)
```

Conformance provides:
- Golden vectors (auto-generated from the Reference Runtime)
- Schema, behavior, and contract validation checks
- Certification gate (100% pass = Certified)

### 2.2 What Conformance IS NOT

| Forbidden Action | Reason |
|------------------|--------|
| Implement business logic | Conformance validates, never computes domain results |
| Modify the Reference Runtime | Conformance reads Runtime output; it must not alter it |
| Call LLM | Conformance is deterministic; LLM is non-deterministic |
| Call databases | Conformance is in-memory only |
| Add new domain models | Conformance tests existing models, does not create them |

---

## 3. Conformance Categories

| Category | Scope |
|----------|-------|
| `SCHEMA` | Pydantic model validation of outputs |
| `GOLDEN_JSON` | Byte-identical JSON match against golden vectors |
| `STABLE_ORDERING` | List and key ordering is deterministic |
| `DETERMINISTIC_HASH` | Same input produces same content hash |
| `CONTRACT_DIFF` | Contract files are structurally valid |
| `NULL_HANDLING` | `None` / null serialization is correct |
| `EMPTY_INPUT` | Empty inputs produce valid deterministic output |
| `DUPLICATE_HANDLING` | Duplicate inputs do not alter output |
| `DETERMINISTIC_OUTPUT` | Same input twice yields identical output |
| `ENUM_SERIALIZATION` | Enums serialize as string values |
| `BEHAVIOR_COVERAGE` | All Behavior Contracts are covered |
| `ARCHITECTURE_BOUNDARY` | Adapter exposes no forbidden methods |

---

## 4. Conformance Rules

### 4.1 Canonical JSON Form (CF-001)

**Rule**: All Runtime output **MUST** be canonical JSON.

**Normative**:
- Output **MUST** be produced by
  `json.dumps(obj, ensure_ascii=False, sort_keys=True)`.
- No trailing whitespace, no pretty-printing, no trailing newline.
- The same Python object **MUST** always produce the same JSON string.

**Test**: `test_reference_conformance.py::TestReferenceAdapterRule::*`

### 4.2 UTF-8 Encoding (CF-002)

**Rule**: All JSON output **MUST** preserve Unicode characters.

**Normative**:
- `ensure_ascii` **MUST** be `False`.
- Chinese characters (e.g., `伤官`) **MUST NOT** be escaped to
  `\uXXXX` sequences.
- This guarantees cross-runtime byte equivalence for CJK content.

**Test**: `test_reference_conformance.py::TestConformanceRules::*`

### 4.3 Sorted Keys (CF-003)

**Rule**: JSON object keys **MUST** be sorted lexicographically.

**Normative**:
- `sort_keys=True` **MUST** be used in all serialization.
- Key order is part of the contract; it is **NOT** optional.
- Production Runtimes **MUST NOT** rely on insertion order.

**Test**: `test_reference_conformance.py::TestReferenceAdapterRule::*`

### 4.4 Stable List Ordering (CF-004)

**Rule**: List outputs **MUST** be deterministically ordered.

**Normative**:
- Lists in output (e.g., `evaluations`, `evidence`, `conclusions`)
  **MUST** have a stable sort key.
- The sort key **MUST** be documented in the relevant Behavior
  Contract (e.g., BC-DET-001).
- Two runs with the same input **MUST** produce lists in identical
  order.

**Test**: `test_reference_conformance.py::TestDeterminism::*`

### 4.5 Deterministic Field Order (CF-005)

**Rule**: Object field order in serialized JSON **MUST** be
determined solely by `sort_keys=True`.

**Normative**:
- Production Runtimes **MUST NOT** emit fields in model-declaration
  order.
- Field order **MUST** be lexicographic by key name.
- This is a corollary of CF-003, restated for emphasis.

**Test**: `test_reference_conformance.py::TestConformanceRules::*`

### 4.6 Content-Addressed Hash (CF-006)

**Rule**: Deterministic hashes **MUST** be content-addressed.

**Normative**:
- The hash algorithm is **SHA-256**.
- The hash input is the canonical JSON string (CF-001).
- The same canonical JSON **MUST** always produce the same hash.
- Hashes are used for vector IDs and contract golden example IDs.

**Test**: `test_reference_conformance.py::TestDeterminism::*`

### 4.7 Hash Stability Across Runs (CF-007)

**Rule**: The hash of a given output **MUST NOT** change between
runs, across machines, or across Python versions.

**Normative**:
- Hash stability depends on CF-001 through CF-005.
- If a hash changes without an ACP, the implementation is buggy.
- Golden vectors store expected output (not hashes); hashes are
  derived at validation time.

**Test**: `test_reference_conformance.py::TestDeterminism::*`

### 4.8 Null Serialization (CF-008)

**Rule**: `None` / null **MUST** serialize as the string `"null"`.

**Normative**:
- When a Pattern does not match, the adapter **MUST** return the
  literal string `"null"` (not `null` in a wrapper object).
- `json.dumps(None)` produces `"null"`; this **MUST** match.
- Production Runtimes **MUST** distinguish `None` (no match) from
  `False` (condition failed).

**Test**: `test_reference_conformance.py::TestReferenceAdapterPattern::test_no_match_returns_null`

### 4.9 None vs Empty Distinction (CF-009)

**Rule**: `None` (no result) and `[]` (empty result) are distinct
outputs and **MUST NOT** be conflated.

**Normative**:
- A PatternMatch that returns `None` **MUST** serialize as `"null"`.
- A Rule evaluation with zero matches **MUST** serialize as `"[]"`.
- An Evidence list with zero items **MUST** serialize as `"[]"`.
- The conformance framework **MUST** verify this distinction.

**Test**: `test_reference_conformance.py::TestConformanceRules::*`

### 4.10 Duplicate Input Idempotency (CF-010)

**Rule**: Duplicate inputs **MUST NOT** alter output.

**Normative**:
- If the same RuleEvaluation appears twice in input, the output
  **MUST** remain identical to a single occurrence (deduplication
  is the domain's responsibility, not conformance's).
- The conformance framework **MUST** verify that running the same
  golden vector twice produces identical results.
- This is enforced by the `DETERMINISTIC_OUTPUT` check.

**Test**: `test_reference_conformance.py::TestDeterminism::test_same_input_same_output`
### 4.11 Duplicate Node/Evidence Handling (CF-011)

**Rule**: Duplicate knowledge nodes or evidence items **MUST** be
handled per their respective Behavior Contracts.

**Normative**:
- Knowledge deduplication follows KB-001.
- Evidence deduplication follows BC-EV-001.
- Conformance **MUST NOT** define new deduplication rules.
- If the Reference Runtime deduplicates, the Production Runtime
  **MUST** also deduplicate identically.

**Test**: `test_reference_conformance.py::TestReferenceAdapterKnowledge::*`

### 4.12 Contract Structural Validity (CF-012)

**Rule**: Every contract file **MUST** be structurally valid.

**Normative**:
- Each contract JSON **MUST** contain `contract_version` (string).
- Each contract JSON **MUST** contain `golden_examples` (array).
- The `CONTRACT_DIFF` check **MUST** verify these fields.
- A contract missing either field **MUST** fail conformance.

**Test**: `test_reference_conformance.py::TestContractDiff::*`

### 4.13 Contract Auto-Generation (CF-013)

**Rule**: Contracts **MUST** be auto-generated by the Reference
Runtime.

**Normative**:
- Contracts **MUST NOT** be hand-written.
- Contracts are generated by `export_*_contract()` functions.
- Golden vectors **MUST** be auto-generated by
  `generate_golden_vectors()`.
- Manual editing of contract or golden files is a **violation**.

**Test**: `test_reference_conformance.py::TestGoldenVectorGeneration::*`

### 4.14 Contract Version Pinning (CF-014)

**Rule**: The conformance framework **MUST** pin contract and
behavior versions.

**Normative**:
- `ConformanceRunner.CONTRACT_VERSION` is `"1.0.0"`.
- `ConformanceRunner.BEHAVIOR_VERSION` is `"1.0.0"`.
- A version bump requires an ACP (see `CONTRACT_VERSIONING.md`).
- The `ConformanceResult` **MUST** report both versions.

**Test**: `test_reference_conformance.py::TestConformanceRunner::test_contract_version`

### 4.15 Behavior Contract Coverage (CF-015)

**Rule**: Conformance **MUST** cover all Behavior Contracts.

**Normative**:
- The `BEHAVIOR_COVERAGE` check verifies a known set of behavior
  contract IDs (BC-RE-001, BC-DNF-001, BC-PM-001, BC-EV-001,
  BC-JSON-001, BC-DET-001, BC-EDGE-001, KB-001 through KB-020,
  CS-001 through CS-025).
- Each behavior contract **MUST** be represented by at least one
  golden vector.
- Missing coverage **MUST** fail conformance.

**Test**: `test_reference_conformance.py::TestConformanceRules::test_behavior_coverage_checks_present`

### 4.16 Behavior Contract Immunity (CF-016)

**Rule**: Conformance **MUST NOT** modify or redefine Behavior
Contracts.

**Normative**:
- Conformance reads Behavior Contracts as reference; it does not
  write them.
- If a Behavior Contract is insufficient, an ACP **MUST** be filed.
- The conformance framework **MUST NOT** add new behavior rules.

**Test**: `test_reference_conformance.py::TestArchitectureBoundary::*`

### 4.17 Golden Vector Auto-Discovery (CF-017)

**Rule**: Golden vectors **MUST** be auto-discovered from disk.

**Normative**:
- `load_golden_vectors()` scans `reference/conformance/golden/`
  for `*_vectors.json` files.
- No manual registration of vectors is permitted.
- Adding a new example YAML file automatically produces a new
  golden vector on regeneration.
- The file count **MUST** equal the number of layers (5).

**Test**: `test_reference_conformance.py::TestGoldenVectorGeneration::test_auto_discovered_from_disk`

### 4.18 Golden Vector Reproducibility (CF-018)

**Rule**: Regenerating golden vectors **MUST** produce identical
results.

**Normative**:
- `generate_golden_vectors()` called twice **MUST** yield the same
  vector IDs and expected outputs.
- The `expected_output` of each vector **MUST** be the exact
  canonical JSON the adapter produces.
- Vectors are compared by `vector_id`, not by disk order.

**Test**: `test_reference_conformance.py::TestGoldenVectorGeneration::test_regenerate_matches_loaded`

### 4.19 Layer Coverage (CF-019)

**Rule**: Conformance **MUST** cover all five layers.

**Normative**:
- The five layers are: `RULE`, `PATTERN`, `EVIDENCE`,
  `KNOWLEDGE`, `CONSENSUS`.
- Each layer **MUST** have at least one golden vector.
- A missing layer **MUST** fail conformance.
- The `ConformanceManifest.supported_layers` **MUST** list all five
  for a certified runtime.

**Test**: `test_reference_conformance.py::TestGoldenVectorGeneration::test_all_layers_covered`

### 4.20 Certification Gate (CF-020)

**Rule**: Only **100%** pass rate grants certification.

**Normative**:
- `ConformanceResult.certified` is `True` if and only if
  `failed == 0` and `total > 0`.
- `ConformanceManifest.certified` mirrors the result.
- A single failure **MUST** prevent certification.
- Coverage is `passed / total`; certification requires
  `coverage == 1.0`.

**Test**: `test_reference_conformance.py::TestCertification::*`

---

## 5. ConformanceResult

The `ConformanceResult` model records the outcome of a conformance
run:

| Field | Type | Description |
|-------|------|-------------|
| `runtime_name` | `str` | Name of the runtime under test |
| `runtime_version` | `str` | Version of the runtime under test |
| `passed` | `int` | Number of checks that passed |
| `failed` | `int` | Number of checks that failed |
| `total` | `int` | Total checks executed |
| `coverage` | `float` | `passed / total`, range `[0.0, 1.0]` |
| `contract_version` | `str` | Pinned contract version (`"1.0.0"`) |
| `behavior_version` | `str` | Pinned behavior version (`"1.0.0"`) |
| `checks` | `list[ConformanceCheckResult]` | Individual check results |
| `certified` | `bool` | `True` iff `failed == 0 and total > 0` |

---

## 6. ConformanceManifest

The `ConformanceManifest` is derived from a `ConformanceResult` via
`certify()`. It records which layers, contracts, and behaviors a
runtime supports:

| Field | Type | Description |
|-------|------|-------------|
| `runtime_name` | `str` | Runtime name |
| `runtime_version` | `str` | Runtime version |
| `supported_layers` | `list[str]` | Layers with passing checks |
| `supported_contracts` | `dict[str, str]` | Contract name -> version |
| `supported_behaviors` | `list[str]` | Behavior contract IDs covered |
| `certified` | `bool` | `True` iff 100% pass |

---

## 7. Runtime Certification

### 7.1 Certification Process

1. Implement `RuntimeAdapter` protocol (see `IMPLEMENTATION_GUIDE.md`).
2. Run `ConformanceRunner().run(adapter, name, version)`.
3. Check `result.certified`.
4. If certified, call `certify(result)` to obtain a
   `ConformanceManifest`.
5. Store the manifest as proof of certification.

### 7.2 Revocation

Certification is **revoked** if:
- Any conformance check fails on re-run.
- The contract version or behavior version changes without an ACP.
- The runtime produces non-deterministic output.

---

## 8. Merge Gate

Before any Production Runtime implementation can be merged:

1. **Golden Tests** **MUST** pass (`tests/test_reference_*.py`).
2. **Contract Diff** **MUST** show no unexpected changes.
3. **Conformance Suite** **MUST** pass at 100%.
4. **Behavior Validation** **MUST** confirm no Behavior Contract
   violations.

If any gate fails, the merge **MUST** be blocked.

This is the enforcement mechanism for Reference Runtime Supremacy
(see `REFERENCE_RUNTIME_SPEC.md` and `AGENTS.md` Section 7).
