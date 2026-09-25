#!/usr/bin/env python3
"""CLI runner for load / forecast / write-report."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from lib.calendar.drift_slots import build_forecast
from lib.report.digest_export import write_report_from_manifest
from lib.units.fragment_merge import merge_timer_bundle


def cmd_load(bundle: Path, timer_name: str, manifest: Path) -> None:
    timer = merge_timer_bundle(bundle, timer_name)
    doc = {"ingest": {"timer_name": timer_name}, "merged_timer": timer}
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("w", encoding="utf-8") as fh:
        json.dump(doc, fh, sort_keys=True, separators=(",", ":"))
        fh.write("\n")


def cmd_forecast(bundle: Path, timer_name: str, context: dict, reference: datetime, manifest: Path) -> None:
    stage_doc = json.loads(manifest.read_text(encoding="utf-8"))
    stage_doc["forecast"] = build_forecast(bundle, timer_name, context, reference)
    with manifest.open("w", encoding="utf-8") as fh:
        json.dump(stage_doc, fh, sort_keys=True, separators=(",", ":"))
        fh.write("\n")


def main() -> None:
    cmd = sys.argv[1]
    if cmd == "load":
        cmd_load(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]))
    elif cmd == "forecast":
        context = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
        ref = datetime.fromisoformat(sys.argv[5].replace("Z", "+00:00")).astimezone(timezone.utc)
        cmd_forecast(Path(sys.argv[2]), sys.argv[3], context, ref, Path(sys.argv[6]))
    elif cmd == "write-report":
        write_report_from_manifest(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        raise SystemExit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
