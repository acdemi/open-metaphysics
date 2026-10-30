"""Export the FastAPI OpenAPI document to ``frontend/openapi.json``.

The snapshot is the single input of the frontend type generator
(``cd frontend && npm run gen:api``). It is written deterministically so that
regenerating it on an unchanged backend produces a byte-identical file, which
``tests/test_api_openapi_contract.py`` enforces.

Usage:
    uv run python scripts/export_openapi.py
"""

from __future__ import annotations

import json
from pathlib import Path

from openmetaphysics.api.app import app

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "frontend" / "openapi.json"


def render_openapi() -> str:
    """Deterministic serialisation of ``app.openapi()`` (sorted keys, 2-space indent)."""
    return json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> None:
    TARGET.write_text(render_openapi(), encoding="utf-8")
    print(f"wrote {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
