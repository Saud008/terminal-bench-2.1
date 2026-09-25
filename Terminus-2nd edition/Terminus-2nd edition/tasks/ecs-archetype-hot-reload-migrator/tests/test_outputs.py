"""Behavioral verifier for ecs-migrate hot-reload apply pipeline."""

from __future__ import annotations

import json
import sqlite3
import struct
import subprocess
import tempfile
from pathlib import Path

import pytest
from reference_apply import (
    CHUNK_MAGIC,
    chunk_checksum,
    component_stride,
    copy_fixture_tree,
    load_layout,
    read_chunk,
    reference_apply,
    replay_start_cursor,
)

APP = Path("/app")
CLI = Path("/usr/local/bin/ecs-migrate")
LAYOUT = APP / "fixtures/layouts/hot_reload_alpha.json"
DB = APP / "data/ecs_meta.db"
CHUNKS = APP / "data/chunks"
JOURNAL = APP / "data/replay.journal.json"
REPORT = APP / "output/migration-report.json"
CONTRACT_DB = "/app/data/ecs_meta.db"
CONTRACT_CHUNKS = "/app/data/chunks/"
CONTRACT_JOURNAL = "/app/data/replay.journal.json"
CONTRACT_REPORT = "/app/output/migration-report.json"
CONTRACT_REPORT_INSTRUCTION = "/app/output/migration-report.json."
STAGING = APP / "state/migration-staging.json"
RESET = APP / "scripts/reset-state.sh"
TB3 = Path("/opt/verifier-fixtures/ecs-migrate")
TB3_CATALOG = json.loads((TB3 / "catalog.json").read_text(encoding="utf-8"))


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=check)


def normalize_line_endings() -> None:
    paths: list[Path] = []
    test_root = Path("/tests")
    if test_root.is_dir():
        paths.extend(test_root.glob("*.py"))
        paths.extend(test_root.glob("*.sh"))
    if (APP / "scripts").is_dir():
        paths.extend((APP / "scripts").glob("*.sh"))
    for path in paths:
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if b"\r" not in raw:
            continue
        path.write_bytes(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n"))


def rebuild_cli() -> None:
    proc = run(["bash", "/app/scripts/verifier-rebuild.sh"], check=False)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def reset_state() -> None:
    proc = run(["bash", str(RESET)], check=False)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def apply(
    *,
    db: Path = DB,
    chunks: Path = CHUNKS,
    journal: Path = JOURNAL,
    report: Path = REPORT,
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            str(CLI),
            "apply",
            "--db",
            str(db),
            "--chunks",
            str(chunks),
            "--layout",
            str(LAYOUT),
            "--journal",
            str(journal),
            "--report",
            str(report),
        ],
        check=False,
    )


@pytest.fixture(scope="session", autouse=True)
def session_setup() -> None:
    normalize_line_endings()
    rebuild_cli()
    reset_state()
    proc = run(["cargo", "test", "--locked", "-p", "ecs-core", "api_contract"], check=False)
    assert proc.returncode == 0, proc.stderr or proc.stdout


@pytest.fixture(autouse=True)
def fresh_bundled_state() -> None:
    reset_state()
    yield


def test_staging_snapshot_not_used_by_apply_hot_path() -> None:
    """Staging snapshot at /app/state/migration-staging.json is off the ecs-migrate apply hot path."""
    if STAGING.exists():
        STAGING.unlink()
    proc = apply()
    assert proc.returncode == 0
    assert not STAGING.exists()


def test_ingest_layout_module_is_decoy_off_apply_path() -> None:
    """Layout ingest helpers under /app/ingest/ are decoy modules and not required for apply."""
    proc = apply()
    assert proc.returncode == 0
    assert (APP / "ingest/layout_ingest.rs").is_file()
    assert (APP / "crates/ecs-core/src/export_stage.rs").is_file()


def test_ecs_migrate_binary_exists() -> None:
    """Instruction requires a rebuilt ecs-migrate CLI on PATH for subprocess apply."""
    assert CLI.is_file()


def test_bundled_layout_manifest() -> None:
    """Instruction cites the bundled layout at /app/fixtures/layouts/hot_reload_alpha.json."""
    manifest = load_layout(LAYOUT)
    assert manifest["layout_id"] == "hot_reload_alpha"
    assert manifest["to_version"] == 2


