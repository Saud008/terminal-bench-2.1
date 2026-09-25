#!/usr/bin/env python3
"""Load YAML variable files and emit sorted JSON for bash callers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml


def load_mapping(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping in {path}")
    return data


def cmd_load(path: Path) -> None:
    print(json.dumps(load_mapping(path), sort_keys=True))


def cmd_touch(path: Path, touch_file: Path) -> None:
    touch_file.parent.mkdir(parents=True, exist_ok=True)
    with touch_file.open("a", encoding="utf-8") as fh:
        fh.write(f"{path.resolve()}\n")
    cmd_load(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    load_p = sub.add_parser("load")
    load_p.add_argument("--file", required=True)

    touch_p = sub.add_parser("touch-load")
    touch_p.add_argument("--file", required=True)
    touch_p.add_argument("--touch", default="/app/output/.resolve-touch")

    args = parser.parse_args()
    if args.cmd == "load":
        cmd_load(Path(args.file))
    elif args.cmd == "touch-load":
        cmd_touch(Path(args.file), Path(args.touch))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        sys.exit(1)
