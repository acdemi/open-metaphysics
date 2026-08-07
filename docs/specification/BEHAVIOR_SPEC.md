# Behavior Specification (Normative)

> **Status**: Normative - Binding on all implementations.
> **Authority**: Defines immutable behavior contracts for the
> Reference Runtime and all formal implementations.
> **Keywords**: RFC 2119 (**MUST**, **MUST NOT**, **SHALL**,
> **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **MAY**).
> **Companion**: `REFERENCE_RUNTIME_SPEC.md`

---

## 1. Purpose

This document defines every **Behavior Contract** in the
open-metaphysics Reference Runtime. A Behavior Contract is an
observable, testable guarantee about how the system processes
inputs and produces outputs.

Behavior Contracts are **immutable**. They may only be changed via
an Architecture Change Proposal (ACP), as defined in
`REFERENCE_RUNTIME_SPEC.md` Section 8.

Any formal implementation (Rust, Go, Python, WASM) that violates
a Behavior Contract is **buggy** and **MUST** be corrected.

---

## 2. Behavior Contract Definition

A **Behavior Contract** is a normative rule that satisfies all of
the following:

1. **Observable** - It can be verified by examining inputs and
   outputs, without inspecting internal implementation.
2. **Deterministic** - The same input always produces the same
   output.
3. **Testable** - It is covered by at least one Golden Test.
4. **Versioned** - It is tied to a Contract version.

### 2.1 Behavior Contract Categories

| Category | Scope |
|----------|-------|
| Rule Engine Behavior | Condition evaluation, operators, field resolution |
| DNF Expansion Behavior | `any:`/`all:`/`not:` transformation |
| Pattern Matching Behavior | Match modes, None vs False, requirements |
| Evidence Layer Behavior | Item generation, grouping, IDs, trace |
| JSON Serialization Behavior | Field order, encoding, null, enums |
| Deterministic Output Behavior | Hash algorithm, content-addressed IDs |
| Edge Case Behavior | Missing fields, null, empty, out-of-range |

---

## 3. Rule Engine Behavior

### 3.1 Condition Evaluation (BC-RE-001)

**Rule**: All conditions in a `Rule` are ANDed. A `Rule` matches
if and only if every `RuleCondition` evaluates to `True`.

**Normative**:
- Conditions **MUST** be evaluated in declaration order.
- Short-circuit evaluation **MAY** be used internally, but the
  result **MUST** be identical to evaluating all conditions.
- A `Rule` with zero conditions is invalid (Pydantic `min_length=1`).

**Test**: `test_reference_rules.py::TestRuleEngine::*`

### 3.2 Operator Semantics (BC-RE-002)

The following 11 operators are defined. Their semantics are
normative and **MUST NOT** change:

| Operator | Semantics |
|----------|-----------|
| `equals` | `actual == expected` |
| `not_equals` | `actual != expected` |
| `contains` | `expected in actual` (returns `False` if `actual is None`) |
| `not_contains` | `expected not in actual` (returns `True` if `actual is None`) |
| `in` | `actual in expected` |
| `not_in` | `actual not in expected` |
| `greater_than` | `actual > expected` |
| `less_than` | `actual < expected` |
| `exists` | Field path resolves without `KeyError`/`IndexError` |
| `not_exists` | Field path raises `KeyError` or `IndexError` |
| `matches` | `re.search(expected, str(actual)) is not None` |

**Normative**:
- `contains` on `None` **MUST** return `False` (not raise).
- `not_contains` on `None` **MUST** return `True` (not raise).
- `matches` **MUST** use `re.search` (not `re.match` or `re.fullmatch`).
- `exists`/`not_exists` **MUST NOT** evaluate the field value;
  they check path resolvability only.

**Test**: `test_reference_rules.py::TestOperators::*`

### 3.3 Field Path Resolution (BC-RE-003)

**Rule**: Field paths use dot notation with bracket index syntax.

