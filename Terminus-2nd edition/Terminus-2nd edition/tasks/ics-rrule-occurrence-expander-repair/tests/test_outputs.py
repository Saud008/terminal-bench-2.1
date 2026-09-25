"""Behavioral verifier for expand CLI + SQLite output."""

from __future__ import annotations

import hashlib
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

VERIFIER_LIB = Path(__file__).resolve().parent / "verifier-lib"
sys.path.insert(0, str(VERIFIER_LIB))
from reference_expand import (  # noqa: E402
    procedural_biweekly,
    procedural_combo,
    procedural_ics,
    procedural_monthly_setpos,
    read_db,
    reference_expand,
)

APP = Path("/app")
CLI = "/usr/local/bin/expand"
CALENDARS = APP / "fixtures/calendars"
OUTPUT = APP / "output"
RESET = APP / "scripts/reset-state.sh"
SEED = "ical-expand-seed-7"
EXTRA_SEEDS = (
    "ical-matrix-07",
    "ical-matrix-13",
    "ical-matrix-19",
    "ical-matrix-42",
    "ical-matrix-55",
    "ical-matrix-88",
    "ical-matrix-91",
)

FIXTURE_WINDOWS = {
    "weekly-byday.ics": "2024-01-01T00:00:00Z/2024-02-29T23:59:59Z",
    "monthly-setpos.ics": "2024-01-01T00:00:00Z/2024-04-30T23:59:59Z",
    "exdate-rdate.ics": "2024-01-01T00:00:00Z/2024-02-29T23:59:59Z",
    "count-exdate.ics": "2024-01-01T00:00:00Z/2024-03-31T23:59:59Z",
    "until-floating.ics": "2024-01-01T00:00:00Z/2024-03-31T23:59:59Z",
    "dst-spring.ics": "2024-03-01T00:00:00Z/2024-04-30T23:59:59Z",
    "negative-setpos.ics": "2024-01-01T00:00:00Z/2024-04-30T23:59:59Z",
    "interval-biweekly.ics": "2024-01-01T00:00:00Z/2024-03-31T23:59:59Z",
    "until-utc.ics": "2024-01-01T00:00:00Z/2024-03-31T23:59:59Z",
    "exdate-on-rdate.ics": "2024-01-01T00:00:00Z/2024-02-29T23:59:59Z",
}

STRICT_FIXTURES = list(FIXTURE_WINDOWS.keys())

