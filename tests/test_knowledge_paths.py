"""H9 regression: knowledge/contract data must load after pip/Docker install.

The old code derived the corpus directory from ``Path(__file__).parents[3]``,
which only holds in a source checkout: inside a wheel/Docker image the package
lives in ``site-packages`` and the path pointed at nothing, so Explain silently
ran without citations. The resolver now uses ``OM_KNOWLEDGE_DIR`` /
``OM_REFERENCE_DIR``, bundled package data, an upward marker search for the
checkout, or the current directory -- never a fixed parents index.

Docker verification is documented in the H9 report; these tests cover the path
resolution itself, the fake "installed package" layout, the non-silent failure,
and the container smoke-check logic with mocked HTTP.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from openmetaphysics.core import paths
from openmetaphysics.core.config import reset_settings

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_FILES = ("ziwei_corpus.json", "bazi_corpus.json", "qimen_corpus.json", "liuyao_corpus.json")


def _write_corpus(directory: Path, names=DOMAIN_FILES) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in names:
        payload = {
            "metadata": {
                "corpus_id": name.removesuffix(".json"),
                "status": "Frozen",
                "version": "0.0.1",
                "counts": {"nodes": 1},
            },
            "nodes": [
                {
                    "id": f"{name}-node",
                    "name_cn": "甲",
                    "name_en": "jia",
                    "interpretation": "测试节点",
                    "node_type": "pattern",
                    "systems": ["ziwei"],
                    "tags": ["test"],
                    "source": {"text": "测试来源", "chapter": "第一章"},
                }
            ],
        }
        (directory / name).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


@pytest.fixture(autouse=True)
def _no_ambient_data_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OM_KNOWLEDGE_DIR", raising=False)
    monkeypatch.delenv("OM_REFERENCE_DIR", raising=False)
    reset_settings()
    yield
    reset_settings()


# -- resolution --------------------------------------------------------------


def test_source_checkout_is_found_by_marker_not_parents_index(tmp_path: Path):
    checkout = tmp_path / "moved-checkout"
    (checkout / "src" / "openmetaphysics" / "rag").mkdir(parents=True)
    (checkout / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    _write_corpus(checkout / "knowledge")

    rag_dir = checkout / "src" / "openmetaphysics" / "rag"
    # `start` is simulated as the module file position of a moved checkout
    assert paths.project_root(rag_dir) == checkout
    assert paths.knowledge_dir(start=rag_dir) == checkout / "knowledge"


def test_installed_package_layout_uses_bundled_data(tmp_path: Path, monkeypatch):
    site_packages = tmp_path / "site-packages"
    fake_pkg = site_packages / "openmetaphysics"
    (fake_pkg / "rag").mkdir(parents=True)
    _write_corpus(fake_pkg / "data" / "knowledge")
    monkeypatch.chdir(tmp_path)  # a wheel install has no repository layout

    resolved = paths.knowledge_dir(package_dir=fake_pkg, start=fake_pkg / "rag")
    assert resolved == fake_pkg / "data" / "knowledge"
    assert (resolved / "ziwei_corpus.json").is_file()
    # bundled data wins over the (incidentally present) source checkout
    assert resolved != ROOT / "knowledge"


def test_installed_layout_loads_corpus_from_bundled_data(tmp_path: Path, monkeypatch):
    from openmetaphysics.rag import corpus

    fake_pkg = tmp_path / "site-packages" / "openmetaphysics"
    (fake_pkg / "rag").mkdir(parents=True)
    _write_corpus(fake_pkg / "data" / "knowledge")
    monkeypatch.chdir(tmp_path)

    resolved = paths.knowledge_dir(package_dir=fake_pkg, start=fake_pkg / "rag")
    assert resolved is not None
    monkeypatch.setattr(corpus, "DEFAULT_CORPUS_PATH", resolved / "ziwei_corpus.json")

    chunks = corpus.load_all_chunks()
    assert chunks, "a bundled corpus in the installed layout must produce chunks"
    status = corpus.knowledge_status()
    assert status["available"] is True
    assert status["dir"] == str(resolved)
    assert status["missing"] == []


def test_om_knowledge_dir_env_drives_the_default_corpus(tmp_path: Path, monkeypatch):
    from openmetaphysics.rag import corpus

    installed = tmp_path / "opt" / "knowledge"
    _write_corpus(installed)
    monkeypatch.setenv("OM_KNOWLEDGE_DIR", str(installed))
    monkeypatch.chdir(tmp_path)
    reset_settings()

    try:
        module = importlib.reload(corpus)
        assert module.DEFAULT_CORPUS_PATH == installed / "ziwei_corpus.json"
        assert len(module.load_all_chunks()) >= 1
    finally:
        monkeypatch.delenv("OM_KNOWLEDGE_DIR", raising=False)
        reset_settings()
        importlib.reload(corpus)


def test_missing_om_knowledge_dir_warns_and_keeps_working(tmp_path: Path, monkeypatch, caplog):
    missing = tmp_path / "no-such-knowledge"
    monkeypatch.setenv("OM_KNOWLEDGE_DIR", str(missing))
    reset_settings()

    import logging

    with caplog.at_level(logging.WARNING):
        resolved = paths.knowledge_dir()

    assert any("OM_KNOWLEDGE_DIR" in record.message for record in caplog.records)
    # the source checkout still resolves, so a typo cannot break running from the repo
    assert resolved == ROOT / "knowledge"


# -- non-silent corpus failure ----------------------------------------------


def test_missing_corpus_logs_a_warning_in_the_default_retriever(
    tmp_path: Path, monkeypatch, caplog
):
    from openmetaphysics.rag import corpus, retriever

    monkeypatch.setattr(corpus, "DEFAULT_CORPUS_PATH", tmp_path / "missing" / "ziwei_corpus.json")
    retriever.reset_retriever()

    import logging

    with caplog.at_level(logging.WARNING):
        loaded = retriever.get_retriever()

    assert loaded.chunks == []
    assert any("knowledge corpora unavailable" in record.message for record in caplog.records)
    retriever.reset_retriever()


# -- frozen reference contracts ---------------------------------------------


def test_reference_contracts_resolve_from_om_reference_dir(tmp_path: Path, monkeypatch):
    from openmetaphysics.contracts import consensus_contract

    reference = tmp_path / "opt" / "reference"
    (reference / "contracts").mkdir(parents=True)
    (reference / "conformance" / "golden").mkdir(parents=True)
    (reference / "contracts" / "consensus_contract.json").write_text(
        json.dumps({"version": "1.0.0"}), encoding="utf-8"
    )
    (reference / "conformance" / "golden" / "consensus_vectors.json").write_text(
        "[]", encoding="utf-8"
    )
    monkeypatch.setenv("OM_REFERENCE_DIR", str(reference))
    reset_settings()

    try:
        module = importlib.reload(consensus_contract)
        assert module.CONTRACT_FILE == reference / "contracts" / "consensus_contract.json"
        assert module.VECTOR_FILE == (
            reference / "conformance" / "golden" / "consensus_vectors.json"
        )
        assert module.ConsensusContractAdapter().load_contract() == {"version": "1.0.0"}
    finally:
        monkeypatch.delenv("OM_REFERENCE_DIR", raising=False)
        reset_settings()
        importlib.reload(consensus_contract)


# -- container smoke check (mocked HTTP, no server needed) ------------------


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


def _fake_urlopen(*, corpora: bool = True, explanation: str = "mock explanation"):
    def _open(request, timeout=None):
        from urllib.request import Request

        assert isinstance(request, Request)
        url = request.full_url
        if url.endswith("/health"):
            return _FakeResponse({"status": "ok", "agents": ["bazi", "qimen", "ziwei", "liuyao"]})
        if url.endswith("/knowledge/corpora"):
            return _FakeResponse({"corpora": [{"corpus_id": "ziwei"}] if corpora else []})
        if url.endswith("/agents/bazi/compute"):
            return _FakeResponse({"agent": "bazi", "result": {}, "confidence": {}, "metadata": {}})
        if url.endswith("/agents/bazi/explain"):
            return _FakeResponse({"agent": "bazi", "explanation": explanation, "degraded": True})
        raise AssertionError(f"unexpected URL: {url}")

    return _open


def test_healthcheck_passes_with_health_corpora_and_explain(monkeypatch):
    from openmetaphysics import healthcheck

    monkeypatch.setattr(healthcheck, "urlopen", _fake_urlopen())
    assert healthcheck.main(["http://api:8000"]) == 0


def test_healthcheck_fails_when_the_knowledge_path_is_broken(monkeypatch, capsys):
    from openmetaphysics import healthcheck

    monkeypatch.setattr(healthcheck, "urlopen", _fake_urlopen(corpora=False))
    assert healthcheck.main(["http://api:8000"]) == 1
    assert "knowledge" in capsys.readouterr().err.lower()


def test_dockerfile_ships_data_and_the_smoke_healthcheck():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "COPY knowledge ./knowledge" in dockerfile
    assert "COPY reference ./reference" in dockerfile
    assert "OM_KNOWLEDGE_DIR=/app/knowledge" in dockerfile
    assert "OM_REFERENCE_DIR=/app/reference" in dockerfile
    assert "openmetaphysics.healthcheck" in dockerfile
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    assert "knowledge" not in dockerignore, "knowledge/ must stay in the build context"
    assert "reference" not in dockerignore, "reference/ must stay in the build context"
