"""TB3 hidden trap tests for rosterctl membership ops."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from roster_refmath import reference_export
from roster_shell_ops import (
    CLUSTER,
    OFF_CATALOG,
    PATHS,
    drive_full_attestation_run,
    read_jsonl,
    wipe_workspace,
)


def test_roster_tb3_hidden_truncation_poison_fixture_dir() -> None:
    """TB3_FIXTURE_DIR at /opt/verifier-fixtures/rosterctl drives hidden truncation poison."""
    wipe_workspace()
    drive_full_attestation_run("hidden-truncation-poison", OFF_CATALOG)
    ledger = read_jsonl(PATHS["ledger"])
    ref, _ = reference_export(CLUSTER, "hidden-truncation-poison", OFF_CATALOG)
    assert ledger == ref
    assert Path("/opt/verifier-fixtures/rosterctl/hidden-truncation-poison").is_dir()


def test_roster_tb3_hidden_uncommitted_leader_partial_fix_fails() -> None:
    """Hidden uncommitted leader trap under verifier-fixtures fails export-only partial fixes."""
    wipe_workspace()
    drive_full_attestation_run("hidden-uncommitted-leader", OFF_CATALOG)
    staging = json.loads(PATHS["staging"].read_text(encoding="utf-8"))
    assert staging["leader_id"]
    ledger = read_jsonl(PATHS["ledger"])
    ref, _ = reference_export(CLUSTER, "hidden-uncommitted-leader", OFF_CATALOG)
    assert ledger == ref


def test_roster_tb3_subprocess_cli_rebuild_wrapper() -> None:
    """Subprocess rebuild wrapper stays executable for rosterctl."""
    proc = subprocess.run(
        ["bash", "/app/scripts/verifier-rebuild.sh"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
