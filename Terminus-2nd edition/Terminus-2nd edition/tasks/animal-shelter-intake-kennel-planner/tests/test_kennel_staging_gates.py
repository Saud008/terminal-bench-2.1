"""Bind/weave staging gate tests — ingest-only bind, weave header snapshot, seal prerequisites."""

from __future__ import annotations

import json
from pathlib import Path

from kennel_session import (
    CLI_BIN,
    FIXTURE_ROOT,
    SCENARIO_CLEAN,
    SCENARIO_OVERFLOW,
    SCENARIO_QUAR,
    bind_state_path,
    invoke,
    run_pipeline,
    weave_pass_state_path,
    wipe_state,
)
from shelter_planner_sim import reference_bind


def test_kennel_ingest_bind_registry_digest_clean_intake() -> None:
    """Ingest bind stage attests registry.sqlite digest for clean-intake before weave staging."""
    wipe_state()
    proc = invoke(
        [
            str(CLI_BIN),
            "bind",
            "--registry",
            "sqlite",
            "--arrivals",
            "jsonl",
            "--run-id",
            SCENARIO_CLEAN,
            "--scenario",
            SCENARIO_CLEAN,
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    bind = json.loads(bind_state_path(SCENARIO_CLEAN).read_text(encoding="utf-8"))
    ref = reference_bind(FIXTURE_ROOT, SCENARIO_CLEAN)
    assert bind["registry_digest"] == ref["registry_digest"]


def test_kennel_ingest_bind_registry_digest_overflow_single() -> None:
    """Ingest bind stage copies arrivals jsonl and records kennel counts for overflow-single."""
    wipe_state()
    proc = invoke(
        [
            str(CLI_BIN),
            "bind",
            "--registry",
            "sqlite",
            "--arrivals",
            "jsonl",
            "--run-id",
            SCENARIO_OVERFLOW,
            "--scenario",
            SCENARIO_OVERFLOW,
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    bind = json.loads(bind_state_path(SCENARIO_OVERFLOW).read_text(encoding="utf-8"))
    assert bind["kennel_count"] >= 1


def test_kennel_staging_weave_header_snapshot_clean_intake() -> None:
    """Weave staging snapshot precedes seal export of placement atlas for clean-intake."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    header_path = Path("/app/work/quarantine-weave-clean-intake.header.json")
    assert header_path.is_file()
    header = json.loads(header_path.read_text(encoding="utf-8"))
    assert header["engine"] == "intakectl"
    assert isinstance(header.get("placements"), list)


def test_kennel_staging_weave_header_snapshot_quarantine_block() -> None:
    """Weave staging snapshot records scenario id and weave_pass for quarantine-block rollout."""
    wipe_state()
    run_pipeline(SCENARIO_QUAR)
    header_path = Path("/app/work/quarantine-weave-quarantine-block.header.json")
    header = json.loads(header_path.read_text(encoding="utf-8"))
    assert header["scenario"] == SCENARIO_QUAR
    assert header.get("weave_pass", 0) >= 1


def test_kennel_staging_weave_pass_increments_on_weave() -> None:
    """Operational weave_pass staging counter increments once per weave invocation."""
    wipe_state()
    invoke(
        [
            str(CLI_BIN),
            "bind",
            "--registry",
            "sqlite",
            "--arrivals",
            "jsonl",
            "--run-id",
            SCENARIO_CLEAN,
            "--scenario",
            SCENARIO_CLEAN,
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    proc = invoke([str(CLI_BIN), "weave", "--run-id", SCENARIO_CLEAN])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(weave_pass_state_path(SCENARIO_CLEAN).read_text(encoding="utf-8"))
    assert body.get("weave_pass", 0) == 1


def test_kennel_staging_jsonl_audit_snapshot_lines() -> None:
    """Weave staging jsonl audit snapshot contains placement or transfer kind rows."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    jsonl_path = Path("/app/work/quarantine-weave-clean-intake.jsonl")
    lines = jsonl_path.read_text(encoding="utf-8").splitlines()
    assert lines
    kinds = {json.loads(line)["kind"] for line in lines}
    assert kinds <= {"placement", "transfer"}


def test_kennel_ingest_bind_materializes_registry_sqlite_on_disk() -> None:
    """Ingest bind materializes /app/state/registry-<run>.sqlite before staging weave."""
    wipe_state()
    invoke(
        [
            str(CLI_BIN),
            "bind",
            "--registry",
            "sqlite",
            "--arrivals",
            "jsonl",
            "--run-id",
            SCENARIO_CLEAN,
            "--scenario",
            SCENARIO_CLEAN,
            "--fixture-dir",
            str(FIXTURE_ROOT),
        ]
    )
    reg = Path("/app/state/registry-clean-intake.sqlite")
    assert reg.is_file()
    assert reg.stat().st_size > 0


def test_kennel_staging_weave_blocked_without_ingest_bind() -> None:
    """Weave staging refuses to run when ingest bind artifact is missing."""
    wipe_state()
    proc = invoke([str(CLI_BIN), "weave", "--run-id", SCENARIO_CLEAN])
    assert proc.returncode != 0
