"""Hidden TB3 rsyncprev trap tests."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from rsyncprev_cli_support import run_pipeline, wipe
from rsyncprev_contract_math import reference_preview


def _overlay_hidden(tree: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="tb3-rsfp-"))
    src = Path("/opt/verifier-fixtures/rsyncprev/trees") / tree
    dst = tmp / tree
    shutil.copytree(src, dst)
    return tmp


def test_hidden_prune_anchor_contract():
    """TB3 trap via /opt/verifier-fixtures/rsyncprev/trees/tb3-prune-anchor."""
    wipe()
    root = _overlay_hidden("tb3-prune-anchor")
    out = run_pipeline("tb3-prune-anchor", "run-h1", tree_root=root)
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_preview(root / "tb3-prune-anchor" / "manifest.json", "run-h1")
    assert got == ref


def test_hidden_delete_risk_contract():
    """TB3_TREE_ROOT delete-risk trap under /opt/verifier-fixtures/rsyncprev."""
    wipe()
    root = _overlay_hidden("tb3-delete-risk")
    out = run_pipeline("tb3-delete-risk", "run-h2", tree_root=root)
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_preview(root / "tb3-delete-risk" / "manifest.json", "run-h2")
    assert got == ref


def test_hidden_candidate_and_protected_counts():
    """hidden delete-risk tree must emit both candidate and protected summary counts."""
    wipe()
    root = _overlay_hidden("tb3-delete-risk")
    out = run_pipeline("tb3-delete-risk", "run-h3", tree_root=root)
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got["summary"]["candidate_delete_count"] >= 1
    assert got["summary"]["protected_delete_count"] >= 1


def test_hidden_path_order_stability():
    """hidden prune-anchor preview keeps path_verdicts sorted by path."""
    wipe()
    root = _overlay_hidden("tb3-prune-anchor")
    out = run_pipeline("tb3-prune-anchor", "run-h4", tree_root=root)
    rows = json.loads(out.read_text(encoding="utf-8"))["path_verdicts"]
    paths = [r["path"] for r in rows]
    assert paths == sorted(paths)
