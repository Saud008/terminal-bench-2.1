from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
CLI = APP / "bin" / "rsyncprev"
COMPILED = APP / "state" / "filter-compiled.json"


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


def run_pipeline(tree: str, run_id: str, *, tree_root: Path | None = None) -> Path:
    env: dict[str, str] = {}
    if tree_root is not None:
        env["TB3_TREE_ROOT"] = str(tree_root)
    proc = invoke([str(CLI), "ingest", "--tree", tree, "--run-id", run_id], env=env or None)
    assert proc.returncode == 0, proc.stderr
    proc = invoke([str(CLI), "compile", "--run-id", run_id], env=env or None)
    assert proc.returncode == 0, proc.stderr
    out = APP / "output" / f"{run_id}-atlas.json"
    proc = invoke([str(CLI), "export", "--run-id", run_id, "--output", str(out)], env=env or None)
    assert proc.returncode == 0, proc.stderr
    return out
