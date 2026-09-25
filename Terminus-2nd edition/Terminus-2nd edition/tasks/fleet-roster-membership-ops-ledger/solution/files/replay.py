from __future__ import annotations

import sys

sys.path.insert(0, "/app/fixtures")
from digest_util import sha256_canonical_json
from roster.commit import apply_commit
from roster.config import apply_config
from roster.election import apply_election


def digest_staging(st: dict) -> str:
    qs = {k: st["queue_states"][k] for k in sorted(st["queue_states"])}
    body = {
        "cluster": st["cluster"],
        "commit_index": st["commit_index"],
        "current_term": st["current_term"],
        "leader_id": st["leader_id"],
        "membership": list(st["membership"]),
        "queue_states": qs,
        "truncated_before": st["truncated_before"],
    }
    return sha256_canonical_json(body)


def replay(
    cluster: str,
    entries: list[dict],
    truncated_before: int = 0,
    baseline: dict | None = None,
) -> dict:
    base = baseline or {}
    membership = list(base.get("membership") or [])
    queues = dict(base.get("queue_states") or {})
    commit_index = int(base.get("commit_index") or 0)
    current_term = int(base.get("current_term") or 0)
    epoch_term = int(base.get("epoch_term") or 0)
    leader_id = ""
    pending: list[dict] = []

    for e in entries:
        kind = e.get("kind")
        if kind == "election":
            current_term, leader_id = apply_election(current_term, leader_id, e)
        elif kind == "commit":
            commit_index = apply_commit(commit_index, e)
        elif kind == "config":
            membership, epoch_term = apply_config(membership, epoch_term, e)
        elif kind == "queue":
            pending.append(e)

    for e in pending:
        if int(e["index"]) <= commit_index:
            queues[e["queue_id"]] = int(e["payload"]["messages"])

    membership = sorted(membership)
    st = {
        "cluster": cluster,
        "commit_index": commit_index,
        "current_term": current_term,
        "leader_id": leader_id,
        "membership": membership,
        "queue_states": queues,
        "truncated_before": truncated_before,
    }
    st["replay_digest"] = digest_staging(st)
    return st
