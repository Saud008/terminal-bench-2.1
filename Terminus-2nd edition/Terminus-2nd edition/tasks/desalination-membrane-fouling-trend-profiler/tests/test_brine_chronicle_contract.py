"""Fouling trend chronicle contract tests for rotrace."""

from __future__ import annotations

import json
import random

import pytest

from brine_ndp_contract import (
    contract_chronicle,
    contract_lineage_digest,
    load_batches,
    load_cleaning_csv,
    load_readings_csv,
    severity_rank,
)
from swro_pipeline_driver import APP, ROTRACE, run_swro_fouling_pipeline, scenario_path, invoke_rotrace_cli as shell


class TestSwroChronicleManifest:
    def test_rotrace_binary_installed_under_app_bin(self, isolated_swro_profiler):
        """Instruction requires rotrace binary at /app/bin/rotrace after cargo build."""
        assert ROTRACE.is_file()

    def test_chronicle_filename_suffix_fouling_trend(self, isolated_swro_profiler):
        """publish-chronicle writes JSON under /app/output/ with -fouling-trend-chronicle.json suffix."""
        run_id = "chron-suffix"
        out = run_swro_fouling_pipeline(run_id, "ro-train-alpha")
        assert str(out).startswith("/app/output/")
        assert out.name.endswith("-fouling-trend-chronicle.json")

    def test_train_id_from_meta_propagates_to_chronicle(self, isolated_swro_profiler):
        """train.meta.json train_id must appear in published fouling trend chronicle."""
        run_id = "chron-train-id"
        root = scenario_path("ro-train-alpha")
        meta = json.loads((root / "train.meta.json").read_text(encoding="utf-8"))
        chronicle = json.loads(run_swro_fouling_pipeline(run_id, "ro-train-alpha").read_text(encoding="utf-8"))
        assert chronicle["train_id"] == meta["train_id"]

    def test_bundle_catalog_lists_five_trains(self, isolated_swro_profiler):
        """fixture-train-catalog.md inventory exposes at least five bundled RO train scenarios."""
        catalog = json.loads((APP / "fixtures" / "bundle_catalog.json").read_text(encoding="utf-8"))
        assert len(catalog["bundles"]) >= 5

    def test_decoy_salinity_plot_subcommand_absent(self, isolated_swro_profiler):
        """grade_decoy salinity plot module must not appear on rotrace CLI surface."""
        proc = shell([str(ROTRACE)])
        assert proc.returncode != 0
        assert "plot" not in (proc.stderr + proc.stdout).lower()


class TestBrineNdpVerifierParity:
    @pytest.mark.parametrize(
        "scenario",
        [
            "ro-train-alpha",
            "ro-train-bravo",
            "ro-train-charlie",
            "ro-train-delta",
            "ro-train-echo",
        ],
    )
    def test_chronicle_rows_match_reference_ndp_math(self, isolated_swro_profiler, scenario: str):
        """Chronicle rows must match independent NDP normalization reference for bundled trains."""
        run_id = f"chron-ref-{scenario}"
        root = scenario_path(scenario)
        meta = json.loads((root / "train.meta.json").read_text(encoding="utf-8"))
        got = json.loads(run_swro_fouling_pipeline(run_id, scenario).read_text(encoding="utf-8"))
        exp = contract_chronicle(
            run_id,
            meta["train_id"],
            load_readings_csv(root / "readings.csv"),
            load_batches(root / "membrane_batches.json"),
            load_cleaning_csv(root / "cleaning.csv"),
        )
        assert got["chronicle_rows"] == exp["chronicle_rows"]

    def test_chronicle_digest_matches_reference_hash(self, isolated_swro_profiler):
        """chronicle_digest must match SHA-256 over summary counters per chronicle-publish-fields.md."""
        run_id = "chron-digest"
        root = scenario_path("ro-train-bravo")
        meta = json.loads((root / "train.meta.json").read_text(encoding="utf-8"))
        got = json.loads(run_swro_fouling_pipeline(run_id, "ro-train-bravo").read_text(encoding="utf-8"))
        exp = contract_chronicle(
            run_id,
            meta["train_id"],
            load_readings_csv(root / "readings.csv"),
            load_batches(root / "membrane_batches.json"),
            load_cleaning_csv(root / "cleaning.csv"),
        )
        assert got["chronicle_digest"] == exp["chronicle_digest"]


