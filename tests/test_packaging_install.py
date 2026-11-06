"""Wheel install path regression (P2.5, slow; nightly job).

The source tree is built into a wheel (via ``uv build --wheel``) and installed
into a throwaway venv with ``pip install <wheel>``. This is the same artifact a
PyPI/Docker user receives, without relying on the checkout for imports.

Assertions (both modes):

* ``knowledge/`` corpora resolve when run **from the checkout** without
  ``OM_KNOWLEDGE_DIR`` (upward marker search fallback);
* corpora + all five frozen contracts resolve when ``OM_KNOWLEDGE_DIR`` /
  ``OM_REFERENCE_DIR`` point outside the checkout (wheel/Docker mode);
* the installed distribution exposes the documented console entry points.

Marked ``slow`` so PR CI (``pytest -m "not slow"``) stays fast; nightly runs it
and uploads logs on failure. Subprocess output is included in assertions.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import venv
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

CHECK_SCRIPT = r"""
import json
import os
import sys
from pathlib import Path

# Offline runtime deps: the module-level PYTHONPATH points at the host venv's
# site-packages. Move that entry to the END of sys.path so the wheel installed
# into this venv wins for ``openmetaphysics`` while dependencies still resolve.
host_site = os.environ.get("OM_TEST_HOST_SITE") or ""

def _norm(path: str) -> str:
    return os.path.normcase(os.path.realpath(path))

if host_site:
    host_norm = _norm(host_site)
    sys.path = [p for p in sys.path if _norm(p) != host_norm] + [host_site]

import openmetaphysics
from openmetaphysics.core.paths import knowledge_dir, reference_dir
from openmetaphysics.rag.corpus import corpus_stats, knowledge_status, load_corpus

module_path = Path(openmetaphysics.__file__).resolve()
assert module_path.is_relative_to(Path(sys.prefix).resolve()), module_path
knowledge = knowledge_dir()
reference = reference_dir()
assert knowledge is not None, "knowledge_dir() resolved to None"
assert reference is not None, "reference_dir() resolved to None"
assert (knowledge / "ziwei_corpus.json").is_file(), f"missing corpus under {knowledge}"
contracts = reference / "contracts"
names = sorted(p.name for p in contracts.glob("*.json"))
assert len(names) == 5, f"expected 5 frozen contracts, found {names}"
for name in names:
    json.loads((contracts / name).read_text(encoding="utf-8"))
status = knowledge_status()
assert status["available"] and not status["missing"], status
stats = corpus_stats()
assert len(stats) == 4, f"expected 4 domain corpora, found {stats}"
assert all(item.get("status") == "frozen" for item in stats), stats
raw = load_corpus()
assert isinstance(raw, dict) and raw, "load_corpus() returned an empty mapping"
print(json.dumps({
    "knowledge_dir": str(knowledge),
    "reference_dir": str(reference),
    "contracts": names,
    "corpora": len(stats),
    "module": str(module_path),
}, ensure_ascii=False))
"""

IMPORT_SCRIPT = r"""
import os
import sys

host_site = os.environ.get("OM_TEST_HOST_SITE") or ""

def _norm(path: str) -> str:
    return os.path.normcase(os.path.realpath(path))

if host_site:
    host_norm = _norm(host_site)
    sys.path = [p for p in sys.path if _norm(p) != host_norm] + [host_site]

