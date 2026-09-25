"""CLI helpers for minclus tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP_ROOT = Path("/app")
CLI_BIN = APP_ROOT / "bin" / "minclus"
RESET_SH = APP_ROOT / "scripts" / "reset-workspace.sh"
CORPUS_DIR = APP_ROOT / "fixtures" / "corpora"
PROFILES = json.loads((APP_ROOT / "fixtures" / "run_profiles.json").read_text(encoding="utf-8"))


def resolve_corpus(name: str, env: dict | None = None) -> Path:
    if env and env.get("TB3_CORPUS_DIR"):
        return Path(env["TB3_CORPUS_DIR"]) / name
    return CORPUS_DIR / name


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP_ROOT), capture_output=True, text=True, check=False, env=merged)


def wipe() -> None:
    proc = invoke(["bash", str(RESET_SH)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_pipeline(
    run_id: str,
    corpus_name: str,
    *,
    floor: float | None = None,
    profile: str = "default",
    env: dict | None = None,
) -> Path:
    merged = dict(env or {})
    corpus_path = resolve_corpus(corpus_name, merged)
    if floor is None:
        floor = next(p["jaccard_floor"] for p in PROFILES["profiles"] if p["name"] == profile)
    for step in (
        [
            str(CLI_BIN),
            "scan",
            "--corpus-dir",
            str(corpus_path),
            "--run-id",
            run_id,
            "--profile",
            profile,
        ],
        [str(CLI_BIN), "group", "--run-id", run_id, "--jaccard-floor", str(floor)],
    ):
        proc = invoke(step, env=merged)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP_ROOT / "output" / f"{run_id}-provenance.json"
    proc = invoke(
        [str(CLI_BIN), "attest", "--run-id", run_id, "--output", str(out)],
        env=merged,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out
