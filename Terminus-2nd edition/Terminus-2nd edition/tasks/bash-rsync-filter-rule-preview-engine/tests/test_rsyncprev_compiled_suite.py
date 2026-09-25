"""Compiled-state rsyncprev tests."""

from __future__ import annotations

import json
from pathlib import Path

from rsyncprev_cli_support import COMPILED, invoke, run_pipeline, wipe, CLI


def test_inventory_requires_tree_and_run_id():
    """ingest subcommand must reject missing run-id per cli-contract.md."""
    wipe()
    proc = invoke([str(CLI), "ingest", "--tree", "media-sync"])
    assert proc.returncode != 0


def test_compile_requires_inventory_first():
    """compile must fail when inventory file for run-id is absent."""
    wipe()
    proc = invoke([str(CLI), "compile", "--run-id", "missing"])
    assert proc.returncode != 0


def test_inventory_writes_work_file():
    """ingest writes /app/work/<run-id>-inventory.json for downstream compile."""
    wipe()
    proc = invoke([str(CLI), "ingest", "--tree", "media-sync", "--run-id", "run-inv"])
    assert proc.returncode == 0
    assert Path("/app/work/run-inv-inventory.json").is_file()


def test_staging_has_rule_cascade_entries():
    """filter-compiled.json must include rule_cascade rows after compile."""
    wipe()
    run_pipeline("media-sync", "run-cascade")
    st = json.loads(COMPILED.read_text(encoding="utf-8"))
    assert st["rule_cascade"]
    assert "path" in st["rule_cascade"][0]


def test_prune_true_for_excluded_directory():
    """prune traversal marks excluded directory cache with prune true."""
    wipe()
    out = run_pipeline("media-sync", "run-prune")
    rows = json.loads(out.read_text(encoding="utf-8"))["path_verdicts"]
    d = next(r for r in rows if r["path"] == "cache")
    assert d["prune"] is True
