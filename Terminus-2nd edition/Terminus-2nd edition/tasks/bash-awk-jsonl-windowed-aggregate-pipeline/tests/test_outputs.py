"""Behavioral verifier for agg-run JSONL tumbling-window aggregation."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

APP = Path("/app")
STREAM_DIR = APP / "fixtures" / "streams"
CONFIG_PATH = APP / "config" / "window.json"
REPORT_PATH = APP / "output" / "aggregate-report.json"
STAGING_DIR = APP / "state"
ACCEPTED_PATH = STAGING_DIR / "accepted.ndjson"
STATS_PATH = STAGING_DIR / "ingest-stats.json"
ROLLUP_PATH = STAGING_DIR / "bucket-rollup.ndjson"
MANIFEST_PATH = STAGING_DIR / "ledger-manifest.json"
RUN_SEQ_PATH = STAGING_DIR / "run-seq.json"
INGEST_AWK = APP / "lib" / "ingest.awk"
BUCKET_AWK = APP / "lib" / "bucket.awk"
EXPORT_AWK = APP / "lib" / "export.awk"
WINDOW_AWK = APP / "lib" / "window.awk"
AGG_RUN = APP / "bin" / "agg-run"
BROKEN_LIB = Path(__file__).resolve().parent / "broken_lib"
TB3_ROOT = Path("/opt/verifier-fixtures/agg")
SEED = os.environ.get("VERIFIER_SEED", "bash-awk-jsonl-windowed-aggregate-repair")

# Instruction output paths (audit coverage literals)
OUTPUT_AGGREGATE_JSON = "/app/output/aggregate-report.json"
ACCEPTED_NDJSON = "/app/state/accepted.ndjson"
INGEST_STATS_JSON = "/app/state/ingest-stats.json"
BUCKET_ROLLUP_NDJSON = "/app/state/bucket-rollup.ndjson"
LEDGER_MANIFEST_JSON = "/app/state/ledger-manifest.json"
RUN_SEQ_JSON = "/app/state/run-seq.json"


def _run(cmd: list[str], *, env: dict | None = None) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    merged.setdefault("TZ", "UTC")
    if env:
        merged.update(env)
    return subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        env=merged,
        cwd=str(APP),
    )


def reset_state() -> None:
    proc = _run(["bash", str(APP / "scripts" / "reset-state.sh")])
    assert proc.returncode == 0, proc.stderr


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def list_jsonl_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.jsonl"))


def rfc3339_to_epoch(ts: str) -> int:
    assert ts.endswith("Z")
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return int(dt.timestamp())


def epoch_to_rfc3339(sec: int) -> str:
    return datetime.fromtimestamp(sec, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def valid_number(raw) -> bool:
    if raw is None:
        return False
    if isinstance(raw, str):
        if raw in ("", "null", "NaN", "nan"):
            return False
        try:
            float(raw)
        except ValueError:
            return False
        return True
    if isinstance(raw, (int, float)):
        return not (isinstance(raw, float) and math.isnan(raw))
    return False


def reference_aggregate(stream_root: Path, window_sec: int, *, run_seq: int = 1) -> dict:
    lines_read = 0
    events_deduped = 0
    events_skipped_invalid_value = 0
    seen: set[str] = set()
    events_accepted = 0
    footer_sum = 0.0

    agg: dict[tuple[int, str, str], dict[str, float]] = {}

    for path in list_jsonl_files(stream_root):
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            lines_read += 1
            doc = json.loads(line)
            event_id = str(doc.get("event_id", ""))
            tenant = str(doc.get("tenant", ""))
            metric = str(doc.get("metric", ""))
            ts = str(doc.get("ts", ""))
            value_raw = doc.get("value", "missing")

            if not event_id or not tenant or not metric or not ts:
                events_skipped_invalid_value += 1
                continue

            if event_id in seen:
                events_deduped += 1
                continue
            seen.add(event_id)

            if not valid_number(value_raw):
                events_skipped_invalid_value += 1
                continue

            value = float(value_raw)
            epoch = rfc3339_to_epoch(ts)
            bucket = (epoch // window_sec) * window_sec
            key = (bucket, tenant, metric)
            if key not in agg:
                agg[key] = {"sum": value, "count": 1, "min": value, "max": value}
            else:
                row = agg[key]
                row["sum"] += value
                row["count"] += 1
                row["min"] = min(row["min"], value)
                row["max"] = max(row["max"], value)

            events_accepted += 1
            footer_sum += value

    windows_map: dict[int, list[dict]] = {}
    for (bucket, tenant, metric), stats in agg.items():
        windows_map.setdefault(bucket, []).append(
            {
                "tenant": tenant,
                "metric": metric,
                "sum": stats["sum"],
                "count": int(stats["count"]),
                "min": stats["min"],
                "max": stats["max"],
            }
        )

    windows: list[dict] = []
    for bucket in sorted(windows_map):
        series = sorted(windows_map[bucket], key=lambda s: (s["tenant"], s["metric"]))
        windows.append(
            {
                "bucket_start": epoch_to_rfc3339(bucket),
                "series": series,
            }
        )

    return {
        "agg_version": 1,
        "window_sec": window_sec,
        "stats": {
            "lines_read": lines_read,
            "events_accepted": events_accepted,
            "events_deduped": events_deduped,
            "events_skipped_invalid_value": events_skipped_invalid_value,
        },
        "windows": windows,
        "footer": {
            "total_events": events_accepted,
            "total_value_sum": footer_sum,
            "run_seq": run_seq,
        },
    }


def reference_rollup(stream_root: Path, window_sec: int) -> list[dict]:
    rows: list[dict] = []
    for window in reference_aggregate(stream_root, window_sec)["windows"]:
        bucket = rfc3339_to_epoch(window["bucket_start"])
        for series in window["series"]:
            rows.append(
                {
                    "bucket": bucket,
                    "tenant": series["tenant"],
                    "metric": series["metric"],
                    "sum": series["sum"],
                    "count": series["count"],
                    "min": series["min"],
                    "max": series["max"],
                }
            )
    rows.sort(key=lambda r: (r["bucket"], r["tenant"], r["metric"]))
    return rows


def reference_staging(stream_root: Path) -> dict:
    report = reference_aggregate(stream_root, int(load_config()["window_sec"]))
    accepted: list[dict] = []
    seen: set[str] = set()

    for path in list_jsonl_files(stream_root):
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            doc = json.loads(line)
            event_id = str(doc.get("event_id", ""))
            tenant = str(doc.get("tenant", ""))
            metric = str(doc.get("metric", ""))
            ts = str(doc.get("ts", ""))
            value_raw = doc.get("value", "missing")

            if not event_id or not tenant or not metric or not ts:
                continue
            if event_id in seen:
                continue
            seen.add(event_id)
            if not valid_number(value_raw):
                continue
            accepted.append(
                {
                    "epoch": rfc3339_to_epoch(ts),
                    "tenant": tenant,
                    "metric": metric,
                    "value": float(value_raw),
                }
            )

    return {
        "accepted": accepted,
        "stats": {
            "lines_read": report["stats"]["lines_read"],
            "events_accepted": report["stats"]["events_accepted"],
            "events_deduped": report["stats"]["events_deduped"],
            "events_skipped_invalid_value": report["stats"]["events_skipped_invalid_value"],
            "footer_sum": report["footer"]["total_value_sum"],
        },
    }


def reference_manifest(stream_root: Path) -> dict:
    staging = reference_staging(stream_root)
    accepted_bytes = "\n".join(
        json.dumps(row, separators=(",", ": ")) for row in staging["accepted"]
    )
    if staging["accepted"]:
        accepted_bytes += "\n"
    digest = hashlib.sha256(accepted_bytes.encode("utf-8")).hexdigest()
    return {
        "manifest_version": 1,
        "accepted_sha256": digest,
        "events_accepted": staging["stats"]["events_accepted"],
    }


def run_agg(
    stream_dir: Path,
    output: Path = REPORT_PATH,
    *,
    env: dict | None = None,
) -> subprocess.CompletedProcess:
    return _run(
        [
            "/app/bin/agg-run",
            "--stream-dir",
            str(stream_dir),
            "--config",
            str(CONFIG_PATH),
            "--output",
            str(output),
        ],
        env=env,
    )


def load_report(path: Path = REPORT_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_close(a: float, b: float) -> None:
    assert math.isclose(a, b, rel_tol=0, abs_tol=1e-6), (a, b)


def compare_reports(got: dict, expected: dict) -> None:
    assert got["agg_version"] == expected["agg_version"]
    assert got["window_sec"] == expected["window_sec"]
    assert got["stats"] == expected["stats"]
    assert got["footer"]["total_events"] == expected["footer"]["total_events"]
    assert_close(float(got["footer"]["total_value_sum"]), float(expected["footer"]["total_value_sum"]))
    assert got["footer"]["run_seq"] == expected["footer"]["run_seq"]

    assert [w["bucket_start"] for w in got["windows"]] == [
        w["bucket_start"] for w in expected["windows"]
    ]
    assert len(got["windows"]) == len(expected["windows"])
    for gw, ew in zip(got["windows"], expected["windows"]):
        gseries = {(s["tenant"], s["metric"]): s for s in gw["series"]}
        eseries = {(s["tenant"], s["metric"]): s for s in ew["series"]}
        assert set(gseries) == set(eseries)
        for key in eseries:
            for field in ("count",):
                assert gseries[key][field] == eseries[key][field]
            for field in ("sum", "min", "max"):
                assert_close(float(gseries[key][field]), float(eseries[key][field]))


def isolated_stream(*names: str) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="agg-stream-"))
    for name in names:
        shutil.copy2(STREAM_DIR / name, tmp / name)
    return tmp


def seeded_measurement() -> str:
    digest = hashlib.sha256(SEED.encode("utf-8")).hexdigest()[:8]
    return f"seed_{digest}"


def snapshot_agg_sources() -> dict[str, str]:
    return {
        "ingest": INGEST_AWK.read_text(encoding="utf-8"),
        "bucket": BUCKET_AWK.read_text(encoding="utf-8"),
        "export": EXPORT_AWK.read_text(encoding="utf-8"),
        "agg_run": AGG_RUN.read_text(encoding="utf-8"),
    }


def restore_agg_sources(saved: dict[str, str]) -> None:
    INGEST_AWK.write_text(saved["ingest"], encoding="utf-8")
    BUCKET_AWK.write_text(saved["bucket"], encoding="utf-8")
    EXPORT_AWK.write_text(saved["export"], encoding="utf-8")
    AGG_RUN.write_text(saved["agg_run"], encoding="utf-8")
    os.chmod(AGG_RUN, 0o755)


def install_ingest(name: str) -> None:
    shutil.copy2(BROKEN_LIB / name, INGEST_AWK)


def install_bucket(name: str) -> None:
    shutil.copy2(BROKEN_LIB / name, BUCKET_AWK)


def install_export(name: str) -> None:
    shutil.copy2(BROKEN_LIB / name, EXPORT_AWK)


def install_agg_run(name: str) -> None:
    shutil.copy2(BROKEN_LIB / name, AGG_RUN)
    os.chmod(AGG_RUN, 0o755)


def report_differs_from_reference(stream_dir: Path, window_sec: int) -> bool:
    try:
        compare_reports(load_report(), reference_aggregate(stream_dir, window_sec))
    except AssertionError:
        return True
    return False


class TestAggRunPipeline:
    def test_output_paths_written(self):
        """All instruction output paths must exist after a successful run."""
        reset_state()
        proc = run_agg(STREAM_DIR)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert str(REPORT_PATH) == OUTPUT_AGGREGATE_JSON
        assert str(ACCEPTED_PATH) == ACCEPTED_NDJSON
        assert str(STATS_PATH) == INGEST_STATS_JSON
        assert str(ROLLUP_PATH) == BUCKET_ROLLUP_NDJSON
        assert str(MANIFEST_PATH) == LEDGER_MANIFEST_JSON
        assert str(RUN_SEQ_PATH) == RUN_SEQ_JSON
        assert REPORT_PATH.is_file()
        assert ACCEPTED_PATH.is_file()
        assert STATS_PATH.is_file()
        assert ROLLUP_PATH.is_file()
        assert MANIFEST_PATH.is_file()

    def test_staging_ledger_matches_reference(self):
        """Ingest stage must write accepted.ndjson and ingest-stats.json per staging-schema."""
        reset_state()
        proc = run_agg(STREAM_DIR)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        expected = reference_staging(STREAM_DIR)
        assert ACCEPTED_PATH.is_file()
        assert STATS_PATH.is_file()
        got_rows = [json.loads(line) for line in ACCEPTED_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(got_rows) == len(expected["accepted"])
        for got, want in zip(got_rows, expected["accepted"]):
            assert got["epoch"] == want["epoch"]
            assert got["tenant"] == want["tenant"]
            assert got["metric"] == want["metric"]
            assert_close(float(got["value"]), float(want["value"]))
        got_stats = json.loads(STATS_PATH.read_text(encoding="utf-8"))
        assert got_stats["lines_read"] == expected["stats"]["lines_read"]
        assert got_stats["events_accepted"] == expected["stats"]["events_accepted"]
        assert got_stats["events_deduped"] == expected["stats"]["events_deduped"]
        assert got_stats["events_skipped_invalid_value"] == expected["stats"]["events_skipped_invalid_value"]
        assert_close(float(got_stats["footer_sum"]), float(expected["stats"]["footer_sum"]))

    def test_ledger_manifest_matches_reference(self):
        """Wrapper must write ledger-manifest.json binding accepted staging before export."""
        reset_state()
        proc = run_agg(STREAM_DIR)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert MANIFEST_PATH.is_file()
        got = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        stats = json.loads(STATS_PATH.read_text(encoding="utf-8"))
        on_disk = hashlib.sha256(ACCEPTED_PATH.read_bytes()).hexdigest()
        assert got["manifest_version"] == 1
        assert got["events_accepted"] == stats["events_accepted"]
        assert got["accepted_sha256"] == on_disk

    def test_bucket_rollup_intermediate_artifact(self):
        """Stage 2 must write bucket-rollup.ndjson per staging-schema."""
        reset_state()
        window_sec = int(load_config()["window_sec"])
        proc = run_agg(STREAM_DIR)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert ROLLUP_PATH.is_file()
        got_rows = [json.loads(line) for line in ROLLUP_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        expected_rows = reference_rollup(STREAM_DIR, window_sec)
        assert len(got_rows) == len(expected_rows)
        for got, want in zip(got_rows, expected_rows):
            assert got["bucket"] == want["bucket"]
            assert got["tenant"] == want["tenant"]
            assert got["metric"] == want["metric"]
            assert got["count"] == want["count"]
            for field in ("sum", "min", "max"):
                assert_close(float(got[field]), float(want[field]))

    def test_nested_stream_discovered_in_full_tree(self):
        """Nested fixture paths must be included in lexicographic discovery order."""
        reset_state()
        proc = run_agg(STREAM_DIR)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        keys = {
            (s["tenant"], s["metric"])
            for w in load_report()["windows"]
            for s in w["series"]
        }
        assert ("nest", "depth") in keys

    def test_spread_window_min_max(self):
        """008-spread events in one bucket must preserve min and max."""
        reset_state()
        tmp = isolated_stream("008-spread.jsonl")
        proc = run_agg(tmp)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        series = load_report()["windows"][0]["series"][0]
        assert_close(float(series["min"]), 5.0)
        assert_close(float(series["max"]), 15.0)
        assert_close(float(series["sum"]), 20.0)

    def test_pipeline_report_matches_reference(self):
        """Full fixture tree must match the independent reference aggregate."""
        reset_state()
        window_sec = int(load_config()["window_sec"])
        proc = run_agg(STREAM_DIR)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        expected = reference_aggregate(STREAM_DIR, window_sec)
        compare_reports(load_report(), expected)

    def test_window_boundary_utc(self):
        """Boundary timestamps must land in distinct UTC tumbling buckets."""
        reset_state()
        window_sec = int(load_config()["window_sec"])
        tmp = isolated_stream("002-boundary.jsonl")
        proc = run_agg(tmp)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        expected = reference_aggregate(tmp, window_sec)
        compare_reports(load_report(), expected)
        assert len(expected["windows"]) == 2

    def test_agg_run_matches_reference_under_non_utc_process_tz(self):
        """Pipeline must stay UTC-correct when the process timezone is not UTC."""
        reset_state()
        window_sec = int(load_config()["window_sec"])
        tmp = isolated_stream("002-boundary.jsonl")
        proc = run_agg(tmp, env={"TZ": "America/New_York"})
        assert proc.returncode == 0, proc.stderr + proc.stdout
        expected = reference_aggregate(tmp, window_sec)
        compare_reports(load_report(), expected)

    def test_dedup_first_wins(self):
        """Duplicate event_id lines must be dropped after the first accepted row."""
        reset_state()
        tmp = isolated_stream("003-dedup.jsonl")
        proc = run_agg(tmp)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        report = load_report()
        assert report["stats"]["events_deduped"] == 1
        assert report["stats"]["events_accepted"] == 2
        assert report["footer"]["total_events"] == 2
        series = report["windows"][0]["series"][0]
        assert_close(float(series["sum"]), 103.0)

    def test_invalid_values_skipped_not_zero(self):
        """Invalid numeric values must be skipped instead of coerced to zero."""
        reset_state()
        tmp = isolated_stream("004-invalid-values.jsonl")
        proc = run_agg(tmp)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        report = load_report()
        assert report["stats"]["events_skipped_invalid_value"] == 3
        assert report["stats"]["events_accepted"] == 1
        assert report["footer"]["total_events"] == 1
        assert_close(float(report["footer"]["total_value_sum"]), 10.0)

    def test_series_key_no_concat_collision(self):
        """Tenant and metric must not collide when concatenated without a separator."""
        reset_state()
        tmp = isolated_stream("005-key-collision.jsonl")
        proc = run_agg(tmp)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        report = load_report()
        series = report["windows"][0]["series"]
        assert len(series) == 2
        by_key = {(s["tenant"], s["metric"]): s for s in series}
        assert_close(float(by_key[("a", "bc")]["sum"]), 1.0)
        assert_close(float(by_key[("ab", "c")]["sum"]), 2.0)

    def test_footer_total_events_not_window_count(self):
        """Footer total_events must count accepted events, not window buckets."""
        reset_state()
        tmp = isolated_stream("006-multi-window.jsonl")
        proc = run_agg(tmp)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        report = load_report()
        assert len(report["windows"]) == 2
        assert report["footer"]["total_events"] == 3
        assert report["stats"]["events_accepted"] == 3

    def test_export_series_and_bucket_sort_order(self):
        """Report windows and per-window series must follow contract sort order."""
        reset_state()
        proc = run_agg(STREAM_DIR)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        report = load_report()
        bucket_starts = [w["bucket_start"] for w in report["windows"]]
        assert bucket_starts == sorted(bucket_starts)
        for window in report["windows"]:
            pairs = [(s["tenant"], s["metric"]) for s in window["series"]]
            assert pairs == sorted(pairs)

    def test_run_seq_unchanged_on_idempotent_rerun(self):
        """Identical stream inputs must keep run_seq stable across consecutive runs."""
        reset_state()
        proc = run_agg(STREAM_DIR)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        first_seq = json.loads(RUN_SEQ_PATH.read_text(encoding="utf-8"))["seq"]
        first_report_seq = load_report()["footer"]["run_seq"]
        proc2 = run_agg(STREAM_DIR)
        assert proc2.returncode == 0, proc2.stderr + proc2.stdout
        second_seq = json.loads(RUN_SEQ_PATH.read_text(encoding="utf-8"))["seq"]
        assert second_seq == first_seq == first_report_seq == 1

    def test_run_seq_increments_on_different_input(self):
        """Changing stream contents must bump run_seq while preserving prior report correctness."""
        reset_state()
        tmp_a = isolated_stream("003-dedup.jsonl")
        proc = run_agg(tmp_a)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        assert load_report()["footer"]["run_seq"] == 1
        tmp_b = isolated_stream("004-invalid-values.jsonl")
        proc2 = run_agg(tmp_b)
        assert proc2.returncode == 0, proc2.stderr + proc2.stdout
        assert load_report()["footer"]["run_seq"] == 2

    def test_run_seq_increments_on_same_path_content_change(self):
        """Mutating JSONL bytes at an unchanged path must change fingerprint and bump run_seq."""
        reset_state()
        tmp = Path(tempfile.mkdtemp(prefix="agg-fp-content-"))
        stream = tmp / "events.jsonl"
        stream.write_text(
            json.dumps(
                {
                    "event_id": "fp-a",
                    "tenant": "acme",
                    "metric": "probe",
                    "ts": "2024-01-15T08:00:00Z",
                    "value": 1,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        proc = run_agg(tmp)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        first = json.loads(RUN_SEQ_PATH.read_text(encoding="utf-8"))
        assert first["seq"] == 1
        assert load_report()["footer"]["run_seq"] == 1
        first_fp = first["input_fingerprint"]

        stream.write_text(
            json.dumps(
                {
                    "event_id": "fp-b",
                    "tenant": "acme",
                    "metric": "probe",
                    "ts": "2024-01-15T08:00:00Z",
                    "value": 2,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        proc2 = run_agg(tmp)
        assert proc2.returncode == 0, proc2.stderr + proc2.stdout
        second = json.loads(RUN_SEQ_PATH.read_text(encoding="utf-8"))
        assert second["input_fingerprint"] != first_fp
        assert second["seq"] == 2
        assert load_report()["footer"]["run_seq"] == 2

    def test_idempotent_double_run(self):
        """Two consecutive runs on the same inputs must emit identical JSON."""
        reset_state()
        proc = run_agg(STREAM_DIR)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        first = load_report()
        proc2 = run_agg(STREAM_DIR)
        assert proc2.returncode == 0, proc2.stderr + proc2.stdout
        second = load_report()
        assert first == second

    def test_verifier_seed_injected_stream(self):
        """Runtime seed stream must be aggregated like public fixtures."""
        reset_state()
        meas = seeded_measurement()
        tmp = Path(tempfile.mkdtemp(prefix="agg-seed-"))
        shutil.copytree(STREAM_DIR, tmp, dirs_exist_ok=True)
        offset = int(hashlib.sha256(SEED.encode()).hexdigest()[0:2], 16) % 120
        ts_sec = 1705305600 + offset
        ts = epoch_to_rfc3339(ts_sec)
        extra = tmp / "seed-extra.jsonl"
        extra.write_text(
            json.dumps(
                {
                    "event_id": f"{meas}-evt",
                    "tenant": meas,
                    "metric": "probe",
                    "ts": ts,
                    "value": 7,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        window_sec = int(load_config()["window_sec"])
        proc = run_agg(tmp)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        expected = reference_aggregate(tmp, window_sec, run_seq=1)
        compare_reports(load_report(), expected)
        keys = {
            (s["tenant"], s["metric"])
            for w in load_report()["windows"]
            for s in w["series"]
        }
        assert (meas, "probe") in keys

    def test_verifier_hidden_manifest_trap_stream(self):
        """Hidden verifier stream under /opt/verifier-fixtures must match reference export."""
        assert TB3_ROOT.is_dir(), "missing /opt/verifier-fixtures/agg mount"
        reset_state()
        tmp = Path(tempfile.mkdtemp(prefix="agg-tb3-"))
        shutil.copy2(TB3_ROOT / "streams" / "manifest-trap.jsonl", tmp / "manifest-trap.jsonl")
        window_sec = int(load_config()["window_sec"])
        proc = run_agg(tmp)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        expected = reference_aggregate(tmp, window_sec, run_seq=1)
        compare_reports(load_report(), expected)

    def test_verifier_hidden_manifest_dedup_trap(self):
        """Hidden duplicate event_id stream must enforce first-win dedup through full pipeline."""
        assert TB3_ROOT.is_dir(), "missing /opt/verifier-fixtures/agg mount"
        reset_state()
        tmp = Path(tempfile.mkdtemp(prefix="agg-tb3-dedup-"))
        shutil.copy2(TB3_ROOT / "streams" / "manifest-trap-dedup.jsonl", tmp / "manifest-trap-dedup.jsonl")
        proc = run_agg(tmp)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        report = load_report()
        assert report["stats"]["events_deduped"] == 1
        assert report["stats"]["events_accepted"] == 1
        assert_close(float(report["footer"]["total_value_sum"]), 11.0)

    def test_missing_stream_dir_exits_nonzero(self):
        """Missing or unreadable --stream-dir must exit 1 without writing a report."""
        reset_state()
        proc = _run(
            [
                "/app/bin/agg-run",
                "--stream-dir",
                "/app/fixtures/no-such-stream",
                "--config",
                str(CONFIG_PATH),
                "--output",
                str(REPORT_PATH),
            ]
        )
        assert proc.returncode == 1

    def test_partial_export_only_still_fails_multi_window(self):
        """Golden ingest and bucket with footer-only export fix must not satisfy accepted counts."""
        saved = snapshot_agg_sources()
        try:
            reset_state()
            shutil.copy2(BROKEN_LIB / "golden_ingest.awk", INGEST_AWK)
            shutil.copy2(BROKEN_LIB / "golden_bucket.awk", BUCKET_AWK)
            install_export("export_footer_only.awk")
            window_sec = int(load_config()["window_sec"])
            tmp = isolated_stream("006-multi-window.jsonl")
            proc = run_agg(tmp)
            assert proc.returncode == 0, proc.stderr + proc.stdout
            assert report_differs_from_reference(tmp, window_sec)
            assert load_report()["footer"]["total_events"] != 3
        finally:
            restore_agg_sources(saved)

    def test_partial_ingest_only_still_fails_invalid_skip(self):
        """Golden bucket and export cannot compensate for ingest invalid-value coercion."""
        saved = snapshot_agg_sources()
        try:
            reset_state()
            install_ingest("ingest_dedup_only.awk")
            shutil.copy2(BROKEN_LIB / "golden_bucket.awk", BUCKET_AWK)
            shutil.copy2(BROKEN_LIB / "golden_export.awk", EXPORT_AWK)
            tmp = isolated_stream("004-invalid-values.jsonl")
            proc = run_agg(tmp)
            assert proc.returncode != 0 or load_report()["stats"]["events_skipped_invalid_value"] != 3
        finally:
            restore_agg_sources(saved)

    def test_partial_ingest_only_still_fails_bucket_boundary(self):
        """Golden ingest alone must not fix aggregate bucket alignment in stage 2."""
        saved = snapshot_agg_sources()
        try:
            reset_state()
            shutil.copy2(BROKEN_LIB / "golden_ingest.awk", INGEST_AWK)
            install_bucket("bucket_bucket_only.awk")
            install_export("export_baseline.awk")
            window_sec = int(load_config()["window_sec"])
            tmp = isolated_stream("002-boundary.jsonl")
            proc = run_agg(tmp)
            assert proc.returncode == 0, proc.stderr + proc.stdout
            assert report_differs_from_reference(tmp, window_sec)
        finally:
            restore_agg_sources(saved)

    def test_partial_bucket_only_still_fails_dedup_sum(self):
        """Golden bucket rollup alone must not repair broken ingest staging."""
        saved = snapshot_agg_sources()
        try:
            reset_state()
            install_ingest("ingest_baseline.awk")
            shutil.copy2(BROKEN_LIB / "golden_bucket.awk", BUCKET_AWK)
            install_export("export_baseline.awk")
            tmp = isolated_stream("003-dedup.jsonl")
            proc = run_agg(tmp)
            assert proc.returncode == 0, proc.stderr + proc.stdout
            series = load_report()["windows"][0]["series"][0]
            assert not math.isclose(float(series["sum"]), 103.0, rel_tol=0, abs_tol=1e-6)
        finally:
            restore_agg_sources(saved)

    def test_partial_wrapper_tz_only_still_fails_under_non_utc(self):
        """Exporting TZ=UTC in agg-run without full ingest/bucket repair must still fail reference."""
        saved = snapshot_agg_sources()
        try:
            reset_state()
            install_ingest("ingest_baseline.awk")
            install_bucket("bucket_baseline.awk")
            install_export("export_baseline.awk")
            install_agg_run("agg_run_tz_only.sh")
            window_sec = int(load_config()["window_sec"])
            tmp = isolated_stream("002-boundary.jsonl")
            proc = run_agg(tmp, env={"TZ": "America/New_York"})
            assert proc.returncode == 0, proc.stderr + proc.stdout
            assert report_differs_from_reference(tmp, window_sec)
        finally:
            restore_agg_sources(saved)

    def test_partial_manifest_skip_still_fails_golden_export(self):
        """Golden export must reject runs when ledger-manifest.json was never written."""
        saved = snapshot_agg_sources()
        try:
            reset_state()
            shutil.copy2(BROKEN_LIB / "golden_ingest.awk", INGEST_AWK)
            shutil.copy2(BROKEN_LIB / "golden_bucket.awk", BUCKET_AWK)
            shutil.copy2(BROKEN_LIB / "golden_export.awk", EXPORT_AWK)
            install_agg_run("agg_run_tz_only.sh")
            tmp = isolated_stream("001-basic.jsonl")
            proc = run_agg(tmp)
            assert proc.returncode != 0, proc.stderr + proc.stdout
        finally:
            restore_agg_sources(saved)
