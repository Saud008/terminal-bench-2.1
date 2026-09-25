#!/usr/bin/env python3
"""Build chat replay fixture shards for bundled and hidden scenarios."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HIDDEN = Path(os.environ.get("VCREPLAY_HIDDEN_ROOT", ""))


def vc(**parts: int) -> dict[str, int]:
    return dict(parts)


def write_shard(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for ev in events:
            fh.write(json.dumps(ev, separators=(",", ":"), sort_keys=True))
            fh.write("\n")


def scenario_clean() -> dict[str, list[dict]]:
    return {
        "shard_001.jsonl": [
            {
                "event_id": "e001",
                "room_id": "lobby",
                "sender": "alice",
                "type": "message",
                "vector_clock": vc(alice=1),
                "timestamp_ms": 1000,
                "payload": {"text": "hello"},
            },
            {
                "event_id": "e002",
                "room_id": "lobby",
                "sender": "bob",
                "type": "message",
                "vector_clock": vc(alice=1, bob=1),
                "timestamp_ms": 1001,
                "payload": {"text": "hi"},
            },
        ],
        "shard_002.jsonl": [
            {
                "event_id": "e003",
                "room_id": "lobby",
                "sender": "alice",
                "type": "receipt",
                "vector_clock": vc(alice=2, bob=1),
                "timestamp_ms": 1002,
                "payload": {
                    "ref_event_id": "e002",
                    "recipient": "alice",
                    "delivered_clock": vc(alice=1, bob=1),
                },
            }
        ],
    }


def scenario_mod_precedence() -> dict[str, list[dict]]:
    concurrent = vc(mod=1, sys=1)
    return {
        "shard_001.jsonl": [
            {
                "event_id": "m001",
                "sender": "mod",
                "type": "moderation",
                "vector_clock": concurrent,
                "timestamp_ms": 2000,
                "payload": {"action": "kick", "target": "troll"},
            },
            {
                "event_id": "m002",
                "sender": "sys",
                "type": "moderation",
                "vector_clock": concurrent,
                "timestamp_ms": 2000,
                "payload": {"action": "ban", "target": "troll"},
            },
            {
                "event_id": "m003",
                "sender": "troll",
                "type": "message",
                "vector_clock": vc(mod=2, sys=2, troll=1),
                "timestamp_ms": 2001,
                "payload": {"text": "still here"},
            },
        ]
    }


def scenario_mute_window() -> dict[str, list[dict]]:
    return {
        "shard_001.jsonl": [
            {
                "event_id": "u001",
                "sender": "mod",
                "type": "mute_start",
                "vector_clock": vc(mod=1),
                "timestamp_ms": 3000,
                "payload": {"target": "spammer", "start_ms": 3000, "end_ms": 4000},
            },
            {
                "event_id": "u002",
                "sender": "spammer",
                "type": "message",
                "vector_clock": vc(mod=1, spammer=1),
                "timestamp_ms": 3999,
                "payload": {"text": "during mute"},
            },
            {
                "event_id": "u003",
                "sender": "spammer",
                "type": "message",
                "vector_clock": vc(mod=1, spammer=2),
                "timestamp_ms": 4000,
                "payload": {"text": "after mute"},
            },
        ]
    }


def scenario_dup_delivery() -> dict[str, list[dict]]:
    ref = vc(alice=1)
    return {
        "shard_001.jsonl": [
            {
                "event_id": "d001",
                "sender": "alice",
                "type": "message",
                "vector_clock": ref,
                "timestamp_ms": 5000,
                "payload": {"text": "payload"},
            },
            {
                "event_id": "d002",
                "sender": "bob",
                "type": "receipt",
                "vector_clock": vc(alice=1, bob=1),
                "timestamp_ms": 5001,
                "payload": {
                    "ref_event_id": "d001",
                    "recipient": "bob",
                    "delivered_clock": ref,
                },
            },
            {
                "event_id": "d003",
                "sender": "bob",
                "type": "receipt",
                "vector_clock": vc(alice=1, bob=2),
                "timestamp_ms": 5002,
                "payload": {
                    "ref_event_id": "d001",
                    "recipient": "bob",
                    "delivered_clock": ref,
                },
            },
        ]
    }


def scenario_clock_gap() -> dict[str, list[dict]]:
    return {
        "shard_001.jsonl": [
            {
                "event_id": "g001",
                "sender": "a",
                "type": "message",
                "vector_clock": vc(a=1),
                "timestamp_ms": 6000,
                "payload": {"text": "start"},
            },
            {
                "event_id": "g002",
                "sender": "b",
                "type": "message",
                "vector_clock": vc(a=1, b=8),
                "timestamp_ms": 6001,
                "payload": {"text": "jump"},
            },
        ]
    }


def scenario_shard_order() -> dict[str, list[dict]]:
    return {
        "shard_002.jsonl": [
            {
                "event_id": "s001",
                "sender": "n1",
                "type": "message",
                "vector_clock": vc(n1=1),
                "timestamp_ms": 7000,
                "payload": {"text": "first shard"},
            }
        ],
        "shard_010.jsonl": [
            {
                "event_id": "s002",
                "sender": "n1",
                "type": "message",
                "vector_clock": vc(n1=2),
                "timestamp_ms": 7001,
                "payload": {"text": "second shard"},
            }
        ],
    }


def scenario_gap_trap() -> dict[str, list[dict]]:
    return {
        "shard_001.jsonl": [
            {
                "event_id": "t001",
                "sender": "x",
                "type": "message",
                "vector_clock": vc(x=1),
                "timestamp_ms": 8000,
                "payload": {"text": "trap-a"},
            },
            {
                "event_id": "t002",
                "sender": "y",
                "type": "message",
                "vector_clock": vc(x=1, y=6),
                "timestamp_ms": 8001,
                "payload": {"text": "trap-b"},
            },
        ]
    }


def scenario_precedence_trap() -> dict[str, list[dict]]:
    concurrent = vc(mod=1, lead=1)
    return {
        "shard_001.jsonl": [
            {
                "event_id": "p001",
                "sender": "lead",
                "type": "moderation",
                "vector_clock": concurrent,
                "timestamp_ms": 9000,
                "payload": {"action": "warn", "target": "user7"},
            },
            {
                "event_id": "p002",
                "sender": "mod",
                "type": "moderation",
                "vector_clock": concurrent,
                "timestamp_ms": 9000,
                "payload": {"action": "ban", "target": "user7"},
            },
        ]
    }


SCENARIOS = {
    "clean-room": scenario_clean,
    "mod-precedence": scenario_mod_precedence,
    "mute-window": scenario_mute_window,
    "dup-delivery": scenario_dup_delivery,
    "clock-gap": scenario_clock_gap,
    "shard-order": scenario_shard_order,
}

HIDDEN_SCENARIOS = {
    "gap-trap": scenario_gap_trap,
    "precedence-trap": scenario_precedence_trap,
}


def emit(base: Path, mapping: dict[str, callable]) -> None:
    for name, builder in mapping.items():
        shards = builder()
        for shard_name, events in shards.items():
            write_shard(base / "rooms" / name / "shards" / shard_name, events)


def main() -> None:
    emit(ROOT, SCENARIOS)
    if HIDDEN.is_dir():
        emit(HIDDEN, HIDDEN_SCENARIOS)
    rooms = {"rooms": sorted(SCENARIOS.keys())}
    catalog_body = json.dumps(rooms, separators=(",", ":"), sort_keys=True)
    catalog_digest = hashlib.sha256(catalog_body.encode("utf-8")).hexdigest()
    (ROOT / "catalog.json").write_text(
        json.dumps({**rooms, "catalog_digest": catalog_digest}, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
