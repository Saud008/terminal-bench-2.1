"""Workspace shell helpers for kcompactctl offline segment curator."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

BIN = "/app/bin/kcompactctl"
APP_ROOT = Path("/app")
RESET_SCRIPT = Path("/app/scripts/reset-state.sh")
TOPIC_SLUG = "inventory-keys"

PATHS = {
    "staging": Path("/app/state/frozen-segment-snapshot.json"),
    "seal": Path("/app/state/compact-curator-seal.json"),
    "audit": Path("/app/work/segment-audit-report.json"),
    "snapshot": Path("/app/output/topic-key-snapshot.jsonl"),
    "lineage": Path("/app/output/tombstone-lineage.jsonl"),
}

BUNDLED_FIXTURES = APP_ROOT / "fixtures"
OFF_CATALOG_FIXTURES = Path("/opt/verifier-fixtures/kcompactctl")

INGEST_SCENARIOS = (
    "clean-compact",
    "part-order",
    "tomb-retain",
    "dup-offset",
    "key-nfc",
    "seg-order",
    "idempotent-export",
)


def exec_kcompact(argv: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
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
    proc = exec_kcompact(["bash", str(RESET_SCRIPT)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def ingest_only(scenario: str, fixture_root: Path | None = None, extra_env: dict | None = None) -> None:
    root = fixture_root or BUNDLED_FIXTURES
    env: dict[str, str] = {}
    if fixture_root is not None:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    proc = exec_kcompact(
        [
            BIN,
            "pull-segments",
            "--topic",
            TOPIC_SLUG,
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
    env: dict[str, str] = {}
    if fixture_root is not None:
        env["TB3_FIXTURE_DIR"] = str(root)
    if extra_env:
        env.update(extra_env)
    for argv in (
        [
            BIN,
            "pull-segments",
            "--topic",
            TOPIC_SLUG,
            "--scenario",
            scenario,
            "--fixture-dir",
            str(root),
        ],
        [BIN, "audit-log", "--topic", TOPIC_SLUG, "--scenario", scenario],
        [BIN, "publish-keys", "--topic", TOPIC_SLUG, "--scenario", scenario],
    ):
        proc = exec_kcompact(argv, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout


def parse_jsonl_file(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
