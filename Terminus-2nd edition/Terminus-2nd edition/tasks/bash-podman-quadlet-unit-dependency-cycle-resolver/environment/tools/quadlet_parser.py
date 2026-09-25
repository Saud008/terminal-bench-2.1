#!/usr/bin/env python3
"""Surface parser for Podman Quadlet .container fragments (fixture subset)."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SECTION_RE = re.compile(r"^\s*\[(Unit|Service|Container|Install)\]\s*$")
ASSIGN_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*)=(.*)$")


def parse_fragment(path: Path) -> dict[str, dict[str, list[str] | str]]:
    """Parse one quadlet fragment into section -> key -> value(s)."""
    sections: dict[str, dict[str, list[str] | str]] = {}
    current: str | None = None
    text = path.read_text(encoding="utf-8")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        sec = SECTION_RE.match(raw)
        if sec:
            current = sec.group(1)
            sections.setdefault(current, {})
            continue
        if current is None:
            continue
        m = ASSIGN_RE.match(line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        bucket = sections[current]
        list_keys = {
            "After",
            "Wants",
            "Requires",
            "EnvironmentFile",
            "BindsTo",
            "PartOf",
        }
        if key in list_keys:
            items = bucket.setdefault(key, [])
            assert isinstance(items, list)
            for part in val.split():
                if part and part not in items:
                    items.append(part)
        else:
            bucket[key] = val
    return sections


def file_meta(path: Path, touch: Path | None = None) -> dict[str, Any]:
    meta = {"path": str(path.resolve()), "sections": parse_fragment(path)}
    if touch is not None:
        with touch.open("a", encoding="utf-8") as fh:
            fh.write(f"{path.resolve()}\n")
    return meta


def unit_name_from_container(path: Path) -> str:
    stem = path.name
    if not stem.endswith(".container"):
        raise ValueError(f"not a container file: {path}")
    return f"{stem[: -len('.container')]}.service"


def discover_units(tree: Path) -> list[Path]:
    return sorted(tree.rglob("*.container"))


def dropin_dir(base: Path) -> Path:
    return base.parent / f"{base.name}.d"


def list_dropins(base: Path) -> list[Path]:
    d = dropin_dir(base)
    if not d.is_dir():
        return []
    return sorted(d.glob("*.conf"), key=lambda p: p.name)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_file = sub.add_parser("file-meta")
    p_file.add_argument("--file", required=True)
    p_file.add_argument("--touch", default="")

    p_disc = sub.add_parser("discover")
    p_disc.add_argument("--tree", required=True)

    args = ap.parse_args()
    if args.cmd == "file-meta":
        touch = Path(args.touch) if args.touch else None
        print(json.dumps(file_meta(Path(args.file), touch)))
    elif args.cmd == "discover":
        paths = discover_units(Path(args.tree))
        print(json.dumps([str(p.resolve()) for p in paths]))


if __name__ == "__main__":
    main()
