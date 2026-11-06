"""H11/H12 regression: conformance is read-only and does not overclaim.

Review H11 found that ``ConformanceRunner.run()`` rewrote the frozen golden
vectors through ``_check_golden_reproducibility`` (a drifted vector could be
silently "repaired"), and that four per-vector checks were hardcoded
``passed=True``. Review H12 found "Certified" wording that did not match the
check strength.

These tests pin:

* the golden files' bytes **and mtimes** are unchanged by a conformance run;
* the run performs no writes at all (``Path.write_text`` is poisoned);
* an empty golden directory is NOT auto-generated (read-only failure instead);
* derived checks are ``skipped`` (not fake passes) and enum checks are real
  property checks, with negative controls;
* contract-diff and architecture-boundary checks have real negative controls;
* ``certified`` requires a full-strength pass, while ``contract_conformant``
  records "failed=0 with partial/skipped checks".
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from reference.conformance import (
    CheckStatus,
    ConformanceCategory,
    ConformanceCheckResult,
    ConformanceLayer,
    ConformanceResult,
    GoldenVector,
)
from reference.conformance_runner import (
    CONTRACTS_DIR,
    GOLDEN_DIR,
    ConformanceRunner,
    ReferenceAdapter,
    build_golden_vectors,
    generate_golden_vectors,
    serialize_golden_vectors,
)


def _golden_snapshot(directory: Path | None = None) -> dict[str, tuple[str, int]]:
    directory = directory or GOLDEN_DIR
    return {
        path.name: (hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns)
        for path in sorted(directory.glob("*_vectors.json"))
    }


def _check(result: ConformanceResult, check_id: str) -> ConformanceCheckResult:
    matches = [c for c in result.checks if c.check_id == check_id]
    assert len(matches) == 1, f"{check_id}: {len(matches)} checks"
    return matches[0]


# -- read-only ---------------------------------------------------------------


def test_run_does_not_modify_golden_files():
    before = _golden_snapshot()
    assert before, "golden vectors must exist"
    ConformanceRunner().run(ReferenceAdapter(), "reference", "1.0.0")
    assert _golden_snapshot() == before, "conformance run rewrote the frozen golden files"


def test_run_performs_no_file_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    golden_dir = tmp_path / "golden"
    golden_dir.mkdir()
    for path in GOLDEN_DIR.glob("*_vectors.json"):
        (golden_dir / path.name).write_bytes(path.read_bytes())

    def _forbidden(*args, **kwargs):  # pragma: no cover - only on failure
        raise AssertionError("conformance must not write files")

    monkeypatch.setattr(Path, "write_text", _forbidden)
    result = ConformanceRunner(golden_dir=golden_dir).run(ReferenceAdapter(), "reference", "1.0.0")
    assert result.failed == 0
    assert sorted(p.name for p in golden_dir.glob("*_vectors.json")) == sorted(
        p.name for p in GOLDEN_DIR.glob("*_vectors.json")
    )


def test_empty_golden_dir_is_not_auto_generated(tmp_path: Path):
    golden_dir = tmp_path / "empty-golden"
    golden_dir.mkdir()
    result = ConformanceRunner(golden_dir=golden_dir).run(ReferenceAdapter(), "reference", "1.0.0")

    assert list(golden_dir.iterdir()) == [], "runner must not generate golden vectors"
    assert result.certified is False
    assert _check(result, "CF-GOLDEN-MISSING").status == CheckStatus.FAILED
    assert _check(result, "CF-018").status == CheckStatus.FAILED


def test_serialized_golden_matches_disk_without_writing():
    serialized = serialize_golden_vectors(build_golden_vectors())
    on_disk = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(GOLDEN_DIR.glob("*_vectors.json"))
    }
    assert serialized == on_disk
    result = ConformanceRunner().run(ReferenceAdapter(), "reference", "1.0.0")
    assert _check(result, "CF-018").status == CheckStatus.PASSED
    assert "read-only" in _check(result, "CF-018").message


def test_explicit_generator_still_writes_tooling_output(tmp_path: Path):
    output = tmp_path / "generated"
    generate_golden_vectors(output)
    assert sorted(p.name for p in output.glob("*_vectors.json")) == sorted(
        p.name for p in GOLDEN_DIR.glob("*_vectors.json")
    )
    for path in sorted(GOLDEN_DIR.glob("*_vectors.json")):
        assert (output / path.name).read_bytes() == path.read_bytes()


# -- truthful check statuses -------------------------------------------------


def test_derived_checks_are_skipped_not_passed():
    result = ConformanceRunner().run(ReferenceAdapter(), "reference", "1.0.0")
    derived = [
        c
        for c in result.checks
        if c.category
        in (
            ConformanceCategory.STABLE_ORDERING,
            ConformanceCategory.DETERMINISTIC_HASH,
            ConformanceCategory.NULL_HANDLING,
        )
    ]
    assert derived, "derived checks must still be reported (as skipped)"
    for check in derived:
        assert check.status == CheckStatus.SKIPPED
        assert check.passed is False
        assert "not independently" in check.message.lower() or "H11" in check.message


def test_enum_check_is_a_real_property_check():
    runner = ConformanceRunner()
    vector = GoldenVector(vector_id="gv:test:enum", layer=ConformanceLayer.RULE, name="enum-probe")

    valid = ConformanceResult(runtime_name="x", runtime_version="1")
    runner._check_enum('{"node_type": "shen_sha", "relation_type": "ke"}', vector, valid)
    assert _check(valid, "CF-ENUM-gv:test:enum").status == CheckStatus.PASSED

    invalid = ConformanceResult(runtime_name="x", runtime_version="1")
    runner._check_enum('{"node_type": "not_a_node_type"}', vector, invalid)
    assert _check(invalid, "CF-ENUM-gv:test:enum").status == CheckStatus.FAILED

    nullable = ConformanceResult(runtime_name="x", runtime_version="1")
    runner._check_enum('{"node_type": null}', vector, nullable)
    assert _check(nullable, "CF-ENUM-gv:test:enum").status == CheckStatus.PARTIAL

    absent = ConformanceResult(runtime_name="x", runtime_version="1")
    runner._check_enum('{"foo": 1}', vector, absent)
    assert _check(absent, "CF-ENUM-gv:test:enum").status == CheckStatus.PARTIAL


def test_contract_diff_is_a_real_model_diff(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = ConformanceRunner()
    ok = ConformanceResult(runtime_name="x", runtime_version="1")
    runner._check_contract_diff(ok)
    assert all(c.status == CheckStatus.PASSED for c in ok.checks), [
        c.message for c in ok.checks if c.status != CheckStatus.PASSED
    ]

    contract = json.loads((CONTRACTS_DIR / "rule_contract.json").read_text(encoding="utf-8"))
    contract["models"]["RuleCondition"]["required"].append("does_not_exist_field")
    bad_dir = tmp_path / "contracts"
    bad_dir.mkdir()
    (bad_dir / "rule_contract.json").write_text(json.dumps(contract), encoding="utf-8")
    monkeypatch.setattr("reference.conformance_runner.CONTRACTS_DIR", bad_dir)
    bad = ConformanceResult(runtime_name="x", runtime_version="1")
    runner._check_contract_diff(bad)
    diff_checks = [c for c in bad.checks if c.category == ConformanceCategory.CONTRACT_DIFF]
    assert diff_checks and diff_checks[0].status == CheckStatus.FAILED
    assert "does_not_exist_field" in diff_checks[0].message


def test_architecture_boundary_scans_adapter_source(monkeypatch: pytest.MonkeyPatch):
    runner = ConformanceRunner()
    ok = ConformanceResult(runtime_name="x", runtime_version="1")
    runner._check_architecture_boundary(ReferenceAdapter(), ok)
    assert _check(ok, "CF-ARCH-001").status == CheckStatus.PASSED
    assert "module source scanned" in _check(ok, "CF-ARCH-001").message

    fake_source = Path(__file__)
    forbidden_source = fake_source.parent / "conftest_forbidden_adapter_tmp.py"
    forbidden_source.write_text("import httpx\n\nclass Adapter:\n    pass\n", encoding="utf-8")
    try:
        monkeypatch.setattr(
            "reference.conformance_runner.inspect.getsourcefile", lambda cls: str(forbidden_source)
        )
        bad = ConformanceResult(runtime_name="x", runtime_version="1")
        runner._check_architecture_boundary(ReferenceAdapter(), bad)
        assert _check(bad, "CF-ARCH-001").status == CheckStatus.FAILED
    finally:
        forbidden_source.unlink(missing_ok=True)


# -- certification semantics -------------------------------------------------


def test_certification_requires_full_strength():
    passed = ConformanceResult(runtime_name="x", runtime_version="1", behavior_coverage=1.0)
    passed.add_check(
        ConformanceCheckResult(
            check_id="c1",
            category=ConformanceCategory.GOLDEN_JSON,
            name="n",
            passed=True,
            status=CheckStatus.PASSED,
        )
    )
    assert passed.certified is True
    assert passed.contract_conformant is True

    partial = ConformanceResult(runtime_name="x", runtime_version="1", behavior_coverage=1.0)
    partial.add_check(
        ConformanceCheckResult(
            check_id="c1",
            category=ConformanceCategory.GOLDEN_JSON,
            name="n",
            passed=False,
            status=CheckStatus.SKIPPED,
        )
    )
    assert partial.failed == 0
    assert partial.skipped == 1
    assert partial.certified is False
    assert partial.coverage == 0.0
    assert partial.contract_conformant is True

    failing = ConformanceResult(runtime_name="x", runtime_version="1", behavior_coverage=1.0)
    failing.add_check(
        ConformanceCheckResult(
            check_id="c1",
            category=ConformanceCategory.GOLDEN_JSON,
            name="n",
            passed=False,
            status=CheckStatus.FAILED,
        )
    )
    assert failing.contract_conformant is False


def test_status_derivation_keeps_passed_consistent():
    plain_pass = ConformanceCheckResult(
        check_id="c1", category=ConformanceCategory.GOLDEN_JSON, name="n", passed=True
    )
    assert plain_pass.status == CheckStatus.PASSED and plain_pass.passed is True

    forced_skip = ConformanceCheckResult(
        check_id="c2",
        category=ConformanceCategory.GOLDEN_JSON,
        name="n",
        passed=True,
        status=CheckStatus.SKIPPED,
    )
    assert forced_skip.passed is False
