#!/usr/bin/env python3
"""Behavioral verifier for gnu-parallel-job-manifest-reconciler."""

from __future__ import annotations

import json
import subprocess
import uuid
from pathlib import Path

import pytest

from reference_parallel import (
    cpu_seconds_total,
    db_distinct_seq_count,
    db_job_count,
    exit_histogram_from_run,
    failed_exit_count,
    job_count,
    make_synthetic_run,
    par_file_count,
    peak_concurrency,
)

BIN = Path("/app/bin/par-chain")
STATE = Path("/app/state")
OUTPUT = Path("/app/output")
FIXTURES = Path("/app/fixtures")
SEED = FIXTURES / "seed"
MANIFEST_DB = STATE / "manifest.db"
STAGING = STATE / "job.manifest.json"


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def _reset_state() -> None:
    if MANIFEST_DB.exists():
        MANIFEST_DB.unlink()
    if STAGING.exists():
        STAGING.unlink()


def _chain(joblog: Path, par_dir: Path) -> Path:
    _reset_state()
    _run([str(BIN), "reconcile", "--joblog", str(joblog), "--par-dir", str(par_dir)])
    _run([str(BIN), "stage", "--joblog", str(joblog), "--par-dir", str(par_dir)])
    OUTPUT.mkdir(parents=True, exist_ok=True)
    out = OUTPUT / f"parallel-export-{uuid.uuid4().hex[:8]}.json"
    _run([str(BIN), "export", "--joblog", str(joblog), "--par-dir", str(par_dir), "--out", str(out)])
    return out


