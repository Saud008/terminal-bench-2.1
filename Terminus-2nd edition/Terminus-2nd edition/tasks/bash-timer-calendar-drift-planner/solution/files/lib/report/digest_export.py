#!/usr/bin/env python3
"""Correct digest export for oracle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def plan_digest(plan: dict[str, Any]) -> str:
    payload = {
        "catchup_run_utc": plan["catchup_run_utc"],
        "missed_run_utc": plan["missed_run_utc"],
        "next_fire_utc_earliest": plan["next_fire_utc_earliest"],
        "next_fire_utc_latest": plan["next_fire_utc_latest"],
        "timer_mode": plan["timer_mode"],
        "timer_name": plan["timer_name"],
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def write_report_from_manifest(manifest: Path, out: Path) -> None:
    stage_doc = json.loads(manifest.read_text(encoding="utf-8"))
    if "forecast" not in stage_doc:
        raise SystemExit("missing forecast block")
    plan = stage_doc["forecast"]
    doc = dict(plan)
    doc["plan_digest"] = plan_digest(plan)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(doc, fh, sort_keys=True, separators=(",", ":"))
        fh.write("\n")
