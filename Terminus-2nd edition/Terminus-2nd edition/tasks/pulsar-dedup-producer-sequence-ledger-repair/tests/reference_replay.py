"""Independent reference for pulsar-dedup-replay export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def stream_key(producer: str, topic: str) -> str:
    return f"{producer}|{topic}"


def empty_stream(epoch: int) -> dict[str, Any]:
    return {
        "epoch": epoch,
        "high_water": 0,
        "broker_acked_max": 0,
        "dedup_miss": 0,
        "duplicate_replay": 0,
        "accepted_count": 0,
    }


def reference_replay(scenario: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    window = int(scenario["dedup_window"])
    streams: dict[str, dict[str, Any]] = {}
    seen_msg: dict[str, set[str]] = {}
    seen_seq: dict[str, set[int]] = {}

    for ev in scenario["events"]:
        key = stream_key(ev["producer"], ev["topic"])
        if key not in streams:
            streams[key] = empty_stream(int(ev["epoch"]))
            seen_msg[key] = set()
            seen_seq[key] = set()
        st = streams[key]

        seq = int(ev["sequence"])
        epoch = int(ev["epoch"])
        msg_id = str(ev["msg_id"])
        broker_ack = bool(ev.get("broker_ack", True))

        if seq < st["high_water"]:
            if epoch <= st["epoch"]:
                st["dedup_miss"] += 1
                continue
            st["epoch"] = epoch
            st["high_water"] = 0
            st["broker_acked_max"] = 0
            seen_msg[key] = set()
            seen_seq[key] = set()

        if msg_id in seen_msg[key]:
            st["duplicate_replay"] += 1
            continue

        if seq in seen_seq[key]:
            st["dedup_miss"] += 1
            continue

        if seq < st["high_water"] and (st["high_water"] - seq) > window:
            st["dedup_miss"] += 1
            continue

        if not broker_ack:
            st["dedup_miss"] += 1
            continue

        st["accepted_count"] += 1
        seen_msg[key].add(msg_id)
        seen_seq[key].add(seq)
        if seq > st["high_water"]:
            st["high_water"] = seq
        if seq > st["broker_acked_max"]:
            st["broker_acked_max"] = seq

    snap = {
        "tenant": scenario["tenant"],
        "streams": streams,
        "staging_written": True,
        "export_before_ack": False,
    }
    barrier_ok = all(
        st["high_water"] <= st["broker_acked_max"] for st in streams.values()
    )
    report = {
        "tenant": scenario["tenant"],
        "streams": streams,
        "export_barrier_ok": barrier_ok,
    }
    return snap, report


def reference_export(scenario_path: Path) -> dict[str, Any]:
    sc = json.loads(scenario_path.read_text(encoding="utf-8"))
    _, report = reference_replay(sc)
    return report


def reference_snapshot(scenario_path: Path) -> dict[str, Any]:
    sc = json.loads(scenario_path.read_text(encoding="utf-8"))
    snap, _ = reference_replay(sc)
    return snap
