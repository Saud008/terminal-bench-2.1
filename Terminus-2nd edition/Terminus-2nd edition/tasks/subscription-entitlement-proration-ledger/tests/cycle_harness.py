from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

CTL_BIN = "/app/bin/subledctl"
DB_PATH = Path("/app/state/billing.db")
INVOICE_JSON = Path("/app/output/subscription-invoices.json")
BUFFER_JSON = Path("/app/work/entitlement-buffer.json")
FIXTURE_ROOT = Path(os.environ.get("TB3_FIXTURE_DIR", "/app/fixtures"))


def reset_billing_workspace() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def exec_subledctl(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [CTL_BIN, *args],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )


def drive_billing_cycle(scenario: str, fixture_root: Path | None = None) -> None:
    root = fixture_root or FIXTURE_ROOT
    steps = [
        ["load-cycle", "--scenario", scenario, "--fixture-dir", str(root)],
        ["reconcile-entitlements", "--scenario", scenario],
        ["publish-invoices", "--scenario", scenario],
    ]
    for step in steps:
        proc = exec_subledctl(step)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def load_reconcile_counter() -> dict:
    return json.loads(Path("/app/state/reconcile-pass.json").read_text(encoding="utf-8"))
