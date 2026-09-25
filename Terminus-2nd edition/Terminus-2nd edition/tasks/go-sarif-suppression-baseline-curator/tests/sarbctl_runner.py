"""Subprocess driver and path constants for sarbctl verification."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
CLI = Path("/usr/local") / "bin" / "sarbctl"
RESET = APP / "scripts" / "reset-state.sh"
STAGING = APP / "state" / "finding-staging.json"
STAGING_SEQ = APP / "state" / "staging-seq.json"
BASELINE_REV = APP / "state" / "reconcile-revision.json"
DELTA_OUT = APP / "output" / "finding-delta.json"
REJECTED = APP / "output" / "rejected-findings.jsonl"
SARIF = APP / "fixtures" / "scans" / "alpha.sarif.json"
BASELINE = APP / "fixtures" / "snapshots" / "alpha-snapshot.json"
POLICY = APP / "fixtures" / "policies" / "alpha-policy.json"
REMAP = APP / "fixtures" / "remap" / "ci-paths.json"
HIDDEN = Path("/opt") / "verifier-fixtures" / "sarif-gamma"
PATCHES = Path(__file__).resolve().parent / "patches"

PATCH_TARGETS = {
    "stage": APP / "internal" / "scanstage" / "stage.go",
    "canonical": APP / "internal" / "rules" / "canonical.go",
    "remap": APP / "internal" / "remap" / "path.go",
    "fingerprint": APP / "internal" / "fingerprint" / "drift.go",
    "suppress": APP / "internal" / "suppress" / "expiry.go",
    "dedupe": APP / "internal" / "dedupe" / "collapse.go",
    "curate": APP / "internal" / "curate" / "run.go",
    "emit": APP / "internal" / "emitdelta" / "delta.go",
}


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged["PATH"] = os.pathsep.join(
        [
            str(Path("/usr/local") / "go" / "bin"),
            str(Path("/opt") / "verifier-venv" / "bin"),
            str(Path("/usr/local") / "bin"),
            merged.get("PATH", ""),
        ]
    )
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def wipe_state() -> None:
    proc = invoke(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def sarbctl_scan(
    sarif: Path,
    policy: Path,
    remap: Path,
    baseline: Path,
    env: dict | None = None,
) -> None:
    proc = invoke(
        [
            str(CLI),
            "scan",
            "--sarif",
            str(sarif),
            "--policy",
            str(policy),
            "--remap",
            str(remap),
            "--baseline",
            str(baseline),
        ],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def sarbctl_curate() -> None:
    proc = invoke([str(CLI), "curate"])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def sarbctl_emit() -> None:
    proc = invoke([str(CLI), "emit"])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def sarbctl_full_run(
    sarif: Path,
    policy: Path,
    remap: Path,
    baseline: Path,
    env: dict | None = None,
) -> None:
    sarbctl_scan(sarif, policy, remap, baseline, env)
    sarbctl_curate()
    sarbctl_emit()
