"""SQLite schema migration dirty guard and version ledger exporter tests."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

CLI = "/app/bin/migratectl"
DEFAULT_DB = Path("/app/state/migrations.db")
DEFAULT_STAGE = Path("/app/state/migrate-stage.json")
LEDGER = Path("/app/output/version-ledger.json")


def _db_path() -> Path:
    suffix = os.environ.get("TB3_DB_SUFFIX", "")
    if suffix:
        return Path(f"/app/state/migrations.db{suffix}")
    return DEFAULT_DB


def _stage_path() -> Path:
    suffix = os.environ.get("TB3_DB_SUFFIX", "")
    if suffix:
        return Path(f"/app/state/migrate-stage{suffix}.json")
    return DEFAULT_STAGE


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return sorted(rows, key=lambda r: r["seq"])


def reference_split_sql(sql: str) -> list[str]:
    out: list[str] = []
    cur: list[str] = []
    in_quote = False
    for ch in sql:
        if ch == "'":
            in_quote = not in_quote
            cur.append(ch)
            continue
        if ch == ";" and not in_quote:
            stmt = "".join(cur).strip()
            if stmt:
                out.append(stmt)
            cur = []
            continue
        cur.append(ch)
    stmt = "".join(cur).strip()
    if stmt:
        out.append(stmt)
    return out


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER NOT NULL,
            dirty INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS version_log (
            version INTEGER NOT NULL
        );
        """
    )


def _read_version(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT version FROM schema_migrations ORDER BY rowid DESC LIMIT 1"
    ).fetchone()
    return int(row[0]) if row else 0


def _read_dirty(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT dirty FROM schema_migrations ORDER BY rowid DESC LIMIT 1"
    ).fetchone()
    return bool(row and int(row[0]) != 0)


def _write_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute("DELETE FROM schema_migrations")
    conn.execute(
        "INSERT INTO schema_migrations (version, dirty) VALUES (?, 0)", (version,)
    )


def _write_dirty(conn: sqlite3.Connection, dirty: bool) -> None:
    version = _read_version(conn)
    conn.execute("DELETE FROM schema_migrations")
    conn.execute(
        "INSERT INTO schema_migrations (version, dirty) VALUES (?, ?)",
        (version, 1 if dirty else 0),
    )


def _exec_statements(conn: sqlite3.Connection, sql: str) -> None:
    for stmt in reference_split_sql(sql):
        conn.execute(stmt)


