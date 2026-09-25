"""Subprocess driver and workspace paths for flink-skew verifier."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
JAR = APP / "bin" / "flink-skew.jar"
JAVA = "java"
REBUILD = APP / "scripts" / "rebuild-flink-skew.sh"
RESET = APP / "scripts" / "reset-state.sh"

PATHS = {
    "index": APP / "state" / "event_index.json",
    "buffer": APP / "state" / "alignment.buffer",
    "chronicle": APP / "output" / "barrier_skew_chronicle.json",
    "events": APP / "fixtures" / "jm-events",
    "config": APP / "fixtures" / "config",
}

HIDDEN_ROOT = Path("/opt/verifier-fixtures/flink_skew_hidden")


def fixture_events_dir() -> Path:
    root = os.environ.get("TB3_FIXTURE_ROOT")
    if root:
        return Path(root) / "jm-events"
    return PATHS["events"]


def exec_skew(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([JAVA, "-jar", str(JAR), *argv], capture_output=True, text=True)


def rebuild_jar() -> None:
    subprocess.run(["bash", str(REBUILD)], check=True, capture_output=True, text=True)


def wipe_workspace() -> None:
    subprocess.run(["bash", str(RESET)], check=True, capture_output=True, text=True)


def run_full_pipeline() -> None:
    wipe_workspace()
    events = fixture_events_dir()
    proc = exec_skew(["load-events", "--input", str(events), "--out", str(PATHS["index"])])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    proc = exec_skew(["align-barriers", "--index", str(PATHS["index"]), "--out", str(PATHS["buffer"])])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    proc = exec_skew(["emit-chronicle", "--buffer", str(PATHS["buffer"]), "--out", str(PATHS["chronicle"])])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
