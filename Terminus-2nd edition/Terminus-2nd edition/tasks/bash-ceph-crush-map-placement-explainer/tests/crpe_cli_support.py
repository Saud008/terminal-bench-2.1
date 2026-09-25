from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
CLI = APP / "bin" / "crpe"
NORMALIZED = APP / "state" / "crpe-normalized.json"
MAPS = APP / "maps"


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
    map_name: str,
    run_id: str,
    pg_start: int = 0,
    pg_end: int = 3,
    *,
    map_root: Path | None = None,
) -> Path:
    env: dict[str, str] = {}
    if map_root is not None:
        env["TB3_MAP_ROOT"] = str(map_root)
    proc = invoke([str(CLI), "ingest", "--map", map_name, "--run-id", run_id], env=env or None)
    assert proc.returncode == 0, proc.stderr
    proc = invoke([str(CLI), "normalize", "--run-id", run_id], env=env or None)
    assert proc.returncode == 0, proc.stderr
    out = APP / "output" / f"{run_id}-ledger.json"
    proc = invoke(
        [
            str(CLI),
            "export-ledger",
            "--run-id",
            run_id,
            "--pg-start",
            str(pg_start),
            "--pg-end",
            str(pg_end),
            "--output",
            str(out),
        ],
        env=env or None,
    )
    assert proc.returncode == 0, proc.stderr
    return out
