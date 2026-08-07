# Consensus Behavior Specification (Normative)

> **Status**: Normative - Binding on all implementations.
> **Authority**: Defines immutable Consensus Layer behavior contracts.
> **Keywords**: RFC 2119 (**MUST**, **MUST NOT**, **SHALL**,
> **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **MAY**).
> **Companion**: `REFERENCE_RUNTIME_SPEC.md`, `BEHAVIOR_SPEC.md`

---

## 1. Purpose

This document defines the **Consensus Layer Behavior Contracts**
(CS-001 through CS-025) for the open-metaphysics Reference Runtime.

The Consensus Engine consumes `Evidence[]` and produces
`ConsensusConclusion[]` grouped into a `ConsensusReport`. It is the
final aggregation step before the Explain Layer.

### Architecture Boundary

Consensus **ONLY** consumes Evidence. It **MUST NOT**:
- Call Rule Engine, Pattern Matcher, Knowledge Query, or LLM.
- Re-reason, re-calculate rules, or add new Patterns.
- Modify input Evidence.
- Increase Confidence beyond the aggregation formula.

```
Evidence[] ──► ConsensusBuilder ──► ConsensusReport
                                      ├── conclusions[]
                                      ├── conflicts[]
                                      ├── domains[]
                                      ├── evidence_ids[]
                                      └── overall_confidence
```

---

## 2. Behavior Contracts

### Input Boundary

#### CS-001: ConsensusInput Only Accepts Evidence

**Rule**: `ConsensusInput.evidence` **MUST** be `list[Evidence]`.
Non-Evidence objects **MUST** be rejected at validation time.

**Test**: `test_input_accepts_evidence`, `test_input_only_evidence`

#### CS-002: Non-Evidence Rejected

**Rule**: Passing `RuleEvaluation`, `PatternMatch`, `KnowledgeNode`,
or raw dicts to `ConsensusInput` **MUST** raise `ValidationError`.

**Test**: `test_input_rejects_non_evidence`

### Aggregation

#### CS-003: Evidence Grouping

**Rule**: Evidence **MUST** be grouped by `(domain, conclusion)`.
Evidence with the same domain AND conclusion are merged into one
`ConsensusConclusion`.

**Test**: `test_groups_by_domain_conclusion`

#### CS-004: retain_all Strategy

**Rule**: `retain_all` keeps ALL conclusions, even conflicting ones.
No conclusions are dropped. All conflicting conclusions have
`is_conflict=True`.

**Test**: `test_retain_all_keeps_all`, `test_retain_all_marks_conflict`

#### CS-005: highest_confidence Strategy

**Rule**: `highest_confidence` keeps only the conclusion with the
highest aggregated confidence per domain. Losers go to `conflicts`.
Tie-break: conclusion text ascending, then conclusion_id.

**Test**: `test_highest_keeps_winner`, `test_highest_drops_loser`,
`test_highest_tie_break`

#### CS-006: majority Strategy

**Rule**: `majority` keeps the conclusion with the most evidence
items per domain. Losers go to `conflicts`.
Tie-break: confidence descending, then conclusion text, then ID.

**Test**: `test_majority_keeps_majority`, `test_majority_drops_minority`,
`test_majority_tie_break_confidence`

#### CS-007: Confidence Aggregation

**Rule**: Base confidence = `max(evidence.confidence)` within a group.
Final confidence = `base + cross_system_bonus`, clamped to
`[min_confidence, max_confidence]`.

**Test**: `test_confidence_aggregation`

### Cross-System Bonus

#### CS-008: Bonus Applied

**Rule**: When 2+ distinct systems contribute to the same conclusion,
a bonus **MUST** be applied: `bonus = bonus_per_system * (system_count - 1)`.

**Test**: `test_bonus_multi_system`

#### CS-009: Bonus Capped

**Rule**: The total bonus **MUST NOT** exceed `max_cross_system_bonus`.

**Test**: `test_bonus_capped`

#### CS-010: Bonus Configurable

**Rule**: `cross_system_bonus_per_system` and `max_cross_system_bonus`
**MUST** be configurable via `ConsensusConfig`. Setting per_system to 0
disables the bonus.

**Test**: `test_bonus_configurable`, `test_bonus_zero_disabled`

### Sorting

#### CS-011: Domain Sorting

**Rule**: `ConsensusReport.domains` **MUST** be sorted alphabetically
by `Domain` enum value.

**Test**: `test_domain_sorting`

#### CS-012: Conclusion Sorting

**Rule**: `ConsensusReport.conclusions` **MUST** be sorted by:
1. Domain (ascending)
2. Confidence (descending)
3. Conclusion text (ascending)
4. Conclusion ID (ascending)

**Test**: `test_conclusion_by_domain`, `test_conclusion_by_confidence`,
`test_conclusion_by_text`

### Conflict Handling

#### CS-013: Conflict Detection

**Rule**: A conflict exists when 2+ conclusions share the same domain.
The conflict strategy determines which survive.

**Test**: `test_same_domain_diff_conclusion_conflict`

#### CS-014: Conflict Marking

