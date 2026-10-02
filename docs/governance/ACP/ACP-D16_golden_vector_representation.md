# ACP-D16 — Golden Vector Representation Semantics & ConformanceResult Field Documentation

> **Status**: **PROPOSED / DRAFT — PENDING HUMAN / CAO APPROVAL**
> **This ACP does not constitute implementation authorization.**
> **Type**: Reference / Conformance governance — independent decision item
> **Baseline**: `main @ de97fd7`

---

## §0 Governance Metadata

```text
document: ACP-D16 — Golden Vector Representation Semantics & ConformanceResult Field Documentation
project: ACIS
domain: Reference / Conformance
baseline: main @ de97fd7
binding_source: docs/governance/reference/D16_GOLDEN_VECTOR_ADJUDICATION.md
governance_input: docs/governance/reference/D16_GOLDEN_VECTOR_CLARIFICATION.md
decision_authority: CAO
status: DRAFTED — PENDING HUMAN / CAO APPROVAL
implementation_authorization: NONE (this ACP is a proposal only)
scope_items: D-16-A (CF-015 representation semantics), D-16-B (CONFORMANCE_SPEC §5 field documentation)
```

**Relationship of this document to the adjudication**: the adjudication record
(`D16_GOLDEN_VECTOR_ADJUDICATION.md`) is the authoritative source of the D-16 decisions.
This ACP is the **implementation-authorization vehicle** required by D-16-4. It does **not**
re-adjudicate, re-interpret, or re-open any D-16 decision.

---

## §1 Problem / Governance Trigger

### 1.1 Trigger

`D16_GOLDEN_VECTOR_CLARIFICATION.md` established that CF-015
(`docs/specification/CONFORMANCE_SPEC.md` §4.15) requires:

> Each behavior contract **MUST** be represented by at least one golden vector.

while the P1-1 implementation represents the 52 required behavior IDs through an
**executable behavior representation** (bool-returning verification assertions resolved by
`ConformanceRunner._behavior_representation()`, `reference/conformance_runner.py:544`),
not through entries in `reference/conformance/golden/*_vectors.json`.

The clarification recorded the terminology divergence and the frozen artifacts involved, and
left the matter as `REQUIRES HUMAN DECISION`.

### 1.2 Resolution already provided by the adjudication

The CAO adjudicated D-16-1 = **ALLOW**, establishing the interpretation that closes the
divergence, and separately required (D-16-5) that two already-existing implementation fields be
formally described in the frozen specification — which itself requires an ACP.

### 1.3 What this ACP therefore must accomplish

Two, and only two, implementation-authorization proposals:

| Item | Subject |
|------|---------|
| **D-16-A** | Land the D-16-1 interpretation in the appropriate normative / governance carrier |
| **D-16-B** | Formally describe `behavior_coverage` and `unrepresented_behaviors` in `CONFORMANCE_SPEC.md` §5 |

---

## §2 Existing Adjudication Binding

The following are **binding recorded facts**, reproduced from
`docs/governance/reference/D16_GOLDEN_VECTOR_ADJUDICATION.md`. This ACP does not restate their
rationale and does not alter them.

```text
D-16-1 = ALLOW
D-16-2 = N/A
D-16-3 = N/A
D-16-4 = INDEPENDENT D-16 ACP
D-16-5 = ADD TO CONFORMANCE_SPEC §5
         (ACP required; version impact NOT PREJUDGED)
```

Recorded governance state (adjudication §0 §9):

```text
D-16 DECISION REACHED
D-16 IMPLEMENTATION NOT YET AUTHORIZED
P1-1 = UNCHANGED
P2 = NOT STARTED / BLOCKED
```

**The ACP is an implementation authorization proposal.**
**The ACP itself does not constitute implementation authorization.**

D-16-1 is already decided as `ALLOW`; it is **not** re-argued, **not** re-opened, and the
Option A / Option B representation alternatives are **not** re-proposed here.

---

## §3 Scope

This ACP covers exactly two deliverables.

### §3.1 D-16-A — CF-015 representation semantics (normative carrier)

Formalize, in the appropriate normative / governance carrier, the already-recorded
interpretation:

```text
CF-015 representation semantics
=
executable behavior representation
is an equivalent representation of a Behavior Contract
for CF-015 coverage purposes
```

and preserve, as binding boundaries:

```text
golden vector
≠ executable behavior representation

executable verifier
≠ traditional golden vector artifact

JSON golden-vector schema
UNCHANGED
```

