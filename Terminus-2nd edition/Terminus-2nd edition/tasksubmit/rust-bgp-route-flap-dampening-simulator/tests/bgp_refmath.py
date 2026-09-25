"""Independent BGP dampening reference for rdampctl verifier."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any


def fixture_root() -> Path:
    return Path(os.environ.get("TB3_FIXTURE_DIR", "/app/fixtures"))


def half_life_bias() -> int:
    return int(os.environ.get("TB3_HALF_LIFE_BIAS", "0"))


def reference_compile_lock(root: Path, scenario_id: str) -> dict[str, Any]:
    spec = json.loads((root / "scenarios" / f"{scenario_id}.json").read_text(encoding="utf-8"))
    raw = (root / spec["feed_path"]).read_bytes()
    events = parse_feed(raw)
    assert_peer_monotonic(events)
    events = dedupe(events)
    sort_feed(events)
    peer_table = load_peer_table(root, spec["peers"])
    return {
        "scenario_id": scenario_id,
        "feed_fingerprint": feed_fingerprint(raw),
        "feed_relpath": spec["feed_path"],
        "line_count": len(events),
        "peer_table": peer_table,
        "_events": events,
    }


def parse_feed(raw: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def assert_peer_monotonic(events: list[dict[str, Any]]) -> None:
    last: dict[str, int] = {}
    for ev in events:
        if ev["ts_ms"] < last.get(ev["peer"], 0):
            raise ValueError(f"peer {ev['peer']} ts regression")
        last[ev["peer"]] = ev["ts_ms"]


def dedupe(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    for ev in events:
        key = (ev["ts_ms"], ev["peer"], ev["prefix"], ev["kind"])
        if key in seen:
            continue
        seen.add(key)
        out.append(ev)
    return out


def sort_feed(events: list[dict[str, Any]]) -> None:
    events.sort(key=lambda ev: (ev["ts_ms"], ev["peer"], ev["prefix"], 0 if ev["kind"] == "announce" else 1))


def feed_fingerprint(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_peer_table(root: Path, peers: list[str]) -> dict[str, dict[str, Any]]:
    bias = half_life_bias()
    out: dict[str, dict[str, Any]] = {}
    for peer in peers:
        path = root / "policies" / f"{peer}.json"
        row = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else fallback_peer(peer)
        row = dict(row)
        if bias:
            row["half_life_ms"] = max(1, int(row["half_life_ms"]) + bias)
        if row["reuse_threshold"] * 2 >= row["suppress_threshold"]:
            raise ValueError(f"invalid reuse for peer {peer}")
        out[peer] = row
    return out


def fallback_peer(peer_id: str) -> dict[str, Any]:
    return {
        "peer_id": peer_id,
        "suppress_threshold": 2000,
        "reuse_threshold": 750,
        "half_life_ms": 300_000,
        "flap_penalty": 1000,
        "max_penalty": 16000,
    }


def apply_decay(penalty: int, last_ts_ms: int, now_ms: int, half_life_ms: int) -> int:
    if now_ms <= last_ts_ms or half_life_ms == 0:
        return penalty
    delta = now_ms - last_ts_ms
    factor = 0.5 ** (delta / half_life_ms)
    return math.floor(penalty * factor)


def drive_lock(lock: dict[str, Any]) -> dict[str, Any]:
    entries: dict[str, dict[str, Any]] = {}
    for ev in lock["_events"]:
        key = f"{ev['peer']}:{ev['prefix']}"
        pol = lock["peer_table"][ev["peer"]]
        slot = entries.setdefault(
            key,
            {
                "penalty": 0,
                "advertised": False,
                "suppressed": False,
                "flap_count": 0,
                "peak_penalty": 0,
                "last_ts_ms": 0,
                "stable_at_ms": None,
            },
        )
        slot["penalty"] = apply_decay(slot["penalty"], slot["last_ts_ms"], ev["ts_ms"], pol["half_life_ms"])
        slot["last_ts_ms"] = ev["ts_ms"]
        if ev["kind"] == "announce":
            if slot["advertised"] or (slot["suppressed"] and slot["penalty"] >= pol["reuse_threshold"]):
                pass
            else:
                slot["advertised"] = True
                if slot["penalty"] >= pol["suppress_threshold"]:
                    slot["suppressed"] = True
        elif ev["kind"] == "withdraw" and slot["advertised"]:
            slot["advertised"] = False
            slot["penalty"] = min(pol["max_penalty"], slot["penalty"] + pol["flap_penalty"])
            slot["flap_count"] += 1
            if slot["penalty"] >= pol["suppress_threshold"]:
                slot["suppressed"] = True
        slot["peak_penalty"] = max(slot["peak_penalty"], slot["penalty"])
        if not slot["advertised"] and slot["penalty"] < pol["reuse_threshold"] and slot["stable_at_ms"] is None:
            slot["stable_at_ms"] = ev["ts_ms"]
    return {"entries": entries}


def suppression_lines(lock: dict[str, Any], ledger: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, slot in ledger["entries"].items():
        peer, prefix = key.split(":", 1)
        pol = lock["peer_table"][peer]
        if slot["flap_count"] == 0 and not slot["suppressed"] and slot["peak_penalty"] < pol["reuse_threshold"]:
            continue
        rows.append(
            {
                "peer_id": peer,
                "prefix": prefix,
                "final_penalty": slot["penalty"],
                "suppressed": slot["suppressed"],
                "flap_count": slot["flap_count"],
                "peak_penalty": slot["peak_penalty"],
                "stable_at_ms": slot["stable_at_ms"],
            }
        )
    rows.sort(key=lambda r: (r["peer_id"], r["prefix"]))
    return rows


def reference_pipeline(root: Path, scenario_id: str) -> dict[str, Any]:
    lock = reference_compile_lock(root, scenario_id)
    ledger = drive_lock(lock)
    rows = suppression_lines(lock, ledger)
    return {"lock": lock, "ledger": ledger, "rows": rows}


def ms_to_reuse(penalty_now: int, reuse_threshold: int, half_life_ms: int) -> int:
    if half_life_ms == 0:
        raise ValueError("half_life_ms must be non-zero")
    if penalty_now < reuse_threshold:
        return 0
    lo = 0
    hi = max(1, half_life_ms * penalty_now + 1)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        nxt = (penalty_now * half_life_ms) // (half_life_ms + mid)
        if nxt < reuse_threshold:
            hi = mid
        else:
            lo = mid + 1
    return lo


def slot_digest(
    peer_id: str,
    prefix: str,
    penalty_now: int,
    reuse_threshold: int,
    ms: int,
    forecast_anchor_ms: int,
) -> str:
    preimage = f"{peer_id}|{prefix}|{penalty_now}|{reuse_threshold}|{ms}|{forecast_anchor_ms}"
    return hashlib.sha256(preimage.encode("utf-8")).hexdigest()


def reference_reuse_forecast(root: Path, scenario_id: str) -> list[dict[str, Any]]:
    pipe = reference_pipeline(root, scenario_id)
    lock = pipe["lock"]
    ledger = pipe["ledger"]
    rows: list[dict[str, Any]] = []
    for key, slot in ledger["entries"].items():
        peer, prefix = key.split(":", 1)
        pol = lock["peer_table"][peer]
        if not (slot["suppressed"] or slot["peak_penalty"] >= pol["reuse_threshold"]):
            continue
        ms = ms_to_reuse(slot["penalty"], pol["reuse_threshold"], pol["half_life_ms"])
        epoch = slot["last_ts_ms"]
        rows.append(
            {
                "peer_id": peer,
                "prefix": prefix,
                "penalty_now": slot["penalty"],
                "reuse_threshold": pol["reuse_threshold"],
                "half_life_ms": pol["half_life_ms"],
                "ms_to_reuse": ms,
                "forecast_anchor_ms": epoch,
                "slot_digest": slot_digest(
                    peer, prefix, slot["penalty"], pol["reuse_threshold"], ms, epoch
                ),
            }
        )
    rows.sort(key=lambda r: (r["peer_id"], r["prefix"]))
    return rows
