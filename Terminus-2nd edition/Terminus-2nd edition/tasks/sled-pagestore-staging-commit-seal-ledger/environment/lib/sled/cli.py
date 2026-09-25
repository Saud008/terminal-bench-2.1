from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from sled import batch, commit, crash_replay, export, pin, reclaim, walk


def resolve_table(table: str) -> str:
    prefix = os.environ.get("TB3_TABLE_PREFIX", "")
    if prefix.startswith("/"):
        return f"{prefix.rstrip('/')}/{table}"
    return table


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("usage: sledtool <command>", file=sys.stderr)
        return 2
    cmd = args[0]
    rest = args[1:]
    if cmd == "batch":
        table = _flag(rest, "--table")
        inp = Path(_flag(rest, "--input"))
        batch.apply_batch_file(resolve_table(table), inp)
    elif cmd == "delete":
        table = _flag(rest, "--table")
        key = _flag(rest, "--key")
        batch.delete_key(resolve_table(table), key)
    elif cmd == "publish":
        table = _flag(rest, "--table")
        commit.commit_table(resolve_table(table))
    elif cmd == "snapshot-pin":
        table = _flag(rest, "--table")
        snap = _flag(rest, "--snapshot-id")
        pin.pin_snapshot(resolve_table(table), snap)
    elif cmd == "compact":
        table = _flag(rest, "--table")
        freed = reclaim.compact_table(resolve_table(table))
        print(json.dumps({"pages_freed": freed}))
    elif cmd == "journal-replay":
        table = _flag(rest, "--table")
        journal = Path(_flag(rest, "--journal"))
        applied = crash_replay.replay_crash_journal(resolve_table(table), journal)
        print(json.dumps({"entries_applied": applied}))
    elif cmd == "scan-range":
        table = _flag(rest, "--table")
        start = _flag(rest, "--start")
        end = _flag(rest, "--end")
        out = Path(_flag(rest, "--out"))
        export.export_range(resolve_table(table), start, end, out)
    elif cmd == "export":
        table = _flag(rest, "--table")
        out = Path(_flag(rest, "--out"))
        export.export_table(resolve_table(table), out)
    elif cmd == "walk":
        table = _flag(rest, "--table")
        report = walk.walk_table(resolve_table(table))
        print(json.dumps(report))
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        return 2
    return 0


def _flag(args: list[str], name: str) -> str:
    for i, arg in enumerate(args):
        if arg == name and i + 1 < len(args):
            return args[i + 1]
    raise ValueError(f"missing {name}")


if __name__ == "__main__":
    raise SystemExit(main())