import openmetaphysics.api.app  # noqa: F401
print("import ok")
"""


def _host_site_packages() -> str:
    import sysconfig

    return sysconfig.get_paths()["purelib"]


def _run(
    cmd: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: int = 600,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def _clean_env() -> dict[str, str]:
    env = dict(os.environ)
    for name in ("PYTHONPATH", "PYTHONHOME", "OM_KNOWLEDGE_DIR", "OM_REFERENCE_DIR"):
        env.pop(name, None)
    # Runtime deps come from the host venv; CHECK_SCRIPT/IMPORT_SCRIPT move this
    # entry to the end of sys.path so the wheel in the temp venv takes priority.
    host_site = _host_site_packages()
    env["OM_TEST_HOST_SITE"] = host_site
    env["PYTHONPATH"] = host_site
    return env


def _venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


@pytest.fixture(scope="module")
def built_wheel(tmp_path_factory: pytest.TempPathFactory) -> Path:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is required to build the wheel for the install test")
    out_dir = tmp_path_factory.mktemp("wheel-dist")
    env = _clean_env()
    # Keep uv's cache inside the test sandbox: the shared user cache may be
    # read-only in CI/container environments.
    env["UV_CACHE_DIR"] = str(tmp_path_factory.mktemp("uv-cache"))
    env["UV_LINK_MODE"] = "copy"
    build = _run(
        [uv, "build", "--wheel", "--out-dir", str(out_dir)],
        cwd=ROOT,
        env=env,
        timeout=600,
    )
    assert build.returncode == 0, (
        f"uv build --wheel failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )
    wheels = sorted(out_dir.glob("*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"
    return wheels[0]


def _install_wheel(python: Path, wheel: Path, env: dict[str, str]) -> None:
    result = _run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--disable-pip-version-check",
            str(wheel),
        ],
        cwd=wheel.parent,
        env=env,
        timeout=300,
    )
    assert result.returncode == 0, (
        f"pip install <wheel> failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


@pytest.mark.slow
def test_pip_install_uses_checkout_and_configured_data_dirs(
    built_wheel: Path, tmp_path: Path
) -> None:
    venv_dir = tmp_path / "venv"
    venv.create(venv_dir, with_pip=True)
    python = _venv_python(venv_dir)
    env = _clean_env()
    _install_wheel(python, built_wheel, env)

    # (a) no OM_KNOWLEDGE_DIR: run from the checkout; the upward marker search
    # must find knowledge/ and reference/ even though the package is installed
    # in the venv's site-packages.
    fallback = _run([str(python), "-c", CHECK_SCRIPT], cwd=ROOT, env=env)
    assert fallback.returncode == 0, (
        "installed package could not resolve data from the checkout\n"
        f"stdout:\n{fallback.stdout}\nstderr:\n{fallback.stderr}"
    )
    fallback_payload = json.loads(fallback.stdout.strip().splitlines()[-1])
    assert Path(fallback_payload["knowledge_dir"]) == ROOT / "knowledge"
    assert Path(fallback_payload["reference_dir"]) == ROOT / "reference"

    # (b) configured dirs: copy data outside the checkout and point the
    # resolver at it (this is the wheel/Docker installation mode).
    data_root = tmp_path / "runtime-data"
    shutil.copytree(ROOT / "knowledge", data_root / "knowledge")
    shutil.copytree(ROOT / "reference" / "contracts", data_root / "reference" / "contracts")
    configured_env = dict(env)
    configured_env["OM_KNOWLEDGE_DIR"] = str(data_root / "knowledge")
    configured_env["OM_REFERENCE_DIR"] = str(data_root / "reference")

    configured = _run([str(python), "-c", CHECK_SCRIPT], cwd=tmp_path, env=configured_env)
    assert configured.returncode == 0, (
        "installed package could not resolve configured data dirs\n"
        f"stdout:\n{configured.stdout}\nstderr:\n{configured.stderr}"
    )
    payload = json.loads(configured.stdout.strip().splitlines()[-1])
    assert Path(payload["knowledge_dir"]) == data_root / "knowledge"
    assert Path(payload["reference_dir"]) == data_root / "reference"
    assert len(payload["contracts"]) == 5


@pytest.mark.slow
def test_installed_wheel_has_entry_points_and_importable_app(
    built_wheel: Path, tmp_path: Path
) -> None:
    venv_dir = tmp_path / "venv-cli"
    venv.create(venv_dir, with_pip=True)
    python = _venv_python(venv_dir)
    env = _clean_env()
    _install_wheel(python, built_wheel, env)

    check = _run(
        [str(python), "-c", IMPORT_SCRIPT],
        cwd=tmp_path,
        env=env,
        timeout=120,
    )
    assert check.returncode == 0, f"import failed:\n{check.stdout}\n{check.stderr}"
    assert "import ok" in check.stdout

    scripts = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    # Windows wrappers are ``<name>.exe``; POSIX wrappers have no suffix.
    installed = {p.stem for p in scripts.glob("openmetaphysics*")}
    expected = {"openmetaphysics", "openmetaphysics-cli", "openmetaphysics-mcp"}
    assert expected <= installed, f"missing console scripts: {sorted(expected - installed)}"
