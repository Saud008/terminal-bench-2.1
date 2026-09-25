"""Rank ledger staging probes for calloutd."""

from __future__ import annotations

import json
from pathlib import Path

from callout_pipeline import FIXTURE_ROOT, invoke, wipe_state


def test_calloutd_rank_ledger_written_after_rank_faults() -> None:
    """rank-faults must emit /app/work/rank-ledger.json staging artifact."""
    wipe_state()
    invoke(["load-roster", "--scenario", "clean-dispatch", "--fixture-dir", str(FIXTURE_ROOT)])
    proc = invoke(["rank-faults", "--scenario", "clean-dispatch"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    ledger = json.loads(Path("/app/work/rank-ledger.json").read_text(encoding="utf-8"))
    assert "ranked" in ledger
    assert len(ledger["ranked"]) == 1


def test_calloutd_rank_ledger_priority_matches_snapshot() -> None:
    """rank-ledger priority_score must match score-snapshot row."""
    wipe_state()
    invoke(["load-roster", "--scenario", "trapped-escalation", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke(["rank-faults", "--scenario", "trapped-escalation"])
    snap = json.loads(Path("/app/work/urgency-snapshot.json").read_text(encoding="utf-8"))
    ledger = json.loads(Path("/app/work/rank-ledger.json").read_text(encoding="utf-8"))
    assert ledger["ranked"][0]["priority_score"] == snap["faults"][0]["priority_score"]


def test_calloutd_urgency_snapshot_written_with_rank_ledger() -> None:
    """rank-faults must write /app/work/urgency-snapshot.json alongside rank-ledger."""
    wipe_state()
    invoke(["load-roster", "--scenario", "clean-dispatch", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke(["rank-faults", "--scenario", "clean-dispatch"])
    assert Path("/app/work/urgency-snapshot.json").is_file()
    assert Path("/app/work/rank-ledger.json").is_file()
