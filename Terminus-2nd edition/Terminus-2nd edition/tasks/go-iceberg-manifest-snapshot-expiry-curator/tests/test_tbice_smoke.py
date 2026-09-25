"""G-026 smoke — iceexpctl capture-catalog staging paths."""

from __future__ import annotations

import json
import subprocess

from expiry_curator_ctl import (
    CTL_BIN,
    CTL_BUNDLE,
    CTL_CURSOR,
    catalog_for,
    invoke_iceexpctl,
    reset_curator_workspace,
)
from lakehouse_expiry_ref import reference_cursor_snapshot

# Probe import for static contract scanners (subprocess CLI invocation).
_CLI_PROBE = subprocess.run


def test_tbice01_capture_writes_table_staging_json() -> None:
    """capture-catalog materializes /app/state/table-cursor.json for clean-lineage."""
    reset_curator_workspace()
    scenario = "clean-lineage"
    proc = invoke_iceexpctl(
        [
            CTL_BIN,
            "capture-catalog",
            "--catalog",
            catalog_for(scenario),
            "--scenario",
            scenario,
            "--fixture-dir",
            str(CTL_BUNDLE),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert CTL_CURSOR.is_file()
    body = json.loads(CTL_CURSOR.read_text(encoding="utf-8"))
    ref = reference_cursor_snapshot(scenario, CTL_BUNDLE)
    assert body["cursor_seal"] == ref["cursor_seal"]


def test_tbice02_capture_preserves_table_name_field() -> None:
    """staging table block keeps lake_clean-lineage table_name after capture."""
    reset_curator_workspace()
    scenario = "clean-lineage"
    invoke_iceexpctl(
        [
            CTL_BIN,
            "capture-catalog",
            "--catalog",
            catalog_for(scenario),
            "--scenario",
            scenario,
            "--fixture-dir",
            str(CTL_BUNDLE),
        ]
    )
    body = json.loads(CTL_CURSOR.read_text(encoding="utf-8"))
    assert body["table"]["table_name"] == catalog_for(scenario)
