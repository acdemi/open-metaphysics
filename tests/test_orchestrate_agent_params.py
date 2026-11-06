"""H3 regression: /orchestrate domain-specific parameters + process-stable auto seed.

Review H3: ``OrchestrationRequest.payload`` was typed as the strict ``AgentInput``
envelope, so domain fields (Liuyao ``casts``, Ziwei ``lunar_month``/``lunar_day``,
Bazi ``dayun_count``) were rejected with 422. Separately, Liuyao's automatic
cast path derived its seed with Python's ``hash()``, which is salted per process
(``PYTHONHASHSEED``) and therefore not reproducible across processes.

The fix routes domain fields per agent (payload extras + explicit
``agent_params``) and derives the automatic seed from SHA-256.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput
from openmetaphysics.api.app import create_app
from openmetaphysics.core.engines import derive_seed

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
BORN = "1990-06-15T08:30:00+09:00"
CLIENT = TestClient(create_app())


def _orchestrate(
    *,
    request_id: str = "h3-domain",
    agents: tuple[str, ...] = ("bazi", "ziwei"),
    payload_extra: dict | None = None,
    agent_params: dict | None = None,
):
    payload = {
        "request_id": request_id,
        "born_at": BORN,
        "gender": "male",
        "question": "事业与财运",
    }
    payload.update(payload_extra or {})
    body: dict = {
        "request_id": request_id,
        "payload": payload,
        "agents": list(agents),
    }
    if agent_params is not None:
        body["agent_params"] = agent_params
    return CLIENT.post("/orchestrate", json=body)


def _cast_values(result: dict) -> list[int]:
    return [line["cast_value"] for line in result["original"]]


# -- domain parameters reach the agent --------------------------------------


def test_orchestrate_accepts_liuyao_casts_in_agent_params():
    casts = [9, 9, 7, 7, 8, 8]
    response = _orchestrate(agents=("liuyao",), agent_params={"liuyao": {"casts": casts}})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["errors"] == []
    assert [output["agent"] for output in data["outputs"]] == ["liuyao"]
    assert _cast_values(data["outputs"][0]["result"]) == casts

    direct = CLIENT.post(
        "/agents/liuyao/compute",
        json={
            "request_id": "h3-domain",
            "born_at": BORN,
            "gender": "male",
            "question": "事业与财运",
            "casts": casts,
        },
    ).json()
    assert data["outputs"][0]["result"] == direct["result"]
    assert data["outputs"][0]["input_hash"] == direct["input_hash"]


def test_orchestrate_accepts_liuyao_casts_on_payload():
    """Domain fields directly on ``payload`` are dispatched, not rejected (422)."""
    casts = [7, 7, 8, 8, 7, 8]
    response = _orchestrate(agents=("liuyao",), payload_extra={"casts": casts})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["errors"] == []
    assert _cast_values(data["outputs"][0]["result"]) == casts


def test_orchestrate_accepts_bazi_dayun_count():
    response = _orchestrate(agents=("bazi",), agent_params={"bazi": {"dayun_count": 4}})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["errors"] == []
    assert len(data["outputs"][0]["result"]["dayun"]) == 4


def test_orchestrate_accepts_ziwei_lunar_fields():
    lunar = {"lunar_month": 3, "lunar_day": 12}
    response = _orchestrate(agents=("ziwei",), agent_params={"ziwei": lunar})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["errors"] == []
    result = data["outputs"][0]["result"]

    direct = CLIENT.post(
        "/agents/ziwei/compute",
        json={
            "request_id": "h3-domain",
            "born_at": BORN,
            "gender": "male",
            "question": "事业与财运",
            **lunar,
        },
    ).json()
    assert result == direct["result"]
    assert result["calendar_note"] is None or "leap" not in result["calendar_note"]


def test_agent_params_override_payload_domain_field():
    response = _orchestrate(
        agents=("liuyao",),
        payload_extra={"casts": [7, 7, 7, 7, 7, 7]},
        agent_params={"liuyao": {"casts": [9, 9, 9, 9, 9, 9]}},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["errors"] == []
    assert _cast_values(data["outputs"][0]["result"]) == [9] * 6


# -- validation -------------------------------------------------------------


def test_invalid_agent_params_is_reported_per_agent():
    response = _orchestrate(
        agents=("bazi", "liuyao"),
        agent_params={"liuyao": {"casts": [1, 2, 3, 4, 5, 6]}},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert [output["agent"] for output in data["outputs"]] == ["bazi"]
    assert any("liuyao" in error and "casts" in error for error in data["errors"]), data["errors"]


def test_unknown_agent_key_in_agent_params_is_reported():
    response = _orchestrate(agents=("bazi",), agent_params={"nope": {"casts": [7] * 6}})
    assert response.status_code == 200, response.text
    errors = response.json()["errors"]
    assert any("agent_params" in error and "nope" in error for error in errors), errors


def test_unaccepted_payload_field_is_reported():
    response = _orchestrate(agents=("bazi",), payload_extra={"casts": [7] * 6})
    assert response.status_code == 200, response.text
    data = response.json()
    assert [output["agent"] for output in data["outputs"]] == ["bazi"]
    assert any("casts" in error for error in data["errors"]), data["errors"]


# -- backward compatibility -------------------------------------------------


def test_old_request_shape_still_works_unchanged():
    response = _orchestrate(agents=("bazi", "ziwei"))
    assert response.status_code == 200, response.text
    data = response.json()
    assert set(data) == {
        "request_id",
        "outputs",
        "consensus",
        "explanation",
        "explanation_detail",
        "errors",
    }
    assert data["errors"] == []
    assert [output["agent"] for output in data["outputs"]] == ["bazi", "ziwei"]
    assert data["consensus"] is not None  # unchanged multi-agent behaviour


# -- process-stable Liuyao auto seed ---------------------------------------


def test_derive_seed_is_sha256_based():
    payload = LiuyaoInput(
        request_id="stable-r1",
        born_at=datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc),
        client_nonce="nonce-1",
    )
    expected = int.from_bytes(hashlib.sha256(b"stable-r1\x1fnonce-1").digest()[:8], "big") % (2**31)
    assert derive_seed(payload) == expected


def test_explicit_seed_is_untouched():
    payload = LiuyaoInput(
        request_id="stable-r1",
        born_at=datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc),
        seed=12345,
    )
    assert derive_seed(payload) == 12345


_SUBPROCESS_PROBE = """
import json
from datetime import datetime, timezone
from openmetaphysics.agents.liuyao import LiuyaoAgent, LiuyaoInput

