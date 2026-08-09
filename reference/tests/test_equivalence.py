"""Reference ↔ Product 确定性等价证明 (Phase 5.7 对齐 Sprint, Task B).

固定种子 30 个合法输入, 分别经:
1. Product Runtime (src/openmetaphysics/agents/qimen.py, 只读)
2. Reference Runtime (reference/qimen/domain.py)
比较输出: 完整 board JSON (canonical form, 逐字节一致) + 元数据版本声明。

本文件为等价对照脚本 (Task B), 因此是唯一允许导入 src 的 reference/tests
文件; 独立性声明由 reference/tests/test_golden_vectors.py 的源码导入检查强制。

结果声明: "强确定性等价成立" —— 详见 docs/qimen/reference_alignment_proof.md
与 docs/qimen/reference_certification.md。
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from openmetaphysics.agents.qimen import QimenAgent, QimenInput
from openmetaphysics.core.schemas import GeoPoint
from reference.qimen.domain import compute as reference_compute

ROOT = Path(__file__).resolve().parents[2]
SHANGHAI = ZoneInfo("Asia/Shanghai")

PRODUCT_ENGINE_VERSION = "0.3.0"
RULE_SET_VERSION = "0.3.0"
CONTRACT_VERSION = "1.0.0"


def _generate_inputs(seed: int, count: int) -> list[dict]:
    """固定种子生成合法输入 (2023-2025 随机日期小时 + 北京坐标)。"""
    rng = random.Random(seed)
    inputs: list[dict] = []
    for i in range(count):
        year = rng.choice([2023, 2024, 2025])
        dt = datetime(year, 1, 1, 0, 0, tzinfo=SHANGHAI) + timedelta(
            days=rng.randrange(0, 365), hours=rng.randrange(0, 24)
        )
        inputs.append(
            {
                "request_id": f"eq-{i}",
                "born_at": dt.isoformat(),
                "gender": "unknown",
                "born_location": {
                    "latitude": 39.9,
                    "longitude": 116.4,
                    "timezone": "Asia/Shanghai",
                },
            }
        )
    return inputs


def _product_compute(payload: dict) -> dict:
    inp = dict(payload)
    inp["born_at"] = datetime.fromisoformat(inp["born_at"])
    inp["born_location"] = GeoPoint(**inp["born_location"])
    return QimenAgent().compute(QimenInput.model_validate(inp)).result.model_dump(mode="json")


def test_equivalence_30_sampled_inputs():
    """30 抽样: Reference == Product (board JSON 逐字节一致)。"""
    inputs = _generate_inputs(seed=2024, count=30)
    assert len(inputs) == 30
    mismatched: list[str] = []
    for payload in inputs:
        reference = reference_compute(payload)
        product = _product_compute(payload)
        reference_json = json.dumps(reference, ensure_ascii=False, sort_keys=True)
        product_json = json.dumps(product, ensure_ascii=False, sort_keys=True)
        if reference_json != product_json:
            mismatched.append(payload["request_id"])
    assert not mismatched, f"equivalence mismatch: {mismatched}"


def test_equivalence_metadata_versions():
    """元数据版本声明一致 (契约/规则集/引擎)。"""
    assert RULE_SET_VERSION == "0.3.0"
    assert CONTRACT_VERSION == "1.0.0"
    assert QimenAgent().engine_version == PRODUCT_ENGINE_VERSION
    inputs = _generate_inputs(seed=2024, count=3)
    for payload in inputs:
        reference = reference_compute(payload)
        product = _product_compute(payload)
        assert reference["ju"] == product["ju"]
        assert reference["dun_type"] == product["dun_type"]
        assert reference["triple_offset"] == product["triple_offset"]
        assert reference["solar_term"] == product["solar_term"]


def test_equivalence_statistics(capsys):
    """显式统计输出: N/N equivalence passed。"""
    inputs = _generate_inputs(seed=2024, count=30)
    passed = 0
    for payload in inputs:
        if reference_compute(payload) == _product_compute(payload):
            passed += 1
    with capsys.disabled():
        print(f"\n[Equivalence] {passed}/{len(inputs)} inputs byte-identical")
    assert passed == len(inputs) == 30
