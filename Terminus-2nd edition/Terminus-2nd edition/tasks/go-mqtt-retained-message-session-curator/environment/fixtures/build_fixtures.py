#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HIDDEN = Path(os.environ.get("MQTT_HIDDEN_ROOT", ROOT.parent / "hidden"))


def copy_scenarios(src: Path, dst: Path) -> None:
    if not src.is_dir():
        return
    for scenario_dir in sorted(src.iterdir()):
        if not scenario_dir.is_dir():
            continue
        events = scenario_dir / "events.jsonl"
        if not events.is_file():
            continue
        out = dst / "broker-journals" / scenario_dir.name
        out.mkdir(parents=True, exist_ok=True)
        out.joinpath("events.jsonl").write_text(events.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> None:
    copy_scenarios(HIDDEN / "broker-journals", ROOT)


if __name__ == "__main__":
    main()
