from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from reference_walplan import expected_plan, expected_stage, load_catalog

BIN = Path("/app/bin/walplan")
ARCHIVES = Path("/app/fixtures/archives")
STATE = Path("/app/state")
OUTPUT = Path("/app/output")
STAGING = STATE / "wal-archive.stage"
BROKEN = Path("/opt/verifier-broken-walplan")
GOLDEN = Path("/tests/golden_lib")
LIB = Path("/app/lib")
MODULES = (
    "wal_name",
    "timeline",
    "continuity",
    "partial",
    "label",
    "target",
    "digest",
    "staging",
    "plan",
)
CAT = load_catalog(ARCHIVES / "catalog.json")
TARGET_OK = "2024-06-15 14:34:00 UTC"
TARGET_LATE = "2024-06-15 14:35:00 UTC"


def _tool_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    merged = os.environ.copy()
    merged["PATH"] = "/app/bin:/opt/verifier-venv/bin:/usr/local/bin:" + merged.get("PATH", "")
    merged["APP_ROOT"] = "/app"
    if extra:
        merged.update(extra)
    return merged


def run(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, cwd="/app", capture_output=True, text=True, check=False, env=_tool_env(env)
    )


def reset() -> None:
    if STATE.exists():
        shutil.rmtree(STATE)
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    STATE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)


def ingest(archive: Path, staging: Path = STAGING) -> subprocess.CompletedProcess[str]:
    return run([str(BIN), "ingest", "--archive", str(archive), "--staging", str(staging)])


def plan(
    out: Path,
    restore_target: str = TARGET_OK,
    staging: Path = STAGING,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            str(BIN),
            "plan",
            "--staging",
            str(staging),
            "--out",
            str(out),
            "--restore-target",
            restore_target,
        ],
        env=env,
    )


def ingest_plan(archive: Path, out: Path, restore_target: str = TARGET_OK) -> subprocess.CompletedProcess[str]:
    proc = ingest(archive)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return plan(out, restore_target)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def install_modules(only_broken: set[str]) -> None:
    for mod in MODULES:
        src = BROKEN / f"{mod}.sh" if mod in only_broken else GOLDEN / f"{mod}.sh"
        shutil.copy2(src, LIB / f"{mod}.sh")
    os.chmod(LIB / "wal_name.sh", 0o755)


def restore_broken() -> None:
    for mod in MODULES:
        shutil.copy2(BROKEN / f"{mod}.sh", LIB / f"{mod}.sh")


@contextmanager
def partial_module_trap(only_broken: set[str]) -> Iterator[None]:
    install_modules(only_broken)
    try:
        yield
    finally:
        restore_broken()


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset()


def test_catalog_exists() -> None:
    """Catalog lists bundled archive fixtures."""
    assert len(CAT["archives"]) >= 5


def test_walplan_binary_exists() -> None:
    """walplan CLI is installed."""
    assert BIN.is_file()


@pytest.mark.parametrize("stem", ["alpha", "shuffle-label"])
def test_ingest_writes_expected_staging(stem: str) -> None:
    """ingest staging snapshot matches independent reference."""
    archive = ARCHIVES / stem
    proc = ingest(archive)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert load_json(STAGING) == expected_stage(archive)


def test_ingest_does_not_write_plan() -> None:
    """ingest alone must not emit planner JSON."""
    proc = ingest(ARCHIVES / "alpha")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert STAGING.is_file()
    assert not (OUTPUT / "alpha-plan.json").exists()