def reference_apply(events: list[dict[str, Any]], db_path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    try:
        _ensure_schema(conn)
        stage = {
            "last_seq": 0,
            "version": 0,
            "dirty": False,
            "failed_down_rollbacks": 0,
            "applied_steps": 0,
        }
        for ev in events:
            if ev["direction"] == "up":
                if _read_dirty(conn):
                    raise RuntimeError(f"dirty guard at seq {ev['seq']}")
                try:
                    _exec_statements(conn, ev["sql"])
                except sqlite3.Error:
                    _write_dirty(conn, True)
                    rollbacks = 0
                    for down in events:
                        if (
                            down["seq"] > ev["seq"]
                            and down["direction"] == "down"
                            and down["version"] == ev["version"]
                        ):
                            _exec_statements(conn, down["sql"])
                            rollbacks += 1
                    stage["failed_down_rollbacks"] += rollbacks
                    if rollbacks > 0:
                        _write_dirty(conn, False)
                        stage["dirty"] = False
                    else:
                        stage["dirty"] = True
                    stage["version"] = _read_version(conn)
                    stage["last_seq"] = ev["seq"]
                    stage["applied_steps"] += 1
                    conn.commit()
                    raise
                _write_version(conn, ev["version"])
                conn.execute(
                    "INSERT INTO version_log (version) VALUES (?)", (ev["version"],)
                )
                _write_dirty(conn, False)
                stage["version"] = ev["version"]
                stage["dirty"] = False
            elif ev["direction"] == "down":
                _exec_statements(conn, ev["sql"])
                _write_version(conn, ev["version"] - 1)
                stage["version"] = ev["version"] - 1
            stage["last_seq"] = ev["seq"]
            stage["applied_steps"] += 1
            conn.commit()
        return stage
    finally:
        conn.close()


def reference_export(db_path: Path, stage: dict[str, Any], export_pass: int) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT version FROM version_log").fetchall()
        max_v = max((int(r[0]) for r in rows), default=0)
        return {
            "max_version": max_v,
            "dirty": _read_dirty(conn),
            "failed_down_rollbacks": stage.get("failed_down_rollbacks", 0),
            "stage_version": stage.get("version", 0),
            "export_pass": export_pass,
        }
    finally:
        conn.close()


def reset_state() -> None:
    db = _db_path()
    stage = _stage_path()
    if db.exists():
        db.unlink()
    if stage.exists():
        stage.unlink()
    if LEDGER.exists():
        LEDGER.unlink()


def run_apply(journal: Path, *, expect_fail: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [CLI, "apply", str(journal)], capture_output=True, text=True, check=False
    )
    if expect_fail:
        assert proc.returncode != 0, proc.stdout + proc.stderr
    else:
        assert proc.returncode == 0, proc.stderr + proc.stdout
    return proc


def run_export(pass_n: int = 1) -> None:
    proc = subprocess.run(
        [CLI, "export", "--pass", str(pass_n)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert LEDGER.is_file()


def load_stage() -> dict[str, Any]:
    return json.loads(_stage_path().read_text(encoding="utf-8"))


def load_ledger() -> dict[str, Any]:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


class TestMigratectlBasics:
    def test_subprocess_cli_binary_exists(self) -> None:
        """migratectl must be invoked as a rebuilt subprocess CLI binary."""
        proc = subprocess.run(["test", "-x", CLI], capture_output=True, text=True)
        assert proc.returncode == 0

    def test_apply_writes_stage_snapshot(self) -> None:
        """apply must materialize /app/state/migrate-stage.json."""
        reset_state()
        run_apply(Path("/app/data/happy_path.jsonl"))
        assert _stage_path().is_file()

    def test_happy_path_stage_matches_reference(self) -> None:
        """Stage version and dirty flag must match independent reference apply."""
        reset_state()
        events = _load_jsonl(Path("/app/data/happy_path.jsonl"))
        run_apply(Path("/app/data/happy_path.jsonl"))
        ref_db = Path("/tmp/reference_happy.db")
        if ref_db.exists():
            ref_db.unlink()
        ref = reference_apply(events, ref_db)
        stage = load_stage()
        assert stage["version"] == ref["version"] == 2
        assert stage["dirty"] is False
        assert stage["last_seq"] == ref["last_seq"]


class TestDirtyVersionGuard:
    def test_failed_up_keeps_prior_version(self) -> None:
        """Version must advance only after successful up commit per dirty-version-guard.md."""
        reset_state()
        run_apply(Path("/app/data/failed_rollback.jsonl"), expect_fail=True)
        stage = load_stage()
        assert stage["version"] == 1

    def test_failed_down_rollback_counter(self) -> None:
        """Stage failed_down_rollbacks must count journal down steps after failed up."""
        reset_state()
        run_apply(Path("/app/data/failed_rollback.jsonl"), expect_fail=True)
        stage = load_stage()
        assert stage["failed_down_rollbacks"] == 1

    def test_dirty_guard_blocks_second_up(self) -> None:
        """Second up must be rejected while schema_migrations dirty remains set."""
        reset_state()
        run_apply(Path("/app/data/failed_no_down.jsonl"), expect_fail=True)
        proc = subprocess.run(
            [CLI, "apply", "/app/data/dirty_block.jsonl"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode != 0
        assert "dirty" in (proc.stderr + proc.stdout).lower()

    def test_failed_up_clears_dirty_after_rollback(self) -> None:
        """Dirty clears only after down rollback steps execute."""
        reset_state()
        run_apply(Path("/app/data/failed_rollback.jsonl"), expect_fail=True)
        stage = load_stage()
        assert stage["dirty"] is False


class TestStatementSplit:
    def test_literal_semicolon_insert_value(self) -> None:
        """Semicolons inside string literals must not split statements early."""
        reset_state()
        run_apply(Path("/app/data/literal_semicolon.jsonl"))
        conn = sqlite3.connect(_db_path())
        row = conn.execute("SELECT note FROM dept WHERE id = 1").fetchone()
        conn.close()
        assert row is not None
        assert row[0] == "a;b"

    def test_literal_semicolon_second_statement_runs(self) -> None:
        """Second statement after literal semicolon must still execute."""
        reset_state()
        run_apply(Path("/app/data/literal_semicolon.jsonl"))
        conn = sqlite3.connect(_db_path())
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert "audit_log" in tables


class TestVersionLedgerExport:
    def test_export_writes_ledger_file(self) -> None:
        """export must write /app/output/version-ledger.json."""
        reset_state()
        run_apply(Path("/app/data/happy_path.jsonl"))
        run_export()
        assert LEDGER.is_file()

    def test_version_sort_integer_max_not_lexicographic(self) -> None:
        """max_version must use integer compare not lexicographic string sort."""
        reset_state()
        run_apply(Path("/app/data/version_sort.jsonl"))
        run_export()
        ledger = load_ledger()
        assert ledger["max_version"] == 10

    def test_export_pass_flag(self) -> None:
        """export --pass N must echo export_pass in the ledger."""
        reset_state()
        run_apply(Path("/app/data/happy_path.jsonl"))
        run_export(pass_n=3)
        ledger = load_ledger()
        assert ledger["export_pass"] == 3

    def test_export_stage_version_matches_snapshot(self) -> None:
        """Ledger stage_version must match migrate-stage.json version field."""
        reset_state()
        run_apply(Path("/app/data/happy_path.jsonl"))
        stage = load_stage()
        run_export()
        ledger = load_ledger()
        assert ledger["stage_version"] == stage["version"]

    def test_export_failed_rollback_counter_propagated(self) -> None:
        """Ledger failed_down_rollbacks must copy stage snapshot counter."""
        reset_state()
        run_apply(Path("/app/data/failed_rollback.jsonl"), expect_fail=True)
        run_export()
        ledger = load_ledger()
        assert ledger["failed_down_rollbacks"] == 1


class TestStagingSnapshot:
    def test_stage_contains_required_fields(self) -> None:
        """Stage snapshot must expose version dirty and rollback counter fields."""
        reset_state()
        run_apply(Path("/app/data/happy_path.jsonl"))
        stage = load_stage()
        for key in (
            "last_seq",
            "version",
            "dirty",
            "failed_down_rollbacks",
            "applied_steps",
        ):
            assert key in stage

    def test_reapply_happy_path_idempotent(self) -> None:
        """Re-applying the same journal reproduces stage version deterministically."""
        reset_state()
        events = _load_jsonl(Path("/app/data/happy_path.jsonl"))
        run_apply(Path("/app/data/happy_path.jsonl"))
        first = load_stage()
        _stage_path().unlink()
        run_apply(Path("/app/data/happy_path.jsonl"))
        second = load_stage()
        ref_db = Path("/tmp/reference_reapply.db")
        if ref_db.exists():
            ref_db.unlink()
        ref = reference_apply(events, ref_db)
        assert first["version"] == second["version"] == ref["version"]


class TestHiddenFixtures:
    def test_tb3_db_suffix_isolates_state(self) -> None:
        """TB3_DB_SUFFIX must isolate /app/state/migrations.db from default path."""
        reset_state()
        os.environ["TB3_DB_SUFFIX"] = "_tb3"
        try:
            run_apply(Path("/app/data/happy_path.jsonl"))
            assert _db_path().is_file()
            assert not DEFAULT_DB.exists()
        finally:
            os.environ.pop("TB3_DB_SUFFIX", None)
            reset_state()

    def test_tb3_literal_semicolon_hidden_note(self) -> None:
        """Hidden TB3_LITERAL_NOTE must survive literal-safe statement splitting."""
        reset_state()
        note = os.environ.get("TB3_LITERAL_NOTE", "x;y")
        events = _load_jsonl(Path("/app/data/literal_semicolon.jsonl"))
        events[1]["sql"] = (
            f"INSERT INTO dept (id, note) VALUES (2, '{note}'); "
            "CREATE TABLE audit_log (id INTEGER PRIMARY KEY);"
        )
        tmp = Path("/tmp/tb3_literal.jsonl")
        tmp.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
        run_apply(tmp)
        conn = sqlite3.connect(_db_path())
        row = conn.execute("SELECT note FROM dept WHERE id = 2").fetchone()
        conn.close()
        assert row is not None
        assert row[0] == note


class TestExclusiveLock:
    def test_exclusive_lock_blocks_concurrent_apply(self) -> None:
        """export must hold BEGIN EXCLUSIVE so concurrent apply cannot write."""
        reset_state()
        run_apply(Path("/app/data/happy_path.jsonl"))
        os.environ["TB3_EXPORT_HOLD_MS"] = "600"
        errors: list[str] = []

        def do_export() -> None:
            proc = subprocess.run(
                [CLI, "export"],
                capture_output=True,
                text=True,
                check=False,
                env={**os.environ},
            )
            if proc.returncode != 0:
                errors.append(proc.stderr)

        def do_apply() -> None:
            time.sleep(0.05)
            proc = subprocess.run(
                [CLI, "apply", "/app/data/dirty_block.jsonl"],
                capture_output=True,
                text=True,
                check=False,
                env={**os.environ},
            )
            if proc.returncode == 0:
                errors.append("apply should fail under export lock")

        t1 = threading.Thread(target=do_export)
        t2 = threading.Thread(target=do_apply)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)
        os.environ.pop("TB3_EXPORT_HOLD_MS", None)
        assert not errors, errors

    def test_version_log_rows_after_happy_path(self) -> None:
        """Each successful up must append one row to version_log."""
        reset_state()
        run_apply(Path("/app/data/happy_path.jsonl"))
        conn = sqlite3.connect(_db_path())
        rows = conn.execute("SELECT version FROM version_log ORDER BY rowid").fetchall()
        conn.close()
        assert [int(r[0]) for r in rows] == [1, 2]
