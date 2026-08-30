"""Phase 4 infrastructure characterization probe (protocol-frozen, standalone).

Implements sections 1-7 of
``docs/governance/phase4/INFRASTRUCTURE_CHARACTERIZATION_PROTOCOL.md``.

Design constraints (from the approved protocol):

- Standalone tool: touches nothing under ``src/openmetaphysics/agents/``,
  ``benchmarks/``, or any Phase 4 experiment script.
- ``openai`` is imported lazily inside the live request path ONLY, so that
  ``import scripts.infra_probe``, config inspection, dry runs and the offline
  selftest never require the package and never touch the network.
- Live requests are hard-locked to the approved execution window
  (``EXECUTION_WINDOW_UTC``); outside that window ``run`` refuses to start.
  Dry runs emit zero network requests.
- No retry / no exponential backoff on connection errors (protocol section 6):
  a condition stops after N consecutive failures and enters recovery
  observation instead of pushing on.
- Thresholds in ``CONFIG["thresholds"]`` were frozen by human review on
  2026-08-25; changing them requires a new protocol review.

Outputs (protocol section 8): ``manifest.json``, ``records.jsonl`` and
``results.json`` under ``data/characterization/<run_id>/`` (or ``--out-dir``).
Results contain facts and PASS/FAIL states only - never architecture
interpretation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Frozen configuration (protocol sections 1, 4, 5).
# ---------------------------------------------------------------------------

CONFIG: dict[str, Any] = {
    "endpoint": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "temperature": 0.1,
    "response_format": {"type": "json_object"},
    # PROPOSED values frozen by human review on 2026-08-25 - DO NOT MODIFY.
    "thresholds": {
        "X": 90,
        "Y": 3,
        "Z": 60,
        "W": 5,
        "Q0": 300,
        "T_max": 900,
        "N": 5,
        "rolling_windows": [1, 5, 10],
        "conditions": {
            "A": {"interval": 30, "count": 20},
            "B": {"interval": 5, "count": 40},
            "C": {"interval": 1, "count": 60},
            "D": {"flow": ["pause", "probe", "confirm"]},
        },
    },
}

#: Approved execution window for LIVE runs (UTC). Hard lock, see module docstring.
#: Window authorized by human CAO on 2026-08-30 (char-001): immediate execution,
#: 2h duration, supersedes the unused 02:00Z..04:00Z registration. Provenance
#: chain: 2026-08-27T02:00Z..06:00Z (expired) -> 2026-08-30T00:00Z..00:30Z ->
#: 2026-08-30T00:30Z..01:00Z -> 2026-08-30T02:00Z..04:00Z (expired unused) ->
#: 2026-08-30T07:53Z..09:53Z. Thresholds and state machine unchanged.
EXECUTION_WINDOW_UTC: tuple[str, str] = ("2026-08-30T07:53:00Z", "2026-08-30T09:53:00Z")

#: Fixed synthetic payload - transport parameters identical to the judge path,
#: but no real challenge case (protocol section 2).
_PROBE_SYSTEM_PROMPT = "You are an evaluation judge. Respond only with a JSON object."
_PROBE_USER_PROMPT = (
    'Synthetic infrastructure probe. Return a JSON object {"status": "ok"}.'
)

#: The 17 frozen record fields (protocol section 1), in order.
RECORD_KEYS: tuple[str, ...] = (
    "request_id",
    "run_id",
    "condition_id",
    "timestamp_start",
    "timestamp_end",
    "base_url",
    "model",
    "judge_mode",
    "result",
    "exception_type",
    "exception_message",
    "exception_cause",
    "elapsed_seconds",
    "inter_request_interval",
    "rolling_requests_per_minute",
    "cumulative_request_number",
    "consecutive_failures",
)

_AUTH_BILLING_TYPE_NAMES = {"AuthenticationError", "InsufficientBalanceError"}


# ---------------------------------------------------------------------------
# Time helpers.
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    """ISO-8601 UTC with a ``Z`` suffix."""
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def check_execution_window(now: datetime | None = None) -> tuple[bool, str]:
    """Return (in_window, reason). Live runs must start inside the window."""
    current = now or _utc_now()
    start = _parse_iso(EXECUTION_WINDOW_UTC[0])
    end = _parse_iso(EXECUTION_WINDOW_UTC[1])
    if start <= current <= end:
        return True, f"now={_iso(current)} inside approved window"
    return False, (
        f"now={_iso(current)} outside approved live window "
        f"{EXECUTION_WINDOW_UTC[0]}..{EXECUTION_WINDOW_UTC[1]}"
    )


# ---------------------------------------------------------------------------
# Pure helpers (offline-tested by the ``selftest`` subcommand).
# ---------------------------------------------------------------------------


def load_api_key() -> tuple[str, str]:
    """Load DEEPSEEK_API_KEY from env. Returns (key_or_empty, source_label)."""
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    return key, ("env:DEEPSEEK_API_KEY" if key else "missing")


def key_fingerprint(key: str) -> str:
    """Short non-reversible fingerprint so manifests can identify a key safely."""
    if not key:
        return "none"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def cause_chain_repr(exc: BaseException, limit: int = 500) -> str | None:
    """repr() chain of ``exc.__cause__`` truncated to ``limit`` chars (field 12)."""
    causes: list[str] = []
    current: BaseException | None = exc.__cause__
    while current is not None and len(causes) < 4:
        causes.append(repr(current))
        current = current.__cause__
    if not causes:
        return None
    return " | ".join(causes)[:limit]


def exception_fields(exc: BaseException) -> tuple[str, str, str | None]:
    """(type name, message, cause chain) - closes the Incident UNKNOWN gap."""
    return type(exc).__name__, str(exc), cause_chain_repr(exc)


def is_auth_or_billing(exc: BaseException) -> bool:
    """Global-abort detector: account state changed mid-run (section 6)."""
    if type(exc).__name__ in _AUTH_BILLING_TYPE_NAMES:
        return True
    status = getattr(exc, "status_code", None)
    if status in (401, 402):
        return True
    return "insufficient balance" in str(exc).lower()


def classify(judge_mode: str) -> str:
    """Frozen rule (field 9): success <=> judge_mode == "deepseek"."""
    return "success" if judge_mode == "deepseek" else "failure"


def compute_rolling(previous_starts: list[datetime], current: datetime) -> dict[str, int]:
    """Trailing rolling request counts (minutes) over prior request starts.

    Window semantics are half-open ``(current - window, current]``: a request
    started exactly ``window`` ago is excluded.
    """
    windows = CONFIG["thresholds"]["rolling_windows"]
    cutoffs = {m: current.timestamp() - m * 60 for m in windows}
    return {f"{m}min": sum(1 for s in previous_starts if s.timestamp() > cut)
            for m, cut in cutoffs.items()}


def evaluate_condition(records: list[dict[str, Any]], condition_id: str) -> dict[str, Any]:
    """Apply frozen S1-S3 to A/B; mark C observational; summarize any condition."""
    th = CONFIG["thresholds"]
    total = len(records)
    successes = sum(1 for r in records if r["result"] == "success")
    rate = round(100.0 * successes / total, 2) if total else 0.0
    max_streak = 0
    streak = 0
    for r in records:
        streak = 0 if r["result"] == "success" else streak + 1
        max_streak = max(max_streak, streak)
    trailing_failures = 0
    for r in reversed(records):
        if r["result"] != "failure":
            break
        trailing_failures += 1

    info: dict[str, Any] = {
        "requests": total,
        "successes": successes,
        "failures": total - successes,
        "success_rate": rate,
        "max_consecutive_failures": max_streak,
        "trailing_failure_run_length": trailing_failures,
    }
    if condition_id in ("A", "B"):
        s1 = rate >= th["X"]
        s2 = max_streak <= th["Y"]
        s3 = trailing_failures < th["W"]
        info["S1_success_rate_ge_X"] = s1
        info["S2_max_consecutive_le_Y"] = s2
        info["S3_no_permanent_window"] = s3
        info["passed"] = bool(s1 and s2 and s3)
    elif condition_id == "C":
        info["pass_criteria"] = "NOT_APPLIED_OBSERVATIONAL"
    return info


# ---------------------------------------------------------------------------
# Preflight gate G1 (stdlib only - no openai package needed for preflight).
# ---------------------------------------------------------------------------


def g1_connectivity(endpoint: str, api_key: str, timeout: float = 15.0) -> dict[str, Any]:
    """GET <endpoint>/models must return HTTP 2xx and not 401/402 (gate G1)."""
    url = endpoint.rstrip("/") + "/models"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            code = int(resp.status)
        detail = "http_2xx"
    except urllib.error.HTTPError as exc:
        code = int(exc.code)
        detail = f"http_error_{code}"
    except Exception as exc:  # transport-level failure: DNS/TLS/refused/timeout
        code = -1
        detail = f"{type(exc).__name__}: {exc}"
    passed = 200 <= code < 300 and code not in (401, 402)
    return {"gate": "G1_connectivity", "http_status": code, "detail": detail, "passed": passed}


def g2_config_snapshot(run_id: str, dry_run: bool) -> dict[str, Any]:
    """Configuration snapshot for manifest.json (gate G2)."""
    key, source = load_api_key()
    proxy_names = (
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
        "http_proxy", "https_proxy", "all_proxy", "no_proxy",
    )
    proxies = {n: os.environ[n] for n in proxy_names if os.environ.get(n) is not None}
    return {
        "gate": "G2_config_snapshot",
        "passed": True,
        "run_id": run_id,
        "base_url": CONFIG["endpoint"],
        "model": CONFIG["model"],
        "api_key_source": source,
        "api_key_fingerprint": key_fingerprint(key),
        "proxy_env_vars": proxies,
        "launch_command": [sys.executable, *sys.argv],
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "dry_run": dry_run,
        "execution_window_utc": list(EXECUTION_WINDOW_UTC),
        "thresholds_frozen": CONFIG["thresholds"],
    }


# ---------------------------------------------------------------------------
# The characterization run.
# ---------------------------------------------------------------------------


class CharacterizationRun:
    """Executes the frozen A/B/C/D matrix and writes the three output files."""

    def __init__(
        self,
        run_id: str,
        conditions: list[str],
        out_dir: Path,
        *,
        dry_run: bool = False,
        interval_scale: float = 1.0,
    ) -> None:
        if interval_scale != 1.0 and not dry_run:
            raise ValueError("interval_scale is only allowed together with --dry-run")
        self.run_id = run_id
        self.conditions = conditions
        self.out_dir = out_dir
        self.dry_run = dry_run
        self.scale = interval_scale if dry_run else 1.0
        self.records: list[dict[str, Any]] = []
        self.streak = 0
        self.abort_reason: str | None = None
        self.stopped_conditions: list[str] = []
        self.executed: list[str] = []
        self.summaries: dict[str, dict[str, Any]] = {}
        self.d_summary: dict[str, Any] = {}
        self.g2_snapshot: dict[str, Any] = {}
        self.started_iso = _iso(_utc_now())
        self._file = None
        self._last_start: datetime | None = None

    # -- output plumbing ----------------------------------------------------

    def _paths(self) -> tuple[Path, Path, Path]:
        return (
            self.out_dir / "manifest.json",
            self.out_dir / "records.jsonl",
            self.out_dir / "results.json",
        )

    def _write_manifest(self, final_status: str, gates: list[dict[str, Any]]) -> None:
        manifest_path, _, _ = self._paths()
        manifest = {
            "run_id": self.run_id,
            "final_status": final_status,
            "started_utc": self.started_iso,
            "finished_utc": _iso(_utc_now()),
            "conditions_planned": self.conditions,
            "conditions_executed": self.executed,
            "requests_total": len(self.records),
            "gates": gates,
            "config_snapshot": self.g2_snapshot,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                                 encoding="utf-8")

    def _write_results(self, results_path: Path, final_status: str) -> None:
        th = CONFIG["thresholds"]
        results: dict[str, Any] = {
            "run_id": self.run_id,
            "window": f"{EXECUTION_WINDOW_UTC[0]}/{EXECUTION_WINDOW_UTC[1]}",
            "generated_at_utc": _iso(_utc_now()),
            "dry_run": self.dry_run,
            "final_status": final_status,
            "thresholds_frozen": {k: v for k, v in th.items() if k != "conditions"},
            "conditions": {},
            "notes": [
                "facts and PASS/FAIL states only; architecture interpretation "
                "excluded (protocol section 0)"
            ],
        }
        for cond in self.executed:
            if cond == "D":
                results["conditions"]["D"] = dict(self.d_summary)
            else:
                results["conditions"][cond] = dict(self.summaries.get(cond, {}))
        results_path.write_text(
            json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _append_record(self, record: dict[str, Any]) -> None:
        public = {k: v for k, v in record.items() if not k.startswith("_")}
        assert self._file is not None, "records file not opened"
        self._file.write(json.dumps(public, ensure_ascii=False) + "\n")
        self._file.flush()

    # -- request layer -------------------------------------------------------

    def _probe_once(self, condition_id: str) -> dict[str, Any]:
        ts_start = _utc_now()
        mono_start = time.monotonic()
        judge_mode = "deepseek"
        exc_type: str | None = None
        exc_msg: str | None = None
        exc_cause: str | None = None
        if self.dry_run:
            time.sleep(0.001)  # simulated transport latency, zero network
        else:
            import openai  # lazy import: only the live path needs the SDK

            key, _source = load_api_key()
            if not key:
                raise RuntimeError("DEEPSEEK_API_KEY not set - refusing live probe")
            client = openai.OpenAI(api_key=key, base_url=CONFIG["endpoint"])
            try:
                response = client.chat.completions.create(
                    model=CONFIG["model"],
                    temperature=CONFIG["temperature"],
                    response_format=CONFIG["response_format"],
                    messages=[
                        {"role": "system", "content": _PROBE_SYSTEM_PROMPT},
                        {"role": "user", "content": _PROBE_USER_PROMPT},
                    ],
                )
                json.loads(response.choices[0].message.content or "")
            except Exception as exc:  # noqa: BLE001 - every exception is data here
                exc_type, exc_msg, exc_cause = exception_fields(exc)
                judge_mode = "rules"
                if is_auth_or_billing(exc):
                    self.abort_reason = (
                        f"auth_or_billing:{exc_type}:{exc_msg[:120]}"
                    )
        ts_end = _utc_now()

        if judge_mode != "deepseek":
            self.streak += 1
        else:
            self.streak = 0
        previous_starts = [r["_start_dt"] for r in self.records]
        interval = (
            None
            if self._last_start is None
            else round((ts_start - self._last_start).total_seconds(), 3)
        )
        record: dict[str, Any] = {
            "request_id": f"{self.run_id}-{len(self.records) + 1:04d}",
            "run_id": self.run_id,
            "condition_id": condition_id,
            "timestamp_start": _iso(ts_start),
            "timestamp_end": _iso(ts_end),
            "base_url": CONFIG["endpoint"],
            "model": CONFIG["model"],
            "judge_mode": judge_mode,
            "result": classify(judge_mode),
            "exception_type": exc_type,
            "exception_message": exc_msg,
            "exception_cause": exc_cause,
            "elapsed_seconds": round(time.monotonic() - mono_start, 3),
            "inter_request_interval": interval,
            "rolling_requests_per_minute": compute_rolling(previous_starts, ts_start),
            "cumulative_request_number": len(self.records) + 1,
            "consecutive_failures": self.streak,
            # internal scheduling fields, stripped from records.jsonl:
            "_start_dt": ts_start,
            "_end_dt": ts_end,
        }
        self._last_start = ts_start
        self._append_record(record)
        self.records.append(record)
        return record

    # -- condition drivers -----------------------------------------------------

    def _sleep_scaled(self, seconds: float) -> None:
        delay = seconds * self.scale
        if delay > 0:
            time.sleep(delay)

    def _quiet_pause(self, seconds: float) -> None:
        if self.abort_reason:
            return
        print(f"  quiet pause {seconds:.0f}s (x{self.scale:g} scale)", flush=True)
        self._sleep_scaled(seconds)

    def _stop_rule_fired(self) -> bool:
        return self.streak >= CONFIG["thresholds"]["N"]

    def _last_failure_end(self) -> datetime | None:
        for record in reversed(self.records):
            if record["result"] == "failure":
                return record["_end_dt"]
        return None

    def _run_fixed_density(self, condition_id: str) -> dict[str, Any]:
        cfg = CONFIG["thresholds"]["conditions"][condition_id]
        count, interval = int(cfg["count"]), float(cfg["interval"])
        start_index = len(self.records)
        stopped = False
        for i in range(count):
            if self.abort_reason:
                break
            target_mono = time.monotonic() + interval * self.scale
            self._probe_once(condition_id)
            if self.abort_reason:
                break
            if self._stop_rule_fired():
                stopped = True
                self.stopped_conditions.append(condition_id)
                print(f"  [stop-rule] {condition_id}: "
                      f"{self.streak} consecutive failures", flush=True)
                break
            if i + 1 < count:
                self._sleep_until(target_mono)
        summary = evaluate_condition(self.records[start_index:], condition_id)
        summary["stopped_by_failure_rule"] = stopped
        return summary

    def _sleep_until(self, target_mono: float) -> None:
        delay = target_mono - time.monotonic()
        if delay > 0:
            time.sleep(delay)

    def _recovery_observation(self) -> None:
        """Section 6: single probes at 60s intervals until success or T_max."""
        th = CONFIG["thresholds"]
        attempts = int(th["T_max"] // 60)
        baseline = self._last_failure_end()
        for attempt in range(attempts):
            if attempt > 0:
                self._sleep_scaled(60)
            if self.abort_reason:
                break
            record = self._probe_once("D")
            if record["result"] == "success":
                latency = (record["_end_dt"] - baseline).total_seconds()
                self.d_summary["recovery_latency_seconds"] = round(latency, 3)
                return
        self.d_summary["recovery_latency_seconds"] = None

    def _run_condition_d(self, c_summary: dict[str, Any]) -> dict[str, Any]:
        th = CONFIG["thresholds"]
        stopped_in_c = bool(c_summary.get("stopped_by_failure_rule"))
        self.d_summary = {
            "variant": "RECOVERY_FLOW" if stopped_in_c else "SUSTAINED_STRESS_C_DENSITY",
            "recovery_latency_seconds": None,
            "stable_recovery": None,
            "S4_pass": None,
        }
        if stopped_in_c:
            print("  D1: recovery probing (60s interval, T_max cap)", flush=True)
            self._recovery_observation()
            latency = self.d_summary["recovery_latency_seconds"]
            if latency is not None:
                print("  D2: recovery confirmation (10 x 5s)", flush=True)
                confirm_ok = 0
                for _ in range(10):
                    if self.abort_reason:
                        break
                    self._sleep_scaled(5)
                    confirm_ok += self._probe_once("D")["result"] == "success"
                self.d_summary["confirmation_successes"] = confirm_ok
                self.d_summary["stable_recovery"] = confirm_ok >= 9
                self.d_summary["S4_pass"] = bool(latency <= th["Z"])
            else:
                self.d_summary["stable_recovery"] = False
                self.d_summary["note"] = "no recovery within T_max"
        else:
            self.d_summary["note"] = "C finished without stop rule; D1/D2 NOT_TRIGGERED"
            start_index = len(self.records)
            interval = float(th["conditions"]["C"]["interval"])
            for i in range(120):
                if self.abort_reason:
                    break
                target_mono = time.monotonic() + interval * self.scale
                self._probe_once("D")
                if self._stop_rule_fired():
                    self.stopped_conditions.append("D")
                    print("  [stop-rule] D sustained stress hit failure threshold",
                          flush=True)
                    break
                if i + 1 < 120:
                    self._sleep_until(target_mono)
            self.d_summary["probes_sent"] = len(self.records) - start_index
        return dict(self.d_summary)

    # -- orchestration ----------------------------------------------------------

    def execute(self) -> Path:
        th = CONFIG["thresholds"]
        self.out_dir.mkdir(parents=True, exist_ok=True)
        manifest_path, records_path, results_path = self._paths()

        gates: list[dict[str, Any]] = []
        if self.dry_run:
            gates.append({"gate": "G1_connectivity", "http_status": None,
                          "detail": "SKIPPED_DRY_RUN", "passed": True})
        else:
            key, _source = load_api_key()
            if not key:
                raise SystemExit("DEEPSEEK_API_KEY not set - cannot start live run")
            gates.append(g1_connectivity(CONFIG["endpoint"], key))
        self.g2_snapshot = g2_config_snapshot(self.run_id, self.dry_run)
        gates.append(dict(self.g2_snapshot))
        gates.append({"gate": "G3_time_registration", "passed": True,
                      "started_utc": self.started_iso})
        if not all(gate["passed"] for gate in gates):
            self._write_manifest("CANCELLED_PREFLIGHT_FAILED", gates)
            raise SystemExit(f"preflight failed: {gates}")

        final_status = "COMPLETED"
        self._file = records_path.open("w", encoding="utf-8")
        try:
            previous_stop = False
            for idx, cond in enumerate(self.conditions):
                if self.abort_reason:
                    final_status = self._aborted_status()
                    break
                if idx > 0:
                    self._quiet_pause(float(th["Q0"]))
                print(f"[condition {cond}]", flush=True)
                if cond == "D":
                    self.summaries["D"] = self._run_condition_d(
                        self.summaries.get("C", {})
                    )
                else:
                    self.summaries[cond] = self._run_fixed_density(cond)
                self.executed.append(cond)
                if self.abort_reason:
                    final_status = self._aborted_status()
                    break
                if cond != "D" and self.summaries[cond].get("stopped_by_failure_rule"):
                    print("  entering recovery observation (section 6)", flush=True)
                    self._recovery_observation()
                    if previous_stop:
                        final_status = "ABORTED_TWO_CONSECUTIVE_CONDITION_STOPS"
                        break
                    previous_stop = True
                else:
                    previous_stop = False
            if self.abort_reason and final_status == "COMPLETED":
                final_status = self._aborted_status()
        finally:
            self._file.close()
            self._write_manifest(final_status, gates)
            self._write_results(results_path, final_status)
        print(f"run finished: {final_status}; outputs in {self.out_dir}", flush=True)
        return results_path

    def _aborted_status(self) -> str:
        reason = (self.abort_reason or "unknown").split(":")[0]
        return f"ABORTED_{reason.upper()}"


# ---------------------------------------------------------------------------
# Public entry points (importable with zero side effects).
# ---------------------------------------------------------------------------

DEFAULT_OUT_ROOT = Path("data") / "characterization"


def preflight(out_dir: Path | None = None, run_id: str = "preflight") -> Path:
    """Execute gates G1-G3 only; writes a manifest; sends exactly one GET."""
    target = out_dir or DEFAULT_OUT_ROOT / run_id
    target.mkdir(parents=True, exist_ok=True)
    key, _source = load_api_key()
    if not key:
        raise SystemExit("DEEPSEEK_API_KEY not set")
    gates = [
        g1_connectivity(CONFIG["endpoint"], key),
        g2_config_snapshot(run_id, dry_run=False),
        {"gate": "G3_time_registration", "passed": True,
         "started_utc": _iso(_utc_now())},
    ]
    status = "PREFLIGHT_PASS" if all(g["passed"] for g in gates) else "PREFLIGHT_FAIL"
    (target / "manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "final_status": status,
                "started_utc": _iso(_utc_now()),
                "finished_utc": _iso(_utc_now()),
                "gates": gates,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(status)
    return target / "manifest.json"


def run_characterization(
    run_id: str = "char-001",
    conditions: list[str] | None = None,
    *,
    dry_run: bool = False,
    out_dir: Path | None = None,
    interval_scale: float = 1.0,
) -> Path:
    """Run the characterization matrix (live: window-locked; dry-run: offline)."""
    if not dry_run:
        in_window, reason = check_execution_window()
        if not in_window:
            raise SystemExit(f"live run refused - outside execution window: {reason}")
    conditions = conditions or ["A", "B", "C", "D"]
    unknown = [c for c in conditions if c not in {"A", "B", "C", "D"}]
    if unknown:
        raise SystemExit(f"unknown conditions: {unknown}")
    runner = CharacterizationRun(
        run_id,
        conditions,
        out_dir or DEFAULT_OUT_ROOT / run_id,
        dry_run=dry_run,
        interval_scale=interval_scale,
    )
    return runner.execute()


# ---------------------------------------------------------------------------
# Offline selftest: pure helpers against synthetic data. Zero network.
# ---------------------------------------------------------------------------


def selftest() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool) -> None:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            failures.append(name)

    # record schema shape (17 frozen fields)
    check("record_keys_count_17", len(RECORD_KEYS) == 17)
    check("record_keys_first", RECORD_KEYS[0] == "request_id")

    # exception capture incl. cause chain
    try:
        try:
            raise OSError("disk on fire")
        except OSError as inner:
            raise ConnectionError("Connection error.") from inner
    except ConnectionError as exc:
        etype, emsg, ecause = exception_fields(exc)
        check("exception_type", etype == "ConnectionError")
        check("exception_message", emsg == "Connection error.")
        check("exception_cause_chain", ecause is not None and "OSError" in ecause)

    # cause-chain truncation at 500 chars
    nested: BaseException = ValueError("root")
    for layer in range(50):
        wrapper = RuntimeError(f"layer-{layer}-{'x' * 200}")
        wrapper.__cause__ = nested
        nested = wrapper
    _, _, deep = exception_fields(nested)
    check("exception_cause_truncated_500", deep is not None and len(deep) <= 500)

    # rolling window arithmetic: 150 requests spaced 1s over 2.5 minutes
    base = datetime(2026, 8, 27, 2, 0, 0, tzinfo=timezone.utc)
    starts = [base + timedelta(seconds=i) for i in range(150)]
    rolling = compute_rolling(starts, starts[-1])
    check("rolling_10min_all", rolling["10min"] == 150)
    check("rolling_1min_last_60", rolling["1min"] == 60)

    # frozen success rule
    check("classify_success", classify("deepseek") == "success")
    check("classify_failure", classify("rules") == "failure")

    # threshold evaluation: clean condition A passes all of S1-S3
    clean = [{"result": "success"} for _ in range(20)]
    ev_clean = evaluate_condition(clean, "A")
    check("evaluate_A_pass", ev_clean["passed"] is True)
    check("evaluate_A_rate_100", ev_clean["success_rate"] == 100.0)

    # permanent failure window (trailing run >= W=5) fails S3
    bad = [{"result": "success"}] * 15 + [{"result": "failure"}] * 5
    ev_bad = evaluate_condition(bad, "B")
    check("evaluate_B_permanent_window_fails", ev_bad["passed"] is False)
    check("evaluate_B_trailing_len_5", ev_bad["trailing_failure_run_length"] == 5)

    # C is observational regardless of numbers
    ev_c = evaluate_condition(bad, "C")
    check("evaluate_C_not_applied", ev_c.get("pass_criteria") == "NOT_APPLIED_OBSERVATIONAL")

    # auth/billing detector
    class FakeStatusError(Exception):
        status_code = 402

    check("billing_via_status_code", is_auth_or_billing(FakeStatusError("Insufficient Balance")))
    check("plain_conn_error_not_billing", not is_auth_or_billing(ConnectionError("refused")))

    # window guard math (samples tied to EXECUTION_WINDOW_UTC)
    inside = check_execution_window(_parse_iso("2026-08-30T08:53:00Z"))
    outside = check_execution_window(_parse_iso("2026-08-30T10:53:00Z"))
    check("window_inside_true", inside[0] is True)
    check("window_outside_false", outside[0] is False)

    print(f"selftest: {'ALL PASS' if not failures else f'FAILURES: {failures}'}")
    return 0 if not failures else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 4 infrastructure characterization probe (frozen)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("show-config", help="print frozen CONFIG and execution window")
    sub.add_parser("selftest", help="offline helper assertions (zero network)")
    p_pre = sub.add_parser("preflight", help="run gates G1-G3 only (one GET request)")
    p_pre.add_argument("--out-dir", type=Path, default=None)
    p_pre.add_argument("--run-id", default="preflight")
    p_run = sub.add_parser("run", help="execute the characterization matrix")
    p_run.add_argument("--run-id", default="char-001")
    p_run.add_argument("--conditions", default="A,B,C,D")
    p_run.add_argument(
        "--dry-run",
        action="store_true",
        help="offline state-machine validation; emits zero network requests",
    )
    p_run.add_argument(
        "--dry-run-interval-scale",
        type=float,
        default=1.0,
        help="time compression for dry runs only (live runs always use 1.0)",
    )
    p_run.add_argument("--out-dir", type=Path, default=None)

    args = parser.parse_args(argv)
    if args.command == "show-config":
        print(json.dumps(
            {"CONFIG": CONFIG, "EXECUTION_WINDOW_UTC": EXECUTION_WINDOW_UTC},
            indent=2,
            ensure_ascii=False,
        ))
        return 0
    if args.command == "selftest":
        return selftest()
    if args.command == "preflight":
        preflight(args.out_dir, args.run_id)
        return 0
    if args.command == "run":
        conds = [c.strip().upper() for c in args.conditions.split(",") if c.strip()]
        run_characterization(
            args.run_id,
            conds,
            dry_run=args.dry_run,
            out_dir=args.out_dir,
            interval_scale=args.dry_run_interval_scale,
        )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
