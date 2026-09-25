"""NATS JetStream offline journal replay and pending rollup export tests."""

from __future__ import annotations

import json
import os
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any

CLI = "/app/bin/natsctl"
STAGE = Path("/app/state/nats-jetstream-stage.json")
ROLLUP = Path("/app/output/pending-rollup.json")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return sorted(rows, key=lambda r: r["seq"])


def _match_filter(subject: str, pattern: str) -> bool:
    if pattern in ("", ">"):
        return True
    subj_tokens = subject.split(".")
    pat_tokens = pattern.split(".")
    if len(subj_tokens) != len(pat_tokens):
        return False
    for s_tok, p_tok in zip(subj_tokens, pat_tokens):
        if p_tok == "*":
            continue
        if p_tok != s_tok:
            return False
    return True


def reference_consumer_model(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Independent replay for staging snapshot and rollup inputs."""
    streams: dict[str, dict[str, Any]] = {}
    subject_catalog: list[str] = []
    seen_subjects: set[str] = set()

    for ev in sorted(events, key=lambda e: e["seq"]):
        op = ev["op"]
        if op == "PUB":
            st = streams.setdefault(
                ev["stream"],
                {"messages": [], "max_seq": 0, "consumers": {}},
            )
            st["messages"].append({"stream_seq": ev["stream_seq"], "subject": ev["subject"]})
            if ev["stream_seq"] > st["max_seq"]:
                st["max_seq"] = ev["stream_seq"]
            subj = ev["subject"]
            if subj not in seen_subjects:
                seen_subjects.add(subj)
                subject_catalog.append(subj)
        elif op == "CONSUMER_UPSERT":
            st = streams.setdefault(ev["stream"], {"messages": [], "max_seq": 0, "consumers": {}})
            cons = st["consumers"].setdefault(
                ev["consumer"],
                {
                    "filter_subject": "",
                    "max_deliver": 0,
                    "require_ack_sync": False,
                    "tick_ledger": 0,
                    "high_water_seq": 0,
                    "pending": {},
                },
            )
            cons["filter_subject"] = ev.get("filter_subject", "")
            cons["max_deliver"] = ev.get("max_deliver", 0)
            cons["require_ack_sync"] = ev.get("require_ack_sync", False)
        elif op == "DELIVER":
            st = streams[ev["stream"]]
            cons = st["consumers"][ev["consumer"]]
            msg = next(m for m in st["messages"] if m["stream_seq"] == ev["stream_seq"])
            if not _match_filter(msg["subject"], cons["filter_subject"]):
                continue
            cons["pending"][ev["stream_seq"]] = {
                "stream_seq": ev["stream_seq"],
                "delivery_num": ev["delivery_num"],
                "redelivery_due_tick": 0,
            }
            if ev["tick"] > cons["tick_ledger"]:
                cons["tick_ledger"] = ev["tick"]
        elif op == "ACK":
            st = streams[ev["stream"]]
            cons = st["consumers"][ev["consumer"]]
            seq = ev["stream_seq"]
            if seq not in cons["pending"]:
                continue
            if cons["require_ack_sync"] and not ev.get("ack_sync", False):
                continue
            cons["pending"].pop(seq, None)
            if ev.get("ack_sync", False) and seq > cons["high_water_seq"]:
                cons["high_water_seq"] = seq
            if ev["tick"] > cons["tick_ledger"]:
                cons["tick_ledger"] = ev["tick"]
        elif op == "NAK":
            st = streams[ev["stream"]]
            cons = st["consumers"][ev["consumer"]]
            seq = ev["stream_seq"]
            if seq not in cons["pending"]:
                continue
            entry = cons["pending"][seq]
            entry["redelivery_due_tick"] = ev["tick"] + ev["delay_ms"]
            cons["pending"][seq] = entry
            if ev["tick"] > cons["tick_ledger"]:
                cons["tick_ledger"] = ev["tick"]
        elif op == "TERM":
            st = streams[ev["stream"]]
            cons = st["consumers"][ev["consumer"]]
            seq = ev["stream_seq"]
            entry = cons["pending"].get(seq)
            if entry is None:
                continue
            if cons["max_deliver"] > 0 and entry["delivery_num"] >= cons["max_deliver"]:
                cons["pending"].pop(seq, None)
            if ev["tick"] > cons["tick_ledger"]:
                cons["tick_ledger"] = ev["tick"]

    subject_catalog = sorted(subject_catalog)
    return {
        "last_applied_seq": events[-1]["seq"] if events else 0,
        "subject_catalog": subject_catalog,
        "streams": streams,
    }


def reference_rollup(stage: dict[str, Any], export_pass: int = 1) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for sname, stream in sorted(stage["streams"].items()):
        for cname, cons in sorted(stream["consumers"].items()):
            due = 0
            for p in cons["pending"].values():
                due_tick = p.get("redelivery_due_tick", 0)
                if due_tick > 0 and due_tick <= cons["tick_ledger"]:
                    due += 1
            rows.append(
                {
                    "stream": sname,
                    "consumer": cname,
                    "pending_count": len(cons["pending"]),
                    "high_water_seq": cons["high_water_seq"],
                    "redelivery_due": due,
                }
            )
    return {"consumers": rows, "export_pass": export_pass}


def run_replay(journal: Path) -> None:
    if STAGE.exists():
        STAGE.unlink()
    if ROLLUP.exists():
        ROLLUP.unlink()
    proc = subprocess.run([CLI, "replay", str(journal)], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr + proc.stdout


def run_export(export_pass: int = 1) -> None:
    proc = subprocess.run(
        [CLI, "export", "--pass", str(export_pass)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def load_stage() -> dict[str, Any]:
    return json.loads(STAGE.read_text(encoding="utf-8"))


def load_rollup() -> dict[str, Any]:
    return json.loads(ROLLUP.read_text(encoding="utf-8"))


def apply_tb3_subject_prefix(events: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    out = deepcopy(events)
    for ev in out:
        if "subject" in ev:
            ev["subject"] = f"{prefix}{ev['subject']}"
    return out


def consumer_pending(stage: dict[str, Any], stream: str, consumer: str) -> dict[str, Any]:
    return stage["streams"][stream]["consumers"][consumer]["pending"]


def pending_seq_keys(pending: dict[str, Any]) -> set[int]:
    return {int(k) for k in pending.keys()}


class TestNatsJetstreamReplay:
    """Offline JetStream journal replay and rollup export."""

    def test_replay_writes_stage_snapshot(self) -> None:
        """Replay must materialize /app/state/nats-jetstream-stage.json."""
        run_replay(Path("/app/data/ack_sync_gate.jsonl"))
        assert STAGE.is_file()

    def test_staging_subject_catalog_matches_reference(self) -> None:
        """Ingest subject catalog in stage must match reference ingest."""
        journal = Path("/app/data/filter_glob.jsonl")
        events = _load_jsonl(journal)
        run_replay(journal)
        stage = load_stage()
        ref = reference_consumer_model(events)
        assert stage["subject_catalog"] == ref["subject_catalog"]

    def test_ack_sync_false_keeps_pending(self) -> None:
        """Non-durable ACK must not clear ack-pending when require_ack_sync is set."""
        journal = Path("/app/data/ack_sync_gate.jsonl")
        run_replay(journal)
        pending = consumer_pending(load_stage(), "ORDERS", "c1")
        assert 1 in pending_seq_keys(pending)

    def test_ack_sync_true_clears_pending(self) -> None:
        """Durable ACK clears pending and updates high water."""
        events = _load_jsonl(Path("/app/data/ack_sync_gate.jsonl"))
        events.append(
            {
                "seq": 5,
                "op": "ACK",
                "stream": "ORDERS",
                "consumer": "c1",
                "stream_seq": 1,
                "ack_sync": True,
                "tick": 40,
            }
        )
        tmp = Path("/tmp/ack_sync_true.jsonl")
        tmp.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
        run_replay(tmp)
        stage = load_stage()
        ref = reference_consumer_model(events)
        assert consumer_pending(stage, "ORDERS", "c1") == {}
        assert stage["streams"]["ORDERS"]["consumers"]["c1"]["high_water_seq"] == 1
        assert ref["streams"]["ORDERS"]["consumers"]["c1"]["high_water_seq"] == 1

    def test_nak_redelivery_uses_tick_ledger(self) -> None:
        """NAK redelivery due tick must be journal tick plus delay_ms."""
        journal = Path("/app/data/nak_tick_ledger.jsonl")
        run_replay(journal)
        pending = consumer_pending(load_stage(), "EVENTS", "w1")
        entry = pending["1"]
        assert entry["redelivery_due_tick"] == 250

    def test_nak_not_wall_timestamp(self) -> None:
        """Redelivery must not use timestamp_ms wall clock base."""
        journal = Path("/app/data/nak_tick_ledger.jsonl")
        run_replay(journal)
        pending = consumer_pending(load_stage(), "EVENTS", "w1")
        entry = pending["1"]
        assert entry["redelivery_due_tick"] != 9050

    def test_filter_subject_single_token_star(self) -> None:
        """orders.* delivers only two-segment subjects."""
        journal = Path("/app/data/filter_glob.jsonl")
        events = _load_jsonl(journal)
        run_replay(journal)
        stage = load_stage()
        ref = reference_consumer_model(events)
        assert pending_seq_keys(consumer_pending(stage, "SHIP", "regional")) == {2, 3}
        assert set(ref["streams"]["SHIP"]["consumers"]["regional"]["pending"].keys()) == {2, 3}

    def test_filter_rejects_cross_segment_wildcard(self) -> None:
        """orders.us.east must not match orders.* filter."""
        journal = Path("/app/data/filter_glob.jsonl")
        run_replay(journal)
        pending = consumer_pending(load_stage(), "SHIP", "regional")
        assert 1 not in pending_seq_keys(pending)

    def test_term_purges_when_max_deliver_exhausted(self) -> None:
        """TERM clears ack-pending when delivery_num reached max_deliver."""
        journal = Path("/app/data/term_max_deliver.jsonl")
        run_replay(journal)
        pending = consumer_pending(load_stage(), "TASKS", "worker")
        assert pending == {}

    def test_term_before_max_keeps_pending(self) -> None:
        """Without TERM line, pending remains after partial delivery."""
        events = _load_jsonl(Path("/app/data/term_max_deliver.jsonl"))
        partial = [e for e in events if e["seq"] <= 3]
        tmp = Path("/tmp/term_partial.jsonl")
        tmp.write_text("\n".join(json.dumps(e) for e in partial) + "\n", encoding="utf-8")
        run_replay(tmp)
        ref = reference_consumer_model(partial)
        stage = load_stage()
        assert len(consumer_pending(stage, "TASKS", "worker")) == 1
        assert ref["streams"]["TASKS"]["consumers"]["worker"]["pending"]

    def test_export_rollup_per_consumer_high_water(self) -> None:
        """Export high_water_seq must be per-consumer not stream max."""
        journal = Path("/app/data/rollup_highwater.jsonl")
        run_replay(journal)
        run_export()
        rollup = load_rollup()
        ref = reference_rollup(load_stage())
        assert rollup == ref
        slow = next(r for r in rollup["consumers"] if r["consumer"] == "slow")
        fast = next(r for r in rollup["consumers"] if r["consumer"] == "fast")
        assert slow["high_water_seq"] == 1
        assert fast["high_water_seq"] == 2

    def test_export_not_stream_max_seq(self) -> None:
        """Rollup must not echo stream max_seq for every consumer row."""
        journal = Path("/app/data/rollup_highwater.jsonl")
        run_replay(journal)
        run_export()
        rollup = load_rollup()
        fast = next(r for r in rollup["consumers"] if r["consumer"] == "fast")
        assert fast["high_water_seq"] != 3

    def test_subprocess_cli_rebuild_path(self) -> None:
        """natsctl must be invoked via subprocess CLI."""
        proc = subprocess.run(["test", "-x", CLI], capture_output=True, text=True)
        assert proc.returncode == 0

    def test_export_pass_persistence(self) -> None:
        """Second export pass echoes --pass for cross-run persistence checks."""
        run_replay(Path("/app/data/ack_sync_gate.jsonl"))
        run_export(2)
        rollup = load_rollup()
        assert rollup["export_pass"] == 2

    def test_pending_count_in_rollup(self) -> None:
        """Rollup pending_count matches ack-pending map size."""
        run_replay(Path("/app/data/rollup_highwater.jsonl"))
        run_export()
        rollup = load_rollup()
        fast = next(r for r in rollup["consumers"] if r["consumer"] == "fast")
        assert fast["pending_count"] == 1

    def test_redelivery_due_count_export(self) -> None:
        """Rollup redelivery_due counts entries due on tick ledger."""
        events = _load_jsonl(Path("/app/data/nak_tick_ledger.jsonl"))
        events.append(
            {
                "seq": 5,
                "op": "DELIVER",
                "stream": "EVENTS",
                "consumer": "w1",
                "stream_seq": 1,
                "delivery_num": 2,
                "tick": 260,
            }
        )
        tmp = Path("/tmp/nak_due.jsonl")
        tmp.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
        run_replay(tmp)
        run_export()
        rollup = load_rollup()
        row = next(r for r in rollup["consumers"] if r["consumer"] == "w1")
        assert row["redelivery_due"] == 1

    def test_replay_idempotent_stage(self) -> None:
        """Replaying twice reproduces identical stage snapshot."""
        journal = Path("/app/data/filter_glob.jsonl")
        run_replay(journal)
        first = load_stage()
        STAGE.unlink()
        run_replay(journal)
        second = load_stage()
        assert first == second

    def test_last_applied_seq_persisted(self) -> None:
        """Stage records last applied journal seq."""
        journal = Path("/app/data/ack_sync_gate.jsonl")
        run_replay(journal)
        assert load_stage()["last_applied_seq"] == 4

    def test_tb3_delayed_nak_burst_hidden(self) -> None:
        """TB3 subject prefix with delayed NAK burst must match reference pending ticks."""
        base = _load_jsonl(Path("/app/data/nak_tick_ledger.jsonl"))
        prefix = os.environ.get("TB3_SUBJECT_PREFIX", "tb3.")
        events = apply_tb3_subject_prefix(base, prefix)
        events.append(
            {
                "seq": 5,
                "op": "NAK",
                "stream": "EVENTS",
                "consumer": "w1",
                "stream_seq": 1,
                "delay_ms": 80,
                "tick": 300,
                "timestamp_ms": 12000,
            }
        )
        tmp = Path("/tmp/tb3_nak_burst.jsonl")
        tmp.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
        run_replay(tmp)
        stage = load_stage()
        ref = reference_consumer_model(events)
        got_tick = consumer_pending(stage, "EVENTS", "w1")["1"]["redelivery_due_tick"]
        ref_tick = ref["streams"]["EVENTS"]["consumers"]["w1"]["pending"][1]["redelivery_due_tick"]
        assert got_tick == ref_tick == 380

    def test_tb3_subject_prefix_filter_hidden(self) -> None:
        """TB3 subject prefix on filter_glob must match reference pending keys."""
        base = _load_jsonl(Path("/app/data/filter_glob.jsonl"))
        prefix = os.environ.get("TB3_SUBJECT_PREFIX", "tb3.")
        events = apply_tb3_subject_prefix(base, prefix)
        tmp = Path("/tmp/tb3_filter.jsonl")
        tmp.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
        run_replay(tmp)
        stage = load_stage()
        ref = reference_consumer_model(events)
        got = pending_seq_keys(consumer_pending(stage, "SHIP", "regional"))
        expected = set(ref["streams"]["SHIP"]["consumers"]["regional"]["pending"].keys())
        assert got == expected == {2, 3}