**Normative**:
- Dot separator `.` splits path into segments.
- Bracket syntax `[N]` accesses list index `N`.
- Multiple indices per segment are supported: `pillars[0][1]`.
- Path resolution **MUST** raise `KeyError` if a dict key is absent.
- Path resolution **MUST** raise `IndexError` if a list index is
  out of range.
- Invalid path segments **MUST** raise `ValueError`.

**Examples**:
```
"day_master_strength"           -> data["day_master_strength"]
"ten_gods_map.values"           -> data["ten_gods_map"]["values"]
"pillars[0].ten_gods_stem"      -> data["pillars"][0]["ten_gods_stem"]
```

**Test**: `test_reference_rules.py::TestFieldPath::*`

### 3.4 Negate Handling (BC-RE-004)

**Rule**: `negate=True` inverts the condition result.

**Normative**:
- If the condition evaluates to `True`, `negate=True` makes it
  `False`, and vice versa.
- `negate` applies to ALL operators, including `exists` and
  `not_exists`.
- `negate=True` on `exists` is equivalent to `not_exists` (but
  implemented as `not field_exists(...)`).

**Test**: `test_reference_rules.py::TestNegate::*`

### 3.5 RuleEvaluation Output (BC-RE-005)

**Rule**: The `RuleEvaluation` output for a matched and non-matched
rule is normative.

**Matched rule** (`all conditions True`):
```
RuleEvaluation(
    rule_id = rule.id,
    matched = True,
    results = list(rule.results),       # copy, not reference
    priority = rule.priority,
    confidence = rule.confidence,
)
```

**Non-matched rule** (`any condition False`):
```
RuleEvaluation(
    rule_id = rule.id,
    matched = False,
    results = [],                        # empty list
    priority = rule.priority,
    confidence = rule.confidence,
)
```

**Normative**:
- `priority` and `confidence` are ALWAYS copied from the Rule,
  regardless of match status.
- `results` for non-matched **MUST** be an empty list, not `None`.
- `results` for matched **MUST** be a copy of `rule.results`.

**Test**: `test_reference_rules.py::TestRuleEngine::*`

---

## 4. DNF Expansion Behavior

### 4.1 DNF Expansion Overview (BC-DNF-001)

**Rule**: The DSL Parser converts the `if:` section into
Disjunctive Normal Form (DNF), producing one or more `Rule` objects.

**Normative**:
- Each DNF conjunction becomes a separate `Rule`.
- All DNF-expanded Rules share the same `results`, `priority`,
  `source`, `confidence`, `version`, and all other metadata.
- Only `id` and `conditions` differ between expanded Rules.

### 4.2 any: Expansion (BC-DNF-002)

**Rule**: `any:` at the top level produces multiple Rules.

**Normative**:
- Each child of `any:` becomes a separate Rule.
- Rule IDs use `#N` suffix: `base_id#1`, `base_id#2`, ...
- `N` is 1-indexed, assigned in declaration order.
- If only one conjunction results (no `any:`), the original ID is
  used with NO `#N` suffix.

**Example**:
```yaml
# Input: any: [condition_a, condition_b]
# Output: 2 Rules
#   Rule 1: id=base#1, conditions=[condition_a]
#   Rule 2: id=base#2, conditions=[condition_b]
```

**Test**: `test_reference_rules.py::TestDNFExpansion::*`

### 4.3 all: Expansion (BC-DNF-003)

**Rule**: `all:` combines children into a single conjunction
(AND). When nested with `any:`, cross-product expansion applies.

**Normative**:
- `all: [a, b, c]` produces one conjunction: `[a, b, c]`.
- `all: [any:[a,b], c]` produces two conjunctions: `[a, c]` and
  `[b, c]` (cross product).
- Empty `all:` **MUST** raise `ValueError`.

### 4.4 not: Expansion (BC-DNF-004)

**Rule**: `not:` applies De Morgan's laws.

