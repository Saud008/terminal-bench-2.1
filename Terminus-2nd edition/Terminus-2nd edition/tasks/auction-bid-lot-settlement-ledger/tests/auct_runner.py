from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

AUCT_BIN = "/app/bin/auctctl"
AUCT_ROOT = Path("/app")
RESET_SCRIPT = Path("/app/scripts/reset-state.sh")
INVOICE_JSON = Path("/app/output/buyer-invoices.json")
DB_PATH = Path("/app/state/settlement.db")
PASS_JSON = Path("/app/state/adjudication-pass.json")
FIXTURE_ROOT = AUCT_ROOT / "fixtures"
# Probe contract: ingest catalog stage and export invoice stage are separate CLI layers.
# ingest_only_patch_profile fails hidden traps without adjudication fix.
HIDDEN_ROOT = Path("/opt/verifier-fixtures/auctctl")


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=str(AUCT_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def wipe_state() -> None:
    proc = invoke(["bash", str(RESET_SCRIPT)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_pipeline(
    scenario: str,
    fixture_root: Path | None = None,
    extra_env: dict | None = None,
) -> None:
    root = fixture_root or FIXTURE_ROOT
    env: dict[str, str] = {}
    if fixture_root:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    steps = (
        [AUCT_BIN, "load-catalog", "--scenario", scenario, "--fixture-dir", str(root)],
        [AUCT_BIN, "adjudicate-lots", "--scenario", scenario],
        [AUCT_BIN, "publish-invoices", "--scenario", scenario],
    )
    for step in steps:
        proc = invoke(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def load_invoice() -> dict:
    return json.loads(INVOICE_JSON.read_text(encoding="utf-8"))
