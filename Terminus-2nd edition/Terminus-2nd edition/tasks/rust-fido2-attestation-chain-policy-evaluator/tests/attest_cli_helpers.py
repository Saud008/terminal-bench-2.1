"""CLI helpers for fido2eval tests."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
CLI = APP / "bin" / "fido2eval"
RESET = APP / "scripts" / "reset-state.sh"


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def wipe() -> None:
    proc = invoke(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_pipeline(batch: str, bundle: str, policy: str, *, env: dict | None = None) -> Path:
    merged = dict(env or {})
    if "TB3_REGISTRY_ROOT" in merged and "TB3_METADATA_PATH" not in merged:
        merged["TB3_METADATA_PATH"] = str(Path(merged["TB3_REGISTRY_ROOT"]) / "authenticators" / "aaguid-registry.json")
    out = APP / "output" / f"{batch}-trust.json"
    proc = invoke(
        [
            str(CLI),
            "run-batch",
            "--batch",
            batch,
            "--bundle",
            bundle,
            "--policy",
            policy,
            "--output",
            str(out),
        ],
        env=merged,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out