**Normative**:
| Input | Transformation |
|-------|---------------|
| `not: {leaf}` | Flip `negate` flag on the leaf |
| `not: {all: [a, b]}` | `any: [not: a, not: b]` (De Morgan) |
| `not: {any: [a, b]}` | `all: [not: a, not: b]` (De Morgan) |
| `not: {not: X}` | `X` (double negation cancels) |

**Flip negate rule**:
- If `negate` is absent or `False`, set to `True`.
- If `negate` is `True`, set to `False`.

**Test**: `test_reference_rules.py::TestNegateDNF::*`

### 4.5 DNF ID Convention (BC-DNF-005)

**Rule**: The `#N` suffix is only applied when DNF expansion
produces more than one conjunction.

**Normative**:
- Single conjunction: `rule:bazi:yang_ren_ge:v1` (no suffix)
- Multiple conjunctions: `rule:bazi:xxx:v1#1`, `rule:bazi:xxx:v1#2`
- `N` **MUST** be sequential starting from 1.
- `N` **MUST** reflect declaration order of `any:` children.

**ID regex**: `^rule:[a-z]+:[a-z_]+:v[0-9]+(#\d+)?$`

---

## 5. Pattern Matching Behavior

### 5.1 Return Value Semantics (BC-PM-001)

**Rule**: `PatternMatcher.match()` returns one of three values.

| Condition | Return |
|-----------|--------|
| No pattern rule_ids present in evaluations | `None` |
| Pattern rule_ids present but requirements not met | `PatternMatch(matched=False)` |
| Pattern rule_ids present and requirements met | `PatternMatch(matched=True)` |

**Normative**:
- `None` means "not applicable" - the pattern was not even
  considered.
- `PatternMatch(matched=False)` means "considered but rejected."
- These two cases **MUST NOT** be conflated.

**Test**: `test_reference_patterns.py::TestSingleRuleMatch::*`

### 5.2 Single Rule Match (BC-PM-002)

**Rule**: A pattern with `requirements` containing a single
requirement with `logic: all` and one `rule_id` matches when that
rule's evaluation has `matched=True`.

### 5.3 Multi Rule Match - ALL Logic (BC-PM-003)

**Rule**: A requirement with `logic: all` matches when ALL listed
`rule_ids` have matched evaluations.

**Normative**:
- `len(matched_rule_ids & req.rule_ids) == len(req.rule_ids)`

### 5.4 Multi Rule Match - ANY Logic (BC-PM-004)

**Rule**: A requirement with `logic: any` matches when at least
`min_matches` of the listed `rule_ids` have matched evaluations.

**Normative**:
- `len(matched_rule_ids & req.rule_ids) >= req.min_matches`
- `min_matches` defaults to 1.

### 5.5 Cross-System Match (BC-PM-005)

**Rule**: `match_cross_system()` accepts a dict mapping system
names to their evaluation lists.

**Normative**:
- Evaluations from all systems are combined.
- `matched_by` **MUST** be `"cross_system"`.
- Evidence records **MUST** include the originating system name.

### 5.6 Match Output Fields (BC-PM-006)

**Rule**: `PatternMatch` output fields are normative.

| Field | Matched | Not Matched |
|-------|---------|-------------|
| `matched` | `True` | `False` |
| `confidence` | `pattern.confidence` | `0.0` |
| `matched_rule_ids` | sorted list of matched rule IDs | sorted list (may be non-empty) |
| `evidence` | list of `PatternEvidence` | list of `PatternEvidence` |
| `knowledge_node_ids` | copy of `pattern.knowledge_node_ids` | copy |
| `category` | `pattern.category` | `pattern.category` |

**Normative**:
- `matched_rule_ids` **MUST** be sorted lexicographically.
- `confidence` for non-matched **MUST** be exactly `0.0`, not
  `pattern.confidence`.

### 5.7 match_all vs match_all_with_misses (BC-PM-007)

**Rule**: The two batch methods have different filtering behavior.

| Method | Returns |
|--------|---------|
| `match_all()` | Only `PatternMatch` where `matched=True` |
| `match_all_with_misses()` | All `PatternMatch` (matched + non-matched), excluding `None` |

