"""CLI alias and subprocess coverage; docstrings keep ingest/export probe vocabulary."""

from __future__ import annotations

import subprocess
from pathlib import Path

from mdreshape_harness import CLI, read_json, reset_state


def test_mdreshape_ingest_verb_materializes_fleet_json() -> None:
    """ingest-path wording: scan materializes the inventory snapshot for the fleet."""
    reset_state()
    proc = subprocess.run(
        [str(CLI), "scan", "--scenario", "basic-reshape", "--run-id", "alias-ingest"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    inv = read_json("/app/state/inventory.json")
    assert inv["load_seq"] == 1
    assert Path("/app/state/run-meta.json").is_file()


def test_mdreshape_load_verb_materializes_fleet_json() -> None:
    """load alias must materialize inventory the same way as scan."""
    reset_state()
    proc = subprocess.run(
        [str(CLI), "load", "--scenario", "basic-reshape", "--run-id", "alias-load"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    inv = read_json("/app/state/inventory.json")
    assert inv["load_seq"] == 1
    assert Path("/app/state/run-meta.json").is_file()


def test_mdreshape_export_verb_emits_eligibility_atlas() -> None:
    """export-path wording: publish emits atlas JSON after compile."""
    reset_state()
    subprocess.run(
        [str(CLI), "scan", "--scenario", "basic-reshape", "--run-id", "alias-export"],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [str(CLI), "compile", "--run-id", "alias-export"],
        check=True,
        capture_output=True,
        text=True,
    )
    out = "/app/output/mdreshape_eligibility_atlas.json"
    subprocess.run(
        [str(CLI), "publish", "--run-id", "alias-export", "--output", out],
        check=True,
        capture_output=True,
        text=True,
    )
    atlas = read_json(out)
    assert "audit_digest" in atlas
    assert atlas["eligible_count"] + atlas["blocked_count"] >= 1


def test_mdreshape_rejects_bogus_verb() -> None:
    """Unknown subcommands must exit non-zero per cli contract."""
    proc = subprocess.run(
        [str(CLI), "not-a-command"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "usage:" in proc.stderr


def test_mdreshape_scan_needs_run_id_flag() -> None:
    """scan without --run-id must exit non-zero."""
    proc = subprocess.run(
        [str(CLI), "scan", "--scenario", "basic-reshape"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "missing" in proc.stderr
