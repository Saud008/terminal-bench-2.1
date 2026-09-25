"""sheetd CLI — impose and sample verbs (golden — oversized exits 2)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sheet import flow
from sheet.validate import OversizedError


def cmd_impose(args: argparse.Namespace) -> int:
    try:
        flow.run_impose(
            Path(args.catalog),
            Path(args.marks),
            args.set,
            int(args.seed),
            Path(args.sheet_out),
            Path(args.ledger_out),
        )
    except OversizedError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def cmd_sample(args: argparse.Namespace) -> int:
    try:
        result = flow.run_sample(
            Path(args.sheet),
            Path(args.ledger),
            args.mark,
            int(args.frame),
            float(args.u),
            float(args.v),
        )
        flow.emit_sample_json(result)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, RuntimeError, ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sheetd")
    sub = parser.add_subparsers(dest="command", required=True)

    p_impose = sub.add_parser("impose")
    p_impose.add_argument("--catalog", required=True)
    p_impose.add_argument("--marks", required=True)
    p_impose.add_argument("--set", required=True)
    p_impose.add_argument("--seed", required=True, type=int)
    p_impose.add_argument("--sheet-out", required=True)
    p_impose.add_argument("--ledger-out", required=True)
    p_impose.set_defaults(func=cmd_impose)

    p_sample = sub.add_parser("sample")
    p_sample.add_argument("--sheet", required=True)
    p_sample.add_argument("--ledger", required=True)
    p_sample.add_argument("--mark", required=True)
    p_sample.add_argument("--frame", required=True, type=int)
    p_sample.add_argument("--u", required=True, type=float)
    p_sample.add_argument("--v", required=True, type=float)
    p_sample.set_defaults(func=cmd_sample)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
