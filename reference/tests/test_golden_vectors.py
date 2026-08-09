"""Reference Qimen — 24 规范向量独立验收 (Phase 5.7 对齐 Sprint).

独立性: 本文件只依赖 reference.qimen 实现与 golden_vectors.json,
**禁止导入 src/openmetaphysics 任何模块** (含 Product Runtime 与 core)。

E016 (Evidence Ledger — 文本记录):
  id:      E016
  domain:  qimen (Reference)
  date:    2026-08-09
  status:  PASSED
  detail:  reference/qimen 自包含实现 (domain.py + astronomy.py, 无 src 导入)
           24/24 规范向量逐字节一致; 独立性由源码导入检查强制。
"""

import json
import re
from pathlib import Path

import pytest

from reference.qimen.domain import compute

ROOT = Path(__file__).resolve().parents[2]
VECTORS_PATH = ROOT / "docs" / "qimen" / "golden_vectors.json"

REFERENCE_SOURCES = [
    ROOT / "reference" / "qimen" / "domain.py",
    ROOT / "reference" / "qimen" / "astronomy.py",
]

_IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+openmetaphysics", re.MULTILINE)


def _load_vectors() -> list[dict]:
    return json.loads(VECTORS_PATH.read_text(encoding="utf-8"))["vectors"]


def test_reference_source_independent_of_src():
    """独立实现声明: Reference 源码不含任何 src/openmetaphysics 导入。"""
    for path in REFERENCE_SOURCES:
        text = path.read_text(encoding="utf-8")
        assert not _IMPORT_RE.search(text), f"{path.name} imports openmetaphysics"


def test_all_24_vectors_match():
    """24/24 规范向量逐字节一致 (核心验收)。"""
    vectors = _load_vectors()
    mismatched = [v["id"] for v in vectors if compute(v["input"]) != v["expected_board"]]
    assert not mismatched, f"reference mismatch: {mismatched}"
    assert len(vectors) == 24


@pytest.mark.parametrize("vector", _load_vectors(), ids=lambda v: v["id"])
def test_vector_regression(vector):
    """逐向量回归 (失败显式点名)。"""
    assert compute(vector["input"]) == vector["expected_board"]


def test_reference_deterministic():
    """同输入两次 → 逐字节一致 (QC-001)。"""
    for vector in _load_vectors()[:5]:
        assert compute(vector["input"]) == compute(vector["input"])
