"""Reference Qimen Domain 验收测试 (自主 Sprint 5.9B).

验收标准: reference/qimen 实现输出与 24 规范向量 expected_board 逐字节一致。
E015 (Evidence Ledger — 文本记录):
  id:      E015
  domain:  qimen (Reference)
  date:    2026-08-09
  status:  PASSED
  detail:  reference/qimen 实现依契约 v1.0.0, 24/24 规范向量逐字节一致,
           与 Product Runtime 输出一致 (双实现互证 + 规范装置仲裁)。
           本模块即自动执行证据 (每次 pytest 重放)。
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from openmetaphysics.agents.qimen import QimenAgent, QimenInput
from openmetaphysics.core.schemas import GeoPoint
from reference.qimen.domain import compute

ROOT = Path(__file__).resolve().parent.parent
VECTORS_PATH = ROOT / "docs" / "qimen" / "golden_vectors.json"


def _load_vectors() -> list[dict]:
    return json.loads(VECTORS_PATH.read_text(encoding="utf-8"))["vectors"]


def _reference_compute(vector: dict) -> dict:
    return compute(vector["input"])


def test_reference_matches_all_24_vectors():
    """24/24 向量逐字节一致 (核心验收)。"""
    vectors = _load_vectors()
    mismatched = []
    for v in vectors:
        if _reference_compute(v) != v["expected_board"]:
            mismatched.append(v["id"])
    assert not mismatched, f"reference mismatch: {mismatched}"
    assert len(vectors) == 24


@pytest.mark.parametrize("vector", _load_vectors(), ids=lambda v: v["id"])
def test_reference_vector_regression(vector):
    """逐向量回归 (失败显式点名)。"""
    assert compute(vector["input"]) == vector["expected_board"]


def test_reference_deterministic():
    """相同输入两次 → 输出一致 (QC-001)。"""
    for v in _load_vectors()[:5]:
        assert compute(v["input"]) == compute(v["input"])


def test_reference_matches_product_runtime():
    """Reference 与 Product Runtime 双实现互证 (规范装置仲裁)。"""
    vectors = _load_vectors()
    for v in vectors:
        inp = dict(v["input"])
        inp["born_at"] = datetime.fromisoformat(inp["born_at"])
        inp["born_location"] = GeoPoint(**inp["born_location"])
        payload = QimenInput.model_validate(inp)
        runtime_board = QimenAgent().compute(payload).result.model_dump(mode="json")
        assert runtime_board == v["expected_board"], f"runtime drift: {v['id']}"
        assert runtime_board == compute(v["input"]), f"reference vs runtime: {v['id']}"


def test_reference_deterministic_seeded_sample():
    """固定种子抽样: reference 与 runtime 输出一致 (除向量外更多输入)。"""
    import random

    rng = random.Random(2024)
    from zoneinfo import ZoneInfo

    sh = ZoneInfo("Asia/Shanghai")
    for i in range(30):
        dt = datetime(2024, 1, 1, 0, 0, tzinfo=sh) + __import__("datetime").timedelta(
            days=rng.randrange(0, 365), hours=rng.randrange(0, 24)
        )
        payload = {
            "request_id": f"ref{i}",
            "born_at": dt.isoformat(),
            "gender": "unknown",
            "born_location": {"latitude": 39.9, "longitude": 116.4, "timezone": "Asia/Shanghai"},
        }
        reference_board = compute(payload)
        runtime_board = (
            QimenAgent()
            .compute(
                QimenInput.model_validate(
                    {
                        "request_id": f"ref{i}",
                        "born_at": dt,
                        "gender": "unknown",
                        "born_location": GeoPoint(
                            latitude=39.9, longitude=116.4, timezone="Asia/Shanghai"
                        ),
                    }
                )
            )
            .result.model_dump(mode="json")
        )
        assert reference_board == runtime_board, f"sample {i} mismatch"
