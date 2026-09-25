"""Source-level guards over the documented /app/lib/boltlane module tree.

Hot-path modules inspected here are documented in instruction.md under
"Hot-path module layout": fleet_intake/collect_fleet_snapshot.sh,
eligibility_engine/compose_reconnect_ledger.sh, and
atlas_emit/publish_rollout_atlas.sh.
"""

from __future__ import annotations

from pathlib import Path

LIB = Path("/app/lib/boltlane")


def test_unused_mac_formatter_is_never_sourced_by_any_hot_path_stage() -> None:
    """decoy/stale_mac_formatter.sh must not be referenced by scan, compile, or publish."""
    scan_src = (LIB / "fleet_intake" / "collect_fleet_snapshot.sh").read_text()
    compile_src = (LIB / "eligibility_engine" / "compose_reconnect_ledger.sh").read_text()
    publish_src = (LIB / "atlas_emit" / "publish_rollout_atlas.sh").read_text()
    for src in (scan_src, compile_src, publish_src):
        assert "stale_mac_formatter" not in src
        assert "decoy/" not in src


def test_all_five_gate_modules_exist_under_the_documented_gates_directory() -> None:
    """pairing, resume, power, storm, and gatt gates must each exist under lib/boltlane/gates."""
    gates_dir = LIB / "gates"
    for name in (
        "pairing_drift_gate.sh",
        "resume_slot_gate.sh",
        "power_sequence_gate.sh",
        "reconnect_storm_gate.sh",
        "gatt_service_catalog.sh",
    ):
        assert (gates_dir / name).is_file(), name


def test_eligibility_engine_never_re_reads_fixture_scenarios_directly() -> None:
    """compose_reconnect_ledger.sh must derive eligibility from state, not fixtures/scenarios."""
    compile_src = (LIB / "eligibility_engine" / "compose_reconnect_ledger.sh").read_text()
    assert "fixtures/scenarios" not in compile_src
    assert "/app/state/inventory.json" in compile_src
