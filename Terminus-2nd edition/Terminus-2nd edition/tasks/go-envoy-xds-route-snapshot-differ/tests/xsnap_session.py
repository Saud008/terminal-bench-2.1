"""Subprocess session helpers for xsnapctl verifier runs."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

XSNAP_BIN = "/app/bin/xsnapctl"
XSNAP_APP = Path("/app")
XSNAP_STAGE = Path("/app/state/xds-staging.json")
XSNAP_NORM_L = Path("/app/state/normalized-left.json")
XSNAP_NORM_R = Path("/app/state/normalized-right.json")
XSNAP_REV = Path("/app/state/normalize-revision.json")
XSNAP_OUT = Path("/app/output/xds-diff-report.json")
XSNAP_FIX = XSNAP_APP / "fixtures"
XSNAP_TB3 = Path("/opt/verifier-fixtures/xsnapctl")


def invoke_xsnap(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd, cwd=str(XSNAP_APP), capture_output=True, text=True, check=False, env=merged
    )


def reset_xsnap_workspace() -> None:
    proc = invoke_xsnap(["bash", "/app/scripts/reset-state.sh"])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def drive_xsnap_triple(scenario: str, root: Path | None = None, env: dict | None = None) -> None:
    fix = root or XSNAP_FIX
    e: dict[str, str] = {}
    if root:
        e["TB3_FIXTURE_DIR"] = str(fix)
    if env:
        e.update(env)
    for step in (
        [XSNAP_BIN, "ingest-pair", "--scenario", scenario, "--fixture-dir", str(fix)],
        [XSNAP_BIN, "canonicalize", "--scenario", scenario],
        [XSNAP_BIN, "publish-diff", "--scenario", scenario],
    ):
        proc = invoke_xsnap(step, env=e or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout
