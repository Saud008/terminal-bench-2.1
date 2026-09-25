#!/usr/bin/env python3
"""Mock s6-rc change/up transitions against a state directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_rc(state_dir: Path) -> dict[str, str]:
    rc = state_dir / "services.json"
    if not rc.is_file():
        return {}
    return json.loads(rc.read_text(encoding="utf-8"))


def save_rc(state_dir: Path, data: dict[str, str]) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "services.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def apply_order(state_dir: Path, order: list[str], log_path: Path | None = None) -> list[str]:
    rc = load_rc(state_dir)
    transitions: list[str] = []
    for name in order:
        prev = rc.get(name, "down")
        if prev != "up":
            rc[name] = "up"
            transitions.append(name)
    save_rc(state_dir, rc)
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        existing: list[str] = []
        if log_path.is_file():
            existing = json.loads(log_path.read_text(encoding="utf-8"))
        existing.extend(transitions)
        log_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    return transitions


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_change = sub.add_parser("change")
    p_change.add_argument("--state-dir", required=True)
    p_change.add_argument("--order-json", required=True)
    p_change.add_argument("--log", default="")
    p_status = sub.add_parser("status")
    p_status.add_argument("--state-dir", required=True)
    p_status.add_argument("--service", required=True)
    args = parser.parse_args()
    state_dir = Path(args.state_dir)
    if args.cmd == "change":
        order = json.loads(Path(args.order_json).read_text(encoding="utf-8"))["order"]
        log = Path(args.log) if args.log else None
        applied = apply_order(state_dir, order, log)
        print(json.dumps({"transitions": applied}))
        return 0
    rc = load_rc(state_dir)
    print(json.dumps({"service": args.service, "state": rc.get(args.service, "down")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
