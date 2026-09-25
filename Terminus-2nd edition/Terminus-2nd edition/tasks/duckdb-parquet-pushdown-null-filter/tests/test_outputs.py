"""Behavioral verifier for parquet-pushdown-scan filter."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from reference_pushdown import reference_filter_path

APP = Path("/app")
CATALOG = APP / "fixtures" / "catalog"
OUTPUT = APP / "output"
PLAN = APP / "state" / "pushdown-plan.json"
RESET = APP / "scripts" / "reset-state.sh"
CLI = "/usr/local/bin/parquet-pushdown-scan"
TB3_ROOT = Path("/opt/verifier-fixtures")
TB3_NULL_TRAP = TB3_ROOT / "null-heavy-trap.json"
TB3_DICT_TRAP = TB3_ROOT / "tb3-dictionary-trap.json"
PARTIAL = Path(__file__).resolve().parent / "partial"

FILTER_CASES = [
    ("01-baseline.json", {"is_null_col": "sensor_id", "workers": 1}),
    ("02-null-stats-omitted.json", {"is_null_col": "sensor_id", "workers": 1}),
    ("03-dictionary-page-order.json", {"is_null_col": "sensor_id", "workers": 1}),
    ("04-timestamp-utc-bound.json", {"ts_gte": "2024-06-15T12:00:00Z", "workers": 1}),
    ("05-parallel-chunk-split.json", {"is_null_col": "sensor_id", "workers": 2}),
]

MODULES = {
    "planner": APP / "internal/planner/predicate.go",
    "stats": APP / "internal/stats/evaluator.go",
    "page": APP / "internal/page/reader.go",
    "timezone": APP / "internal/timezone/filter.go",
    "parallel": APP / "internal/parallel/splitter.go",
}

ALL_CORE = list(MODULES.keys())


def run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        cwd=str(cwd or APP),
        capture_output=True,
        text=True,
        check=False,
        env=merged,
    )


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr


def build() -> subprocess.CompletedProcess[str]:
    return run(["/usr/local/go/bin/go", "build", "-mod=readonly", "-o", CLI, "./cmd/parquet-pushdown-scan"])


def cli_filter(
    catalog: Path,
    out: Path,
    spec: dict,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [CLI, "filter", "--catalog", str(catalog), "--output", str(out)]
    if spec.get("is_null_col"):
        cmd.extend(["--is-null", spec["is_null_col"]])
    if spec.get("ts_gte"):
        cmd.extend(["--ts-gte", spec["ts_gte"]])
    cmd.extend(["--workers", str(spec.get("workers", 1))])
    return run(cmd, env=env)


def install_modules(variants: dict[str, str]) -> dict[str, bytes]:
    saved = {name: MODULES[name].read_bytes() for name in variants}
    for name, variant in variants.items():
        src = PARTIAL / f"{name}_{variant}.go"
        assert src.is_file(), f"missing partial {src}"
        shutil.copy2(src, MODULES[name])
    proc = build()
    assert proc.returncode == 0, proc.stderr
    return saved


def restore_modules(saved: dict[str, bytes]) -> None:
    for name, blob in saved.items():
        MODULES[name].write_bytes(blob)
    proc = build()
    assert proc.returncode == 0, proc.stderr


@pytest.fixture(autouse=True)
def _setup() -> None:
    reset()
    proc = build()
    assert proc.returncode == 0, proc.stderr


class TestParquetPushdownScan:
    @pytest.mark.parametrize("catalog_file,spec", FILTER_CASES)
    def test_filter_matches_reference(self, catalog_file: str, spec: dict) -> None:
        """CLI filter output matches independent stats reference for catalog scenarios."""
        catalog = CATALOG / catalog_file
        out = OUTPUT / f"filter-{catalog_file}"
        proc = cli_filter(catalog, out, spec)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        cli = json.loads(out.read_text(encoding="utf-8"))
        _, ref = reference_filter_path(catalog, spec)
        assert cli["matched_row_ids"] == ref["matched_row_ids"]
        assert cli["row_count"] == ref["row_count"]

    def test_staging_plan_written(self) -> None:
        """Filter writes /app/state/pushdown-plan.json before output."""
        catalog = CATALOG / "06-merged.json"
        out = OUTPUT / "plan-check.json"
        spec = {"is_null_col": "sensor_id", "ts_gte": "2024-06-15T12:00:00Z", "workers": 2}
        proc = cli_filter(catalog, out, spec)
        assert proc.returncode == 0, proc.stderr
        assert PLAN.is_file(), "pushdown-plan.json missing"
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        ref_plan, _ = reference_filter_path(catalog, spec)
        assert plan["selected_row_groups"] == ref_plan["selected_row_groups"]
        assert plan["worker_slices"] == ref_plan["worker_slices"]
        assert plan["plan_written"] is True

    def test_merged_filter_matches_reference(self) -> None:
        """Merged catalog requires all pushdown modules for combined predicates."""
        catalog = CATALOG / "06-merged.json"
        out = OUTPUT / "merged.json"
        spec = {"is_null_col": "sensor_id", "ts_gte": "2024-06-15T12:00:00Z", "workers": 2}
        proc = cli_filter(catalog, out, spec)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        _, ref = reference_filter_path(catalog, spec)
        assert cli["matched_row_ids"] == ref["matched_row_ids"]
        assert cli["row_count"] == ref["row_count"]
        assert cli["pruned_row_groups"] == ref["pruned_row_groups"]

    def test_tb3_fixture_directory_mounted(self) -> None:
        """Hidden verifier fixtures are available under /opt/verifier-fixtures."""
        assert TB3_ROOT.is_dir()
        assert TB3_NULL_TRAP.is_file()
        assert TB3_DICT_TRAP.is_file()

    def test_tb3_null_heavy_hidden_flag_matches_reference(self) -> None:
        """TB3 catalog null-heavy hidden_flag column with omitted null_count stats."""
        catalog = TB3_NULL_TRAP
        out = OUTPUT / "tb3-hidden-trap.json"
        spec = {"is_null_col": "hidden_flag", "workers": 1}
        proc = cli_filter(catalog, out, spec)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        _, ref = reference_filter_path(catalog, spec)
        assert cli["matched_row_ids"] == ref["matched_row_ids"]

    def test_tb3_dictionary_page_order_trap_matches_reference(self) -> None:
        """TB3 dictionary-before-null_bitmap page order trap via verifier-fixtures."""
        catalog = TB3_DICT_TRAP
        out = OUTPUT / "tb3-dict-trap.json"
        spec = {"is_null_col": "sensor_id", "workers": 1}
        proc = cli_filter(catalog, out, spec)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        _, ref = reference_filter_path(catalog, spec)
        assert cli["matched_row_ids"] == ref["matched_row_ids"]

    def test_plan_checksum_matches_reference(self) -> None:
        """Export output includes plan_checksum aligned with staging plan."""
        catalog = CATALOG / "06-merged.json"
        out = OUTPUT / "checksum.json"
        spec = {"is_null_col": "sensor_id", "ts_gte": "2024-06-15T12:00:00Z", "workers": 2}
        proc = cli_filter(catalog, out, spec)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        _, ref = reference_filter_path(catalog, spec)
        assert cli["plan_checksum"] == ref["plan_checksum"]

    def test_row_count_equals_matched_ids_length(self) -> None:
        """row_count field matches len(matched_row_ids) for baseline ingest."""
        catalog = CATALOG / "01-baseline.json"
        out = OUTPUT / "row-count.json"
        spec = {"is_null_col": "sensor_id", "workers": 1}
        proc = cli_filter(catalog, out, spec)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        assert cli["row_count"] == len(cli["matched_row_ids"])

    def test_baseline_pruned_row_groups_empty(self) -> None:
        """Baseline IS NULL filter keeps the only row group (no stats prune)."""
        catalog = CATALOG / "01-baseline.json"
        out = OUTPUT / "pruned-empty.json"
        spec = {"is_null_col": "sensor_id", "workers": 1}
        proc = cli_filter(catalog, out, spec)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        assert cli["pruned_row_groups"] == []

    def test_filter_output_table_field(self) -> None:
        """Export table name matches catalog table after ingest."""
        catalog = CATALOG / "01-baseline.json"
        out = OUTPUT / "table-field.json"
        spec = {"is_null_col": "sensor_id", "workers": 1}
        proc = cli_filter(catalog, out, spec)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        assert cli["table"] == "events"

    def test_parallel_chunks_union_covers_matched_rows(self) -> None:
        """Parallel worker slices cover every matched row id."""
        catalog = CATALOG / "05-parallel-chunk-split.json"
        out = OUTPUT / "parallel-cover.json"
        spec = {"is_null_col": "sensor_id", "workers": 2}
        proc = cli_filter(catalog, out, spec)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        covered = {rid for sl in plan["worker_slices"] for rid in sl}
        assert set(cli["matched_row_ids"]).issubset(covered)

    def test_stats_ts_prune_excludes_early_row_group(self) -> None:
        """Timestamp stats pruning drops row groups below ts_gte bound."""
        catalog = CATALOG / "04-timestamp-utc-bound.json"
        out = OUTPUT / "ts-prune.json"
        spec = {"ts_gte": "2024-06-15T12:00:00Z", "workers": 1}
        proc = cli_filter(catalog, out, spec)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        _, ref = reference_filter_path(catalog, spec)
        assert cli["pruned_row_groups"] == ref["pruned_row_groups"]

    def test_partial_stats_only_still_wrong(self) -> None:
        """Stats evaluator fix alone does not fix page-order decode trap."""
        saved = install_modules({name: "broken" for name in ALL_CORE} | {"stats": "fixed"})
        try:
            catalog = CATALOG / "03-dictionary-page-order.json"
            out = OUTPUT / "partial-stats.json"
            spec = {"is_null_col": "sensor_id", "workers": 1}
            proc = cli_filter(catalog, out, spec)
            assert proc.returncode == 0, proc.stderr
            cli = json.loads(out.read_text(encoding="utf-8"))
            _, ref = reference_filter_path(catalog, spec)
            assert cli["matched_row_ids"] != ref["matched_row_ids"]
        finally:
            restore_modules(saved)

    def test_partial_parallel_only_still_wrong(self) -> None:
        """Parallel splitter fix alone does not fix null_stats planner trap."""
        saved = install_modules({name: "broken" for name in ALL_CORE} | {"parallel": "fixed"})
        try:
            catalog = CATALOG / "02-null-stats-omitted.json"
            out = OUTPUT / "partial-parallel.json"
            spec = {"is_null_col": "sensor_id", "workers": 1}
            proc = cli_filter(catalog, out, spec)
            assert proc.returncode == 0, proc.stderr
            cli = json.loads(out.read_text(encoding="utf-8"))
            _, ref = reference_filter_path(catalog, spec)
            assert cli["matched_row_ids"] != ref["matched_row_ids"]
        finally:
            restore_modules(saved)

    def test_timestamp_tz_env_sensitivity(self) -> None:
        """Timestamp bounds honor UTC when catalog_tz is UTC even under non-UTC TZ."""
        catalog = CATALOG / "04-timestamp-utc-bound.json"
        out = OUTPUT / "tz-check.json"
        spec = {"ts_gte": "2024-06-15T12:00:00Z", "workers": 1}
        proc = cli_filter(
            catalog,
            out,
            spec,
            env={"TZ": "America/New_York"},
        )
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        _, ref = reference_filter_path(catalog, spec)
        assert cli["matched_row_ids"] == ref["matched_row_ids"]

    def test_partial_planner_only_still_wrong(self) -> None:
        """Fixing planner alone leaves dictionary page and stats traps failing."""
        saved = install_modules({name: "broken" for name in ALL_CORE} | {"planner": "fixed"})
        try:
            catalog = CATALOG / "03-dictionary-page-order.json"
            out = OUTPUT / "partial-planner.json"
            spec = {"is_null_col": "sensor_id", "workers": 1}
            proc = cli_filter(catalog, out, spec)
            assert proc.returncode == 0, proc.stderr
            cli = json.loads(out.read_text(encoding="utf-8"))
            _, ref = reference_filter_path(catalog, spec)
            assert cli["matched_row_ids"] != ref["matched_row_ids"]
        finally:
            restore_modules(saved)

    def test_partial_page_only_still_wrong(self) -> None:
        """Page-order fix alone does not fix null_count_omitted planner trap."""
        saved = install_modules({name: "broken" for name in ALL_CORE} | {"page": "fixed"})
        try:
            catalog = CATALOG / "02-null-stats-omitted.json"
            out = OUTPUT / "partial-page.json"
            spec = {"is_null_col": "sensor_id", "workers": 1}
            proc = cli_filter(catalog, out, spec)
            assert proc.returncode == 0, proc.stderr
            cli = json.loads(out.read_text(encoding="utf-8"))
            _, ref = reference_filter_path(catalog, spec)
            assert cli["matched_row_ids"] != ref["matched_row_ids"]
        finally:
            restore_modules(saved)

    def test_missing_catalog_exit_two(self, tmp_path: Path) -> None:
        """Missing catalog path returns exit code 2."""
        proc = cli_filter(tmp_path / "missing.json", OUTPUT / "missing.json", {"workers": 1})
        assert proc.returncode == 2

    def test_malformed_catalog_exit_three(self, tmp_path: Path) -> None:
        """Invalid catalog JSON returns exit code 3."""
        bad = tmp_path / "bad.json"
        bad.write_text('{"table":""}\n', encoding="utf-8")
        proc = cli_filter(bad, OUTPUT / "bad.json", {"workers": 1})
        assert proc.returncode == 3