def test_instruction_contract_paths_exist_after_apply() -> None:
    """Instruction names /app/data/ecs_meta.db, /app/data/chunks/, /app/data/replay.journal.json, and /app/output/migration-report.json."""
    proc = apply()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert str(DB) == CONTRACT_DB and DB.is_file()
    assert str(CHUNKS) + "/" == CONTRACT_CHUNKS and CHUNKS.is_dir()
    assert any(CHUNKS.glob("chunk_*.bin"))
    assert str(JOURNAL) == CONTRACT_JOURNAL and JOURNAL.is_file()
    assert str(REPORT) == CONTRACT_REPORT and REPORT.is_file()
    assert CONTRACT_REPORT_INSTRUCTION.startswith(CONTRACT_REPORT)


def test_apply_writes_migration_report() -> None:
    """Apply must write migration-report.json under /app/output/."""
    proc = apply()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert REPORT.is_file()


def test_report_matches_reference_apply() -> None:
    """Bundled apply output must match an independent Python reference_apply implementation."""
    proc = apply()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    actual = json.loads(REPORT.read_text(encoding="utf-8"))
    reset_state()
    ref = reference_apply(DB, CHUNKS, LAYOUT, JOURNAL)
    assert actual == ref


def test_journal_replayed_from_commit_cursor() -> None:
    """Replay journal commit_cursor drives journal_replayed_from when status is pending."""
    journal_before = json.loads(JOURNAL.read_text(encoding="utf-8"))
    proc = apply()
    assert proc.returncode == 0
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["journal_replayed_from"] == replay_start_cursor(journal_before)


def test_only_move_step_applied_this_run() -> None:
    """Journal replay must skip step one already committed and apply only step two move."""
    proc = apply()
    assert proc.returncode == 0
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert len(report["steps_applied"]) == 1
    step = report["steps_applied"][0]
    assert step["order"] == 2
    assert step["op"] == "move"


def test_entities_moved_nonzero() -> None:
    """Move step must relocate entities across chunks and increment entities_moved."""
    proc = apply()
    assert proc.returncode == 0
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["entities_moved"] >= 1


def test_placeholder_remapped_to_stable_id_six() -> None:
    """Entity-id remap must assign stable_id 6 to the bundled placeholder row."""
    proc = apply()
    assert proc.returncode == 0
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["ids_remapped"] == 1
    con = sqlite3.connect(DB)
    try:
        row = con.execute(
            "SELECT stable_id FROM entities WHERE alive = 1 AND stable_id = 6"
        ).fetchone()
        assert row is not None
        assert row[0] == 6
    finally:
        con.close()


def test_chunk_payload_stable_id_zero_bytes_unchanged() -> None:
    """Stable_id remap updates SQLite only and must not rewrite chunk payload bytes."""
    before = read_chunk(CHUNKS, 2)[1]
    placeholder_before = next(e for e in before if e["stable_id"] == 0)
    proc = apply()
    assert proc.returncode == 0
    after = read_chunk(CHUNKS, 2)[1]
    placeholder_after = next(e for e in after if e["stable_id"] == 0)
    assert placeholder_before["payload"] == placeholder_after["payload"]


def test_archetypes_sorted_by_id() -> None:
    """Migration report archetypes array must be sorted by archetype_id ascending."""
    proc = apply()
    assert proc.returncode == 0
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    ids = [row["archetype_id"] for row in report["archetypes"]]
    assert ids == sorted(ids)


def test_chunk_checksums_use_big_endian_header() -> None:
    """Chunk checksum rows must follow chunk-format.md big-endian header hashing."""
    proc = apply()
    assert proc.returncode == 0
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    manifest = load_layout(LAYOUT)
    stride = component_stride(manifest)
    for row in report["chunks"]:
        _, entities = read_chunk(CHUNKS, row["chunk_id"])
        payload = bytearray()
        for ent in entities:
            payload.extend(struct.pack(">I", ent["stable_id"]))
            body = bytearray(ent["payload"])
            body.extend(b"\x00" * max(0, stride - len(body)))
            payload.extend(bytes(body[:stride]))
        expected = chunk_checksum(row["chunk_id"], manifest["to_version"], bytes(payload))
        assert row["checksum"] == expected


def test_journal_marked_committed() -> None:
    """Successful apply must mark /app/data/replay.journal.json committed."""
    proc = apply()
    assert proc.returncode == 0
    journal = json.loads(JOURNAL.read_text(encoding="utf-8"))
    assert journal["status"] == "committed"
    assert journal["commit_cursor"] == 2


def test_second_apply_is_idempotent() -> None:
    """Re-apply on a committed journal must emit empty steps_applied and zero counters."""
    proc = apply()
    assert proc.returncode == 0
    first = json.loads(REPORT.read_text(encoding="utf-8"))
    proc = apply()
    assert proc.returncode == 0
    second = json.loads(REPORT.read_text(encoding="utf-8"))
    assert second["steps_applied"] == []
    assert second["entities_moved"] == 0
    assert second["ids_remapped"] == 0
    assert second["archetypes"] == first["archetypes"]


