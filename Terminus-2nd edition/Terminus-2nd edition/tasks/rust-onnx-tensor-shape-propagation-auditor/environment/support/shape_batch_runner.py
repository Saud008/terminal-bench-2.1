"""Subprocess driver for shapeprop batch-propagate and emit-violations."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path("/app")
ENV_ROOT = ROOT / "environment"
SHAPEPROP_BIN = ENV_ROOT / "tools" / "shapeprop" / "shapeprop"
BUILD_SCRIPT = ENV_ROOT / "scripts" / "build_all.sh"
LEDGER_PATH = ROOT / "state" / "tensor_prop_batch.jsonl"
REPORT_PATH = ROOT / "output" / "constraint_diagnostic_report.json"
DEFAULT_BATCH = ENV_ROOT / "fixtures" / "graphs"


def resolve_graph_batch() -> Path:
    override = os.environ.get("TB3_GRAPH_DIR")
    return Path(override) if override else DEFAULT_BATCH


def invoke(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def compile_shapeprop() -> None:
    invoke(["bash", str(BUILD_SCRIPT)])


def clear_artifacts() -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    for path in (LEDGER_PATH, REPORT_PATH):
        if path.exists():
            path.unlink()


def run_batch_and_emit(batch: Path | None = None) -> None:
    batch = batch or resolve_graph_batch()
    clear_artifacts()
    invoke(
        [
            str(SHAPEPROP_BIN),
            "batch-propagate",
            "--graph-batch",
            str(batch),
            "--ledger",
            str(LEDGER_PATH),
        ]
    )
    invoke(
        [
            str(SHAPEPROP_BIN),
            "emit-violations",
            "--ledger",
            str(LEDGER_PATH),
            "--graph-batch",
            str(batch),
            "--report",
            str(REPORT_PATH),
        ]
    )


def read_ledger_rows() -> list[dict]:
    return [json.loads(line) for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def cli_help_tokens() -> tuple[str, ...]:
    """Subcommand tokens that must appear in shapeprop --help output."""
    return ("batch-propagate", "emit-violations")


def read_diagnostic_report() -> list[dict]:
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


def run_shapeprop_help() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SHAPEPROP_BIN), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
