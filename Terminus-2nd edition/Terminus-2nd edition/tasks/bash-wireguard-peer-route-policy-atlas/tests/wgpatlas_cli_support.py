from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
CLI = APP / "bin" / "wgpatlas"
WORKSPACE = APP / "state" / "wgpatlas-workspace.json"
SITES = APP / "sites"


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


def run_pipeline(
    site: str,
    run_id: str,
    *,
    site_root: Path | None = None,
) -> Path:
    env: dict[str, str] = {}
    if site_root is not None:
        env["TB3_SITE_ROOT"] = str(site_root)
    proc = invoke([str(CLI), "ingest", "--site", site, "--run-id", run_id], env=env or None)
    assert proc.returncode == 0, proc.stderr
    proc = invoke([str(CLI), "analyze", "--run-id", run_id], env=env or None)
    assert proc.returncode == 0, proc.stderr
    out = APP / "output" / f"{run_id}-atlas.json"
    proc = invoke([str(CLI), "export", "--run-id", run_id, "--output", str(out)], env=env or None)
    assert proc.returncode == 0, proc.stderr
    return out
