#!/usr/bin/env python3
"""Generate deterministic AIS JSONL fixtures and ports.geojson for aissegment."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STREAMS = ROOT / "streams"
HIDDEN = ROOT / "hidden"


def ts(epoch: int) -> str:
    """Format fixed UTC epoch labels for tests."""
    # 2024-01-15 12:00:00 UTC + epoch offset seconds
    base = 1705320000
    dt = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=base + epoch)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, separators=(",", ":")) + "\n")


def round_coord(v: float) -> float:
    return math.floor(v * 1_000_000) / 1_000_000


def stream_fingerprint(rows: list[dict]) -> str:
    payload = json.dumps(rows, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def build_ports() -> None:
    geo = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "rotterdam"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [4.00, 51.85],
                            [4.50, 51.85],
                            [4.50, 51.95],
                            [4.00, 51.95],
                            [4.00, 51.85],
                        ]
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {"name": "hamburg"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [9.90, 53.50],
                            [10.05, 53.50],
                            [10.05, 53.60],
                            [9.90, 53.60],
                            [9.90, 53.50],
                        ]
                    ],
                },
            },
        ],
    }
    (ROOT / "ports.geojson").write_text(json.dumps(geo, indent=2) + "\n", encoding="utf-8")


def fixture_001() -> None:
    """Open sea approach then rotterdam port entry — two legs."""
    rows = [
        {"seq": 0, "mmsi": 244000001, "ts": ts(0), "lat": 51.50, "lon": 3.50, "sog": 12.0, "draught": 8.0, "station": "BS-A"},
        {"seq": 1, "mmsi": 244000001, "ts": ts(3600), "lat": 51.88, "lon": 4.10, "sog": 10.0, "draught": 8.0, "station": "BS-A"},
        {"seq": 2, "mmsi": 244000001, "ts": ts(7200), "lat": 51.90, "lon": 4.20, "sog": 5.0, "draught": 8.0, "station": "BS-B"},
    ]
    write_jsonl(STREAMS / "001-port-entry.jsonl", rows)


def fixture_002() -> None:
    """MMSI dedupe — duplicate coords within 2 sec."""
    rows = [
        {"seq": 0, "mmsi": 244000002, "ts": ts(0), "lat": 52.00, "lon": 3.00, "sog": 8.0, "draught": 7.5, "station": "BS-X"},
        {"seq": 1, "mmsi": 244000002, "ts": ts(1), "lat": 52.0000004, "lon": 3.0000004, "sog": 9.0, "draught": 7.5, "station": "BS-Y"},
        {"seq": 2, "mmsi": 244000002, "ts": ts(3600), "lat": 52.01, "lon": 3.01, "sog": 8.0, "draught": 7.5, "station": "BS-X"},
    ]
    write_jsonl(STREAMS / "002-mmsi-dedupe.jsonl", rows)


def fixture_003() -> None:
    """Impossible speed teleport."""
    rows = [
        {"seq": 0, "mmsi": 244000003, "ts": ts(0), "lat": 50.0, "lon": 2.0, "sog": 10.0, "draught": 6.0, "station": "BS-1"},
        {"seq": 1, "mmsi": 244000003, "ts": ts(60), "lat": 55.0, "lon": 8.0, "sog": 10.0, "draught": 6.0, "station": "BS-1"},
        {"seq": 2, "mmsi": 244000003, "ts": ts(7200), "lat": 55.01, "lon": 8.01, "sog": 9.0, "draught": 6.0, "station": "BS-1"},
    ]
    write_jsonl(STREAMS / "003-speed-anomaly.jsonl", rows)


def fixture_004() -> None:
    """Draught change splits leg without port change."""
    rows = [
        {"seq": 0, "mmsi": 244000004, "ts": ts(0), "lat": 51.80, "lon": 3.50, "sog": 11.0, "draught": 8.0, "station": "BS-D"},
        {"seq": 1, "mmsi": 244000004, "ts": ts(1800), "lat": 51.82, "lon": 3.52, "sog": 11.0, "draught": 8.6, "station": "BS-D"},
        {"seq": 2, "mmsi": 244000004, "ts": ts(3600), "lat": 51.84, "lon": 3.54, "sog": 10.0, "draught": 8.6, "station": "BS-D"},
    ]
    write_jsonl(STREAMS / "004-draught-boundary.jsonl", rows)


def fixture_005() -> None:
    """Base station burst duplicates."""
    rows = [
        {"seq": 0, "mmsi": 244000005, "ts": ts(0), "lat": 52.10, "lon": 3.20, "sog": 7.0, "draught": 5.0, "station": "BS-R"},
        {"seq": 1, "mmsi": 244000005, "ts": ts(0), "lat": 52.10001, "lon": 3.20001, "sog": 7.1, "draught": 5.0, "station": "BS-R"},
        {"seq": 2, "mmsi": 244000005, "ts": ts(600), "lat": 52.11, "lon": 3.21, "sog": 7.0, "draught": 5.0, "station": "BS-R"},
    ]
    write_jsonl(STREAMS / "005-burst-dedupe.jsonl", rows)


def fixture_006_hidden() -> None:
    """Edge port boundary + out-of-order seq with jittered epoch labels."""
    rows = [
        {"seq": 2, "mmsi": 244000006, "ts": ts(10), "lat": 51.85, "lon": 4.00, "sog": 4.0, "draught": 9.0, "station": "BS-H"},
        {"seq": 0, "mmsi": 244000006, "ts": ts(0), "lat": 51.84, "lon": 3.99, "sog": 5.0, "draught": 9.0, "station": "BS-H"},
        {"seq": 1, "mmsi": 244000006, "ts": ts(5), "lat": 51.850001, "lon": 4.000001, "sog": 4.5, "draught": 9.0, "station": "BS-H"},
        {"seq": 3, "mmsi": 244000006, "ts": ts(3600), "lat": 51.90, "lon": 4.15, "sog": 6.0, "draught": 9.0, "station": "BS-H"},
    ]
    write_jsonl(HIDDEN / "006-edge-port-jitter.jsonl", rows)


def main() -> None:
    build_ports()
    fixture_001()
    fixture_002()
    fixture_003()
    fixture_004()
    fixture_005()
    fixture_006_hidden()
    print(f"ais fixtures ready ({stream_fingerprint([{'seq': 0}])[:8]})")


if __name__ == "__main__":
    main()
