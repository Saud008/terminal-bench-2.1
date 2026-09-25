#!/usr/bin/env python3
"""Parse s6-rc bundle definition files into structured metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_bundle(path: Path) -> dict:
    bundle_name = ""
    services: dict[str, str] = {}
    hard_deps: list[list[str]] = []
    soft_deps: list[list[str]] = []
    longruns: list[str] = []

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        head = parts[0]
        if head == "bundle" and len(parts) >= 2:
            bundle_name = parts[1]
        elif head == "service" and len(parts) >= 3:
            services[parts[1]] = parts[2]
        elif head == "dep" and len(parts) >= 4 and parts[2] == "hard":
            hard_deps.append([parts[1], parts[3]])
        elif head == "dep" and len(parts) >= 4 and parts[2] == "soft":
            # dep CHILD soft PARENT → [CHILD, PARENT]
            soft_deps.append([parts[1], parts[3]])
        elif (
            head == "soft"
            and len(parts) >= 5
            and parts[1] == "dep"
            and parts[3] == "soft"
        ):
            # soft dep CHILD soft PARENT → [CHILD, PARENT]
            soft_deps.append([parts[2], parts[4]])
        elif head == "longrun" and len(parts) >= 2:
            longruns.append(parts[1])

    if not bundle_name:
        bundle_name = path.stem

    return {
        "name": bundle_name,
        "source": str(path.resolve()),
        "services": [{"name": n, "type": t} for n, t in sorted(services.items())],
        "hard_deps": hard_deps,
        "soft_deps": soft_deps,
        "longruns": sorted(set(longruns)),
    }


def ingest_tree(tree: Path, touch: Path | None = None) -> dict:
    bundles: dict[str, dict] = {}
    for path in sorted(tree.rglob("*.bundle")):
        meta = parse_bundle(path)
        bundles[meta["name"]] = meta
        if touch is not None:
            with touch.open("a", encoding="utf-8") as fh:
                fh.write(f"{path.resolve()}\n")
    return {"tree": str(tree.resolve()), "bundles": bundles}


def file_meta(path: Path, touch: Path | None = None) -> dict:
    return parse_bundle(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_file = sub.add_parser("file-meta")
    p_file.add_argument("--file", required=True)
    p_file.add_argument("--touch", default="")
    p_tree = sub.add_parser("ingest-tree")
    p_tree.add_argument("--tree", required=True)
    p_tree.add_argument("--touch", default="")
    args = parser.parse_args()
    touch = Path(args.touch) if getattr(args, "touch", "") else None
    if args.cmd == "file-meta":
        print(json.dumps({"bundle": file_meta(Path(args.file), touch)}, indent=2))
    else:
        print(json.dumps(ingest_tree(Path(args.tree), touch), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
