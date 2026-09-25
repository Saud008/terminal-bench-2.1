"""Workspace shell helpers for mqttsessctl offline session curator."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

BIN = "/app/bin/mqttsessctl"
APP_ROOT = Path("/app")
RESET_SCRIPT = Path("/app/scripts/reset-state.sh")
BROKER_SLUG = "edge-broker"

PATHS = {
    "staging": Path("/app/state/mqtt-journal-staging.json"),
    "seal": Path("/app/state/session-curator-seal.json"),
    "audit": Path("/app/work/mqtt-merge-audit.json"),
    "atlas": Path("/app/output/subscription-atlas.jsonl"),
    "ledger": Path("/app/output/delivery-ledger.jsonl"),
}

BUNDLED_FIXTURES = APP_ROOT / "fixtures"
OFF_CATALOG_FIXTURES = Path("/opt/verifier-fixtures/mqttsessctl")

def exec_mqtt(argv: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        argv,
        cwd=str(APP_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def wipe_workspace() -> None:
    proc = exec_mqtt(["bash", str(RESET_SCRIPT)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def ingest_only(scenario: str, fixture_root: Path | None = None, extra_env: dict | None = None) -> None:
    root = fixture_root or BUNDLED_FIXTURES
    env: dict[str, str] = {}
    if fixture_root is not None:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    proc = exec_mqtt(
        [
            BIN,
            "ingest-journal",
            "--broker",
            BROKER_SLUG,
            "--scenario",
            scenario,
            "--fixture-dir",
            str(root),
        ],
        env=env or None,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def drive_full_curator_run(
    scenario: str,
    fixture_root: Path | None = None,
    extra_env: dict | None = None,
) -> None:
    root = fixture_root or BUNDLED_FIXTURES
    ingest_only(scenario, root, extra_env)
    proc = exec_mqtt(
        [BIN, "merge-session", "--broker", BROKER_SLUG, "--scenario", scenario],
        env=extra_env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    proc = exec_mqtt(
        [BIN, "emit-atlas", "--broker", BROKER_SLUG, "--scenario", scenario],
        env=extra_env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows
