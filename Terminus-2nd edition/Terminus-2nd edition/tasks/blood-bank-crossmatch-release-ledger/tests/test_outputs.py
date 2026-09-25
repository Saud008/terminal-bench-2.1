"""Bundled serology release scenarios for bbreleasectl.

Covers ingest-only import-panels, compatibility-matrix buffer, and export seal-releases layers.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess

import pytest

from crossmatch_spec import reference_crossmatch, reference_releases
from hemo_session import PATHS, HemotherapySession


@pytest.fixture()
def session() -> HemotherapySession:
    s = HemotherapySession()
    s.clear_workspace()
    return s


class TestPanelImport:
    def test_cli_help_surface(self, session: HemotherapySession) -> None:
        """CLI must expose documented verbs from cli-surface.md."""
        proc = subprocess.run(
            [str(PATHS.binary)],
            cwd=PATHS.workspace,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 2
        assert "import-panels" in proc.stderr

    def test_import_hydrates_sqlite(self, session: HemotherapySession) -> None:
        """import-panels must persist patient and unit rows in /app/state/release.db per scenario-load-contract."""
        session.import_panels("abo-clean-release")
        con = sqlite3.connect(PATHS.release_db)
        try:
            assert con.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 1
            assert con.execute("SELECT COUNT(*) FROM units").fetchone()[0] == 1
        finally:
            con.close()


class TestSerologyReleases:
    def test_abo_clean_matches_spec(self, session: HemotherapySession) -> None:
        """ABO compatibility closure must match independent crossmatch_spec for abo-clean-release."""
        session.run_full("abo-clean-release")
        spec = reference_releases("abo-clean-release", PATHS.fixture_root)
        ledger = json.loads(PATHS.ledger_json.read_text(encoding="utf-8"))
        assert ledger["releases"] == spec["releases"]
        assert ledger["ledger_digest"] == spec["ledger_digest"]

    def test_rh_negative_selects_neg_unit(self, session: HemotherapySession) -> None:
        """Rh-negative patients must receive Rh-negative units unless waiver applies per abo-rh-compatibility-contract."""
        session.run_full("rh-negative-guard")
        body = session.read_ledger()
        spec = reference_releases("rh-negative-guard", PATHS.fixture_root)
        assert body["releases"] == spec["releases"]

    def test_anti_e_blocks_e_antigen_unit(self, session: HemotherapySession) -> None:
        """Antibody exclusion must reject units carrying the matched antigen per antibody-exclusion-contract."""
        session.run_full("antibody-anti-e")
        assert session.read_ledger()["releases"] == reference_releases(
            "antibody-anti-e", PATHS.fixture_root
        )["releases"]

    def test_expired_unit_rejected(self, session: HemotherapySession) -> None:
        """Units past expires_at relative to release_clock must not release per unit-expiration-contract."""
        session.run_full("unit-expired-window")
        assert session.read_ledger()["releases"] == reference_releases(
            "unit-expired-window", PATHS.fixture_root
        )["releases"]

    def test_emergency_waiver_audit(self, session: HemotherapySession) -> None:
        """Emergency overrides must surface authorizer audit fields per emergency-override-contract."""
        session.run_full("emergency-override-audit")
        body = session.read_ledger()
        spec = reference_releases("emergency-override-audit", PATHS.fixture_root)
        assert body["releases"] == spec["releases"]

    def test_o_recipient_only_o_unit(self, session: HemotherapySession) -> None:
        """Group O recipients must only receive group O units per abo-rh-compatibility-contract."""
        session.run_full("abo-o-universal-donor")
        assert session.read_ledger()["releases"] == reference_releases(
            "abo-o-universal-donor", PATHS.fixture_root
        )["releases"]

    def test_earliest_collection_wins(self, session: HemotherapySession) -> None:
        """Tie-break among compatible units must prefer earliest collected_at per release-ledger-contract."""
        session.run_full("multi-unit-collect-order")
        assert session.read_ledger()["releases"] == reference_releases(
            "multi-unit-collect-order", PATHS.fixture_root
        )["releases"]

    def test_ab_recipient_accepts_a_or_b(self, session: HemotherapySession) -> None:
        """Group AB recipients may accept A, B, AB, or O units per abo-rh-compatibility-contract."""
        session.run_full("ab-recipient-broad")
        body = session.read_ledger()
        spec = reference_releases("ab-recipient-broad", PATHS.fixture_root)
        assert body["releases"] == spec["releases"]

    def test_dual_antibody_panel(self, session: HemotherapySession) -> None:
        """Multiple antibodies must each exclude matching antigens per antibody-exclusion-contract."""
        session.run_full("dual-antibody-panel")
        assert session.read_ledger()["releases"] == reference_releases(
            "dual-antibody-panel", PATHS.fixture_root
        )["releases"]


class TestLedgerPersistence:
    def test_repeat_seal_digest(self, session: HemotherapySession) -> None:
        """Repeated seal-releases must not change ledger_digest per release-ledger-contract idempotency rules."""
        session.run_full("publish-repeat-seal")
        first = session.read_ledger()["ledger_digest"]
        session.seal_releases("publish-repeat-seal")
        second = session.read_ledger()["ledger_digest"]
        assert first == second

    def test_screening_pass_counter(self, session: HemotherapySession) -> None:
        """score-compatibility must increment screening_pass in /app/state/screening-pass.json."""
        session.run_full("abo-clean-release")
        assert json.loads(PATHS.screening_json.read_text(encoding="utf-8"))["screening_pass"] == 1

    def test_release_db_path(self) -> None:
        """import-panels and seal-releases must use /app/state/release.db as the SQLite state store."""
        assert PATHS.release_db.as_posix() == "/app/state/release.db"

    def test_screening_json_location(self) -> None:
        """score-compatibility must write screening_pass to /app/state/screening-pass.json."""
        assert PATHS.screening_json.as_posix() == "/app/state/screening-pass.json"

    def test_publish_blocked_without_screening(self, session: HemotherapySession) -> None:
        """seal-releases must fail when screening_pass is zero per serology-matrix-contract."""
        session.import_panels("abo-clean-release")
        proc = session.shell([str(PATHS.binary), "seal-releases", "--scenario", "abo-clean-release"])
        assert proc.returncode != 0
        assert not PATHS.ledger_json.exists()

    def test_matrix_jsonl_written(self, session: HemotherapySession) -> None:
        """score-compatibility must emit compatibility-matrix JSONL under /app/work/compatibility-matrix."""
        session.import_panels("abo-clean-release")
        session.score_compatibility("abo-clean-release")
        stage = PATHS.workspace / "work" / "compatibility-matrix" / "abo-clean-release.jsonl"
        assert stage.is_file()

    def test_crossmatch_table_matches_spec(self, session: HemotherapySession) -> None:
        """crossmatch_rows in release.db must match independent reference_crossmatch expectations."""
        session.import_panels("rh-negative-guard")
        session.score_compatibility("rh-negative-guard")
        con = sqlite3.connect(PATHS.release_db)
        try:
            rows = con.execute(
                "SELECT patient_id, unit_id, compatible FROM crossmatch_rows ORDER BY patient_id, unit_id"
            ).fetchall()
        finally:
            con.close()
        spec = reference_crossmatch("rh-negative-guard", PATHS.fixture_root)
        for (pid, uid, compat), expected in zip(rows, spec):
            assert pid == expected["patient_id"]
            assert uid == expected["unit_id"]
            assert bool(compat) == expected["compatible"]

    def test_default_ledger_output_path(self) -> None:
        """seal-releases must write /app/output/release-ledger.json per release-ledger-contract."""
        expected = "/app/output/release-ledger.json"
        assert PATHS.ledger_json.as_posix() == expected

    def test_release_sort_order(self, session: HemotherapySession) -> None:
        """Release rows must sort by patient_id then unit_id per release-ledger-contract."""
        session.run_full("ab-recipient-broad")
        releases = session.read_ledger()["releases"]
        keys = [(r["patient_id"], r["unit_id"]) for r in releases]
        assert keys == sorted(keys)