**Normative**:
- Neither method returns `None` entries.
- `match_all` **MUST NOT** include `matched=False` results.

**Test**: `test_reference_patterns.py::TestBatchMatching::*`

---

## 6. Evidence Layer Behavior

### 6.1 EvidenceItem Generation from RuleEvaluation (BC-EV-001)

**Rule**: A matched `RuleEvaluation` with N results produces N
`EvidenceItem` objects (one per result). Non-matched evaluations
produce zero items.

**Normative**:
- `evidence_id` **MUST** be deterministic (see BC-DET-001).
- `source_type` **MUST** be `EvidenceType.RULE`.
- `source_id` **MUST** be `evaluation.rule_id`.
- `confidence` **MUST** be `evaluation.confidence`.
- `conclusion` **MUST** be `result.conclusion`.
- `domain` **MUST** be `result.domain`.
- `direction` **MUST** be `result.direction`.
- `weight` **MUST** be `result.weight`.
- Non-matched evaluation **MUST** produce an empty list.

**Test**: `test_reference_evidence.py::TestRuleToEvidence::*`

### 6.2 EvidenceItem Generation from PatternMatch (BC-EV-002)

**Rule**: A matched `PatternMatch` produces exactly one
`EvidenceItem`. Non-matched produces `None`.

**Normative**:
- `source_type` **MUST** be `EvidenceType.PATTERN`.
- `source_id` **MUST** be `match.pattern_id`.
- `system` **MUST** be `match.matched_by`.
- `conclusion` **MUST** be `match.pattern_name`.
- `confidence` **MUST** be `match.confidence`.
- `domain` **MUST** be derived from `category` via
  `category_to_domain()` mapping.
- `direction` **MUST** be `None` (patterns have no direction).
- `weight` **MUST** be `match.confidence`.

**Category-to-Domain mapping** (normative):
| PatternCategory | Domain |
|-----------------|--------|
| `personality` | `personality` |
| `career` | `career` |
| `geju` | `overall` |
| `shensha` | `overall` |
| `relation` | `overall` |
| `wuxing` | `overall` |
| `cross_system` | `overall` |
| `None` | `overall` |

**Test**: `test_reference_evidence.py::TestPatternToEvidence::*`

### 6.3 Evidence Grouping (BC-EV-003)

**Rule**: `EvidenceItem` objects are grouped by `(domain, conclusion)`
into `Evidence` objects.

**Normative**:
- Items with the same `domain` AND `conclusion` **MUST** be in the
  same `Evidence`.
- Items with different `domain` OR `conclusion` **MUST** be in
  separate `Evidence` objects.
- Empty item list **MUST** produce empty `Evidence` list.
- `Evidence.confidence` **MUST** be `max(item.confidence)` across
  items in the group.
- `Evidence.system` **MUST** be the single system if all items
  share it, otherwise `"multi"`.
- `Evidence.items` **MUST** have `min_length=1` (empty rejected).

**Test**: `test_reference_evidence.py::TestRuleToEvidence::test_build_from_evaluations_same_conclusion_grouped`

### 6.4 Evidence ID Generation (BC-EV-004)

**Rule**: Evidence and EvidenceItem IDs are content-addressed.

**EvidenceItem ID**:
```
ev:<system>:<hash>
```
where `hash = SHA256("|".join(source_type, source_id, system, conclusion, index))[:12]`

**Evidence (group) ID**:
```
ev:<domain>:<hash>
```
where `hash = SHA256("|".join(domain, conclusion, "|".join(sorted(item_ids))))[:12]`

**Normative**:
- `index` is the 0-based result index for rules (0 for patterns).
- Item IDs within a group **MUST** be sorted before hashing.
- Same content **MUST** always produce the same ID.
- Different content **MUST** produce different IDs (collision
  resistance: 12 hex chars = 48 bits).

**Test**: `test_reference_evidence.py::TestDeterminism::*`

