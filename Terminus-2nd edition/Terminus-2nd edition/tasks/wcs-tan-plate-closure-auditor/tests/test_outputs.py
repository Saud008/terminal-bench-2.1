"""Bundled plate laboratory scenarios for platclosectl.

Covers hydrate-plates ingest journal priming, residual-matrix buffer snapshots, and
seal-closure certificate export layers.
"""

from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest
from closure_spec import reference_certificate
from plate_session import BIN, FIXTURES, WORK, bind_pass, cert, reset, run, run_full

BIND_PASS_PATH = "/app/state/bind-pass.json"
PLATE_DB_PATH = "/app/state/plate-closure.db"


@pytest.fixture(autouse=True)
def _clean() -> None:
    reset()


class TestCLISurface:
    def test_usage_lists_laboratory_verbs(self) -> None:
        """Missing verb must exit 2 and mention hydrate-plates bind-residuals seal-closure."""
        proc = subprocess.run([str(BIN)], capture_output=True, text=True, check=False)
        assert proc.returncode == 2
        err = proc.stderr
        assert "hydrate-plates" in err
        assert "bind-residuals" in err
        assert "seal-closure" in err


class TestHydrateJournal:
    def test_hydrate_writes_sqlite_event(self) -> None:
        """hydrate-plates must journal the scenario into plate-closure.db."""
        assert run("hydrate-plates", "plate-tight-tan").returncode == 0
        con = sqlite3.connect(PLATE_DB_PATH)
        try:
            row = con.execute(
                "SELECT scenario, verb FROM lab_events ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
        finally:
            con.close()
        assert row == ("plate-tight-tan", "hydrate-plates")


class TestBundledClosures:
    @pytest.mark.parametrize(
        "scenario",
        [
            "plate-tight-tan",
            "plate-mask-exclude",
            "plate-epoch-nudge",
            "plate-loose-rms",
            "plate-multi-star",
            "plate-repeat-seal",
        ],
    )
    def test_certificate_matches_reference(self, scenario: str) -> None:
        """Full hydrate/bind/seal must match independent closure_spec certificate."""
        run_full(scenario)
        got = cert(scenario)
        exp = reference_certificate(FIXTURES / f"{scenario}.json")
        assert got == exp
        assert (WORK / "residual-matrix" / f"{scenario}.jsonl").is_file()
        assert bind_pass() >= 1

    def test_bind_pass_json_advances(self) -> None:
        """bind-residuals must set bind_pass > 0 in bind-pass.json."""
        assert run("hydrate-plates", "plate-tight-tan").returncode == 0
        assert bind_pass() == 0
        assert run("bind-residuals", "plate-tight-tan").returncode == 0
        assert bind_pass() >= 1
        assert Path(BIND_PASS_PATH).is_file()

    def test_mask_excludes_det_bit(self) -> None:
        """det_mask bit 0x04 stars must leave the active certificate set."""
        run_full("plate-mask-exclude")
        assert cert("plate-mask-exclude")["stars"] == ["S01", "S03"]

    def test_loose_class_when_rms_high(self) -> None:
        """closure_class must be loose when either RMS is at least 0.35."""
        run_full("plate-loose-rms")
        body = cert("plate-loose-rms")
        assert body["closure_class"] == "loose"
        assert body["rms_ra_arcsec"] >= 0.35 or body["rms_dec_arcsec"] >= 0.35
