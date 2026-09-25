"""Minimal ttalloc smoke surface — deeper contracts live in sibling modules."""
from __future__ import annotations

import json
from pathlib import Path

from ttalloc_refmath import reference_assignments
from ttalloc_driver import ATLAS_JSON, CLI_BIN, FIXTURE_ROOT, SCENARIO_CLEAN, run_pipeline, wipe_state


def test_t6c5f5b_ttalloc_section_binary_present():
    """ttalloc binary must exist at the documented /app/bin path."""
    assert Path(CLI_BIN).exists()


def test_t6c5f5b_ttalloc_section_cli_rejects_empty_argv():
    """Invoking ttalloc without a subcommand must exit non-zero."""
    import subprocess

    proc = subprocess.run([CLI_BIN], capture_output=True, text=True, check=False)
    assert proc.returncode != 0


def test_t6c5f5b_ttalloc_section_clean_atlas_matches_ref():
    """Clean scenario atlas assignments must match independent reference math."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_assignments(FIXTURE_ROOT, SCENARIO_CLEAN)
    assert atlas["assignments"] == ref["assignments"]
