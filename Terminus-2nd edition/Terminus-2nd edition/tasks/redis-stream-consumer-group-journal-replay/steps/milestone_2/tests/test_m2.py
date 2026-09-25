"""Milestone 2 — XAUTOCLAIM idle boundary and MKSTREAM dollar id semantics."""

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


def reference_autoclaim_reclaim(events: list[dict[str, Any]]) -> int:
    streams: dict[str, dict[str, Any]] = {}
    reclaim = 0
    for ev in sorted(events, key=lambda e: e["seq"]):
        if ev["op"] == "XADD":
            st = streams.setdefault(ev["stream"], {"entries": [], "groups": {}})
            mid = ev.get("id") or f"{ev['timestamp_ms']}-{len(st['entries'])}"
            st["entries"].append({"id": mid})
        elif ev["op"] == "XREADGROUP":
            st = streams[ev["stream"]]
            grp = st["groups"].setdefault(ev["group"], {"pending": {}})
            for mid in ev["ids"]:
                grp["pending"][mid] = {
                    "consumer": ev["consumer"],
                    "idle_ms": ev["timestamp_ms"],
                    "delivery_count": grp["pending"].get(mid, {}).get("delivery_count", 0) + 1,
                }
        elif ev["op"] == "XAUTOCLAIM":
            st = streams[ev["stream"]]
            grp = st["groups"][ev["group"]]
            now = ev["timestamp_ms"]
            for mid, pel in list(grp["pending"].items()):
                if pel["consumer"] == ev["consumer"]:
                    continue
                idle = now - pel["idle_ms"]
                if idle >= ev["min_idle_ms"]:
                    pel["consumer"] = ev["consumer"]
                    pel["delivery_count"] += 1
                    pel["idle_ms"] = now
                    grp["pending"][mid] = pel
                    reclaim += 1
    return reclaim


def reference_mkstream_last_id(events: list[dict[str, Any]]) -> str:
    streams: dict[str, dict[str, Any]] = {}
    last_id = ""
    for ev in sorted(events, key=lambda e: e["seq"]):
        if ev["op"] == "XADD":
            st = streams.setdefault(ev["stream"], {"entries": []})
            mid = ev.get("id") or f"{ev['timestamp_ms']}-{len(st['entries'])}"
            st["entries"].append({"id": mid})
        elif ev["op"] == "XGROUP" and ev.get("sub") == "CREATE":
            st = streams.setdefault(ev["stream"], {"entries": []})
            start = ev.get("id", "0-0")
            if start == "$":
                start = st["entries"][-1]["id"] if st["entries"] else "0-0"
            last_id = start
    return last_id


def run_replay(journal: Path) -> None:
    if STAGE.exists():
        STAGE.unlink()
    proc = subprocess.run([CLI, "replay", str(journal)], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr + proc.stdout


def load_stage() -> dict[str, Any]:
    return json.loads(STAGE.read_text(encoding="utf-8"))


class TestMilestone2:
    """AUTOCLAIM idle compare and MKSTREAM dollar tail id."""

    def test_mkstream_dollar_uses_tail_id(self) -> None:
        """XGROUP CREATE with dollar id must store stream tail, not 0-0."""
        journal = Path("/app/data/m2_mkstream_dollar.jsonl")
        events = _load_jsonl(journal)
        run_replay(journal)
        stage = load_stage()
        grp = stage["streams"]["events"]["groups"]["workers"]
        assert grp["last_id"] == reference_mkstream_last_id(events)
        assert grp["last_id"] == "2000-0"

    def test_autoclaim_reclaims_at_exact_min_idle(self) -> None:
        """Idle equal to min_idle_ms must reclaim per contract."""
        journal = Path("/app/data/m2_autoclaim_idle.jsonl")
        events = _load_jsonl(journal)
        run_replay(journal)
        stage = load_stage()
        grp = stage["streams"]["jobs"]["groups"]["g1"]
        assert grp["reclaim_total"] == reference_autoclaim_reclaim(events)
        assert grp["reclaim_total"] == 1

    def test_autoclaim_assigns_fast_consumer(self) -> None:
        """Reclaimed message must move to the claiming consumer."""
        journal = Path("/app/data/m2_autoclaim_idle.jsonl")
        run_replay(journal)
        pel = load_stage()["streams"]["jobs"]["groups"]["g1"]["pending"]["3000-0"]
        assert pel["consumer"] == "fast"

    def test_subprocess_replay_mkstream_journal(self) -> None:
        """CLI replay subprocess succeeds on mkstream journal."""
        proc = subprocess.run(
            [CLI, "replay", "/app/data/m2_mkstream_dollar.jsonl"],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0

    def test_tb3_prefix_mkstream_hidden(self) -> None:
        """TB3_STREAM_PREFIX hidden journal preserves dollar tail semantics."""
        base = _load_jsonl(Path("/app/data/m2_mkstream_dollar.jsonl"))
        prefix = os.environ.get("TB3_STREAM_PREFIX", "hidden_")
        events = deepcopy(base)
        for ev in events:
            ev["stream"] = prefix + ev["stream"]
        tmp = Path("/tmp/tb3_m2_mkstream.jsonl")
        tmp.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
        run_replay(tmp)
        stage = load_stage()
        key = prefix + "events"
        grp = stage["streams"][key]["groups"]["workers"]
        assert grp["last_id"] == reference_mkstream_last_id(events)

    def test_idle_boundary_reference_exact(self) -> None:
        """Reference idle math uses greater-than-or-equal boundary."""
        events = _load_jsonl(Path("/app/data/m2_autoclaim_idle.jsonl"))
        assert reference_autoclaim_reclaim(events) == 1

    def test_stage_persists_group_metadata(self) -> None:
        """Replay persists group last_id in stage file."""
        run_replay(Path("/app/data/m2_mkstream_dollar.jsonl"))
        raw = STAGE.read_text(encoding="utf-8")
        assert "last_id" in raw
        assert "workers" in raw