**Rule**: Conclusions involved in a conflict **MUST** have
`is_conflict=True`. Non-conflicting conclusions have `is_conflict=False`.

**Test**: `test_retain_all_marks_conflict`, `test_single_no_conflict`

#### CS-015: Dropped Conclusions

**Rule**: For `highest_confidence` and `majority`, dropped conclusions
**MUST** appear in `ConsensusReport.conflicts` (not just disappear).
For `retain_all`, `conflicts` **MUST** be empty.

**Test**: `test_highest_drops_loser`, `test_majority_drops_minority`

### Null / Empty / Duplicate

#### CS-016: Empty Input

**Rule**: Empty `Evidence[]` **MUST** produce an empty `ConsensusReport`
with `overall_confidence=0.0`, empty conclusions, conflicts, domains,
and evidence_ids.

**Test**: `test_empty_input`

#### CS-017: Duplicate Evidence Dedup

**Rule**: Evidence with duplicate `evidence_id` **MUST** be deduplicated
(keep first occurrence).

**Test**: `test_dedup_evidence`

#### CS-018: Duplicate Domain Handling

**Rule**: Multiple conclusions in the same domain are handled by the
conflict strategy. Each domain may produce 0-N conclusions.

**Test**: `test_same_domain_diff_conclusion_conflict`

#### CS-019: Duplicate Conclusion Handling

**Rule**: Evidence with the same `(domain, conclusion)` **MUST** be
merged into one conclusion with aggregated confidence and combined
evidence_ids.

**Test**: `test_groups_by_domain_conclusion`

### Determinism

#### CS-020: Deterministic Output

**Rule**: Same `ConsensusInput` **MUST** always produce byte-identical
`ConsensusReport` JSON, regardless of input order.

**Test**: `test_deterministic_build`, `test_deterministic_conclusion_id`

#### CS-021: Stable JSON

**Rule**: Serializing the same `ConsensusReport` twice **MUST** produce
identical JSON strings.

**Test**: `test_deterministic_json`

### Report Fields

#### CS-022: Overall Confidence

**Rule**: `overall_confidence` = average of surviving conclusion
confidences. If no conclusions, `0.0`.

**Test**: `test_overall_confidence`

#### CS-023: Evidence IDs Collected

**Rule**: `ConsensusReport.evidence_ids` **MUST** contain all consumed
Evidence IDs, sorted lexicographically.

**Test**: `test_evidence_ids_sorted`

#### CS-024: Report Required Fields

**Rule**: `ConsensusReport` **MUST** always contain: `report_id`,
`overall_confidence`, `domains`, `conclusions`, `conflicts`,
`evidence_ids`, `metadata`, `version`.

**Test**: `test_serialization` (TestConsensusReport)

### Architecture Boundary

#### CS-025: No Reasoning / Query Methods

**Rule**: `ConsensusBuilder` **MUST NOT** expose methods that call
RuleEngine, PatternMatcher, KnowledgeStore, or LLM. Forbidden method
names include: `reason`, `conclude`, `evaluate`, `evaluate_rule`,
`match_pattern`, `query_knowledge`, `call_llm`, `infer`.

**Test**: `test_no_reasoning_methods`, `test_methods_consensus_only`,
`test_does_not_modify_evidence`

---

## 3. Summary Table

| ID | Contract | Category |
|----|----------|----------|
| CS-001 | Input only accepts Evidence | Input Boundary |
| CS-002 | Non-Evidence rejected | Input Boundary |
| CS-003 | Evidence grouping by (domain, conclusion) | Aggregation |
| CS-004 | retain_all keeps all | Conflict Strategy |
| CS-005 | highest_confidence keeps winner | Conflict Strategy |
| CS-006 | majority keeps majority | Conflict Strategy |
| CS-007 | Confidence = max + bonus | Aggregation |
| CS-008 | Cross-system bonus applied | Cross-System |
| CS-009 | Bonus capped | Cross-System |
| CS-010 | Bonus configurable | Cross-System |
| CS-011 | Domain sorting | Sorting |
| CS-012 | Conclusion sorting | Sorting |
| CS-013 | Conflict detection | Conflict |
| CS-014 | Conflict marking | Conflict |
| CS-015 | Dropped conclusions in conflicts list | Conflict |
| CS-016 | Empty input -> empty report | Null/Empty |
| CS-017 | Duplicate evidence dedup | Duplicate |
| CS-018 | Duplicate domain handling | Duplicate |
| CS-019 | Duplicate conclusion merged | Duplicate |
| CS-020 | Deterministic output | Determinism |
| CS-021 | Stable JSON | Determinism |
| CS-022 | Overall confidence = average | Report |
| CS-023 | Evidence IDs sorted | Report |
| CS-024 | Report required fields | Report |
| CS-025 | No reasoning/query methods | Architecture |

**Total: 25 Consensus Behavior Contracts**

---

## 4. Immutability

All 25 contracts are immutable as of version 1.0.0. Modification
requires ACP + version bump + Golden Test update + contract regeneration.

---

## 5. Revision History

| Date | Version | Change |
|------|---------|--------|
| 2026-07-14 | 1.0.0 | Initial creation - 25 Consensus Behavior Contracts |
