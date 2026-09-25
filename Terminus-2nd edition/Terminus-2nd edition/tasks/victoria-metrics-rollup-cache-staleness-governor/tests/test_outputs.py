"""Behavioral verifier for vmrollup ingest, rollup snapshot, and query grace."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from reference_f58d4df5_victoria import (
    align_window,
    reference_counter,
    reference_hist_inf,
)

APP = Path("/app")
DB = APP / "data" / "metrics.db"
CONFIG = APP / "config" / "rollup.json"
SCRAPE_DIR = APP / "fixtures" / "scrapes"
MANIFEST = APP / "state" / "scrape-manifest.json"
SNAPSHOT = APP / "state" / "rollup-snapshot.json"
CACHE_INDEX = APP / "state" / "cache-index.json"
QUERY_OUT = APP / "output" / "query-report.json"
HIDDEN = Path("/opt/verifier-fixtures")
INTERVAL_SEC = 60
INTERVAL_MS = INTERVAL_SEC * 1000


def _run(cmd: list[str], *, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, check=False, capture_output=True, text=True, env=merged, cwd=str(APP))


def reset_state() -> None:
    proc = _run(["bash", str(APP / "scripts" / "reset-state.sh")])
    assert proc.returncode == 0, proc.stderr


def rebuild() -> None:
    proc = _run(["go", "build", "-mod=readonly", "-o", "/usr/local/bin/vmrollup", "./cmd/vmrollup"])
    assert proc.returncode == 0, proc.stderr + proc.stdout


def ingest(scrape_dir: Path | None = None) -> None:
    proc = _run(
        [
            "vmrollup",
            "ingest",
            "--scrape-dir",
            str(scrape_dir or SCRAPE_DIR),
            "--config",
            str(CONFIG),
            "--db",
            str(DB),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def query(metric: str, start_ms: int, end_ms: int, output: Path | None = None, query_ms: int | None = None) -> dict:
    out = output or QUERY_OUT
    cmd = [
        "vmrollup",
        "query",
        "--metric",
        metric,
        "--window-start-ms",
        str(start_ms),
        "--window-end-ms",
        str(end_ms),
        "--config",
        str(CONFIG),
        "--db",
        str(DB),
        "--output",
        str(out),
    ]
    if query_ms is not None:
        cmd.extend(["--query-ms", str(query_ms)])
    proc = _run(cmd)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return json.loads(out.read_text(encoding="utf-8"))


def load_snapshot() -> dict:
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def find_series(snap: dict, metric: str, tier: str = "raw") -> dict | None:
    for row in snap["series"]:
        if row["metric"] == metric and row.get("tier") == tier:
            return row
    return None


def find_series_window(
    snap: dict, metric: str, window_start_ms: int, window_end_ms: int, tier: str = "raw"
) -> dict | None:
    for row in snap["series"]:
        if (
            row["metric"] == metric
            and row.get("tier") == tier
            and row["window_start_ms"] == window_start_ms
            and row["window_end_ms"] == window_end_ms
        ):
            return row
    return None


def expected_cache_key(row: dict) -> str:
    return f"{row['metric']}|{row.get('labels', '')}|{row['window_start_ms']}|{row['window_end_ms']}"


@pytest.fixture(autouse=True)
def _fresh_state():
    reset_state()
    rebuild()
    yield


def test_tf58d4d_ingest_writes_manifest_and_snapshot():
    """Ingest must emit /app/state/scrape-manifest.json, /app/state/rollup-snapshot.json, and /app/state/cache-index.json."""
    ingest()
    assert MANIFEST.is_file()
    assert SNAPSHOT.is_file()
    assert CACHE_INDEX.is_file()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["samples_accepted"] > 0
    assert manifest["manifest_sha256"]


def test_tf58d4d_snapshot_series_sorted():
    """Rollup snapshot series must sort by metric, window_start_ms, then tier."""
    ingest()
    snap = load_snapshot()
    keys = [(s["metric"], s["window_start_ms"], s["tier"]) for s in snap["series"]]
    assert keys == sorted(keys)


def test_tf58d4d_vm_requests_total_rate_reference():
    """Counter rate for vm_requests_total must match independent reference math."""
    ingest()
    snap = load_snapshot()
    row = find_series(snap, "vm_requests_total")
    assert row is not None
    ref_last, ref_rate, start, end = reference_counter("vm_requests_total", SCRAPE_DIR)
    assert row["window_start_ms"] == start
    assert row["window_end_ms"] == end
    assert row["value"] == pytest.approx(ref_last)
    assert row["rate_per_sec"] == pytest.approx(ref_rate)


def test_tf58d4d_counter_reset_mid_window():
    """Counter reset detection must apply after the first scrape in a window."""
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        scrape = Path(tmp)
        shutil.copy(SCRAPE_DIR / "counter-reset.prom", scrape / "counter-reset.prom")
        ingest(scrape)
        snap = load_snapshot()
        row = find_series(snap, "vm_reset_total")
        assert row is not None
        _, ref_rate, _, _ = reference_counter("vm_reset_total", scrape)
        assert row.get("rate_per_sec", 0.0) == pytest.approx(ref_rate)


def test_tf58d4d_histogram_inf_bucket_preserved():
    """Histogram merge must keep the +Inf bucket when le bounds shift."""
    ingest()
    snap = load_snapshot()
    shift_start, shift_end = align_window(1704067260000, INTERVAL_MS)
    row = find_series_window(snap, "vm_latency_seconds", shift_start, shift_end)
    assert row is not None
    ref_buckets = reference_hist_inf("vm_latency_seconds", SCRAPE_DIR, window_start_ms=shift_start)
    ref_inf = next(b for b in ref_buckets if b["le"] == "+Inf")
    got_inf = next(b for b in row["buckets"] if b["le"] == "+Inf")
    assert got_inf["count"] == pytest.approx(ref_inf["count"])


def test_tf58d4d_stale_propagates_to_5m_tier():
    """Staleness on raw tier must propagate to the 5m downsample tier."""
    ingest()
    snap = load_snapshot()
    raw = find_series(snap, "vm_stale_gauge", tier="raw")
    five = find_series(snap, "vm_stale_gauge", tier="5m")
    assert raw is not None and five is not None
    assert raw["stale"] is True
    assert five["stale"] is True


def test_tf58d4d_cache_ttl_uses_sample_timestamp():
    """Cache TTL must expire on the query path using last_sample_ts_ms per cache-ttl.md."""
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        scrape = Path(tmp)
        shutil.copy(SCRAPE_DIR / "cache-ttl.prom", scrape / "cache-ttl.prom")
        ingest(scrape)
        snap = load_snapshot()
        for row in snap["series"]:
            if row["metric"] == "vm_cache_probe" and row.get("tier") == "raw":
                row["value"] = 1.0
        SNAPSHOT.write_text(json.dumps(snap), encoding="utf-8")
        start, end = align_window(1704067200000, INTERVAL_MS)
        last_sample_ms = 1704067250000
        query_ms = last_sample_ms + 130_000
        report = query("vm_cache_probe", start, end, query_ms=query_ms)
        assert report["served_from_cache"] is False
        assert report["rollup"]["value"] == pytest.approx(2.0)


def test_tf58d4d_grace_bypasses_cache_on_late_raw():
    """Query must bypass cache when fresher raw samples arrive inside grace window."""
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        scrape = Path(tmp)
        shutil.copy(SCRAPE_DIR / "grace-raw.prom", scrape / "a-grace-raw.prom")
        shutil.copy(SCRAPE_DIR / "grace-late.prom", scrape / "b-grace-late.prom")
        ingest(scrape)
        start, end = align_window(1704067200000, INTERVAL_MS)
        snap = load_snapshot()
        snap["generated_at_ms"] = 1704067200000
        SNAPSHOT.write_text(json.dumps(snap), encoding="utf-8")
        idx = json.loads(CACHE_INDEX.read_text(encoding="utf-8"))
        for entry in idx["entries"]:
            if (
                entry["metric"] == "vm_grace_total"
                and entry["window_start_ms"] == start
                and entry["window_end_ms"] == end
            ):
                entry["last_sample_ts_ms"] = 1704067200000
                break
        CACHE_INDEX.write_text(json.dumps(idx), encoding="utf-8")
        report = query("vm_grace_total", start, end)
        assert report["fresh_raw_within_grace"] is True
        assert report["served_from_cache"] is False
        assert report["rollup"]["value"] == pytest.approx(50.0)


def test_tf58d4d_ingest_missing_scrape_dir_fails():
    """Ingest must exit 1 when --scrape-dir is missing."""
    proc = _run(
        [
            "vmrollup",
            "ingest",
            "--config",
            str(CONFIG),
            "--db",
            str(DB),
        ]
    )
    assert proc.returncode != 0


def test_tf58d4d_tb3_scrape_dir_ingest_reference():
    """Ingest from /opt/tb3-probes must produce reference rollup for probe scrapes."""
    probe_dir = Path("/opt/tb3-probes")
    assert (probe_dir / "sample-counter.prom").is_file()
    ingest(probe_dir)
    snap = load_snapshot()
    row = find_series(snap, "vm_requests_total")
    assert row is not None
    _, ref_rate, start, end = reference_counter("vm_requests_total", probe_dir)
    assert row["window_start_ms"] == start
    assert row["window_end_ms"] == end
    assert row["rate_per_sec"] == pytest.approx(ref_rate)


@pytest.mark.parametrize(
    "fixture,metric",
    [
        ("hidden-reset.prom", "vm_hidden_reset_total"),
    ],
)
def test_tf58d4d_hidden_counter_reset_fixture(fixture: str, metric: str):
    """Hidden scrape at /opt/verifier-fixtures must pass reference counter rollup."""
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        scrape = Path(tmp)
        shutil.copy(HIDDEN / fixture, scrape / fixture)
        ingest(scrape)
        snap = load_snapshot()
        row = find_series(snap, metric)
        assert row is not None
        _, ref_rate, _, _ = reference_counter(metric, scrape)
        assert row["rate_per_sec"] == pytest.approx(ref_rate)


@pytest.mark.parametrize(
    "fixture,metric",
    [
        ("hidden-inf.prom", "vm_hidden_hist_seconds"),
    ],
)
def test_tf58d4d_hidden_histogram_inf_fixture(fixture: str, metric: str):
    """Hidden histogram scrape at /opt/verifier-fixtures must preserve +Inf bucket."""
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp:
        scrape = Path(tmp)
        shutil.copy(HIDDEN / fixture, scrape / fixture)
        ingest(scrape)
        snap = load_snapshot()
        shift_start, shift_end = align_window(1704067260000, INTERVAL_MS)
        row = find_series_window(snap, metric, shift_start, shift_end)
        assert row is not None
        ref_buckets = reference_hist_inf(metric, scrape, window_start_ms=shift_start)
        ref_inf = next(b for b in ref_buckets if b["le"] == "+Inf")
        got_inf = next(b for b in row["buckets"] if b["le"] == "+Inf")
        assert got_inf["count"] == pytest.approx(ref_inf["count"])


def test_tf58d4d_distinct_windows_distinct_cache_keys():
    """Cache index must keep separate keys per metric window per cache-ttl.md."""
    ingest()
    assert CACHE_INDEX.is_file()
    idx = json.loads(CACHE_INDEX.read_text(encoding="utf-8"))
    keys = [e["key"] for e in idx["entries"]]
    assert len(keys) == len(set(keys))
    vm_entries = [e for e in idx["entries"] if e["metric"] == "vm_requests_total"]
    assert len(vm_entries) >= 2
    windows = {(e["window_start_ms"], e["window_end_ms"]) for e in vm_entries}
    assert len(windows) >= 2


def test_tf58d4d_manifest_rollup_windows_positive():
    """Manifest rollup_windows_built must reflect built snapshot series."""
    ingest()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    snap = load_snapshot()
    assert manifest["rollup_windows_built"] == len(snap["series"])


def test_tf58d4d_query_report_fields():
    """Query report must include served_from_cache and fresh_raw_within_grace flags."""
    ingest()
    start, end = align_window(1704067200000, INTERVAL_MS)
    report = query("vm_requests_total", start, end)
    for key in ("metric", "served_from_cache", "fresh_raw_within_grace", "rollup"):
        assert key in report


def test_tf58d4d_query_writes_report_json():
    """Query must write /app/output/query-report.json per query-report.md."""
    ingest()
    start, end = align_window(1704067200000, INTERVAL_MS)
    query("vm_requests_total", start, end)
    assert QUERY_OUT.is_file()


def test_tf58d4d_cache_index_covers_each_raw_window():
    """Cache index must store one keyed entry per raw rollup window per cache-index.md."""
    ingest()
    snap = load_snapshot()
    idx = json.loads(CACHE_INDEX.read_text(encoding="utf-8"))
    raw_rows = [s for s in snap["series"] if s.get("tier") == "raw"]
    needed_keys = {expected_cache_key(row) for row in raw_rows}
    idx_keys = {e["key"] for e in idx["entries"]}
    assert needed_keys.issubset(idx_keys)


def test_tf58d4d_query_cache_ttl_uses_query_ms():
    """Cache TTL expiry must use --query-ms minus last_sample_ts_ms, not wall clock."""
    ingest()
    start, end = align_window(1704067200000, INTERVAL_MS)
    idx = json.loads(CACHE_INDEX.read_text(encoding="utf-8"))
    entry = next(e for e in idx["entries"] if e["metric"] == "vm_requests_total" and e["window_start_ms"] == start)
    query_ms = entry["last_sample_ts_ms"] + 200_000
    report = query("vm_requests_total", start, end, query_ms=query_ms)
    assert report["query_ms"] == query_ms
    assert report["served_from_cache"] is False


def test_tf58d4d_query_ms_defaults_to_generated_at_plus_offset():
    """Omitted --query-ms must echo generated_at_ms plus 1000 per cli-surface.md."""
    ingest()
    snap = load_snapshot()
    start, end = align_window(1704067200000, INTERVAL_MS)
    report = query("vm_requests_total", start, end)
    assert report["query_ms"] == snap["generated_at_ms"] + 1000