def test_move_step_chunks_touched_counts_source_only() -> None:
    """Move steps count distinct source chunks touched, not destination receive chunks."""
    proc = apply()
    assert proc.returncode == 0
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    step = report["steps_applied"][0]
    assert step["chunks_touched"] >= 1


def test_report_layout_version_two() -> None:
    """Report layout_version must reflect hot_reload_alpha to_version after apply."""
    proc = apply()
    assert proc.returncode == 0
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["layout_version"] == 2
    assert report["layout_id"] == "hot_reload_alpha"


def test_archetype_signatures_include_health() -> None:
    """Archetype rebuild must derive Health component signatures from live chunk payloads."""
    proc = apply()
    assert proc.returncode == 0
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    signatures = {row["signature"] for row in report["archetypes"]}
    assert any("Health" in sig for sig in signatures)


def test_sqlite_migration_state_committed() -> None:
    """Apply must persist committed migration_state rows in /app/data/ecs_meta.db."""
    proc = apply()
    assert proc.returncode == 0
    con = sqlite3.connect(DB)
    try:
        row = con.execute(
            "SELECT layout_version, journal_status, commit_cursor FROM migration_state WHERE id = 1"
        ).fetchone()
        assert row == (2, "committed", 2)
    finally:
        con.close()


def test_chunk_files_have_ecs_magic() -> None:
    """Binary chunk store under /app/data/chunks/ must remain valid ECS chunk files."""
    for path in sorted(CHUNKS.glob("chunk_*.bin")):
        magic = struct.unpack(">I", path.read_bytes()[:4])[0]
        assert magic == CHUNK_MAGIC


def test_tombstone_gap_hidden_fixture_remap() -> None:
    """TB3 tombstone-gap fixture requires skipping reserved ids during placeholder remap."""
    case = next(c for c in TB3_CATALOG["cases"] if c["id"] == "tombstone-gap")
    with tempfile.TemporaryDirectory(prefix="ecs-tb3-") as tmp:
        root = Path(tmp)
        db, chunks, journal = copy_fixture_tree(
            Path(case["db"]),
            Path(case["chunks"]),
            Path(case["journal"]),
            root,
        )
        out = root / "migration-report.json"
        proc = apply(db=db, chunks=chunks, journal=journal, report=out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads(out.read_text(encoding="utf-8"))
        assert report["ids_remapped"] >= 1
        con = sqlite3.connect(db)
        try:
            remapped = con.execute(
                "SELECT stable_id FROM entities WHERE alive = 1 AND stable_id = ?",
                (case["expect_stable_id"],),
            ).fetchone()
            assert remapped is not None
        finally:
            con.close()


def test_health_only_placeholder_hidden_archetype() -> None:
    """TB3 health-only placeholder fixture must rebuild a Health signature archetype."""
    case = next(c for c in TB3_CATALOG["cases"] if c["id"] == "health-only-placeholder")
    with tempfile.TemporaryDirectory(prefix="ecs-tb3-") as tmp:
        root = Path(tmp)
        db, chunks, journal = copy_fixture_tree(
            Path(case["db"]),
            Path(case["chunks"]),
            Path(case["journal"]),
            root,
        )
        out = root / "migration-report.json"
        proc = apply(db=db, chunks=chunks, journal=journal, report=out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
        report = json.loads(out.read_text(encoding="utf-8"))
        signatures = {row["signature"] for row in report["archetypes"]}
        assert case["expect_signature"] in signatures


def test_bundled_seed_not_mutated_after_hidden_runs() -> None:
    """Hidden fixture applies must not mutate bundled /app/data seed files."""
    db_bytes = DB.read_bytes()
    chunk1 = (CHUNKS / "chunk_0001.bin").read_bytes()
    case = next(c for c in TB3_CATALOG["cases"] if c["id"] == "tombstone-gap")
    with tempfile.TemporaryDirectory(prefix="ecs-tb3-") as tmp:
        root = Path(tmp)
        db, chunks, journal = copy_fixture_tree(
            Path(case["db"]),
            Path(case["chunks"]),
            Path(case["journal"]),
            root,
        )
        out = root / "migration-report.json"
        proc = apply(db=db, chunks=chunks, journal=journal, report=out)
        assert proc.returncode == 0, proc.stderr or proc.stdout
    reset_state()
    assert DB.read_bytes() == db_bytes
    assert (CHUNKS / "chunk_0001.bin").read_bytes() == chunk1