payload = LiuyaoInput(
    request_id="cross-process",
    born_at=datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc),
    client_nonce="nonce-1",
)
result = LiuyaoAgent().compute(payload).result
print(json.dumps({
    "casts": [line.cast_value for line in result.original],
    "original": result.original_hexagram,
    "changed": result.changed_hexagram,
}))
"""


def _auto_cast_with_hash_seed(hash_seed: str) -> dict:
    env = {**os.environ, "PYTHONHASHSEED": hash_seed, "PYTHONPATH": str(SRC)}
    try:
        process = subprocess.run(
            [sys.executable, "-c", _SUBPROCESS_PROBE],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            cwd=str(ROOT),
            timeout=120,
        )
    except PermissionError:
        pytest.skip("sandbox blocks subprocess pipes (WinError 5)")
    assert process.returncode == 0, process.stderr
    return json.loads(process.stdout.strip().splitlines()[-1])


def test_auto_cast_is_identical_across_python_hash_seeds():
    zero = _auto_cast_with_hash_seed("0")
    one = _auto_cast_with_hash_seed("1")
    assert zero == one, "auto cast must not depend on PYTHONHASHSEED"

    # and identical to the in-process auto path
    local = (
        LiuyaoAgent()
        .compute(
            LiuyaoInput(
                request_id="cross-process",
                born_at=datetime(2024, 5, 1, 12, 0, tzinfo=timezone.utc),
                client_nonce="nonce-1",
            )
        )
        .result
    )
    assert zero["casts"] == [line.cast_value for line in local.original]
    assert zero["original"] == local.original_hexagram
    assert zero["changed"] == local.changed_hexagram
