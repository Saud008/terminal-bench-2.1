"""Telemetry buffer and probe grid tests for kilnbal."""

from __future__ import annotations

import json
import random

import pytest

from kiln_balance_verifier import (
    celsius_from_probe,
    load_fuel_rows,
    load_telemetry_rows,
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


def test_tele_buffer_path_under_state():
    """load-probes writes JSONL under tele-buffer; staging snapshot artifact per tele-buffer-schema.md."""
    run_id = "stage-path"
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
    path = APP / "state" / "tele-buffer" / f"{run_id}.jsonl"
    assert str(path).startswith("/app/state/tele-buffer/")
    assert path.is_file()


def test_kelvin_normalization_in_buffer():
    """Kelvin probes normalize to Celsius in buffer before calibration per therm-unit-contract.md."""
    run_id = "stage-kelvin"
    root = scenario_path("kiln-run-01")
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
    row = json.loads((APP / "state" / "tele-buffer" / f"{run_id}.jsonl").read_text().splitlines()[1])
    tele = load_telemetry_rows(root / "telemetry.csv")[0]
    assert abs(row["temp_norm_c"] - celsius_from_probe(tele["temp_raw"], tele["unit"])) < 0.02


def test_fuel_buffer_energy_field():
    """bind-fuel stores energy_mj using kcal_to_mj factor from kilnbal.json config."""
    run_id = "bind-fuel-energy"
    root = scenario_path("kiln-run-01")
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
            "--kiln-id",
            "KILN-Alpha",
        ]
    )
    doc = json.loads((APP / "work" / "fuel-buffer" / f"{run_id}.json").read_text(encoding="utf-8"))
    ref = load_fuel_rows(root / "fuel.csv")[0]
    assert abs(doc["fuel_batches"][0]["energy_mj"] - ref["energy_mj"]) < 0.5


def test_probe_grid_batch_lineage_inclusive():
    """interpolate-probes maps batch_id with inclusive start_ts/end_ts lineage windows."""
    run_id = "grid-lineage"
    root = scenario_path("kiln-run-01")
    expect = reference_probe_timeline(load_telemetry_rows(root / "telemetry.csv"), load_fuel_rows(root / "fuel.csv"))
    drive_full_kiln_run(run_id, "kiln-run-01")
    grid = json.loads((APP / "work" / "probe-grid" / f"{run_id}.json").read_text(encoding="utf-8"))
    for exp, got in zip(expect, grid):
        assert got["batch_id"] == exp["batch_id"]


def test_probe_grid_interpolation_flags():
    """Missing grid probe_tss mark interpolated true per probe-gap-interpolation.md."""
    run_id = "grid-interp"
    root = scenario_path("kiln-run-01")
    expect = reference_probe_timeline(load_telemetry_rows(root / "telemetry.csv"), load_fuel_rows(root / "fuel.csv"))
    drive_full_kiln_run(run_id, "kiln-run-01")
    grid = json.loads((APP / "work" / "probe-grid" / f"{run_id}.json").read_text(encoding="utf-8"))
    for exp, got in zip(expect, grid):
        assert got["interpolated"] == exp["interpolated"]


def test_probe_grid_calibrated_temperature():
    """Calibrated temp_c on probe grid matches independent subtract-offset reference math."""
    run_id = "grid-temp"
    root = scenario_path("kiln-run-01")
    expect = reference_probe_timeline(load_telemetry_rows(root / "telemetry.csv"), load_fuel_rows(root / "fuel.csv"))
    drive_full_kiln_run(run_id, "kiln-run-01")
    grid = json.loads((APP / "work" / "probe-grid" / f"{run_id}.json").read_text(encoding="utf-8"))
    for exp, got in zip(expect, grid):
        assert abs(got["temp_c"] - exp["temp_c"]) < 0.05


def test_tb3_fixture_root_hidden_scenario():
    """TB3_FIXTURE_ROOT loads hidden kiln bundle for verifier-only cal-table scenario."""
    run_id = "grid-tb3-root"
    env = {"TB3_FIXTURE_ROOT": "/opt/verifier-fixtures/kilnbal/kiln-runs"}
    root = scenario_path("tb3-cal-offset", env)
    probes = reference_probe_timeline(
        load_telemetry_rows(root / "telemetry.csv"),
        load_fuel_rows(root / "fuel.csv"),
        {"HX1": 1.5},
    )
    ledger = json.loads(
        drive_full_kiln_run(
            run_id,
            "tb3-cal-offset",
            env=env,
            cal_table=str(root / "cal_table.csv"),
        ).read_text(encoding="utf-8")
    )
    assert ledger["kiln_id"] == "KILN-TB3"
    assert ledger["lineage_digest"] == reference_lineage_digest(probes)


