"""H10 regression: honest knowledge evidence coverage + valid source YAML.

Review H10 found three problems:

* eight ``knowledge/sources/*.yaml`` files were actually Markdown tables and did
  not parse as YAML (``check-yaml`` would fail, but no test ever parsed them);
* most corpus nodes had no entry-level ``KnowledgeReference`` while
  ``knowledge/validate.py`` still printed a bare ``VALIDATION PASSED``;
* nothing registered the frozen corpus counts/digests, so silent corpus drift
  was possible.

These tests pin the fix: every source dossier is valid YAML, the registry covers
every citation label, the validator prints a real coverage report and refuses to
call itself a full-coverage pass, ``--strict`` fails every known gap, and the
frozen corpus register matches the artifacts on disk.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
DOMAINS = ("ziwei", "bazi", "qimen", "liuyao")

sys.path.insert(0, str(KNOWLEDGE))
import validate as validator  # noqa: E402  (path bootstrap above)


def _baseline() -> dict:
    return json.loads((KNOWLEDGE / "coverage_baseline.json").read_text(encoding="utf-8"))


def _registry() -> dict:
    return yaml.safe_load((KNOWLEDGE / "sources" / "registry.yaml").read_text(encoding="utf-8"))


def _corpus(domain: str) -> dict:
    return json.loads((KNOWLEDGE / f"{domain}_corpus.json").read_text(encoding="utf-8"))


# -- source files must be valid YAML ---------------------------------------


def test_every_source_dossier_is_valid_yaml_with_metadata():
    files = sorted((KNOWLEDGE / "sources").rglob("*.yaml"))
    assert len(files) == 9, f"expected 8 dossiers + registry, got {len(files)}"
    for path in files:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict), f"{path.name} is not a YAML mapping"
        if path.name == "registry.yaml":
            continue
        for key in ("source_id", "title", "evidence_status", "acquisition_status"):
            assert data.get(key), f"{path.name}: missing required source metadata {key}"


def test_registry_covers_every_dossier_and_every_citation_label():
    registry = _registry()
    assert registry["schema"] == "openmetaphysics.knowledge.sources.v1"
    entries = registry["sources"]
    titles = [entry["title"] for entry in entries]
    assert len(titles) == len(set(titles)), "duplicate source titles in registry"

    registered_files = {rel for entry in entries for rel in entry.get("files") or []}
    dossier_files = {
        path.relative_to(KNOWLEDGE / "sources").as_posix()
        for path in (KNOWLEDGE / "sources").rglob("*.yaml")
        if path.name != "registry.yaml"
    }
    assert dossier_files <= registered_files
    for rel in registered_files:
        assert (KNOWLEDGE / "sources" / rel).is_file(), f"missing dossier: {rel}"

    used: set[str] = set()
    for domain in DOMAINS:
        corpus = _corpus(domain)
        used |= {item["source"]["text"] for item in corpus["nodes"]}
        used |= {item["source"]["text"] for item in corpus["relations"]}
        used |= {item["source"]["text"] for item in corpus["references"]}
    assert used <= set(titles), f"unregistered citation labels: {sorted(used - set(titles))}"


# -- validator must not silently PASS --------------------------------------


def test_validator_default_passes_but_reports_registered_gaps():
    assert validator.validate() == []
    report = validator.coverage_report()
    totals = report["totals"]
    baseline = _baseline()

    assert totals["nodes"] == sum(data["nodes"] for data in report["domains"].values())
    assert totals["uncovered_nodes"] == sum(
        len(data["uncovered_nodes"]) for data in baseline["coverage"].values()
    )
    assert totals["uncovered_relations"] == sum(
        len(data["uncovered_relations"]) for data in baseline["coverage"].values()
    )
    # The real (unflattering) numbers are surfaced, not hidden behind PASS.
    assert totals["uncovered_nodes"] == 165
    assert totals["uncovered_relations"] == 222
    assert totals["references_attributed_source"] == 16


def test_validator_strict_gate_fails_every_known_gap():
    failures = validator.validate(strict=True)
    assert len(failures) >= 387, len(failures)
    assert any("no entry-level KnowledgeReference" in failure for failure in failures)
    assert any("no registered verbatim verification claim" in failure for failure in failures)
    assert any("no chapter/page anchor" in failure for failure in failures)


def _run_validator(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(KNOWLEDGE / "validate.py"), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_validator_cli_prints_real_coverage_report_and_qualified_pass():
    proc = _run_validator()
    assert proc.returncode == 0, proc.stderr
    assert "KNOWLEDGE COVERAGE REPORT" in proc.stdout
    assert "entry-level reference gaps: 165 nodes / 222 relations" in proc.stdout
    assert "NOT a full-coverage claim" in proc.stdout
    # the old bare PASS string must be gone
    assert "PASSED: all corpus entries conform" not in proc.stdout


def test_validator_cli_strict_exits_nonzero():
    proc = _run_validator("--strict")
    assert proc.returncode == 1
    assert "VALIDATION FAILED" in proc.stdout


def test_invalid_yaml_registry_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "registry.yaml").write_text("sources: [\n", encoding="utf-8")
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    entries, failures = validator.load_source_registry()
    assert entries == {}
    assert any("not valid YAML" in failure for failure in failures)


# -- frozen corpus register -------------------------------------------------


def test_frozen_corpus_register_matches_the_artifacts():
    baseline = _baseline()
    for domain in DOMAINS:
        info = baseline["corpora"][domain]
        raw = (KNOWLEDGE / f"{domain}_corpus.json").read_bytes()
        assert hashlib.sha256(raw).hexdigest() == info["sha256"], domain
        metadata = json.loads(raw)["metadata"]
        assert metadata["counts"] == info["counts"], domain
        assert metadata["source_digests"] == info["source_digests"], domain
        assert metadata["status"] == info["status"] and metadata["version"] == info["version"]


def test_precommit_runs_check_yaml_and_the_knowledge_validator():
    config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    hook_ids = {hook["id"] for repo in config["repos"] for hook in repo["hooks"]}
    assert "check-yaml" in hook_ids
    assert "knowledge-validate" in hook_ids
