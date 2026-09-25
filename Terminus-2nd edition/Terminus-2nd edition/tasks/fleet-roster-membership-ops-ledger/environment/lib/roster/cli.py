from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from roster.audit import write_audit
from roster.ledger import export_ledger
from roster.logparse import read_cluster_logs
from roster.replay import replay
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
        elif args[i] == "--output-ledger" or args[i] == "--output-seal":
            i += 1
            rest.append(args[i - 1])
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
    # BUG: empty baseline (ignores snapshot term/membership/queues/commit)
    st = replay(cluster, tail, int(snap["last_included_index"]))
    for k, v in qs.items():
        st["queue_states"].setdefault(k, v)
    if not st["membership"]:
        st["membership"] = mem
    st["commit_index"] = max(st["commit_index"], commit_idx)
    from roster.replay import digest_staging

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
        print(
            "rosterctl replay-log|merge-snapshot|audit-membership|export-committed ...",
            file=sys.stderr,
        )
        return 2
    cmd, *rest = argv
    if cmd == "replay-log":
        return cmd_replay(rest)
    if cmd == "merge-snapshot":
        return cmd_merge(rest)
    if cmd == "audit-membership":
        return cmd_audit(rest)
    if cmd == "export-committed":
        return cmd_export(rest)
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
