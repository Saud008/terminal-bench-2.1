"""Build randomized quorum Raft fixtures (anti-hardcoding)."""
from __future__ import annotations

import json
import os
import random
from pathlib import Path

ROOT = Path(os.environ.get("QQRAFT_HIDDEN_ROOT", "/app/fixtures"))


def node_name(rng: random.Random, i: int) -> str:
    return f"node-{rng.randint(1000, 9999)}-{i}"


def queue_id(rng: random.Random, i: int) -> str:
    return f"qq.{rng.randint(10, 99)}.{rng.choice(['orders', 'events', 'audit'])}.{i}"


def write_scenario(slug: str, builder) -> None:
    d = ROOT / slug
    d.mkdir(parents=True, exist_ok=True)
    builder(d)


def dump_log(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")


def leader_handoff(d: Path) -> None:
    rng = random.Random(41)
    n1, n2, n3 = (node_name(rng, i) for i in range(3))
    q = queue_id(rng, 1)
    rows = [
        {"term": 1, "index": 1, "kind": "config", "payload": {"op": "add_voter", "node_id": n1}},
        {"term": 1, "index": 2, "kind": "config", "payload": {"op": "add_voter", "node_id": n2}},
        {"term": 1, "index": 3, "kind": "config", "payload": {"op": "add_voter", "node_id": n3}},
        {"term": 1, "index": 4, "kind": "election", "payload": {"node_id": n1, "role": "leader"}},
        {"term": 1, "index": 5, "kind": "queue", "queue_id": q, "payload": {"messages": 4, "replicas": [n1, n2, n3]}},
        {"term": 1, "index": 6, "kind": "commit", "payload": {"commit_index": 6}},
        {"term": 2, "index": 7, "kind": "election", "payload": {"node_id": n2, "role": "leader"}},
        {"term": 2, "index": 8, "kind": "queue", "queue_id": q, "payload": {"messages": 9, "replicas": [n1, n2, n3]}},
        {"term": 2, "index": 9, "kind": "commit", "payload": {"commit_index": 9}},
    ]
    dump_log(d / "segment-a.qlog", rows)
    meta = {"nodes": [n1, n2, n3], "primary_queue": q}
    (d / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def term_order_trap(d: Path) -> None:
    rng = random.Random(88)
    n1, n2 = node_name(rng, 1), node_name(rng, 2)
    q = queue_id(rng, 2)
    rows = [
        {"term": 1, "index": 1, "kind": "config", "payload": {"op": "add_voter", "node_id": n1}},
        {"term": 1, "index": 1, "kind": "election", "payload": {"node_id": n1, "role": "leader"}},
        {"term": 2, "index": 1, "kind": "election", "payload": {"node_id": n2, "role": "leader"}},
        {"term": 2, "index": 2, "kind": "config", "payload": {"op": "add_voter", "node_id": n2}},
        {"term": 2, "index": 3, "kind": "queue", "queue_id": q, "payload": {"messages": 3, "replicas": [n1, n2]}},
        {"term": 2, "index": 4, "kind": "commit", "payload": {"commit_index": 4}},
    ]
    dump_log(d / "segment-b.qlog", rows)
    (d / "meta.json").write_text(json.dumps({"nodes": [n1, n2], "primary_queue": q}, indent=2) + "\n")


def uncommitted_tail(d: Path) -> None:
    rng = random.Random(17)
    n1 = node_name(rng, 1)
    q1, q2 = queue_id(rng, 1), queue_id(rng, 2)
    rows = [
        {"term": 3, "index": 1, "kind": "config", "payload": {"op": "add_voter", "node_id": n1}},
        {"term": 3, "index": 2, "kind": "election", "payload": {"node_id": n1, "role": "leader"}},
        {"term": 3, "index": 3, "kind": "queue", "queue_id": q1, "payload": {"messages": 11, "replicas": [n1]}},
        {"term": 3, "index": 4, "kind": "commit", "payload": {"commit_index": 4}},
        {"term": 3, "index": 5, "kind": "queue", "queue_id": q2, "payload": {"messages": 99, "replicas": [n1]}},
    ]
    dump_log(d / "segment-c.qlog", rows)
    (d / "meta.json").write_text(json.dumps({"nodes": [n1], "committed_queue": q1, "tail_queue": q2}, indent=2) + "\n")


def snapshot_truncation(d: Path) -> None:
    rng = random.Random(55)
    nodes = [node_name(rng, i) for i in range(3)]
    q = queue_id(rng, 3)
    snap = {
        "last_included_term": 4,
        "last_included_index": 5,
        "commit_index": 5,
        "membership": sorted(nodes[:2]),
        "queue_states": {q: 7},
    }
    (d / "snapshot.json").write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    rows = [
        {"term": 4, "index": 4, "kind": "queue", "queue_id": q, "payload": {"messages": 1, "replicas": nodes[:2]}},
        {"term": 4, "index": 5, "kind": "commit", "payload": {"commit_index": 5}},
        {"term": 5, "index": 6, "kind": "election", "payload": {"node_id": nodes[2], "role": "leader"}},
        {"term": 5, "index": 7, "kind": "commit", "payload": {"commit_index": 7}},
        {"term": 5, "index": 8, "kind": "queue", "queue_id": q, "payload": {"messages": 12, "replicas": nodes}},
    ]
    dump_log(d / "segment-d.qlog", rows)
    (d / "meta.json").write_text(json.dumps({"nodes": nodes, "primary_queue": q}, indent=2) + "\n")


def replica_add_same_term(d: Path) -> None:
    rng = random.Random(29)
    n1, n2, n3 = (node_name(rng, i) for i in range(3))
    q = queue_id(rng, 4)
    rows = [
        {"term": 6, "index": 1, "kind": "config", "payload": {"op": "add_voter", "node_id": n1}},
        {"term": 6, "index": 2, "kind": "config", "payload": {"op": "add_voter", "node_id": n2}},
        {"term": 6, "index": 3, "kind": "election", "payload": {"node_id": n1, "role": "leader"}},
        {"term": 6, "index": 4, "kind": "config", "payload": {"op": "add_voter", "node_id": n3}},
        {"term": 6, "index": 5, "kind": "queue", "queue_id": q, "payload": {"messages": 6, "replicas": [n1, n2, n3]}},
        {"term": 6, "index": 6, "kind": "commit", "payload": {"commit_index": 6}},
    ]
    dump_log(d / "segment-e.qlog", rows)
    (d / "meta.json").write_text(json.dumps({"nodes": [n1, n2, n3], "primary_queue": q}, indent=2) + "\n")


def cross_run_idempotent(d: Path) -> None:
    leader_handoff(d)


def hidden_truncation_poison(d: Path) -> None:
    rng = random.Random(911)
    nodes = [node_name(rng, i) for i in range(4)]
    q = queue_id(rng, 9)
    snap = {
        "last_included_term": 9,
        "last_included_index": 3,
        "commit_index": 3,
        "membership": sorted(nodes[:3]),
        "queue_states": {q: 2},
    }
    (d / "snapshot.json").write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    rows = [
        {"term": 9, "index": 2, "kind": "queue", "queue_id": q, "payload": {"messages": 0, "replicas": nodes[:3]}},
        {"term": 9, "index": 3, "kind": "commit", "payload": {"commit_index": 3}},
        {"term": 10, "index": 4, "kind": "config", "payload": {"op": "add_voter", "node_id": nodes[3]}},
        {"term": 10, "index": 5, "kind": "commit", "payload": {"commit_index": 5}},
        {"term": 10, "index": 6, "kind": "queue", "queue_id": q, "payload": {"messages": 15, "replicas": nodes}},
    ]
    dump_log(d / "segment-h.qlog", rows)
    (d / "meta.json").write_text(json.dumps({"nodes": nodes, "primary_queue": q}, indent=2) + "\n")


def hidden_uncommitted_leader(d: Path) -> None:
    rng = random.Random(712)
    n1, n2 = node_name(rng, 1), node_name(rng, 2)
    q = queue_id(rng, 7)
    rows = [
        {"term": 11, "index": 1, "kind": "config", "payload": {"op": "add_voter", "node_id": n1}},
        {"term": 11, "index": 2, "kind": "config", "payload": {"op": "add_voter", "node_id": n2}},
        {"term": 11, "index": 3, "kind": "election", "payload": {"node_id": n1, "role": "leader"}},
        {"term": 11, "index": 4, "kind": "queue", "queue_id": q, "payload": {"messages": 20, "replicas": [n1, n2]}},
        {"term": 11, "index": 5, "kind": "commit", "payload": {"commit_index": 5}},
        {"term": 11, "index": 6, "kind": "election", "payload": {"node_id": n2, "role": "leader"}},
    ]
    dump_log(d / "segment-u.qlog", rows)
    (d / "meta.json").write_text(json.dumps({"nodes": [n1, n2], "primary_queue": q}, indent=2) + "\n")


SCENARIOS = {
    "leader-handoff": leader_handoff,
    "term-order-trap": term_order_trap,
    "uncommitted-tail": uncommitted_tail,
    "snapshot-truncation": snapshot_truncation,
    "replica-add-same-term": replica_add_same_term,
    "cross-run-idempotent": cross_run_idempotent,
    "hidden-truncation-poison": hidden_truncation_poison,
    "hidden-uncommitted-leader": hidden_uncommitted_leader,
}

def main() -> None:
    is_hidden_root = ROOT.name == "qqraftctl" or "QQRAFT_HIDDEN_ROOT" in os.environ
    for slug, fn in SCENARIOS.items():
        if slug.startswith("hidden") and not is_hidden_root:
            continue
        write_scenario(slug, fn)

if __name__ == "__main__":
    main()
    print("fixtures ok", ROOT)
