"""CLI helpers for seismocomply tests."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP_ROOT = Path("/app")
CLI_BIN = APP_ROOT / "bin" / "seismocomply"
RESET_SH = APP_ROOT / "scripts" / "clear-seismo-run.sh"
BUFFER_PATH = APP_ROOT / "state" / "peak-correlation-buffer.json"
PASSPORT_PATH = APP_ROOT / "work" / "audit-passport.json"
CATALOG = json.loads((APP_ROOT / "fixtures" / "survey_catalog.json").read_text(encoding="utf-8"))
SURVEY_DIR = APP_ROOT / "fixtures" / "surveys"
SEED_POOL = json.loads((APP_ROOT / "fixtures" / "blast_seed_pool.json").read_text(encoding="utf-8"))["seeds"]
HIDDEN_SURVEYS = Path("/opt/verifier-fixtures/seismocomply/surveys")


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP_ROOT), capture_output=True, text=True, check=False, env=merged)


def wipe() -> None:
    proc = invoke(["bash", str(RESET_SH)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def run_pipeline(
    seed: str,
    survey: str,
    *,
    fixture_dir: Path | None = None,
    env: dict | None = None,
) -> Path:
    merged = dict(env or {})
    if fixture_dir is not None:
        merged["TB3_FIXTURE_DIR"] = str(fixture_dir)
    for step in (
        [str(CLI_BIN), "load-survey", "--seed", seed, "--survey", survey],
        [str(CLI_BIN), "correlate", "--seed", seed, "--survey", survey],
    ):
        proc = invoke(step, env=merged)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP_ROOT / "output" / f"{seed}-{survey}-atlas.json"
    proc = invoke(
        [
            str(CLI_BIN),
            "publish-atlas",
            "--seed",
            seed,
            "--survey",
            survey,
            "--output",
            str(out),
        ],
        env=merged,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out
