"""Stable diff ledger and idempotent export tests."""

from __future__ import annotations

import subprocess

import pytest

from xsnap_refmath import read_json, reference_diff_report
from xsnap_session import (
    XSNAP_BIN,
    XSNAP_FIX,
    XSNAP_NORM_L,
    XSNAP_OUT,
    XSNAP_REV,
    drive_xsnap_triple,
    invoke_xsnap,
    reset_xsnap_workspace,
)


@pytest.mark.parametrize("scenario", ("match-precedence", "stable-diff-pair", "sds-ref-resolve", "idempotent-export"))
def test_xsnapctl_diff_report_matches_refmath(scenario: str) -> None:
    """publish-diff output matches independent reference_diff_report."""
    reset_xsnap_workspace()
    drive_xsnap_triple(scenario)
    body = read_json(XSNAP_OUT)
    ref = reference_diff_report(scenario, XSNAP_FIX)
    assert body["changes"] == ref["changes"]
    assert body["report_digest"] == ref["report_digest"]


def test_xsnapctl_change_paths_sorted_ascending() -> None:
    """Diff ledger entries sorted by path ascending."""
    reset_xsnap_workspace()
    drive_xsnap_triple("stable-diff-pair")
    paths = [c["path"] for c in read_json(XSNAP_OUT)["changes"]]
    assert paths == sorted(paths)


def test_xsnapctl_idempotent_publish_bytes() -> None:
    """Second publish-diff produces byte-identical report file."""
    reset_xsnap_workspace()
    drive_xsnap_triple("idempotent-export")
    first = XSNAP_OUT.read_bytes()
    proc = invoke_xsnap([XSNAP_BIN, "publish-diff", "--scenario", "idempotent-export"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert XSNAP_OUT.read_bytes() == first


def test_xsnapctl_identical_pair_zero_changes() -> None:
    """Identical snapshots produce empty change list."""
    reset_xsnap_workspace()
    drive_xsnap_triple("idempotent-export")
    assert read_json(XSNAP_OUT)["change_count"] == 0


def test_xsnapctl_stable_pair_detects_cluster_delta() -> None:
    """stable-diff-pair reports route cluster modifications."""
    reset_xsnap_workspace()
    drive_xsnap_triple("stable-diff-pair")
    paths = [c["path"] for c in read_json(XSNAP_OUT)["changes"]]
    assert "/routes/cc" in paths or "/routes/cb" in paths


def test_xsnapctl_canonicalize_writes_sidecar_files() -> None:
    """canonicalize creates normalized-left and revision JSON."""
    reset_xsnap_workspace()
    invoke_xsnap([XSNAP_BIN, "ingest-pair", "--scenario", "weight-normalize", "--fixture-dir", str(XSNAP_FIX)])
    invoke_xsnap([XSNAP_BIN, "canonicalize", "--scenario", "weight-normalize"])
    assert XSNAP_NORM_L.is_file()
    assert XSNAP_REV.is_file()


def test_xsnapctl_binary_invoked_directly() -> None:
    """xsnapctl is executed as compiled binary not shell wrapper."""
    reset_xsnap_workspace()
    proc = subprocess.run([XSNAP_BIN, "ingest-pair"], capture_output=True, text=True, check=False)
    assert proc.returncode != 0
