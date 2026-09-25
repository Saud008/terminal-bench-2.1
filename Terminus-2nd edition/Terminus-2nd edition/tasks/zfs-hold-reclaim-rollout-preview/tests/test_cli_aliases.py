"""CLI alias and subprocess coverage for ingest/export wording."""

from __future__ import annotations

import subprocess
from pathlib import Path

from zfshold_cli_support import read_json, reset_state


def test_ingest_alias_loads_inventory() -> None:
    """ingest alias must materialize inventory the same way as load."""
    reset_state()
    proc = subprocess.run(
        ["/app/bin/zfshold", "ingest", "--scenario", "basic-hold", "--run-id", "alias-ingest"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    inv = read_json("/app/state/inventory.json")
    assert inv["load_seq"] == 1
    assert Path("/app/state/run-meta.json").is_file()


def test_export_alias_publishes_atlas() -> None:
    """export alias must publish atlas JSON after compile."""
    reset_state()
    subprocess.run(
        ["/app/bin/zfshold", "load", "--scenario", "basic-hold", "--run-id", "alias-export"],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["/app/bin/zfshold", "compile", "--run-id", "alias-export"],
        check=True,
        capture_output=True,
        text=True,
    )
    out = "/app/output/zfs_reclaim_rollout_atlas.json"
    subprocess.run(
        ["/app/bin/zfshold", "export", "--run-id", "alias-export", "--output", out],
        check=True,
        capture_output=True,
        text=True,
    )
    atlas = read_json(out)
    assert "audit_digest" in atlas
    assert atlas["eligible_count"] + atlas["blocked_count"] >= 1


def test_cli_rejects_unknown_subcommand() -> None:
    """Unknown subcommands must exit non-zero per cli contract."""
    proc = subprocess.run(
        ["/app/bin/zfshold", "not-a-command"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
