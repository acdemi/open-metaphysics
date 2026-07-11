"""Liuyao agent — golden vectors and determinism."""

from datetime import datetime, timezone

from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput


def _run(casts, question=None):
    payload = LiuyaoInput(
        request_id="t",
        born_at=datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc),
        casts=casts,
        question=question,
    )
    return LiuyaoAgent().compute(payload).result


def test_all_nine_is_qian_changing_to_kun():
    r = _run([9, 9, 9, 9, 9, 9])
    assert r.original_hexagram == 1  # 乾为天
    assert r.changed_hexagram == 2  # 变坤
    assert all(y.is_changing for y in r.original)
    assert r.shi_position == 6 and r.ying_position == 3
    assert r.palace == "乾"


def test_qian_najia_and_liuqin_canonical():
    r = _run([7, 7, 7, 7, 7, 7])  # 乾 stable
    assert r.original_hexagram == 1
    assert r.changed_hexagram is None
    assert r.najia == ["甲子", "甲寅", "甲辰", "壬午", "壬申", "壬戌"]
    assert r.liu_qin == ["子孙", "妻财", "父母", "官鬼", "兄弟", "父母"]


def test_seed_replay_is_deterministic():
    base = LiuyaoInput(
        request_id="r", born_at=datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc), seed=12345
    )
    a = LiuyaoAgent().compute(base).result
    b = LiuyaoAgent().compute(base).result
    assert a.model_dump() == b.model_dump()
    assert a.original_hexagram == b.original_hexagram


def test_yong_shen_keyword_selection():
    assert _run([7, 7, 8, 8, 7, 8], question="财运如何").yong_shen == "妻财"
    assert _run([7, 7, 8, 8, 7, 8], question="事业升迁").yong_shen == "官鬼"
    assert _run([7, 7, 8, 8, 7, 8]).yong_shen == "世爻"  # default


def test_mutual_hexagram_present():
    r = _run([7, 8, 9, 6, 7, 8])
    assert len(r.mutual) == 6
    assert r.mutual_hexagram is not None


def test_output_envelope_fields():
    payload = LiuyaoInput(
        request_id="t", born_at=datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc), casts=[7] * 6
    )
    out = LiuyaoAgent().compute(payload)
    assert out.agent == "liuyao"
    assert 0.0 <= out.confidence.value <= 1.0
    assert len(out.reasoning_trace) >= 4
    assert out.input_hash and len(out.input_hash) == 64
