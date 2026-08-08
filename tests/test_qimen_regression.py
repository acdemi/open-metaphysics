"""Qimen Golden Vector 机器回归验证 (Phase 5.8C).

将 Golden Vectors 从"人工检查的静态清单"升级为"自动执行的回归防护网":
每个 CI 周期自动证明 Runtime 对契约 v1.0.0 的遵守。

E014 (Evidence Ledger — 文本记录):
  id:      E014
  domain:  qimen
  date:    2026-08-09
  status:  PASSED
  detail:  24/24 规范向量自动回归验证通过; Runtime engine 0.3.0 对
           QIMEN_BEHAVIOR_CONTRACT.md v1.0.0 (Frozen) 持续合规。
           本模块即自动执行证据 (每次 pytest 重放)。
  注:      本条目仅文本描述, 不生成额外报告文件。

比较策略: 盘面数据为 str/int/bool/None (无浮点), 采用深度相等比较
(无需容差)。任何向量不匹配 → 测试显式失败。

纪律: 不修改 runtime / 契约 / golden_vectors.json fixtures; 不新增规则。
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pytest

from openmetaphysics.agents.qimen import LIUJIA, QimenAgent, QimenInput
from openmetaphysics.core.schemas import GeoPoint

ROOT = Path(__file__).resolve().parent.parent
VECTORS_PATH = ROOT / "docs" / "qimen" / "golden_vectors.json"
SCHEMA_PATH = ROOT / "docs" / "specification" / "qimen_contract.schema.json"

_BOARD_KEY_ORDER = ["solar_term", "ju", "dun_type", "day_of_month", "triple_offset", "cells"]
_CELL_KEY_ORDER = [
    "palace",
    "name",
    "sky_plate",
    "earth_plate",
    "eight_gods",
    "nine_stars",
    "eight_doors",
    "three_qi",
    "is_void",
    "is_central",
]


def _load_vectors() -> list[dict]:
    if not VECTORS_PATH.exists():
        raise FileNotFoundError(f"vectors missing: {VECTORS_PATH}")
    return json.loads(VECTORS_PATH.read_text(encoding="utf-8"))["vectors"]


def _load_contract_rules() -> list[dict]:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"schema missing: {SCHEMA_PATH}")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return schema["x-contract"]["rules"]


def _vector_input(vector: dict) -> QimenInput:
    inp = dict(vector["input"])
    inp["born_at"] = datetime.fromisoformat(inp["born_at"])
    inp["born_location"] = GeoPoint(**inp["born_location"])
    return QimenInput.model_validate(inp)


def _compute_board(vector: dict) -> dict:
    return QimenAgent().compute(_vector_input(vector)).result.model_dump(mode="json")


def _boards(vectors: list[dict]) -> list[dict]:
    return [v["expected_board"] for v in vectors]


def _board_check(board: dict, when: str, cond: bool, what: str) -> list[str]:
    return [] if cond else [f"{when}: {what}"]


# ---------------------------------------------------------------------------
# 契约覆盖校验器: 每个 QC 的 observable_output 由机器断言覆盖
# ---------------------------------------------------------------------------
def _qc001_determinism(vectors: list[dict]) -> list[str]:
    bad: list[str] = []
    for v in vectors:
        first = _compute_board(v)
        second = _compute_board(v)
        if first != second:
            bad.append(f"{v['id']}: non-deterministic replay")
    return bad


def _qc002_nine_palaces(vectors: list[dict]) -> list[str]:
    bad: list[str] = []
    for v in vectors:
        b = v["expected_board"]
        cells = b["cells"]
        bad += _board_check(b, v["id"], len(cells) == 9, "len(cells) != 9")
        bad += _board_check(
            b,
            v["id"],
            [c["palace"] for c in cells] == list(range(1, 10)),
            "palaces not unique 1..9",
        )
        bad += _board_check(
            b,
            v["id"],
            {c["name"] for c in cells} == {"坎", "坤", "震", "巽", "中宫", "乾", "兑", "艮", "离"},
            "palace names mismatch",
        )
        bad += _board_check(b, v["id"], list(b.keys()) == _BOARD_KEY_ORDER, "board key order")
        bad += _board_check(
            b, v["id"], all(list(c.keys()) == _CELL_KEY_ORDER for c in cells), "cell key order"
        )
    return bad


def _qc003_dun_type(vectors: list[dict]) -> list[str]:
    bad: list[str] = []
    duns = set()
    tags = set()
    for v in vectors:
        b = v["expected_board"]
        duns.add(b["dun_type"])
        tags.update(v["coverage"])
        bad += _board_check(b, v["id"], b["dun_type"] in ("yang", "yin"), "dun_type invalid")
        bad += _board_check(b, v["id"], isinstance(b["solar_term"], str), "solar_term missing")
    if duns != {"yang", "yin"}:
        bad.append(f"dun coverage: {duns}")
    if not ({"winter_solstice", "summer_solstice_before", "summer_solstice_after"} <= tags):
        bad.append("boundary coverage missing (冬至/夏至)")
    return bad


def _qc004_ju(vectors: list[dict]) -> list[str]:
    bad: list[str] = []
    yang_ju: set[int] = set()
    for v in vectors:
        b = v["expected_board"]
        yang_ju.add(b["ju"]) if b["dun_type"] == "yang" else None
        bad += _board_check(
            b, v["id"], isinstance(b["ju"], int) and 1 <= b["ju"] <= 9, "ju out of [1,9]"
        )
        bad += _board_check(b, v["id"], b["triple_offset"] in (0, 3, 6), "triple_offset invalid")
        inp_day = datetime.fromisoformat(v["input"]["born_at"]).day
        bad += _board_check(b, v["id"], b["day_of_month"] == inp_day, "day_of_month != input day")
    if yang_ju != set(range(1, 10)):
        bad.append(f"yang ju coverage: {sorted(yang_ju)}")
    return bad


def _plate_set_check(vectors: list[dict], field: str, label: str) -> list[str]:
    bad: list[str] = []
    full = {"戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"}
    for v in vectors:
        plates = [c[field] for c in v["expected_board"]["cells"]]
        bad += _board_check(
            v["expected_board"],
            v["id"],
            None not in plates and set(plates) == full and len(set(plates)) == 9,
            f"{label} not 9 distinct 六仪三奇",
        )
    return bad


def _qc005_earth(vectors: list[dict]) -> list[str]:
    return _plate_set_check(vectors, "earth_plate", "earth_plate")


def _qc006_heaven(vectors: list[dict]) -> list[str]:
    bad = _plate_set_check(vectors, "sky_plate", "sky_plate")
    for v in vectors:
        b = v["expected_board"]
        sky = {c["sky_plate"] for c in b["cells"]}
        earth = {c["earth_plate"] for c in b["cells"]}
        bad += _board_check(b, v["id"], sky == earth, "sky set != earth set")
        plan = v.get("plan")
        if plan:  # 值符宫天盘干 = 旬首仪 (plan 向量)
            sky_at = {c["palace"]: c["sky_plate"] for c in b["cells"]}
            expect = dict(LIUJIA)[plan["xun"]]  # 旬名 → 所遁六仪
            bad += _board_check(
                b, v["id"], sky_at[plan["hour_stem_palace"]] == expect, "值符宫天盘干 != 旬首仪"
            )
    return bad


def _qc007_zhifu(vectors: list[dict]) -> list[str]:
    bad: list[str] = []
    for v in vectors:
        b = v["expected_board"]
        gods = {c["palace"]: c["eight_gods"] for c in b["cells"]}
        zhifu_palaces = [p for p, g in gods.items() if g == "值符"]
        bad += _board_check(b, v["id"], len(zhifu_palaces) == 1, "值符 not unique")
        plan = v.get("plan")
        if plan and len(zhifu_palaces) == 1:
            bad += _board_check(
                b, v["id"], zhifu_palaces[0] == plan["zhi_fu_palace"], "值符神落宫 != 值符落宫"
            )
    return bad


def _qc008_zhishi(vectors: list[dict]) -> list[str]:
    bad: list[str] = []
    for v in vectors:
        plan = v.get("plan")
        if not plan:
            continue
        doors = {c["palace"]: c["eight_doors"] for c in v["expected_board"]["cells"]}
        bad += _board_check(
            v["expected_board"],
            v["id"],
            doors[plan["zhi_shi_palace"]] == plan["zhi_shi_door"],
            "值使门落宫 != 值使落宫",
        )
    return bad


def _qc009_stars(vectors: list[dict]) -> list[str]:
    bad: list[str] = []
    full = {"天蓬", "天芮", "天冲", "天辅", "天禽", "天心", "天柱", "天任", "天英"}
    for v in vectors:
        stars = [c["nine_stars"] for c in v["expected_board"]["cells"]]
        bad += _board_check(
            v["expected_board"],
            v["id"],
            None not in stars and set(stars) == full and len(set(stars)) == 9,
            "nine_stars not 9 distinct",
        )
    return bad


def _qc010_doors(vectors: list[dict]) -> list[str]:
    bad: list[str] = []
    full = {"休门", "死门", "伤门", "杜门", "开门", "惊门", "生门", "景门"}
    for v in vectors:
        b = v["expected_board"]
        doors = [c["eight_doors"] for c in b["cells"]]
        non_none = [d for d in doors if d is not None]
        bad += _board_check(
            b, v["id"], set(non_none) == full and len(set(non_none)) == 8, "doors not 8 distinct"
        )
        for c in b["cells"]:
            if c["is_central"] and c["eight_doors"] is not None:
                bad.append(f"{v['id']}: central has door")
            if not c["is_central"] and c["eight_doors"] is None:
                bad.append(f"{v['id']}: non-central missing door")
    return bad


def _qc011_gods(vectors: list[dict]) -> list[str]:
    bad: list[str] = []
    full = {"值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"}
    for v in vectors:
        b = v["expected_board"]
        gods = [c["eight_gods"] for c in b["cells"]]
        non_none = [g for g in gods if g is not None]
        bad += _board_check(
            b, v["id"], set(non_none) == full and len(set(non_none)) == 8, "gods not 8 distinct"
        )
        for c in b["cells"]:
            if c["is_central"] and c["eight_gods"] is not None:
                bad.append(f"{v['id']}: central has god")
            if not c["is_central"] and c["eight_gods"] is None:
                bad.append(f"{v['id']}: non-central missing god")
    return bad


def _qc012_three_qi(vectors: list[dict]) -> list[str]:
    bad: list[str] = []
    for v in vectors:
        sanqi = [c["three_qi"] for c in v["expected_board"]["cells"] if c["three_qi"] is not None]
        bad += _board_check(
            v["expected_board"],
            v["id"],
            len(sanqi) == 3 and set(sanqi) == {"乙", "丙", "丁"} and len(set(sanqi)) == 3,
            f"three_qi not exactly 乙丙丁: {sanqi}",
        )
    return bad


def _qc013_void(vectors: list[dict]) -> list[str]:
    bad: list[str] = []
    for v in vectors:
        void = [c["palace"] for c in v["expected_board"]["cells"] if c["is_void"]]
        bad += _board_check(
            v["expected_board"], v["id"], 1 <= len(void) <= 2, f"void palaces {void}"
        )
    return bad


def _qc014_central(vectors: list[dict]) -> list[str]:
    bad: list[str] = []
    for v in vectors:
        central = [c["palace"] for c in v["expected_board"]["cells"] if c["is_central"]]
        bad += _board_check(v["expected_board"], v["id"], central == [5], f"central {central}")
    return bad


# QC → 覆盖校验器 (与 qimen_contract.schema.json x-contract 的 rule id 一一对应)
QC_CHECKERS: dict[str, Callable[[list[dict]], list[str]]] = {
    "QC-001": _qc001_determinism,
    "QC-002": _qc002_nine_palaces,
    "QC-003": _qc003_dun_type,
    "QC-004": _qc004_ju,
    "QC-005": _qc005_earth,
    "QC-006": _qc006_heaven,
    "QC-007": _qc007_zhifu,
    "QC-008": _qc008_zhishi,
    "QC-009": _qc009_stars,
    "QC-010": _qc010_doors,
    "QC-011": _qc011_gods,
    "QC-012": _qc012_three_qi,
    "QC-013": _qc013_void,
    "QC-014": _qc014_central,
}


# ---------------------------------------------------------------------------
# 1) 全量回归: 24/24 自动验证 + 显式统计
# ---------------------------------------------------------------------------
def test_all_normative_vectors_pass(capsys):
    """遍历全部向量: Runtime 计算 vs expected 深度比较; 输出统计。"""
    vectors = _load_vectors()
    failures: list[str] = []
    for v in vectors:
        try:
            actual = _compute_board(v)
        except Exception as exc:  # noqa: BLE001 — 显式失败并记录
            failures.append(f"{v['id']}: compute raised {exc}")
            continue
        if actual != v["expected_board"]:
            failures.append(f"{v['id']}: output != expected_board")
    with capsys.disabled():
        total = len(vectors)
        passed = total - len(failures)
        print(f"\n[Qimen Regression] {passed}/{total} vectors passed")
        for f in failures:
            print(f"[FAIL] {f}")
    assert not failures, "\n".join(failures)
    assert total == 24


@pytest.mark.parametrize("vector", _load_vectors(), ids=lambda v: v["id"])
def test_normative_vector_regression(vector):
    """逐向量回归 (失败时 pytest 显式点名向量)。"""
    assert _compute_board(vector) == vector["expected_board"], f"{vector['id']} mismatch"


# ---------------------------------------------------------------------------
# 2) 契约覆盖: 每项 observable_output 由向量集合机器验证
# ---------------------------------------------------------------------------
def test_contract_coverage():
    """golden_vectors 覆盖契约中定义的每一项 observable_output。"""
    vectors = _load_vectors()
    rules = _load_contract_rules()
    # 每个 QC 条款都有对应校验器 (无遗漏)
    rule_ids = {r["id"] for r in rules}
    assert rule_ids == set(QC_CHECKERS), (
        f"checker registry mismatch: missing {rule_ids - set(QC_CHECKERS)}"
    )
    violations: dict[str, list[str]] = {}
    for rule in rules:
        qc = rule["id"]
        found = QC_CHECKERS[qc](vectors)
        if found:
            violations[qc] = found
    assert not violations, f"contract coverage violations: {violations}"