### 6.5 Trace Chain (BC-EV-005)

**Rule**: Every `EvidenceItem` carries a `trace` list proving
traceability to its source.

**Rule evidence trace**:
```
[rule_id, conclusion_node_id?]   # conclusion_node_id only if present
```

**Pattern evidence trace**:
```
[pattern_id, *sorted(matched_rule_ids), *sorted(knowledge_node_ids)]
```

**Normative**:
- `trace[0]` **MUST** always equal `source_id`.
- Rule IDs in pattern traces **MUST** be sorted lexicographically.
- Knowledge node IDs in pattern traces **MUST** be sorted
  lexicographically.
- `conclusion_node_id` is optional; if `None`, it is omitted from
  the trace.

**Test**: `test_reference_evidence.py::TestTraceability::*`

### 6.6 Knowledge Protocol (BC-EV-006)

**Rule**: `KnowledgeEvidenceProvider` is a Protocol (interface only).

**Normative**:
- The Protocol defines `from_knowledge_node()` and
  `from_knowledge_nodes()` method signatures.
- **No implementation exists** in the Reference Runtime.
- Future KnowledgeStore adapters **MUST** implement this Protocol.
- The Protocol **MUST NOT** be removed or have its signature
  changed without an ACP.

**Test**: `test_reference_evidence.py::TestKnowledgeProtocol::*`

---

## 7. JSON Serialization Behavior

### 7.1 Field Order (BC-JSON-001)

**Rule**: JSON field order follows Pydantic model field definition
order (insertion order).

**Normative**:
- `model_dump_json()` output **MUST** have fields in model
  definition order.
- Contract JSON files use `sort_keys=True` for canonical comparison.
- Formal implementations **MUST** produce the same field values,
  but field ORDER in Contract files is canonical (sorted).

### 7.2 Encoding (BC-JSON-002)

**Rule**: All JSON **MUST** be UTF-8 encoded.

**Normative**:
- `ensure_ascii=False` **MUST** be used for Contract generation.
- Chinese characters **MUST** appear as literal characters, not
  `\uXXXX` escapes.
- Contract files **MUST** be valid UTF-8.

### 7.3 Null Handling (BC-JSON-003)

**Rule**: Optional fields with `None` values **MUST** be serialized
as JSON `null`, not omitted.

**Normative**:
- `timestamp: None` serializes as `"timestamp": null`.
- `direction: None` serializes as `"direction": null`.
- `conclusion_node_id: None` serializes as `"conclusion_node_id": null`.
- Formal implementations **MUST** include null fields, not omit them.
- Exception: Pydantic models with `exclude_none=True` are not used
  in the Reference Runtime.

### 7.4 Enum Serialization (BC-JSON-004)

**Rule**: Enums serialize to their `.value` string.

**Normative**:
- `EvidenceType.RULE` -> `"rule"` (not `"EvidenceType.RULE"`).
- `Domain.PERSONALITY` -> `"personality"`.
- `ResultDirection.POSITIVE` -> `"positive"`.
- `PatternCategory.GEJU` -> `"geju"`.

### 7.5 Contract JSON Format (BC-JSON-005)

**Rule**: Contract files use canonical JSON for deterministic
comparison.

**Normative**:
- `json.dump(..., ensure_ascii=False, indent=2, sort_keys=True)`.
- `sort_keys=True` ensures key order is deterministic regardless
  of insertion order.
- `indent=2` for human readability.
- Re-generating a Contract **MUST** produce byte-identical output
  if no behavior changed.

**Test**: `test_reference_evidence.py::TestContract::test_contract_determinism`

---

## 8. Deterministic Output Behavior

### 8.1 Hash Algorithm (BC-DET-001)

**Rule**: Content-addressed IDs use SHA-256 with 12-character hex
truncation.

**Specification**:
```
Algorithm: SHA-256
Input encoding: UTF-8
Input format: pipe-delimited ("|".join(parts))
Truncation: first 12 hex characters of the 64-character digest
Output: 12-character lowercase hexadecimal string
```

