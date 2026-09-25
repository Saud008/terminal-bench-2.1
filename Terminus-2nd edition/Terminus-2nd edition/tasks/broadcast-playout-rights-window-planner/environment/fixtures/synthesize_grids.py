#!/usr/bin/env python3
"""Build scenario bundle.json files with randomized titles and contract labels."""
from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HIDDEN_ROOT = os.environ.get("GRIDPLAN_HIDDEN_ROOT")
TARGET = Path(HIDDEN_ROOT) if HIDDEN_ROOT else ROOT

BUNDLED = ["clean-playout", "rights-overlap", "blackout-precedence", "ad-marker-preserve", "feed-substitution", "dedupe-recompile", "stable-airtime-rank", "multi-feed-plan"]
HIDDEN = ["hidden-rights-trap", "hidden-blackout-trap"]

def _scenario_bundle(name: str, rng: random.Random, *, hidden: bool = False) -> dict:
    feed_a = f"F{rng.randint(10, 99)}"
    feed_b = f"F{rng.randint(10, 99)}"
    region = "US-EAST"
    channel = f"CH{rng.randint(1, 9)}"
    policies = {"overlap_rule": "narrowest_window"}

    if name == "clean-playout":
        programs = [
            {"program_id": "P1", "feed_id": feed_a, "start_utc": "2026-06-01T12:00:00Z", "duration_sec": 3600, "title": f"News-{rng.randint(100,999)}"},
        ]
        rights = [
            {"contract_id": "R1", "program_id": "P1", "region": region, "window_start": "2026-01-01", "window_end": "2026-12-31"},
        ]
        blackouts = []
        ad_markers = [{"program_id": "P1", "offset_sec": 900, "marker_id": "AD1"}]
        feeds = [{"feed_id": feed_a, "substitutions": {}}]
    elif name == "rights-overlap":
        programs = [
            {"program_id": "P1", "feed_id": feed_a, "start_utc": "2026-06-15T18:00:00Z", "duration_sec": 1800, "title": f"Movie-{rng.randint(100,999)}"},
        ]
        rights = [
            {"contract_id": "R-WIDE", "program_id": "P1", "region": region, "window_start": "2026-01-01", "window_end": "2026-12-31"},
            {"contract_id": "R-NARROW", "program_id": "P1", "region": region, "window_start": "2026-06-01", "window_end": "2026-06-30"},
        ]
        blackouts = []
        ad_markers = []
        feeds = [{"feed_id": feed_a, "substitutions": {}}]
    elif name == "blackout-precedence":
        programs = [
            {"program_id": "P1", "feed_id": feed_a, "start_utc": "2026-07-04T20:00:00Z", "duration_sec": 7200, "title": f"Special-{rng.randint(100,999)}"},
        ]
        rights = [
            {"contract_id": "R1", "program_id": "P1", "region": region, "window_start": "2026-01-01", "window_end": "2026-12-31"},
        ]
        blackouts = [
            {"blackout_id": "B-HIGH", "region": region, "start_utc": "2026-07-04T18:00:00Z", "end_utc": "2026-07-04T23:00:00Z", "precedence": 20},
        ]
        ad_markers = []
        feeds = [{"feed_id": feed_a, "substitutions": {}}]
    elif name == "ad-marker-preserve":
        programs = [
            {"program_id": "P-SRC", "feed_id": feed_a, "start_utc": "2026-08-01T14:00:00Z", "duration_sec": 3600, "title": f"Src-{rng.randint(100,999)}"},
        ]
        rights = [
            {"contract_id": "R1", "program_id": "P-DST", "region": region, "window_start": "2026-01-01", "window_end": "2026-12-31"},
        ]
        blackouts = []
        ad_markers = [{"program_id": "P-DST", "offset_sec": 600, "marker_id": "AD-MAIN"}]
        feeds = [{"feed_id": feed_a, "substitutions": {"P-SRC": "P-DST"}}]
    elif name == "feed-substitution":
        programs = [
            {"program_id": "P-LOCAL", "feed_id": feed_a, "start_utc": "2026-09-01T10:00:00Z", "duration_sec": 1800, "title": f"Local-{rng.randint(100,999)}"},
        ]
        rights = [
            {"contract_id": "R1", "program_id": "P-NET", "region": region, "window_start": "2026-01-01", "window_end": "2026-12-31"},
        ]
        blackouts = []
        ad_markers = []
        feeds = [{"feed_id": feed_a, "substitutions": {"P-LOCAL": "P-NET"}}]
    elif name == "dedupe-recompile":
        programs = [
            {"program_id": "P1", "feed_id": feed_a, "start_utc": "2026-05-01T08:00:00Z", "duration_sec": 3600, "title": f"ReRun-{rng.randint(100,999)}"},
        ]
        rights = [
            {"contract_id": "R1", "program_id": "P1", "region": region, "window_start": "2026-01-01", "window_end": "2026-12-31"},
        ]
        blackouts = []
        ad_markers = []
        feeds = [{"feed_id": feed_a, "substitutions": {}}]
    elif name == "stable-airtime-rank":
        programs = [
            {"program_id": "P2", "feed_id": feed_a, "start_utc": "2026-04-02T12:00:00Z", "duration_sec": 1800, "title": f"B-{rng.randint(100,999)}"},
            {"program_id": "P1", "feed_id": feed_a, "start_utc": "2026-04-01T12:00:00Z", "duration_sec": 1800, "title": f"A-{rng.randint(100,999)}"},
        ]
        rights = [
            {"contract_id": "R1", "program_id": "P1", "region": region, "window_start": "2026-01-01", "window_end": "2026-12-31"},
            {"contract_id": "R2", "program_id": "P2", "region": region, "window_start": "2026-01-01", "window_end": "2026-12-31"},
        ]
        blackouts = []
        ad_markers = []
        feeds = [{"feed_id": feed_a, "substitutions": {}}]
    elif name == "multi-feed-plan":
        programs = [
            {"program_id": "P1", "feed_id": feed_a, "start_utc": "2026-03-01T06:00:00Z", "duration_sec": 3600, "title": f"East-{rng.randint(100,999)}"},
            {"program_id": "P2", "feed_id": feed_b, "start_utc": "2026-03-01T07:00:00Z", "duration_sec": 3600, "title": f"West-{rng.randint(100,999)}"},
        ]
        rights = [
            {"contract_id": "R1", "program_id": "P1", "region": region, "window_start": "2026-01-01", "window_end": "2026-12-31"},
            {"contract_id": "R2", "program_id": "P2", "region": region, "window_start": "2026-01-01", "window_end": "2026-12-31"},
        ]
        blackouts = []
        ad_markers = []
        feeds = [
            {"feed_id": feed_a, "substitutions": {}},
            {"feed_id": feed_b, "substitutions": {}},
        ]
    elif name == "hidden-rights-trap":
        programs = [
            {"program_id": "P1", "feed_id": feed_a, "start_utc": "2026-10-10T22:00:00Z", "duration_sec": 5400, "title": f"Trap-{rng.randint(100,999)}"},
        ]
        rights = [
            {"contract_id": "R-OUT", "program_id": "P1", "region": region, "window_start": "2026-01-01", "window_end": "2026-09-30"},
            {"contract_id": "R-IN", "program_id": "P1", "region": region, "window_start": "2026-10-01", "window_end": "2026-10-31"},
        ]
        blackouts = []
        ad_markers = []
        feeds = [{"feed_id": feed_a, "substitutions": {}}]
    elif name == "hidden-blackout-trap":
        programs = [
            {"program_id": "P1", "feed_id": feed_a, "start_utc": "2026-11-11T19:00:00Z", "duration_sec": 3600, "title": f"Blk-{rng.randint(100,999)}"},
        ]
        rights = [
            {"contract_id": "R1", "program_id": "P1", "region": region, "window_start": "2026-01-01", "window_end": "2026-12-31"},
        ]
        blackouts = [
            {"blackout_id": "B-TRAP", "region": region, "start_utc": "2026-11-11T18:00:00Z", "end_utc": "2026-11-11T21:00:00Z", "precedence": 50},
        ]
        ad_markers = []
        feeds = [{"feed_id": feed_a, "substitutions": {}}]
    else:
        raise ValueError(name)

    seed = hashlib.sha256(f"{name}-{'hidden' if hidden else 'bundled'}".encode()).hexdigest()[:16]
    return {
        "seed": seed,
        "channel": channel,
        "region": region,
        "programs": programs,
        "rights": rights,
        "blackouts": blackouts,
        "ad_markers": ad_markers,
        "feeds": feeds,
        "policies": policies,
    }



def build(name: str, hidden: bool = False) -> None:
    rng = random.Random(name + ("hidden" if hidden else "bundled"))
    body = _scenario_bundle(name, rng, hidden=hidden)
    dest = TARGET / "scenarios" / name
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "bundle.json").write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    for s in BUNDLED:
        build(s, hidden=False)
    if HIDDEN_ROOT:
        for s in HIDDEN:
            build(s, hidden=True)


if __name__ == "__main__":
    main()
