"""sipcdrctl argparse/argv switchboard."""

from __future__ import annotations

import sys

from sipcdr import pipeline


def usage() -> None:
    print("sipcdrctl ingest-transcript --tenant T --scenario S", file=sys.stderr)
    print("sipcdrctl compile-dialogs --tenant T --scenario S", file=sys.stderr)
    print("sipcdrctl rate-billing --tenant T --scenario S", file=sys.stderr)
    print("sipcdrctl export-cdr --tenant T --scenario S", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv:
        usage()
        return 2
    cmd, *rest = argv
    try:
        if cmd == "ingest-transcript":
            pipeline.ingest_transcript(rest)
        elif cmd == "compile-dialogs":
            pipeline.compile_dialogs_cmd(rest)
        elif cmd == "rate-billing":
            pipeline.rate_billing(rest)
        elif cmd == "export-cdr":
            pipeline.export_cdr(rest)
        else:
            usage()
            return 2
    except Exception as exc:  # noqa: BLE001 — CLI surface mirrors Go exit-1 on error
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
