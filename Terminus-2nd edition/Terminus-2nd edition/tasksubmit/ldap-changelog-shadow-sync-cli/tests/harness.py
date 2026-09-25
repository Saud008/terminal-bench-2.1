"""Shared helpers for shadow-sync verifier tests."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

BIN = Path("/app/bin/shadow-sync")
STATE = Path("/app/state")
OUTPUT = Path("/app/output")
FIXTURES = Path("/app/fixtures")
STAGING = STATE / "changelog-staging.jsonl"
DB = STATE / "shadow.db"
INGEST_STATS = STATE / "last-ingest-stats.json"
SHADOW_JSON = OUTPUT / "shadow.json"
AUDIT_JSON = OUTPUT / "shadow-audit.json"


def reset_state() -> None:
    for p in (STATE, OUTPUT):
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)


def ingest_ldif(path: Path, db: Path = DB) -> None:
    subprocess.run(
        [str(BIN), "ingest-ldif", "--input", str(path), "--db", str(db)],
        check=True,
        capture_output=True,
        text=True,
    )


def export_shadow(db: Path = DB) -> tuple[Path, Path]:
    subprocess.run(
        [
            str(BIN),
            "export",
            "--db",
            str(db),
            "--shadow",
            str(SHADOW_JSON),
            "--audit",
            str(AUDIT_JSON),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return SHADOW_JSON, AUDIT_JSON


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_staging() -> list[dict]:
    if not STAGING.exists():
        return []
    rows = []
    for line in STAGING.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
