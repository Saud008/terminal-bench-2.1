"""Hidden μ(E) traps under /opt/verifier-fixtures/xanes-delta."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from reference_xanes import reference_close

APP = Path("/app")
CLI = "/usr/local/bin/xanesctl"
OUTPUT = APP / "output"
HIDDEN_ROOT = "/opt/verifier-fixtures/xanes-delta"
HIDDEN_BIN3_TRACE = f"{HIDDEN_ROOT}/traces/hidden-bin3-trap.json"
HIDDEN_BIN3_WINDOWS = f"{HIDDEN_ROOT}/windows/hidden-bin3-trap.json"
HIDDEN_MEDGE_TRACE = f"{HIDDEN_ROOT}/traces/hidden-medge-trap.json"
HIDDEN_MEDGE_WINDOWS = f"{HIDDEN_ROOT}/windows/hidden-medge-trap.json"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def close_paths(trace: str, windows: str, export: Path, seed: str = "") -> subprocess.CompletedProcess[str]:
    cmd = [CLI, "close", "--trace", trace, "--windows", windows, "--export", str(export)]
    if seed:
        cmd.extend(["--seed", seed])
    return run(cmd)


def test_hidden_bin3_jitter_trap_under_verifier_fixtures() -> None:
    """Hidden bin-3 jitter pack under /opt/verifier-fixtures/xanes-delta must match oracle."""
    os.environ["XANES_FIXTURE_ROOT"] = HIDDEN_ROOT
    seed = "xanes-seed-11"
    export = OUTPUT / "hidden-bin3-trap.json"
    proc = close_paths(HIDDEN_BIN3_TRACE, HIDDEN_BIN3_WINDOWS, export, seed)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    body = json.loads(export.read_text(encoding="utf-8"))
    ref = reference_close(Path(HIDDEN_BIN3_TRACE), Path(HIDDEN_BIN3_WINDOWS), seed)
    assert body["closure_digest"] == ref["closure_digest"]


def test_hidden_medge_integral_trap_under_verifier_fixtures() -> None:
    """Hidden M-edge pack under /opt/verifier-fixtures/xanes-delta must match oracle integrals."""
    os.environ["XANES_FIXTURE_ROOT"] = HIDDEN_ROOT
    export = OUTPUT / "hidden-medge-trap.json"
    proc = close_paths(HIDDEN_MEDGE_TRACE, HIDDEN_MEDGE_WINDOWS, export)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    body = json.loads(export.read_text(encoding="utf-8"))
    ref = reference_close(Path(HIDDEN_MEDGE_TRACE), Path(HIDDEN_MEDGE_WINDOWS), "")
    assert body["closure_digest"] == ref["closure_digest"]
