"""Pressure and cleaning staging buffer tests for rotrace."""

from __future__ import annotations

import json

from swro_pipeline_driver import APP, ROTRACE, scenario_path, invoke_rotrace_cli as shell


def test_pressure_buffer_path_under_state(isolated_swro_profiler):
    """load-readings must write staged rows to /app/state/pressure-buffer/<run-id>.jsonl."""
    run_id = "buf-pressure"
    root = scenario_path("ro-train-alpha")
    shell(
        [
            str(ROTRACE),
            "load-readings",
            "--run-id",
            run_id,
            "--stream",
            str(root / "readings.csv"),
        ]
    )
    path = APP / "state" / "pressure-buffer" / f"{run_id}.jsonl"
    assert str(path).startswith("/app/state/pressure-buffer/")
    assert path.is_file()


def test_cleaning_buffer_written_after_bind(isolated_swro_profiler):
    """bind-cleaning must persist membrane batches and train_id under /app/work/cleaning-buffer/."""
    run_id = "buf-cleaning"
    root = scenario_path("ro-train-bravo")
    meta = json.loads((root / "train.meta.json").read_text(encoding="utf-8"))
    shell(
        [
            str(ROTRACE),
            "load-readings",
            "--run-id",
            run_id,
            "--stream",
            str(root / "readings.csv"),
        ]
    )
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
    doc = json.loads((APP / "work" / "cleaning-buffer" / f"{run_id}.json").read_text(encoding="utf-8"))
    assert doc["train_id"] == meta["train_id"]
    assert doc["batches"]


def test_pressure_buffer_jsonl_has_staged_reading_rows(isolated_swro_profiler):
    """pressure-buffer-schema.md requires one JSONL row per loaded sensor reading."""
    run_id = "buf-jsonl-rows"
    root = scenario_path("ro-train-delta")
    shell(
        [
            str(ROTRACE),
            "load-readings",
            "--run-id",
            run_id,
            "--stream",
            str(root / "readings.csv"),
        ]
    )
    lines = (APP / "state" / "pressure-buffer" / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2
