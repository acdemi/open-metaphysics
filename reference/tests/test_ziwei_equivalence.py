"""Ziwei Reference equivalence tests (Phase 6.7.4).

Verifies for all 24 golden vectors:
- Reference output == expected chart, exact structural equality
  (fate/body palace, yin_yang, wuxing_ju, 12 palaces with all fields,
   calendar_note). No fuzzy matching, no field omission.
- Reference source independence: no openmetaphysics (src/) imports.
- Determinism and serialization stability of the reference engine.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from reference.ziwei import compute as ref_compute

REPO_ROOT = Path(__file__).resolve().parents[2]
VECTOR_FILE = REPO_ROOT / "docs" / "ziwei" / "golden_vectors.json"
REFERENCE_DIR = REPO_ROOT / "reference" / "ziwei"


def _vectors() -> list[dict]:
    return json.loads(VECTOR_FILE.read_text(encoding="utf-8"))["vectors"]


def _reference(v: dict) -> dict:
    return ref_compute(v["input"])


def test_reference_independent_of_production() -> None:
    """Reference modules must not import openmetaphysics (src/)."""
    src_pattern = re.compile(r"(^|\s)(from|import)\s+openmetaphysics")
    offenders: list[str] = []
    for path in sorted(REFERENCE_DIR.rglob("*.py")):
        if any(part in ("__pycache__",) for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        if src_pattern.search(text):
            offenders.append(str(path))
    assert not offenders, f"src imports found in: {offenders}"

    # runtime check in a clean subprocess: importing reference.ziwei must
    # not pull any openmetaphysics (src/) module into sys.modules
    import os
    import subprocess

    code = (
        "import sys; "
        "from reference.ziwei import compute; "
        "assert 'openmetaphysics' not in sys.modules, 'src imported'"
    )
    env = dict(
        os.environ,
        PYTHONPATH=os.pathsep.join([str(REPO_ROOT / "src"), str(REPO_ROOT / "reference")]),
    )
    subprocess.run(
        [sys.executable, "-c", code], check=True, capture_output=True, text=True, env=env
    )


def test_24_golden_vectors_equivalent() -> None:
    vectors = _vectors()
    assert len(vectors) == 24
    for v in vectors:
        got = _reference(v)
        assert got == v["expected"]["chart"], f"{v['id']}: reference output != expected chart"


def test_determinism_reference() -> None:
    for v in _vectors():
        first = _reference(v)
        second = _reference(v)
        assert first == second, f"{v['id']}: reference not deterministic"


def test_serialization_stable_reference() -> None:
    for v in _vectors():
        got = _reference(v)
        canonical = json.dumps(got, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        again = (
            json.dumps(json.loads(canonical), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        )
        assert again == canonical, f"{v['id']}: serialization not stable"
