"""Independent reference for promingest remote-write payloads and snapshots."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

APP = Path("/app")
PROMENC = "/usr/local/bin/promenc"
LE_CATALOG = json.loads((APP / "fixtures" / "le-catalog.json").read_text(encoding="utf-8"))
BOUNDS = LE_CATALOG["bounds"]


def fnv1a64(seed: str) -> int:
    h = 0xCBF29CE484222325
    for b in seed.encode("utf-8"):
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def trace_id(seed: str, le: str) -> str:
    return f"trace-{fnv1a64(seed + ':' + le):016x}"


def build_write_request(seed: str) -> dict:
    n = fnv1a64(seed)
    bounds = BOUNDS
    if seed.startswith("rw-hidden-"):
        bounds = ["0.05", "0.5", "2.5", "+Inf"]
    buckets = []
    exemplars = []
    for i, le in enumerate(bounds):
        buckets.append({"le": le, "count": (n >> (i * 4)) & 0xFF})
        if le != "+Inf":
            exemplars.append({"le": le, "trace_id": trace_id(seed, le), "value": 1.0})
    if seed.startswith("rw-hidden-"):
        exemplars.reverse()
    wrong_name = "wrong_metric" if (n % 2) == 0 else "http_latency_bucket"
    series = [
        {
            "labels": [
                {"name": "__name__", "value": "http_latency_bucket"},
                {"name": "job", "value": f"svc-{seed}"},
                {"name": "__name__", "value": wrong_name},
                {"name": "seed", "value": seed},
            ],
            "histogram_schema": 2,
            "counter_reset": False,
            "buckets": buckets,
            "exemplars": exemplars,
        },
        {
            "labels": [
                {"name": "__name__", "value": "http_errors_total"},
                {"name": "seed", "value": seed},
            ],
            "histogram_schema": 0,
            "counter_reset": True,
            "buckets": [{"le": "+Inf", "count": 3}],
            "exemplars": [{"le": "+Inf", "trace_id": trace_id(seed, "stale"), "value": 2.0}],
        },
    ]
    return {"seed": seed, "series": series}


def encode_block(req: dict, *, bad_crc: bool = False) -> bytes:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(req, fh)
        path = fh.name
    try:
        cmd = [PROMENC]
        if bad_crc:
            cmd.append("--bad-crc")
        cmd.append(path)
        proc = subprocess.run(cmd, capture_output=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.decode() or proc.stdout.decode())
        return proc.stdout
    finally:
        Path(path).unlink(missing_ok=True)


def expected_snapshot(seed: str, *, sequence: int = 1) -> dict:
    req = build_write_request(seed)
    series_out = []
    for raw in req["series"]:
        labels: dict[str, str] = {}
        for pair in raw["labels"]:
            name = pair["name"]
            if name == "__name__" and "__name__" in labels:
                continue
            labels[name] = pair["value"]
        buckets = []
        for bucket in raw["buckets"]:
            entry = {"le": bucket["le"], "count": bucket["count"]}
            if not raw["counter_reset"]:
                for ex in raw["exemplars"]:
                    if ex["le"] == bucket["le"]:
                        entry["exemplar_trace_id"] = ex["trace_id"]
            buckets.append(entry)
        schema = raw["histogram_schema"]
        schema = min(2, schema)
        series_out.append(
            {
                "labels": labels,
                "histogram_schema": schema,
                "buckets": buckets,
            }
        )
    series_out.sort(key=lambda s: (s["labels"].get("__name__", ""), s["labels"].get("le", "")))
    return {"seed": seed, "sequence": sequence, "series": series_out}


def expected_staging_record(seed: str, *, sequence: int = 1) -> dict:
    req = build_write_request(seed)
    return {"seed": seed, "sequence": sequence, "series": req["series"]}
