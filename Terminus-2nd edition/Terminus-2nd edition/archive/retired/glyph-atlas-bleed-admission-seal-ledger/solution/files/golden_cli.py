"""atlasd CLI — pack and probe verbs (golden — oversized exits 2)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from atlas import flow
from atlas.validate import OversizedError


def cmd_pack(args: argparse.Namespace) -> int:
    try:
        flow.run_pack(
            Path(args.catalog),
            Path(args.sprites),
            args.set,
            int(args.seed),
            Path(args.atlas_out),
            Path(args.manifest_out),
        )
    except OversizedError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def cmd_probe(args: argparse.Namespace) -> int:
    try:
        result = flow.run_probe(
            Path(args.atlas),
            Path(args.manifest),
            args.glyph,
            int(args.frame),
            float(args.u),
            float(args.v),
        )
        flow.emit_probe_json(result)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="atlasd")
    sub = parser.add_subparsers(dest="command", required=True)

    p_pack = sub.add_parser("pack")
    p_pack.add_argument("--catalog", required=True)
    p_pack.add_argument("--sprites", required=True)
    p_pack.add_argument("--set", required=True)
    p_pack.add_argument("--seed", required=True, type=int)
    p_pack.add_argument("--atlas-out", required=True)
    p_pack.add_argument("--manifest-out", required=True)
    p_pack.set_defaults(func=cmd_pack)

    p_probe = sub.add_parser("probe")
    p_probe.add_argument("--atlas", required=True)
    p_probe.add_argument("--manifest", required=True)
    p_probe.add_argument("--glyph", required=True)
    p_probe.add_argument("--frame", required=True, type=int)
    p_probe.add_argument("--u", required=True, type=float)
    p_probe.add_argument("--v", required=True, type=float)
    p_probe.set_defaults(func=cmd_probe)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