### §3.2 D-16-B — `ConformanceResult` field documentation

Formally describe two **already-existing** implementation fields in
`docs/specification/CONFORMANCE_SPEC.md` §5:

```text
behavior_coverage
unrepresented_behaviors
```

---

## §4 Non-Scope

This ACP **explicitly does not** cover, authorize, or touch:

| Excluded | Note |
|----------|------|
| Golden vector schema redesign | `IMPLEMENTATION_GUIDE.md` §5 stays as-is |
| Golden vector generation changes | `generate_golden_vectors()` unchanged; CF-013 / CF-017 / CF-018 intact |
| New or regenerated golden vectors | `reference/conformance/golden/*.json` unchanged |
| `RuntimeAdapter` changes | the 6-method protocol is unchanged |
| P1-1 implementation changes | `reference/conformance.py`, `reference/conformance_runner.py`, `knowledge_behavior.py`, `consensus_behavior.py` unchanged |
| Field semantics changes / additional fields | D-16-B is documentation of existing fields only |
| `ConformanceManifest` | unchanged (§6 of the spec untouched) |
| Other conformance schemas | out of scope |
| `REFERENCE_RUNTIME_SPEC` §3.1 / §3.2 / §6.1 / §10 | belongs to ACP-REF-002 |
| `rule_contract.json` / `pattern_contract.json` | belongs to ACP-REF-002 |
| Reference Runtime registration / final freeze | belongs to ACP-REF-002 |
| `ACP-REF-002` itself | not modified by this ACP |
| `CAPABILITY_STATUS` / `PROJECT_STATUS` / `ROADMAP` | out of scope |
| **P2 / 六爻 Contractification** | **MUST NOT START** |

---

## §5 Proposed Specification Changes

> The following are **proposals for approval**. They are **not** applied by this ACP preparation.

### §5.1 D-16-A — proposed clarification clause

**Target**: `docs/specification/CONFORMANCE_SPEC.md`, §4.15 (CF-015) — appended to the existing
`**Normative**:` bullet list. **No existing sentence of CF-015 is modified or deleted.**

**Proposed text** (exact wording is an approval item):

```text
- Representation semantics (D-16 governance interpretation): the coverage
  requirement of this rule is satisfied when a Behavior Contract is represented
  by an executable behavior representation. The D-16 governance decision
  (docs/governance/reference/D16_GOLDEN_VECTOR_ADJUDICATION.md) establishes this
  as an EQUIVALENT representation for CF-015 coverage purposes. This clause does
  NOT redefine the JSON golden-vector schema (IMPLEMENTATION_GUIDE.md §5,
  CF-017, CF-018), and an executable verifier is NOT a traditional golden
  vector artifact.
```

**Carrier note**: the authoritative source of the interpretation remains the adjudication
record; the proposed clause is the normative cross-reference that makes it binding on future
conformance runs.

### §5.2 D-16-B — proposed `ConformanceResult` field rows

**Target**: `docs/specification/CONFORMANCE_SPEC.md` §5, the `ConformanceResult` field table.
**Proposed insertion point**: immediately after the existing `coverage` row (grouping the
coverage-related fields). **No existing row is modified or deleted.**

**Proposed rows** (exact wording is an approval item):

```text
| `behavior_coverage` | `float` | CF-015 behavior-contract coverage: executed representations / required IDs, range `[0.0, 1.0]` |
| `unrepresented_behaviors` | `list[str]` | CF-015 required behavior IDs that resolved to no executed representation (these are also emitted as failing checks) |
```

**Factual statement of record** (per D-16-B): both fields **already exist** in the frozen
implementation — `reference/conformance.py:81-82`, assigned at
`reference/conformance_runner.py:681-682`. This ACP proposes **documentation only**; it does not
change their semantics, does not add further fields, and does not modify P1-1.

---

## §6 Semantic / Terminology Constraints

This ACP inherits the terminology discipline of the adjudication (§2.2). The following
distinction is binding on the spec edit, the implementation, and all future evidence:

| Term | Meaning | NOT |
|------|---------|-----|
| **traditional golden vector artifact** | a JSON object in `reference/conformance/golden/{layer}_vectors.json`, per `IMPLEMENTATION_GUIDE.md` §5; generated by `generate_golden_vectors()` (CF-013), auto-discovered (CF-017), `expected_output` = exact canonical JSON produced by the adapter (CF-018) | — |
| **executable behavior representation** | a bool-returning executable verification assertion resolved per behavior ID | **not** a traditional golden vector artifact |
| **behavior coverage** | `ConformanceResult.behavior_coverage` = executed representations / required IDs | **not** a "golden vector coverage" measure in artifact terms |
| **supported_behaviors** | `ConformanceManifest` field listing behavior contract IDs covered | **does not** by itself satisfy CF-015 representation |

