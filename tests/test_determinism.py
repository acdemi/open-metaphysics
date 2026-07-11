"""Determinism / golden-replay: same input -> byte-identical output (except computed_at)."""

from datetime import datetime, timezone

from openmetaphysics.agents.bazi import BaziAgent, BaziInput
from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput
from openmetaphysics.core.schemas import Gender


def _strip(output):
    d = output.model_dump(mode="json")
    d.pop("computed_at", None)
    return d


def test_liuyao_replay_identical():
    payload = LiuyaoInput(
        request_id="r", born_at=datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc), seed=42
    )
    a = _strip(LiuyaoAgent().compute(payload))
    b = _strip(LiuyaoAgent().compute(payload))
    assert a == b


def test_bazi_replay_identical():
    payload = BaziInput(
        request_id="r",
        born_at=datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc),
        gender=Gender.MALE,
    )
    a = _strip(BaziAgent().compute(payload))
    b = _strip(BaziAgent().compute(payload))
    assert a == b


def test_input_hash_stable():
    payload = BaziInput(
        request_id="r",
        born_at=datetime(1985, 8, 15, 10, 0, tzinfo=timezone.utc),
        gender=Gender.MALE,
    )
    h1 = BaziAgent().compute(payload).input_hash
    h2 = BaziAgent().compute(payload).input_hash
    assert h1 == h2 and len(h1) == 64


def test_different_seed_different_liuyao():
    p1 = LiuyaoInput(
        request_id="r1", born_at=datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc), seed=1
    )
    p2 = LiuyaoInput(
        request_id="r2", born_at=datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc), seed=2
    )
    o1 = LiuyaoAgent().compute(p1).result
    o2 = LiuyaoAgent().compute(p2).result
    assert o1.najia != o2.najia or o1.original_hexagram != o2.original_hexagram
