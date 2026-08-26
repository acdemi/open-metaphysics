# Scripts

Utility scripts for setup, deployment, and maintenance.

## Available

- `setup-dev.sh` -- One-command developer environment setup (Unix/macOS)
- `setup-dev.ps1` -- One-command developer environment setup (Windows)
- `infra_probe.py` -- Phase 4 infrastructure characterization probe (governance-gated; see below)

---

## `infra_probe.py` — Infrastructure Characterization Probe

Implements `docs/governance/phase4/INFRASTRUCTURE_CHARACTERIZATION_PROTOCOL.md`
(sections 1–7). Standalone: touches no experiment/agent/benchmark code.

### Modes

```bash
# frozen config + approved live window (no side effects)
python -m scripts.infra_probe show-config

# offline helper assertions (zero network)
python -m scripts.infra_probe selftest

# preflight gates G1-G3 (sends exactly one GET <endpoint>/models)
python -m scripts.infra_probe preflight --run-id preflight

# OFFLINE state-machine validation; emits zero network requests
python -m scripts.infra_probe run --dry-run --dry-run-interval-scale 0.01 \
    --out-dir /tmp/probe-dry

# LIVE characterization run - refused outside the approved window
# (EXECUTION_WINDOW_UTC, currently 2026-08-27T02:00Z..06:00Z); requires
# DEEPSEEK_API_KEY in the environment and explicit human authorization.
python -m scripts.infra_probe run --run-id char-001
```

### Frozen configuration

Thresholds (`X=90, Y=3, Z=60, W=5, Q0=300, T_max=900, N=5`) are hard-frozen in
`CONFIG["thresholds"]` per the 2026-08-25 human review. Changing them requires
a new protocol review. The endpoint is pinned to `https://api.deepseek.com` /
`deepseek-chat`.

### Behavior rules baked into the code

- No retry and no exponential backoff on connection errors. A condition stops
  after `N` consecutive failures and enters recovery observation instead.
- Global abort on auth/billing errors (`401` / `402` / "Insufficient Balance").
- Every request records all 17 protocol fields; `base_url`/`model` are captured
  from the effective runtime configuration, and exceptions store
  type + message + `__cause__` chain (repr, truncated to 500 chars).
- Results contain facts and PASS/FAIL states only.

### Outputs (`data/characterization/<run_id>/`)

| File | Content |
|------|---------|
| `manifest.json` | Preflight snapshot: gates G1–G3, key fingerprint (not the key), proxy env vars, launch command, UTC start/end |
| `records.jsonl` | One 17-field JSON object per probe request (protocol section 1) |
| `results.json` | Per-condition summaries, S1–S4 verdicts, recovery latency; no interpretation |

### Dependencies

Standard library only for import/preflight/dry-run/selftest. The `openai`
package is required only by the live `run` mode (imported lazily at request
time) and must be installed in the environment that executes live runs.

