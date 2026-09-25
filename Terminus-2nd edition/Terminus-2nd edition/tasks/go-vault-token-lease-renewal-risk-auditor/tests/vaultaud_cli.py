"""CLI subprocess driver for vaultaud audit and rollup."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

APP = Path("/app")
BIN = APP / "bin" / "vaultaud"
REBUILD = APP / "scripts" / "rebuild-vaultaud.sh"
RESET = APP / "scripts" / "reset-state.sh"
LEDGER = APP / "state" / "lease_audit_buffer.jsonl"
ATLAS = APP / "output" / "token_risk_rollup.json"
DEFAULT_TRANSCRIPTS = APP / "fixtures" / "renewal_logs"
CONFIG = APP / "fixtures" / "config"


def active_transcript_dir() -> Path:
    tb3 = os.environ.get("TB3_TRANSCRIPT_DIR")
    if tb3:
        return Path(tb3)
    return DEFAULT_TRANSCRIPTS


def invoke(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def compile_vaultaud() -> None:
    invoke(["bash", str(REBUILD)])


def clear_outputs() -> None:
    invoke(["bash", str(RESET)])


def run_audit_rollup(tdir: Path | None = None) -> None:
    tdir = tdir or active_transcript_dir()
    clear_outputs()
    invoke([
        str(BIN), "audit",
        "--transcript-dir", str(tdir),
        "--config-dir", str(CONFIG),
        "--staging", str(LEDGER),
    ])
    invoke([
        str(BIN), "rollup",
        "--staging", str(LEDGER),
        "--atlas", str(ATLAS),
    ])
