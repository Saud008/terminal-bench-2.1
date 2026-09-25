"""Independent reference math for flink barrier skew chronicle."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

CONFIG = Path("/app/fixtures/config")
DEFAULT_TIMEOUT = 60000


def load_graph() -> dict:
    return json.loads((CONFIG / "operator_graph.json").read_text(encoding="utf-8"))


def load_job_meta() -> dict:
    return json.loads((CONFIG / "job_meta.json").read_text(encoding="utf-8"))


def read_jsonl_dir(folder: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(folder.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def dedupe_key(ev: dict) -> str:
    return (
        f"{ev['checkpoint_id']}|{ev['attempt_id']}|{ev['operator_id']}|"
        f"{ev['subtask_index']}|{ev['event_kind']}|{ev['timestamp_ms']}"
    )


def reference_event_index(events_dir: Path) -> list[dict]:
    seen: set[str] = set()
    rows: list[dict] = []
    for ev in read_jsonl_dir(events_dir):
        key = dedupe_key(ev)
        if key in seen:
            continue
        seen.add(key)
        rows.append(ev)
    rows.sort(key=lambda r: (r["timestamp_ms"], r["operator_id"], r["subtask_index"]))
    return rows


def expected_subtasks(operator_id: str, graph: dict) -> int:
    for op in graph["operators"]:
        if op["operator_id"] == operator_id:
            return op["parallelism"]
    return 1


def chain_accepts(ev: dict, mapped: str, graph: dict) -> bool:
    ops = graph["operators"]
    spec = next((o for o in ops if o["operator_id"] == mapped), None)
    if spec is None:
        return True
    if spec.get("chain_head") and not spec.get("chain_tail"):
        nxt = next((o for o in ops if o["vertex_index"] == spec["vertex_index"] + 1), None)
        if nxt and ev["operator_id"] == nxt["operator_id"]:
            return False
    return True


def buffer_digest(row: dict) -> str:
    body = {
        "alignment_class": row["alignment_class"],
        "attempt_id": row["attempt_id"],
        "barriers_received": row["barriers_received"],
        "checkpoint_id": row["checkpoint_id"],
        "expected_subtasks": row["expected_subtasks"],
        "first_barrier_ms": row["first_barrier_ms"],
        "last_barrier_ms": row["last_barrier_ms"],
        "operator_id": row["operator_id"],
        "skew_ms": row["skew_ms"],
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def reference_alignment_rows(events: list[dict]) -> list[dict]:
    graph = load_graph()
    buckets: dict[str, list[int]] = {}
    unaligned: dict[str, bool] = {}
    timeouts: dict[str, int] = {}
    for ev in events:
        if ev["event_kind"] not in ("CHECKPOINT_BARRIER",):
            continue
        mapped = ev["operator_id"]
        if not chain_accepts(ev, mapped, graph):
            continue
        gkey = f"{ev['checkpoint_id']}|{ev['attempt_id']}|{mapped}"
        unaligned[gkey] = unaligned.get(gkey, False) or ev.get("is_unaligned", False)
        timeouts.setdefault(gkey, ev.get("aligned_checkpoint_timeout_ms") or DEFAULT_TIMEOUT)
        bkey = f"{gkey}|{ev['subtask_index']}"
        buckets.setdefault(bkey, []).append(ev["timestamp_ms"])
    groups: dict[str, list[str]] = {}
    for bkey in buckets:
        gkey = bkey.rsplit("|", 1)[0]
        groups.setdefault(gkey, []).append(bkey)
    rows: list[dict] = []
    for gkey, bkeys in groups.items():
        cp_s, attempt_s, op = gkey.split("|")
        cp = int(cp_s)
        attempt = int(attempt_s)
        ts: list[int] = []
        for bk in bkeys:
            ts.extend(buckets[bk])
        if not ts:
            continue
        mn = min(ts)
        mx = max(ts)
        skew = mx - mn
        expected = expected_subtasks(op, graph)
        received = len(bkeys)
        timeout = timeouts[gkey]
        if unaligned.get(gkey):
            clazz = "UNALIGNED_DECLARED"
        elif received < expected:
            clazz = "INCOMPLETE"
        elif skew > timeout:
            clazz = "TIMEOUT_VIOLATION"
        else:
            clazz = "ALIGNED_OK"
        row = {
            "checkpoint_id": cp,
            "attempt_id": attempt,
            "operator_id": op,
            "skew_ms": skew,
            "alignment_class": clazz,
            "barriers_received": received,
            "expected_subtasks": expected,
            "first_barrier_ms": mn,
            "last_barrier_ms": mx,
        }
        row["buffer_digest"] = buffer_digest(row)
        rows.append(row)
    rows.sort(key=lambda r: (r["checkpoint_id"], r["attempt_id"], r["operator_id"]))
    return rows


def reference_chronicle(buffer_rows: list[dict]) -> dict:
    meta = load_job_meta()
    grouped: dict[tuple[int, int], list[dict]] = {}
    for row in buffer_rows:
        key = (row["checkpoint_id"], row["attempt_id"])
        grouped.setdefault(key, []).append(row)
    checkpoints = []
    for (cp, attempt), ops in sorted(grouped.items()):
        op_rows = []
        max_skew = 0
        timeout_count = 0
        unaligned_count = 0
        for row in sorted(ops, key=lambda r: r["operator_id"]):
            max_skew = max(max_skew, row["skew_ms"])
            if row["alignment_class"] == "TIMEOUT_VIOLATION":
                timeout_count += 1
            if row["alignment_class"] == "UNALIGNED_DECLARED":
                unaligned_count += 1
            mis = "SKEW_TIMEOUT" if row["alignment_class"] == "TIMEOUT_VIOLATION" else row["alignment_class"]
            op_rows.append({
                "operator_id": row["operator_id"],
                "skew_ms": row["skew_ms"],
                "alignment_class": row["alignment_class"],
                "misalignment_class": mis,
                "barriers_received": row["barriers_received"],
                "expected_subtasks": row["expected_subtasks"],
            })
        checkpoints.append({
            "checkpoint_id": cp,
            "attempt_id": attempt,
            "operators": op_rows,
            "summary": {
                "operator_count": len(op_rows),
                "max_skew_ms": max_skew,
                "timeout_violation_count": timeout_count,
                "unaligned_count": unaligned_count,
            },
        })
    return {
        "job_id": meta["job_id"],
        "alignment_timeout_ms": meta["alignment_timeout_ms"],
        "checkpoints": checkpoints,
    }
