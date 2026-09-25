"""Independent FIX drop-copy replay reference for verifier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def side_sign(side: str) -> int:
    return 1 if side == "1" else -1


def signed_qty(side: str, qty: float) -> int:
    return int(qty) * side_sign(side)


def replay_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    rows: dict[str, dict[str, Any]] = {}
    seq: dict[str, dict[str, Any]] = {}

    by_file: dict[str, list[dict[str, Any]]] = {}
    for ev in events:
        by_file.setdefault(ev["stream_file"], []).append(ev)

    for stream_file in sorted(by_file):
        batch_rows = {k: dict(v) for k, v in rows.items()}
        batch_seq = {k: dict(v) for k, v in seq.items()}
        try:
            for ev in by_file[stream_file]:
                if ev.get("reset_seq"):
                    batch_seq[ev["session"]] = {"last": 0, "allow_reset": True}
                    continue
                session = ev["session"]
                st = batch_seq.setdefault(session, {"last": 0, "allow_reset": False})
                msg_seq = ev["msg_seq"]
                if msg_seq <= st["last"] and not st.get("allow_reset"):
                    raise ValueError("sequence regression")
                exec_id = ev["exec_id"]
                if exec_id in batch_rows:
                    continue
                qty = signed_qty(ev["side"], ev["last_qty"])
                if ev.get("exec_type") == "H":
                    ref = next(
                        (r for r in batch_rows.values() if r["cl_ord_id"] == ev.get("orig_cl_ord_id") and r["active"]),
                        None,
                    )
                    if ref is None:
                        raise ValueError("missing bust reference")
                    qty = -ref["signed_qty"]
                if ev.get("exec_trans_type") == "2":
                    qty = signed_qty(ev["side"], ev["last_qty"])
                    orig = ev.get("orig_cl_ord_id", "")
                    for r in batch_rows.values():
                        if r.get("orig_cl_ord_id") == orig and r.get("exec_trans_type") == "1":
                            r["active"] = False
                if ev.get("exec_trans_type") == "1":
                    orig = ev.get("orig_cl_ord_id", "")
                    for r in batch_rows.values():
                        if r["cl_ord_id"] == orig:
                            r["active"] = False
                # Bust posts a reversing qty; original fill stays active so net zeros.
                batch_rows[exec_id] = {
                    "exec_id": exec_id,
                    "cl_ord_id": ev["cl_ord_id"],
                    "orig_cl_ord_id": ev.get("orig_cl_ord_id", ""),
                    "exec_trans_type": ev.get("exec_trans_type", "0"),
                    "exec_type": ev.get("exec_type", "0"),
                    "symbol": ev["symbol"],
                    "signed_qty": qty,
                    "active": True,
                    "sending_time": ev["sending_time"],
                    "stream_file": stream_file,
                }
                st["last"] = msg_seq
                st["allow_reset"] = False
                batch_seq[session] = st
        except ValueError:
            continue
        rows = batch_rows
        seq = batch_seq

    net: dict[str, int] = {}
    active_ids: list[str] = []
    bust = correct = cancel = 0
    for r in rows.values():
        if r["exec_type"] == "H":
            bust += 1
        if r["exec_trans_type"] == "2":
            correct += 1
        if r["exec_trans_type"] == "1":
            cancel += 1
        if r["active"]:
            net[r["symbol"]] = net.get(r["symbol"], 0) + r["signed_qty"]
            active_ids.append(r["exec_id"])
    active_ids.sort()
    payload = {"net_positions": net, "active_exec_ids": active_ids}
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "net_positions": net,
        "bust_count": bust,
        "correction_count": correct,
        "cancel_count": cancel,
        "active_exec_ids": active_ids,
        "audit_digest": digest,
    }


def load_staging_events(fixture_root: Path, scenario: str, seq_bias: int = 0) -> list[dict[str, Any]]:
    manifest = json.loads((fixture_root / "scenarios" / f"{scenario}.json").read_text(encoding="utf-8"))
    events: list[dict[str, Any]] = []
    for rel in manifest["streams"]:
        path = fixture_root / rel
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            row["msg_seq"] = row["msg_seq"] + seq_bias
            body = row["fix_body"].replace("|", "\x01")
            tags = {}
            for part in body.split("\x01"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    tags[k] = v
            if tags.get("35") == "A" and tags.get("141") == "Y":
                events.append(
                    {
                        "session": row["session"],
                        "msg_seq": row["msg_seq"],
                        "sending_time": row["sending_time"],
                        "reset_seq": True,
                        "stream_file": rel,
                    }
                )
                continue
            if tags.get("35") != "8":
                continue
            events.append(
                {
                    "session": row["session"],
                    "msg_seq": row["msg_seq"],
                    "sending_time": row["sending_time"],
                    "reset_seq": False,
                    "cl_ord_id": tags.get("11", ""),
                    "orig_cl_ord_id": tags.get("41", ""),
                    "exec_id": tags.get("17", ""),
                    "exec_trans_type": tags.get("20", "0"),
                    "exec_type": tags.get("150", "0"),
                    "symbol": tags.get("55", ""),
                    "side": tags.get("54", ""),
                    "last_qty": float(tags.get("32", "0")),
                    "stream_file": rel,
                }
            )
    events.sort(key=lambda e: (e["sending_time"], e["msg_seq"]))
    return events


def reference_compliance(fixture_root: Path, scenario: str, seq_bias: int = 0) -> dict[str, Any]:
    events = load_staging_events(fixture_root, scenario, seq_bias)
    out = replay_events(events)
    out["scenario"] = scenario
    out["replay_generation"] = 1
    return out