**Normative**:
- The hash algorithm **MUST NOT** change without an ACP.
- The truncation length (12) **MUST NOT** change without an ACP.
- The pipe delimiter **MUST** be used.
- The hash **MUST** be lowercase hex.

**Test**: `test_reference_evidence.py::TestDeterminism::test_deterministic_item_id_repeated`

### 8.2 Deterministic Output Guarantee (BC-DET-002)

**Rule**: Identical inputs **MUST** produce byte-identical outputs.

**Normative**:
- Running any builder method twice with the same input **MUST**
  produce objects whose `model_dump_json()` is identical.
- Re-generating a Contract **MUST** produce an identical dict.
- Lists that could vary in order (e.g., `matched_rule_ids`,
  `trace` for patterns, `item_ids` for grouping) **MUST** be
  sorted before inclusion in output.

### 8.3 Sorting Rules (BC-DET-003)

**Rule**: Specific fields **MUST** be sorted for determinism.

| Field | Sort Order |
|-------|-----------|
| `PatternMatch.matched_rule_ids` | Lexicographic ascending |
| `EvidenceItem.trace` (pattern) | `pattern_id` first, then sorted `rule_ids`, then sorted `knowledge_node_ids` |
| `Evidence.items` (within group) | By `evidence_id` for group ID hashing |
| `Evidence` list (from builder) | By `(domain, conclusion)` |
| Contract JSON keys | `sort_keys=True` |

**Normative**:
- `EvidenceItem.trace` for rules is NOT sorted (it preserves
  `[rule_id, conclusion_node_id]` order).
- `matched_rule_ids` is sorted AFTER filtering to pattern rules.

---

## 9. Edge Case Behavior

### 9.1 Missing Fields (BC-EDGE-001)

**Rule**: Missing required fields **MUST** raise `ValidationError`.

**Normative**:
- `Evidence` with `items=[]` **MUST** be rejected (`min_length=1`).
- `Rule` with `conditions=[]` **MUST** be rejected (`min_length=1`).
- `Rule` with `results=[]` **MUST** be rejected (`min_length=1`).
- `PatternRequirement` with `rule_ids=[]` **MUST** be rejected
  (`min_length=1`).

### 9.2 Null Values (BC-EDGE-002)

**Rule**: Nullable fields accept `None` and serialize as `null`.

**Normative**:
- `EvidenceItem.timestamp` defaults to `None`.
- `EvidenceItem.direction` defaults to `None` (for patterns).
- `RuleResult.conclusion_node_id` may be `None`.
- `Pattern.source` may be `None`.
- `EvidenceItem.metadata` defaults to `{}` (empty dict, not `None`).

### 9.3 Empty Inputs (BC-EDGE-003)

**Rule**: Empty input lists produce empty output lists.

| Input | Output |
|-------|--------|
| `build_from_evaluations([])` | `[]` |
| `build_from_pattern_matches([])` | `[]` |
| `from_rule_evaluations([])` | `[]` |
| `from_pattern_matches([])` | `[]` |
| `match_all(patterns, [])` | `[]` (no evaluations to match) |

### 9.4 Out-of-Range Values (BC-EDGE-004)

**Rule**: Numeric fields enforce bounds via Pydantic validation.

**Normative**:
- `confidence`: `[0.0, 1.0]` - out of range raises `ValidationError`.
- `weight`: `[0.0, 1.0]`.
- `credibility`: `[0.0, 1.0]`.
- `priority`: `[0, 100]` (integer).
- `min_matches`: `>= 1` (integer).

---

## 10. Behavior Contract Inventory