def test_default_staging_and_plan_paths() -> None:
    """cli.md default paths wal-archive.stage and plan.json."""
    staging = Path("/app/state/wal-archive.stage")
    out = Path("/app/output/plan.json")
    proc = run(
        [
            str(BIN),
            "ingest",
            "--archive",
            str(ARCHIVES / "alpha"),
            "--staging",
            str(staging),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert staging.is_file()
    proc = run(
        [
            str(BIN),
            "plan",
            "--staging",
            str(staging),
            "--out",
            str(out),
            "--restore-target",
            TARGET_OK,
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert out.is_file()
    assert load_json(out)["restore_ready"] is True


def test_export_alias_matches_plan() -> None:
    """export subcommand emits same planner JSON as plan."""
    ingest(ARCHIVES / "alpha")
    out_plan = OUTPUT / "export-plan.json"
    out_export = OUTPUT / "export-via-export.json"
    assert plan(out_plan).returncode == 0
    proc = run(
        [
            str(BIN),
            "export",
            "--staging",
            str(STAGING),
            "--out",
            str(out_export),
            "--restore-target",
            TARGET_OK,
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert load_json(out_export) == load_json(out_plan)


def test_alpha_plan_matches_reference() -> None:
    """alpha archive plan matches reference at restore target."""
    out = OUTPUT / "alpha-plan.json"
    proc = ingest_plan(ARCHIVES / "alpha", out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert load_json(out) == expected_plan(ARCHIVES / "alpha", TARGET_OK)


def test_alpha_restore_ready_exit_zero() -> None:
    """restore_ready alpha exits 0."""
    out = OUTPUT / "alpha-ready.json"
    proc = ingest_plan(ARCHIVES / "alpha", out)
    assert proc.returncode == 0
    assert load_json(out)["restore_ready"] is True


def test_gap_detects_continuity_failure() -> None:
    """gap archive reports continuity_ok false."""
    out = OUTPUT / "gap-plan.json"
    proc = ingest_plan(ARCHIVES / "gap", out)
    assert proc.returncode == 2
    body = load_json(out)
    assert body["continuity_ok"] is False
    assert len(body["gaps"]) >= 1


def test_scan_exits_two_on_gap() -> None:
    """scan subcommand exits 2 on gap archive."""
    proc = run([str(BIN), "scan", "--archive", str(ARCHIVES / "gap")])
    assert proc.returncode == 2


def test_scan_exits_zero_on_alpha() -> None:
    """scan subcommand exits 0 on continuous archive."""
    proc = run([str(BIN), "scan", "--archive", str(ARCHIVES / "alpha")])
    assert proc.returncode == 0


def test_partial_block_rejects_restore() -> None:
    """partial segment blocks restore_ready at late target."""
    out = OUTPUT / "partial-plan.json"
    proc = ingest_plan(ARCHIVES / "partial-block", out, TARGET_LATE)
    assert proc.returncode == 2
    body = load_json(out)
    assert body["restore_ready"] is False
    assert body["partial_rejected"]


def test_timeline_switch_staging_lists_history() -> None:
    """timeline-switch ingest records timeline history parents."""
    proc = ingest(ARCHIVES / "timeline-switch")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    stage = load_json(STAGING)
    assert any(row["timeline"] == 2 for row in stage["timelines"])


def test_shuffle_label_parses_utc_start_time() -> None:
    """shuffle-label backup_label whitespace still parses UTC start time."""
    proc = ingest(ARCHIVES / "shuffle-label")
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert load_json(STAGING)["start_time"] == "2024-06-15 14:30:00 UTC"


def test_plan_reads_staging_not_rescan() -> None:
    """plan uses mutated staging segments_present without rescanning archive."""
    archive = ARCHIVES / "alpha"
    ingest(archive)
    stage = load_json(STAGING)
    stage["segments_present"] = stage["segments_present"][:2]
    stage["digest"] = "deadbeefdeadbeef"
    STAGING.write_text(json.dumps(stage, indent=2), encoding="utf-8")
    out = OUTPUT / "alpha-staging-only.json"
    proc = plan(out)
    body = load_json(out)
    assert proc.returncode in (0, 2)
    assert body["digest"] == "deadbeefdeadbeef"
    assert body["selected_segment"] == stage["segments_present"][-1]


def test_tb3_hidden_archive_with_clock_root() -> None:
    """TB3 archive under /opt uses TB3_CLOCK_ROOT segment clock."""
    tb3 = Path("/opt/verifier-fixtures/wal-archives/tb3-random-timeline")
    assert tb3.is_dir()
    env = {"TB3_CLOCK_ROOT": "/opt/verifier-fixtures/wal-config"}
    proc = ingest(tb3, STAGING)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    out = OUTPUT / "tb3-plan.json"
    proc = plan(out, "2024-01-01 00:02:30 UTC", env=env)
    ref = expected_plan(
        tb3,
        "2024-01-01 00:02:30 UTC",
        config_root=Path("/opt/verifier-fixtures/wal-config"),
    )
    assert load_json(out) == ref


def test_tb3_scan_hidden_gap_free() -> None:
    """TB3 hidden archive passes scan continuity."""
    tb3 = Path("/opt/verifier-fixtures/wal-archives/tb3-random-timeline")
    proc = run([str(BIN), "scan", "--archive", str(tb3)])
    assert proc.returncode == 0


def test_alpha_selected_segment_for_target() -> None:
    """selected segment matches reference segment four at 14:34 target."""
    out = OUTPUT / "alpha-seg.json"
    ingest_plan(ARCHIVES / "alpha", out)
    body = load_json(out)
    ref = expected_plan(ARCHIVES / "alpha", TARGET_OK)
    assert body["selected_segment"] == ref["selected_segment"]


def test_gap_plan_matches_reference() -> None:
    """gap planner JSON matches reference builder."""
    out = OUTPUT / "gap-ref.json"
    ingest(ARCHIVES / "gap")
    plan(out, TARGET_OK)
    assert load_json(out) == expected_plan(ARCHIVES / "gap", TARGET_OK)


def test_staging_partial_files_listed() -> None:
    """partial-block staging lists partial_files separately."""
    ingest(ARCHIVES / "partial-block")
    stage = load_json(STAGING)
    assert any(name.endswith(".partial") for name in stage["partial_files"])
    assert all(not name.endswith(".partial") for name in stage["segments_present"])


def test_partial_broken_wal_name_differs() -> None:
    """partial trap installs broken wal_name module."""
    with partial_module_trap({"wal_name"}):
        assert (LIB / "wal_name.sh").read_text(encoding="utf-8") != (
            GOLDEN / "wal_name.sh"
        ).read_text(encoding="utf-8")


def test_partial_broken_continuity_differs() -> None:
    """partial trap installs broken continuity module."""
    with partial_module_trap({"continuity"}):
        assert (LIB / "continuity.sh").read_text(encoding="utf-8") != (
            GOLDEN / "continuity.sh"
        ).read_text(encoding="utf-8")


def test_partial_broken_plan_differs() -> None:
    """partial trap installs broken plan module."""
    with partial_module_trap({"plan"}):
        assert (LIB / "plan.sh").read_text(encoding="utf-8") != (
            GOLDEN / "plan.sh"
        ).read_text(encoding="utf-8")
