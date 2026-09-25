"""Behavioral verifier for entmigrate post_author edge migrations."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest

from reference_migrate import (
    BUNDLED_CATALOG,
    UP_PHASES,
    assert_event_order,
    backfilled_author_count,
    connect,
    count_orphans,
    count_posts,
    expected_codegen_hash,
    has_column,
    index_exists,
    load_catalog,
    load_golden_patch,
    resolve_hidden_catalog,
    schema_version,
    trigger_exists,
)

APP = Path("/app")
CLI = "/usr/local/bin/entmigrate"
WORK = APP / "work"
REPORT = APP / "output/migration-report.json"
BROKEN = Path(__file__).resolve().parent / "broken"

PATCH_TARGETS = {
    "generator.go": APP / "internal/migrate/generator.go",
    "applier.go": APP / "internal/migrate/applier.go",
    "backfill.go": APP / "internal/migrate/backfill.go",
    "refresh.go": APP / "internal/codegen/refresh.go",
}

PROTECTED_SHA256 = {
    "fixtures/catalogs/bundled-v3.json": hashlib.sha256(
        BUNDLED_CATALOG.read_bytes()
    ).hexdigest(),
}


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "PATH": "/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:"
        + os.environ.get("PATH", ""),
    }
    proc = subprocess.run(
        cmd,
        cwd=str(APP),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if check and proc.returncode != 0:
        raise AssertionError(proc.stderr or proc.stdout or f"exit {proc.returncode}")
    return proc


def _reset() -> None:
    _run(["bash", str(APP / "scripts/reset-state.sh")])


def _build() -> None:
    _run(["bash", str(APP / "scripts/verifier-rebuild.sh")])


def _migrate_up(
    *,
    catalog: Path = BUNDLED_CATALOG,
    seed: str = "bundled",
    db: Path | None = None,
    expect_ok: bool = True,
) -> subprocess.CompletedProcess[str]:
    db_path = db or (WORK / "test.db")
    proc = _run(
        [
            CLI,
            "up",
            "--catalog",
            str(catalog),
            "--db",
            str(db_path),
            "--seed",
            seed,
            "--report",
            str(REPORT),
        ],
        check=False,
    )
    if expect_ok:
        assert proc.returncode == 0, proc.stderr or proc.stdout
    return proc


def _migrate_down(
    *, steps: int = 4, db: Path | None = None, expect_ok: bool = True
) -> subprocess.CompletedProcess[str]:
    db_path = db or (WORK / "test.db")
    proc = _run(
        [
            CLI,
            "down",
            "--catalog",
            str(BUNDLED_CATALOG),
            "--db",
            str(db_path),
            "--steps",
            str(steps),
            "--report",
            str(REPORT),
        ],
        check=False,
    )
    if expect_ok:
        assert proc.returncode == 0, proc.stderr or proc.stdout
    return proc


def _read_report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def _restore_broken_modules() -> None:
    for name, target in PATCH_TARGETS.items():
        shutil.copy(BROKEN / name, target)
    _build()


@contextmanager
def patched_module(name: str):
    _restore_broken_modules()
    try:
        PATCH_TARGETS[name].write_text(load_golden_patch(name), encoding="utf-8")
        _build()
        yield
    finally:
        _restore_broken_modules()


class TestEntMigrate:
    """SQLite ent-style edge migration barrier repair."""

    def setup_method(self) -> None:
        _reset()
        _build()

    def test_bundled_catalog_integrity(self) -> None:
        """Bundled catalog JSON must remain unchanged."""
        for rel, digest in PROTECTED_SHA256.items():
            path = APP / rel
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest

    def test_baseline_schema_version_two(self) -> None:
        """Seed bundled fixture leaves schema version 2 without author_id."""
        db = WORK / "baseline.db"
        _reset()
        conn = connect(db)
        try:
            seed_sql = (APP / "fixtures/seeds/bundled.sql").read_text(encoding="utf-8")
            conn.executescript(seed_sql)
            assert schema_version(conn) == 2
            assert not has_column(conn, "posts", "author_id")
        finally:
            conn.close()

    def test_migrate_up_success(self) -> None:
        """entmigrate up completes on bundled catalog."""
        _migrate_up()
        report = _read_report()
        assert report["schema_version"] == 3
        assert report["direction"] == "up"

    def test_codegen_hash_matches_reference(self) -> None:
        """Report codegen_hash must match independent ent refresh reference."""
        cat = load_catalog(BUNDLED_CATALOG)
        _migrate_up()
        report = _read_report()
        assert report["codegen_hash"] == expected_codegen_hash(cat)
        assert report["codegen_hash"] != "ent-codegen-v2-stale"

    def test_event_ordering(self) -> None:
        """Events list must follow migration-pipeline.md phase order."""
        _migrate_up()
        report = _read_report()
        assert_event_order(report["events"])

    def test_backfill_and_counts(self) -> None:
        """All bundled posts receive author_id with zero orphans."""
        _migrate_up()
        report = _read_report()
        conn = connect(WORK / "test.db")
        try:
            assert backfilled_author_count(conn) == count_posts(conn)
            assert count_orphans(conn) == 0
            assert report["counts"]["orphans"] == 0
            assert report["counts"]["posts"] == count_posts(conn)
        finally:
            conn.close()

    def test_index_and_edge_trigger(self) -> None:
        """Schema version 3 exposes idx_posts_author and trg_post_author_edge."""
        _migrate_up()
        conn = connect(WORK / "test.db")
        try:
            assert index_exists(conn, "idx_posts_author")
            assert trigger_exists(conn, "trg_post_author_edge")
        finally:
            conn.close()

    def test_full_down_restores_v2(self) -> None:
        """Four down steps restore schema version 2 without author_id."""
        _migrate_up()
        _migrate_down(steps=4)
        conn = connect(WORK / "test.db")
        try:
            assert schema_version(conn) == 2
            assert not has_column(conn, "posts", "author_id")
            assert not index_exists(conn, "idx_posts_author")
            assert not trigger_exists(conn, "trg_post_author_edge")
        finally:
            conn.close()

    def test_first_down_step_detaches_fk(self) -> None:
        """First rollback step must drop edge trigger, not index-first."""
        _migrate_up()
        _migrate_down(steps=1)
        conn = connect(WORK / "test.db")
        try:
            assert not trigger_exists(conn, "trg_post_author_edge")
            assert index_exists(conn, "idx_posts_author")
        finally:
            conn.close()

    def test_up_down_cycle_idempotent_shape(self) -> None:
        """Up then full down returns to v2 row counts."""
        db = WORK / "cycle.db"
        _migrate_up(db=db)
        posts_after_up = count_posts(connect(db))
        connect(db).close()
        _migrate_down(steps=4, db=db)
        conn = connect(db)
        try:
            assert schema_version(conn) == 2
            assert count_posts(conn) == posts_after_up
        finally:
            conn.close()

    def test_hidden_orphan_seed_rejected(self) -> None:
        """Hidden orphan fixture must fail migrate up even with repaired code."""
        hidden = resolve_hidden_catalog()
        assert hidden.is_file(), "hidden catalog missing from image"
        proc = _migrate_up(
            catalog=hidden,
            seed="hidden-orphan",
            db=WORK / "hidden.db",
            expect_ok=False,
        )
        assert proc.returncode != 0

    def test_tb3_catalog_dir_hidden_orphan(self) -> None:
        """TB3_CATALOG_DIR must resolve hidden catalogs with the bundled schema."""
        os.environ["TB3_CATALOG_DIR"] = "/opt/verifier-fixtures/ent-edge"
        hidden = resolve_hidden_catalog()
        assert hidden.is_file()
        proc = _migrate_up(
            catalog=hidden,
            seed="hidden-orphan",
            db=WORK / "tb3-hidden.db",
            expect_ok=False,
        )
        assert proc.returncode != 0

    def test_partial_backfill_seed_up(self) -> None:
        """partial-backfill seed uses u:N refs and must migrate when backfill is correct."""
        db = WORK / "partial.db"
        _migrate_up(seed="partial-backfill", db=db)
        conn = connect(db)
        try:
            assert backfilled_author_count(conn) == count_posts(conn)
            assert count_orphans(conn) == 0
        finally:
            conn.close()

    def test_partial_backfill_down_drops_fk_first(self) -> None:
        """After partial-backfill up, first down step detaches edge before index."""
        db = WORK / "partial-down.db"
        _migrate_up(seed="partial-backfill", db=db)
        _migrate_down(steps=1, db=db)
        conn = connect(db)
        try:
            assert not trigger_exists(conn, "trg_post_author_edge")
            assert index_exists(conn, "idx_posts_author")
        finally:
            conn.close()

    def test_snapshot_seq_positive(self) -> None:
        """Atlas snapshot records positive table count after codegen."""
        _migrate_up()
        report = _read_report()
        assert report["snapshot_seq"] > 0

    def test_report_phases_complete(self) -> None:
        """Report lists every up phase from the contract."""
        _migrate_up()
        phases = [e["phase"] for e in _read_report()["events"]]
        assert phases == UP_PHASES


@pytest.mark.parametrize(
    "module_name",
    ["generator.go", "applier.go", "backfill.go", "refresh.go"],
)
def test_isolated_golden_module_insufficient(module_name: str) -> None:
    """Single-module golden patch alone must not pass full bundled migrate up."""
    _reset()
    _restore_broken_modules()
    with patched_module(module_name):
        _reset()
        proc = _migrate_up(expect_ok=False)
        assert proc.returncode != 0, module_name
