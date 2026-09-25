"""Heat balance ledger contract tests for kilnbal."""

from __future__ import annotations

import json
import random

import pytest

from kiln_balance_verifier import (
    load_clinker_rows,
    load_fuel_rows,
    load_telemetry_rows,
    reference_audit_digest,
    reference_heat_balance,
    reference_lineage_digest,
    reference_probe_timeline,
)
from kiln_cli_runner import APP, KILNBAL, drive_full_kiln_run, reset_workspace, scenario_path, shell

pytestmark = pytest.mark.usefixtures("kiln_clean")


@pytest.fixture
def kiln_clean():
    reset_workspace()
    yield
    reset_workspace()


def test_binary_installed_under_app_bin():
    """kilnbal must be installed at /app/bin/kilnbal per workflow contract."""
    assert KILNBAL.is_file()


def test_ledger_filename_suffix_contract():
    """publish-ledger publishs heat balance JSON under /app/output/ with -heat-balance-ledger.json suffix."""
    run_id = "ledger-suffix"
    out = drive_full_kiln_run(run_id, "kiln-run-01")
    assert str(out).startswith("/app/output/")
    assert out.name.endswith("-heat-balance-ledger.json")


def test_kiln_id_from_meta_propagates():
    """bind-fuel --kiln-id from scenario meta appears in final heat balance ledger."""
    run_id = "ledger-kiln-id"
    ledger = json.loads(drive_full_kiln_run(run_id, "kiln-run-01").read_text(encoding="utf-8"))
    assert ledger["kiln_id"] == "KILN-Alpha"


def test_energy_in_matches_reference_fuel_sum():
    """Ledger residual fields match independent heat-balance-residual.md reference math."""
    run_id = "ledger-energy"
    root = scenario_path("kiln-run-02")
    fuels = load_fuel_rows(root / "fuel.csv")
    clinker = load_clinker_rows(root / "clinker.csv")
    heat = json.loads((root / "heat_loss.json").read_text())["heat_loss_mj"]
    expect = reference_heat_balance(fuels, clinker, heat)
    ledger = json.loads(drive_full_kiln_run(run_id, "kiln-run-02").read_text(encoding="utf-8"))
    assert abs(ledger["energy_in_mj"] - expect["energy_in_mj"]) < 1.0
    assert abs(ledger["residual_mj"] - expect["residual_mj"]) < 1.0


def test_multi_fuel_batch_count_kiln_run_03():
    """Heat ledger lists every fuel batch staged for multi-fuel kiln-run-03 scenario."""
    run_id = "ledger-multi-fuel"
    ledger = json.loads(drive_full_kiln_run(run_id, "kiln-run-03").read_text(encoding="utf-8"))
    assert len(ledger["fuel_batches"]) == 2


def test_clinker_tonnage_sum_matches_windows():
    """clinker_out_t equals sum of clinker window tonnes from staged CSV inputs."""
    run_id = "ledger-clinker-sum"
    root = scenario_path("kiln-run-03")
    expect_t = sum(r["clinker_t"] for r in load_clinker_rows(root / "clinker.csv"))
    ledger = json.loads(drive_full_kiln_run(run_id, "kiln-run-03").read_text(encoding="utf-8"))
    assert abs(ledger["clinker_out_t"] - expect_t) < 0.01


def test_audit_digest_matches_reference_hash():
    """audit_digest SHA256 matches heat-ledger-fields.md sorted JSON body."""
    run_id = "ledger-audit"
    root = scenario_path("kiln-run-01")
    tele = load_telemetry_rows(root / "telemetry.csv")
    fuels = load_fuel_rows(root / "fuel.csv")
    probes = reference_probe_timeline(tele, fuels)
    ledger = json.loads(drive_full_kiln_run(run_id, "kiln-run-01").read_text(encoding="utf-8"))
    ledger["lineage_digest"] = reference_lineage_digest(probes)
    assert ledger["audit_digest"] == reference_audit_digest(ledger)


def test_lineage_digest_sorted_pairs():
    """lineage_digest hashes sorted probe_ts:batch_id probe lineage pairs."""
    run_id = "ledger-lineage"
    root = scenario_path("kiln-run-02")
    probes = reference_probe_timeline(load_telemetry_rows(root / "telemetry.csv"), load_fuel_rows(root / "fuel.csv"))
    ledger = json.loads(drive_full_kiln_run(run_id, "kiln-run-02").read_text(encoding="utf-8"))
    assert ledger["lineage_digest"] == reference_lineage_digest(probes)


def test_probe_windows_sorted_probe_tss():
    """probe_windows array stays sorted by ascending probe_ts in emitted ledger."""
    run_id = "ledger-sort"
    ledger = json.loads(drive_full_kiln_run(run_id, "kiln-run-03").read_text(encoding="utf-8"))
    stamps = [row["probe_ts"] for row in ledger["probe_windows"]]
    assert stamps == sorted(stamps)


def test_partial_pipeline_cannot_publish():
    """Ingest-only partial fix without interpolate cannot export publish-ledger heat balance output."""
    run_id = "ledger-partial"
    root = scenario_path("kiln-run-02")
    shell(
        [
            str(KILNBAL),
            "load-probes",
            "--run-id",
            run_id,
            "--telemetry",
            str(root / "telemetry.csv"),
        ]
    )
    shell(
        [
            str(KILNBAL),
            "bind-fuel",
            "--run-id",
            run_id,
            "--fuel",
            str(root / "fuel.csv"),
            "--clinker",
            str(root / "clinker.csv"),
        ]
    )
    out = APP / "output" / f"{run_id}-heat-balance-ledger.json"
    proc = shell([str(KILNBAL), "publish-ledger", "--run-id", run_id, "--output", str(out)])
    assert proc.returncode != 0 or not out.is_file()


def test_randomized_fuel_label_energy():
    """Randomized fuel names and masses still stage without hard-coded fuel table lookups."""
    rng = random.Random(31415)
    mass = rng.uniform(1200, 8800)
    cv = rng.uniform(7100, 9800)
    label = f"Blend-{rng.randint(10, 99)}"
    run_id = "ledger-rand-fuel"
    fuel_csv = APP / "work" / "rand-fuel.csv"
    fuel_csv.write_text(
        f"batch_id,fuel_name,mass_kg,cv_kcal_kg,start_ts,end_ts\nRB,{label},{mass:.3f},{cv:.3f},100,900\n",
        encoding="utf-8",
    )
    root = scenario_path("kiln-run-02")
    shell(
        [
            str(KILNBAL),
            "load-probes",
            "--run-id",
            run_id,
            "--telemetry",
            str(root / "telemetry.csv"),
        ]
    )
    shell(
        [
            str(KILNBAL),
            "bind-fuel",
            "--run-id",
            run_id,
            "--fuel",
            str(fuel_csv),
            "--clinker",
            str(root / "clinker.csv"),
        ]
    )
    doc = json.loads((APP / "work" / "fuel-buffer" / f"{run_id}.json").read_text(encoding="utf-8"))
    assert doc["fuel_batches"][0]["fuel_name"] == label


def test_bundle_catalog_lists_three_runs():
    """fixture-bundle-catalog.md lists at least three bundled kiln run scenarios."""
    catalog = json.loads((APP / "fixtures" / "bundle_catalog.json").read_text(encoding="utf-8"))
    assert len(catalog["bundles"]) >= 3


def test_decoy_grade_subcommand_absent():
    """clinker grade decoy module is not exposed as a kilnbal CLI subcommand."""
    proc = shell([str(KILNBAL)])
    assert proc.returncode != 0
    assert "grade" not in (proc.stderr + proc.stdout).lower()
