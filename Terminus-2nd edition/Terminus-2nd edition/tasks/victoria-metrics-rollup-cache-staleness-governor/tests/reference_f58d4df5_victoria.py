"""Independent reference math for vmrollup verifier tests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

INTERVAL_MS = 60_000


def align_window(ts_ms: int, interval_ms: int) -> tuple[int, int]:
    start = (ts_ms // interval_ms) * interval_ms
    return start, start + interval_ms


@dataclass(frozen=True)
class Sample:
    value: float
    ts_ms: int
    scrape_order: int


_LINE = re.compile(
    r"^(?P<name>[a-zA-Z_:][a-zA-Z0-9_:]*)(?P<labels>\{[^}]*\})?\s+"
    r"(?P<value>[-+0-9.eE]+)(?:\s+(?P<ts>\d+))?\s*$"
)


def _parse_prom_files(scrape_dir: Path) -> list[tuple[int, str, str, float, int]]:
    rows: list[tuple[int, str, str, float, int]] = []
    files = sorted(scrape_dir.glob("*.prom"))
    for order, path in enumerate(files):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = _LINE.match(line)
            if not match:
                continue
            name = match.group("name")
            labels = match.group("labels") or ""
            value = float(match.group("value"))
            ts_ms = int(match.group("ts")) if match.group("ts") else 0
            rows.append((order, name, labels, value, ts_ms))
    return rows


def _counter_samples(metric: str, scrape_dir: Path) -> list[Sample]:
    out: list[Sample] = []
    for order, name, _labels, value, ts_ms in _parse_prom_files(scrape_dir):
        if name == metric:
            out.append(Sample(value=value, ts_ms=ts_ms, scrape_order=order))
    out.sort(key=lambda s: (s.scrape_order, s.ts_ms))
    return out


def _histogram_bucket_samples(metric: str, scrape_dir: Path) -> list[tuple[int, str, float, int]]:
    prefix = f"{metric}_bucket"
    rows: list[tuple[int, str, float, int]] = []
    for order, name, labels, value, ts_ms in _parse_prom_files(scrape_dir):
        if name != prefix:
            continue
        match = re.search(r'le="([^"]*)"', labels)
        if not match:
            continue
        rows.append((order, match.group(1), value, ts_ms))
    rows.sort(key=lambda r: (r[0], r[3]))
    return rows


def _compute_rate(samples: list[Sample], window_sec: float) -> tuple[float, float]:
    if not samples:
        return 0.0, 0.0
    baseline = samples[0].value
    prev = samples[0].value
    for sample in samples[1:]:
        if sample.value < prev:
            baseline = sample.value
        prev = sample.value
    last = samples[-1].value
    delta = last - baseline
    if delta < 0:
        delta = 0.0
    rate = delta / window_sec if window_sec > 0 else 0.0
    return last, rate


def _pick_window(samples: list[Sample], interval_ms: int) -> tuple[int, int, list[Sample]]:
    grouped: dict[int, list[Sample]] = {}
    for sample in samples:
        start, _ = align_window(sample.ts_ms, interval_ms)
        grouped.setdefault(start, []).append(sample)
    start = min(grouped, key=lambda ws: ws)
    end = start + interval_ms
    window_samples = sorted(grouped[start], key=lambda s: (s.scrape_order, s.ts_ms))
    return start, end, window_samples


def reference_counter(metric: str, scrape_dir: Path) -> tuple[float, float, int, int]:
    samples = _counter_samples(metric, scrape_dir)
    if not samples:
        raise ValueError(f"no counter samples for {metric} under {scrape_dir}")
    start, end, window_samples = _pick_window(samples, INTERVAL_MS)
    last, rate = _compute_rate(window_samples, INTERVAL_MS / 1000.0)
    return last, rate, start, end


def reference_hist_inf(
    metric: str, scrape_dir: Path, *, window_start_ms: int | None = None
) -> list[dict[str, float | str]]:
    rows = _histogram_bucket_samples(metric, scrape_dir)
    if not rows:
        raise ValueError(f"no histogram buckets for {metric} under {scrape_dir}")

    by_window: dict[int, dict[str, float]] = {}
    for order, le, value, ts_ms in rows:
        start, _ = align_window(ts_ms, INTERVAL_MS)
        bucket_map = by_window.setdefault(start, {})
        bucket_map[le] = value

    if window_start_ms is None:
        window_start_ms = max(by_window)
    bucket_map = by_window.get(window_start_ms, {})
    return [{"le": le, "count": count} for le, count in sorted(bucket_map.items(), key=lambda x: x[0])]
