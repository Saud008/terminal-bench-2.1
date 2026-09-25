"""Milestone 1 — pending_log visibility after XACK during journal replay."""

from __future__ import annotations

import json
import os
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any

CLI = "/app/bin/redisctl"
STAGE = Path("/app/state/redis-stream-stage.json")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return sorted(rows, key=lambda r: r["seq"])


def reference_stream_state_machine(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Independent replay for pending_log and PEL visibility."""
    pending_log: list[dict[str, Any]] = []
    streams: dict[str, dict[str, Any]] = {}
    reads_waiting_ack: dict[str, dict[str, Any]] = {}

    def pel_key(stream: str, group: str, mid: str) -> str:
        return f"{stream}|{group}|{mid}"

    for ev in sorted(events, key=lambda e: e["seq"]):
        op = ev["op"]
        if op == "XADD":
            st = streams.setdefault(ev["stream"], {"entries": [], "groups": {}})
            mid = ev.get("id") or f"{ev['timestamp_ms']}-{len(st['entries'])}"
            st["entries"].append({"id": mid, "fields": ev.get("fields", {})})
        elif op == "XGROUP" and ev.get("sub") == "CREATE":
            st = streams.setdefault(ev["stream"], {"entries": [], "groups": {}})
            groups = st["groups"]
            gid = ev["group"]
            start = ev.get("id", "0-0")
            if start == "$":
                start = st["entries"][-1]["id"] if st["entries"] else "0-0"
            groups.setdefault(gid, {"last_id": start, "pending": {}})
        elif op == "XREADGROUP":
            st = streams.setdefault(ev["stream"], {"entries": [], "groups": {}})
            grp = st["groups"].setdefault(ev["group"], {"last_id": "0-0", "pending": {}})
            for mid in ev["ids"]:
                grp["pending"][mid] = {
                    "consumer": ev["consumer"],
                    "delivery_count": grp["pending"].get(mid, {}).get("delivery_count", 0) + 1,
                    "idle_ms": ev["timestamp_ms"],
                }
                reads_waiting_ack[pel_key(ev["stream"], ev["group"], mid)] = {
                    "stream": ev["stream"],
                    "group": ev["group"],
                    "consumer": ev["consumer"],
                    "message_id": mid,
                    "read_seq": ev["seq"],
                }
        elif op == "XACK":
            st = streams[ev["stream"]]
            grp = st["groups"][ev["group"]]
            for mid in ev["ids"]:
                key = pel_key(ev["stream"], ev["group"], mid)
                meta = reads_waiting_ack.pop(key, None)
                if meta:
                    pending_log.append(
                        {
                            "seq": meta["read_seq"],
                            "stream": ev["stream"],
                            "group": ev["group"],
                            "consumer": meta["consumer"],
                            "message_id": mid,
                            "ack_seq": ev["seq"],
                        }
                    )
                grp["pending"].pop(mid, None)
    return {"pending_log": pending_log, "streams": streams, "last_applied_seq": events[-1]["seq"] if events else 0}


def run_replay(journal: Path) -> None:
    if STAGE.exists():
        STAGE.unlink()
    proc = subprocess.run([CLI, "replay", str(journal)], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr + proc.stdout


def load_stage() -> dict[str, Any]:
    return json.loads(STAGE.read_text(encoding="utf-8"))


def apply_tb3_prefix(events: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    out = deepcopy(events)
    for ev in out:
        if "stream" in ev:
            ev["stream"] = f"{prefix}{ev['stream']}"
    return out


class TestMilestone1:
    """Pending advance visibility gated on XACK journal lines."""

    def test_replay_writes_stage_snapshot(self) -> None:
        """Replay must materialize /app/state/redis-stream-stage.json."""
        journal = Path("/app/data/m1_ack_order.jsonl")
        run_replay(journal)
        assert STAGE.is_file()

    def test_pending_log_matches_reference_order(self) -> None:
        """pending_log rows must match the reference state machine."""
        journal = Path("/app/data/m1_ack_order.jsonl")
        events = _load_jsonl(journal)
        run_replay(journal)
        stage = load_stage()
        ref = reference_stream_state_machine(events)
        assert stage["pending_log"] == ref["pending_log"]

    def test_ack_seq_not_read_seq(self) -> None:
        """ack_seq must reference the XACK journal line, not XREADGROUP."""
        journal = Path("/app/data/m1_ack_order.jsonl")
        run_replay(journal)
        stage = load_stage()
        assert stage["pending_log"]
        row = stage["pending_log"][0]
        assert row["ack_seq"] == 3
        assert row["seq"] == 2

    def test_no_pending_log_before_ack_replayed(self) -> None:
        """Simulated partial replay must not emit pending_log before XACK."""
        events = _load_jsonl(Path("/app/data/m1_ack_order.jsonl"))
        partial = [e for e in events if e["seq"] <= 2]
        ref = reference_stream_state_machine(partial)
        assert ref["pending_log"] == []

    def test_subprocess_cli_rebuild_path(self) -> None:
        """redisctl replay must be invoked via subprocess CLI."""
        proc = subprocess.run(["test", "-x", CLI], capture_output=True, text=True)
        assert proc.returncode == 0

    def test_last_applied_seq_persisted(self) -> None:
        """Stage snapshot records last applied journal seq."""
        journal = Path("/app/data/m1_ack_order.jsonl")
        run_replay(journal)
        stage = load_stage()
        assert stage["last_applied_seq"] == 3

    def test_tb3_interleaved_ack_journal_hidden(self) -> None:
        """Hidden journal with TB3_STREAM_PREFIX must match reference pending_log."""
        base = _load_jsonl(Path("/app/data/m1_ack_order.jsonl"))
        prefix = os.environ.get("TB3_STREAM_PREFIX", "tb3_")
        events = apply_tb3_prefix(base, prefix)
        tmp = Path("/tmp/tb3_m1_journal.jsonl")
        tmp.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
        run_replay(tmp)
        stage = load_stage()
        ref = reference_stream_state_machine(events)
        assert stage["pending_log"] == ref["pending_log"]

    def test_reopen_stage_file_idempotent_replay(self) -> None:
        """Replaying onto a removed stage file reproduces pending_log."""
        journal = Path("/app/data/m1_ack_order.jsonl")
        events = _load_jsonl(journal)
        run_replay(journal)
        first = load_stage()["pending_log"]
        STAGE.unlink()
        run_replay(journal)
        second = load_stage()["pending_log"]
        ref = reference_stream_state_machine(events)
        assert first == second == ref["pending_log"]