PROTECTED_SHA256: dict[str, str] = {
    "calendars/count-exdate.ics": "5e8ab3c4ea49c5226c63018c258710b959ea3e9aa84eab37abbb59174480bd60",
    "calendars/dst-spring.ics": "27880660533fa3ddd2e66973260e0b7de076e436bfededb1ec051e84f6fd5d44",
    "calendars/exdate-on-rdate.ics": "12d5edb22a5348785b58a76104c68d348c21234aa1f8c4adffd4956601ed9b4f",
    "calendars/exdate-rdate.ics": "981513715216b8c1596b01569dba178d8614808b83db68f6b807ab1622e1337f",
    "calendars/interval-biweekly.ics": "9c6a6d48660b7897c6326bdf4955a738f4722928fb8dcb537ba51e62ec4927cd",
    "calendars/monthly-setpos.ics": "5d1a716dcba4e59cc3eebcf0b28144a3f16a6441d957892ea508902676a26d09",
    "calendars/negative-setpos.ics": "234a3ba64b12b5cc9a171b0935a74c8db9d677cb03ecda30f8226b6cdfdae5bf",
    "calendars/until-floating.ics": "c9731e537b01f4ffc4d33b1b8ba9582314256ad97f2984aedd70f1a6d30d49a1",
    "calendars/until-utc.ics": "ae820d0a3fa80dc3a01dde8234f5ceae93d5452ee1085c02bef0ee90c8f3ba5c",
    "calendars/weekly-byday.ics": "b50de038512417891fcdfd32fe2cb37b4707f7be69243622fe13093e641e04bb",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def build_cli() -> None:
    proc = run(["go", "build", "-mod=readonly", "-o", CLI, "./cmd/expand"])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def expand_cli(ics: Path, window: str, db: Path) -> subprocess.CompletedProcess[str]:
    db.parent.mkdir(parents=True, exist_ok=True)
    return run([CLI, "--ics", str(ics), "--window", window, "--db", str(db)])


def assert_matches_reference(ics: Path, window: str, db: Path) -> None:
    proc = expand_cli(ics, window, db)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert read_db(db) == reference_expand(ics, window)


def read_db_with_seq(path: Path) -> list[tuple[str, str, int]]:
    conn = sqlite3.connect(path)
    cur = conn.execute(
        "SELECT uid, start_utc, seq FROM occurrences ORDER BY start_utc ASC, uid ASC"
    )
    rows = [(r[0], r[1], int(r[2])) for r in cur.fetchall()]
    conn.close()
    return rows


class TestExpand:
    """RRULE expansion into SQLite."""

    def setup_method(self) -> None:
        reset()
        build_cli()

    def test_fixture_integrity(self) -> None:
        """Bundled calendars must remain unchanged."""
        assert PROTECTED_SHA256, "populate PROTECTED_SHA256 before upload"
        for rel, digest in PROTECTED_SHA256.items():
            path = APP / "fixtures" / rel
            assert _sha256(path) == digest, rel

    def test_cli_missing_args_fails(self) -> None:
        """expand must exit non-zero when required flags are omitted."""
        proc = run([CLI])
        assert proc.returncode != 0

    def test_malformed_calendar_fails(self) -> None:
        """expand must exit non-zero for malformed calendar input."""
        proc = expand_cli(
            CALENDARS / "malformed.ics",
            "2024-01-01T00:00:00Z/2024-12-31T23:59:59Z",
            OUTPUT / "bad.db",
        )
        assert proc.returncode != 0

    @pytest.mark.parametrize("name", STRICT_FIXTURES)
    def test_fixture_matches_reference(self, name: str) -> None:
        """Core fixtures must match the independent reference for the contract window."""
        window = FIXTURE_WINDOWS[name]
        assert_matches_reference(CALENDARS / name, window, OUTPUT / f"{name}.db")

    def test_dst_spring_gap_suppressed(self) -> None:
        """Spring-forward gap must not create an occurrence row."""
        name = "dst-spring.ics"
        window = FIXTURE_WINDOWS[name]
        db = OUTPUT / "dst-check.db"
        proc = expand_cli(CALENDARS / name, window, db)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert len(read_db(db)) == 2

    def test_exdate_with_rdate(self) -> None:
        """EXDATE must apply even when RDATE is present."""
        name = "exdate-rdate.ics"
        window = FIXTURE_WINDOWS[name]
        db = OUTPUT / "mix-check.db"
        proc = expand_cli(CALENDARS / name, window, db)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        starts = [r[1] for r in read_db(db)]
        assert "2024-01-17T15:00:00Z" not in starts
        assert len(starts) == 4

    def test_exdate_on_rdate_suppressed(self) -> None:
        """EXDATE must remove RDATE injections that match the exception."""
        name = "exdate-on-rdate.ics"
        window = FIXTURE_WINDOWS[name]
        db = OUTPUT / "exdate-rdate-overlap.db"
        proc = expand_cli(CALENDARS / name, window, db)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        starts = [r[1] for r in read_db(db)]
        assert "2024-01-10T15:00:00Z" not in starts
        assert len(starts) == 3

    def test_count_after_exdate(self) -> None:
        """COUNT must be enforced after EXDATE filtering."""
        name = "count-exdate.ics"
        window = FIXTURE_WINDOWS[name]
        db = OUTPUT / "count-check.db"
        proc = expand_cli(CALENDARS / name, window, db)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert len(read_db(db)) == 5

    def test_negative_setpos_last_friday(self) -> None:
        """BYSETPOS=-1 must select the last matching weekday in each month."""
        name = "negative-setpos.ics"
        window = FIXTURE_WINDOWS[name]
        db = OUTPUT / "neg-setpos.db"
        proc = expand_cli(CALENDARS / name, window, db)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        starts = [r[1] for r in read_db(db)]
        assert len(starts) == 3
        assert "2024-01-26T15:00:00Z" in starts
        assert "2024-02-23T15:00:00Z" in starts

    def test_until_floating_inclusive_boundary(self) -> None:
        """Floating UNTIL must include the boundary occurrence."""
        name = "until-floating.ics"
        window = FIXTURE_WINDOWS[name]
        db = OUTPUT / "until-float.db"
        proc = expand_cli(CALENDARS / name, window, db)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        starts = [r[1] for r in read_db(db)]
        assert "2024-01-29T09:00:00Z" in starts

    def test_until_utc_boundary(self) -> None:
        """Z-suffixed UNTIL must compare in UTC."""
        name = "until-utc.ics"
        window = FIXTURE_WINDOWS[name]
        db = OUTPUT / "until-utc.db"
        assert_matches_reference(CALENDARS / name, window, db)

    def test_biweekly_interval_stride(self) -> None:
        """INTERVAL=2 must skip alternate weeks."""
        name = "interval-biweekly.ics"
        window = FIXTURE_WINDOWS[name]
        db = OUTPUT / "biweekly.db"
        proc = expand_cli(CALENDARS / name, window, db)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        starts = [r[1] for r in read_db(db)]
        assert len(starts) == 4
        assert "2024-01-02T20:00:00Z" in starts
        assert "2024-01-09T20:00:00Z" not in starts

    def test_seq_column_matches_global_sort(self) -> None:
        """seq must be zero-based row order after global start_utc then uid sort."""
        name = "exdate-rdate.ics"
        window = FIXTURE_WINDOWS[name]
        db = OUTPUT / "seq-check.db"
        proc = expand_cli(CALENDARS / name, window, db)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        rows = read_db_with_seq(db)
        assert rows, "expected at least one occurrence row"
        assert [seq for _, _, seq in rows] == list(range(len(rows)))

    def test_run_replaces_prior_rows(self) -> None:
        """Each expand run must replace all rows in the target database."""
        name = "weekly-byday.ics"
        narrow = "2024-01-01T00:00:00Z/2024-01-15T23:59:59Z"
        wide = FIXTURE_WINDOWS[name]
        db = OUTPUT / "replace-check.db"
        first = expand_cli(CALENDARS / name, narrow, db)
        assert first.returncode == 0, first.stderr + first.stdout
        narrow_count = len(read_db(db))
        second = expand_cli(CALENDARS / name, wide, db)
        assert second.returncode == 0, second.stderr + second.stdout
        wide_rows = read_db(db)
        assert len(wide_rows) > narrow_count
        assert wide_rows == reference_expand(CALENDARS / name, wide)

    def test_procedural_generated_calendar(self) -> None:
        """Fresh generated ICS must match the harness reference."""
        ics_path = OUTPUT / f"proc-{SEED}.ics"
        ics_path.write_text(procedural_ics(SEED), encoding="utf-8")
        window = "2024-01-01T00:00:00Z/2024-06-30T23:59:59Z"
        assert_matches_reference(ics_path, window, OUTPUT / f"proc-{SEED}.db")

    @pytest.mark.parametrize("seed", EXTRA_SEEDS)
    def test_procedural_matrix_weekly(self, seed: str) -> None:
        """Independent seeds must expand procedural weekly calendars."""
        ics_path = OUTPUT / f"proc-weekly-{seed}.ics"
        ics_path.write_text(procedural_ics(seed), encoding="utf-8")
        window = "2024-01-01T00:00:00Z/2024-06-30T23:59:59Z"
        assert_matches_reference(ics_path, window, OUTPUT / f"proc-weekly-{seed}.db")

    @pytest.mark.parametrize("seed", EXTRA_SEEDS)
    def test_procedural_matrix_monthly_setpos(self, seed: str) -> None:
        """Independent seeds must expand procedural monthly BYSETPOS calendars."""
        ics_path = OUTPUT / f"proc-monthly-{seed}.ics"
        ics_path.write_text(procedural_monthly_setpos(seed), encoding="utf-8")
        window = "2024-01-01T00:00:00Z/2024-06-30T23:59:59Z"
        assert_matches_reference(ics_path, window, OUTPUT / f"proc-monthly-{seed}.db")

    @pytest.mark.parametrize("seed", EXTRA_SEEDS)
    def test_procedural_matrix_biweekly(self, seed: str) -> None:
        """Independent seeds must expand procedural biweekly calendars."""
        ics_path = OUTPUT / f"proc-biweekly-{seed}.ics"
        ics_path.write_text(procedural_biweekly(seed), encoding="utf-8")
        window = "2024-01-01T00:00:00Z/2024-06-30T23:59:59Z"
        assert_matches_reference(ics_path, window, OUTPUT / f"proc-biweekly-{seed}.db")

    @pytest.mark.parametrize("seed", EXTRA_SEEDS)
    def test_procedural_combo_interactions(self, seed: str) -> None:
        """Generated calendars mixing COUNT, EXDATE, and RDATE must match reference."""
        ics_path = OUTPUT / f"proc-combo-{seed}.ics"
        ics_path.write_text(procedural_combo(seed), encoding="utf-8")
        window = "2024-01-01T00:00:00Z/2024-06-30T23:59:59Z"
        assert_matches_reference(ics_path, window, OUTPUT / f"proc-combo-{seed}.db")
