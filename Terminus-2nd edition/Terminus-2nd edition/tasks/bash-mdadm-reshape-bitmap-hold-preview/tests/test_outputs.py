"""End-to-end atlas checks for the basic-reshape fleet fixture."""

from __future__ import annotations

import subprocess
from pathlib import Path

from mdreshape_harness import scan_compile_publish, reset_state
from mdreshape_mathlib import audit_digest, load_scenario, reference_evaluate


def test_tdb522a_mdreshape_binary_linked_under_bin() -> None:
    """Fleet reshape preview CLI binary must be installed at /app/bin/mdreshape."""
    assert Path("/app/bin/mdreshape").is_file()
    proc = subprocess.run(["/app/bin/mdreshape"], capture_output=True, text=True)
    assert proc.returncode != 0


def test_tdb522a_mdreshape_basic_raid_eligibility_matches_oracle() -> None:
    """Eligibility atlas for basic-reshape must match independent host math."""
    reset_state()
    atlas = scan_compile_publish(
        "basic-reshape",
        "t-basic",
        output="/app/output/mdreshape_eligibility_atlas.json",
    )
    assert Path("/app/state/reshape-ledger.json").is_file()
    assert Path("/app/state/run-meta.json").is_file()
    assert Path("/app/output/mdreshape_eligibility_atlas.json").is_file()
    inv = load_scenario(Path("/app/fixtures/scenarios/basic-reshape/inventory.json"))
    ref = reference_evaluate(inv)
    assert atlas["eligible_count"] == ref["eligible_count"]
    assert atlas["blocked_count"] == ref["blocked_count"]
    assert {r["name"] for r in atlas["eligible"]} == {r["name"] for r in ref["eligible"]}
    assert atlas["audit_digest"] == audit_digest(
        "t-basic", "basic-reshape", ref["eligible"], ref["blocked"]
    )
    assert atlas["schema_version"] == 1
    assert "md0" in {r["name"] for r in atlas["eligible"]}


def test_tdb522a_mdreshape_slot_lex_helper_absent_from_hot_path() -> None:
    """slot_name_lex_helper decoy must never be sourced by compile or publish scripts."""
    internal = Path("/app/internal")
    hot_sources = [
        path.read_text()
        for path in internal.rglob("*.sh")
        if "decoy" not in path.parts
    ]
    assert hot_sources
    for src in hot_sources:
        assert "slot_name_lex_helper" not in src
