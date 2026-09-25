"""Entry pytest module — subprocess CLI smoke and reference parity."""

from __future__ import annotations

import json
import subprocess

from run_originctl import ATLAS_JSON, FIXTURE_ROOT, ORIGIN_BIN, run_pipeline, wipe_state
from tariff_ref import reference_classifications
def test_tout_subprocess_cli_parse_manifest() -> None:
    """Every verifier run must invoke originctl via subprocess, not in-process imports."""
    wipe_state()
    proc = subprocess.run(
        [ORIGIN_BIN, "parse-shipment", "--manifest", "preferential-clean", "--fixture-dir", str(FIXTURE_ROOT)],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
def test_tout_reference_classifications_preferential_clean() -> None:
    """preferential treatment must match independent reference_classifications math."""
    wipe_state()
    run_pipeline("preferential-clean")
    body = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_classifications("preferential-clean", FIXTURE_ROOT)
    assert body["classifications"] == ref["classifications"]
