"""The `/app/bin/partyd` host-local operations interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import clock, db, lifecycle, publish, sweeper


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="partyd")
    sub = p.add_subparsers(dest="verb", required=True)

    def operation(name: str):
        q = sub.add_parser(name)
        q.add_argument("--mono-ms", type=int, required=True)
        return q

    q = operation("create")
    q.add_argument("--leader", required=True)
    q.add_argument("--max-members", type=int)
    q = operation("invite")
    q.add_argument("--party", required=True)
    q.add_argument("--invitee", required=True)
    q.add_argument("--ttl-ms", type=int)
    q = operation("accept")
    q.add_argument("--invite", required=True)
    q.add_argument("--invitee", required=True)
    q.add_argument("--idempotency-key", required=True)
    q = operation("disconnect")
    q.add_argument("--party", required=True)
    q.add_argument("--player", required=True)
    q = operation("sweep")
    q = operation("export")
    q.add_argument("--party", required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        mono = clock.mono_ms(args.mono_ms)
        con = db.connect()
        if args.verb == "create":
            out = lifecycle.create(con, args.leader, args.max_members, mono)
        elif args.verb == "invite":
            out = lifecycle.invite(con, args.party, args.invitee, args.ttl_ms, mono)
        elif args.verb == "accept":
            out = lifecycle.accept(
                con, args.invite, args.invitee, args.idempotency_key, mono
            )
        elif args.verb == "disconnect":
            out = lifecycle.disconnect(con, args.party, args.player, mono)
        elif args.verb == "sweep":
            out = sweeper.sweep(con, mono)
        else:
            out = publish.build_audit_report(con, args.party, mono)
            target = Path("/app/output/party-audit.json")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
            out = {"path": str(target)}
        print(json.dumps(out, separators=(",", ":")))
        return 0
    except publish.ExportRefusal as exc:
        print(str(exc), file=sys.stderr)
        return 3
    except (lifecycle.Conflict, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