**Explicitly prohibited phrasings** (must not appear in the spec edit, implementation, evidence,
or reports):

```text
"the verifier is a golden vector"
"golden vector coverage = behavior coverage"
"supported_behaviors satisfies CF-015 representation"
"52 golden vectors exist"
"the executable verifier is one of the golden JSON artifacts"
```

The D-16 governance decision recognizes the executable behavior representation only as an
**EQUIVALENT representation** for CF-015 coverage purposes. The two are **different artifacts**.

---

## §7 Frozen Surface Impact

> Status labels record the governance boundary. **`CHANGE REQUIRED` does not mean "edit now".**

| Frozen surface | Status under this ACP | Note |
|----------------|----------------------|------|
| `docs/specification/CONFORMANCE_SPEC.md` §4.15 (CF-015) | **CHANGE REQUIRED** (after approval) | §5.1 proposed clarification clause; existing text unchanged |
| `docs/specification/CONFORMANCE_SPEC.md` §5 (field table) | **CHANGE REQUIRED** (after approval) | §5.2 proposed two rows |
| `docs/specification/CONFORMANCE_SPEC.md` other sections | **UNCHANGED** | not in scope |
| `docs/specification/CONFORMANCE_SPEC.md` §6 (`ConformanceManifest`) | **UNCHANGED** | explicitly excluded |
| `docs/specification/IMPLEMENTATION_GUIDE.md` §5 | **UNCHANGED** | JSON golden-vector schema preserved |
| `reference/conformance.py` | **UNCHANGED** | includes `GoldenVector`, `RuntimeAdapter`, `ConformanceResult` |
| `reference/conformance_runner.py` | **UNCHANGED** | includes `REQUIRED_BEHAVIOR_IDS`, `_behavior_representation`, `_check_behavior_coverage`, `certify` |
| `reference/knowledge_behavior.py` / `reference/consensus_behavior.py` | **UNCHANGED** | behavior verifiers untouched |
| `reference/conformance/golden/*.json` (19 vectors) | **UNCHANGED** | no new, no regeneration, no tagging |
| `docs/governance/ACP/ACP-REF-002_scope_expansion_and_contracts.md` | **NOT IN SCOPE / UNCHANGED** | independent governance item |
| `docs/governance/CAPABILITY_STATUS.md` / `PROJECT_STATUS.md` / `ROADMAP.md` | **NOT IN SCOPE** | — |
| P2 / 六爻 artifacts | **NOT IN SCOPE / MUST NOT START** | — |

**Current state**: no frozen artifact has been modified by this ACP preparation (see §13 audit).

---

## §8 Implementation Preconditions

Implementation may begin only when **all** of the following hold:

1. **This ACP is approved** (human / CAO) — including the exact wording in §5.1 and §5.2.
2. **The versioning decision point (§10) is resolved** for the specification change.
3. **The binding adjudication remains unchanged**: D-16-1 = ALLOW, D-16-4 = INDEPENDENT D-16 ACP,
   D-16-5 = ADD TO CONFORMANCE_SPEC §5.
4. **No absorption**: D-16 ACP-REF-002 scope separation (§11) is preserved.
5. **Terminology constraints (§6) are accepted** as binding on the edit.

Implementation will require a **controlled specification edit** limited to the two targets in
§5. It will **not** require any change to `reference/`, `tests/`, `src/`, golden vectors,
the generator, or `RuntimeAdapter`.

---

## §9 Validation / Evidence Requirements

Future implementation evidence must demonstrate, at minimum:

1. `CONFORMANCE_SPEC.md` §5 formally describes both fields.
2. The two field names in the specification match the already-existing implementation fields
   (`reference/conformance.py:81-82`).
3. Field semantics are **unchanged** (documentation only; no behavioural change).
4. Golden vector count and schema are **unmodified by D-16** (still the same files and the same
   schema per `IMPLEMENTATION_GUIDE.md` §5).
5. `RuntimeAdapter` was **not** extended by D-16-1 (still the 6-method protocol).
6. The P1-1 behavior representation mechanism was **not redefined** as a golden vector artifact.
7. D-16 and ACP-REF-002 remain **independently identifiable**.
8. **P2 was not started.**

