"""Dose ledger staging artifact persistence across load-shift-dose runs."""

from __future__ import annotations

import json

from wtcda_refmath import revision_token as reference_revision_token
from wtcda_subprocess import CLI_BIN, ledger_path, invoke, wipe


def test_wtcda_p25() -> None:
    """load-shift-dose leaves dose ledger on disk until reset-workspace.sh clears it."""
    wipe()
    plant, shift = "plant-east-gamma", "outage-forward-fill"
    invoke([str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", shift])
    assert ledger_path(plant).is_file()
    body = json.loads(ledger_path(plant).read_text(encoding="utf-8"))
    token = reference_revision_token(plant, shift, body["as_of"])
    assert body["ledger_revision_token"] == token
    invoke([str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", shift])
    body2 = json.loads(ledger_path(plant).read_text(encoding="utf-8"))
    assert body2["ledger_revision_token"] == token


def test_wtcda_p26() -> None:
    """Re-ingest with a new shift name updates ledger shift field."""
    wipe()
    plant = "plant-central-zeta"
    invoke([str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", "percent-unit-lot"])
    invoke(
        [
            str(CLI_BIN),
            "load-shift-dose",
            "--plant",
            "plant-north-alpha",
            "--shift",
            "dual-chem-basic",
        ]
    )
    body = json.loads(ledger_path("plant-north-alpha").read_text(encoding="utf-8"))
    assert body["shift"] == "dual-chem-basic"


def test_wtcda_p27() -> None:
    """reset-workspace.sh removes staged dose ledger artifacts."""
    wipe()
    plant = "plant-north-alpha"
    invoke([str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", "dual-chem-basic"])
    assert ledger_path(plant).exists()
    wipe()
    assert not ledger_path(plant).exists()
