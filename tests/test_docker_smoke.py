"""Docker image smoke test (P2.5, slow, nightly only; requires Docker daemon).

Builds the real image and verifies the packaged runtime data is visible:

1. ``docker exec ... python -m openmetaphysics.healthcheck`` — reuses the
   image's own HEALTHCHECK module (``/health`` + ``/knowledge/corpora`` +
   offline Explain fallback);
2. explicit ``/health`` and ``/knowledge/corpora`` HTTP checks;
3. a direct ``/agents/bazi/compute?explain=true`` call so the Explain chain is
   exercised end to end, not just via the healthcheck helper.

Marked ``slow`` + ``docker``: excluded from PR CI; nightly runs
``pytest -m "slow and docker"``. On failure the Docker build/run logs are
included in the assertion message so CI keeps the evidence.
"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import time
import uuid
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest

ROOT = Path(__file__).resolve().parents[1]
BORN = "1990-06-15T10:30:00+08:00"


def _run(cmd: list[str], *, timeout: int = 1800) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)


def _docker() -> str | None:
    executable = shutil.which("docker")
    if executable is None:
        return None
    try:
        probe = _run([executable, "info"], timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return executable if probe.returncode == 0 else None


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _get_json(url: str) -> dict:
    request = Request(url)
    with urlopen(request, timeout=15) as response:  # noqa: S310 - fixed localhost URL
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=60) as response:  # noqa: S310 - fixed localhost URL
        return json.loads(response.read().decode("utf-8"))


def _wait_for_health(base_url: str, timeout: float = 120.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            payload = _get_json(f"{base_url}/health")
            if payload.get("status") == "ok":
                return
        except (URLError, OSError, ValueError) as exc:
            last_error = exc
        time.sleep(2)
    raise AssertionError(f"/health not ready within {timeout}s: {last_error!r}")


@pytest.mark.slow
@pytest.mark.docker
def test_docker_image_healthcheck_and_smoke() -> None:
    docker = _docker()
    if docker is None:
        pytest.skip("Docker binary/daemon unavailable; Docker smoke runs in nightly CI")

    tag = f"openmetaphysics:p2-smoke-{uuid.uuid4().hex[:8]}"
    container = f"om-p2-smoke-{uuid.uuid4().hex[:8]}"
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"

    build = _run([docker, "build", "--progress=plain", "-t", tag, str(ROOT)], timeout=1800)
    if build.returncode != 0:
        pytest.fail(f"docker build failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}\n")

    run = _run(
        [
            docker,
            "run",
            "-d",
            "--name",
            container,
            "-p",
            f"127.0.0.1:{port}:8000",
            tag,
        ],
        timeout=120,
    )
    if run.returncode != 0:
        pytest.fail(f"docker run failed:\n{run.stdout}\n{run.stderr}")

    try:
        _wait_for_health(base_url)

        health = _get_json(f"{base_url}/health")
        assert health["status"] == "ok"
        assert sorted(health["agents"]) == ["bazi", "liuyao", "qimen", "ziwei"]

        corpora = _get_json(f"{base_url}/knowledge/corpora")["corpora"]
        assert corpora, "/knowledge/corpora is empty inside the image"

        smoke = _run(
            [
                docker,
                "exec",
                container,
                "python",
                "-m",
                "openmetaphysics.healthcheck",
            ],
            timeout=120,
        )
        assert smoke.returncode == 0, (
            "in-image `python -m openmetaphysics.healthcheck` failed\n"
            f"stdout:\n{smoke.stdout}\nstderr:\n{smoke.stderr}"
        )
        assert "healthcheck OK" in smoke.stdout

        computed = _post_json(
            f"{base_url}/agents/bazi/compute?explain=true",
            {"request_id": "p2-docker-smoke", "born_at": BORN, "gender": "male"},
        )
        assert computed["agent"] == "bazi"
        assert computed["result"], "compute returned an empty result"
        explain = computed.get("explain") or {}
        assert str(explain.get("explanation") or "").strip(), (
            "Explain returned an empty explanation"
        )
        assert explain.get("provider") is None, "Docker smoke must stay offline (no provider)"
    except Exception as exc:  # keep container logs in the failure message
        logs = _run([docker, "logs", container], timeout=60)
        pytest.fail(
            f"Docker smoke failed: {exc!r}\n--- docker logs ---\n{logs.stdout}\n{logs.stderr}\n"
        )
    finally:
        _run([docker, "rm", "-f", container], timeout=60)
        _run([docker, "rmi", "-f", tag], timeout=300)
