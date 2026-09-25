from __future__ import annotations

import os
import subprocess
from pathlib import Path

CTL_BIN = "/app/bin/ppareconctl"
JSONL_PATH = Path("/app/state/settlement-lines.jsonl")
DB_PATH = Path("/app/state/ppa-settlement.db")
INVOICE_PATH = Path("/app/output/invoice-rollup.json")
FIXTURE_ROOT = Path(os.environ.get("TB3_FIXTURE_DIR", "/app/fixtures"))
OVERLAY_FIXTURES = Path("/opt/verifier-fixtures/ppareconctl")


def reset_ppa_workspace() -> None:
    subprocess.run(["bash", "/app/scripts/reset-state.sh"], check=True)


def exec_ppareconctl(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [CTL_BIN, *args],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def run_ingest_materialize_lines(scenario: str, fixture_root: Path | None = None) -> None:
    """Ingest meter readings into the staging settlement-lines artifact."""
    root = fixture_root or FIXTURE_ROOT
    proc = exec_ppareconctl(
        ["materialize-lines", "--scenario", scenario, "--fixture-dir", str(root)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def run_export_invoice_rollup(scenario: str, fixture_root: Path | None = None) -> None:
    """Export invoice rollup JSON from staged settlement lines."""
    root = fixture_root or FIXTURE_ROOT
    proc = exec_ppareconctl(
        ["rollup-billing-invoice", "--scenario", scenario, "--fixture-dir", str(root)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def run_ppa_billing_pipeline(scenario: str, fixture_root: Path | None = None) -> None:
    root = fixture_root or FIXTURE_ROOT
    run_ingest_materialize_lines(scenario, root)
    run_export_invoice_rollup(scenario, root)


# Back-compat alias for older test imports
drive_settlement = run_ppa_billing_pipeline
