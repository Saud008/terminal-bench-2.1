"""duelctl argparse/argv switchboard."""

from __future__ import annotations

import sys

from duelctl import pipeline


def usage() -> None:
    print("duelctl admit-log --arena T --scenario S", file=sys.stderr)
    print("duelctl fold-branches --arena T --scenario S", file=sys.stderr)
    print("duelctl score-windows --arena T --scenario S", file=sys.stderr)
    print("duelctl seal-ledger --arena T --scenario S", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv:
        usage()
        return 2
    cmd, *rest = argv
    try:
        if cmd == "admit-log":
            pipeline.admit_log(rest)
        elif cmd == "fold-branches":
            pipeline.fold_branches_cmd(rest)
        elif cmd == "score-windows":
            pipeline.score_windows(rest)
        elif cmd == "seal-ledger":
            pipeline.seal_ledger(rest)
        else:
            usage()
            return 2
    except Exception as exc:  # noqa: BLE001 — CLI surface exits 1 on error
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
