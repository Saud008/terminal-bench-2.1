from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
CLI = APP / "bin" / "kcfgattest"
STAGE = APP / "state" / "kcfg-stage.json"


def wipe() -> None:
    subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)


def invoke(args: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        args,
        cwd=str(APP),
        env=merged,
        text=True,
        capture_output=True,
        timeout=120,
    )


def compile_and_emit(
    bundle: str,
    run_id: str,
    *,
    bundle_root: Path | None = None,
) -> Path:
    env: dict[str, str] = {}
    if bundle_root is not None:
        env["TB3_BUNDLE_ROOT"] = str(bundle_root)
    proc = invoke(
        [str(CLI), "compile-stage", "--bundle", bundle, "--run-id", run_id],
        env=env or None,
    )
    assert proc.returncode == 0, proc.stderr
    out = APP / "output" / f"{run_id}-manifest.json"
    proc = invoke(
        [str(CLI), "emit-manifest", "--run-id", run_id, "--output", str(out)],
        env=env or None,
    )
    assert proc.returncode == 0, proc.stderr
    return out
