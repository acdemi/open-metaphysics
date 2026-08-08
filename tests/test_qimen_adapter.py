"""QimenContractAdapter 测试 (Phase 5.8B).

验证:
- 契约版本声明
- 输入字段完整性/范围拒绝
- 输出结构合规
- Golden Vector 回归验证 (行为与直接调用 runtime 一致)
"""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from openmetaphysics.agents.qimen import QimenAgent, QimenInput
from openmetaphysics.core.schemas import GeoPoint
from openmetaphysics.domain.qimen.adapter import QimenContractAdapter

ROOT = Path(__file__).resolve().parent.parent
VECTORS_PATH = ROOT / "docs" / "qimen" / "golden_vectors.json"
SHANGHAI = ZoneInfo("Asia/Shanghai")


def _load_vectors() -> list[dict]:
    return json.loads(VECTORS_PATH.read_text(encoding="utf-8"))["vectors"]


def _adapter() -> QimenContractAdapter:
    return QimenContractAdapter()


def _raw_from_vector(vector: dict) -> dict:
    """由规范向量输入构造原始 dict (year/month/day/hour)。"""
    born_at = datetime.fromisoformat(vector["input"]["born_at"])
    return {"year": born_at.year, "month": born_at.month, "day": born_at.day, "hour": born_at.hour}


def _make_input(raw: dict) -> QimenInput:
    return QimenInput(
        request_id="adapter",
        born_at=datetime(raw["year"], raw["month"], raw["day"], raw["hour"], tzinfo=SHANGHAI),
        gender="unknown",
        born_location=GeoPoint(latitude=39.9, longitude=116.4, timezone="Asia/Shanghai"),
    )


def test_adapter_contract_version_declaration():
    adapter = _adapter()
    assert adapter.contract_version == "1.0.0"
    status = adapter.get_contract_status()
    assert status["contract_version"] == "1.0.0"
    assert status["status"] == "Frozen"
    assert status["contract_id"] == "qimen:behavior:v1.0.0"
    assert status["engine_version"] == QimenAgent().engine_version


def test_adapter_rejects_missing_input_fields():
    adapter = _adapter()
    assert not adapter.validate_input({})
    assert not adapter.validate_input({"year": 2024, "month": 2, "day": 15})
    assert not adapter.validate_input({"year": 2024, "month": 2, "hour": 12})
    assert not adapter.validate_input({"year": 2024, "day": 15, "hour": 12})
    assert not adapter.validate_input({"month": 2, "day": 15, "hour": 12})
    assert not adapter.validate_input(None)
    assert not adapter.validate_input("2024-02-15")


def test_adapter_rejects_out_of_range_values():
    adapter = _adapter()
    valid = {"year": 2024, "month": 2, "day": 15, "hour": 12}
    for key, bad_values in {
        "year": [1899, 2101, "2024", 2024.5],
        "month": [0, 13, "2", 2.0],
        "day": [0, 32, "15", 15.0],
        "hour": [-1, 24, "12", 12.0],
    }.items():
        for bad in bad_values:
            raw = dict(valid)
            raw[key] = bad
            assert not adapter.validate_input(raw), f"{key}={bad!r} should be rejected"
    assert not adapter.validate_input(dict(valid, day=30, month=2))  # 2 月 30 日
    assert not adapter.validate_input(dict(valid, month=2, day=29, year=2023))  # 非闰年
    assert not adapter.validate_input(dict(valid, hour=True))  # bool 不是合法整数


def test_adapter_accepts_valid_golden_input():
    adapter = _adapter()
    vectors = _load_vectors()
    assert len(vectors) == 24
    hour_granular = 0
    for vector in vectors:
        raw = _raw_from_vector(vector)
        assert adapter.validate_input(raw), f"golden input rejected: {vector['id']}"
        # 行为不变: 经适配器校验的输入 → runtime 输出与直接调用一致。
        # 原始接口为小时粒度 (year/month/day/hour), 仅分钟为 0 的向量
        # 可由 raw dict 精确复现盘面。
        if datetime.fromisoformat(vector["input"]["born_at"]).minute == 0:
            direct = QimenAgent().compute(_make_input(raw)).result.model_dump(mode="json")
            assert direct == vector["expected_board"], f"behavior changed: {vector['id']}"
            hour_granular += 1
    assert hour_granular >= 19  # 24 向量中至少 19 个为整点输入


def test_adapter_verify_golden_vector():
    adapter = _adapter()
    vectors = _load_vectors()
    for vector in vectors[:5]:
        assert adapter.verify_golden_vector(vector), f"golden verify failed: {vector['id']}"
    # 篡改 expected_board → 必须失败
    tampered = dict(vectors[0])
    tampered["expected_board"] = dict(vectors[0]["expected_board"], ju=9)
    assert not adapter.verify_golden_vector(tampered)
    # 缺字段的向量 → 失败且不抛异常
    assert not adapter.verify_golden_vector({"id": "broken"})
    assert adapter.get_contract_status()["golden_vectors_verified"] == 5


def test_adapter_accepts_valid_output():
    adapter = _adapter()
    vectors = _load_vectors()
    for vector in vectors:
        assert adapter.validate_output(vector["expected_board"]), f"output rejected: {vector['id']}"


def test_adapter_rejects_invalid_output():
    adapter = _adapter()
    board = dict(_load_vectors()[0]["expected_board"])
    assert not adapter.validate_output({})
    assert not adapter.validate_output(dict(board, cells=board["cells"][:8]))  # 缺宫
    assert not adapter.validate_output(dict(board, ju=0))
    assert not adapter.validate_output(dict(board, ju="7"))
    assert not adapter.validate_output(dict(board, triple_offset=1))
    assert not adapter.validate_output(dict(board, dun_type="neutral"))
    # 宫位重复
    dup = json.loads(json.dumps(board))
    dup["cells"][1]["palace"] = dup["cells"][0]["palace"]
    assert not adapter.validate_output(dup)
    # 缺 cell 字段
    stripped = json.loads(json.dumps(board))
    stripped["cells"][0].pop("is_void")
    assert not adapter.validate_output(stripped)
