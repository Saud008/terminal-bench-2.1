"""Independent bag-audit ground truth for verifier."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Message:
    topic: str
    seq: int
    publish_ns: int
    receive_ns: int
    payload: bytes
    synthetic: bool


@dataclass
class DeadlineMiss:
    topic: str
    seq: int
    delta_ns: int
    deadline_ms: int


def decode_payload_bytes(raw_topic: str, payload: bytes) -> bytes:
    if raw_topic == "/legacy/cmd" and payload:
        return payload[1:]
    return payload


def payload_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_bag(bag_dir: Path) -> tuple[dict, list[Message]]:
    meta = json.loads((bag_dir / "metadata.json").read_text(encoding="utf-8"))
    remap = meta.get("remap", {})
    out: list[Message] = []
    for line in (bag_dir / "messages.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        raw_topic = raw["topic"]
        payload = decode_payload_bytes(raw_topic, bytes.fromhex(raw["payload"]))
        topic = remap.get(raw_topic, raw_topic)
        out.append(
            Message(
                topic=topic,
                seq=int(raw["seq"]),
                publish_ns=int(raw["publish_ns"]),
                receive_ns=int(raw["receive_ns"]),
                payload=payload,
                synthetic=False,
            )
        )
    return meta, out


def fill_gaps(messages: list[Message], seed: int) -> list[Message]:
    seed_ns = seed % 11
    by_topic: dict[str, list[Message]] = {}
    for m in messages:
        by_topic.setdefault(m.topic, []).append(m)
    out: list[Message] = []
    for _topic, rows in by_topic.items():
        rows.sort(key=lambda m: m.seq)
        if not rows:
            continue
        for seq in range(rows[0].seq, rows[-1].seq + 1):
            hit = next((r for r in rows if r.seq == seq), None)
            if hit:
                out.append(hit)
                continue
            prev = next((r for r in reversed(rows) if r.seq < seq), None)
            nxt = next((r for r in rows if r.seq > seq), None)
            publish_ns = _interpolate(seq, prev, nxt) + seed_ns
            payload = prev.payload if prev else (nxt.payload if nxt else b"")
            out.append(
                Message(
                    topic=rows[0].topic,
                    seq=seq,
                    publish_ns=publish_ns,
                    receive_ns=publish_ns,
                    payload=payload,
                    synthetic=True,
                )
            )
    out.sort(key=lambda m: (m.topic, m.seq))
    return out


def _interpolate(seq: int, prev: Message | None, nxt: Message | None) -> int:
    if prev and nxt and nxt.seq > prev.seq:
        steps = nxt.seq - prev.seq
        pos = seq - prev.seq
        span = nxt.publish_ns - prev.publish_ns
        return prev.publish_ns + (span * pos) // steps
    if prev:
        return prev.publish_ns + (seq - prev.seq)
    if nxt:
        return nxt.publish_ns - (nxt.seq - seq)
    return 0


def find_deadline_misses(
    meta: dict, messages: list[Message], speed: float, seed: int
) -> list[DeadlineMiss]:
    speed = speed if speed > 0 else 1.0
    seed_ms = seed % 5
    by_topic: dict[str, list[Message]] = {}
    for m in messages:
        by_topic.setdefault(m.topic, []).append(m)
    misses: list[DeadlineMiss] = []
    for topic, profile in meta.get("topics", {}).items():
        rows = by_topic.get(topic, [])
        if not rows or profile.get("deadline_clock") != "publish":
            continue
        rows.sort(key=lambda m: m.seq)
        effective_ms = max(1, math.ceil(profile["deadline_ms"] / speed) - seed_ms)
        limit_ns = effective_ms * 1_000_000
        for prev, cur in zip(rows, rows[1:]):
            delta = cur.publish_ns - prev.publish_ns
            if delta > limit_ns:
                misses.append(
                    DeadlineMiss(
                        topic=topic,
                        seq=cur.seq,
                        delta_ns=delta,
                        deadline_ms=int(profile["deadline_ms"]),
                    )
                )
    return misses


def expected_message_rows(messages: list[Message]) -> list[tuple]:
    return [
        (
            m.topic,
            m.seq,
            m.publish_ns,
            m.receive_ns,
            payload_hash(m.payload),
            1 if m.synthetic else 0,
        )
        for m in sorted(messages, key=lambda x: (x.topic, x.seq))
    ]


def expected_miss_rows(misses: list[DeadlineMiss]) -> list[tuple]:
    return [
        (m.topic, m.seq, m.delta_ns, m.deadline_ms)
        for m in sorted(misses, key=lambda x: (x.topic, x.seq))
    ]


def read_sqlite(path: Path) -> tuple[list[tuple], list[tuple]]:
    conn = sqlite3.connect(path)
    try:
        msgs = conn.execute(
            "SELECT topic, seq, publish_ns, receive_ns, payload_hash, synthetic FROM messages ORDER BY topic, seq"
        ).fetchall()
        misses = conn.execute(
            "SELECT topic, seq, delta_ns, deadline_ms FROM deadline_misses ORDER BY topic, seq"
        ).fetchall()
        return msgs, misses
    finally:
        conn.close()


def publish_ns_monotonic_per_topic(path: Path) -> bool:
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute(
            "SELECT topic, seq, publish_ns FROM messages ORDER BY topic, seq"
        ).fetchall()
        last: dict[str, int] = {}
        for topic, _seq, publish_ns in rows:
            if topic in last and publish_ns <= last[topic]:
                return False
            last[topic] = int(publish_ns)
        return True
    finally:
        conn.close()
