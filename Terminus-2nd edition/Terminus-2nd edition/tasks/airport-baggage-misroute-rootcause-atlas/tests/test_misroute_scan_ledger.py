"""Scan ledger sequence tie-breaks and relay supersession."""

from __future__ import annotations

import json
from pathlib import Path

from baggage_oracle import parse_scan_stream, reference_dedupe_scans


def test_scan_ledger_snapshot_after_seq_scans(misroute_harness):
    """seq-scans lane writes scan ledger snapshot under /app/work/scan-ledger/."""
    hub_id = "hub-alpha"
    misroute_harness.full_pipeline(hub_id)
    ledger_path = "/app/work/scan-ledger/hub-alpha.jsonl"
    assert "scan-ledger" in ledger_path
    rows = misroute_harness.scan_rows(hub_id)
    assert len(rows) >= 1


def test_emit_rootcause_lane_writes_atlas(misroute_harness):
    """emit-rootcause lane publishes atlas JSON after route-belts lattice pass."""
    hub_id = "hub-alpha"
    out = misroute_harness.full_pipeline(hub_id)
    assert out.parent.name == "output"
    assert "rootcause-atlas" in out.name


def test_relay_pass_keeps_highest_duplicate_scan(misroute_harness):
    """duplicate scan_seq supersession keeps max relay_pass per scan-sequence-contract.md."""
    hub_id = "hub-delta"
    misroute_harness.full_pipeline(hub_id)
    rows = misroute_harness.scan_rows(hub_id)
    assert len(rows) == 1
    assert rows[0]["relay_pass"] == 2


def test_equal_minute_rows_sorted_by_scan_seq(misroute_harness):
    """scan_minute tie-break uses ascending scan_seq per scan-sequence-contract.md."""
    hub_id = "hub-epsilon"
    stream = misroute_harness.hub_dir(hub_id) / "scans.jsonl"
    expected = reference_dedupe_scans(parse_scan_stream(stream))
    misroute_harness.full_pipeline(hub_id)
    ledger_rows = misroute_harness.scan_rows(hub_id)
    assert [(r["scan_minute"], r["scan_seq"]) for r in ledger_rows] == [
        (r["scan_minute"], r["scan_seq"]) for r in expected
    ]


def test_scan_ledger_header_carries_topology_revision(misroute_harness):
    """scan-ledger header records topology_revision from hub latch."""
    hub_id = "hub-alpha"
    misroute_harness.full_pipeline(hub_id)
    raw = Path("/app/work/scan-ledger/hub-alpha.jsonl").read_text(encoding="utf-8").splitlines()[0]
    header = json.loads(raw)
    latch = misroute_harness.latch_doc(hub_id)
    assert header["topology_revision"] == latch["topology_revision"]
