from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from roster.audit import write_audit
from roster.ledger import export_ledger
from roster.logparse import read_cluster_logs
from roster.replay import digest_staging, replay
from roster.seal import compute_membership_seal
from roster.staging import DEFAULT_PATH, read_staging, write_staging
from roster.truncate import filter_after_snapshot, load_baseline


def _parse(args: list[str]) -> tuple[str, str, str, list[str]]:
    cluster = ""
    scenario = ""
    fixture_dir = os.environ.get("TB3_FIXTURE_DIR") or "/app/fixtures"
    rest: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--cluster":
            i += 1
            cluster = args[i]
        elif args[i] == "--scenario":
            i += 1
            scenario = args[i]
        elif args[i] == "--fixture-dir":
            i += 1
            fixture_dir = args[i]
        elif args[i] in ("--output-ledger", "--output-seal"):
            rest.append(args[i])
            i += 1
            rest.append(args[i])
        else:
            rest.append(args[i])
        i += 1
    return cluster, scenario, fixture_dir, rest


def cmd_replay(args: list[str]) -> int:
    cluster, scenario, fixture_dir, _ = _parse(args)
    entries = read_cluster_logs(Path(fixture_dir) / scenario)
    st = replay(cluster, entries, 0)
    write_staging(DEFAULT_PATH, st)
    return 0


def cmd_merge(args: list[str]) -> int:
    cluster, scenario, fixture_dir, _ = _parse(args)
    d = Path(fixture_dir) / scenario
    snap = json.loads((d / "snapshot.json").read_text(encoding="utf-8"))
    entries = read_cluster_logs(d)
    tail = filter_after_snapshot(entries, snap)
    qs, mem, commit_idx = load_baseline(snap)
    st = replay(
        cluster,
        tail,
        int(snap["last_included_index"]),
        baseline={
            "membership": mem,
            "queue_states": qs,
            "commit_index": commit_idx,
            "current_term": int(snap["last_included_term"]),
            "epoch_term": int(snap["last_included_term"]),
        },
    )
    st["replay_digest"] = digest_staging(st)
    write_staging(DEFAULT_PATH, st)
    return 0


def cmd_audit(args: list[str]) -> int:
    cluster, scenario, _, _ = _parse(args)
    write_audit(cluster, scenario)
    return 0


def cmd_export(args: list[str]) -> int:
    _, _, _, rest = _parse(args)
    ledger = "/app/output/committed-queue-state.jsonl"
    seal = "/app/output/membership-seal.json"
    i = 0
    while i < len(rest):
        if rest[i] == "--output-ledger":
            i += 1
            ledger = rest[i]
        elif rest[i] == "--output-seal":
            i += 1
            seal = rest[i]
        i += 1
    st = read_staging(DEFAULT_PATH)
    st["raft_seal"] = compute_membership_seal(st)
    export_ledger(st, ledger, seal)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv:
        return 2
    cmd, *rest = argv
    dispatch = {
        "replay-log": cmd_replay,
        "merge-snapshot": cmd_merge,
        "audit-membership": cmd_audit,
        "export-committed": cmd_export,
    }
    fn = dispatch.get(cmd)
    if not fn:
        return 2
    return fn(rest)


if __name__ == "__main__":
    raise SystemExit(main())
