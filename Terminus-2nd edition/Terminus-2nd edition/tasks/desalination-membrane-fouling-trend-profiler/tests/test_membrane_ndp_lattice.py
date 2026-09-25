"""NDP grid and trend scratch artifact tests for rotrace."""

from __future__ import annotations

import json

from swro_pipeline_driver import APP, ROTRACE, scenario_path, invoke_rotrace_cli as shell


def test_ndp_grid_created_after_normalize(isolated_swro_profiler):
    """normalize-ndp must emit hourly NDP lattice JSON at /app/work/ndp-grid/<run-id>.json."""
    run_id = "buf-ndp-grid"
    root = scenario_path("ro-train-alpha")
    meta = json.loads((root / "train.meta.json").read_text(encoding="utf-8"))
    shell([str(ROTRACE), "load-readings", "--run-id", run_id, "--stream", str(root / "readings.csv")])
    shell(
        [
            str(ROTRACE),
            "bind-cleaning",
            "--run-id",
            run_id,
            "--events",
            str(root / "cleaning.csv"),
            "--membrane",
            str(root / "membrane_batches.json"),
            "--train-id",
            meta["train_id"],
        ]
    )
    shell([str(ROTRACE), "normalize-ndp", "--run-id", run_id])
    path = APP / "work" / "ndp-grid" / f"{run_id}.json"
    assert path.is_file()
    grid = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(grid, list)
    assert grid[0]["ndp"] is not None


def test_trend_scratch_created_after_score(isolated_swro_profiler):
    """score-trends must write trend scratch rows before publish-chronicle can succeed."""
    run_id = "buf-trend"
    root = scenario_path("ro-train-echo")
    meta = json.loads((root / "train.meta.json").read_text(encoding="utf-8"))
    shell([str(ROTRACE), "load-readings", "--run-id", run_id, "--stream", str(root / "readings.csv")])
    shell(
        [
            str(ROTRACE),
            "bind-cleaning",
            "--run-id",
            run_id,
            "--events",
            str(root / "cleaning.csv"),
            "--membrane",
            str(root / "membrane_batches.json"),
            "--train-id",
            meta["train_id"],
        ]
    )
    shell([str(ROTRACE), "normalize-ndp", "--run-id", run_id])
    shell([str(ROTRACE), "score-trends", "--run-id", run_id])
    scratch = json.loads((APP / "work" / "trend-scratch" / f"{run_id}.json").read_text(encoding="utf-8"))
    assert scratch["rows"]


def test_ndp_grid_rows_include_batch_and_hour_keys(isolated_swro_profiler):
    """ndp-grid-schema.md requires hour_index, batch_id, and ndp on every grid row."""
    run_id = "buf-ndp-keys"
    root = scenario_path("ro-train-charlie")
    meta = json.loads((root / "train.meta.json").read_text(encoding="utf-8"))
    shell([str(ROTRACE), "load-readings", "--run-id", run_id, "--stream", str(root / "readings.csv")])
    shell(
        [
            str(ROTRACE),
            "bind-cleaning",
            "--run-id",
            run_id,
            "--events",
            str(root / "cleaning.csv"),
            "--membrane",
            str(root / "membrane_batches.json"),
            "--train-id",
            meta["train_id"],
        ]
    )
    shell([str(ROTRACE), "normalize-ndp", "--run-id", run_id])
    grid = json.loads((APP / "work" / "ndp-grid" / f"{run_id}.json").read_text(encoding="utf-8"))
    assert {"hour_index", "batch_id", "ndp"}.issubset(grid[0].keys())