class TestMembraneLineageOrdering:
    def test_row_sort_order_severity_then_hour_ndp(self, isolated_swro_profiler):
        """chronicle-publish-fields.md ranks rows by trend severity descending then hour_index ascending."""
        run_id = "chron-sort"
        got = json.loads(run_swro_fouling_pipeline(run_id, "ro-train-echo").read_text(encoding="utf-8"))
        keys = [(severity_rank(r["trend_class"]), r["hour_index"]) for r in got["chronicle_rows"]]
        assert keys == sorted(keys)

    def test_batch_lineage_digest_sorted_pairs(self, isolated_swro_profiler):
        """batch_lineage_digest uses sorted hour:batch_id pairs per membrane-batch-lineage.md."""
        run_id = "chron-lineage"
        root = scenario_path("ro-train-charlie")
        batches = load_batches(root / "membrane_batches.json")
        got = json.loads(run_swro_fouling_pipeline(run_id, "ro-train-charlie").read_text(encoding="utf-8"))
        assert got["batch_lineage_digest"] == contract_lineage_digest(batches)

    def test_summary_critical_count_matches_ndp_rows(self, isolated_swro_profiler):
        """summary.critical_count must equal rows classified critical in chronicle_rows."""
        run_id = "chron-critical"
        got = json.loads(run_swro_fouling_pipeline(run_id, "ro-train-echo").read_text(encoding="utf-8"))
        counted = sum(1 for r in got["chronicle_rows"] if r["trend_class"] == "critical")
        assert got["summary"]["critical_count"] == counted


class TestSkidPipelineGates:
    def test_partial_pipeline_cannot_publish_chronicle(self, isolated_swro_profiler):
        """publish-chronicle must fail when normalize-ndp and score-trends stages were skipped."""
        run_id = "chron-partial"
        root = scenario_path("ro-train-alpha")
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
        out = APP / "output" / f"{run_id}-fouling-trend-chronicle.json"
        proc = shell([str(ROTRACE), "publish-chronicle", "--run-id", run_id, "--output", str(out)])
        assert proc.returncode != 0 or not out.is_file()

    def test_randomized_membrane_label_anti_hardcode(self, isolated_swro_profiler):
        """Runtime overlay with randomized membrane batch id must still produce chronicle rows."""
        rng = random.Random(90210)
        run_id = "chron-rand-mem"
        bid = f"MBR-{rng.randint(10000, 99999)}"
        overlay = APP / "output" / "overlay-scenario"
        overlay.mkdir(parents=True, exist_ok=True)
        (overlay / "train.meta.json").write_text(
            json.dumps(
                {
                    "train_id": f"RO-{rng.randint(10, 99)}",
                    "unit_id": "U1",
                    "membrane_id": "M1",
                    "scenario": "overlay",
                }
            ),
            encoding="utf-8",
        )
        (overlay / "membrane_batches.json").write_text(
            json.dumps(
                {
                    "batches": [
                        {
                            "batch_id": bid,
                            "parent_batch_id": None,
                            "alpha": 1.0,
                            "beta": 1.0,
                            "p_base": 2.0,
                            "t_ref": 25.0,
                            "q_ref": 100.0,
                            "active_from_hour": 0,
                            "active_until_hour": 48,
                        }
                    ]
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (overlay / "cleaning.csv").write_text("hour_index,event_type,cleaned_on\n", encoding="utf-8")
        (overlay / "readings.csv").write_text(
            f"hour_index,batch_id,pressure_bar,salinity_ppt,flow_m3h,temperature_c,sensor_flags,cal_offset_ppt\n"
            f"0,{bid},3.5,35.0,100.0,25.0,ok,0.0\n",
            encoding="utf-8",
        )
        env = {"TB3_FIXTURE_ROOT": str(overlay.parent)}
        got = json.loads(run_swro_fouling_pipeline(run_id, "overlay-scenario", env=env).read_text(encoding="utf-8"))
        assert got["chronicle_rows"]
