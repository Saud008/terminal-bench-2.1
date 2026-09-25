"""Primary pytest entry — yard ingest, dwell ledger staging snapshot, invoice export publish."""

import subprocess  # noqa: F401 — subprocess CLI contract

from demur_refmath import reference_invoices, reference_ledger_digest  # noqa: F401

import test_demur_output_paths
import test_demur_stage_gates


def test_demur_daemon_blocks_early_invoice_export() -> None:
    """Daemon clock_pass gate blocks demurrage invoice publish before dwell ledger completes."""
    test_demur_stage_gates.test_demur_S03_publish_blocked_before_staging()


def test_demur_yard_topology_staging_manifest() -> None:
    """Yard topology manifest captures dwell-ledger digest after dwell daemon runs."""
    test_demur_output_paths.test_demur_O02_staging_json_exists()


def test_demur_host_config_persists_yard_db() -> None:
    """Host config tables persist gate events and tariff rows inside yard.db."""
    test_demur_output_paths.test_demur_O01_load_yard_paths()


def test_demur_tariff_invoice_manifest_matches_ref() -> None:
    """Demurrage invoice manifest lines match independent tier-bucket reference math."""
    test_demur_stage_gates.test_demur_S06_basic_free_time_invoices()