Recorded baseline for evidence purposes (from the adjudication, not re-run here):

```text
Conformance: 170/170; REQUIRED_BEHAVIOR_IDS = 52; behavior_coverage = 1.0;
unrepresented_behaviors = []; certified = True; repository tests 627/627.
```

> Note: the 52/52 figure is a **behavior coverage** result. It does **not** mean that 52 golden
> vector artifacts exist.

---

## §10 Versioning Decision Point

```text
version impact is a decision point inside this ACP,
not a pre-adjudicated outcome.
```

Per D-16-5, the version impact is **NOT PREJUDGED**. During approval, the applicable
specification versioning rules (`docs/specification/CONTRACT_VERSIONING.md`) must be applied to
determine whether the §4.15 clarification and the §5 field documentation require a
`CONFORMANCE_SPEC` version increment. No version number is assumed or pre-selected by this draft.

**Approval item**: record the versioning outcome (increment required / not required, and the
resulting version) as part of approving this ACP.

---

## §11 Relationship to ACP-REF-002

```text
D-16 ACP = independent governance item
ACP-REF-002 = separate governance item
```

Allowed:

```text
same governance batch
```

Never:

```text
absorbed into ACP-REF-002
```

**Boundary**: ACP-REF-002 may be referenced **only as a dependency / coordination boundary**.
It is **not** part of this ACP's decision scope.

This ACP does **not** cover, and must not be used to carry:

```text
REFERENCE_RUNTIME_SPEC §3.1 / §3.2 / §6.1 / §10
rule_contract.json / pattern_contract.json
Reference Runtime registration
ACP-REF-002 scope expansion
Reference Runtime final freeze
any other contract decision unrelated to D-16
```

`ACP-REF-002` is **not modified** by this ACP preparation.

---

## §12 Approval Criteria

This ACP may be approved only if **all** criteria below are confirmed.

### Criterion A — D-16 semantic preservation

Confirmed that the executable behavior representation remains **only**:

```text
an EQUIVALENT representation for CF-015 coverage purposes
```

and is **not** a JSON golden vector.

### Criterion B — Golden schema preservation

Confirmed that none of the following is changed by this ACP:

```text
IMPLEMENTATION_GUIDE.md §5
CF-017
CF-018
reference/conformance/golden/*.json
```

### Criterion C — Field documentation

Confirmed that the following receive formal field descriptions in `CONFORMANCE_SPEC.md` §5:

```text
behavior_coverage
unrepresented_behaviors
```

### Criterion D — Scope containment

Confirmed that this ACP does **not** absorb:

```text
ACP-REF-002
Reference Runtime scope expansion
rule/pattern contract completion
P2
六爻 Contractification
```

### Criterion E — Versioning

Confirmed that the versioning outcome is recorded as a **decision inside this ACP**
(§10), not as a pre-adjudicated result.

---

## §13 STOP / Authorization Boundary

**Authorization boundary**

```text
This ACP is a proposal.
Approval of this ACP authorizes implementation of §5 only.
This ACP preparation itself performs no implementation.
```

**Prohibited until this ACP is approved**

```text
- modifying CONFORMANCE_SPEC.md (including CF-015 and §5)
- modifying IMPLEMENTATION_GUIDE.md
- modifying reference/ (including conformance.py / conformance_runner.py / behavior verifiers)
- modifying reference/conformance/golden/ (no new, no regeneration, no tagging)
- modifying generate_golden_vectors()
- modifying RuntimeAdapter
- modifying P1-1
- creating implementation plans, code patches, or test patches
- modifying ACP-REF-002
- modifying CAPABILITY_STATUS / PROJECT_STATUS / ROADMAP
- starting P2 / 六爻 Contractification
```

**STOP condition for this preparation**

After this draft is created and audited (§14 of the task), **STOP**. Do not self-approve this
ACP. Do not begin implementation. Do not enter P2.

---

## Appendix — Preparation Audit (read-only)

Performed at preparation time on `main @ de97fd7`:

```text
Modified:
ONLY docs/governance/ACP/ACP-D16_golden_vector_representation.md   (new file)

Frozen implementation modified: NONE
Specification modified:         NONE
Golden vectors modified:        NONE (19 vectors, unchanged)
ACP-REF-002 modified:           NONE
P2 artifacts created:           NONE
Tests:                          NOT RUN
```
