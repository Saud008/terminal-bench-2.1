"""Subprocess session helpers for vecchat vcreplay verifier."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

VCREPLAY_BIN = "/app/bin/vcreplay"
VCREPLAY_APP = Path("/app")
VCREPLAY_RESET = Path("/app/scripts/reset-state.sh")
VCREPLAY_STAGE = Path("/app/state/chat-staging.json")
VCREPLAY_GEN = Path("/app/state/reconcile-revision.json")
VCREPLAY_FINDINGS = Path("/app/work/reconcile-findings.json")
VCREPLAY_TIMELINE = Path("/app/output/audit-timeline.jsonl")
VCREPLAY_EARLY = Path("/app/output/early-timeline.jsonl")
VCREPLAY_BUNDLE = VCREPLAY_APP / "fixtures"
VCREPLAY_HIDDEN = Path("/opt/verifier-fixtures/vcreplay")
VCREPLAY_ROOM = "lobby"

BUNDLED_SCENARIOS = (
    "clean-room",
    "mod-precedence",
    "mute-window",
    "dup-delivery",
    "clock-gap",
    "shard-order",
)


def vcreplay_cli(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=str(VCREPLAY_APP),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def vcreplay_reset_workspace() -> None:
    proc = vcreplay_cli(["bash", str(VCREPLAY_RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def vcreplay_run_pipeline(
    scenario: str,
    fixture_root: Path | None = None,
    output: Path | None = None,
    extra_env: dict | None = None,
) -> Path:
    root = fixture_root or VCREPLAY_BUNDLE
    env = {"TB3_FIXTURE_DIR": str(root)} if fixture_root else {}
    if extra_env:
        env.update(extra_env)
    for step in (
        [
            VCREPLAY_BIN,
            "load",
            "--room",
            VCREPLAY_ROOM,
            "--scenario",
            scenario,
            "--fixture-dir",
            str(root),
        ],
        [VCREPLAY_BIN, "reconcile", "--room", VCREPLAY_ROOM, "--scenario", scenario],
    ):
        proc = vcreplay_cli(step, env=env or None)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = output or VCREPLAY_TIMELINE
    proc = vcreplay_cli(
        [
            VCREPLAY_BIN,
            "emit-timeline",
            "--room",
            VCREPLAY_ROOM,
            "--scenario",
            scenario,
            "--output",
            str(out),
        ],
        env=env or None,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out


def read_timeline(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
