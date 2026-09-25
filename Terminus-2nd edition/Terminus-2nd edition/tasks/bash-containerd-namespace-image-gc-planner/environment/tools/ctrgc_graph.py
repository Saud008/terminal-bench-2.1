#!/usr/bin/env python3
"""Graph helpers for ctrgc snapshot trees."""

from __future__ import annotations

import argparse
import hashlib
import json
from typing import Any


def digest_lines(body: str) -> str:
    """SHA-256 hex digest for canonical line bodies (matches ctrgc plan math)."""
    return hashlib.sha256(body.encode()).hexdigest()


def _load_snaps(raw: str) -> list[dict[str, Any]]:
    data = json.loads(raw)
    if not isinstance(data, list):
        raise SystemExit("snapshots must be a JSON array")
    return data


def descendants(root: str, snaps: list[dict[str, Any]]) -> list[str]:
    by_parent: dict[str, list[str]] = {}
    for s in snaps:
        by_parent.setdefault(s.get("parent") or "", []).append(s["key"])
    out: set[str] = set()

    def walk(k: str) -> None:
        out.add(k)
        for c in by_parent.get(k, []):
            walk(c)

    if any(s["key"] == root for s in snaps):
        walk(root)
    return sorted(out)


def ancestors(key: str, snaps: list[dict[str, Any]]) -> list[str]:
    by_key = {s["key"]: s for s in snaps}
    out: list[str] = []
    cur = key
    while cur:
        par = by_key.get(cur, {}).get("parent") or ""
        if not par:
            break
        out.append(par)
        cur = par
    return sorted(set(out))


def depth_map(snaps: list[dict[str, Any]]) -> dict[str, int]:
    by_key = {s["key"]: s for s in snaps}

    def depth(k: str) -> int:
        par = by_key[k].get("parent") or ""
        return 0 if not par else 1 + depth(par)

    return {s["key"]: depth(s["key"]) for s in snaps}


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("descendants")
    d.add_argument("--root", required=True)
    d.add_argument("--snaps-json", required=True)

    a = sub.add_parser("ancestors")
    a.add_argument("--key", required=True)
    a.add_argument("--snaps-json", required=True)

    m = sub.add_parser("depth-map")
    m.add_argument("--snaps-json", required=True)

    args = p.parse_args()
    if args.cmd == "descendants":
        print(json.dumps(descendants(args.root, _load_snaps(args.snaps_json))))
    elif args.cmd == "ancestors":
        print(json.dumps(ancestors(args.key, _load_snaps(args.snaps_json))))
    elif args.cmd == "depth-map":
        print(json.dumps(depth_map(_load_snaps(args.snaps_json)), sort_keys=True))


if __name__ == "__main__":
    main()