def test_tb3_cal_table_env_variable():
    """TB3_CAL_TABLE env applies calibration overrides when CLI --cal-table omitted."""
    run_id = "grid-tb3-env"
    env = {
        "TB3_FIXTURE_ROOT": "/opt/verifier-fixtures/kilnbal/kiln-runs",
        "TB3_CAL_TABLE": "/opt/verifier-fixtures/kilnbal/kiln-runs/tb3-cal-offset/cal_table.csv",
    }
    root = scenario_path("tb3-cal-offset", env)
    expect = reference_probe_timeline(
        load_telemetry_rows(root / "telemetry.csv"),
        load_fuel_rows(root / "fuel.csv"),
        {"HX1": 1.5},
    )
    drive_full_kiln_run(run_id, "tb3-cal-offset", env=env)
    grid = json.loads((APP / "work" / "probe-grid" / f"{run_id}.json").read_text(encoding="utf-8"))
    assert abs(grid[0]["temp_c"] - expect[0]["temp_c"]) < 0.05


def test_random_kelvin_telemetry_row():
    """Random Kelvin telemetry rows anti-hardcode unit conversion without fixture-specific constants."""
    rng = random.Random(88001)
    k_val = rng.uniform(820, 1180)
    run_id = "stage-rand-k"
    tele = APP / "work" / "rand-k.csv"
    tele.write_text(
        f"probe_id,probe_ts,temp_raw,unit,cal_offset_c\nRK,{5000},{k_val:.4f},K,0.6\n",
        encoding="utf-8",
    )
    shell([str(KILNBAL), "load-probes", "--run-id", run_id, "--telemetry", str(tele)])
    row = json.loads((APP / "state" / "tele-buffer" / f"{run_id}.jsonl").read_text().splitlines()[1])
    assert abs(row["temp_norm_c"] - (k_val - 273.15)) < 0.02


def test_random_probe_ts_grid_interpolation():
    """Randomized probe probe_tss still produce interpolated grid rows on grid_step_sec cadence."""
    rng = random.Random(55221)
    t0 = rng.randint(11000, 22000)
    t1 = t0 + 600
    run_id = "grid-rand-ts"
    tele = APP / "work" / "rand-ts.csv"
    tele.write_text(
        f"probe_id,probe_ts,temp_raw,unit,cal_offset_c\nTG,{t0},910.0,C,0.3\nTG,{t1},915.0,C,0.3\n",
        encoding="utf-8",
    )
    fuel = APP / "work" / "rand-ts-fuel.csv"
    fuel.write_text(
        f"batch_id,fuel_name,mass_kg,cv_kcal_kg,start_ts,end_ts\nBF,{rng.choice(['Coal','RDF','Tyre'])},3000,8100,{t0-50},{t1+50}\n",
        encoding="utf-8",
    )
    clinker = APP / "work" / "rand-ts-clinker.csv"
    clinker.write_text(f"window_id,batch_id,clinker_t,start_ts,end_ts\nWF,BF,44.0,{t0-50},{t1+50}\n", encoding="utf-8")
    shell([str(KILNBAL), "load-probes", "--run-id", run_id, "--telemetry", str(tele)])
    shell(
        [
            str(KILNBAL),
            "bind-fuel",
            "--run-id",
            run_id,
            "--fuel",
            str(fuel),
            "--clinker",
            str(clinker),
        ]
    )
    shell([str(KILNBAL), "interpolate-probes", "--run-id", run_id])
    grid = json.loads((APP / "work" / "probe-grid" / f"{run_id}.json").read_text(encoding="utf-8"))
    assert any(row["interpolated"] for row in grid)


def test_reset_workspace_clears_buffer():
    """reset-workspace.sh clears telemetry buffer before cross-run verifier isolation."""
    run_id = "grid-reset"
    drive_full_kiln_run(run_id, "kiln-run-01")
    buffer = APP / "state" / "tele-buffer" / f"{run_id}.jsonl"
    assert buffer.is_file()
    reset_workspace()
    assert not buffer.exists()
