"""One-off generator for docs/liuyao/golden_vectors.json.

Expectations are produced by running the EXISTING production engine, so the
vectors record current behaviour rather than an idealized design.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "src")

from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput  # noqa: E402

OUT = Path("docs/liuyao/golden_vectors.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

ALL = ["LY-01", "LY-02", "LY-03", "LY-04", "LY-05", "LY-06", "LY-07", "LY-08", "LY-09", "LY-10", "LY-11"]

CASES: list[dict] = [
    # -- normal --
    dict(id="LY_norm_001", category="normal", desc="乾为天, all stable young-yang",
         casts=[7, 7, 7, 7, 7, 7], born="1985-08-15T10:00:00+08:00", coverage=ALL),
    dict(id="LY_norm_002", category="normal", desc="坤为地, all stable young-yin",
         casts=[8, 8, 8, 8, 8, 8], born="1985-08-15T10:00:00+08:00", coverage=ALL),
    dict(id="LY_norm_003", category="normal", desc="乾 -> 坤, all six lines changing",
         casts=[9, 9, 9, 9, 9, 9], born="1985-08-15T10:00:00+08:00", coverage=ALL),
    dict(id="LY_norm_004", category="normal", desc="坤 -> 乾, all six old-yin",
         casts=[6, 6, 6, 6, 6, 6], born="1985-08-15T10:00:00+08:00", coverage=ALL),
    dict(id="LY_norm_005", category="normal", desc="mixed lines with changing lines",
         casts=[7, 8, 9, 6, 7, 8], born="2024-05-01T12:00:00+00:00", coverage=ALL),
    dict(id="LY_norm_006", category="normal", desc="seeded three-coin casting (no explicit casts)",
         casts=None, seed=12345, born="2024-05-01T12:00:00+00:00", coverage=["LY-01", "LY-02", "LY-03", "LY-04", "LY-05", "LY-06", "LY-07", "LY-08", "LY-09", "LY-10", "LY-11"]),
    dict(id="LY_norm_007", category="normal", desc="single changing line (upper six)",
         casts=[7, 7, 7, 7, 7, 9], born="2024-05-01T12:00:00+00:00", coverage=ALL),
    dict(id="LY_norm_008", category="normal", desc="question 财运 -> 妻财 用神",
         casts=[7, 7, 8, 8, 7, 8], born="2024-05-01T12:00:00+00:00", question="财运如何", coverage=ALL),
    dict(id="LY_norm_009", category="normal", desc="question 事业升迁 -> 官鬼 用神",
         casts=[7, 7, 8, 8, 7, 8], born="2024-05-01T12:00:00+00:00", question="事业升迁", coverage=ALL),
    dict(id="LY_norm_010", category="normal", desc="no changing lines -> changed_hexagram is null",
         casts=[7, 8, 7, 8, 7, 8], born="2024-05-01T12:00:00+00:00", coverage=ALL),
    # -- edge --
    dict(id="LY_edge_001", category="edge", desc="no question -> default 世爻 用神",
         casts=[7, 7, 7, 7, 7, 7], born="2024-05-01T12:00:00+00:00", coverage=["LY-11"]),
    dict(id="LY_edge_002", category="edge", desc="question matching several keyword groups (first rule wins)",
         casts=[7, 7, 8, 8, 7, 8], born="2024-05-01T12:00:00+00:00", question="财运与事业", coverage=["LY-11"]),
    dict(id="LY_edge_003", category="edge", desc="question 出行 -> 子孙 用神",
         casts=[7, 7, 8, 8, 7, 8], born="2024-05-01T12:00:00+00:00", question="出行平安", coverage=["LY-11"]),
    dict(id="LY_edge_004", category="edge", desc="question 考试 -> 父母 用神",
         casts=[8, 8, 7, 7, 8, 8], born="2024-05-01T12:00:00+00:00", question="考试结果", coverage=["LY-11"]),
    dict(id="LY_edge_005", category="edge", desc="mutual hexagram derived from lines 2-4 / 3-5",
         casts=[7, 8, 9, 6, 7, 8], born="2024-05-01T12:00:00+00:00", coverage=["LY-04", "LY-05"]),
    dict(id="LY_edge_006", category="edge", desc="22:00 clock time does not trigger the 23:00 day rollover",
         casts=[7, 7, 8, 8, 7, 8], born="2024-05-01T22:00:00+00:00", coverage=["LY-10"]),
    # -- boundary --
    dict(id="LY_bound_001", category="boundary", desc="23:30 triggers the 23:00 day rollover for 六神",
         casts=[6, 7, 8, 9, 6, 7], born="2024-05-01T23:30:00+00:00", coverage=["LY-10"]),
    dict(id="LY_bound_002", category="boundary", desc="23:00 exactly triggers the rollover",
         casts=[6, 7, 8, 9, 6, 7], born="2024-05-01T23:00:00+00:00", coverage=["LY-10"]),
    dict(id="LY_bound_003", category="boundary", desc="00:00 clock time, no rollover",
         casts=[6, 7, 8, 9, 6, 7], born="2024-05-02T00:00:00+00:00", coverage=["LY-10"]),
    dict(id="LY_bound_004", category="boundary", desc="leap day (2024-02-29)",
         casts=[7, 7, 8, 8, 7, 8], born="2024-02-29T12:00:00+00:00", coverage=["LY-10", "LY-05"]),
    dict(id="LY_bound_005", category="boundary", desc="year boundary 2023-12-31T23:59",
         casts=[7, 7, 8, 8, 7, 8], born="2023-12-31T23:59:00+00:00", coverage=["LY-10"]),
    # -- invalid --
    dict(id="LY_inv_001", category="invalid", desc="five cast values rejected",
         casts=[7, 7, 7, 7, 7], born="2024-05-01T12:00:00+00:00", expected_error="casts must have exactly 6 values"),
    dict(id="LY_inv_002", category="invalid", desc="cast value 5 rejected",
         casts=[5, 7, 7, 7, 7, 7], born="2024-05-01T12:00:00+00:00", expected_error="each cast value must be 6,7,8 or 9"),
    dict(id="LY_inv_003", category="invalid", desc="cast value 10 rejected",
         casts=[7, 7, 7, 7, 7, 10], born="2024-05-01T12:00:00+00:00", expected_error="each cast value must be 6,7,8 or 9"),
]


def main() -> None:
    vectors = []
    for case in CASES:
        entry = {
            "id": case["id"],
            "category": case["category"],
            "description": case["desc"],
            "input": {
                "born_at": case["born"],
                "casts": case["casts"],
                "question": case.get("question"),
                "seed": case.get("seed"),
            },
            "coverage": case.get("coverage", []),
        }
        if "expected_error" in case:
            entry["expected_error"] = case["expected_error"]
            entry["expected"] = None
            # assert the production engine really rejects it
            try:
                LiuyaoInput(
                    request_id="gv",
                    born_at=datetime.fromisoformat(case["born"]),
                    casts=case["casts"],
                )
                raise SystemExit(f"{case['id']} unexpectedly accepted")
            except ValueError as exc:
                assert case["expected_error"] in str(exc), (case["id"], str(exc))
        else:
            payload = LiuyaoInput(
                request_id="gv",
                born_at=datetime.fromisoformat(case["born"]),
                casts=case["casts"],
                question=case.get("question"),
                seed=case.get("seed"),
            )
            entry["expected"] = LiuyaoAgent().compute(payload).result.model_dump()
        vectors.append(entry)

    doc = {
        "metadata": {
            "domain": "liuyao",
            "engine_version": "0.1.0",
            "status": "candidate",
            "contract": "docs/liuyao/LIUYAO_BEHAVIOR_CONTRACT.md",
            "rule_inventory": "docs/liuyao/LIUYAO_RULE_INVENTORY.md",
            "reference": "reference/liuyao/domain.py",
            "total_vectors": len(vectors),
            "categories": sorted({v["category"] for v in vectors}),
            "generated_from": "src/openmetaphysics/agents/liuyao.py (existing behaviour)",
        },
        "vectors": vectors,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT} with {len(vectors)} vectors")


if __name__ == "__main__":
    main()
