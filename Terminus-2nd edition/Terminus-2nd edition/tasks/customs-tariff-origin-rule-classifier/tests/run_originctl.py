from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ORIGIN_BIN = "/app/bin/originctl"
DB_PATH = Path("/app/var/ledger/tariff.db")
ATLAS_JSON = Path("/app/output/tariff-classifications.json")
WORKBENCH_LINES_JSON = Path("/app/var/workbench/normalized-lines.json")
FIXTURE_ROOT = Path("/app/fixtures")


def wipe_state() -> None:
    for p in (
        DB_PATH,
        WORKBENCH_LINES_JSON,
        ATLAS_JSON,
        Path("/app/output/origin-audit.jsonl"),
        Path("/app/var/workbench/origin-scores.json"),
        Path("/app/var/run/origin-pass.json"),
    ):
        if p.exists():
            p.unlink()
    Path("/app/var/run").mkdir(parents=True, exist_ok=True)
    Path("/app/var/run/origin-pass.json").write_text(
        '{"parse_pass":0,"atlas_pass":0}\n', encoding="utf-8"
    )


def invoke(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [ORIGIN_BIN, *args],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ},
    )


def run_pipeline(manifest: str, fixture_root: Path | None = None) -> None:
    root = str(fixture_root or FIXTURE_ROOT)
    proc = invoke("parse-shipment", "--manifest", manifest, "--fixture-dir", root)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    proc2 = invoke("score-origin", "--manifest", manifest)
    assert proc2.returncode == 0, proc2.stderr + proc2.stdout
    proc3 = invoke("write-atlas", "--manifest", manifest)
    assert proc3.returncode == 0, proc3.stderr + proc3.stdout


def read_classifications() -> dict:
    return json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
