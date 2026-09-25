"""CLI dispatch contract: the load alias, unknown verbs, and required flag validation."""

from __future__ import annotations

import subprocess

from fleet_cutover_harness import CLI, load_json, wipe_run_state


def test_load_alias_produces_an_identical_inventory_snapshot_to_scan() -> None:
    """hciroll load must be a verbatim alias for hciroll scan."""
    wipe_run_state()
    subprocess.run(
        [str(CLI), "load", "--scenario", "basic-reconnect", "--run-id", "alias-check"],
        check=True,
        capture_output=True,
        text=True,
    )
    via_load = load_json("/app/state/inventory.json")

    wipe_run_state()
    subprocess.run(
        [str(CLI), "scan", "--scenario", "basic-reconnect", "--run-id", "alias-check"],
        check=True,
        capture_output=True,
        text=True,
    )
    via_scan = load_json("/app/state/inventory.json")

    assert via_load["fleet"] == via_scan["fleet"]
    assert via_load["adapters"] == via_scan["adapters"]


def test_unrecognized_subcommand_is_rejected() -> None:
    """An unknown verb must exit non-zero rather than silently no-op."""
    proc = subprocess.run(
        [str(CLI), "unroll", "--scenario", "basic-reconnect", "--run-id", "x"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_scan_rejects_a_scenario_name_with_no_matching_fixture() -> None:
    """A scenario directory that does not exist under fixtures must fail loudly."""
    wipe_run_state()
    proc = subprocess.run(
        [str(CLI), "scan", "--scenario", "does-not-exist", "--run-id", "missing-fixture"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_publish_omitting_output_flag_writes_the_documented_default_path() -> None:
    """publish without --output must fall back to the configured default_output path."""
    wipe_run_state()
    subprocess.run(
        [str(CLI), "scan", "--scenario", "basic-reconnect", "--run-id", "default-out"],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [str(CLI), "compile", "--run-id", "default-out"],
        check=True,
        capture_output=True,
        text=True,
    )
    proc = subprocess.run(
        [str(CLI), "publish", "--run-id", "default-out"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    default_atlas = load_json("/app/output/hci_reconnect_rollout_atlas.json")
    assert default_atlas["run_id"] == "default-out"


def test_compile_rejects_missing_run_id_flag() -> None:
    """compile invoked with no --run-id must fail the flag contract."""
    proc = subprocess.run([str(CLI), "compile"], capture_output=True, text=True)
    assert proc.returncode != 0
