"""Qimen Contract Adapter 测试 (Phase 5.8 补齐, 自主工作).

验证 src/openmetaphysics/contracts/qimen_contract.py:
- schema 校验 (MANIFEST 正例 + 篡改反例)
- adapter 校验 (input / output / runtime alignment)
- 24/24 golden vector 验证 (元数据 + expected_board + 运行时复算)
"""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from openmetaphysics.contracts.qimen_contract import MANIFEST, QimenContractAdapter, load_manifest
from openmetaphysics.domain.qimen.adapter import QimenContractAdapter as RuntimeAdapter

ROOT = Path(__file__).resolve().parent.parent
VECTORS_PATH = ROOT / "docs" / "qimen" / "golden_vectors.json"
SHANGHAI = ZoneInfo("Asia/Shanghai")


def _adapter() -> QimenContractAdapter:
    return QimenContractAdapter(vectors_path=VECTORS_PATH)


def test_manifest_valid_against_schema():
    """MANIFEST 满足 qimen_contract.schema.json (正例)。"""
    adapter = _adapter()
    assert adapter.validate_manifest() == []
    assert adapter.validate_manifest(load_manifest()) == []


def test_manifest_rejects_tampered():
    """篡改清单必须被 schema 拒绝。"""
    adapter = _adapter()

    wrong_version = dict(MANIFEST, version="0.9.0")
    assert adapter.validate_manifest(wrong_version)

    wrong_status = dict(MANIFEST, status="Draft")
    assert adapter.validate_manifest(wrong_status)

    missing_qc = dict(MANIFEST)
    missing_qc["qc_ids"] = [q for q in MANIFEST["qc_ids"] if q != "QC-014"]
    assert adapter.validate_manifest(missing_qc)

    extra_rule = dict(MANIFEST)
    extra_rule["frozen_rules"] = MANIFEST["frozen_rules"] + ["D99"]
    assert adapter.validate_manifest(extra_rule)

    nonempty_deferred = dict(MANIFEST, deferred_rules=["D2"])
    assert adapter.validate_manifest(nonempty_deferred)

    unknown_key = dict(MANIFEST, invented="nonsense")
    assert adapter.validate_manifest(unknown_key)


def test_validate_input_adapter():
    """契约适配层输入校验 (QC-001 前置)。"""
    adapter = _adapter()
    dt = datetime(2024, 2, 15, 12, 0, tzinfo=SHANGHAI)
    from openmetaphysics.agents.qimen import QimenInput

    valid = QimenInput(request_id="x", born_at=dt, gender="unknown")
    assert adapter.validate_input(valid) == []
    assert adapter.validate_input(valid.model_dump(mode="json")) == []

    # naive datetime: 以 dict 形态传入, 由适配层捕获 pydantic 校验失败
    naive = {"request_id": "x", "born_at": datetime(2024, 2, 15, 12, 0), "gender": "unknown"}
    assert adapter.validate_input(naive) != []

    assert adapter.validate_input({"request_id": "x"}) != []
    assert adapter.validate_input("not-an-input") != []


def test_validate_output_adapter():
    """契约适配层输出校验 (QC-002~014 可观察不变量)。"""
    adapter = _adapter()
    data = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    board = data["vectors"][0]["expected_board"]
    assert adapter.validate_output(board) == []
    assert adapter.validate_output(dict(board, cells=board["cells"][:8])) != []
    assert adapter.validate_output(dict(board, ju=0)) != []
    assert adapter.validate_output(dict(board, dun_type="neutral")) != []
    assert adapter.validate_output({}) != []


def test_runtime_alignment():
    """适配层符号表与运行时一致 (单一真源)。"""
    adapter = _adapter()
    assert adapter.validate_runtime_alignment() == []


def test_golden_vectors_24_ok():
    """24/24 向量: 元数据一致 + expected_board 不变量 + 运行时复算。"""
    adapter = _adapter()
    report = adapter.validate_golden_vectors()
    assert report["total"] == 24
    assert report["ok"] == 24, f"errors: {report['errors']}"
    assert not report["errors"]
    # 已知漂移以 warning 记录 (fixtures 冻结前元数据, 非错误)
    assert report["warnings"], "expected deferred-drift warnings"
    sample = next(iter(report["warnings"].values()))
    assert any("deferred_rules" in w for w in sample)


def test_contract_status_metadata():
    """契约状态声明与清单一致。"""
    adapter = _adapter()
    assert adapter.contract_id == "qimen:behavior:v1.0.0"
    assert adapter.version == "1.0.0"
    assert adapter.status == "Frozen"
    assert adapter.engine_version == "0.3.0"
    assert adapter.qc_ids == [f"QC-{i:03d}" for i in range(1, 15)]
    # domain 层 runtime adapter 与契约版本一致
    assert RuntimeAdapter().contract_version == adapter.version
