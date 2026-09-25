"""Independent OCF Raft WAL replay reference for qqraftctl quorum membership attestation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "/app/fixtures")
from digest_util import sha256_canonical_json


def load_logs(scenario_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for path in sorted(scenario_dir.glob("*.qlog")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    rows.sort(key=lambda r: (r["term"], r["index"]))
    return rows


def load_snapshot(scenario_dir: Path) -> dict | None:
    p = scenario_dir / "snapshot.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def replay_reference(cluster: str, scenario_dir: Path) -> dict:
    snap = load_snapshot(scenario_dir)
    entries = load_logs(scenario_dir)
    truncated = 0
    commit_index = 0
    current_term = 0
    leader_id = ""
    membership: list[str] = []
    epoch_term = 0
    queues: dict[str, int] = {}

    if snap:
        truncated = snap["last_included_index"]
        commit_index = snap["commit_index"]
        current_term = snap["last_included_term"]
        membership = list(snap["membership"])
        epoch_term = snap["last_included_term"]
        queues = dict(snap["queue_states"])
        entries = [e for e in entries if e["index"] > truncated]

    for e in entries:
        term = e["term"]
        idx = e["index"]
        kind = e["kind"]
        if kind == "election":
            role = e["payload"]["role"]
            node = e["payload"]["node_id"]
            if term > current_term:
                current_term = term
                if role == "leader":
                    leader_id = node
            elif term == current_term and role == "leader":
                leader_id = node
        if kind == "commit":
            ci = int(e["payload"]["commit_index"])
            commit_index = max(commit_index, ci)
        if kind == "config" and term >= epoch_term:
            epoch_term = term
            op = e["payload"]["op"]
            node = e["payload"]["node_id"]
            if op == "add_voter" and node not in membership:
                membership.append(node)
            if op == "remove_voter" and node in membership:
                membership.remove(node)
            membership.sort()

    for e in entries:
        idx = e["index"]
        if e["kind"] == "queue" and idx <= commit_index:
            qid = e["queue_id"]
            queues[qid] = int(e["payload"]["messages"])

    membership = sorted(membership)
    queues = {k: queues[k] for k in sorted(queues)}
    body = {
        "cluster": cluster,
        "commit_index": commit_index,
        "current_term": current_term,
        "leader_id": leader_id,
        "membership": membership,
        "queue_states": queues,
        "truncated_before": truncated,
    }
    digest = sha256_canonical_json(body)
    body["replay_digest"] = digest
    return body


def reference_export(cluster: str, scenario: str, fixture_root: Path) -> tuple[list[dict], dict]:
    st = replay_reference(cluster, fixture_root / scenario)
    rows = []
    for qid in sorted(st["queue_states"]):
        rows.append(
            {
                "queue_id": qid,
                "messages": st["queue_states"][qid],
                "leader_id": st["leader_id"],
                "term": st["current_term"],
                "commit_index": st["commit_index"],
                "replicas": list(st["membership"]),
            }
        )
    seal_body = {
        "cluster": st["cluster"],
        "commit_index": st["commit_index"],
        "current_term": st["current_term"],
        "leader_id": st["leader_id"],
        "membership": st["membership"],
        "queue_states": {k: st["queue_states"][k] for k in sorted(st["queue_states"])},
        "membership_epoch": st["current_term"],
    }
    raft_seal = sha256_canonical_json(seal_body)
    seal = {
        "raft_seal": raft_seal,
        "membership_epoch": st["current_term"],
        "export_row_count": len(rows),
    }
    return rows, seal
