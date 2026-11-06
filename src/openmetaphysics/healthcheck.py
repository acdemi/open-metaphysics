"""Container/local smoke check: ``/health``, ``/knowledge/corpora`` and Explain.

Used as the Docker ``HEALTHCHECK`` and runnable by hand. It stays fully offline:
the Explain call uses the deterministic fallback path when no provider is
configured, so the image does not need an LLM to pass its own health check.

Usage::

    python -m openmetaphysics.healthcheck [base_url]

Base URL defaults to ``OM_BASE_URL`` (``http://127.0.0.1:8000``).
Exit code 0 = healthy; 1 = at least one check failed (details on stderr).
"""

from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
_SMOKE_BORN_AT = "1990-06-15T10:30:00+08:00"


def _request(base_url: str, path: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"} if data else {}
    request = Request(f"{base_url}{path}", data=data, headers=headers)
    with urlopen(request, timeout=15) as response:  # noqa: S310 - fixed local base URL
        return json.loads(response.read().decode("utf-8"))


def _get(base_url: str, path: str) -> dict:
    return _request(base_url, path)


def _post(base_url: str, path: str, body: dict) -> dict:
    return _request(base_url, path, body)


def _check_health(base_url: str) -> list[str]:
    payload = _get(base_url, "/health")
    problems = []
    if payload.get("status") != "ok":
        problems.append(f"/health status={payload.get('status')!r}")
    if not payload.get("agents"):
        problems.append("/health returned no agents")
    return problems


def _check_knowledge(base_url: str) -> list[str]:
    payload = _get(base_url, "/knowledge/corpora")
    corpora = payload.get("corpora") or []
    if not corpora:
        return [
            "/knowledge/corpora is empty: knowledge corpora are not visible inside "
            "the container (set OM_KNOWLEDGE_DIR / check the image COPY)"
        ]
    return []


def _check_explain(base_url: str) -> list[str]:
    computed = _post(
        base_url,
        "/agents/bazi/compute",
        {
            "request_id": "docker-smoke",
            "born_at": _SMOKE_BORN_AT,
            "gender": "male",
        },
    )
    explained = _post(base_url, "/agents/bazi/explain", {"output": computed})
    if not str(explained.get("explanation") or "").strip():
        return ["/agents/bazi/explain returned an empty explanation"]
    if explained.get("agent") != "bazi":
        return [f"/agents/bazi/explain agent={explained.get('agent')!r}"]
    return []


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    base_url = (args[0] if args else os.environ.get("OM_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
    problems: list[str] = []
    for name, check in (
        ("health", _check_health),
        ("knowledge", _check_knowledge),
        ("explain", _check_explain),
    ):
        try:
            problems.extend(check(base_url))
        except HTTPError as exc:  # pragma: no cover - network environment
            problems.append(f"{name}: HTTP {exc.code} {exc.reason}")
        except (URLError, OSError) as exc:  # pragma: no cover - network environment
            problems.append(f"{name}: unreachable ({exc})")
        except Exception as exc:  # pragma: no cover - defensive
            problems.append(f"{name}: {type(exc).__name__}: {exc}")

    if problems:
        print("healthcheck FAILED:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"healthcheck OK ({base_url})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
