"""North Sea AIS voyage leg atlas verifier."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

APP = Path("/app")
BIN = APP / "target" / "debug" / "aissegment"
STREAMS = Path("/app/fixtures/streams")
PORTS = Path("/app/fixtures/ports.geojson")
HIDDEN = Path("/opt/verifier-fixtures/ais")
STATE = Path("/app/state")
OUTPUT = Path("/app/output")
SNAPSHOT_PATH = Path("/app/state/track-snapshot.json")
ATLAS = Path("/app/output/voyage-atlas.json")

EARTH_RADIUS_NM = 3440.065


def _rebuild_binary() -> None:
    proc = subprocess.run(
        ["cargo", "build", "--locked", "-p", "aissegment"],
        cwd=str(APP),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "cargo build failed")


_rebuild_binary()

PROT_SHA: dict[str, str] = {}
HIDDEN_SHA: dict[str, str] = {}


def _policy() -> dict[str, float | int]:
    return {
        "mmsi_dedupe_sec": int(os.environ.get("AIS_MMSI_DEDUPE_SEC", "2")),
        "burst_ms": int(os.environ.get("AIS_BURST_MS", "500")),
        "max_sog_knots": float(os.environ.get("AIS_MAX_SOG_KNOTS", "45")),
        "draught_delta_m": float(os.environ.get("AIS_DRAUGHT_DELTA_M", "0.5")),
        "max_gap_hours": float(os.environ.get("AIS_MAX_GAP_HOURS", "12")),
    }


def round6(v: float) -> float:
    return round(v, 6)


def parse_ts_epoch(ts: str) -> int:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int((dt - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())


def epoch_to_rfc3339(epoch: int) -> str:
    dt = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=epoch)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def reference_parse_jsonl(raw: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        rows.append(
            {
                "seq": int(obj["seq"]),
                "mmsi": int(obj["mmsi"]),
                "ts_epoch": parse_ts_epoch(obj["ts"]),
                "lat": float(obj["lat"]),
                "lon": float(obj["lon"]),
                "sog": float(obj["sog"]),
                "draught": float(obj["draught"]),
                "station": str(obj["station"]),
            }
        )
    return rows


def reference_dedupe_mmsi(rows: list[dict[str, Any]], policy: dict[str, float | int]) -> tuple[list[dict[str, Any]], int]:
    kept: list[dict[str, Any]] = []
    removed = 0
    for row in rows:
        dup = False
        for existing in kept:
            if existing["mmsi"] != row["mmsi"]:
                continue
            if round6(existing["lat"]) != round6(row["lat"]) or round6(existing["lon"]) != round6(row["lon"]):
                continue
            if abs(existing["ts_epoch"] - row["ts_epoch"]) <= int(policy["mmsi_dedupe_sec"]):
                removed += 1
                dup = True
                break
        if not dup:
            kept.append(dict(row))
    return kept, removed


def reference_burst(rows: list[dict[str, Any]], policy: dict[str, float | int]) -> tuple[list[dict[str, Any]], int]:
    kept: list[dict[str, Any]] = []
    removed = 0
    for row in rows:
        dup = False
        for existing in kept:
            if existing["mmsi"] != row["mmsi"] or existing["station"] != row["station"]:
                continue
            dt_ms = abs(existing["ts_epoch"] - row["ts_epoch"]) * 1000
            if dt_ms > int(policy["burst_ms"]):
                continue
            if abs(existing["lat"] - row["lat"]) > 0.0001 or abs(existing["lon"] - row["lon"]) > 0.0001:
                continue
            removed += 1
            dup = True
            break
        if not dup:
            kept.append(dict(row))
    return kept, removed


def load_ports(path: Path) -> dict[str, list[tuple[float, float]]]:
    geo = json.loads(path.read_text())
    out: dict[str, list[tuple[float, float]]] = {}
    for feat in geo["features"]:
        name = feat["properties"]["name"]
        ring = feat["geometry"]["coordinates"][0]
        out[name] = [(lon, lat) for lon, lat in ring]
    return out


def on_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> bool:
    cross = (py - ay) * (bx - ax) - (px - ax) * (by - ay)
    if abs(cross) > 1e-9:
        return False
    dot = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
    if dot < 0:
        return False
    len_sq = (bx - ax) ** 2 + (by - ay) ** 2
    return dot <= len_sq + 1e-9


def point_in_polygon(lon: float, lat: float, ring: list[tuple[float, float]]) -> bool:
    inside = False
    n = len(ring)
    if n < 3:
        return False
    for i in range(n):
        j = 0 if i + 1 == n else i + 1
        xi, yi = ring[i]
        xj, yj = ring[j]
        if xi == xj and yi == yj:
            continue
        intersect = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / max(yj - yi, 1e-15) + xi
        )
        if intersect:
            inside = not inside
        if on_segment(lon, lat, xi, yi, xj, yj):
            return True
    return inside


def port_at(lat: float, lon: float, ports: dict[str, list[tuple[float, float]]]) -> str:
    in_rot = point_in_polygon(lon, lat, ports["rotterdam"])
    in_ham = point_in_polygon(lon, lat, ports["hamburg"])
    if in_rot:
        return "rotterdam"
    if in_ham:
        return "hamburg"
    return "none"


def haversine_nm(a: dict[str, Any], b: dict[str, Any]) -> float:
    lat1 = math.radians(a["lat"])
    lat2 = math.radians(b["lat"])
    dlat = math.radians(b["lat"] - a["lat"])
    dlon = math.radians(b["lon"] - a["lon"])
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_NM * math.asin(math.sqrt(h))


def reference_speed_filter(
    rows: list[dict[str, Any]], policy: dict[str, float | int]
) -> tuple[list[dict[str, Any]], int]:
    by_mmsi: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_mmsi.setdefault(row["mmsi"], []).append(dict(row))
    kept_all: list[dict[str, Any]] = []
    removed = 0
    for track in by_mmsi.values():
        track.sort(key=lambda r: (r["ts_epoch"], r["seq"]))
        kept: list[dict[str, Any]] = []
        for point in track:
            if not kept:
                kept.append(point)
                continue
            prev = kept[-1]
            hours = (point["ts_epoch"] - prev["ts_epoch"]) / 3600.0
            speed = 0.0 if hours <= 0 else haversine_nm(prev, point) / hours
            if speed > float(policy["max_sog_knots"]):
                removed += 1
                continue
            kept.append(point)
        kept_all.extend(kept)
    kept_all.sort(key=lambda r: (r["mmsi"], r["ts_epoch"], r["seq"]))
    return kept_all, removed


def count_out_of_order_before_sort(rows: list[dict[str, Any]]) -> int:
    sorted_rows = sorted(rows, key=lambda r: (r["mmsi"], r["ts_epoch"], r["seq"]))
    return sum(1 for a, b in zip(rows, sorted_rows, strict=True) if a["seq"] != b["seq"])


def reference_segment(
    points: list[dict[str, Any]],
    ports: dict[str, list[tuple[float, float]]],
    policy: dict[str, float | int],
    anomalies: dict[str, int],
) -> dict[str, Any]:
    by_mmsi: dict[int, list[dict[str, Any]]] = {}
    for p in points:
        by_mmsi.setdefault(p["mmsi"], []).append(p)
    legs: list[dict[str, Any]] = []
    for mmsi, track in sorted(by_mmsi.items()):
        track.sort(key=lambda r: (r["ts_epoch"], r["seq"]))
        ordinal = 1
        leg_points: list[dict[str, Any]] = []
        leg_start_draught = 0.0
        prev_port = "none"
        prev_ts = 0

        def flush(pts: list[dict[str, Any]], ord_num: int) -> None:
            if not pts:
                return
            start = pts[0]
            end = pts[-1]
            visited: list[str] = []
            for pt in pts:
                label = port_at(pt["lat"], pt["lon"], ports)
                if not visited or visited[-1] != label:
                    visited.append(label)
            legs.append(
                {
                    "leg_id": f"{mmsi}-L{ord_num}",
                    "mmsi": mmsi,
                    "start_ts": epoch_to_rfc3339(start["ts_epoch"]),
                    "end_ts": epoch_to_rfc3339(end["ts_epoch"]),
                    "point_count": len(pts),
                    "start_port": port_at(start["lat"], start["lon"], ports),
                    "end_port": port_at(end["lat"], end["lon"], ports),
                    "ports": visited,
                }
            )

        for idx, point in enumerate(track):
            port = port_at(point["lat"], point["lon"], ports)
            if idx == 0:
                leg_start_draught = point["draught"]
                prev_port = port
                prev_ts = point["ts_epoch"]
                leg_points.append(point)
                continue
            split = False
            if port != prev_port:
                split = True
            if abs(point["draught"] - leg_start_draught) >= float(policy["draught_delta_m"]):
                split = True
            gap_hours = (point["ts_epoch"] - prev_ts) / 3600.0
            if gap_hours > float(policy["max_gap_hours"]):
                split = True
            if split:
                flush(leg_points, ordinal)
                ordinal += 1
                leg_points = [point]
                leg_start_draught = point["draught"]
            else:
                leg_points.append(point)
            prev_port = port
            prev_ts = point["ts_epoch"]
        flush(leg_points, ordinal)
    legs.sort(key=lambda leg: (leg["mmsi"], leg["leg_id"]))
    digest = hashlib.sha256(",".join(leg["leg_id"] for leg in legs).encode()).hexdigest()
    return {"voyage_legs": legs, "anomalies": anomalies, "leg_chain_digest": digest}


def reference_pipeline(stream_path: Path, ports_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    policy = _policy()
    raw_rows = reference_parse_jsonl(stream_path.read_text())
    raw_count = len(raw_rows)
    after_mmsi, dup = reference_dedupe_mmsi(raw_rows, policy)
    after_burst, burst = reference_burst(after_mmsi, policy)
    out_of_order = count_out_of_order_before_sort(after_burst)
    snap_points = sorted(after_burst, key=lambda r: (r["mmsi"], r["ts_epoch"], r["seq"]))
    snapshot = {
        "source": str(stream_path),
        "points": snap_points,
        "feed_stats": {
            "raw_rows": raw_count,
            "after_mmsi_dedupe": raw_count - dup,
            "after_burst": raw_count - dup - burst,
            "out_of_order": out_of_order,
        },
    }
    ports = load_ports(ports_path)
    filtered, impossible = reference_speed_filter(snap_points, policy)
    anomalies = {
        "impossible_speed": impossible,
        "duplicate_mmsi": dup,
        "burst_duplicate": burst,
        "out_of_order": out_of_order,
    }
    atlas = reference_segment(filtered, ports, policy, anomalies)
    return snapshot, atlas


def _run_cli(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [str(BIN), *args],
        capture_output=True,
        text=True,
        env=merged,
        check=False,
    )


def _reset_state() -> None:
    for path in (SNAPSHOT_PATH, ATLAS):
        if path.exists():
            path.unlink()
    if STATE.exists():
        for child in STATE.iterdir():
            if child.is_file():
                child.unlink()


def _feed_atlas(stream: Path, env: dict[str, str] | None = None) -> None:
    _reset_state()
    STATE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rc_i = _run_cli(
        [
            "feed",
            "--input",
            str(stream),
            "--snapshot",
            str(SNAPSHOT_PATH),
            "--ports",
            str(PORTS),
        ],
        env=env,
    )
    assert rc_i.returncode == 0, rc_i.stderr
    rc_e = _run_cli(
        [
            "atlas",
            "--output",
            str(ATLAS),
            "--snapshot",
            str(SNAPSHOT_PATH),
            "--ports",
            str(PORTS),
        ],
        env=env,
    )
    assert rc_e.returncode == 0, rc_e.stderr


def _load_hashes() -> None:
    global PROT_SHA, HIDDEN_SHA
    if PROT_SHA:
        return
    for path in sorted(STREAMS.glob("*.jsonl")):
        PROT_SHA[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    hidden_name = "006-edge-port-jitter.jsonl"
    hidden_path = HIDDEN / hidden_name
    if hidden_path.is_file():
        HIDDEN_SHA[hidden_name] = hashlib.sha256(hidden_path.read_bytes()).hexdigest()


__all__ = [
    "APP",
    "ATLAS",
    "BIN",
    "EARTH_RADIUS_NM",
    "HIDDEN",
    "HIDDEN_SHA",
    "OUTPUT",
    "PORTS",
    "PROT_SHA",
    "STATE",
    "SNAPSHOT_PATH",
    "STREAMS",
    "hashlib",
    "json",
    "Path",
    "_feed_atlas",
    "_load_hashes",
    "_reset_state",
    "_run_cli",
]