class TestGnuParallelJobManifestReconciler:
    """GNU parallel joblog + .par reconciliation with independent reference oracle."""

    def test_binary_exists(self):
        """par-chain CLI is installed at /app/bin/par-chain."""
        assert BIN.is_file(), "missing /app/bin/par-chain"

    def test_bundled_seed_manifest_and_export(self):
        """Bundled seed run matches reference histogram, peak, and CPU totals."""
        joblog = SEED / "joblog.tsv"
        par_dir = SEED / "par"
        report_path = _chain(joblog, par_dir)
        staged = json.loads(STAGING.read_text(encoding="utf-8"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        expected_jobs = job_count(joblog)
        expected_parsed = par_file_count(par_dir)
        expected_peak = peak_concurrency(par_dir)
        expected_hist = exit_histogram_from_run(joblog, par_dir)
        expected_cpu = cpu_seconds_total(par_dir)
        expected_failed = failed_exit_count(joblog, par_dir)

        assert staged["job_count"] == expected_jobs
        assert staged["par_files_parsed"] == expected_parsed
        assert staged["peak_concurrency"] == expected_peak
        assert staged["exit_histogram"] == expected_hist
        assert report["job_count"] == expected_jobs
        assert report["peak_concurrency"] == expected_peak
        assert report["exit_histogram"] == expected_hist
        assert abs(report["cpu_seconds"] - expected_cpu) < 1e-4
        assert report["failed_exit_count"] == expected_failed
        assert "127" in staged["exit_histogram"]
        assert staged["exit_histogram"]["127"] == 1

    def test_unique_overlap_peak_not_max_slot(self, tmp_path: Path):
        """Peak concurrency counts overlapping intervals, not MAX(slot)."""
        suffix = uuid.uuid4().hex[:10]
        joblog, par_dir = make_synthetic_run(
            tmp_path / f"peak_{suffix}",
            suffix=suffix,
            jobs=[
                {"seq": 1, "slot": 4, "start_epoch": 1.0, "end_epoch": 3.0, "exit": 0},
                {"seq": 2, "slot": 1, "start_epoch": 1.5, "end_epoch": 2.5, "exit": 0},
                {"seq": 3, "slot": 2, "start_epoch": 2.0, "end_epoch": 2.8, "exit": 0},
            ],
        )
        _chain(joblog, par_dir)
        staged = json.loads(STAGING.read_text(encoding="utf-8"))
        assert peak_concurrency(par_dir) == 3
        assert staged["peak_concurrency"] == 3

    def test_exit_127_counts_as_failure(self, tmp_path: Path):
        """Exit code 127 must appear in histogram and failed_exit_count."""
        suffix = uuid.uuid4().hex[:10]
        joblog, par_dir = make_synthetic_run(
            tmp_path / f"exit127_{suffix}",
            suffix=suffix,
            jobs=[
                {
                    "seq": 11,
                    "slot": 1,
                    "start_epoch": 10.0,
                    "end_epoch": 10.5,
                    "joblog_exit": 0,
                    "exit": 127,
                },
            ],
        )
        report_path = _chain(joblog, par_dir)
        staged = json.loads(STAGING.read_text(encoding="utf-8"))
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert staged["exit_histogram"] == {"127": 1}
        assert report["failed_exit_count"] == 1

    def test_cpu_sum_from_proc_jiffies(self, tmp_path: Path):
        """cpu_seconds sums utime+stime jiffies, not max wall_sec."""
        suffix = uuid.uuid4().hex[:10]
        joblog, par_dir = make_synthetic_run(
            tmp_path / f"cpu_{suffix}",
            suffix=suffix,
            jobs=[
                {
                    "seq": 21,
                    "slot": 1,
                    "start_epoch": 1.0,
                    "end_epoch": 5.0,
                    "exit": 0,
                    "utime_jiffies": 200,
                    "stime_jiffies": 100,
                },
                {
                    "seq": 22,
                    "slot": 2,
                    "start_epoch": 2.0,
                    "end_epoch": 3.0,
                    "exit": 0,
                    "utime_jiffies": 150,
                    "stime_jiffies": 50,
                },
            ],
        )
        report_path = _chain(joblog, par_dir)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        expected = cpu_seconds_total(par_dir)
        assert expected == pytest.approx(5.0, abs=1e-4)
        assert report["cpu_seconds"] == pytest.approx(expected, abs=1e-4)
        assert report["cpu_seconds"] != pytest.approx(4.0, abs=1e-4)

    def test_second_reconcile_idempotent(self, tmp_path: Path):
        """Second reconcile must not duplicate job rows."""
        suffix = uuid.uuid4().hex[:10]
        joblog, par_dir = make_synthetic_run(
            tmp_path / f"idem_{suffix}",
            suffix=suffix,
            jobs=[
                {"seq": 31, "slot": 1, "start_epoch": 1.0, "end_epoch": 1.5, "exit": 0},
                {"seq": 32, "slot": 2, "start_epoch": 2.0, "end_epoch": 2.4, "exit": 0},
            ],
        )
        _reset_state()
        _run([str(BIN), "reconcile", "--joblog", str(joblog), "--par-dir", str(par_dir)])
        first = db_job_count(MANIFEST_DB)
        distinct_first = db_distinct_seq_count(MANIFEST_DB)
        _run([str(BIN), "reconcile", "--joblog", str(joblog), "--par-dir", str(par_dir)])
        second = db_job_count(MANIFEST_DB)
        distinct_second = db_distinct_seq_count(MANIFEST_DB)
        assert first == job_count(joblog)
        assert second == first
        assert distinct_first == first
        assert distinct_second == distinct_first

    def test_manifest_after_all_par_parsed(self, tmp_path: Path):
        """Staging manifest uses .par exit overrides after full par scan."""
        suffix = uuid.uuid4().hex[:10]
        joblog, par_dir = make_synthetic_run(
            tmp_path / f"stage_{suffix}",
            suffix=suffix,
            jobs=[
                {
                    "seq": 41,
                    "slot": 1,
                    "start_epoch": 5.0,
                    "end_epoch": 5.5,
                    "joblog_exit": 0,
                    "exit": 2,
                },
                {
                    "seq": 42,
                    "slot": 2,
                    "start_epoch": 6.0,
                    "end_epoch": 6.3,
                    "joblog_exit": 0,
                    "exit": 0,
                },
            ],
        )
        _reset_state()
        _run([str(BIN), "reconcile", "--joblog", str(joblog), "--par-dir", str(par_dir)])
        _run([str(BIN), "stage", "--joblog", str(joblog), "--par-dir", str(par_dir)])
        staged = json.loads(STAGING.read_text(encoding="utf-8"))
        expected = exit_histogram_from_run(joblog, par_dir)
        assert staged["par_files_parsed"] == par_file_count(par_dir)
        assert staged["exit_histogram"] == expected
        assert staged["exit_histogram"].get("2") == 1