| ID | Contract | Component | Test File |
|----|----------|-----------|-----------|
| BC-RE-001 | Condition AND evaluation | Rule Engine | `test_reference_rules.py` |
| BC-RE-002 | Operator semantics (11 operators) | Rule Engine | `test_reference_rules.py` |
| BC-RE-003 | Field path resolution | Rule Engine | `test_reference_rules.py` |
| BC-RE-004 | Negate handling | Rule Engine | `test_reference_rules.py` |
| BC-RE-005 | RuleEvaluation output | Rule Engine | `test_reference_rules.py` |
| BC-DNF-001 | DNF expansion overview | DSL Parser | `test_reference_rules.py` |
| BC-DNF-002 | `any:` expansion | DSL Parser | `test_reference_rules.py` |
| BC-DNF-003 | `all:` expansion | DSL Parser | `test_reference_rules.py` |
| BC-DNF-004 | `not:` De Morgan expansion | DSL Parser | `test_reference_rules.py` |
| BC-DNF-005 | DNF ID convention (#N) | DSL Parser | `test_reference_rules.py` |
| BC-PM-001 | Return value (None vs False) | Pattern Matcher | `test_reference_patterns.py` |
| BC-PM-002 | Single rule match | Pattern Matcher | `test_reference_patterns.py` |
| BC-PM-003 | Multi rule ALL logic | Pattern Matcher | `test_reference_patterns.py` |
| BC-PM-004 | Multi rule ANY logic | Pattern Matcher | `test_reference_patterns.py` |
| BC-PM-005 | Cross-system match | Pattern Matcher | `test_reference_patterns.py` |
| BC-PM-006 | Match output fields | Pattern Matcher | `test_reference_patterns.py` |
| BC-PM-007 | match_all vs match_all_with_misses | Pattern Matcher | `test_reference_patterns.py` |
| BC-EV-001 | EvidenceItem from RuleEvaluation | Evidence Layer | `test_reference_evidence.py` |
| BC-EV-002 | EvidenceItem from PatternMatch | Evidence Layer | `test_reference_evidence.py` |
| BC-EV-003 | Evidence grouping | Evidence Layer | `test_reference_evidence.py` |
| BC-EV-004 | Evidence ID generation | Evidence Layer | `test_reference_evidence.py` |
| BC-EV-005 | Trace chain | Evidence Layer | `test_reference_evidence.py` |
| BC-EV-006 | Knowledge protocol | Evidence Layer | `test_reference_evidence.py` |
| BC-JSON-001 | Field order | JSON Serialization | `test_reference_evidence.py` |
| BC-JSON-002 | UTF-8 encoding | JSON Serialization | `test_reference_evidence.py` |
| BC-JSON-003 | Null handling | JSON Serialization | `test_reference_evidence.py` |
| BC-JSON-004 | Enum serialization | JSON Serialization | `test_reference_evidence.py` |
| BC-JSON-005 | Contract JSON format | JSON Serialization | `test_reference_evidence.py` |
| BC-DET-001 | Hash algorithm | Determinism | `test_reference_evidence.py` |
| BC-DET-002 | Deterministic output guarantee | Determinism | All test files |
| BC-DET-003 | Sorting rules | Determinism | All test files |
| BC-EDGE-001 | Missing fields | Edge Cases | All test files |
| BC-EDGE-002 | Null values | Edge Cases | All test files |
| BC-EDGE-003 | Empty inputs | Edge Cases | All test files |
| BC-EDGE-004 | Out-of-range values | Edge Cases | All test files |

**Total: 35 Behavior Contracts**

---

## 11. Immutability Statement

All 35 Behavior Contracts listed in Section 10 are **immutable**
as of Contract Version 1.0.0. Any modification to these contracts
requires:

1. An Architecture Change Proposal (ACP) - see
   `REFERENCE_RUNTIME_SPEC.md` Section 8.
2. A Contract Version bump - see `CONTRACT_VERSIONING.md`.
3. Updated Golden Tests.
4. Regenerated Architecture Contract.
5. Sync of all formal implementations.

No exception, shortcut, or "temporary override" is permitted.

---

## 12. Revision History

| Date | Version | Change |
|------|---------|--------|
| 2026-07-12 | 1.0.0 | Initial creation - 35 Behavior Contracts defined |
