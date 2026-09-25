"""Contract tests for custody reference helpers."""
from __future__ import annotations

import json
from pathlib import Path

from custody_verifier_math import (
    alias_findings,
    build_edges,
    chrono_findings,
    lineage_gap,
    load_locations,
    seal_findings,
)

FIX = Path("/app/fixtures/cases")
CAT = Path("/app/catalog/storage-locations.json")


def test_seal_break_on_transfer_mismatch() -> None:
    """Verify reference seal_findings flags transfer row seal mismatch."""
    bundle = json.loads((FIX / "seal-break-trap.json").read_text(encoding="utf-8"))
    rows = bundle["transfers"]
    findings = seal_findings(rows)
    assert len(findings) == 1
    assert findings[0]["code"] == "seal_break"


def test_lineage_edges_order_by_epoch() -> None:
    """Verify reference build_edges sorts by event_epoch_ms within evidence."""
    bundle = json.loads((FIX / "metro-gun-chain.json").read_text(encoding="utf-8"))
    edges = build_edges(bundle["transfers"])
    assert len(edges) == 2
    assert edges[0]["event_epoch_ms"] < edges[1]["event_epoch_ms"]


def test_lineage_gap_detects_officer_discontinuity() -> None:
    """Verify reference lineage_gap detects missing intermediate officer."""
    bundle = json.loads((FIX / "lineage-gap-trap.json").read_text(encoding="utf-8"))
    assert lineage_gap("EVD-E301", bundle["transfers"]) is True


def test_alias_collision_pair_detected() -> None:
    """Verify reference alias_findings detects duplicate court_alias."""
    bundle = json.loads((FIX / "alias-collision-trap.json").read_text(encoding="utf-8"))
    findings = alias_findings(bundle["exhibit_aliases"])
    assert any(f["code"] == "alias_collision" for f in findings)


def test_chrono_equal_epoch_is_violation() -> None:
    """Verify equal event_epoch_ms values emit chronology_violation."""
    rows = [
        {
            "evidence_id": "EVD-X",
            "event_epoch_ms": 100,
            "event_id": "a",
            "event_type": "transfer",
        },
        {
            "evidence_id": "EVD-X",
            "event_epoch_ms": 100,
            "event_id": "b",
            "event_type": "transfer",
        },
    ]
    assert len(chrono_findings(rows)) == 1


def test_location_catalog_loads_active_status() -> None:
    """Verify location catalog exposes active status for secure vault."""
    catalog = load_locations(CAT)
    assert catalog["LOC-SECURE-VAULT-3"] == "active"
