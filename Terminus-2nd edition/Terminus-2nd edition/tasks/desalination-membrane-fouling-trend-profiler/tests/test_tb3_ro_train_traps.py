"""Hidden fixture traps for rotrace TB3 fouling probes."""

from __future__ import annotations

import json

from brine_ndp_contract import (
    apply_cal_table,
    load_batches,
    load_cleaning_csv,
    load_readings_csv,
    contract_chronicle,
)
from swro_pipeline_driver import HIDDEN, LOCAL_HIDDEN, run_swro_fouling_pipeline, scenario_path


def test_tb3_salinity_offset_hidden_cal_table(isolated_swro_profiler):
    """TB3 salinity calibration overlay must shift NDP rows per salinity-calibration-offset.md."""
    run_id = "tb3-cal-offset"
    root = scenario_path("tb3-salinity-offset", {"TB3_FIXTURE_ROOT": str(HIDDEN.parent)})
    meta = json.loads((root / "train.meta.json").read_text(encoding="utf-8"))
    cal = str(root / "cal_table.csv")
    got = json.loads(
        run_swro_fouling_pipeline(
            run_id,
            "tb3-salinity-offset",
            env={"TB3_FIXTURE_ROOT": str(HIDDEN.parent)},
            cal_table=cal,
        ).read_text(encoding="utf-8")
    )
    exp = contract_chronicle(
        run_id,
        meta["train_id"],
        apply_cal_table(load_readings_csv(root / "readings.csv"), root / "cal_table.csv"),
        load_batches(root / "membrane_batches.json"),
        load_cleaning_csv(root / "cleaning.csv"),
    )
    assert got["chronicle_rows"] == exp["chronicle_rows"]


def test_tb3_dropout_poison_local_hidden(isolated_swro_profiler):
    """Local tb3-dropout-poison trap verifies sensor dropout bridge independent of bundled fixtures."""
    run_id = "tb3-poison"
    root = LOCAL_HIDDEN / "tb3-dropout-poison"
    meta = json.loads((root / "train.meta.json").read_text(encoding="utf-8"))
    got = json.loads(
        run_swro_fouling_pipeline(
            run_id,
            "tb3-dropout-poison",
            env={"TB3_FIXTURE_ROOT": str(LOCAL_HIDDEN)},
        ).read_text(encoding="utf-8")
    )
    exp = contract_chronicle(
        run_id,
        meta["train_id"],
        load_readings_csv(root / "readings.csv"),
        load_batches(root / "membrane_batches.json"),
        load_cleaning_csv(root / "cleaning.csv"),
    )
    assert got["chronicle_rows"] == exp["chronicle_rows"]


def test_tb3_hidden_fixture_root_env_propagates(isolated_swro_profiler):
    """TB3_FIXTURE_ROOT must redirect bundled train loading to verifier fixture root."""
    run_id = "tb3-root-env"
    out = run_swro_fouling_pipeline(
        run_id,
        "tb3-salinity-offset",
        env={"TB3_FIXTURE_ROOT": str(HIDDEN.parent)},
        cal_table=str(scenario_path("tb3-salinity-offset", {"TB3_FIXTURE_ROOT": str(HIDDEN.parent)}) / "cal_table.csv"),
    )
    assert out.exists()
